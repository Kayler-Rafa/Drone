import os
import time
import math
import json
from collections import deque
import numpy as np
import pybullet as p
import pybullet_data

NODE_RED_URL = "http://127.0.0.1:1880/metrics"   

# -------------- CONFIG --------------
AREA_RADIUS = 18.0
POINT_COUNT = 100.0
DETECTION_RADIUS = 5
ALTITUDE_TARGET = 2.0
TIME_STEP = 1/240
SIM_SECONDS_MAX = 600
MAX_SIM_STEPS = int(SIM_SECONDS_MAX / TIME_STEP)
SPEED_MAX = 20.0            # m/s target horizontal speed
DRONE_MASS = 1.2
LOG_FILE = "logs_quad_v5.json"
RANDOM_SEED = 42

# Altitude PID (simple PD-ish)
KP_Z = 30.0
KD_Z = 8.0

# horizontal velocity controller gains (PD on velocity error)
KP_V = 8.0
KD_V = 2.0

# visual scale
POINT_SCALE = 1.0
DRONE_BOX = (0.6, 0.6, 0.12)
# -------------------------------------

np.random.seed(RANDOM_SEED)

def dist(a, b):
    a = np.array(a); b = np.array(b)
    return float(np.linalg.norm(a - b))

# --- simple NN + 2-opt (local improvement) ---
def nearest_neighbor(start, points):
    if not points:
        return []
    rem = points.copy()
    route = []
    cur = tuple(start)
    while rem:
        nxt = min(rem, key=lambda p: dist(cur, p))
        route.append(nxt)
        rem.remove(nxt)
        cur = nxt
    return route

def two_opt(route, start_point=None, iters=150):
    if not route or len(route) < 3:
        return route
    best = route.copy()

    def total_length(r):
        total = 0.0
        cur = start_point if start_point is not None else (0,0,0)
        for p_ in r:
            total += dist(cur, p_)
            cur = p_
        return total

    improved = True
    it = 0
    while improved and it < iters:
        improved = False
        it += 1
        n = len(best)
        for i in range(0, n-2):
            for j in range(i+2, n):
                newr = best[:i+1] + list(reversed(best[i+1:j+1])) + best[j+1:]
                if total_length(newr) + 1e-9 < total_length(best):
                    best = newr
                    improved = True
    return best

# generate points with soft constraint to avoid >3 inside detection radius
MAX_INITIAL_DETECT = 3
def generate_points(n_points, area_radius, detection_radius, base=(0,0,0)):
    pts = []
    attempts = 0
    while len(pts) < n_points and attempts < n_points * 300:
        attempts += 1
        r = area_radius * math.sqrt(np.random.uniform(0,1))
        theta = np.random.uniform(0, 2*math.pi)
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        z = 0.2
        cand = (x, y, z)
        nearby = sum(1 for p_ in pts if dist(p_, cand) <= detection_radius)
        if nearby <= (MAX_INITIAL_DETECT - 1):
            pts.append(cand)
    if len(pts) < n_points:
        print("[WARN] Couldn't place all points without clustering. Generated:", len(pts))
    return pts

class Logger:
    def __init__(self, filename):
        self.filename = filename
        self.entries = []
    def log(self, event, data):
        ent = {"evento": event, "data": data, "t": time.time()}
        self.entries.append(ent)
        print(json.dumps(ent))
    def save(self):
        with open(self.filename, "w") as f:
            json.dump(self.entries, f, indent=2)

# write a simple URDF for the quad (visual + inertial approximate)
def create_quad_urdf(path):
    bx, by, bz = DRONE_BOX
    urdf = '<?xml version="1.0" ?>\n<robot name="simple_quad">\n'
    urdf += f'  <link name="base_link">\n'
    urdf += f'    <inertial>\n      <origin xyz="0 0 0" rpy="0 0 0"/>\n      <mass value="{DRONE_MASS}"/>\n      <inertia ixx="0.02" iyy="0.02" izz="0.04" ixy="0" ixz="0" iyz="0"/>\n    </inertial>\n'
    urdf += f'    <visual>\n      <origin xyz="0 0 0" rpy="0 0 0"/>\n      <geometry>\n        <box size="{bx} {by} {bz}"/>\n      </geometry>\n      <material name="blue"><color rgba="0.2 0.3 0.8 1"/></material>\n    </visual>\n    <collision>\n      <origin xyz="0 0 0" rpy="0 0 0"/>\n      <geometry>\n        <box size="{bx} {by} {bz}"/>\n      </geometry>\n    </collision>\n  </link>\n'
    rotor_positions = [(bx/2,by/2,bz/2),(bx/2,-by/2,bz/2),(-bx/2,by/2,bz/2),(-bx/2,-by/2,bz/2)]
    for i,(x,y,z) in enumerate(rotor_positions):
        urdf += f'  <link name="rotor_{i}">\n'
        urdf += f'    <visual>\n      <origin xyz="{x} {y} {z}" rpy="0 0 0"/>\n      <geometry>\n        <cylinder length="0.02" radius="0.08"/>\n      </geometry>\n      <material name="black"><color rgba="0 0 0 1"/></material>\n    </visual>\n  </link>\n'
        urdf += f'  <joint name="joint_rotor_{i}" type="fixed">\n    <parent link="base_link"/>\n    <child link="rotor_{i}"/>\n    <origin xyz="0 0 0" rpy="0 0 0"/>\n  </joint>\n'
    urdf += '</robot>\n'
    with open(path, "w") as f:
        f.write(urdf)
    return path

# ---------------- SIMULAÇÃO ----------------
def run():
    logger = Logger(LOG_FILE)

    # connect GUI (fallback tiny)
    physicsClient = None
    try:
        physicsClient = p.connect(p.GUI)
        print("[INFO] p.connect(p.GUI) ->", physicsClient)
    except Exception as e:
        print("[WARN] p.connect GUI failed:", e)
    if physicsClient is None or physicsClient < 0:
        try:
            physicsClient = p.connect(p.TINY_GUI)
            print("[INFO] fallback to TINY_GUI ->", physicsClient)
        except Exception as e:
            print("[ERROR] could not open GUI or TINY_GUI:", e)
            return

    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.resetSimulation()
    p.setGravity(0,0,-9.8)
    p.setRealTimeSimulation(0)
    p.setTimeStep(TIME_STEP)
    p.loadURDF("plane.urdf")

    # create and load quad URDF
    quad_path = os.path.join(os.getcwd(), "quad_simple_v5.urdf")
    create_quad_urdf(quad_path)
    base_pos = (0.0, 0.0, ALTITUDE_TARGET)
    quad = p.loadURDF(quad_path, base_pos, useFixedBase=False)
    # increase damping to keep stable
    p.changeDynamics(quad, -1, mass=DRONE_MASS, linearDamping=0.8, angularDamping=1.0)

    # generate points
    pontos = generate_points(POINT_COUNT, AREA_RADIUS, DETECTION_RADIUS, base=base_pos)
    point_ids = []
    for pt in pontos:
        pid = p.loadURDF("sphere_small.urdf", pt, globalScaling=POINT_SCALE)
        point_ids.append(pid)

    logger.log("pontos_gerados", {"pontos": pontos})
    pontos_detectados = []
    deliveries = []
    rota_atual = []
    destino_atual = None

    replan_count = 0
    force_history = []
    altitude_history = []
    pos_history = []
    time_per_point = []
    last_delivery_time = None

    sim_time = 0.0
    step = 0

    def get_state(body):
        pos, orn = p.getBasePositionAndOrientation(body)
        euler = p.getEulerFromQuaternion(orn)
        lin_vel, ang_vel = p.getBaseVelocity(body)
        return np.array(pos), np.array(euler), np.array(lin_vel), np.array(ang_vel)

    logger.log("sim_start", {"POINT_COUNT": POINT_COUNT, "DETECTION_RADIUS": DETECTION_RADIUS})

    while step < MAX_SIM_STEPS:
        pos, euler, lin_vel, ang_vel = get_state(quad)
        altitude_history.append(float(pos[2]))
        pos_history.append(tuple(pos))

        # detection: add points that enter detection radius
        for pt in pontos:
            if pt not in pontos_detectados and pt not in deliveries:
                if dist(pos, pt) <= DETECTION_RADIUS:
                    pontos_detectados.append(pt)
                    logger.log("detectado", {"ponto": pt, "sim_time": sim_time})

        # initial plan if needed
        if not rota_atual and pontos_detectados:
            nn = nearest_neighbor(tuple(pos), pontos_detectados)
            rota_atual = two_opt(nn, start_point=tuple(pos), iters=200)
            destino_atual = rota_atual[0] if rota_atual else None
            logger.log("planejamento_inicial", {"rota": rota_atual})

        # determine active target:
        # If there is a current delivery destination, use it; otherwise patrol (slow circle)
        if destino_atual is None:
            # slow patrol (small circle near base) to find new points
            theta = 0.25 * sim_time
            r_patrol = 3.0
            target = np.array([r_patrol * math.cos(theta), r_patrol * math.sin(theta), ALTITUDE_TARGET])
        else:
            target = np.array([destino_atual[0], destino_atual[1], ALTITUDE_TARGET])

        # ---- ALTITUDE CONTROL (PD) ----
        z_err = ALTITUDE_TARGET - pos[2]
        vz = lin_vel[2]
        thrust_z = KP_Z * z_err - KD_Z * vz + DRONE_MASS * 9.8
        # small safety multiplier and clamp
        thrust_z *= 1.02
        thrust_z = float(max(0.0, min(thrust_z, DRONE_MASS * 80.0)))

        # ---- HORIZONTAL CONTROL (velocity PD) ----
        horiz_vec = target[:2] - pos[:2]
        dist_h = np.linalg.norm(horiz_vec)
        desired_velocity = np.array([0.0, 0.0])
        if dist_h > 0.05:
            direction = horiz_vec / dist_h
            desired_speed = min(SPEED_MAX, dist_h)  # speed proportional to distance but capped
            desired_velocity = direction * desired_speed

        # velocity error
        v_err = desired_velocity - lin_vel[:2]
        # compute required horizontal force (simple PD)
        fx = float(KP_V * v_err[0] - KD_V * lin_vel[0])
        fy = float(KP_V * v_err[1] - KD_V * lin_vel[1])

        # safety clamp on horizontal forces to avoid blowing away
        MAX_H_FORCE = 12.0
        fx = max(-MAX_H_FORCE, min(MAX_H_FORCE, fx))
        fy = max(-MAX_H_FORCE, min(MAX_H_FORCE, fy))

        # apply forces: vertical thrust + horizontal PD force
        p.applyExternalForce(quad, -1, [fx, fy, thrust_z], pos.tolist(), p.WORLD_FRAME)
        force_history.append((fx, fy, thrust_z))

        # debug prints occasionally
        if step % 120 == 0:
            print(f"[DEBUG] sim_time={sim_time:.2f} pos=({pos[0]:.2f},{pos[1]:.2f},{pos[2]:.2f}) "
                  f"dstTarget={dist_h:.2f} thrust={thrust_z:.1f} vx={lin_vel[0]:.2f} vy={lin_vel[1]:.2f}")

        # ---- Arrival / Delivery / Replanning logic ----
        arrival_radius = 0.55
        if destino_atual is not None and dist_h <= arrival_radius:
            # mark delivered
            deliveries.append(destino_atual)
            tnow = sim_time
            if last_delivery_time is not None:
                time_per_point.append(tnow - last_delivery_time)
            else:
                time_per_point.append(tnow)
            last_delivery_time = tnow
            logger.log("entrega", {"ponto": destino_atual, "sim_time": sim_time, "idx": len(deliveries)})

            # remove from detectados if present and from rota
            if destino_atual in pontos_detectados:
                try:
                    pontos_detectados.remove(destino_atual)
                except ValueError:
                    pass
            if rota_atual and rota_atual[0] == destino_atual:
                rota_atual.pop(0)

            # immediate assignment of next target if route has elements
            if rota_atual:
                destino_atual = rota_atual[0]
                logger.log("novo_destino_imediato", {"destino": destino_atual})
            else:
                destino_atual = None
                # if there are other detected but not in route, replan
                if pontos_detectados:
                    nn = nearest_neighbor(tuple(pos), pontos_detectados)
                    rota_atual = two_opt(nn, start_point=tuple(pos), iters=200)
                    destino_atual = rota_atual[0] if rota_atual else None
                    replan_count += 1
                    logger.log("replan", {"nova_rota": rota_atual, "replan_count": replan_count})
                else:
                    # if everything delivered, return to base and finish
                    if len(deliveries) >= len(pontos):
                        logger.log("missao_concluida", {"total_deliveries": len(deliveries)})
                        # simple return-to-base sequence
                        for _ in range(300):
                            pos_now, _, linv_now, _ = get_state(quad)
                            horiz_ret = np.array([base_pos[0], base_pos[1]]) - np.array([pos_now[0], pos_now[1]])
                            dhr = np.linalg.norm(horiz_ret)
                            if dhr > 0.2:
                                dirb = horiz_ret / dhr
                                desired_v = dirb * min(SPEED_MAX, dhr)
                                v_err_b = desired_v - linv_now[:2]
                                fx_b = float(KP_V * v_err_b[0] - KD_V * linv_now[0])
                                fy_b = float(KP_V * v_err_b[1] - KD_V * linv_now[1])
                                fx_b = max(-MAX_H_FORCE, min(MAX_H_FORCE, fx_b))
                                fy_b = max(-MAX_H_FORCE, min(MAX_H_FORCE, fy_b))
                                p.applyExternalForce(quad, -1, [fx_b, fy_b, thrust_z], pos_now.tolist(), p.WORLD_FRAME)
                            p.stepSimulation()
                            time.sleep(TIME_STEP)
                        break

        # step sim
        p.stepSimulation()
        time.sleep(TIME_STEP)
        sim_time += TIME_STEP
        step += 1

        # finalize metrics
    energy = sum(math.sqrt(fx*fx + fy*fy + fz*fz) * TIME_STEP for (fx,fy,fz) in force_history)

    dist_real = 0.0
    for i in range(1, len(pos_history)):
        dist_real += dist(pos_history[i-1], pos_history[i])

    metrics = {
        "deliveries": len(deliveries),
        "replans": replan_count,
        "time_per_point": time_per_point,
        "energy_est": energy,
        "alt_mean": float(np.mean(altitude_history)) if altitude_history else None,
        "alt_std": float(np.std(altitude_history)) if altitude_history else None,
        "distance_real": dist_real
    }

    # log final metrics
    logger.log("metrics_final", metrics)

    # envia MÉTRICAS para Node-RED (sem tentar iterar nada inexistente)
    try:
        import requests
        requests.post(NODE_RED_URL, json=metrics, timeout=2)
    except Exception as e:
        print("[ERRO] Falha ao enviar métricas ao Node-RED:", e)

    logger.save()
    p.disconnect()
    print("Simulação finalizada. Logs em", LOG_FILE)

if __name__ == "__main__":
    base_pos = (0.0, 0.0, ALTITUDE_TARGET)
    run()

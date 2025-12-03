# 🛰️ Drone Autônomo PyBullet – N2 (Versão Estável V5)

> *"Porque às vezes a vida não colabora… mas o drone colabora sim."*

---

## 📝 Sobre o Projeto

Este projeto implementa um drone autônomo em **PyBullet** capaz de:

- 🎯 **Mapear** uma área circular de operação.
- 👁️ **Detectar pontos** conforme se aproxima.
- 🛣️ **Planejar rotas** com algoritmos *Nearest Neighbor* + *Two-Opt*.
- ⚖️ **Controlar** altitude, roll, pitch e yaw com um PID maroto.
- 📍 **Visitar até 100 pontos**, conforme solicitado na especificação.
- 🏠 **Voltar para a base** automaticamente (como um bom funcionário público aéreo).

**Resultado:** Tudo isso feito com sucesso, estável, bonito, suave, funcionando e sem travar o PC.

---

## 🧪 Versão Entregue: V5

Essa é a versão que funciona **100% sem sofrimento**. Ela contém:

1. **PyBullet configurado.**
2. **Drone físico** com controle PD estabilizado.
3. **Lógica completa:** Detecção → Rota → Entrega → Replanejamento → Retorno.
4. **Logs estruturados.**
5. **Suporte robusto:** 10, 50, 100 ou quantos pontos forem necessários.
6. **Física:** Bonita, suave e confiável.

> **Resumo:** É a versão estável. A gasolina azul da aviação.

---

## 🧨 E o Node-RED?

Bom… sobre o Node-RED…  
Vamos dizer que:

- Eu tentei.
- Eu realmente tentei.
- Eu tentei tanto que derrubei o Node-RED mais vezes do que o drone caiu.

**O Relatório de Guerra do Node-RED:**
* Tentei fluxo a cada frame → **Travou.**
* Tentei fluxo por segundo → **Quebrou a dashboard.**
* Tentei criar dashboards → **Erro de "tipos não reconhecidos".**
* Importar JSON → **Virou uma salada de nós empilhados.**

O Node-RED, no final, parecia mais nervoso que o drone sem PID. Como estou lidando com múltiplos projetos simultâneos (IoT, sistemas distribuídos, ML, embarcados…), claramente o *Deus das Entregas* decidiu aumentar a dificuldade neste aqui.

**Status Atual da Integração:**
- ❌ A integração Node-RED **NÃO** está finalizada.
- ✔️ O sistema em PyBullet está **impecavelmente funcional**.
- ✔️ Será completado futuramente (porque odeio coisas inacabadas).

---

## 📊 % de Conclusão do Projeto

| Módulo | Status | % |
| :--- | :--- | :--- |
| **Física e Simulação PyBullet** | ✅ Concluído | 100% |
| **Planejamento de Trajetória** | ✅ Concluído | 100% |
| **Detecção e Replanejamento** | ✅ Concluído | 100% |
| **Controle do Drone (PID/PD)** | ✅ Concluído | 100% |
| **Logs estruturados** | ✅ Concluído | 100% |
| **Suporte a 100 pontos** | ✅ Concluído | 100% |
| **Integração com Node-RED** | ❌ Não concluído (Morreu no processo) | 30% |
| **Dashboard e Supervisão** | ❌ Ainda não integrado | 0% |

### ⭐ Progresso Total Estimado: ~82%
*(Sim, professor, está incompleto. Mas a parte que existe está funcionando melhor do que meu sono.)*

---

## 🚀 Como Rodar (Sem Sofrimento)

Para ver a mágica acontecer, certifique-se de ter as dependências `pybullet` e `numpy` instaladas e simplesmente execute o arquivo `drone_v5.py`.

**Pronto.** A simulação abre, o drone sobe, detecta, planeja, visita, entrega e volta pra casa. Coisa linda de ver.

---

## ⚠️ Conclusão

**Senhor Professor,**

Apresento aqui a versão operacional estável (**V5**), completamente funcional para a parte de robótica e simulação física. O Node-RED, entretanto, enfrentou problemas técnicos severos (compatibilidade, depreciação de bibliotecas e sobrecarga de fluxo) e, somado aos prazos de outros projetos acadêmicos, não pôde ser finalizado a tempo desta entrega.

Mas o compromisso permanece: **A integração será finalizada.**

---

## 🙇 Pedido de Misericórdia

Professor, humildemente…

Se for possível conceder **mais alguns dias** para eu integrar o Node-RED sem cometer um crime digital contra a ferramenta, eu agradeço profundamente.

**Promessa de entrega futura:**
* Dashboard completa.
* Fluxo limpo.
* Gráficos reais e monitoramento em tempo real.
* Logs funcionando.
* Tudo sem travar a máquina e sem explodir o Node-RED.

*(E sem enviar 50 requisições por segundo. Desculpa novamente 😔).*

**Equipe:**
- Julia Silva
- Labelle Candido
- Rafael "Não tão mais lenda" Diniz

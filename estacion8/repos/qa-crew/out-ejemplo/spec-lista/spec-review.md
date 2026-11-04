# Spec review · spec-lista.md

**Nota (calculada por el código): A** · nota que propuso el LLM: A

- Todos los críticos cumplen con evidencia → A

Ola única (demo-app). Todos los críticos cumplen con evidencia; T3 y T4 declarados.

| Criterio | Estado | Evidencia | Corrección mínima |
|---|---|---|---|
| P1 | Cumple | §1 Problema y usuario |  |
| P2 | Cumple | §2 Alcance (3 capacidades) |  |
| P3 | Cumple | §3 Fuera de alcance |  |
| P4 | Cumple | §4 BR-ESC-01 a BR-ESC-04 |  |
| P5 | Parcial | §1 menciona Persona + Juez, sin métrica explícita | Definir: Carlos y Pedro dejan de reprobar por escalamiento |
| P6 | Cumple | §8 Ninguna pendiente |  |
| T1 | Cumple | §5 CA-01 a CA-04 con resultado observable |  |
| T2 | Cumple | §5 tabla de casos + casos borde |  |
| T3 | Cumple | §6 npm run test:bdd, playwright chromium, test:unit |  |
| T4 | Cumple | §6 TDD declarado: escenarios antes del código |  |
| D1 | Cumple | §7 generateResponse() en demo-app/lib/agent.ts |  |
| D2 | Cumple | §7 POST /api/chat sin cambios de contrato |  |
| D3 | N/A | §7 sin cambios de interfaz |  |
| D4 | Cumple | §7 sin datos personales nuevos |  |

## Vacíos más graves

Ninguno.

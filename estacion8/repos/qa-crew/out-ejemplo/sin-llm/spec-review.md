# Spec review · escalamiento.md

| Ola | Nota (código) | Nota (LLM) | Decisión |
|---|---|---|---|
| ola-1 · Detección de la intención | **A** | A | pasa |
| ola-2 · Experiencia en el chat | **B** | B | pasa con supuestos (plan obligatorio) |
| ola-3 · Transferencia real a un asesor | **C** | C | vuelve a diseño |

## ola-1 · Detección de la intención · A

- Todos los críticos cumplen con evidencia → A

| Criterio | Estado | Evidencia | Corrección mínima |
|---|---|---|---|
| P1 | Cumple | §1 Problema y usuario |  |
| P3 | Cumple | §3 Fuera de alcance |  |
| P5 | Cumple | §2 Criterio de éxito |  |
| T3 | Cumple | §4 comandos de unit y bdd |  |
| T4 | Cumple | §4 TDD declarado |  |
| D2 | Cumple | §5 POST /api/chat sin cambios |  |
| D3 | N/A | §5 sin cambios de interfaz |  |
| D4 | Cumple | §5 sin datos personales nuevos |  |
| P2 | Cumple | Ola 1 · Alcance |  |
| P4 | Cumple | Ola 1 · BR-ESC-01 a BR-ESC-04 |  |
| P6 | Cumple | Ola 1 sin pendientes |  |
| T1 | Cumple | Ola 1 · CA-01 a CA-04 con resultado observable |  |
| T2 | Cumple | Ola 1 · tabla de CA + casos borde |  |
| D1 | Cumple | §5 generateResponse() en demo-app/lib/agent.ts |  |

## ola-2 · Experiencia en el chat · B

- Críticos parciales cerrados con supuesto: T2 → B

Supuestos (pendientes de aprobación):
- El horario del escalamiento es fijo, lunes a viernes de 8:00 AM a 6:00 PM, y no depende de la hora ni del día en que se pide.

Vacíos más graves:
1. T2: no define el horario de los sábados en el escalamiento

| Criterio | Estado | Evidencia | Corrección mínima |
|---|---|---|---|
| P1 | Cumple | §1 Problema y usuario |  |
| P3 | Cumple | §3 Fuera de alcance |  |
| P5 | Cumple | §2 Criterio de éxito |  |
| T3 | Cumple | §4 comandos de unit y bdd |  |
| T4 | Cumple | §4 TDD declarado |  |
| D2 | Cumple | §5 POST /api/chat sin cambios |  |
| D3 | N/A | §5 sin cambios de interfaz |  |
| D4 | Cumple | §5 sin datos personales nuevos |  |
| P2 | Cumple | Ola 2 · Alcance |  |
| P4 | Cumple | Ola 2 · BR-ESC-05 y BR-ESC-06 |  |
| P6 | Cumple | Ola 2 · Pendiente listado |  |
| T1 | Cumple | Ola 2 · CA-05 y CA-06 en el chat |  |
| T2 | Parcial | Ola 2 · CA-05/CA-06; falta el caso del sábado | Decidir el horario del escalamiento en sábado |
| D1 | Cumple | §5 diseño común |  |

## ola-3 · Transferencia real a un asesor · C

- Críticos que faltan: P4, T2, D1 → C

Vacíos más graves:
1. P4: no hay reglas de tiempos de espera, fuera de horario ni datos enviados
2. D1: la herramienta de soporte no está elegida
3. T2: no hay casos ni bordes

| Criterio | Estado | Evidencia | Corrección mínima |
|---|---|---|---|
| P1 | Cumple | §1 Problema y usuario |  |
| P3 | Cumple | §3 Fuera de alcance |  |
| P5 | Cumple | §2 Criterio de éxito |  |
| T3 | Cumple | §4 comandos de unit y bdd |  |
| T4 | Cumple | §4 TDD declarado |  |
| D2 | Cumple | §5 POST /api/chat sin cambios |  |
| D3 | N/A | §5 sin cambios de interfaz |  |
| D4 | Cumple | §5 sin datos personales nuevos |  |
| P2 | Cumple | Ola 3 · Alcance |  |
| P4 | Falta | — | Escribir reglas de cola, espera y fuera de horario |
| P6 | Parcial | Ola 3 · proveedor sin elegir dicho en prosa | Listarlo como decisión pendiente |
| T1 | Cumple | Ola 3 · CA-07 |  |
| T2 | Falta | — | Casos con entradas y salidas, incluidos errores |
| D1 | Falta | — | Elegir la herramienta de soporte y describir la integración |

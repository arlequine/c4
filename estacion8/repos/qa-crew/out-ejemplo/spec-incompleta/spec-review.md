# Spec review · spec-incompleta.md

**Nota (calculada por el código): D** · nota que propuso el LLM: D

- P1: Parcial sin supuesto escrito → cuenta como Falta
- P2: Parcial sin supuesto escrito → cuenta como Falta
- Falta el alcance (P2) o no hay aceptación observable (T1) → D

Es una intención, no una spec: no hay criterios observables ni reglas.

| Criterio | Estado | Evidencia | Corrección mínima |
|---|---|---|---|
| P1 | Parcial | Párrafo único: 'para que los clientes no se frustren' | Nombrar usuario y situación |
| P2 | Parcial | 'pasar con un humano cuando lo pidan' | Listar capacidades concretas de esta ronda |
| P3 | Falta | — | Agregar sección Fuera de alcance |
| P4 | Falta | — | Escribir reglas BR-XXX con las frases que disparan el escalamiento |
| P5 | Falta | — |  |
| P6 | Falta | — |  |
| T1 | Falta | — | Criterios con entrada y salida esperada |
| T2 | Falta | — | Tabla de casos con bordes (saludo + pedido) |
| T3 | Falta | — |  |
| T4 | N/A | No se declaró TDD |  |
| D1 | Falta | — | Indicar componente que cambia |
| D2 | Falta | — |  |
| D3 | N/A | — |  |
| D4 | Falta | — |  |

## Vacíos más graves

1. T1: no hay ningún resultado observable ('que suene amable' no se puede probar)
2. P4: no hay reglas que digan qué frases cuentan como pedir un humano
3. P3: no dice qué queda fuera (¿transferencia real? ¿tickets?)

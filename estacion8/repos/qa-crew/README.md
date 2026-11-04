# qa-crew — De la spec al código probado, con 5 etapas y 3 modelos (CrewAI)

Ejercicio **bonus** de la Clase 8 (Aseguramiento de Calidad) del programa AI for Developers 30X.

Es la cadena E6 → E7 → E8 en un solo flujo, sobre la app de [`qa-e2e`](../qa-e2e):

```
spec ─► 1 Revisor (Opus) ─► 2 Planificador (Opus) ─► 3 Pruebas (Haiku) ─► ROJO ─► 4 Desarrollo (Sonnet) ─► 5 Ejecutor (Opus) ─► VERDE + match
        evaluate-spec        create-implementation-plan  TDD o BDD por CA          desde el plan             unit + bdd + e2e
        nota por ola         paquete docs/tasks/          deben fallar primero      solo agent.ts             ◄── máx. 2 reintentos ──┘
```

| Etapa | Modelo | Skill | Qué hace | Qué decide el código, no el modelo |
|---|---|---|---|---|
| 1 · Revisor de spec | Opus | `evaluate-spec` (E6) | Califica **cada ola** con los 14 criterios | La nota A–D de cada ola. Pasan A y B; C y D vuelven a diseño |
| 2 · Planificador | Opus | `create-implementation-plan` (E6) | Convierte las olas A y B en `docs/tasks/` (manifiesto, milestones y una tarea por archivo); en las olas B escribe el supuesto en la tarea | Valida el paquete con el paso 6 de la skill: archivos, frontmatter, IDs, dependencias sin ciclos, cada CA en una tarea y el supuesto de cada ola B |
| 3 · Diseñador de pruebas | Haiku | `qa-testing` (E8) | Por cada CA decide **TDD** (Vitest, lógica pura) o **BDD** (Gherkin, lo que ve el usuario) y escribe la prueba con el ID del CA en el nombre | Cada CA tiene prueba y **todas fallan** antes del código |
| 4 · Desarrollador | Sonnet | — | Implementa las tareas **en el orden del plan**, solo en `demo-app/lib/agent.ts` | No puede tocar las pruebas (herramienta + huella de archivos) |
| 5 · Ejecutor | Opus | — | Corre unit, bdd y e2e y explica qué parte del cambio cubre cada CA | El veredicto por CA sale de los reportes JSON de Vitest y Playwright |

El crew **no hace commit**: deja `out/reporte.md` con la matriz CA → prueba → resultado → tarea → cambio, y el diff lo revisas tú.

## La spec: `specs/escalamiento.md`, tres olas

| Ola | Qué cubre | Nota esperada | Pruebas |
|---|---|---|---|
| 1 · Detección de la intención | Frases que cuentan como pedir un humano, mayúsculas, prioridad sobre el saludo, nombre (CA-01 a CA-04) | **A** | TDD (Vitest) |
| 2 · Experiencia en el chat | Respuesta visible con horario y nombre (CA-05, CA-06) | **B**: falta el caso del sábado, que se cierra con un supuesto escrito | BDD (Gherkin) |
| 3 · Transferencia real | Cola y tiempo de espera (CA-07) | **C**: sin reglas ni proveedor | — vuelve a diseño |

**La trampa a propósito (CA-03):** "Hola, quiero hablar con un humano". En `agent.ts` la regla del saludo
va primero; si la regla nueva queda después, CA-03 falla, el ejecutor lo detecta y regresa a desarrollo.

## Requisitos

- `qa-e2e` instalado (`npm install` en `qa-e2e/` y en `qa-e2e/demo-app/`) y Chromium de Playwright.
- Python 3.11–3.13 y [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
- Para el modo con modelos: `ANTHROPIC_API_KEY` (llave de API de console.anthropic.com; **no** es la suscripción de Claude Code).

## Correr

```bash
# Terminal 1 — la app bajo prueba (puerto 3000; apaga cualquier otra)
cd qa-e2e/demo-app && npm run dev

# Terminal 2
cd qa-crew
uv sync
uv run pytest -q                                   # 25 passed, sin modelos ni app
export ANTHROPIC_API_KEY=sk-ant-...                # o en .env (ver .env.example)

uv run crew --spec specs/escalamiento.md --pausar  # se detiene entre etapas (para clase)
uv run crew --spec specs/escalamiento.md           # de corrido
cat out/reporte.md out/spec-review.md
ls ../qa-e2e/docs/tasks                            # el plan que generó Opus
git -C ../qa-e2e diff                              # el cambio de Sonnet: lo revisas tú

uv run crew --reset                                # deja qa-e2e y out/ como estaban
```

Cambiar el modelo de una etapa: `QA_MODEL_REVISOR`, `QA_MODEL_PLAN`, `QA_MODEL_PRUEBAS`, `QA_MODEL_DEV`
o `QA_MODEL_EJECUTOR` (por ejemplo `export QA_MODEL_PLAN=anthropic/claude-sonnet-5-5`).
Otras opciones: `--max-reintentos N` (por defecto 2).

### Plan B: sin llave o si algo falla en vivo

```bash
uv run crew --spec specs/escalamiento.md --sin-llm --pausar
```

No se llama a ningún modelo: la revisión, el plan, las pruebas, los dos intentos de desarrollo y el match
salen de [`referencia/`](referencia), pero **las pruebas corren de verdad**: rojo en los 6 CA, intento 1 con
solo CA-03 en rojo e intento 2 en verde. [`out-ejemplo/`](out-ejemplo) tiene el reporte de esa corrida.

## Códigos de salida

| Código | Significado |
|---|---|
| 0 | VERDE |
| 3 | DETENIDO: ninguna ola tiene A o B |
| 1 | ABORTADO (plan inválido, CA sin prueba, prueba que pasa sin código, pruebas modificadas) o ROJO tras los reintentos |
| 2 | Falla de preparación (app apagada, falta llave, qa-e2e sucio → `--reset`) |

## Estructura

```
qa-crew/
├── src/qa_crew/
│   ├── main.py      # Flow: etapas, modelos por etapa, compuertas (router) y reporte
│   ├── gate.py      # nota por ola, CA por ola desde la spec, cobertura y veredicto por CA
│   ├── plan.py      # validación del paquete de create-implementation-plan
│   └── tools.py     # leer/escribir con rutas por rol; suites en lista blanca con reporte JSON
├── skills/          # evaluate-spec y create-implementation-plan (E6), qa-testing (E8)
├── specs/escalamiento.md
├── referencia/      # respuestas para --sin-llm
├── out-ejemplo/     # corrida grabada (plan B)
└── tests/           # pytest de compuertas, plan y guardrails
```

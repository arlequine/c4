# qa-crew — De la spec al E2E en verde con 4 agentes (CrewAI)

Ejercicio **bonus** de la Clase 8 (Aseguramiento de Calidad) del programa AI for Developers 30X.

Es el ciclo E6 → E7 → E8 en un solo flujo: un equipo de cuatro agentes toma una spec,
la evalúa, escribe los tests, implementa el cambio y corre la suite E2E sobre la app de
[`qa-e2e`](../qa-e2e). Lo importante no son los agentes: son los **guardrails** que
deciden por ellos.

```
spec ──► 1 Revisor de spec ──► 2 QA ──► 4 Ejecutor (ROJO) ──► 3 Desarrollo ──► 4 Ejecutor (VERDE)
         skill evaluate-spec    skill qa-testing   debe fallar     solo agent.ts     bdd + e2e + unit
         nota → la calcula      .feature + steps   si pasa: aborta no toca tests     exit code decide
         el código              existentes                         ◄──── máx. 2 reintentos ────┘
```

| Agente | Skill | Puede escribir | Guardrail |
|---|---|---|---|
| Revisor de spec | `evaluate-spec` (E6) | nada | La nota A–D la recalcula `gate.py` con las reglas de la skill. Si el LLM dice otra cosa, se reporta y manda el código. |
| QA | `qa-testing` (E8) | `tests/features/*.feature`, `steps/*.steps.ts` (no los existentes) | Sus escenarios **deben fallar** antes del cambio; si pasan, no prueban nada y el flujo aborta. |
| Desarrollo | — | solo `demo-app/lib/agent.ts` | Si los tests cambian después de que QA los escribió, el flujo aborta. |
| Ejecutor E2E | — | nada; solo corre `bdd`, `e2e` o `unit` | El veredicto sale del exit code registrado, no de lo que el agente diga. Si no corre una suite, la corre el flujo. |

El crew **no hace commit**: deja `out/reporte.md` con el diff y lo revisas tú.

## El caso: ESC-01 · Escalar a un asesor humano

Hoy, si en el chat escribes "Quiero hablar con una persona", el asistente responde con el
mensaje genérico. Hay dos specs:

- [`specs/spec-incompleta.md`](specs/spec-incompleta.md): una intención de dos líneas. El revisor la frena (nota **D**). Sin spec lista no se codea.
- [`specs/spec-lista.md`](specs/spec-lista.md): reglas BR-ESC-01..04 y criterios CA-01..04. Nota **A**.

**La trampa a propósito (CA-03):** "Hola, quiero hablar con un humano". En `agent.ts` la
regla del saludo va primero; si el desarrollo agrega la regla nueva al final, CA-03 falla,
el ejecutor lo detecta y el flujo regresa a desarrollo. Así se ve el loop en acción.

## Requisitos

- `qa-e2e` instalado (`npm install` en `qa-e2e/` y en `qa-e2e/demo-app/`) y Chromium de Playwright.
- Python 3.11–3.13 y [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
- Para el modo con LLM: `ANTHROPIC_API_KEY` (llave de API de console.anthropic.com; **no** es la suscripción de Claude Code).

## Correr

```bash
# Terminal 1 — la app bajo prueba (puerto 3000; apaga cualquier otra)
cd qa-e2e/demo-app && npm run dev

# Terminal 2
cd qa-crew
uv sync
export ANTHROPIC_API_KEY=sk-ant-...           # o cópialo a .env (ver .env.example)

uv run crew --spec specs/spec-incompleta.md   # se detiene en el revisor
uv run crew --spec specs/spec-lista.md        # rojo → código → verde
cat out/reporte.md
git -C ../qa-e2e diff                         # el diff lo revisas tú

uv run crew --reset                           # deja qa-e2e y out/ como estaban
```

Opciones: `--max-reintentos N` (por defecto 2) y `QA_MODEL` para cambiar el modelo
(por defecto `anthropic/claude-sonnet-5-5`; por ejemplo `anthropic/claude-haiku-5-5` es más barato).

### Plan B: sin llave o si el LLM falla en vivo

```bash
uv run crew --spec specs/spec-lista.md --sin-llm
```

Los agentes no se llaman: la revisión, el `.feature` y los dos intentos de desarrollo salen de
[`referencia/`](referencia), pero **las pruebas son reales** (rojo, intento 1 con CA-03 fallando,
intento 2 en verde). [`out-ejemplo/`](out-ejemplo) tiene el reporte de esa corrida.

## Códigos de salida

| Código | Significado |
|---|---|
| 0 | VERDE |
| 3 | DETENIDO por la spec (esperado con `spec-incompleta.md`) |
| 1 | ABORTADO o ROJO después de los reintentos |
| 2 | Falla de preparación (app apagada, falta llave, qa-e2e sucio → `--reset`) |

## Pruebas del propio crew

```bash
uv run pytest -q    # compuerta A–D y guardrails de las herramientas, sin LLM
```

## Estructura

```
qa-crew/
├── src/qa_crew/
│   ├── main.py      # Flow de CrewAI: agentes, compuertas (router) y reporte
│   ├── gate.py      # nota A–D de evaluate-spec calculada por código
│   └── tools.py     # leer/escribir con rutas permitidas, suites en lista blanca
├── skills/
│   ├── evaluate-spec/SKILL.md   # de la E6 (rework/estacion6)
│   └── qa-testing/SKILL.md      # copia de qa-e2e/.claude/skills
├── specs/           # spec-incompleta.md · spec-lista.md
├── referencia/      # respuestas para --sin-llm
├── out-ejemplo/     # corrida grabada (plan B)
└── tests/           # pytest
```

## Para llevarlo a tu proyecto

Cambia `QA_E2E_DIR`, las rutas permitidas (`QA_PERMITIDAS`, `DEV_PERMITIDAS` en `main.py`) y las
suites de `tools.py` por los comandos de tu repo. Mantén las tres reglas: la nota la calcula el
código, el test debe fallar primero y el veredicto es el exit code.

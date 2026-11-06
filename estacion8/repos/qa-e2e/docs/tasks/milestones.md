# FBK-01 · Milestones (olas)

Fuente: `docs/specs/FBK-01.md` v2 · Evaluación: `docs/specs/FBK-01-review.md` (A · A · B).
Una ola empieza solo cuando todas las tareas de la anterior están en **Done**. En Linear esto se hace con relaciones *blocked by*, que OpenSymphony respeta.

```text
Ola 1   TASK-001 ──► TASK-002
                         │
           ┌─────────────┼─────────────┐
Ola 2   TASK-003     TASK-004      TASK-005      (en paralelo)
           └─────────────┼─────────────┘
Ola 3                TASK-006
```

## Ola 1: Modelo y API de escritura

Objetivo: dominio, regla de un voto por mensaje y `POST /api/feedback`.

- TASK-001 Modelo Feedback, esquema zod y store en memoria
- TASK-002 POST /api/feedback (espera a TASK-001: la Ola 1 corre en dos pasos)

## Ola 2: UI, estadísticas y panel

Objetivo: tres frentes en paralelo que solo dependen de la Ola 1.

- TASK-003 Botones 👍/👎 y motivo en el chat
- TASK-004 computeStats y GET /api/feedback/stats
- TASK-005 Panel /admin/feedback (con `/stats` simulado)

## Ola 3: Flujo completo E2E + BDD

Objetivo: integración real y regresión completa.

- TASK-006 Calificar → aparece en el panel

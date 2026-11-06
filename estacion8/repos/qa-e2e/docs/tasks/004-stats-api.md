---
id: TASK-004
title: "FBK-01 · computeStats y GET /api/feedback/stats"
milestone: "Ola 2: UI, estadísticas y panel"
priority: 3
estimate: 2
blockedBy: [TASK-001, TASK-002]
blocks: [TASK-006]
areas: [feedback-api]
labels: [ola-2]
parent: null
---

## Summary

Calcular las estadísticas con una función pura y exponerlas en `GET /api/feedback/stats`.

## Scope

### In scope

- `demo-app/lib/feedback-stats.ts`: `computeStats(feedback[]) → FeedbackStats` (BR-FBK-04).
- `demo-app/app/api/feedback/stats/route.ts` (`GET`): `computeStats(listFeedback())`.

### Out of scope

- Cambios en `lib/feedback.ts` (TASK-001), salvo importar. Panel (TASK-005).

## Deliverables

- `demo-app/lib/feedback-stats.ts`
- `demo-app/app/api/feedback/stats/route.ts`

## Acceptance Criteria

- [ ] CA-09: 3 `up` y 1 `down` → `{ up: 3, down: 1, total: 4, satisfaction: 75 }`.
- [ ] CA-10: lista vacía → todo en 0 y `lastReasons: []`.
- [ ] CA-11: 7 motivos → los 5 más recientes por `updatedAt`, del más nuevo al más viejo, como `{ reason, at }`.
- [ ] CA-18: un motivo borrado por BR-FBK-02 no aparece en `lastReasons`.
- [ ] CA-17 (parte de esta tarea): tras dos `POST` del mismo `messageId`, `total` de `/stats` sube 1 y no 2.

## Test Plan

- Unitarias: `npm --prefix demo-app run test:unit` con CA-09..11 y CA-18 en `feedback.test.ts`.
- API: `tests/e2e/feedback-api.spec.ts` con CA-17 en diferencias.

## Context

- Contrato de `/stats` y regla de redondeo: spec §6, BR-FBK-04 y S-02.
- Spec: `docs/specs/FBK-01.md` (v2) y su evaluación `docs/specs/FBK-01-review.md`.
- Las pruebas de esta tarea ya existen en rojo (Fase 5, TDD). Tu trabajo es ponerlas en verde sin editarlas. Si una prueba está mal, repórtalo en el issue y no la cambies.
- Rama: `fbk-01/<ID-issue>`, que sale de `estacion8/orquestacion-opensymphony` con las olas anteriores ya integradas. Sin merge a `main` ni `push --force`.
- Puerto: no uses el 3000. Levanta la app con `npm --prefix demo-app run dev -- -p <puerto>` y corre Playwright con `BASE_URL=http://localhost:<puerto>`.

## Definition of Ready

- [x] Las reglas y supuestos vienen de `docs/specs/FBK-01.md` v2 (BR-FBK-01..05, S-01..S-06).
- [x] Los archivos a crear o tocar están listados en Deliverables.
- [x] Un agente puede empezar sin el chat: spec, contratos y comandos están referenciados.

## Notes

- `satisfaction` es `Math.round(up / total * 100)` y 0 si `total = 0`.

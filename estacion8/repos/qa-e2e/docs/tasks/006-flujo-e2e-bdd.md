---
id: TASK-006
title: "FBK-01 · Flujo completo E2E + BDD: calificar → aparece en el panel"
milestone: "Ola 3: Flujo completo E2E + BDD"
priority: 3
estimate: 2
blockedBy: [TASK-003, TASK-004, TASK-005]
blocks: []
areas: [qa]
labels: [ola-3]
parent: null
---

## Summary

Cerrar FBK-01 con la integración real: calificar en el chat y verlo en el panel, en E2E y en BDD en español, más la regresión completa en verde.

## Scope

### In scope

- `steps/feedback.steps.ts`: steps nuevos para `tests/features/feedback.feature`, reutilizando `HomePage` y `FeedbackPanelPage`.
- Ajustes a POM, si hacen falta, para el flujo integrado.

### Out of scope

- Cambios de producto en `demo-app`. Si algo falla por un bug de producto, se reporta en el issue de la tarea dueña.

## Deliverables

- `steps/feedback.steps.ts`
- Ajustes menores en `pages/HomePage.ts` y `pages/FeedbackPanelPage.ts`, si aplican.

## Acceptance Criteria

- [ ] CA-12 (real): el panel muestra los mismos valores que `GET /api/feedback/stats` en ese momento.
- [ ] CA-15: tras votar 👎 con "faltó el precio", `stat-down` sube 1 y el primer `reason-item` es "faltó el precio".
- [ ] `feedback.feature` pasa en el proyecto `bdd`.
- [ ] Regresión completa: 15 + N unitarias, todos los E2E `chromium` y todos los BDD en verde.

## Test Plan

- `npx bddgen && BASE_URL=http://localhost:<puerto> npx playwright test --project=chromium --project=bdd`
- `npm --prefix demo-app run test:unit`

## Context

- Los `.feature` y specs de esta tarea se escriben en la Fase 5 (en rojo). Esta tarea implementa los steps y el pegamento del POM.
- Las pruebas comparan diferencias o coherencia con `/stats`, nunca valores absolutos (R-01, S-06).
- Spec: `docs/specs/FBK-01.md` (v2) y su evaluación `docs/specs/FBK-01-review.md`.
- Las pruebas de esta tarea ya existen en rojo (Fase 5, TDD). Tu trabajo es ponerlas en verde sin editarlas. Si una prueba está mal, repórtalo en el issue y no la cambies.
- Rama: `fbk-01/<ID-issue>`, que sale de `estacion8/orquestacion-opensymphony` con las olas anteriores ya integradas. Sin merge a `main` ni `push --force`.
- Puerto: no uses el 3000. Levanta la app con `npm --prefix demo-app run dev -- -p <puerto>` y corre Playwright con `BASE_URL=http://localhost:<puerto>`.

## Definition of Ready

- [x] Las reglas y supuestos vienen de `docs/specs/FBK-01.md` v2 (BR-FBK-01..05, S-01..S-06).
- [x] Los archivos a crear o tocar están listados en Deliverables.
- [x] Un agente puede empezar sin el chat: spec, contratos y comandos están referenciados.

## Notes

- Es la única tarea de la Ola 3. Cuando pasa, FBK-01 está completa.

---
id: TASK-005
title: "FBK-01 · Panel /admin/feedback"
milestone: "Ola 2: UI, estadísticas y panel"
priority: 3
estimate: 2
blockedBy: [TASK-001, TASK-002]
blocks: [TASK-006]
areas: [feedback-panel]
labels: [ola-2]
parent: null
---

## Summary

Página `/admin/feedback` que lee `GET /api/feedback/stats` y muestra totales, % de satisfacción y últimos motivos, con estado vacío.

## Scope

### In scope

- `demo-app/app/admin/feedback/page.tsx` como **componente cliente** con `fetch` a `/api/feedback/stats` al cargar.
- Testids: `stat-up`, `stat-down`, `stat-total`, `stat-satisfaction` (con `%`), `reasons-list` > `reason-item`, y `empty-state` ("Aún no hay calificaciones").
- `pages/FeedbackPanelPage.ts` ya existe (Fase 5). El panel debe cumplir sus testids.

### Out of scope

- Implementar `/stats` (TASK-004). En esta ola el panel se prueba con `page.route` simulando el contrato.
- Autenticación (fuera de alcance de la spec).

## Deliverables

- `demo-app/app/admin/feedback/page.tsx`
- Ajustes en `pages/FeedbackPanelPage.ts`, solo si el DOM real lo exige (ya existe desde la Fase 5)

## Acceptance Criteria

- [ ] CA-14: con `/stats` simulado en `total: 0`, se ve `empty-state` y no existe `reasons-list`.
- [ ] CA-12 (con datos simulados): con `/stats` simulado `{ up: 3, down: 1, total: 4, satisfaction: 75, lastReasons: [2 items] }`, los `stat-*` muestran 3, 1, 4 y 75% y hay 2 `reason-item` en el mismo orden.

## Test Plan

- Pruebas ya escritas (Fase 5): los tests `@TASK-005` de `tests/e2e/feedback.spec.ts`, con `/stats` simulado vía `page.route`. El POM `pages/FeedbackPanelPage.ts` ya existe.
- Verificar: `BASE_URL=http://localhost:<puerto> npx playwright test --project=chromium --grep @TASK-005` → 2 en verde.
- La versión de CA-12 con datos reales es `@TASK-006`.

## Context

- Contrato: spec §6. Estilos: S-04.
- Spec: `docs/specs/FBK-01.md` (v2) y su evaluación `docs/specs/FBK-01-review.md`.
- Las pruebas de esta tarea ya existen en rojo (Fase 5, TDD). Tu trabajo es ponerlas en verde sin editarlas. Si una prueba está mal, repórtalo en el issue y no la cambies.
- Rama: `fbk-01/<ID-issue>`, que sale de `estacion8/orquestacion-opensymphony` con las olas anteriores ya integradas. Sin merge a `main` ni `push --force`.
- Puerto: no uses el 3000. Levanta la app con `npm --prefix demo-app run dev -- -p <puerto>` y corre Playwright con `BASE_URL=http://localhost:<puerto>`.

## Definition of Ready

- [x] Las reglas y supuestos vienen de `docs/specs/FBK-01.md` v2 (BR-FBK-01..05, S-01..S-06).
- [x] Los archivos a crear o tocar están listados en Deliverables.
- [x] Un agente puede empezar sin el chat: spec, contratos y comandos están referenciados.

## Notes

- Simular `/stats` permite trabajar esta tarea en paralelo con TASK-004 en la misma ola.

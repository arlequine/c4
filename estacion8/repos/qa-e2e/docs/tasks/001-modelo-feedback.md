---
id: TASK-001
title: "FBK-01 · Modelo Feedback, esquema zod y store en memoria"
milestone: "Ola 1: Modelo y API de escritura"
priority: 2
estimate: 2
blockedBy: []
blocks: [TASK-002, TASK-003, TASK-004, TASK-005]
areas: [feedback-api]
labels: [ola-1]
parent: null
---

## Summary

Crear el dominio de FBK-01 en `demo-app/lib/feedback.ts`: tipos, esquema zod de entrada y el store en memoria con la regla de un voto vigente por mensaje.

## Scope

### In scope

- Agregar `zod` a `demo-app/package.json`.
- Tipos `Feedback` (`messageId`, `rating`, `reason?`, `createdAt`, `updatedAt`) y `FeedbackInput`.
- Esquema zod: `messageId` uuid, `rating` `"up" | "down"`, `reason` de 1 a 200 caracteres y solo con `down`.
- Store `Map<messageId, Feedback>` en `globalThis`, con `saveFeedback(input) → { replaced: boolean }` (upsert, BR-FBK-01; borra el motivo al pasar a `up`, BR-FBK-02) y `listFeedback()`.

### Out of scope

- Rutas HTTP (TASK-002), estadísticas (TASK-004) y UI.

## Deliverables

- `demo-app/lib/feedback.ts`
- `demo-app/package.json` y `package-lock.json` con `zod`

## Acceptance Criteria

- [ ] CA-06: `rating: "meh"` no pasa el esquema.
- [ ] CA-07: `reason` de 201 caracteres no pasa el esquema.
- [ ] CA-08: `reason` con `rating: "up"` no pasa el esquema.
- [ ] CA-19: `messageId: "abc"` no pasa el esquema.
- [ ] BR-FBK-01: dos `saveFeedback` del mismo `messageId` dejan un solo registro; el segundo devuelve `replaced: true`.
- [ ] CA-18 / BR-FBK-02: después de `down` con motivo y luego `up` del mismo `messageId`, el registro no tiene `reason`.

## Test Plan

- `npm --prefix demo-app run test:unit`: `demo-app/__tests__/feedback.test.ts`, casos de esquema y store, en verde.
- Regresión: los 15 tests de `agent.test.ts` siguen en verde.
- `npx --prefix demo-app tsc --noEmit -p demo-app` sin errores.

## Context

- Contratos y modelo: spec §6. Reglas: spec §4.
- Spec: `docs/specs/FBK-01.md` (v2) y su evaluación `docs/specs/FBK-01-review.md`.
- Las pruebas de esta tarea ya existen en rojo (Fase 5, TDD). Tu trabajo es ponerlas en verde sin editarlas. Si una prueba está mal, repórtalo en el issue y no la cambies.
- Rama: `fbk-01/<ID-issue>`, que sale de `estacion8/orquestacion-opensymphony` con las olas anteriores ya integradas. Sin merge a `main` ni `push --force`.
- Puerto: no uses el 3000. Levanta la app con `npm --prefix demo-app run dev -- -p <puerto>` y corre Playwright con `BASE_URL=http://localhost:<puerto>`.

## Definition of Ready

- [x] Las reglas y supuestos vienen de `docs/specs/FBK-01.md` v2 (BR-FBK-01..05, S-01..S-06).
- [x] Los archivos a crear o tocar están listados en Deliverables.
- [x] Un agente puede empezar sin el chat: spec, contratos y comandos están referenciados.

## Notes

- Exporta también una función para vaciar el store, solo para las pruebas unitarias (`resetFeedbackStore()`). No la expongas por HTTP.

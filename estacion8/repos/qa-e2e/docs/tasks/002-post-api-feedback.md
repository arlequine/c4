---
id: TASK-002
title: "FBK-01 · POST /api/feedback"
milestone: "Ola 1: Modelo y API de escritura"
priority: 2
estimate: 1
blockedBy: [TASK-001]
blocks: [TASK-003, TASK-004, TASK-005]
areas: [feedback-api]
labels: [ola-1]
parent: null
---

## Summary

Exponer `POST /api/feedback` con el contrato de la spec, usando el esquema y el store de TASK-001.

## Scope

### In scope

- `demo-app/app/api/feedback/route.ts` (`POST`): valida con el esquema zod y guarda con `saveFeedback`.
- Respuestas: `201 { ok: true, replaced: false }`, `200 { ok: true, replaced: true }`, `400 { error }` (también con JSON inválido).

### Out of scope

- `GET /api/feedback/stats` (TASK-004). Cambios en `/api/chat`.

## Deliverables

- `demo-app/app/api/feedback/route.ts`

## Acceptance Criteria

- [ ] CA-05: primer voto válido → `201 { ok: true, replaced: false }`.
- [ ] CA-06 / CA-07 / CA-08 / CA-19 por HTTP → `400 { error }` y nada guardado.
- [ ] CA-17 (parte de esta tarea): segundo `POST` del mismo `messageId` → `200 { ok: true, replaced: true }`.

## Test Plan

- Pruebas ya escritas (Fase 5): `tests/api/feedback-api.spec.ts`, con el builder `fixtures/feedback-builders.ts`.
- Verificar: `BASE_URL=http://localhost:<puerto> npx playwright test --project=api --grep @TASK-002` → todo en verde.
- Regresión: `BASE_URL=http://localhost:<puerto> npx playwright test --project=chromium --project=bdd --grep-invert "@TASK-"` (los 4 E2E + 4 BDD originales).

## Context

- Patrón a seguir: `demo-app/app/api/chat/route.ts` (`NextRequest`, `NextResponse.json`, `400` con `{ error }`).
- Spec: `docs/specs/FBK-01.md` (v2) y su evaluación `docs/specs/FBK-01-review.md`.
- Las pruebas de esta tarea ya existen en rojo (Fase 5, TDD). Tu trabajo es ponerlas en verde sin editarlas. Si una prueba está mal, repórtalo en el issue y no la cambies.
- Rama: `fbk-01/<ID-issue>`, que sale de `estacion8/orquestacion-opensymphony` con las olas anteriores ya integradas. Sin merge a `main` ni `push --force`.
- Puerto: no uses el 3000. Levanta la app con `npm --prefix demo-app run dev -- -p <puerto>` y corre Playwright con `BASE_URL=http://localhost:<puerto>`.

## Definition of Ready

- [x] Las reglas y supuestos vienen de `docs/specs/FBK-01.md` v2 (BR-FBK-01..05, S-01..S-06).
- [x] Los archivos a crear o tocar están listados en Deliverables.
- [x] Un agente puede empezar sin el chat: spec, contratos y comandos están referenciados.

## Notes

- Dentro de la Ola 1, esta tarea espera a TASK-001 porque importa sus tipos. La Ola 1 corre en dos pasos.

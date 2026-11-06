---
id: TASK-003
title: "FBK-01 · Botones 👍/👎 y motivo en cada respuesta del chat"
milestone: "Ola 2: UI, estadísticas y panel"
priority: 3
estimate: 3
blockedBy: [TASK-001, TASK-002]
blocks: [TASK-006]
areas: [feedback-ui]
labels: [ola-2]
parent: null
---

## Summary

Que cada respuesta del asistente tenga su `messageId`, botones 👍/👎 y, con 👎, el campo de motivo, todo enviado a `POST /api/feedback`.

## Scope

### In scope

- `demo-app/app/page.tsx`: `messageId` con `crypto.randomUUID()` al recibir cada respuesta (RF-06). Botones con `aria-label` "Me sirvió" / "No me sirvió", `aria-pressed` y testids `feedback-up` / `feedback-down`.
- Con 👎: `feedback-reason` (`maxLength=200`, placeholder "¿Qué faltó?") y `feedback-reason-submit` ("Enviar motivo").
- Cambio de voto (BR-FBK-01) y clic en el botón activo sin efecto (BR-FBK-05).
- `pages/HomePage.ts`: métodos `rateLatest(up|down)`, `submitReason(text)` y locators de los botones.

### Out of scope

- Cambiar el contrato de `/api/chat`. Panel de admin.

## Deliverables

- `demo-app/app/page.tsx`
- `pages/HomePage.ts` (solo métodos y locators nuevos)

## Acceptance Criteria

- [ ] CA-01: cada `agent-message` muestra "Me sirvió" y "No me sirvió".
- [ ] CA-02: clic en 👍 → `aria-pressed="true"` y `POST /api/feedback` con `rating: "up"`.
- [ ] CA-03: clic en 👎 → aparecen el campo vacío y "Enviar motivo".
- [ ] CA-04: el campo conserva 200 de 201 caracteres.
- [ ] CA-13: calificar la segunda respuesta envía el `messageId` de la segunda.
- [ ] CA-16: de 👍 a 👎 → `aria-pressed` se invierte y aparece el motivo.
- [ ] CA-20: clic en el botón activo → ningún `POST`.

## Test Plan

- `tests/e2e/feedback.spec.ts`, casos CA-01..04, CA-13, CA-16 y CA-20, con `page.waitForRequest` para los `POST`:
  `BASE_URL=http://localhost:<puerto> npx playwright test tests/e2e/feedback.spec.ts --project=chromium`.
- Regresión: los 4 E2E y 4 BDD existentes en verde. Los botones no deben romper `latestAgentMessage.textContent()` en `HomePage`.

## Context

- Render de mensajes: `demo-app/app/page.tsx` (`data-testid="agent-message"`, hoy con `key={i}`).
- Estilos: S-04, reutilizar la paleta en línea de `page.tsx`.
- Spec: `docs/specs/FBK-01.md` (v2) y su evaluación `docs/specs/FBK-01-review.md`.
- Las pruebas de esta tarea ya existen en rojo (Fase 5, TDD). Tu trabajo es ponerlas en verde sin editarlas. Si una prueba está mal, repórtalo en el issue y no la cambies.
- Rama: `fbk-01/<ID-issue>`, que sale de `estacion8/orquestacion-opensymphony` con las olas anteriores ya integradas. Sin merge a `main` ni `push --force`.
- Puerto: no uses el 3000. Levanta la app con `npm --prefix demo-app run dev -- -p <puerto>` y corre Playwright con `BASE_URL=http://localhost:<puerto>`.

## Definition of Ready

- [x] Las reglas y supuestos vienen de `docs/specs/FBK-01.md` v2 (BR-FBK-01..05, S-01..S-06).
- [x] Los archivos a crear o tocar están listados en Deliverables.
- [x] Un agente puede empezar sin el chat: spec, contratos y comandos están referenciados.

## Notes

- **Ojo con la regresión:** el step "la respuesta del agente menciona…" lee `textContent` de `agent-message`. Pon los botones en un contenedor hermano o usa solo emojis sin texto visible, para no ensuciar ese texto.

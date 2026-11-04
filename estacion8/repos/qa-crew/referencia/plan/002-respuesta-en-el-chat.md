---
id: TASK-002
title: Mostrar en el chat la respuesta de escalamiento con horario y nombre
milestone: "M2: Experiencia en el chat"
priority: 3
estimate: 1
blockedBy: [TASK-001]
blocks: []
areas:
  - ola-2
parent: null
---

## Summary

Que la respuesta de escalamiento que ve el usuario en el chat incluya el horario de atención y su nombre si ya lo dijo.

## Scope

### In scope

- Incluir el horario en el texto de escalamiento (BR-ESC-05).
- Mencionar el nombre conocido en la respuesta visible (BR-ESC-06).

### Out of scope

- Horario dinámico según la hora o el día.
- Cambios en la UI de `app/page.tsx`.

## Deliverables

- Texto de la respuesta de escalamiento en `demo-app/lib/agent.ts`.

## Acceptance Criteria

- [ ] CA-05: en una conversación nueva, al enviar `Quiero hablar con una persona`, la respuesta del agente menciona `asesor humano` y `lunes a viernes de 8:00 AM a 6:00 PM`.
- [ ] CA-06: tras enviar `Mi nombre es Ana`, al enviar `Quiero hablar con un asesor`, la respuesta menciona `asesor humano` y `Ana`.

## Test Plan

- CA-05 y CA-06 son lo que el usuario ve en el chat: BDD (Gherkin) en `tests/features/escalamiento.feature`, con los steps de `steps/asistente.steps.ts`.
- `npm run test:bdd` con `demo-app` en `http://localhost:3000`.

## Context

- Depende de TASK-001 (la regla de escalamiento).
- Spec: `qa-crew/specs/escalamiento.md`, Ola 2.

## Definition of Ready

- [x] Hidden assumptions from prior discussion are written down.
- [x] Required files, docs, and dependencies are explicitly referenced.
- [x] A coding agent could begin execution without additional planning context.

Supuesto: El horario del escalamiento es fijo, lunes a viernes de 8:00 AM a 6:00 PM, y no depende de la hora ni del día en que se pide. (Pendiente de aprobación; ola-2 tiene nota B.)

## Notes

Si negocio decide un horario de sábado, se abre una tarea nueva.

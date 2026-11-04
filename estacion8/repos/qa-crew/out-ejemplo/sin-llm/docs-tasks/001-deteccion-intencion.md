---
id: TASK-001
title: Detectar la intención de hablar con un asesor humano
milestone: "M1: Detección de la intención"
priority: 2
estimate: 2
blockedBy: []
blocks: [TASK-002]
areas:
  - ola-1
parent: null
---

## Summary

Agregar a `generateResponse()` una regla que reconozca cuando el usuario pide hablar con una persona y responda con el escalamiento, con prioridad sobre el saludo.

## Scope

### In scope

- Reconocer las frases de BR-ESC-01, sin importar mayúsculas.
- Responder con el texto `asesor humano` (BR-ESC-02).
- Anteponer `Entendido, <Nombre>.` si `extractName` encuentra el nombre (BR-ESC-03).
- Evaluar la regla antes del saludo (BR-ESC-04).

### Out of scope

- Transferencia real, colas o tickets (ola-3).
- Cambios en la interfaz.

## Deliverables

- Regla nueva en `demo-app/lib/agent.ts`.

## Acceptance Criteria

- [ ] CA-01: con historial vacío, `Quiero hablar con una persona` → la respuesta contiene `asesor humano`.
- [ ] CA-02: `QUIERO HABLAR CON UN ASESOR`, `¿Me pasas con un humano?` y `Necesito un agente real` → las tres contienen `asesor humano`.
- [ ] CA-03: `Hola, quiero hablar con un humano` → contiene `asesor humano` y no es el saludo.
- [ ] CA-04: con `Mi nombre es Ana` en el historial, `Quiero hablar con un asesor` → empieza con `Entendido, Ana.`
- [ ] Regresión: `Hola` sigue devolviendo el saludo y la pregunta de horarios sigue devolviendo los horarios.

## Test Plan

- CA-01 a CA-04 son lógica pura de `generateResponse()`: unitarias con Vitest (TDD) en `demo-app/__tests__/escalamiento.test.ts`.
- `npm --prefix demo-app run test:unit` (deben fallar antes del cambio y pasar después, junto con los 15 existentes).

## Context

- `qa-e2e/demo-app/lib/agent.ts`: `generateResponse()` evalúa reglas en orden; el saludo está antes que los horarios.
- Spec: `qa-crew/specs/escalamiento.md`, Ola 1.

## Definition of Ready

- [x] Hidden assumptions from prior discussion are written down.
- [x] Required files, docs, and dependencies are explicitly referenced.
- [x] A coding agent could begin execution without additional planning context.

## Notes

La trampa: si la regla se agrega después del saludo, CA-03 falla.

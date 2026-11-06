---
id: TASK-001
title: Detectar la intención de hablar con un asesor humano en generateResponse()
milestone: "M1: Ola 1 · Detección de la intención"
priority: 2
estimate: 2
blockedBy: []
blocks:
  - TASK-002
areas:
  - ola-1
parent: null
---

## Summary

Hacer que `generateResponse(historial, mensaje)` en `qa-e2e/demo-app/lib/agent.ts`
reconozca cuándo el usuario pide hablar con una persona y responda con un mensaje de
escalamiento que contiene `asesor humano`, con prioridad sobre el saludo y
personalizado con `Entendido, <Nombre>.` si el nombre se conoce. Hoy esos mensajes
caen en la respuesta genérica ("Gracias por tu mensaje. He recibido tu consulta…").

## Scope

### In scope

- Escribir primero (TDD) las pruebas unitarias Vitest de CA-01 a CA-04 y de los casos borde, y verlas fallar.
- Añadir en `generateResponse()` una rama de escalamiento que implemente las reglas de negocio:
  - **BR-ESC-01:** la intención se reconoce cuando el mensaje pide hablar, comunicarse o "pasar" con una persona, un humano, un asesor o un agente real, o menciona "asesor humano" / "agente humano". Mayúsculas y minúsculas dan igual.
  - **BR-ESC-02:** la respuesta de escalamiento contiene el texto exacto `asesor humano`.
  - **BR-ESC-03:** si se conoce el nombre (regla actual de `extractName`), la respuesta empieza con `Entendido, <Nombre>.`
  - **BR-ESC-04:** el escalamiento tiene prioridad sobre el saludo.
- Mantener verdes los casos borde: `Hola` solo sigue devolviendo el saludo; `¿Cuáles son sus horarios de atención?` sigue devolviendo los horarios.

### Out of scope

- Mostrar el horario de atención en la respuesta de escalamiento y pruebas BDD en navegador (TASK-002, Ola 2).
- Transferencia real a una cola de asesores / tiempos de espera (Ola 3, no aprobada).
- Cambios de interfaz (botones, pantallas) y cambios en el contrato de `POST /api/chat` (sigue devolviendo `{ response }`; solo cambia el texto).
- Idiomas distintos al español.
- Nuevos datos personales: el nombre se obtiene del historial con `extractName` existente.

## Deliverables

- `qa-e2e/demo-app/lib/agent.ts`: nueva detección de intención de escalamiento (p. ej. función exportada `wantsHuman(message: string): boolean` o regex equivalente) y nueva rama en `generateResponse()` ubicada **antes** de la rama de saludo.
- `qa-e2e/demo-app/__tests__/agent.test.ts` (o un archivo nuevo `qa-e2e/demo-app/__tests__/escalamiento.test.ts`): pruebas Vitest cuyo nombre incluye el ID del CA (`CA-01`, `CA-02`, `CA-03`, `CA-04`).

## Acceptance Criteria

Sobre `generateResponse(historial, mensaje)`:

- [ ] **CA-01:** Historial vacío · Mensaje `Quiero hablar con una persona` → la respuesta contiene `asesor humano`.
- [ ] **CA-02:** Historial vacío · Mensajes `QUIERO HABLAR CON UN ASESOR`, `¿Me pasas con un humano?`, `Necesito un agente real` → las tres respuestas contienen `asesor humano`.
- [ ] **CA-03:** Historial vacío · Mensaje `Hola, quiero hablar con un humano` → la respuesta contiene `asesor humano` y no es el saludo.
- [ ] **CA-04:** Historial `Mi nombre es Ana` · Mensaje `Quiero hablar con un asesor` → la respuesta empieza con `Entendido, Ana.`
- [ ] Casos borde: `Hola` solo sigue devolviendo el saludo (`¡Hola! Soy el asistente virtual…`); `¿Cuáles son sus horarios de atención?` sigue devolviendo los horarios.
- [ ] Regresión: los 15 unitarios, 4 E2E y 4 escenarios BDD existentes siguen en verde.

## Test Plan

TDD declarado: escribir las pruebas antes del código y comprobar que fallan primero.

- **CA-01 → unitaria (Vitest)**, `it('CA-01 …')` en `qa-e2e/demo-app/__tests__/`. Comando: `npm --prefix demo-app run test:unit`
- **CA-02 → unitaria (Vitest)**, `it('CA-02 …')` con los tres mensajes (o `it.each`, manteniendo `CA-02` en el nombre). Comando: `npm --prefix demo-app run test:unit`
- **CA-03 → unitaria (Vitest)**, `it('CA-03 …')`: `toContain('asesor humano')` y `not.toContain('asistente virtual')`. Comando: `npm --prefix demo-app run test:unit`
- **CA-04 → unitaria (Vitest)**, `it('CA-04 …')` con historial `[{ role: 'user', content: 'Mi nombre es Ana' }]`: `expect(response.startsWith('Entendido, Ana.')).toBe(true)`. Comando: `npm --prefix demo-app run test:unit`
- Casos borde → unitarias (Vitest) (las existentes "responde a saludos…" y "proporciona horarios de atención" ya los cubren; no deben romperse). Comando: `npm --prefix demo-app run test:unit`
- Regresión completa: `npm --prefix demo-app run test:unit` (15 existentes + nuevos) y `npm run test:bdd` con `demo-app` levantada en `http://localhost:3000` (4 escenarios existentes), más la suite E2E existente (4 pruebas).

## Context

- Código a modificar: `qa-e2e/demo-app/lib/agent.ts`. Estado actual relevante:
  - `extractName(messages)` busca en todos los mensajes `user` el patrón `/(?:me llamo|mi nombre es|soy)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+)/i` y devuelve el nombre o `null`. Reutilizarlo tal cual (BR-ESC-03).
  - `generateResponse(history, userMessage)` construye `fullHistory = [...history, { role: 'user', content: userMessage }]`, calcula `name` y `topics`, y evalúa en este orden: recall (`/recuerdas|cómo me llamo|qué necesitaba/i`) → saludo (`/^(hola|buenos días|buenas)/i` sobre el mensaje recortado) → horarios (`/horario|atención/i`) → servicios → soporte técnico (ya usa el patrón `Entendido, ${name}. `) → genérica.
  - Por eso `Hola, quiero hablar con un humano` hoy devuelve el saludo: la rama de escalamiento debe ir **antes** de la de saludo (BR-ESC-04). Colocarla también antes de horarios evita que menciones de "atención" la desvíen; asegurarse de que `¿Cuáles son sus horarios de atención?` NO se detecte como escalamiento.
- Pruebas existentes: `qa-e2e/demo-app/__tests__/agent.test.ts` (importa `generateResponse, extractName, extractTopics, type Message` desde `../lib/agent`).
- Spec: "ESC · Escalar a un asesor humano", sección Ola 1 y secciones comunes 3–5.
- Bloquea a TASK-002 (Ola 2 reutiliza esta rama y le añade el horario).

## Definition of Ready

- [x] Hidden assumptions from prior discussion are written down.
- [x] Required files, docs, and dependencies are explicitly referenced.
- [x] A coding agent could begin execution without additional planning context.

## Notes

- Ola con nota A: no hay supuestos abiertos.
- Ojo con la detección de BR-ESC-01: `Necesito un agente real` no usa "hablar/comunicarse/pasar", así que debe reconocerse por la mención de "agente real"; `¿Me pasas con un humano?` usa "pasas" (conjugación de "pasar"). Cubrir verbos conjugados (hablar, comunicar(me|se), pasa(s|r|me)) seguidos de "con" + persona/humano/asesor/agente, más las menciones directas "asesor humano", "agente humano" y "agente real". Flag `i` para mayúsculas.
- Ejemplo de respuesta válida (el texto exacto es libre salvo lo exigido): sin nombre `Te comunicaré con un asesor humano.`; con nombre `Entendido, Ana. Te comunicaré con un asesor humano.`
- `generateResponse()` debe seguir siendo pura y determinista.

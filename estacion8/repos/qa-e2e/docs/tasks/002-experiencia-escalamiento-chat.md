---
id: TASK-002
title: Mostrar en el chat el escalamiento con horario fijo y nombre del usuario
milestone: "M2: Ola 2 · Experiencia en el chat"
priority: 2
estimate: 3
blockedBy:
  - TASK-001
blocks: []
areas:
  - ola-2
parent: null
---

## Summary

Extender la respuesta de escalamiento creada en TASK-001 para que, en el chat de
`qa-e2e/demo-app` (navegador), quien pide una persona vea que lo van a comunicar con
un `asesor humano`, el horario fijo `lunes a viernes de 8:00 AM a 6:00 PM` y su nombre
si lo dijo antes. Se verifica con escenarios BDD (playwright-bdd) y un unitario para el
caso borde del sábado.

## Scope

### In scope

- Escribir primero (TDD) los escenarios BDD de CA-05 y CA-06 y la prueba unitaria del caso borde del sábado, y verlos fallar.
- Ajustar el texto de escalamiento en `generateResponse()` para cumplir:
  - **BR-ESC-05:** la respuesta visible incluye el horario de atención.
  - **BR-ESC-06:** si el usuario dijo su nombre antes en la conversación, la respuesta visible lo menciona.
  - **BR-ESC-07:** el horario que muestra el escalamiento es fijo, lunes a viernes de 8:00 AM a 6:00 PM, y no depende de la hora ni del día en que se pide (incluido el sábado).
- Mantener las reglas de la Ola 1 (BR-ESC-01 a BR-ESC-04) y sus pruebas CA-01 a CA-04 en verde.

### Out of scope

- Transferencia real a una cola, tiempos de espera o comportamiento fuera de horario (Ola 3, no aprobada).
- Cambios de interfaz: sin botones ni pantallas nuevas; el texto se muestra en la burbuja de agente existente (`[data-testid="agent-message"]`).
- Cambios en el contrato de `POST /api/chat` (sigue devolviendo `{ response }`).
- Modificar la respuesta de la rama de horarios existente (que sí menciona sábados).
- Idiomas distintos al español.

## Deliverables

- `qa-e2e/demo-app/lib/agent.ts`: texto de escalamiento que incluye `asesor humano` y `lunes a viernes de 8:00 AM a 6:00 PM`, sin mencionar `sábados`, y con el nombre si se conoce (manteniendo el prefijo `Entendido, <Nombre>.` de BR-ESC-03).
- Nuevo archivo `qa-e2e/tests/features/escalamiento.feature` con escenarios cuyo nombre incluye `CA-05` y `CA-06`, reutilizando solo los steps de `qa-e2e/steps/asistente.steps.ts`.
- Prueba unitaria Vitest del caso borde del sábado en `qa-e2e/demo-app/__tests__/` (nombre con `CA-05`, p. ej. `CA-05 borde sábado …`).

## Acceptance Criteria

En el chat, con el navegador:

- [ ] **CA-05:** Dado conversación nueva · Cuando el usuario envía `Quiero hablar con una persona` · Entonces la respuesta del agente menciona `asesor humano` y `lunes a viernes de 8:00 AM a 6:00 PM`.
- [ ] **CA-06:** Dado que antes envió `Mi nombre es Ana` · Cuando el usuario envía `Quiero hablar con un asesor` · Entonces la respuesta del agente menciona `asesor humano` y `Ana`.
- [ ] Caso borde: un sábado a las 10:00 AM (reloj del sistema fijado), `Quiero hablar con una persona` devuelve la misma respuesta que CA-05: menciona `asesor humano` y `lunes a viernes de 8:00 AM a 6:00 PM`, y no menciona `sábados`.
- [ ] Regresión: CA-01 a CA-04 de la Ola 1, más los 15 unitarios, 4 E2E y 4 escenarios BDD existentes siguen en verde.

## Test Plan

TDD declarado: escribir las pruebas antes del código y comprobar que fallan primero.

- **CA-05 → BDD (Gherkin)** en `qa-e2e/tests/features/escalamiento.feature`. Comando: `npm run test:bdd` (con `demo-app` en `http://localhost:3000`). Escenario sugerido:
  ```gherkin
  Feature: Escalar a un asesor humano

    Background:
      Given que el usuario está en la página principal

    Scenario: CA-05 El usuario que pide una persona ve el asesor humano y el horario
      When el usuario envía el mensaje "Quiero hablar con una persona"
      Then la respuesta del agente menciona "asesor humano"
      And la respuesta del agente menciona "lunes a viernes de 8:00 AM a 6:00 PM"
  ```
- **CA-06 → BDD (Gherkin)** en el mismo feature. Comando: `npm run test:bdd` (con `demo-app` en `http://localhost:3000`). Escenario sugerido:
  ```gherkin
    Scenario: CA-06 El escalamiento menciona el nombre que el usuario dijo antes
      When el usuario envía el mensaje "Mi nombre es Ana"
      And el agente responde
      When el usuario envía el mensaje "Quiero hablar con un asesor"
      Then la respuesta del agente menciona "asesor humano"
      And la respuesta del agente menciona "Ana"
  ```
- **Caso borde sábado (CA-05) → unitaria (Vitest)**: con `vi.useFakeTimers()` y `vi.setSystemTime(new Date(2025, 0, 4, 10, 0))` (sábado 4 de enero de 2025, 10:00 AM), `generateResponse([], 'Quiero hablar con una persona')` contiene `asesor humano` y `lunes a viernes de 8:00 AM a 6:00 PM`, no contiene `sábados`, y es igual a la respuesta obtenida con un reloj en día laborable. Restaurar con `vi.useRealTimers()`. Comando: `npm --prefix demo-app run test:unit`
- Regresión completa: `npm --prefix demo-app run test:unit`, `npm run test:bdd` (con `demo-app` en `http://localhost:3000`) y la suite E2E existente.

## Context

- Código a modificar: `qa-e2e/demo-app/lib/agent.ts`, rama de escalamiento añadida en TASK-001 (va antes de la de saludo dentro de `generateResponse()`). El nombre se obtiene con `extractName(fullHistory)`, que ya busca `me llamo|mi nombre es|soy` en todos los mensajes `user` del historial.
- La rama de horarios existente devuelve `Nuestros horarios de atención son de lunes a viernes de 8:00 AM a 6:00 PM, y sábados de 9:00 AM a 1:00 PM.` — **no** reutilizar ese texto en el escalamiento porque menciona `sábados` (rompería el caso borde). Escribir el horario fijo como literal, sin `Date`.
- Steps disponibles en `qa-e2e/steps/asistente.steps.ts` (no crear steps nuevos): `que el usuario está en la página principal`, `el usuario envía el mensaje {string}`, `el agente responde`, `la respuesta del agente menciona {string}` (compara en minúsculas con `toContain` sobre el último `[data-testid="agent-message"]`), entre otros.
- Feature existente de referencia: `qa-e2e/tests/features/asistente.feature` (escenario "El agente recuerda el contexto de la conversación" usa el mismo patrón que CA-06).
- Page Object: `qa-e2e/pages/HomePage.ts`.
- Spec: "ESC · Escalar a un asesor humano", sección Ola 2 y secciones comunes 3–5.
- Bloqueada por TASK-001 (necesita la detección de intención y la rama de escalamiento).

## Definition of Ready

- [x] Hidden assumptions from prior discussion are written down.
- [x] Required files, docs, and dependencies are explicitly referenced.
- [x] A coding agent could begin execution without additional planning context.

## Notes

- Ola con nota A: no hay supuestos abiertos.
- El caso borde del sábado se prueba en unitario porque la respuesta se genera en el servidor con una función pura; fijar el reloj del navegador no afectaría al servidor. Lo que importa es que el texto no dependa de la fecha.
- Ejemplo de respuesta válida: `Entendido, Ana. Te comunicaré con un asesor humano. Nuestro horario de atención es de lunes a viernes de 8:00 AM a 6:00 PM.` (sin nombre, omitir `Entendido, Ana. `).
- Verificar que la prueba CA-04 (`empieza con "Entendido, Ana."`) sigue pasando tras el cambio de texto.

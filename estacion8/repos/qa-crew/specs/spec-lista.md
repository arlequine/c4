# ESC-01 · Escalar a un asesor humano

Estado: lista para revisión · Ola única: `demo-app` (asistente del chat)

## 1. Problema y usuario

Quien usa el chat de soporte y no consigue lo que necesita con el asistente
escribe "quiero hablar con una persona". Hoy el asistente responde con el
mensaje genérico ("Gracias por tu mensaje. He recibido tu consulta…") y el
usuario no sabe cómo llegar a alguien. Es la queja más frecuente en las
evaluaciones Persona + Juez (Carlos y Pedro reprueban por esto).

Usuario: cliente final del chat de `qa-e2e/demo-app`.

## 2. Alcance (esta ronda)

- El asistente detecta cuando el usuario pide hablar con una persona.
- Responde que lo comunica con un asesor humano e informa el horario de
  atención.
- Si el usuario ya dijo su nombre en la conversación, lo usa en la respuesta.

## 3. Fuera de alcance

- Transferencia real a un humano, colas o tickets.
- Respuestas distintas según la hora actual (no se lee el reloj).
- Cambios en la interfaz (sin botones nuevos).
- Idiomas distintos al español.

## 4. Reglas de negocio

- **BR-ESC-01:** la intención se reconoce cuando el mensaje pide hablar,
  comunicarse o "pasar" con una persona, un humano, un asesor o un agente
  real, o menciona "asesor humano" / "agente humano". Mayúsculas y minúsculas
  dan igual.
- **BR-ESC-02:** la respuesta contiene el texto exacto `asesor humano` y el
  horario `lunes a viernes de 8:00 AM a 6:00 PM`.
- **BR-ESC-03:** si se conoce el nombre (regla actual de `extractName`), la
  respuesta empieza con `Entendido, <Nombre>.`
- **BR-ESC-04:** la regla de escalamiento tiene prioridad sobre el saludo: un
  mensaje que empieza con "Hola" y pide un humano se escala.

## 5. Criterios de aceptación

| ID | Dado | Cuando el usuario envía | Entonces la respuesta |
|---|---|---|---|
| CA-01 | Conversación nueva | `Quiero hablar con una persona` | menciona `asesor humano` y `lunes a viernes de 8:00 AM a 6:00 PM` |
| CA-02 | Antes envió `Mi nombre es Ana` | `Quiero hablar con un asesor` | menciona `Ana` y `asesor humano` |
| CA-03 | Conversación nueva | `Hola, quiero hablar con un humano` | menciona `asesor humano` (no el saludo) |
| CA-04 | — | (regresión) | los 4 escenarios BDD, los 4 E2E y los 15 unitarios existentes siguen en verde |

Casos borde: un mensaje con solo `Hola` sigue recibiendo el saludo; `¿Cuáles
son sus horarios de atención?` sigue recibiendo la respuesta de horarios.

## 6. Cómo se prueba

- TDD declarado: los escenarios se escriben antes del código y deben fallar
  primero.
- Escenarios BDD en `qa-e2e/tests/features/escalamiento.feature`,
  reutilizando los steps existentes de `steps/asistente.steps.ts`.
- Comandos (desde `qa-e2e/`, con `demo-app` en `http://localhost:3000`):
  `npm run test:bdd`, `npx playwright test --project=chromium` y
  `npm --prefix demo-app run test:unit`.

## 7. Diseño

- Componente único: `generateResponse()` en `qa-e2e/demo-app/lib/agent.ts`
  (función pura). No cambian `app/api/chat/route.ts` ni la UI.
- Contrato: `POST /api/chat` sigue devolviendo `{ response }`; solo cambia el
  texto.
- Sin datos personales nuevos; el nombre ya vive en el historial del cliente.
- `design.md`: N/A, no hay cambios de interfaz.

## 8. Decisiones pendientes

Ninguna para esta ronda.

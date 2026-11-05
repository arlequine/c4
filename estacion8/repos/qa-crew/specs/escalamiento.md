# ESC · Escalar a un asesor humano

Estado: lista para revisión · Producto: asistente del chat de `qa-e2e/demo-app` · Tres olas

## 1. Problema y usuario

Quien usa el chat de soporte y no consigue lo que necesita con el asistente
escribe "quiero hablar con una persona". Hoy el asistente responde con el
mensaje genérico ("Gracias por tu mensaje. He recibido tu consulta…") y el
usuario no sabe cómo llegar a alguien. Es la falla más frecuente en las
evaluaciones Persona + Juez (Carlos y Pedro reprueban por esto).

Usuario: cliente final del chat de `qa-e2e/demo-app`.

## 2. Criterio de éxito

Ningún usuario que pida una persona recibe el mensaje genérico, y en la
siguiente corrida de Persona + Juez Carlos y Pedro dejan de reprobar por no
poder escalar.

## 3. Fuera de alcance (todas las olas)

- Cambios en la interfaz: sin botones ni pantallas nuevas.
- Idiomas distintos al español.

## 4. Cómo se prueba (todas las olas)

- TDD declarado: las pruebas se escriben antes del código y deben fallar primero.
- Unitarias con Vitest en `qa-e2e/demo-app/__tests__/` → `npm --prefix demo-app run test:unit`.
- BDD con playwright-bdd en `qa-e2e/tests/features/`, reutilizando los steps de
  `steps/asistente.steps.ts` → `npm run test:bdd` (con `demo-app` en `http://localhost:3000`).
- Regresión: los 15 unitarios, 4 E2E y 4 escenarios BDD existentes siguen en verde.
- Cada prueba lleva en su nombre el ID del criterio que cubre (por ejemplo `CA-03`).

## 5. Diseño común

- Componente: `generateResponse()` en `qa-e2e/demo-app/lib/agent.ts` (función pura).
- Contrato: `POST /api/chat` sigue devolviendo `{ response }`; solo cambia el texto.
- Sin datos personales nuevos: el nombre ya vive en el historial del cliente.
- `design.md`: N/A, no hay cambios de interfaz.

---

## Ola 1 · Detección de la intención

**Alcance:** el asistente reconoce cuándo el usuario pide hablar con una persona
y responde con el escalamiento, aunque el mensaje empiece con un saludo.

**Reglas de negocio**

- **BR-ESC-01:** la intención se reconoce cuando el mensaje pide hablar,
  comunicarse o "pasar" con una persona, un humano, un asesor o un agente
  real, o menciona "asesor humano" / "agente humano". Mayúsculas y minúsculas
  dan igual.
- **BR-ESC-02:** la respuesta de escalamiento contiene el texto exacto `asesor humano`.
- **BR-ESC-03:** si se conoce el nombre (regla actual de `extractName`), la
  respuesta empieza con `Entendido, <Nombre>.`
- **BR-ESC-04:** el escalamiento tiene prioridad sobre el saludo.

**Criterios de aceptación** (sobre `generateResponse(historial, mensaje)`)

| ID | Historial | Mensaje | La respuesta |
|---|---|---|---|
| CA-01 | vacío | `Quiero hablar con una persona` | contiene `asesor humano` |
| CA-02 | vacío | `QUIERO HABLAR CON UN ASESOR`, `¿Me pasas con un humano?`, `Necesito un agente real` | las tres contienen `asesor humano` |
| CA-03 | vacío | `Hola, quiero hablar con un humano` | contiene `asesor humano` y no es el saludo |
| CA-04 | `Mi nombre es Ana` | `Quiero hablar con un asesor` | empieza con `Entendido, Ana.` |

**Casos borde:** `Hola` solo sigue devolviendo el saludo; `¿Cuáles son sus
horarios de atención?` sigue devolviendo los horarios.

---

## Ola 2 · Experiencia en el chat

**Alcance:** quien pide una persona en el chat ve en pantalla que lo van a
comunicar con un asesor y en qué horario atienden.

**Reglas de negocio**

- **BR-ESC-05:** la respuesta visible incluye el horario de atención.
- **BR-ESC-06:** si el usuario dijo su nombre antes en la conversación, la
  respuesta visible lo menciona.
- **BR-ESC-07:** el horario que muestra el escalamiento es fijo, lunes a viernes
  de 8:00 AM a 6:00 PM, y no depende de la hora ni del día en que se pide
  (incluido el sábado).

**Criterios de aceptación** (en el chat, con el navegador)

| ID | Dado | Cuando el usuario envía | Entonces la respuesta del agente |
|---|---|---|---|
| CA-05 | Conversación nueva | `Quiero hablar con una persona` | menciona `asesor humano` y `lunes a viernes de 8:00 AM a 6:00 PM` |
| CA-06 | Antes envió `Mi nombre es Ana` | `Quiero hablar con un asesor` | menciona `asesor humano` y `Ana` |

**Casos borde:** un sábado a las 10:00 AM (reloj del sistema fijado), `Quiero
hablar con una persona` devuelve la misma respuesta que CA-05: menciona
`asesor humano` y `lunes a viernes de 8:00 AM a 6:00 PM`, y no menciona `sábados`.

---

## Ola 3 · Transferencia real a un asesor

**Alcance:** pasar la conversación a la cola de un asesor y avisar al usuario
cuánto va a esperar.

Se quiere integrar con la herramienta de soporte del equipo, pero todavía no se
eligió cuál. No hay reglas sobre tiempos de espera, qué pasa fuera de horario ni
qué datos se envían.

| ID | Cuando | Entonces |
|---|---|---|
| CA-07 | el usuario pide una persona en horario de atención | la conversación entra a la cola y el usuario ve su tiempo de espera |

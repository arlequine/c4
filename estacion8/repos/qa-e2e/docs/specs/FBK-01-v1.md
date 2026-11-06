# FBK-01 · Calificar las respuestas del asistente

Estado: borrador v1 · Producto: chat de `qa-e2e/demo-app` · Autor: Alfredo · Fecha: 2026-11-06

---

## 1. Problema y usuario

Hoy no sabemos si las respuestas del asistente le sirven a la gente. Las
evaluaciones Persona + Juez (`qa-agent-eval`) miden calidad en laboratorio,
pero no hay ninguna señal de los usuarios reales del chat.

- **Usuario final:** quien conversa con el asistente en `/`. Quiere decir
  rápido si una respuesta le sirvió o no, sin salir del chat.
- **Responsable del asistente:** quien mantiene `lib/agent.ts`. Quiere ver qué
  porcentaje de respuestas gusta y por qué fallan las que no.

## 2. Objetivo y criterio de éxito

- Objetivo: capturar una calificación 👍/👎 por respuesta del asistente y
  mostrar un resumen para el responsable.
- Éxito: en la primera semana de uso, al menos 1 de cada 5 respuestas del
  asistente tiene calificación, y el panel permite identificar los 3 motivos
  de 👎 más recientes sin abrir logs.

## 3. Alcance y fuera de alcance

**Entra en esta ronda**
- Botones 👍 y 👎 en cada respuesta del asistente.
- Motivo opcional al votar 👎.
- API para guardar calificaciones y consultar estadísticas.
- Página `/admin/feedback` con el resumen.

**Fuera de alcance**
- Autenticación de usuarios y protección de `/admin/feedback`.
- Base de datos externa: la persistencia es en memoria del proceso.
- Calificar los mensajes del usuario.
- Exportar datos o graficar tendencias en el tiempo.
- Usar las calificaciones para cambiar las respuestas del asistente.

## 4. Requisitos funcionales (RF)

| ID | Requisito |
|---|---|
| RF-01 | Cada respuesta del asistente muestra dos botones, 👍 y 👎. El usuario puede calificar cada respuesta una sola vez y puede cambiar su voto. |
| RF-02 | Al elegir 👎 aparece un campo de texto opcional "¿Qué faltó?" con máximo 200 caracteres y un botón "Enviar motivo". |
| RF-03 | `POST /api/feedback` guarda una calificación validada con zod. |
| RF-04 | `GET /api/feedback/stats` devuelve los totales de 👍 y 👎, el porcentaje de satisfacción y los últimos 5 motivos. |
| RF-05 | `/admin/feedback` muestra las estadísticas de RF-04. |
| RF-06 | Cada respuesta del asistente tiene un `messageId` estable para que la calificación se asocie a ese mensaje. |

## 5. Criterios de aceptación (CA)

| ID | RF | Dado | Cuando | Entonces |
|---|---|---|---|---|
| CA-01 | RF-01 | el asistente respondió un mensaje | el usuario ve la respuesta | debajo aparecen dos botones con `aria-label` "Me sirvió" y "No me sirvió" |
| CA-02 | RF-01 | una respuesta sin calificar | el usuario hace clic en 👍 | el botón 👍 queda con `aria-pressed="true"` y se envía `POST /api/feedback` con `rating: "up"` |
| CA-03 | RF-02 | una respuesta sin calificar | el usuario hace clic en 👎 | aparece el campo "¿Qué faltó?" vacío y el botón "Enviar motivo" |
| CA-04 | RF-02 | el campo de motivo visible | el usuario escribe 201 caracteres | el campo solo conserva 200 (`maxLength=200`) |
| CA-05 | RF-03 | — | `POST /api/feedback` con `{ messageId, rating: "up" }` válido | responde `201` con `{ ok: true }` |
| CA-06 | RF-03 | — | `POST /api/feedback` con `rating: "meh"` | responde `400` con `{ error }` y no guarda nada |
| CA-07 | RF-03 | — | `POST /api/feedback` con `reason` de 201 caracteres | responde `400` |
| CA-08 | RF-03 | — | `POST /api/feedback` con `reason` y `rating: "up"` | responde `400`: el motivo solo se acepta con 👎 |
| CA-09 | RF-04 | 3 👍 y 1 👎 guardados | `GET /api/feedback/stats` | responde `{ up: 3, down: 1, total: 4, satisfaction: 75, lastReasons: [...] }` |
| CA-10 | RF-04 | sin calificaciones | `GET /api/feedback/stats` | responde `{ up: 0, down: 0, total: 0, satisfaction: 0, lastReasons: [] }` |
| CA-11 | RF-04 | 7 👎 con motivo | `GET /api/feedback/stats` | `lastReasons` tiene los 5 más recientes, del más nuevo al más viejo |
| CA-12 | RF-05 | hay calificaciones | el responsable abre `/admin/feedback` | el panel muestra la información de forma clara y fácil de leer |
| CA-13 | RF-06 | dos respuestas del asistente | se califica la segunda | la calificación lleva el `messageId` de la segunda, no el de la primera |

## 6. Diseño técnico y contratos

**Componentes (dentro de `qa-e2e/demo-app/`)**
- `lib/feedback.ts`: tipos `Feedback` y `FeedbackStats`, esquema zod
  `FeedbackInput`, el store y una función pura `computeStats(feedback[])`.
- `app/api/feedback/route.ts`: `POST`.
- `app/api/feedback/stats/route.ts`: `GET`.
- `app/page.tsx`: botones y campo de motivo en cada `agent-message`.
- `app/admin/feedback/page.tsx`: panel.

**Identificador de mensaje (RF-06):** el cliente genera
`crypto.randomUUID()` al recibir cada respuesta de `/api/chat` y lo guarda en
el estado del mensaje. `POST /api/chat` no cambia su contrato (`{ response }`),
así que las pruebas existentes no se tocan.

**Contrato `POST /api/feedback`**
```ts
// request
{ messageId: string /* uuid */, rating: "up" | "down", reason?: string /* 1..200, solo si rating = "down" */ }
// 201 → { ok: true }    400 → { error: string }
```

**Contrato `GET /api/feedback/stats`**
```ts
{ up: number, down: number, total: number,
  satisfaction: number /* round(up / total * 100); 0 si total = 0 */,
  lastReasons: { reason: string, createdAt: string /* ISO */ }[] /* máx. 5, más nuevo primero */ }
```

**Persistencia:** un arreglo en memoria guardado en `globalThis` para que
sobreviva al hot reload de `next dev`. Se pierde al reiniciar el servidor.

**Dependencias nuevas:** `zod` en `demo-app/package.json`, porque hoy no está.

**Restricciones**
- Sin datos personales: no se guarda el texto de la conversación, solo
  `messageId`, `rating`, `reason` y `createdAt`.
- `/admin/feedback` queda público (ver fuera de alcance). Es una demo, no
  producción.

## 7. Plan de pruebas

- TDD declarado: las pruebas se escriben antes del código y deben fallar primero.
- **Unitarias (Vitest)** en `demo-app/__tests__/feedback.test.ts`: esquema zod
  (CA-06, CA-07, CA-08) y `computeStats` (CA-09, CA-10, CA-11).
  Comando: `npm --prefix demo-app run test:unit`.
- **API (Playwright `request`)** en `tests/e2e/feedback-api.spec.ts`: CA-05 a CA-11.
- **E2E (Playwright + POM)** en `tests/e2e/feedback.spec.ts`, con un Page
  Object nuevo `pages/FeedbackPanelPage.ts` y métodos nuevos en `HomePage`:
  CA-01 a CA-04, CA-12 y CA-13.
- **BDD (playwright-bdd)** en `tests/features/feedback.feature`, con el flujo
  completo calificar → aparece en el panel.
- Comando E2E/BDD: `npx bddgen && npx playwright test --project=chromium --project=bdd`
  con `demo-app` corriendo en el puerto de su worktree (`BASE_URL`).
- Regresión: los 15 unitarios, 4 E2E y 4 BDD existentes siguen en verde.
- Cada prueba lleva en su nombre el ID del CA que cubre.

## 8. Supuestos (S) y preguntas abiertas (P)

| ID | Tipo | Texto |
|---|---|---|
| S-01 | Supuesto | Un solo proceso de Next.js: el store en memoria es suficiente para la demo. |
| S-02 | Supuesto | El porcentaje de satisfacción se redondea al entero más cercano. |
| S-03 | Supuesto | "Nueva conversación" limpia los botones de la pantalla, pero no borra las calificaciones guardadas. |
| P-01 | Pregunta | ¿El motivo se puede enviar después, en un segundo `POST`, o solo junto con el 👎? Default: junto con el 👎 o en un segundo envío del mismo mensaje. |

## 9. Riesgos (R)

| ID | Riesgo | Mitigación |
|---|---|---|
| R-01 | Las pruebas E2E en paralelo comparten el store en memoria y las estadísticas se contaminan. | Las pruebas de stats comparan diferencias (antes/después) en lugar de valores absolutos, o corren en serie. |
| R-02 | El hot reload de `next dev` reinicia el módulo y vacía el store. | Guardar el store en `globalThis` (sección 6). |
| R-03 | Varios agentes en paralelo levantan `demo-app` en el mismo puerto 3000. | Un puerto por worktree (3001, 3002…) vía `BASE_URL` y `next dev -p`. |

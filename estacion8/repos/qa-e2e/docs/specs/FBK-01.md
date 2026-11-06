# FBK-01 · Calificar las respuestas del asistente

Estado: v2 (corregida con `improve-spec`) · Producto: chat de `qa-e2e/demo-app` · Autor: Alfredo · Fecha: 2026-11-06

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
- Quitar un voto (volver a "sin calificar").
- Exportar datos o graficar tendencias en el tiempo.
- Usar las calificaciones para cambiar las respuestas del asistente.

## 4. Requisitos funcionales (RF) y reglas de negocio (BR)

| ID | Requisito |
|---|---|
| RF-01 | Cada respuesta del asistente muestra dos botones, 👍 y 👎. El usuario califica cada respuesta y puede cambiar su voto (ver BR-FBK-01 y BR-FBK-05). |
| RF-02 | Al elegir 👎 aparece un campo de texto opcional "¿Qué faltó?" con máximo 200 caracteres y un botón "Enviar motivo". |
| RF-03 | `POST /api/feedback` guarda una calificación validada con zod. |
| RF-04 | `GET /api/feedback/stats` devuelve los totales de 👍 y 👎, el porcentaje de satisfacción y los últimos 5 motivos. |
| RF-05 | `/admin/feedback` muestra las estadísticas de RF-04. |
| RF-06 | Cada respuesta del asistente tiene un `messageId` estable para que la calificación se asocie a ese mensaje. |

**Reglas de negocio**

- **BR-FBK-01 · Un voto vigente por mensaje.** Cada `messageId` tiene como
  máximo una calificación vigente. Un segundo `POST` con el mismo `messageId`
  **reemplaza** la anterior: no suma ni se rechaza.
- **BR-FBK-02 · El motivo solo vive con 👎.** Si una calificación pasa de 👎 a
  👍, el motivo guardado se borra.
- **BR-FBK-03 · El motivo se puede mandar después.** El motivo se envía junto
  con el 👎 o después, con otro `POST` del mismo `messageId` con
  `rating: "down"` y `reason`, que es un reemplazo según BR-FBK-01.
- **BR-FBK-04 · Qué cuenta en las stats.** Solo las calificaciones vigentes,
  una por `messageId`. `satisfaction = round(up / total × 100)`, y `0` si
  `total = 0`. `lastReasons` se ordena por la fecha de la última actualización,
  de la más nueva a la más vieja.
- **BR-FBK-05 · Clic en el botón activo.** Volver a hacer clic en el botón que
  ya está activo no cambia nada ni envía otra petición.

## 5. Criterios de aceptación (CA)

Nivel: **U** = unitaria (Vitest), **A** = API (Playwright `request`), **E** = E2E/BDD (Playwright + POM).

| ID | RF/BR | Nivel | Dado | Cuando | Entonces |
|---|---|---|---|---|---|
| CA-01 | RF-01 | E | el asistente respondió un mensaje | el usuario ve la respuesta | debajo aparecen dos botones con `aria-label` "Me sirvió" y "No me sirvió" |
| CA-02 | RF-01 | E | una respuesta sin calificar | el usuario hace clic en 👍 | el botón 👍 queda con `aria-pressed="true"` y se envía `POST /api/feedback` con `rating: "up"` |
| CA-03 | RF-02 | E | una respuesta sin calificar | el usuario hace clic en 👎 | aparece el campo "¿Qué faltó?" vacío y el botón "Enviar motivo" |
| CA-04 | RF-02 | E | el campo de motivo visible | el usuario escribe 201 caracteres | el campo solo conserva 200 (`maxLength=200`) |
| CA-05 | RF-03 | A | un `messageId` nuevo | `POST /api/feedback` con `{ messageId, rating: "up" }` | responde `201` con `{ ok: true, replaced: false }` |
| CA-06 | RF-03 | U/A | — | `POST /api/feedback` con `rating: "meh"` | responde `400` con `{ error }` y no guarda nada |
| CA-07 | RF-03 | U/A | — | `POST /api/feedback` con `reason` de 201 caracteres | responde `400` |
| CA-08 | RF-03, BR-FBK-02 | U/A | — | `POST /api/feedback` con `reason` y `rating: "up"` | responde `400`: el motivo solo se acepta con 👎 |
| CA-09 | RF-04, BR-FBK-04 | U | 3 calificaciones `up` y 1 `down` | `computeStats(calificaciones)` | devuelve `{ up: 3, down: 1, total: 4, satisfaction: 75, lastReasons: [...] }` |
| CA-10 | RF-04, BR-FBK-04 | U | lista vacía | `computeStats([])` | devuelve `{ up: 0, down: 0, total: 0, satisfaction: 0, lastReasons: [] }` |
| CA-11 | RF-04, BR-FBK-04 | U | 7 `down` con motivo y fechas distintas | `computeStats(calificaciones)` | `lastReasons` tiene los 5 más recientes por `updatedAt`, del más nuevo al más viejo |
| CA-12 | RF-05 | E | hay al menos una calificación guardada | el responsable abre `/admin/feedback` | `stat-up`, `stat-down`, `stat-total` y `stat-satisfaction` (este último con sufijo `%`) muestran los mismos valores que `GET /api/feedback/stats` en ese momento, y `reasons-list` tiene tantos `reason-item` como `lastReasons`, en el mismo orden *(testids nuevos)* |
| CA-13 | RF-06 | E | dos respuestas del asistente | se califica la segunda | la calificación lleva el `messageId` de la segunda, no el de la primera |
| CA-14 | RF-05 | E | `GET /api/feedback/stats` responde `total: 0` (simulado con `page.route`) | el responsable abre `/admin/feedback` | se ve `empty-state` con el texto "Aún no hay calificaciones" y no existe `reasons-list` *(testids nuevos)* |
| CA-15 | RF-05, BR-FBK-04 | E | el responsable anotó `stat-down` en el panel | en `/` el usuario vota 👎 con el motivo "faltó el precio" y vuelve a abrir el panel | `stat-down` aumentó en 1 y el primer `reason-item` dice "faltó el precio" |
| CA-16 | RF-01, BR-FBK-01 | E | una respuesta calificada con 👍 | el usuario hace clic en 👎 | 👎 queda `aria-pressed="true"`, 👍 queda `aria-pressed="false"` y aparece el campo de motivo |
| CA-17 | RF-03, BR-FBK-01 | A | un `messageId` nuevo y el `total` actual de `/stats` | `POST` con `rating: "up"` y después `POST` del mismo `messageId` con `rating: "down"` | el segundo responde `200` con `{ ok: true, replaced: true }`, y `total` subió **1** (no 2), `down` subió 1 y `up` quedó igual |
| CA-18 | BR-FBK-02 | U | el store tiene `{ messageId: m, rating: "down", reason: "x" }` | se guarda `{ messageId: m, rating: "up" }` | `computeStats` ya no incluye "x" en `lastReasons` |
| CA-19 | RF-03 | U/A | — | `POST /api/feedback` con `messageId: "abc"` (no es uuid) | responde `400` |
| CA-20 | BR-FBK-05 | E | una respuesta con 👍 activo | el usuario vuelve a hacer clic en 👍 | no se envía ningún `POST /api/feedback` y 👍 sigue con `aria-pressed="true"` |

## 6. Diseño técnico y contratos

**Componentes (dentro de `qa-e2e/demo-app/`)**
- `lib/feedback.ts`: tipos `Feedback` y `FeedbackStats`, esquema zod
  `FeedbackInput`, el store (`saveFeedback` hace el upsert de BR-FBK-01 y el
  borrado de BR-FBK-02) y una función pura `computeStats(feedback[])`.
- `app/api/feedback/route.ts`: `POST`.
- `app/api/feedback/stats/route.ts`: `GET`.
- `app/page.tsx`: botones y campo de motivo en cada `agent-message`.
- `app/admin/feedback/page.tsx`: panel. Componente cliente que hace `fetch` a
  `/api/feedback/stats` al cargar, para que CA-14 se pueda simular con
  `page.route`.

**Identificador de mensaje (RF-06):** el cliente genera
`crypto.randomUUID()` al recibir cada respuesta de `/api/chat` y lo guarda en
el estado del mensaje. `POST /api/chat` no cambia su contrato (`{ response }`),
así que las pruebas existentes no se tocan.

**Modelo**
```ts
type Feedback = { messageId: string; rating: "up" | "down"; reason?: string; createdAt: string; updatedAt: string };
```

**Contrato `POST /api/feedback`**
```ts
// request
{ messageId: string /* uuid */, rating: "up" | "down", reason?: string /* 1..200, solo si rating = "down" */ }
// 201 → { ok: true, replaced: false }   primer voto de ese messageId
// 200 → { ok: true, replaced: true }    reemplazo (BR-FBK-01)
// 400 → { error: string }               validación zod
```

**Contrato `GET /api/feedback/stats`**
```ts
{ up: number, down: number, total: number,
  satisfaction: number /* BR-FBK-04 */,
  lastReasons: { reason: string, at: string /* ISO, updatedAt */ }[] /* máx. 5, más nuevo primero */ }
```

**`data-testid` nuevos del panel:** `stat-up`, `stat-down`, `stat-total`,
`stat-satisfaction`, `reasons-list`, `reason-item` y `empty-state`.
En el chat: `feedback-up`, `feedback-down`, `feedback-reason` y
`feedback-reason-submit`, dentro de cada `agent-message`.

**Persistencia:** un `Map<messageId, Feedback>` en memoria guardado en
`globalThis` para que sobreviva al hot reload de `next dev`. Se pierde al
reiniciar el servidor.

**Dependencias nuevas:** `zod` en `demo-app/package.json`, porque hoy no está.

**Restricciones**
- Sin datos personales: no se guarda el texto de la conversación, solo
  `messageId`, `rating`, `reason` y las fechas.
- `/admin/feedback` queda público (ver fuera de alcance). Es una demo, no
  producción.

## 7. Plan de pruebas

- TDD declarado: las pruebas se escriben antes del código y deben fallar primero.
- **Unitarias (Vitest)** en `demo-app/__tests__/feedback.test.ts`: esquema zod
  y store (CA-06, CA-07, CA-08, CA-18, CA-19) y `computeStats` con **valores
  absolutos** (CA-09, CA-10, CA-11).
  Comando: `npm --prefix demo-app run test:unit`.
- **API (Playwright `request`)** en `tests/api/feedback-api.spec.ts`, con el builder `fixtures/feedback-builders.ts` y el proyecto `api` (sin paralelismo): CA-05,
  CA-06, CA-07, CA-08, CA-17 y CA-19. Las stats se comparan como **diferencias**
  (antes/después), nunca como valores absolutos (ver R-01).
- **E2E (Playwright + POM)** en `tests/e2e/feedback.spec.ts`, con un Page
  Object nuevo `pages/FeedbackPanelPage.ts` y métodos nuevos en `HomePage`:
  CA-01 a CA-04, CA-12 a CA-16 y CA-20.
- **BDD (playwright-bdd)** en `tests/features/feedback.feature`: el flujo de
  CA-15 (calificar → aparece en el panel), escrito en español con los steps
  existentes más los nuevos.
- Comando E2E/BDD: `npx bddgen && npx playwright test --project=chromium --project=bdd`
  con `demo-app` corriendo en el puerto de su worktree (`BASE_URL`).
- Regresión: los 15 unitarios, 4 E2E y 4 BDD existentes siguen en verde.
- Cada prueba lleva en su nombre el ID del CA que cubre y un tag `@TASK-00N` para verificarla por tarea (`--grep @TASK-00N`).
- Las unitarias están separadas por tarea: `feedback.test.ts` (TASK-001) y `feedback-stats.test.ts` (TASK-004).

## 8. Supuestos (S) y preguntas abiertas (P)

| ID | Tipo | Texto |
|---|---|---|
| S-01 | Supuesto | Un solo proceso de Next.js: el store en memoria es suficiente para la demo. |
| S-02 | Supuesto | El porcentaje de satisfacción se redondea al entero más cercano. |
| S-03 | Supuesto | "Nueva conversación" limpia los botones de la pantalla, pero no borra las calificaciones guardadas. |
| S-04 | Supuesto | No hay `design.md`: la interfaz reutiliza los estilos en línea y la paleta de `page.tsx` (fondo `#1e293b`, acento `#3b82f6`) y no agrega librerías de UI. |
| S-05 | Default de improve-spec, confirmar | Doble voto = reemplazo (BR-FBK-01). Alternativa descartada: rechazar con `409`. |
| S-06 | Default de improve-spec, confirmar | Las stats se prueban con valores absolutos solo en unitarias; en API y E2E, como diferencias. |
| P-01 | **Resuelta** | ¿El motivo se puede enviar después? → Sí, con un reemplazo (BR-FBK-03). |

## 9. Riesgos (R)

| ID | Riesgo | Mitigación |
|---|---|---|
| R-01 | Las pruebas E2E en paralelo comparten el store en memoria y las estadísticas se contaminan. | Valores absolutos solo en `computeStats` (unitarias). API y E2E comparan diferencias o coherencia con `/stats` (CA-12, CA-15 y CA-17). |
| R-02 | El hot reload de `next dev` reinicia el módulo y vacía el store. | Guardar el store en `globalThis` (sección 6). |
| R-03 | Varios agentes en paralelo levantan `demo-app` en el mismo puerto 3000. | Un puerto por worktree (3001, 3002…) vía `BASE_URL` y `next dev -p`. |

## Cambios v2 (improve-spec, iteración 1)

- P4 → BR-FBK-01..05: doble voto, motivo, stats y botón activo.
- T1 → CA-12 reescrito con `data-testid` y coherencia con `/stats`. Se agregan CA-14 (estado vacío), CA-15 (flujo) y CA-16 (cambio de voto en la UI).
- T2 → CA-17 (reemplazo en la API), CA-18 (motivo borrado), CA-19 (`messageId` inválido) y CA-20 (clic en el botón activo).
- D2 → contrato `POST` con `201`/`200` + `replaced`; modelo con `updatedAt`; `lastReasons.at`.
- D3 → S-04.
- P6 → P-01 resuelta; doble voto documentado en S-05.
- Coherencia CA-09/11 vs R-01 → CA-09, CA-10 y CA-11 pasan a nivel unitario sobre `computeStats`; R-01 y §7 alineados (S-06).
- Se agrega "quitar un voto" a fuera de alcance.

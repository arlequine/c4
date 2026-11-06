# Estándares · <CLAVE> · <título de la spec>

> Plantilla de `implementar-spec` para **`estacion8/repos/qa-e2e`**. Las secciones 1–7 ya traen las convenciones reales del proyecto, y cada regla cita el archivo de donde sale. **No inventes convenciones nuevas.** Las partes `<entre ángulos>` las llena el agente para su tarea. Si algo del repo cambió, actualiza la regla y su cita.
>
> Se copia a `docs/standards/<CLAVE>-estandares.md`. Con OpenSymphony, cada agente escribe la suya como `docs/standards/<CLAVE>-<TASK-00N>-estandares.md`, para no pisarse entre ramas.

---

## 1. Stack y comandos

| Pieza | Versión instalada | Fuente |
|---|---|---|
| Node.js | ≥ 22 (WSL del curso) | `README.md` pide ≥ 18; el adaptador ACP pide 22 |
| Next.js (App Router) | 15.5.x (`^15.1.0`) | `demo-app/package.json`, `demo-app/app/` |
| React | 19.2.x (`^19.0.0`) | `demo-app/package.json` |
| TypeScript | 5.9.x (`^5.3.0`), `strict: true` | `demo-app/tsconfig.json`, `tsconfig.json` |
| Vitest | 2.1.x | `demo-app/package.json`, `demo-app/vitest.config.ts` |
| Playwright | 1.58.x (`^1.48.0`) | `package.json` |
| playwright-bdd | 7.5.x | `package.json`, `playwright.config.ts` |
| zod | **no instalado**. Solo lo agrega la tarea que lo declare (FBK-01: TASK-001) | `demo-app/package.json` |

Todos los comandos se corren desde `estacion8/repos/qa-e2e`.

| Acción | Comando | Estado |
|---|---|---|
| Instalar | `npm ci && npm --prefix demo-app ci` | verificado |
| Navegador | `npx playwright install --with-deps chromium` | verificado |
| Levantar app | `npm --prefix demo-app run dev -- -p <puerto>` (el script fija `-p 3000`; el `-p` extra lo sobrescribe) | verificado (3000) |
| Unitarias | `npm --prefix demo-app run test:unit` | verificado |
| Una unitaria | `npm --prefix demo-app run test:unit -- __tests__/<archivo>.test.ts` | verificado |
| E2E / API / BDD | `npx bddgen && BASE_URL=http://localhost:<puerto> npx playwright test --project=chromium --project=bdd --project=api` | verificado |
| Pruebas de una tarea | `BASE_URL=… npx playwright test --project=<proy> --grep @TASK-00N` | verificado |
| Typecheck app | `cd demo-app && npx tsc --noEmit` | verificado |
| Typecheck pruebas | `npx tsc --noEmit -p .` | verificado |
| Lint / formato | — | **no definido en el repo** (no hay ESLint, Prettier ni Biome). No lo agregues |
| Build | `npm --prefix demo-app run build` | inferido (script existe) |

**No uses** `npm test` en la raíz como "todas las pruebas": corre Playwright con **todos** los proyectos, incluido `firefox`, que falla en WSL, y no corre Vitest (`package.json`, `playwright.config.ts`).

## 2. Estructura

| Qué | Dónde | Fuente |
|---|---|---|
| Páginas (App Router) | `demo-app/app/<ruta>/page.tsx` | `demo-app/app/page.tsx` |
| Rutas de API | `demo-app/app/api/<recurso>/route.ts`, un handler por método (`export async function POST`) | `demo-app/app/api/chat/route.ts` |
| Lógica de dominio pura y tipos | `demo-app/lib/<dominio>.ts` | `demo-app/lib/agent.ts` |
| Unitarias | `demo-app/__tests__/<dominio>.test.ts` (solo ese patrón entra) | `demo-app/vitest.config.ts` |
| Page Objects | `pages/<Nombre>Page.ts`, una clase por página | `pages/HomePage.ts`, skill `qa-testing` §3 |
| E2E | `tests/e2e/<flujo>.spec.ts` | `playwright.config.ts` (proyecto `chromium`) |
| API | `tests/api/<recurso>-api.spec.ts` + builders en `fixtures/<recurso>-builders.ts` | skill `qa-testing` §1 y §5, proyecto `api` |
| BDD | `tests/features/<tema>.feature` + `steps/<tema>.steps.ts`; `tests/bdd/` lo genera `bddgen` | `playwright.config.ts`, skill `qa-testing` §4 |
| Specs y estándares | `docs/specs/<CLAVE>.md`, `docs/standards/` | `docs/specs/FBK-01.md` |

Nombres: archivos de dominio en minúscula con guion (`feedback-stats.ts`), componentes y POM en PascalCase (`FeedbackPanelPage.ts`), funciones en camelCase (`generateResponse`) (`demo-app/lib/agent.ts`, `pages/`).

## 3. Estilo de código

Como no hay linter, mandan los **patrones dominantes** del código:

- **Formato:** 2 espacios, comillas simples, punto y coma y coma final en literales multilínea (`demo-app/lib/agent.ts`, `demo-app/app/page.tsx`).
- **Imports:** alias `@/` dentro de `demo-app/app/` (`app/api/chat/route.ts` → `@/lib/agent`, definido en `demo-app/tsconfig.json` `paths`). Rutas relativas en pruebas y POM (`__tests__/agent.test.ts`, `tests/e2e/flujo-principal.spec.ts`).
- **Exports:** `export function` y `export interface`/`type` con nombre en `lib/`; `export default function` en las páginas (`lib/agent.ts`, `app/page.tsx`).
- **Tipos:** `interface` para formas de datos (`Message` en `lib/agent.ts`), `strict` sin `any` implícito (`demo-app/tsconfig.json`).
- **Dominio puro:** la lógica va en funciones puras y deterministas en `lib/`, fáciles de probar sin servidor (comentario de `lib/agent.ts`).
- **Errores en API:** `NextResponse.json({ error: '<mensaje en español>' }, { status: 400 })` para una entrada inválida (`app/api/chat/route.ts`). Un JSON inválido también responde `400`.
- **Validación:** hoy es manual (`if (!message || !message.trim())`). Para FBK-01 la spec pide **zod** (`docs/specs/FBK-01.md` §6): define el esquema en `lib/` y úsalo en la ruta con `safeParse`.
- **UI:** `'use client'`, `useState`, estilos **en línea** con la paleta de `page.tsx` (fondo `#0f172a`/`#1e293b`, acento `#3b82f6`, texto `#e2e8f0`), sin librerías de UI ni CSS nuevo (`app/page.tsx`, `app/layout.tsx`, spec S-04).
- **Accesibilidad y testids:** cada control lleva `aria-label`; los contenedores que leen las pruebas llevan `data-testid` (`app/page.tsx`: `agent-message`, `loading`, botón "Enviar").
- **Comentarios:** JSDoc breve en español sobre funciones exportadas (`lib/agent.ts`).
- **Logging:** no hay. No agregues `console.log` al código entregado.

## 4. Testing

- **TDD declarado** (spec §7): las pruebas de cada tarea **ya existen en rojo** desde la Fase 5. El agente las pone en verde **sin editarlas**. Si una prueba parece incorrecta, lo reporta en el issue y se detiene.
- Pirámide (skill `qa-testing` §2): lógica pura → Vitest; endpoints → Playwright `request` (proyecto `api`, sin paralelismo); flujo del usuario → E2E con POM; flujo de negocio → BDD en español.
- **POM** (skill `qa-testing` §3): los locators van `readonly` en el constructor y siguen la prioridad `getByRole` > `getByLabel` > `getByText` > `data-testid`. Las aserciones van en el test o el step, nunca en el POM.
- **Nombres:** `it('CA-xx …')` / `test('CA-xx …', { tag: '@TASK-00N' }, …)`, como frase en español (`tests/e2e/feedback.spec.ts`).
- **Estado en memoria:** las pruebas de API y E2E comparan diferencias o coherencia con `/stats`, nunca valores absolutos (spec R-01 y S-06).
- **Proyectos:** `chromium` (E2E), `bdd`, `api`. **No corras `firefox`**: falla en WSL (`playwright.config.ts`).
- **Esperas:** `expect(...)` y `waitFor`, nunca `setTimeout` (skill `qa-testing` §7).

## 5. Trazabilidad y git

- **Rama:** `fbk-01/<ID-issue>` (por ejemplo, `fbk-01/EST-12`), que sale de `estacion8/orquestacion-opensymphony` con las olas anteriores ya integradas.
- **Commits:** el repo mezcla `Estación N: …` con Conventional Commits; la rama del ejercicio usa Conventional (`git log`: `feat(e8): …`, `test(e8): …`). Formato: `feat(<CLAVE>): <qué> [RF-xx, CA-xx] (<ID-issue>)`. Ejemplo: `feat(FBK-01): upsert de calificaciones [RF-03, CA-05, CA-17] (EST-12)`.
- **Matriz CA → prueba → tarea:**

| CA | Prueba (archivo › nombre) | Tarea | Estado |
|---|---|---|---|
| <CA-xx> | <archivo> › "<CA-xx …>" | <TASK-00N> | rojo / verde |

## 6. Límites del agente

- Sin `git push --force`, sin merge ni rebase a `main` ni a `estacion8/orquestacion-opensymphony`, y sin `reset --hard`.
- Solo tocas los archivos de **Deliverables** de tu tarea (`docs/tasks/00N-*.md`). Lo demás va como sugerencia en el issue.
- **No editas pruebas** de `__tests__/`, `tests/` ni `steps/`. Los POM en `pages/` solo se ajustan si la tarea lo permite y el DOM real lo exige.
- Sin dependencias nuevas, salvo las que declara la tarea (FBK-01: `zod` en TASK-001).
- No leas ni escribas `.env*`, llaves ni tokens. `LINEAR_API_KEY` solo se usa a través de la skill `linear`.
- **Puerto propio:** nunca el 3000. Usa el puerto asignado a tu workspace con `-p <puerto>` y `BASE_URL`.
- Sin borrar archivos.

## 7. Definition of Done

- [ ] Las pruebas `@TASK-00N` de la tarea están en verde (comando del *Test Plan* del issue).
- [ ] Regresión en verde: unitarias completas y `--grep-invert "@TASK-"` en `chromium` + `bdd`.
- [ ] Typecheck limpio: `cd demo-app && npx tsc --noEmit` (salvo los errores de módulos de tareas futuras, que se listan) y `npx tsc --noEmit -p .`.
- [ ] Cada CA del issue está cubierto y la matriz de la sección 5 está actualizada.
- [ ] Solo cambiaron los archivos de Deliverables (`git diff --stat`).
- [ ] Commit con el formato de la sección 5. Issue movido a **In Review** con un comentario de resumen.
- Lint: **N/A** (no definido en el repo).

## 8. Modelo asignado

- Modelo: `<sonnet | opus | haiku>` (lo fija `session.model` del perfil ACP; ver la guía, Fase 6).
- Ajuste: <tamaño de tarea e instrucciones según la tabla "Ajuste por modelo" de `SKILL.md`>.

## 9. Supuestos y decisiones

- <S-xx de la spec que afectan esta tarea>
- <decisiones propias de la tarea, con su motivo>

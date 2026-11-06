# Guía de ensayo · Orquestación con OpenSymphony + Claude Code (FBK-01)

Rama: `estacion8/orquestacion-opensymphony` (desde `rework/estacion8`, commit 365e131).
Proyecto de ejemplo: `estacion8/repos/qa-e2e` (la app Next.js vive en `estacion8/repos/qa-e2e/demo-app`).
Entorno del ensayo: WSL (Ubuntu) + Claude Code.

Cada paso trae: **Comando / prompt**, **Resultado esperado**, **Cómo verificar** y **Plan B**.
Al final de cada fase hay un registro de lo que funcionó y lo que falló.

---

## Fase 0 · Preparación

### 0.1 Traer la rama del ejercicio

**Comando**
```bash
cd ~ && git clone https://github.com/arlequine/c4.git && cd c4
git fetch origin estacion8/orquestacion-opensymphony
git switch estacion8/orquestacion-opensymphony
```
**Resultado esperado:** estás en la rama del ejercicio; el último commit es el de esta guía.
**Cómo verificar:** `git log --oneline -2` muestra este commit encima de `365e131`.
**Plan B:** si la rama no existe en el remoto, `git switch -c estacion8/orquestacion-opensymphony origin/rework/estacion8`.

### 0.2 Qué es OpenSymphony (verificado en su documentación)

- OpenSymphony es una implementación en Rust de la especificación **OpenAI Symphony** (`SPEC.md`). Repo: `github.com/kumanday/OpenSymphony`; paquete `opensymphony` en crates.io; docs en docs.rs (versión más reciente vista: 3.0.0).
- Hace *polling* de un proyecto de Linear, crea un workspace aislado por issue (`<workspace_root>/<ID-issue>/`, con hooks como `after_create` para clonar el repo) y lanza un agente por issue.
- Sitio oficial: https://opensymphony.dev/es/ (repo `kumanday/OpenSymphony`, docs en `docs/`).
- **Harnesses soportados: OpenHands (por defecto), Codex app-server y, desde la 3.0.0, perfiles ACP v1** (Agent Client Protocol, un agente local por stdio). La documentación **no menciona Claude Code**; el único perfil ACP de ejemplo es `cursor`.
- **Decisión (2026-11-06): usar el harness ACP con el adaptador `@agentclientprotocol/claude-agent-acp`** (binario `claude-agent-acp`, de terceros, corre sobre el Claude Agent SDK). Verificado en el sandbox:
  - v0.101.0 responde el `initialize` de ACP v1 y anuncia `loadSession` y `resume`.
  - Carga `settingSources: ["user", "project", "local"]` y skills, así que lee `CLAUDE.md` y `.claude/skills/`.
  - Se autentica con tu login de Claude Code (`~/.claude`) o con `ANTHROPIC_API_KEY`. OpenSymphony le pasa el entorno del proceso (menos las credenciales de checkout).
- Instalación (3.0.0 pide **rustc ≥ 1.97.1**; la compilación tarda **~30 min**, hazla antes del ensayo):
  ```bash
  rustup update stable && rustc --version     # ≥ 1.97.1
  cargo install opensymphony --locked         # ~30 min
  npm i -g @agentclientprotocol/claude-agent-acp@0.101.0
  ```
- Conexión con Linear: **API key** (`LINEAR_API_KEY`), solo GraphQL. El orquestador lee Linear; el agente escribe con la skill `linear` de la plantilla oficial (`linear_graphql.py`, Python sin dependencias). No usa el MCP de Linear.
- **Config central (3.0.0):** con ACP la config es un archivo central `schema_version: 1` (`opensymphony run --config <ruta>`). La forma fácil de obtenerla: `opensymphony migrate apply` sobre un `config.yaml` + `WORKFLOW.md` legacy, y luego editar `routing.harness`/`acp.profiles`. El `WORKFLOW.md` queda solo con el prompt y una línea exacta `Target branch: \`<rama>\`` (sin ella, `migrate` falla). `migrate` se niega a convertir un hook `after_create` con `git clone`.
- Worktrees: **en `legacy_single` la 3.0.0 ignora `integration.use_shared_git_worktrees`** (`config.rs`: se lee y se descarta). El workspace de cada issue es un directorio vacío y el código solo llega si `hooks.after_create` lo clona (`git clone <repo> .` corre antes de que exista `.opensymphony/`). Cada issue queda en un **clon propio**, no en un worktree. Para el ejercicio da igual: lo que importa es el aislamiento.
- **La plantilla oficial (`kumanday/OpenSymphony-template`) trae `create-implementation-plan` (idéntica a la de `estacion6/skills/`) y `convert-tasks-to-linear`** con `validate`, `dry-run` y `apply`. No hay que crear esta última desde cero.
- La plantilla usa estados `Human Review`, `Merging` y `Rework` y una skill `land` que hace merge. Para el ejercicio usamos los estados por defecto de Linear (`Todo`, `In Progress`, `In Review`, `Done`) y **no** copiamos `land` (regla: ningún agente hace merge).

### 0.3 ¿Respeta las relaciones "blocked by"?

- **Sí.** Verificado en el código de la 3.0.0 (`crates/opensymphony-orchestrator/src/selection.rs`): `should_dispatch_issue` descarta cualquier issue con un bloqueador en estado no terminal, y el scheduler filtra con esa función antes de despachar. En OpenSymphony aplica a cualquier estado activo, no solo a *Todo* como en la spec Symphony.
- `blocked_by` sale de las `inverseRelations` de Linear con tipo `blocks`.
- También espera a los sub-issues: un issue padre no se despacha mientras tenga hijos sin terminar.
- Consecuencia para "olas": si cada issue de la Ola 2 está *blocked by* los de la Ola 1 y `Done` está en `terminal_states`, la Ola 2 arranca sola cuando la Ola 1 llega a `Done`.

### 0.4 MCP de Linear con escritura (en tu WSL)

**Comando**
```bash
claude mcp add --transport http linear https://mcp.linear.app/mcp
claude            # dentro: /mcp → linear → Authenticate (OAuth en el navegador)
```
**Resultado esperado:** `claude mcp list` muestra `linear: https://mcp.linear.app/mcp (HTTP) - ✓ Connected`.
**Cómo verificar:** en Claude Code: "Lista mis equipos de Linear" → responde con tu equipo de alfredohernandez@30x.com.
**Plan B:** API key por header: `claude mcp add --transport http linear https://mcp.linear.app/mcp --header "Authorization: Bearer lin_api_..."`.
**Ojo:** no usar `/readonly` (el de la E6). OpenSymphony **no** usa este MCP: necesita su propia `LINEAR_API_KEY` (Settings → Security & access → Personal API keys).

### 0.5 Línea base en verde de `qa-e2e`

**Comandos** (dos terminales)
```bash
# Terminal 1 · instalar y levantar la app
cd ~/c4/estacion8/repos/qa-e2e && npm ci && npx playwright install --with-deps chromium
cd demo-app && npm ci && npm run dev          # puerto 3000

# Terminal 2 · pruebas
cd ~/c4/estacion8/repos/qa-e2e/demo-app && npm run test:unit
cd .. && npx bddgen && npx playwright test --project=chromium --project=bdd
```
**Resultado esperado:** Vitest `15 passed`; Playwright `8 passed` (4 chromium + 4 bdd).
**Cómo verificar:** el resumen final de cada comando.
**Plan B:** si falla por puerto ocupado, `lsof -i :3000` y matar el proceso. Si Chromium no baja, apunta a un Chrome del sistema con `launchOptions.executablePath` en una config local no versionada (así se corrió en el ensayo).
**Ojo:** `npm test` en la raíz de `qa-e2e` corre **Playwright con todos los proyectos** (incluido Firefox, que falla en WSL); no corre Vitest. Vitest está en `demo-app` (`npm run test:unit`).

### 0.6 Prueba de humo: OpenSymphony + ACP + Claude (en tu WSL)

Objetivo: probar con un caso mínimo, antes de la Fase 1, las cinco cosas que nadie documenta juntas:
- (a) OpenSymphony despacha a Claude por ACP;
- (b) el agente ve las skills de `.claude/skills/`;
- (c) el agente escribe en Linear;
- (d) se respeta "blocked by";
- (e) cada issue queda en su propio workspace o worktree.

Todo pasa en un repo aislado (`~/os-smoke`) y en un proyecto de Linear desechable, sin tocar c4.

**0.6.1 Preparar Linear (a mano, 3 min)**
1. Linear → Settings → Security & access → Personal API keys → crea una (`lin_api_...`).
2. Crea el proyecto **"30X · E8 Smoke"** en tu equipo. Copia el **slugId**, la parte final de la URL del proyecto (`.../project/30x-e8-smoke-<slugId>/...`). Plan B: pásale a `migrate`/`doctor` el slug completo.
3. Crea dos issues en ese proyecto, ambos en `Todo`:
   - **SMOKE-A** "Smoke A: crear archivo".
   - **SMOKE-B** "Smoke B: crear archivo", con *Blocked by* → SMOKE-A.

**0.6.2 Instalar y preparar**
```bash
rustup update stable && cargo install opensymphony --locked          # ~30 min
npm i -g @agentclientprotocol/claude-agent-acp@0.101.0
command -v claude-agent-acp                                            # el binario existe
export LINEAR_API_KEY=lin_api_...
~/c4/estacion8/orquestacion/smoke/setup-smoke.sh <slugId>
```
**Resultado esperado:** `doctor` termina sin `[FAIL]` (dos `[WARN]` normales: workspace compartido y modo trusted-machine).
**Cómo verificar:** existen `~/os-smoke/.claude/skills/linear/` y `~/.opensymphony/e8-smoke.yaml`.
**Plan B:** si `doctor` falla en `config`, compara tu YAML con `config.template.yaml`. El parser central es estricto y rechaza claves desconocidas.

**0.6.3 Lanzar**
```bash
cd ~/os-smoke && opensymphony run --config ~/.opensymphony/e8-smoke.yaml
# en otra terminal, para ver el estado:
opensymphony tui     # o: curl -s 127.0.0.1:2468/api/v1/snapshot | jq
```
**Resultado esperado en ~2–5 min:**
- SMOKE-A pasa a `In Progress` y luego a `In Review`, y tiene **un comentario** con `pwd`, la rama `smoke/SMOKE-A`, `git worktree list`, `git log` y la lista de skills (debe incluir `linear`).
- **SMOKE-B sigue en `Todo` sin despacharse** (bloqueado).

**Luego:** mueve SMOKE-A a `Done` a mano y **espera hasta ~1–2 min**. El poll de 5 s solo refresca lo que ya está corriendo. La búsqueda de issues nuevos para despachar (con `blocked_by` fresco) corre cada **60 s** (`DISPATCH_DISCOVERY_INTERVAL_MS` en `scheduler.rs`), y la foto completa del tracker cada hora o al reiniciar. Pasado ese tiempo, SMOKE-B se despacha y termina igual.
**Plan B:** si a los 2 min no se despacha, detén `run` con Ctrl+C y vuelve a lanzarlo. Al arrancar hace una foto completa y despacha a B de inmediato.

**Cómo verificar cada punto:**
| | Señal |
|---|---|
| (a) ACP + Claude | El comentario existe y dice el modelo |
| (b) Skills | La lista del comentario incluye `linear` |
| (c) Linear | Los cambios de estado y el comentario los hizo el agente |
| (d) Blocked by | SMOKE-B no arranca hasta que SMOKE-A está en `Done` |
| (e) Aislamiento | El `pwd` está bajo `~/.opensymphony/workspaces/e8-smoke/` y `git worktree list` muestra el checkout |

**Plan B por síntoma:**
- El agente no arranca y la TUI muestra un error de auth → corre `claude` una vez en WSL para iniciar sesión, o exporta `ANTHROPIC_API_KEY` y agrégala a `env_refs` del perfil.
- El agente se queda esperando un permiso → cambia `permissions.mode` a `operator` y respóndelo desde la TUI. Si así funciona, el problema es `allow_once`.
- No aparece `linear` en las skills → el adaptador no cargó `.claude/skills/`. Prueba con `CLAUDE_CONFIG_DIR` apuntando a tu `~/.claude` y avísame.
- El workspace sale vacío o sin git (TUI: `runtime: failed`, `branch: unavailable`, `fatal: not a git repository`) → falta `hooks.after_create`. El kit ya lo trae desde el ensayo 2. Si tu YAML es viejo, vuelve a correr `setup-smoke.sh` y limpia el estado (ver Registro, ensayo 2).
- `agent=down (not_selected)` en la barra de arriba **es normal con ACP**: es el indicador del servidor de OpenHands, que no se usa.
- SMOKE-B arranca antes de tiempo → revisa que la relación sea *Blocked by* (no *Related*) y que `Done` esté en `terminal_states`.

**Limpieza:** `Ctrl+C` en `run`, `rm -rf ~/os-smoke ~/.opensymphony/workspaces/e8-smoke ~/.opensymphony/state/e8-smoke`. Archiva el proyecto Smoke en Linear cuando quieras.

### 0.7 Plan B global: orquestar sin OpenSymphony (solo si la prueba 0.6 falla)

Claude Code como orquestador, sin daemon externo:
- La skill `orquestar-olas` lee Linear con el MCP, arma el grafo con los "blocked by" y lanza un subagente por issue listo.
- Subagente `dev-fbk`: `isolation: worktree`, `skills: [implementar-spec]`, rama `fbk-01/<ID>`, un puerto por worktree (3001, 3002…; `BASE_URL` ya lo lee `playwright.config.ts`).
- Subagente `verificador-fbk`: sin `Edit`/`Write`. Corre las pruebas y comenta en Linear.
- El orquestador abre el PR y mueve el issue a `Done`, o relanza al dev (máximo 2 reintentos).
- `.claude/settings.json` niega `git merge`, `git push --force`, `git push origin main` y `gh pr merge`.

Equivalencias para clase: el polling de Linear se vuelve la skill orquestadora; el workspace por issue, `isolation: worktree`; `WORKFLOW.md`, el prompt de `dev-fbk`; y el filtro de bloqueados, el que hace el orquestador.

Por probar si se activa:
- que el subagente vea el MCP de Linear;
- que `skills:` precargue `implementar-spec`;
- que `implementar-spec` no se detenga a pedir aprobación dentro de un subagente.

### Registro Fase 0 (ensayo 2026-11-06)

Funcionó:
- Vitest 15/15 y Playwright chromium + bdd 8/8 en un clon limpio de `rework/estacion8` @ 365e131.
- `claude mcp add --transport http linear https://mcp.linear.app/mcp` se registra bien (la conexión real requiere tu OAuth).
- `cargo install opensymphony --locked` 3.0.0 compila (28 min) e instala.
- `claude-agent-acp` 0.101.0 responde el handshake ACP v1.
- `setup-smoke.sh` deja `doctor` sin fallas con el perfil ACP `claude`.
- `opensymphony run --dry-run` llega hasta la consulta a Linear. Desde el sandbox no hay red a `api.linear.app`, así que el despacho real se prueba en tu WSL (0.6).

Falló o difiere de lo planeado:
- **OpenSymphony no soporta Claude Code de forma nativa.** Decisión: perfil ACP + `claude-agent-acp`, pendiente de la prueba de humo 0.6.
- `opensymphony init` necesita `api.github.com` para bajar la plantilla. En el sandbox estaba bloqueado y se clonó la plantilla con git. En tu WSL `init` debería funcionar normal.
- La plantilla oficial asume estados `Human Review`/`Merging`/`Rework` y una skill `land` que hace merge. Hay que adaptarla.
- La ruta real es `estacion8/repos/qa-e2e`, no `estacion8/qa-e2e`.
- `npm test` no es Vitest (ver 0.5).
- `demo-app` **no tiene zod** como dependencia; FBK-01 tendría que agregarlo.
- No hay `webServer` en `playwright.config.ts`: la app se levanta a mano en el 3000.

### Registro Fase 0 · ensayo 2 en WSL (2026-11-06, 15:21)

Falló:
- La TUI mostró **EST-5 SMOKE-A `[failed / Todo]`**, con `branch: unavailable`, `retries: 0`, `fatal: not a git…` y `agent=down (not_selected)`. Nunca se lanzó la sesión ACP.
- **Causa:** la config tenía `hooks.after_create: null`, confiando en `use_shared_git_worktrees: true`. La 3.0.0 ignora esa bandera en `legacy_single`, así que el workspace quedó vacío y el `before_run` (`git status`) falló.
- **Corrección:** `config.template.yaml` ahora trae `after_create: git clone --quiet file://__HOME__/os-smoke .` y `use_shared_git_worktrees: false`.

Para reintentar (con `run` detenido):
```bash
cd ~/c4 && git pull
~/c4/estacion8/orquestacion/smoke/setup-smoke.sh <slugId>          # regenera el YAML
rm -rf ~/.opensymphony/workspaces/e8-smoke ~/.opensymphony/state/e8-smoke
cd ~/os-smoke && opensymphony run --config ~/.opensymphony/e8-smoke.yaml
```
Hay que borrar el estado porque el workspace fallido se conservó (`retain_failed: true`) y el estado guarda el intento. Si no lo borras, el issue puede quedarse estacionado.

### Registro Fase 0 · ensayo 3 en WSL (2026-11-06, 15:27)

Funcionó. Comentario del agente en EST-5 (SMOKE-A):
- (a) ✅ ACP + Claude. El modelo reportado es `claude-opus-5-5`, el default del login de Claude Code.
- (b) ✅ Ve la skill `linear` del repo. **También ve las skills de usuario de `~/.claude`** (`evaluate-spec`, `create-implementation-plan`…), porque el adaptador carga `settingSources: user`.
- (c) ✅ Comentó en Linear con la skill GraphQL.
- (e) ✅ Workspace `~/.opensymphony/workspaces/e8-smoke/EST-5`, rama `smoke/EST-5`, commit propio. Es un clon (`git worktree list` muestra solo ese checkout).
- (d) ⏳ Pendiente: mover EST-5 a Done y ver que SMOKE-B se despache.

Falló o difiere:
- El equipo EST **no tiene estado `In Review`** (solo Todo, Backlog, In Progress, Done, Canceled, Duplicate). Se crea en Linear → Settings → Teams → EST → Workflow, con tipo *Started*. Sin ese estado, el issue se queda en `In Progress`, que es activo, y se puede volver a despachar hasta llegar a `max_turns`.

Decisiones para las Fases 5 y 6:
- Las skills del ejercicio van en `.claude/skills/` del repo y el prompt de `WORKFLOW.md` las cita por ruta. Así no dependen de lo que cada estudiante tenga en `~/.claude`.
- Hay que fijar el modelo de los agentes con `session.model` en el perfil ACP, para controlar el costo con 3 agentes en paralelo.

### Registro Fase 0 · ensayo 4 en WSL (2026-11-06, 15:41)

- (d) ✅ **"Blocked by" respetado:** SMOKE-B no se despachó mientras SMOKE-A estaba abierto.
- ⚠️ Después de mover SMOKE-A a Done, B no arrancó solo dentro del tiempo que esperamos. Al reiniciar `opensymphony run` se despachó y terminó en `In Review`.
- Explicación del código: el desbloqueo no es inmediato. El descubrimiento de candidatos corre cada 60 s y la foto completa cada hora o al reiniciar. **Para clase:** avisar que las olas avanzan con hasta ~1 min de retraso, y tener a la mano el reinicio de `run` como plan B. Pendiente confirmar si a los 2 min arranca sin reiniciar.

**Fase 0 cerrada:** (a)–(e) verificados. Ajustes pendientes para las Fases 4–6: estado `In Review` en el equipo, skills en `.claude/skills/` del repo y `session.model` en el perfil ACP.

---

## Fase 1 · Spec FBK-01

### 1.1 Revisar que el código permita la feature

**Prompt (Claude Code, en `estacion8/repos/qa-e2e`):**
> Antes de escribir la spec FBK-01, revisa `demo-app/app/page.tsx`, `demo-app/app/api/chat/route.ts` y `demo-app/lib/agent.ts`. Dime dónde se renderiza cada mensaje del bot, cómo están las rutas de API y qué le falta al código para calificar cada respuesta con 👍/👎. No escribas código.

**Esperado:**
- Los mensajes del bot se renderizan en `page.tsx` con `data-testid="agent-message"` y `key={i}`, **sin ID**.
- Solo existe `POST /api/chat`, que devuelve `{ response }`.
- Hay que agregar un `messageId` por respuesta y `zod`, que no está en `demo-app/package.json`.

**Verificar:** `grep -n "agent-message\|key=" demo-app/app/page.tsx` y `grep zod demo-app/package.json` (sin resultados).
**Plan B:** si la estructura cambió, revisa `git log -3 -- demo-app/`.

### 1.2 Escribir la spec v1 (incompleta a propósito)

**Archivo:** `estacion8/repos/qa-e2e/docs/specs/FBK-01.md`. Va junto al proyecto, como `qa-crew/specs/`.

**Prompt:**
> Escribe `docs/specs/FBK-01.md` con 9 secciones (1 Problema y usuario, 2 Objetivo y éxito, 3 Alcance / fuera de alcance, 4 RF, 5 CA, 6 Diseño y contratos, 7 Plan de pruebas, 8 Supuestos S y Preguntas P, 9 Riesgos R) para: 👍/👎 por respuesta del bot, una vez por mensaje con cambio de voto, motivo opcional ≤ 200 con 👎, `POST /api/feedback` con zod y store en memoria, `GET /api/feedback/stats` (totales, % satisfacción, últimos 5 motivos) y `/admin/feedback`. **Deja a propósito dos vacíos:** el CA del panel sin nada medible y sin decir qué pasa si el usuario vota dos veces el mismo mensaje.

**Esperado:** 6 RF, 13 CA y contratos de los dos endpoints. Los vacíos que se plantaron:
- **CA-12** (panel): "muestra la información de forma clara y fácil de leer". No es observable: no dice qué textos ni qué `data-testid`.
- **Doble voto:** RF-01 dice "una sola vez" y también "puede cambiar su voto", pero no dice qué hace `POST /api/feedback` con un segundo voto del mismo `messageId` (¿reemplaza?, ¿409?) ni cómo cuenta en las stats. No está en las preguntas abiertas: queda escondido.
- **Bonus no planeado:** CA-09 usa conteos absolutos y R-01 dice "comparar diferencias". El evaluador debería marcarlo en coherencia.

**Verificar:** `grep -c "^| CA-" docs/specs/FBK-01.md` → `13`.

**Plan B:** si el agente "arregla" los vacíos por iniciativa propia, pídele: "deja CA-12 y RF-01 tal como te los describí".

### Registro Fase 1 (2026-11-06)

Funcionó:
- La estructura permite la feature con dos ajustes: `messageId` generado en el cliente (`crypto.randomUUID()`), sin cambiar el contrato de `/api/chat`, y `zod` como dependencia nueva.

Difiere del prompt original:
- **La plantilla de 9 secciones con IDs RF/CA no está en el repo.** Venía en `skills-workshop-e6.zip` (`create-prd`). La reconstruí con los IDs RF/CA/S/P/R del contexto. Si quieres la exacta, sube el zip.
- **`evaluate-spec` del repo (`qa-crew/skills/evaluate-spec`) no usa 0–3 ni 18 puntos.** Califica 14 criterios en tres lentes (P1–P6, T1–T4, D1–D4) como Cumple/Parcial/Falta, y pone una nota A–D **por ola**. A y B pasan a planificación. La regla "críticos ≥ 2, ningún 0, ≥ 13/18" es de `review-prd` de la E6, que tampoco está en el repo. Hay que decidirlo antes de la Fase 2.

---

## Fase 2 · Evaluar la spec

Todo se corre desde `estacion8/repos/qa-e2e`. Las skills del ejercicio están en su `.claude/skills/`: `evaluate-spec` (copiada de `qa-crew/skills`), `create-implementation-plan` (de `estacion6/skills`, idéntica a la de `qa-crew`), `improve-spec` (nueva), `convert-tasks-to-linear` y `linear` (de la plantilla de OpenSymphony, adaptadas) y `qa-testing` (ya estaba).

### 2.1 Evaluar la v1

**Prompt:**
> Usa la skill evaluate-spec sobre `docs/specs/FBK-01.md`. Divide en olas: Ola 1 (modelo + POST), Ola 2 (UI + stats + panel), Ola 3 (E2E + BDD). Guarda el resultado en `docs/specs/FBK-01-review-v1.md`.

**Esperado:** **C · C · C**. Vacíos críticos: P4 (no hay regla de doble voto) y T1 (CA-12 no es observable), más la coherencia entre CA-09 y R-01.
**Verificar:** `grep -n "| \*\*C\*\*" docs/specs/FBK-01-review-v1.md`.
**Plan B:** si sale B, el evaluador está siendo blando. Pregúntale: "¿qué CA prueba que el panel está bien? ¿qué pasa con un segundo POST del mismo messageId?".

### 2.2 Mejorar con improve-spec (iteración 1 de 2)

**Prompt:**
> Usa la skill improve-spec con `docs/specs/FBK-01-review-v1.md`. Si yo no contesto, aplica los defaults.

**Esperado:** 3 preguntas con su default:
1. Doble voto → reemplazo (upsert).
2. Panel → testids y coherencia con `/stats`.
3. Stats → valores absolutos solo en las unitarias.

La spec pasa a v2 con BR-FBK-01..05 y CA-14..20, y al final trae la sección "Cambios v2".

**Verificar:** `diff docs/specs/FBK-01-v1.md docs/specs/FBK-01.md | head -50` y `grep -c "^| CA-" docs/specs/FBK-01.md` → `20`.

### 2.3 Re-evaluar

**Esperado:** `docs/specs/FBK-01-review.md` con **A · A · B**. La B es porque la Ola 3 tiene un supuesto: la ruta de los steps BDD.

**Para clase:** muestra lado a lado `FBK-01-review-v1.md` y `FBK-01-review.md`, y `FBK-01-v1.md` contra `FBK-01.md`.

### Registro Fase 2 (2026-11-06)
- ✅ v1 → C·C·C; v2 → A·A·B en **1 iteración** de `improve-spec`.
- Defaults aplicados (pendientes de confirmar, S-05 y S-06): el doble voto reemplaza, y los valores absolutos de las stats solo se prueban en las unitarias.
- Hallazgos de la skill: cita un ejemplo que no existe (`estacion6/ejemplos/spec-review-entrevista-ai.md`) y escribe por defecto en `docs/spec-review.md`; aquí se usa `docs/specs/FBK-01-review*.md`.
- El script `dev` de `demo-app` fija `-p 3000`. Para correr varios agentes en paralelo hay que usar `npm --prefix demo-app run dev -- -p <puerto>`.

---

## Fase 3 · Plan de implementación

### 3.1 Generar el paquete

**Prompt:**
> Usa create-implementation-plan con `docs/specs/FBK-01.md` (v2). Agrupa en olas como milestones: Ola 1 (modelo + POST), Ola 2 (UI, stats, panel en paralelo), Ola 3 (E2E + BDD). Títulos con prefijo "FBK-01 ·", `labels: [ola-N]` en el frontmatter, y cada tarea de una ola *blocked by* todas las de la ola anterior. Escribe en `docs/tasks/`.

**Esperado:** `docs/tasks/task-package.yaml`, `milestones.md` y 6 tareas:

| Ola | Tarea | Blocked by |
|---|---|---|
| 1 | TASK-001 Modelo, zod y store | — |
| 1 | TASK-002 POST /api/feedback | 001 |
| 2 | TASK-003 UI 👍/👎 + motivo | 001, 002 |
| 2 | TASK-004 computeStats + GET /stats | 001, 002 |
| 2 | TASK-005 Panel /admin/feedback (con `/stats` simulado) | 001, 002 |
| 3 | TASK-006 Flujo E2E + BDD | 003, 004, 005 |

**Diferencias con el boceto del prompt:**
- En la Ola 1, TASK-002 depende de TASK-001 porque importa sus tipos, así que la ola corre en 2 pasos.
- El panel (TASK-005) se prueba con `page.route` para poder ir en paralelo con `/stats` (TASK-004). La versión de CA-12 contra datos reales va en la Ola 3.

### 3.2 convert-tasks-to-linear

No se creó desde cero: viene en la plantilla oficial de OpenSymphony y ya tenía `validate`, `dry-run` y `apply`. Se adaptó para:
- aceptar etiquetas planas `ola-N`;
- buscar la skill `linear` en `.claude/skills/`;
- mostrar el detalle de cada issue en el dry-run.

**Comando:**
```bash
S=.claude/skills/convert-tasks-to-linear/scripts/convert_tasks_to_linear.py
python3 $S validate --manifest docs/tasks/task-package.yaml --repo-root .
python3 $S dry-run  --manifest docs/tasks/task-package.yaml --repo-root .
```
**Esperado:** `validation: ok` y 4 *creation waves* (001 / 002 / 003-004-005 / 006), con etiquetas `area:*` + `ola-N` y los *blocked by* de la tabla.
**Plan B:** si falta PyYAML: `pip install --user pyyaml`, o usa `uv run --script $S ...`.

### Registro Fase 3 (2026-11-06)
- ✅ `validate` ok y `dry-run` ok.
- ⚠️ **Decisión pendiente para la Fase 6 (integración entre olas):** cada agente abre su rama desde `estacion8/orquestacion-opensymphony` y ninguno hace merge. Así, la Ola 2 arrancaría **sin el código de la Ola 1**. Propuesta: "Done" = PR mergeado **a la rama del ejercicio** (no a `main`) por Alfredo después del verificador. Ese merge humano es el portón entre olas.

---

## Fase 4 · Subir a Linear (la corre Alfredo en WSL)

El sandbox no llega a `api.linear.app`, así que el `apply` se corre en WSL.

### 4.1 Preparar Linear (a mano)
1. En el equipo **EST** → Settings → Workflow, crea el estado **`In Review`** de tipo *Started*.
2. Crea el proyecto **"30X · E8 Orquestación"** en EST y copia su **slugId** (la parte final de la URL).

### 4.2 Dry-run y apply
```bash
cd ~/c4 && git pull && cd estacion8/repos/qa-e2e
export LINEAR_API_KEY=lin_api_...
S=.claude/skills/convert-tasks-to-linear/scripts/convert_tasks_to_linear.py
python3 $S dry-run --manifest docs/tasks/task-package.yaml --repo-root .
python3 $S apply   --manifest docs/tasks/task-package.yaml --repo-root . --project-slug <slugId> --team-key EST
```
**Esperado:**
- 3 milestones (Ola 1/2/3).
- 6 issues con título `FBK-01 · …`, etiquetas `area:*` + `ola-N` y los *blocked by* de la tabla de la Fase 3.
- El archivo `docs/tasks/linear-publish.yaml` con el mapeo `TASK-00N → EST-NN`.

**Verificar:**
- En Linear, EST-?? (TASK-003) muestra "Blocked by" con TASK-001 y TASK-002.
- `cat docs/tasks/linear-publish.yaml`.
- Haz commit de `linear-publish.yaml` en la rama del ejercicio.

**Plan B:**
- Si falla con `Linear helper not found`, revisa que exista `.claude/skills/linear/scripts/linear_graphql.py`.
- Si falla por falta de PyYAML: `pip install --user pyyaml`.
- Si el proyecto tiene varios equipos y no pasaste `--team-key`, el script lo pide.

---

## Fase 5 · Tests primero (en rojo)

**Prompt:**
> Usa la skill qa-testing. Para cada tarea de `docs/tasks/`, genera las pruebas a partir de sus CA: unitarias con Vitest para la validación y las stats, API con un builder en `fixtures/`, y E2E/BDD con el POM. Primero el POM y después los tests. Marca cada test con el tag `@TASK-00N`. Corre todo y confirma que solo fallan las pruebas nuevas.

**Qué se generó:**

| Archivo | Tarea(s) | Nivel |
|---|---|---|
| `demo-app/__tests__/feedback.test.ts` | 001 | Vitest: esquema zod + store (11) |
| `demo-app/__tests__/feedback-stats.test.ts` | 004 | Vitest: `computeStats` (5) |
| `fixtures/feedback-builders.ts` | 002, 004 | builder de la API (regla §5 de `qa-testing`) |
| `tests/api/feedback-api.spec.ts` | 002 (7), 004 (3) | Playwright `request`, proyecto **`api`** nuevo, sin paralelismo |
| `pages/HomePage.ts` (+ métodos), `pages/FeedbackPanelPage.ts` | 003, 005, 006 | POM, primero (regla §8) |
| `tests/e2e/feedback.spec.ts` | 003 (7), 005 (2), 006 (2) | E2E; el archivo corre en orden en un worker |
| `tests/features/feedback.feature` + `steps/feedback.steps.ts` | 006 | BDD (CA-15) |

**Comando:**
```bash
cd estacion8/repos/qa-e2e
npm --prefix demo-app run test:unit
npx bddgen && npx playwright test --project=chromium --project=bdd --project=api
```
**Esperado (rojo):**
- Vitest: 2 archivos fallan (no existen `lib/feedback*`) y 15 pasan.
- Playwright: **22 fallan** (404 o elementos que no existen) y los **8 originales pasan**.

**Verificar por tarea:** `npx playwright test --project=chromium --grep @TASK-003` (y así cada una).

### Registro Fase 5 (2026-11-06)
- ✅ Rojo confirmado: 22 de Playwright y 2 archivos de Vitest. Regresión 8/8 + 15/15 en verde.
- Decisiones:
  - Los **POM y los steps BDD se escriben en la Fase 5**. Si no, los imports rotos y `bddgen` ("missing steps") tumban la suite de todos los agentes. Las tareas 003, 005 y 006 ahora solo ajustan el POM si el DOM real lo exige.
  - Se agrega el proyecto `api` a `playwright.config.ts`. La skill pide `tests/api/` y builders, y ningún proyecto existente corría esa carpeta.
  - `feedback.spec.ts` usa `mode: 'default'` y no `serial`: con `serial`, al primer fallo se saltaban 10 tests.
  - Tags `@TASK-00N` en cada test. El verificador de cada issue usa `--grep @TASK-00N` y la regresión `--grep-invert "@TASK-"`.
- **Para el verificador (Fase 7):** el comando del prompt (`--project=chromium --project=bdd`) no corre los tests de API. Hay que agregar `--project=api` o usar el comando del *Test Plan* de cada issue.

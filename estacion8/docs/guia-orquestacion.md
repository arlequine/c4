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
- Ruta posible para Claude Code (no documentada por OpenSymphony, sin probar): el adaptador de terceros `@agentclientprotocol/claude-agent-acp` (binario `claude-agent-acp`, corre sobre el Claude Agent SDK) como perfil ACP genérico:
  ```yaml
  routing:
    harness: acp
    harness_profile: claude
  acp:
    profiles:
      claude:
        command: /ruta/absoluta/a/claude-agent-acp   # ruta absoluta, args literales
        args: []
        transport: stdio
        protocol_versions: [1]
        permissions:
          mode: operator        # o allow_once para correr sin supervisión
  ```
  Por verificar: que el adaptador cargue `CLAUDE.md` y las skills de `.claude/skills/` (incluida `implementar-spec`) y cómo se autentica (login de Claude o `ANTHROPIC_API_KEY`).
- Instalación según su README:
  ```bash
  cargo install opensymphony           # requiere Rust estable
  opensymphony install openhands       # harness por defecto (Python 3.13 + uv + LLM_API_KEY)
  export LINEAR_API_KEY="lin_api_..."
  cd <repo> && opensymphony init       # genera WORKFLOW.md, config.yaml y .agents/skills/linear/
  opensymphony doctor
  opensymphony run
  ```
- Conexión con Linear: **API key** (`LINEAR_API_KEY`), solo GraphQL. El orquestador lee Linear; el agente escribe en Linear con la skill local `.agents/skills/linear/` (script `linear_graphql.py`). No usa el MCP de Linear. En `WORKFLOW.md`: `tracker.kind: linear` y `tracker.project_slug` (el `slugId` del proyecto).
- Workspaces: carpetas deterministas por issue. La doc **no dice que sean git worktrees**; eso se arma en el hook `after_create`.

### 0.3 ¿Respeta las relaciones "blocked by"?

- La especificación Symphony (fuente #1 de OpenSymphony) dice que un issue en estado **Todo** solo es elegible para despacho si **no tiene bloqueadores en estado no terminal**.
- OpenSymphony deriva `blocked_by` de las `inverseRelations` de Linear con tipo `blocks`, y las muestra en su task graph.
- **Matiz:** la regla solo aplica a issues en *Todo*. Un issue que alguien mueva a *In Progress* a mano se despacha aunque esté bloqueado. Y la doc de OpenSymphony que revisé no afirma explícitamente que su scheduler aplica la regla; lo hereda de la spec.
- Consecuencia para "olas": si cada issue de la Ola 2 está *blocked by* los de la Ola 1 y "Done" es estado terminal, la Ola 2 arranca sola cuando la Ola 1 termina.

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

### Registro Fase 0 (ensayo 2026-11-06)

Funcionó:
- Vitest 15/15 y Playwright chromium + bdd 8/8 en un clon limpio de `rework/estacion8` @ 365e131.
- `claude mcp add --transport http linear https://mcp.linear.app/mcp` se registra bien (la conexión real requiere tu OAuth).

Falló o difiere de lo planeado:
- **OpenSymphony no soporta Claude Code de forma nativa** (OpenHands, Codex o perfiles ACP). La vía ACP + `claude-agent-acp` es posible pero no está documentada ni probada. Pendiente de decisión.
- La ruta real es `estacion8/repos/qa-e2e`, no `estacion8/qa-e2e`.
- `npm test` no es Vitest (ver 0.5).
- `demo-app` **no tiene zod** como dependencia; FBK-01 tendría que agregarlo.
- No hay `webServer` en `playwright.config.ts`: la app se levanta a mano en el 3000.

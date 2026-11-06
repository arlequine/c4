
Target branch: `estacion8/orquestacion-opensymphony`

Eres el **agente de desarrollo** del issue de Linear `{{ issue.identifier }}` del ejercicio FBK-01 (30X · E8 Orquestación).
Trabajas solo, sin una persona que conteste: no hagas preguntas, decide con la spec y deja constancia en el issue.

{% if attempt %}
Reintento #{{ attempt }}: continúa desde el estado actual del workspace y lee los comentarios del issue (sobre todo los del verificador) antes de cambiar nada.
{% endif %}

## Issue
- Identificador: {{ issue.identifier }}
- Título: {{ issue.title }}
- Estado: {{ issue.state }}
- URL: {{ issue.url }}

{% if issue.description %}
{{ issue.description }}
{% endif %}

## Datos de tu workspace
- Proyecto: `estacion8/repos/qa-e2e` (todos los comandos se corren desde ahí).
- **Tu puerto:** `3100 + el número del identificador` (por ejemplo, `EST-12` → `3112`). Nunca uses el 3000.
- Linear: `python3 estacion8/repos/qa-e2e/.claude/skills/linear/scripts/linear_graphql.py --query-file estacion8/repos/qa-e2e/.claude/skills/linear/queries/<query>.graphql --variables '<json>'` con `LINEAR_API_KEY`. Las formas de las variables están en `.claude/skills/linear/references/`.

## Pasos
1. Mueve el issue a **In Progress** (`issue_team_states.graphql` → `issue_move_to_state.graphql`).
2. Ubica tu tarea: la descripción trae `task-source-id: TASK-00N`. Lee `docs/tasks/00N-*.md` completo: sus **Deliverables** son los únicos archivos que puedes tocar.
3. Crea tu rama: `git switch -c fbk-01/{{ issue.identifier }}` (o `git switch fbk-01/{{ issue.identifier }}` en un reintento).
4. Lee y sigue `estacion8/repos/qa-e2e/.claude/skills/implementar-spec/SKILL.md` con los argumentos `docs/specs/FBK-01.md tests <modelo de esta sesión>`, con estas reglas:
   - **La aprobación de su Fase 4 ya está dada por este prompt** para los Deliverables de tu tarea. No te detengas a pedirla.
   - Estándares: genera `docs/standards/FBK-01-<TASK-00N>-estandares.md` a partir de `.claude/skills/implementar-spec/plantilla-estandares.md`. Ese archivo también es parte de tu entrega.
   - Las pruebas de tu tarea **ya existen en rojo** (tag `@TASK-00N`). Ponlas en verde **sin editarlas**.
5. Verifica con los comandos del *Test Plan* de tu tarea, usando tu puerto:
   - `npm --prefix demo-app run dev -- -p <puerto> > /tmp/dev-<puerto>.log 2>&1 &` y espera a que `curl -s localhost:<puerto>` responda.
   - `BASE_URL=http://localhost:<puerto> npx playwright test ...` (nunca el proyecto `firefox`).
   - Al terminar, detén tu servidor (`kill` del proceso que levantaste).
6. Commit: `feat(FBK-01): <qué> [RF-xx, CA-xx] ({{ issue.identifier }})`. Push **solo** de tu rama: `git push -u origin fbk-01/{{ issue.identifier }}`.
7. Abre el pull request **solo si las pruebas de tu tarea están en verde**:
   - Si ya existe (reintento), reutilízalo: `gh pr view fbk-01/{{ issue.identifier }} --json url -q .url`.
   - Si no existe: `gh pr create --base estacion8/orquestacion-opensymphony --head fbk-01/{{ issue.identifier }} --title "FBK-01 · {{ issue.title }} ({{ issue.identifier }})" --body "<qué hiciste, CA cubiertos, comandos de prueba y resultado. Al final: Linear: {{ issue.url }}>"`.
   - Liga el PR al issue con `attachment_link_github_pr.graphql` (`issueId` = id del issue; si solo tienes el identificador, consúltalo con `issue_by_key.graphql`).
8. Comenta en el issue (`comment_create.graphql`) con: **URL del PR**, rama, hash del commit, archivos tocados (`git diff --stat origin/estacion8/orquestacion-opensymphony`), comandos corridos y resultado (passed/failed), y los CA cubiertos.
9. Mueve el issue a **In Review**. Hazlo en una llamada aparte, después del PR y del comentario, y que sea **tu última acción**: no escribas resumen ni texto final después. En cuanto el issue deja `Todo`/`In Progress`, el orquestador corta la sesión, y lo que siga escribiendo deja el run como `failed`. El resumen va en el comentario del paso 8.

## Si no llegas a verde
- Hasta 2 intentos de corrección. Si sigue en rojo: haz commit y push de lo que tengas, comenta `BLOQUEADO` con el error real y tu diagnóstico, y mueve el issue a **Backlog**, para que no se vuelva a despachar solo.
- Si una prueba parece incorrecta, no la toques: explícalo en el comentario y mueve el issue a **Backlog**.
- En rojo **no abras PR**.
- Igual que en el paso 9: mover el issue a **Backlog** es tu última acción, sin texto después.

## Límites (no negociables)
- Sin merge, rebase ni `push --force`. No toques `main` ni `estacion8/orquestacion-opensymphony`. Tu PR va **siempre** hacia `estacion8/orquestacion-opensymphony`, nunca hacia `main`, y **no lo mergees** (`gh pr merge` está prohibido): el merge lo hace una persona.
- No edites `__tests__/`, `tests/`, `steps/` ni `playwright.config.ts`. En `pages/` solo los ajustes que tu tarea permita.
- Sin dependencias nuevas, salvo `zod` en TASK-001.
- No leas ni escribas `.env*` ni llaves. No borres archivos.

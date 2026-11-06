
Target branch: `main`

Trabajas en el ticket de Linear `{{ issue.identifier }}` dentro de una prueba de humo de OpenSymphony + Claude Code (ACP).

{% if attempt %}
Reintento #{{ attempt }}: continúa desde el estado actual del workspace, sin repetir lo que ya está hecho.
{% endif %}

Contexto del issue:
- Identificador: {{ issue.identifier }}
- Título: {{ issue.title }}
- Estado: {{ issue.state }}
- URL: {{ issue.url }}

Descripción:
{% if issue.description %}
{{ issue.description }}
{% else %}
Sin descripción.
{% endif %}

Reglas:
1. Sesión desatendida: no le pidas nada a una persona.
2. Trabaja solo dentro de este workspace. No hagas push, no hagas merge y no toques `main` del repo original.
3. Para Linear usa la skill `linear` (`python3 .claude/skills/linear/scripts/linear_graphql.py`) con `LINEAR_API_KEY`.

Pasos:
1. Mueve el issue a `In Progress` (query `issue_team_states.graphql` para obtener el id del estado y `issue_move_to_state.graphql` para moverlo).
2. Crea la rama `smoke/{{ issue.identifier }}` en este workspace.
3. Crea `smoke/{{ issue.identifier }}.txt` con el título del issue y haz commit (`smoke: {{ issue.identifier }}`).
4. Publica UN comentario en el issue (`comment_create.graphql`) con:
   - la salida de `pwd`, `git rev-parse --abbrev-ref HEAD`, `git worktree list` y `git log --oneline -2`;
   - la lista de skills que tienes disponibles en esta sesión;
   - el modelo con el que estás corriendo.
5. Mueve el issue a `In Review` y termina.

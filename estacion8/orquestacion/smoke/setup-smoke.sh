#!/usr/bin/env bash
# Prueba de humo: OpenSymphony 3.0.0 + perfil ACP + claude-agent-acp + Linear.
# Uso: LINEAR_API_KEY=lin_api_... ./setup-smoke.sh <slugId-del-proyecto-smoke>
# Crea ~/os-smoke (repo git aislado), ~/.opensymphony/e8-smoke.yaml y corre `opensymphony doctor`.
set -euo pipefail

SLUG="${1:?Falta el slugId del proyecto de Linear (lo que va al final de la URL del proyecto)}"
: "${LINEAR_API_KEY:?Exporta LINEAR_API_KEY antes de correr este script}"
HERE="$(cd "$(dirname "$0")" && pwd)"
ACP_BIN="$(command -v claude-agent-acp || true)"
[ -n "$ACP_BIN" ] || { echo "No encuentro claude-agent-acp. Instala: npm i -g @agentclientprotocol/claude-agent-acp@0.101.0"; exit 1; }
command -v opensymphony >/dev/null || { echo "No encuentro opensymphony. Instala: cargo install opensymphony --locked"; exit 1; }

# 1. Repo aislado para la prueba
if [ ! -d "$HOME/os-smoke/.git" ]; then
  mkdir -p "$HOME/os-smoke" && cd "$HOME/os-smoke"
  git init -q -b main
  echo "# os-smoke" > README.md
  # Skill de Linear de la plantilla oficial, en la ruta que lee Claude Code
  tmp="$(mktemp -d)"
  git clone -q --depth 1 https://github.com/kumanday/OpenSymphony-template "$tmp/tpl"
  mkdir -p .claude/skills && cp -r "$tmp/tpl/.agents/skills/linear" .claude/skills/linear
  rm -rf "$tmp"
  cp "$HERE/WORKFLOW.md" WORKFLOW.md
  git add -A && git commit -q -m "smoke: base"
fi

# 2. Config central
mkdir -p "$HOME/.opensymphony"
sed -e "s#__HOME__#$HOME#g" -e "s#__SLUG__#$SLUG#g" -e "s#__ACP_BIN__#$ACP_BIN#g" \
  "$HERE/config.template.yaml" > "$HOME/.opensymphony/e8-smoke.yaml"

# 3. Preflight
cd "$HOME/os-smoke"
opensymphony doctor --config "$HOME/.opensymphony/e8-smoke.yaml"
echo
echo "Listo. Para lanzar: cd ~/os-smoke && opensymphony run --config ~/.opensymphony/e8-smoke.yaml"

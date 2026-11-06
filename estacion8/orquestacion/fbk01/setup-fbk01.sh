#!/usr/bin/env bash
# Fase 6 · ejercicio FBK-01: genera ~/.opensymphony/e8-fbk01.yaml y corre `opensymphony doctor`.
# Uso: LINEAR_API_KEY=lin_api_... ./setup-fbk01.sh <slugId del proyecto "30X · E8 Orquestación">
set -euo pipefail

SLUG="${1:?Falta el slugId del proyecto de Linear (la parte final de la URL del proyecto)}"
: "${LINEAR_API_KEY:?Exporta LINEAR_API_KEY antes de correr este script}"
HERE="$(cd "$(dirname "$0")" && pwd)"
ACP_BIN="$(command -v claude-agent-acp || true)"
[ -n "$ACP_BIN" ] || { echo "No encuentro claude-agent-acp. Instala: npm i -g @agentclientprotocol/claude-agent-acp@0.101.0"; exit 1; }
command -v opensymphony >/dev/null || { echo "No encuentro opensymphony. Instala: cargo install opensymphony --locked"; exit 1; }
[ -d "$HOME/c4/.git" ] || { echo "No encuentro ~/c4. Clona: git clone https://github.com/arlequine/c4.git ~/c4"; exit 1; }

# Los agentes hacen push de su rama fbk-01/* a GitHub: comprueba que git tiene credenciales.
git -C "$HOME/c4" ls-remote --exit-code origin estacion8/orquestacion-opensymphony >/dev/null \
  || { echo "git no puede leer origin. Corre: gh auth login && gh auth setup-git"; exit 1; }

mkdir -p "$HOME/.opensymphony"
sed -e "s#__HOME__#$HOME#g" -e "s#__SLUG__#$SLUG#g" -e "s#__ACP_BIN__#$ACP_BIN#g" \
  "$HERE/config.template.yaml" > "$HOME/.opensymphony/e8-fbk01.yaml"

cd "$HOME/c4"
opensymphony doctor --config "$HOME/.opensymphony/e8-fbk01.yaml"
echo
echo "Listo. Para lanzar: cd ~/c4 && opensymphony run --config ~/.opensymphony/e8-fbk01.yaml"

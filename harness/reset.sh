#!/usr/bin/env bash
# Volta o projeto ao esqueleto commitado (descarta TUDO que o modelo gerou).
# Preserva: .venv, docs/results.jsonl (ignorado pelo git) e tudo que está no .gitignore.
# Uso: harness/reset.sh        (mostra o que seria apagado e pede confirmação)
#      harness/reset.sh -y     (sem perguntar; para uso em scripts)
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Arquivos rastreados modificados (serão revertidos):"
git status --short --untracked-files=no || true
echo "Arquivos novos (serão apagados):"
git clean -nd -- backend frontend docs harness | sed 's/^Would remove /  /'

if [[ "${1:-}" != "-y" ]]; then
  read -r -p "Continuar? [s/N] " ans
  [[ "$ans" =~ ^[sSyY]$ ]] || { echo "Cancelado."; exit 1; }
fi

git checkout -- .
git clean -fd -- backend frontend docs harness
find backend harness -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
echo "Reset concluído: projeto no commit $(git rev-parse --short HEAD)."

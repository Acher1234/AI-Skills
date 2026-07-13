#!/usr/bin/env bash
#
# 🛠️  setup.sh — bootstrap du dépôt hermes-script
# À lancer UNE fois après le clone :
#   ./setup.sh
#
# Active les hooks git versionnés (dossier .githooks/), dont le pre-commit
# qui bloque les secrets via gitleaks.
#
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Se placer à la racine du dépôt (là où est ce script)
cd "$(dirname "$0")"

echo -e "${YELLOW}🔧 Configuration des hooks git...${NC}"
git config core.hooksPath .githooks
echo -e "${GREEN}✔ core.hooksPath = .githooks${NC}"

# Vérifie que gitleaks est présent (utilisé par le hook pre-commit)
if command -v gitleaks >/dev/null 2>&1; then
  echo -e "${GREEN}✔ gitleaks détecté ($(gitleaks version 2>/dev/null | head -n1))${NC}"
else
  echo -e "${RED}⚠ gitleaks n'est pas installé.${NC}"
  echo "    macOS  : brew install gitleaks"
  echo "    Linux  : apt-get install gitleaks"
  echo -e "${YELLOW}    (Le hook pre-commit en a besoin pour scanner les secrets.)${NC}"
fi

echo -e "${GREEN}✅ Setup terminé.${NC}"

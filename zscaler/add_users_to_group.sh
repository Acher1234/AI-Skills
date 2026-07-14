#!/usr/bin/env bash
#
# Ajoute en masse des users ZIA à un groupe (+ département) en s'appuyant
# UNIQUEMENT sur les commandes déjà présentes du CLI Hermes (cli.py).
#
# Usage:
#   ./add_users_to_group.sh "Vo2 - Canada" "Canada" fichier1.json [fichier2.json ...]
#
# Les fichiers JSON sont au format export ZIA:
#   {"users":[{"Email Address [Required]":"...", ...}, ...]}
#
set -euo pipefail

if [[ $# -lt 3 ]]; then
  echo "Usage: $0 <group-name> <department-name> <users.json> [users2.json ...]" >&2
  exit 2
fi

GROUP_NAME="$1"; shift
DEPARTMENT_NAME="$1"; shift
FILES=("$@")

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${SCRIPT_DIR}/.venv/bin/python"
CLI="${SCRIPT_DIR}/cli.py"

# Extrait les emails uniques des fichiers JSON (via le python du venv).
emails="$("${PYTHON}" - "${FILES[@]}" <<'PY'
import json, sys
seen, out = set(), []
for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    for u in data.get("users", []):
        email = (u.get("Email Address [Required]") or "").strip()
        key = email.casefold()
        if email and key not in seen:
            seen.add(key)
            out.append(email)
print("\n".join(out))
PY
)"

total="$(printf '%s\n' "${emails}" | grep -c . || true)"
echo "Users à traiter: ${total}"
echo "Groupe: ${GROUP_NAME} | Département: ${DEPARTMENT_NAME}"
echo

ok=0; ko=0; i=0
while IFS= read -r email; do
  [[ -z "${email}" ]] && continue
  i=$((i + 1))
  printf '[%d/%d] %s ... ' "${i}" "${total}" "${email}"
  if "${PYTHON}" "${CLI}" zia set-groups \
        --username "${email}" \
        --group-name "${GROUP_NAME}" \
        --department-name "${DEPARTMENT_NAME}" \
        --add >/dev/null 2>/tmp/hermes_setgroups_err; then
    echo "OK"
    ok=$((ok + 1))
  else
    echo "ERREUR"
    sed 's/^/    /' /tmp/hermes_setgroups_err >&2
    ko=$((ko + 1))
  fi
done <<< "${emails}"

echo
echo "=== RÉSUMÉ ==="
echo "OK:     ${ok}"
echo "Erreurs:${ko}"

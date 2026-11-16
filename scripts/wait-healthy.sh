#!/usr/bin/env bash
# Rôle : attend que l'API réponde sur /health ; décide si la mise en service est saine.
# Exécution : ./scripts/wait-healthy.sh  (URL modifiable : HEALTH_URL=http://... ./scripts/wait-healthy.sh)
# Code 0 = « staging sain » ; code 1 = « staging non sain » -> déclenche le retour arrière.
set -uo pipefail

HEALTH_URL="${HEALTH_URL:-http://localhost:8080/health}"
ATTEMPTS="${ATTEMPTS:-12}"
DELAY="${DELAY:-5}"

for i in $(seq 1 "$ATTEMPTS"); do
  # -f : code d'erreur si HTTP >= 400 ; -s : silencieux ; -S : affiche quand même les erreurs ; --max-time : pas d'attente infinie.
  if body="$(curl -fsS --max-time 3 "$HEALTH_URL" 2>/dev/null)"; then
    echo "[$(date '+%H:%M:%S')] tentative $i/$ATTEMPTS : $body"
    echo "staging sain"
    exit 0
  fi
  echo "[$(date '+%H:%M:%S')] tentative $i/$ATTEMPTS : pas de réponse saine de $HEALTH_URL"
  [[ "$i" -lt "$ATTEMPTS" ]] && sleep "$DELAY"
done

echo "staging non sain après $ATTEMPTS tentatives ($HEALTH_URL)" >&2
exit 1

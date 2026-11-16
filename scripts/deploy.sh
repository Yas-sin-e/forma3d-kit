#!/usr/bin/env bash
# Rôle : met en service une version publiée (tag) en staging, avec retour arrière automatique.
# Exécution : ./scripts/deploy.sh v1.0.1
# Étapes : écrit IMAGE_TAG dans .env.deploy -> pull -> up -d -> wait-healthy.sh
#          sain : le tag est mémorisé dans .last-good-tag ; non sain : on revient au dernier tag sain.
# SKIP_PULL=1 : utilise une image déjà présente en local (répétition hors ligne de la soutenance).
set -uo pipefail

TAG="${1:-}"
if [[ ! "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Usage : $0 vX.Y.Z   (tag de version publié sur GHCR)" >&2
  exit 1
fi
cd "$(git rev-parse --show-toplevel)" || exit 1

if [[ ! -f .env.staging ]]; then
  echo "Fichier .env.staging absent : cp .env.staging.example .env.staging" >&2
  exit 1
fi

COMPOSE=(docker compose -p forma3d-staging -f compose.staging.yaml --env-file .env.deploy)
PREVIOUS="$(cat .last-good-tag 2>/dev/null || true)"

start_version() {
  echo "IMAGE_TAG=$1" > .env.deploy
  echo "== [$(date '+%H:%M:%S')] Mise en service de $1"
  if [[ "${SKIP_PULL:-0}" != "1" ]]; then
    "${COMPOSE[@]}" pull api || return 1
  fi
  "${COMPOSE[@]}" up -d
}

if start_version "$TAG" && ./scripts/wait-healthy.sh; then
  echo "$TAG" > .last-good-tag
  echo "== [$(date '+%H:%M:%S')] $TAG en service."
  exit 0
fi

echo "== [$(date '+%H:%M:%S')] $TAG non sain. Journaux de l'API :" >&2
"${COMPOSE[@]}" logs --tail=30 api >&2
if [[ -z "$PREVIOUS" || "$PREVIOUS" == "$TAG" ]]; then
  echo "== Aucun tag sain précédent connu : retour arrière impossible." >&2
  exit 1
fi
echo "== [$(date '+%H:%M:%S')] RETOUR ARRIÈRE vers $PREVIOUS" >&2
if start_version "$PREVIOUS" && ./scripts/wait-healthy.sh; then
  echo "== [$(date '+%H:%M:%S')] Retour arrière réussi : $PREVIOUS en service ; $TAG refusé." >&2
else
  echo "== Retour arrière ÉCHOUÉ : intervention manuelle nécessaire." >&2
fi
exit 1

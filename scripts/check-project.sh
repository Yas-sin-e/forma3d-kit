#!/usr/bin/env bash
# Rôle : contrôle automatique du dépôt Forma3D avant un commit, une PR ou une livraison.
# Exécution : ./scripts/check-project.sh [--strict] depuis n'importe quel dossier du dépôt ;
# lancé aussi par le job « test » du pipeline CI. Code de sortie 0 = succès, 1 = échec.
#
# Contrôles :
#   1. fichiers requis présents ;
#   2. aucun secret (.env), fichier de base locale (.sqlite3, .db) ni GLB généré suivi par Git ;
#   3. aucun marqueur de conflit de fusion dans les fichiers suivis ;
#   4. option --strict : l'arbre de travail doit être propre (git status --porcelain vide).

# -u : une variable non définie est une erreur ; -o pipefail : un pipeline échoue si une commande échoue.
# Pas de « -e » : on veut exécuter TOUS les contrôles puis donner le total des erreurs.
set -uo pipefail

STRICT=0
for arg in "$@"; do
  case "$arg" in
    --strict) STRICT=1 ;;
    -h|--help)
      echo "Usage : $0 [--strict]"
      echo "  --strict  échoue aussi si des modifications ne sont pas commitées"
      exit 0 ;;
    *)
      echo "[ECHEC] option inconnue : $arg (voir --help)" >&2
      exit 1 ;;
  esac
done

# On se place à la racine du dépôt : le script fonctionne quel que soit le dossier courant.
if ! ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  echo "[ECHEC] ce dossier n'est pas un dépôt Git." >&2
  exit 1
fi
cd "$ROOT" || exit 1

ERRORS=0
ok()   { echo "[OK]     $1"; }
fail() { echo "[ERREUR] $1" >&2; ERRORS=$((ERRORS + 1)); }

echo "== Contrôle du dépôt : $ROOT"

# 1. Fichiers requis : sans eux, l'application ne s'installe pas ou ne se construit pas.
REQUIRED_FILES=(
  README.md
  .gitignore
  .gitattributes
  .env.example
  backend/requirements.txt
  backend/app/main.py
  Dockerfile
  .dockerignore
  compose.yaml
  # Documents de projet (contrôles repris de l'ancien workflow CI)
  AGENTS.md
  PRODUCT.md
  DESIGN.md
  docs/ETAT.md
  docs/STRUCTURE.md
  docs/etapes/etape-01.md
  backend/README.md
  frontend/README.md
  backend/tests/test_health.py
)
for file in "${REQUIRED_FILES[@]}"; do
  if [[ -f "$file" ]]; then ok "présent : $file"; else fail "fichier manquant : $file"; fi
done

# 2. Rien de sensible ou de généré dans Git. « git ls-files » liste ce qui est SUIVI (pas ce qui existe).
TRACKED="$(git ls-files)"
if grep -Eq '(^|/)\.env$' <<<"$TRACKED"; then
  fail "un fichier .env est suivi par Git (secret potentiel)"
else
  ok "aucun fichier .env suivi"
fi
if grep -Eq '\.sqlite3?$|\.db$' <<<"$TRACKED"; then
  fail "un fichier de base de données locale (.sqlite3, .db) est suivi par Git"
else
  ok "aucun fichier de base locale suivi"
fi
if grep -Eq '^backend/(storage|data)/' <<<"$TRACKED"; then
  fail "des fichiers de backend/storage ou backend/data sont suivis (GLB, photos ou base locale)"
else
  ok "aucun fichier de backend/storage ou backend/data suivi"
fi

# 3. Marqueurs de conflit oubliés après une fusion. -I ignore les fichiers binaires.
CONFLICTS="$(git grep -I -l -E '^(<<<<<<<|>>>>>>>)( |$)' -- . ':!scripts/check-project.sh' 2>/dev/null || true)"
if [[ -n "$CONFLICTS" ]]; then
  fail "marqueurs de conflit dans : $(tr '\n' ' ' <<<"$CONFLICTS")"
else
  ok "aucun marqueur de conflit"
fi

# 3b. Contrat de port (leçon de l'incident v1.1.0) : le port d'écoute de l'image (EXPOSE, CMD,
# HEALTHCHECK) doit être celui que les fichiers Compose publient côté conteneur (« …:8080 »).
if [[ -f Dockerfile ]]; then
  IMAGE_PORT="$(sed -nE 's/^EXPOSE ([0-9]+).*/\1/p' Dockerfile | head -n1)"
  PORT_ERRORS=0
  if ! grep -Eq -- "--port\", \"${IMAGE_PORT}\"" Dockerfile || ! grep -Eq "127\.0\.0\.1:${IMAGE_PORT}/health" Dockerfile; then
    fail "Dockerfile : CMD ou HEALTHCHECK n'utilise pas le port EXPOSE ${IMAGE_PORT}"
    PORT_ERRORS=1
  fi
  for compose_file in compose.yaml compose.staging.yaml; do
    [[ -f "$compose_file" ]] || continue
    if ! grep -Eq "\"127\.0\.0\.1:[0-9]+:${IMAGE_PORT}\"" "$compose_file"; then
      fail "$compose_file ne publie pas le port ${IMAGE_PORT} de l'image (contrat de port rompu)"
      PORT_ERRORS=1
    fi
  done
  [[ "$PORT_ERRORS" -eq 0 ]] && ok "contrat de port respecté (image et Compose : ${IMAGE_PORT})"
fi

# 4. Garde-fou : en mode strict, on refuse de valider un arbre avec des changements non commités.
if [[ "$STRICT" -eq 1 ]]; then
  if [[ -n "$(git status --porcelain)" ]]; then
    fail "mode --strict : l'arbre de travail contient des modifications non commitées"
  else
    ok "mode --strict : arbre de travail propre"
  fi
fi

if [[ "$ERRORS" -eq 0 ]]; then
  echo "[SUCCES] tous les contrôles sont passés."
  exit 0
fi
echo "[ECHEC] $ERRORS erreur(s)." >&2
exit 1

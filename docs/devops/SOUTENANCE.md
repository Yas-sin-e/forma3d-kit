# Phase P9 — Scénario de soutenance (10 minutes, 4 pts)

## Préparation la veille

```bash
docker pull ghcr.io/yas-sin-e/forma3d:v1.0.1      # images en local : aucune dépendance réseau pendant la démo
docker pull ghcr.io/yas-sin-e/forma3d:v1.1.0
docker pull ghcr.io/yas-sin-e/forma3d:v1.1.1
docker pull postgres:17-alpine
docker compose down                               # port 8080 libre pour le staging
./scripts/deploy.sh v1.0.1                        # point de départ : v1.0.1 saine
```
Onglets ouverts : PR verte (Actions), PR rouge `test/failing-demo` (journal), page *Packages*,
`docs/devops/FICHE-PROJET.md`, `docs/devops/INCIDENT-v1.1.0.md`. Plan B hors ligne : captures de
`PREUVES.md`, et `SKIP_PULL=1` devant `deploy.sh`.

## Déroulé minuté

| Temps | Montrer | Dire (résumé) |
|---|---|---|
| 1 min | Schéma de `FICHE-PROJET.md` | Rôle de chaque brique : contrôle, image, Compose, CI, release, staging, rollback |
| 2 min | PR verte : jobs `test` → `docker-build`, artefact `rapport-tests` téléchargé | `needs`, service PostgreSQL, `if: always()`, test de fumée |
| 2 min | PR rouge : journal, première erreur utile (`AssertionError` dans `test_health.py`) | Pourquoi `docker-build` est « skipped » ; fusion bloquée si B1 |
| 2 min | `./scripts/deploy.sh v1.0.1` puis `ps` | Image publiée non reconstruite, `IMAGE_TAG`, `wait-healthy.sh` code 0 |
| 2 min | `./scripts/deploy.sh v1.1.0` → échec, logs, retour automatique à v1.0.1 ; lire `INCIDENT-v1.1.0.md` | Santé vue de l'extérieur, 39 s, correction en v1.1.1, contrat de port |
| 1 min | Bilan | À grande échelle : Kubernetes (rolling update, readiness, `rollout undo`), Ansible ; invariants : image immuable, santé, rollback |

## Commandes de secours

```bash
docker compose -p forma3d-staging -f compose.staging.yaml --env-file .env.deploy ps
docker compose -p forma3d-staging -f compose.staging.yaml --env-file .env.deploy logs --tail=30 api
echo "IMAGE_TAG=v1.0.1" > .env.deploy && docker compose -p forma3d-staging -f compose.staging.yaml --env-file .env.deploy up -d
./scripts/wait-healthy.sh; echo "code=$?"
```

## Questions de jury à préparer

Voir `QUIZ.md`. Les plus probables : 0.0.0.0 vs 127.0.0.1 ; `db` vs `localhost` ; `down` vs `down -v` ;
pourquoi ne pas reconstruire en staging ; pourquoi un tag ne bouge jamais (exemple vécu : `v1.0.0` posé trop tôt, remplacé par `v1.0.1`) ; d'où vient le `GITHUB_TOKEN`.

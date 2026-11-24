# Fiche projet DevOps — Forma3D Studio (API FastAPI + PostgreSQL)

**Dépôt :** https://github.com/Yas-sin-e/forma3d-kit · **Démarrage (développement) :** `docker compose up -d --build` → http://localhost:8080
· **Staging :** `./scripts/deploy.sh vX.Y.Z` → http://localhost:8080/health

## 1. Architecture

```
 Navigateur ──► api (FastAPI/Uvicorn :8080, seul port publié, 127.0.0.1)
                 ├─ /, /static/*                Studio, viewer et widget (HTML statique servi par FastAPI)
                 ├─ /models, /categories, ...   API interne du Studio
                 ├─ /api/v1/*                   API externe protégée par clé API
                 └─ /health                     contrôle de santé (Docker, CI, deploy.sh)
                        │ DATABASE_URL (hôte « db »)
                        ▼
 db : PostgreSQL 17 (postgres:17-alpine), port 5432 non publié, volume persistant pgdata
 volume storage : GLB et photos générés (conservés quand le conteneur api est recréé)
```
- Connexion par **nom de service** (`postgresql://…@db:5432/…`), démarrage conditionné à la santé (`depends_on: condition: service_healthy`, `pg_isready`).
- Image non root (`USER appuser`), `HEALTHCHECK` sur `/health`, tag explicite `ghcr.io/yas-sin-e/forma3d:vX.Y.Z` (aucun tag `latest`).
- Secrets dans `.env.compose` / `.env.staging` (ignorés par Git) ; en CI, copie du modèle `.env.staging.example` (valeurs fictives) ; GHCR uniquement via `secrets.GITHUB_TOKEN`.
- Debug local volontaire : `compose.debug.yaml` (PostgreSQL sur 127.0.0.1:5433 pour DBeaver) ou `--profile debug` (Adminer sur 127.0.0.1:8081).

## 2. Chaîne CI/CD

| Étape | Déclencheur | Résultat |
|---|---|---|
| CI (`ci.yml`) | pull request / push `main` | `check-project.sh` + tests pytest sur PostgreSQL (matrice Python 3.12 et 3.13, workflow réutilisable `reusable-tests.yml`), rapports JUnit en artefacts → **puis** (needs) `docker-build` : image `forma3d:ci` + test de fumée `/health` |
| Release (`release.yml`) | tag `vX.Y.Z` | tests → image publiée `ghcr.io/yas-sin-e/forma3d:vX.Y.Z` → (needs) `deploy-staging` : mise en service de l'image publiée (sans reconstruction) + `wait-healthy.sh` |
| Deploy (`scripts/deploy.sh`) | manuel, sur le poste | `pull` de l'image du tag, `up -d`, contrôle de santé ; si non sain → retour automatique au dernier tag sain |
| Dependabot (`dependabot.yml`) | hebdomadaire | PR de mise à jour pip et GitHub Actions, chacune testée par la CI |

| Exécution | Lien |
|---|---|
| ✅ CI réussie (PR #14, `test` → `docker-build`) | https://github.com/Yas-sin-e/forma3d-kit/actions/runs/43965184922 |
| ✅ CI réussie avec matrice Python 3.12/3.13 (PR #33, 3 jobs) | https://github.com/Yas-sin-e/forma3d-kit/actions/runs/45149442887 |
| ❌ CI en échec (PR #15, régression volontaire) | https://github.com/Yas-sin-e/forma3d-kit/actions/runs/43965191693 — 1re erreur utile : `AssertionError: assert {'status': 'ok'} == {'status': 'broken'}` (`tests/test_health.py:27`) ; job `docker-build` *skipped* (needs) ; PR non fusionnée |
| ✅ Release v1.0.1 | https://github.com/Yas-sin-e/forma3d-kit/actions/runs/43960593859 |
| ✅ Release v1.1.0 (version volontairement défectueuse) | https://github.com/Yas-sin-e/forma3d-kit/actions/runs/43960593512 |
| ✅ Release v1.1.1 (correction) | https://github.com/Yas-sin-e/forma3d-kit/actions/runs/43960593801 |
| ✅ Release v1.1.2 (publication + `deploy-staging` automatique) | https://github.com/Yas-sin-e/forma3d-kit/actions/runs/45010763481 |

## 3. Version mise en service

| Environnement | Version | Contrôle |
|---|---|---|
| Staging (PC local, images GHCR publiées, 16/11/2026) | **v1.1.1** | `./scripts/deploy.sh v1.1.1` → `tentative 2/12 : {"status":"ok"}`, `staging sain`, code 0 ; `.last-good-tag` = `v1.1.1` |
| Staging (GitHub, environnement `staging`, 22/11/2026) | v1.1.2 | job `deploy-staging` vert : image `v1.1.2` tirée de GHCR, `wait-healthy.sh` code 0 |

Image jamais reconstruite au déploiement : `compose.staging.yaml` n'a pas de `build:`, seulement `image: ghcr.io/yas-sin-e/forma3d:${IMAGE_TAG}`. Changer de version = changer `IMAGE_TAG`.
Le tag `v1.0.0` a été posé par erreur avant la fusion de `release.yml` : aucune image, tag jamais déplacé (tracé dans `phase-05.md`).

## 4. Déroulé du retour arrière

Cas réel provoqué : en **v1.1.0**, l'API écoutait sur le port 8000 alors que le staging publie 8080 → `/health` sans réponse.

1. Constat : `./scripts/deploy.sh v1.1.0` → `staging non sain après 6 tentatives (http://localhost:8080/health)`.
2. Journaux (affichés par le script) : `Uvicorn running on http://0.0.0.0:8000` → première erreur utile.
3. Le script remet automatiquement le dernier tag sain lu dans `.last-good-tag` : `RETOUR ARRIÈRE vers v1.0.1`, `pull` de l'image **déjà publiée**, `up -d`, aucune reconstruction.
4. Contrôle automatique : `wait-healthy.sh` → `{"status":"ok"}`, `Retour arrière réussi : v1.0.1 en service ; v1.1.0 refusé.` (code de sortie 1 pour signaler la version refusée).
5. Durée : 95 s au plus entre le lancement de `v1.1.0` (22:43:11) et le retour sain de `v1.0.1` (22:44:46), téléchargement de l'image compris.
6. Les données PostgreSQL et les GLB sont conservés (volumes `pgdata` et `storage` non touchés).
7. Correction livrée par le tag **`v1.1.1`** (port 8080 rétabli), mise en service avec `./scripts/deploy.sh v1.1.1` (code 0) ; prévention : contrôle « contrat de port » ajouté à `scripts/check-project.sh`.

Retour arrière manuel : `echo IMAGE_TAG=v1.0.1 > .env.deploy && docker compose -p forma3d-staging -f compose.staging.yaml --env-file .env.deploy up -d && ./scripts/wait-healthy.sh`

Historique : v1.0.1 → v1.1.0 (refusée) → **retour arrière v1.0.1** → v1.1.1 → v1.1.2 (GitHub). Détails : [INCIDENT-v1.1.0.md](INCIDENT-v1.1.0.md), [phase-07.md](phase-07.md) §4b.

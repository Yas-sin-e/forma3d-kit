# Fiche projet DevOps — Forma3D Studio (une page)

**Étudiante :** projet individuel, Licence 3 DSI, ISET · **Application :** API FastAPI + Studio HTML + widget
· **Dépôt :** `Yas-sin-e/forma3d-kit-codex` (privé) · **Image :** `ghcr.io/yas-sin-e/forma3d:<tag>`

## Architecture

```
 poste (Windows + WSL2)  --git push branche + PR-->  GitHub
                                                       |
            CI (ci.yml, sur chaque PR)                 |
   +-------------------------------+   needs   +----------------------+
   | test : check-project.sh       | --------> | docker-build         |
   |        pytest SQLite + PG     |           | image forma3d:ci     |
   |        artefact rapport-tests |           | test de fumée /health|
   +-------------------------------+           +----------------------+
                     | vert -> fusion dans main
                     | git tag -a vX.Y.Z  ->  release.yml (GITHUB_TOKEN)
                     v
          ghcr.io/yas-sin-e/forma3d:vX.Y.Z   (image immuable)
                     |
                     v   ./scripts/deploy.sh vX.Y.Z
   +--------------------------------------------------+
   | STAGING (compose.staging.yaml, -p forma3d-staging)|
   |  api  image:${IMAGE_TAG}  127.0.0.1:8080          |
   |   | DATABASE_URL -> hôte « db »                   |
   |  db   postgres:17-alpine  (5432 non publié)       |
   |  volumes : pgdata (base)  storage (GLB, photos)   |
   +--------------------------------------------------+
                     |
          wait-healthy.sh -> GET /health
          sain : .last-good-tag = tag      non sain : retour au dernier tag sain
```

## Briques et rôle

| Brique | Fichier | Point du barème |
|---|---|---|
| Contrôle du dépôt (0/1) | `scripts/check-project.sh` | 2 |
| Image non root + HEALTHCHECK | `Dockerfile`, `.dockerignore` | 3 |
| Pile api + PostgreSQL | `compose.yaml` (+ `compose.debug.yaml` pour DBeaver) | 4 |
| Persistance PostgreSQL (seule base, SQLite retiré) | `backend/app/repositories/postgres_repository.py`, `factory.py` | 4 |
| CI `test` → `docker-build` | `.github/workflows/ci.yml` | 5 |
| Version immuable GHCR | `.github/workflows/release.yml` | 6 |
| Staging + santé | `compose.staging.yaml`, `scripts/wait-healthy.sh`, `scripts/deploy.sh` | 6 |
| Retour arrière | `scripts/deploy.sh`, `INCIDENT-v1.1.0.md` | 7 |

## Versions publiées

| Tag | Commit | Contenu | Rôle |
|---|---|---|---|
| `v1.0.0` | `c447aca` (ancien `main`) | aucun `release.yml` | **posé par erreur avant la fusion : aucune image, jamais déplacé** |
| `v1.0.1` | `4b2d063` (fin de P6) | image port 8080, staging | version saine de référence |
| `v1.1.0` | `3552bb5` (port 8000) | version volontairement défectueuse | incident P7 |
| `v1.1.1` | `a17c181` (`main` après la PR n°13) | correction du port, contrôle du contrat de port, PostgreSQL seule base | correction de l'incident |

## Version en service

| Environnement | Version | État |
|---|---|---|
| Staging (répétition locale du 16/11/2026) | `v1.1.1` (image construite localement) | sain — `wait-healthy.sh` code 0 |
| Staging avec images GHCR publiées | — | à faire après fusion et push des tags |

## Déroulé du retour arrière

1. `./scripts/deploy.sh v1.1.0` → `wait-healthy.sh` échoue (code 1) : API sur 8000, staging publie 8080.
2. `docker compose … logs --tail=30 api` → `Uvicorn running on http://0.0.0.0:8000`.
3. `deploy.sh` remet automatiquement le dernier tag sain (`v1.0.1` en version publiée), `up -d`, santé OK — **39 s** d'indisponibilité, aucune reconstruction.
4. Correction livrée en `v1.1.1` ; prévention : contrôle « contrat de port » dans `check-project.sh`.

Manuel : `echo IMAGE_TAG=v1.0.1 > .env.deploy && docker compose -p forma3d-staging -f compose.staging.yaml --env-file .env.deploy up -d && ./scripts/wait-healthy.sh`

## Ce qui changerait à grande échelle

Kubernetes remplacerait Compose (déploiement progressif *rolling update*, `readinessProbe` au lieu de
`wait-healthy.sh`, `kubectl rollout undo` au lieu de `deploy.sh`), Ansible ou Terraform prépareraient les
serveurs, et les secrets iraient dans un coffre (Vault, secrets Kubernetes). **Ce qui ne change pas :**
image immuable versionnée, configuration par l'environnement, contrôle de santé, retour arrière sans reconstruction.

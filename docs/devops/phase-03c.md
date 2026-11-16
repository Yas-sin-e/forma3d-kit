# Phase P3c — Suppression de SQLite : PostgreSQL seule base

- **Branche :** `feature/postgres-only`
- **Date :** 16 novembre 2026
- **Décision D5 (étudiante) :** « enlever définitivement le code SQLite, laisser seulement PostgreSQL ».
  Elle remplace la décision D3 (SQLite par défaut).
- **Barème :** consolide le point 4 (une vraie base de données serveur, partout).

## 1. Objectif

Une seule base de données dans tous les environnements : poste de développement, tests, CI, Compose et
staging. On supprime l'écart « SQLite en local, PostgreSQL en production », source classique de bugs qui
n'apparaissent qu'en production (principe 12-factor n° 10 : *dev/prod parity*).

## 2. Fichiers

| Fichier | Action | Rôle |
|---|---|---|
| `backend/app/repositories/sqlite_repository.py` | **supprimé** | Ancien dépôt SQLite |
| `backend/app/repositories/factory.py` | réécrit | `DATABASE_URL` obligatoire, `postgresql://` seulement, message clair sinon |
| `backend/app/main.py` | modifié | `create_repository()` sans chemin de fichier ; journal de l'URL **masquée** |
| `backend/tests/pg_support.py` | créé | URL de test sécurisée, remise à zéro, requêtes d'inspection |
| `backend/tests/conftest.py` | modifié | Fixe `DATABASE_URL` sur la base de test avant d'importer l'application ; base remise à zéro avant **chaque** test |
| 13 fichiers `backend/tests/test_*.py` | modifiés | `SQLiteGenerationRepository(fichier)` → `make_repository()` ; inspections `sqlite3`/`PRAGMA` → requêtes PostgreSQL et `information_schema` |
| `backend/tests/test_repository_factory.py` | réécrit | URL absente, autre moteur (dont `sqlite://`) refusés |
| `scripts/dev.ps1` | modifié | Démarre PostgreSQL par Compose (127.0.0.1:5433), crée `forma3d_test`, fixe `DATABASE_URL` et `TEST_DATABASE_URL` |
| `.github/workflows/ci.yml` | modifié | Le test de fumée de `docker-build` reçoit lui aussi un service PostgreSQL |
| `.github/workflows/release.yml` | modifié | Le job `test` reçoit un service PostgreSQL |
| `Dockerfile` | modifié | Plus de dossier `backend/data` (servait à SQLite) ; en-tête : `DATABASE_URL` requise |
| `.env.example`, `AGENTS.md`, `README.md`, `scripts/check-project.sh`, `docs/STRUCTURE.md`, `docs/STOCKAGE.md`, `docs/COMPRENDRE-FORMA3D.md` | modifiés | Documentation alignée ; notes historiques en tête des anciens documents |

## 3. Logique expliquée

| Choix | Pourquoi | Sans lui |
|---|---|---|
| `DATABASE_URL` obligatoire, erreur au démarrage | *Fail fast* : une configuration absente est signalée immédiatement, avec l'exemple à suivre | L'API démarrerait sur une base imprévue ou planterait plus tard avec une erreur obscure |
| `conftest.py` fixe `DATABASE_URL` **avant** `import app.main` | `main.py` crée le dépôt dès son import | Les tests se connecteraient à la base de travail, ou échoueraient |
| Base de test séparée `forma3d_test` + refus si le nom ne contient pas « test » | Les tests vident les tables : ils ne doivent jamais toucher la base de travail | Un `TRUNCATE` sur la vraie base effacerait les modèles de la propriétaire |
| `TRUNCATE … RESTART IDENTITY CASCADE` avant chaque test | Chaque test part de trois catégories et d'identifiants à 1, comme un fichier SQLite neuf autrefois | Les tests dépendraient de l'ordre d'exécution |
| `information_schema.columns` | Catalogue standard SQL pour vérifier les migrations | `PRAGMA table_info` n'existe qu'en SQLite |
| Test « une connexion par opération » via un espion sur `psycopg.connect` | Prouve qu'aucune connexion n'est partagée entre requêtes et tâche de fond, et qu'elles sont fermées | — |
| `dev.ps1` réutilise le service `db` de `compose.yaml` | Une seule définition de la base pour Compose, `dev.ps1` et DBeaver | Deux bases à maintenir |
| Test de fumée CI avec `--network host` | Le conteneur joint la base du service sur `localhost:5432` du runner | L'image refuserait de démarrer (pas de `DATABASE_URL`) et la CI serait rouge |

**Données existantes :** l'ancien fichier `backend/data/forma3d.sqlite3` du poste n'est **ni supprimé ni
migré** ; il n'est simplement plus lu (il reste ignoré par Git). Une migration de ses lignes vers
PostgreSQL demanderait un script dédié et l'accord explicite de l'étudiante.

## 4. Vérifications observées (16/11/2026)

| Contrôle | Résultat |
|---|---|
| `grep -ri sqlite backend/app` | aucune occurrence |
| Suite complète sur PostgreSQL (base de test sur 55432) | `177 passed` |
| Bloc PostgreSQL de `dev.ps1` exécuté seul | `db` healthy sur 127.0.0.1:5433, bases `forma3d` et `forma3d_test` présentes |
| Suite complète sur la base de `dev.ps1` (5433) | `177 passed in 39.26s` |
| Application avec `DATABASE_URL` → `/health` | `{"status":"ok"}` |
| Application **sans** `DATABASE_URL` | `DatabaseUrlError: DATABASE_URL est vide : PostgreSQL est obligatoire…` |
| `docker compose up -d --build --wait` | `api` et `db` healthy, `/health` OK, catégorie `bench` de P3b toujours présente |
| `check-project.sh` | `[SUCCES]` |

Durée des tests : environ 40 s sous Windows (une connexion TCP vers Docker Desktop par opération).
Sur le runner Linux de GitHub, la latence est plus faible. **La CI GitHub de cette branche n'a pas
encore été observée.**

## 5. Lancer

```bash
docker compose -f compose.yaml -f compose.debug.yaml up -d --wait db
docker compose exec db psql -U forma3d -d forma3d -c "CREATE DATABASE forma3d_test"   # une seule fois
cd backend
PYTHON_DOTENV_DISABLED=true HF_SPACE_ID= \
  TEST_DATABASE_URL=postgresql://forma3d:dev-password@127.0.0.1:5433/forma3d_test python -m pytest -q
```
Sous Windows, `./scripts/dev.ps1` fait tout cela automatiquement.

## 6. À dire en soutenance

> J'ai retiré SQLite pour avoir la même base PostgreSQL partout : en développement, dans les tests, en CI
> et en staging, ce qui évite les bugs qui n'apparaissent qu'en production. L'application refuse de
> démarrer sans `DATABASE_URL`, avec un message qui explique quoi faire. Les tests utilisent une base
> séparée dont le nom doit contenir « test », remise à zéro avant chaque test par `TRUNCATE`. Mon script
> `dev.ps1` démarre lui-même la base grâce au service `db` de Compose, la même que je visualise dans DBeaver.

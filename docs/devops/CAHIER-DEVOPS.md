# Cahier des charges DevOps — Forma3D Studio

**Module :** DevOps · Licence 3 DSI · ISET — Projet de fin de module (individuel)
**Application support :** Forma3D Studio (API FastAPI + Studio HTML + widget intégrable)
**Rédigé le :** 16 novembre 2026
**Destinataire :** l'assistant IA (Claude) qui réalise le travail avec l'étudiante, phase par phase.

> **Principe du module.** Le code de l'application n'est pas noté : seule la **chaîne DevOps** l'est.
> Ce document transforme les exigences des ateliers 1 à 5 et du guide de projet en un plan de travail
> concret, adapté au dépôt Forma3D tel qu'il existe aujourd'hui. Les bonus ne comptent que si les
> 7 points essentiels sont présents.

---

## 0. Comment utiliser ce document

1. Le travail se fait **une phase à la fois**, dans l'ordre (P0 → P9, puis bonus B1 → B3).
2. Au début de chaque phase, l'assistant rappelle : **objectif, fichiers concernés, critère de réussite, points du barème visés**.
3. À la fin de chaque phase, l'assistant fournit : liste des fichiers créés/modifiés, commandes de vérification, **preuves à conserver**, et une section **« À dire en soutenance »** (3 à 5 phrases).
4. Chaque phase se termine par une **merge request (pull request GitHub)** relue, puis fusionnée dans `main`. Personne ne pousse directement sur `main`.
5. L'assistant ne déclare jamais un résultat qu'il n'a pas observé (pipeline vert, image publiée, santé OK). Ce qui n'a pas pu être vérifié est écrit comme tel.

---

## 1. Point de départ : ce qui existe et ce qui manque

Inventaire réalisé sur la branche `main` (commit `4fa727a`).

| Exigence du barème | Déjà présent dans Forma3D | Manquant |
|---|---|---|
| 1. Git propre (2 pts) | Dépôt GitHub `forma3d-kit`, branches `claude/*`, PR fusionnées, `.gitignore` complet (`.env`, `backend/data/`, `backend/storage/`), `.env.example` à jour | Convention de nommage DevOps (`feature/`, `ci/`, `docs/`), messages *Conventional Commits* systématiques, `.dockerignore`, vérification « aucun secret dans l'historique » |
| 2. Script Bash de contrôle (2 pts) | `scripts/dev.ps1` (PowerShell, lancement local) | **`scripts/check-project.sh`** : contrôles, codes de sortie 0/1, garde-fou `git status --porcelain` |
| 3. Conteneuriser (3 pts) | Route `GET /health` → `{"status":"ok"}` | **`Dockerfile`**, **`.dockerignore`**, tag explicite, utilisateur non root, `HEALTHCHECK` |
| 4. Compose (3 pts) | Persistance via **SQLite** (`backend/data/forma3d.sqlite3`) derrière l'interface `GenerationRepository` | **Une vraie base dans un service séparé** (PostgreSQL), `compose.yaml`, réseau privé, volume nommé, `depends_on: condition: service_healthy` |
| 5. Pipeline CI (3 pts) | `.github/workflows/ci.yml` : un job `project-checks` (pytest + présence de fichiers) | Job **`test`** → job **`docker-build`** avec `needs`, **rapport JUnit en artefact** (`if: always()`), déclenchement explicite `pull_request` |
| 6. Livrer et mettre en service (2 pts) | Aucun tag, aucune image | Tag annoté **`v1.0.0`**, image **`ghcr.io/yas-sin-e/forma3d:v1.0.0`**, `compose.staging.yaml`, `scripts/wait-healthy.sh` |
| 7. Retour arrière (1 pt) | — | Version défectueuse publiée, échec du contrôle de santé, **rollback** vers `v1.0.0`, compte rendu d'incident |
| Soutenance (4 pts) | — | Scénario de 10 minutes répété, PR verte + PR rouge prêtes |
| Bonus (+4) | — | Protection de `main`, déploiement auto sur tag, matrice Python |

**Constat central :** Forma3D a déjà une bonne hygiène Git, des tests (≈ 159 tests pytest) et une CI minimale.
Le gros du travail porte sur **Docker, Compose avec PostgreSQL, la chaîne CI/CD complète, la livraison versionnée et le rollback**.

---

## 2. Règles non négociables

### 2.1 Projet individuel
- Toutes les PR sont ouvertes **et** fusionnées par l'étudiante. La « revue » se fait sous forme d'auto-relecture documentée : chaque PR contient la description type (Objectif / Changements / Vérification) et au moins un commentaire de relecture suivi d'un commit de correction quand c'est pertinent.
- Les explications doivent permettre à l'étudiante de **tout justifier seule** devant le jury.

### 2.2 Sécurité
- Aucun mot de passe, jeton, clé ni fichier `.env` dans Git, dans une image Docker ou dans un journal de pipeline.
- Le fichier `backend/.env` n'est **jamais lu ni modifié** par l'assistant (règle d'`AGENTS.md`).
- Valeurs de démonstration fictives uniquement (`dev-password`…), placées dans des fichiers `.env.*` ignorés par Git, avec un `*.example` versionné.
- Secrets de la plateforme : seul `GITHUB_TOKEN` (fourni automatiquement) est utilisé pour publier sur GHCR. Aucun `echo` d'une variable secrète.
- Le Studio n'a qu'une authentification mono-propriétaire : l'environnement « staging » reste **local** (poste ou runner GitHub), jamais exposé sur Internet.

### 2.3 Cohérence avec le projet existant
- Langue : explications en **français** ; code, noms de fichiers et commandes en **anglais**.
- Chaque nouveau fichier : en-tête de commentaire en français (rôle + exécution) **et** une ligne dans `docs/STRUCTURE.md`.
- Chaque phase : un fichier `docs/devops/phase-XX.md` (rôle des fichiers, logique, lancement, test, justification soutenance) et une mise à jour de `docs/ETAT.md`.
- Toute nouvelle fonction Python est couverte par un test pytest.
- Aucun service payant. GitHub Actions et GHCR sont gratuits pour cet usage.
- **Exception explicite au périmètre d'`AGENTS.md` :** le module DevOps exige Docker et une base PostgreSQL. L'étudiante autorise ces ajouts **pour le projet DevOps uniquement**. L'assistant met à jour la ligne correspondante d'`AGENTS.md` dans la phase P0 pour tracer cette décision. Le fournisseur 3D (TripoSR/TRELLIS) ne change pas ; le lancement local par `scripts/dev.ps1` et SQLite restent fonctionnels.

### 2.4 Méthode de diagnostic (à appliquer et à citer en soutenance)
Observer l'état sans rien modifier → lire les journaux et retenir la **première** erreur utile → comparer configuration attendue et effective → formuler une hypothèse vérifiable → appliquer **une seule** correction → revalider.

---

## 3. Architecture cible

```
  développeur (poste Windows + WSL2)
        |  git push  feature/xxx  +  pull request
        v
  +-----------------+   needs   +-------------------+
  | job  test       | --------> | job  docker-build |
  | pytest (SQLite  |           | build image       |
  |  + PostgreSQL)  |           | tag : forma3d:ci  |
  | report.xml  ->  |           +-------------------+
  |  artefact       |
  +-----------------+
        | vert -> fusion dans main (protégée)
        |
        |  git tag -a v1.0.0  ->  workflow release
        v
  ghcr.io/yas-sin-e/forma3d:v1.0.0   (image immuable)
        |
        v
  +---------------------------------------------+
  | STAGING  (docker compose, poste ou runner)  |
  |                                             |
  |  api  (forma3d:${IMAGE_TAG})  :8080 publié  |
  |    |  DATABASE_URL -> host "db"             |
  |    v                                        |
  |  db  postgres:17-alpine   (5432 NON publié) |
  |    volume pgdata    +  volume storage (GLB) |
  +---------------------------------------------+
        |
        v
  scripts/wait-healthy.sh  ->  GET /health
        |  sain -> on garde      | non sain -> ROLLBACK (IMAGE_TAG précédent)
```

**Livraison continue, pas déploiement continu** : le pipeline produit automatiquement une image prête ; la mise en service est déclenchée volontairement (sauf bonus B2, où un tag déclenche la mise en service sur un environnement de test jetable).

---

## 4. Phases de réalisation

Chaque phase = une branche + une PR. Noms de branches proposés entre parenthèses.

### P0 — Diagnostic d'entrée et cadrage (`docs/devops-kickoff`)
**Objectif :** partir d'un état connu et tracer les décisions.
- Exécuter et consigner : `git status`, `git log --oneline --graph -n 15`, `git remote -v`, `docker version`, `docker compose version`, ports 8080/5432 libres.
- Vérifier qu'aucun secret n'a jamais été commité : `git log --all --full-history -- "*.env" ".env"` et une recherche de motifs (`hf_`, `ghp_`, `PASSWORD=` non vide). Si un secret réel apparaît : le signaler, le **révoquer**, ne pas réécrire l'historique sans accord.
- Créer `docs/devops/README.md` (sommaire des phases + lien vers ce cahier).
- Mettre à jour `AGENTS.md` (exception DevOps, §2.3).
- **Critère :** environnement vérifié, décisions écrites, PR fusionnée.

### P1 — Script Bash de contrôle (`chore/check-project`) — *point 2, 2 pts*
**Fichier :** `scripts/check-project.sh` (fins de ligne **LF**, bit exécutable via `git update-index --chmod=+x`).
**Contrôles :**
1. Fichiers requis présents : `README.md`, `.gitignore`, `.env.example`, `backend/requirements.txt`, `backend/app/main.py`, `Dockerfile`, `.dockerignore`, `compose.yaml` (les trois derniers ajoutés à la liste quand ils existent, en P2/P3).
2. Aucun fichier `.env` suivi par Git (`git ls-files | grep -Eq '(^|/)\.env$'`), aucun `*.sqlite3` ni GLB de `backend/storage/` suivi.
3. Aucun marqueur de conflit (`<<<<<<<`) dans les fichiers suivis.
4. **Garde-fou (défi atelier 2)** : option `--strict` qui échoue si `git status --porcelain` n'est pas vide.
5. Message final `[SUCCES]` → `exit 0` ; sinon `[ECHEC] N erreur(s)` sur stderr → `exit 1`.
- Ajouter `.gitattributes` avec `*.sh text eol=lf` pour éviter le piège CRLF sous Windows.
- **Preuves :** sortie en succès (`echo $?` → 0) et en échec provoqué (fichier renommé → 1).
- Le pipeline (P4) exécutera ce script : c'est le lien atelier 2 → atelier 5.

### P2 — Conteneuriser l'application (`feature/dockerfile`) — *point 3, 3 pts*
**Fichiers :** `Dockerfile`, `.dockerignore`.
- Base `python:3.12-slim` (version fixée, jamais `latest`).
- Ordre des couches justifié : `COPY backend/requirements.txt` → `pip install --no-cache-dir` → `COPY backend/app` → `COPY frontend` (le backend sert `frontend/` sous `/static` via `_PROJECT_ROOT`, donc l'arborescence `/app/backend` + `/app/frontend` doit être respectée).
- Utilisateur non root : `useradd --create-home appuser`, `chown` des dossiers `backend/data` et `backend/storage`, puis `USER appuser`.
- `EXPOSE 8080` ; `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]` exécuté depuis `/app/backend`. Expliquer pourquoi **0.0.0.0** et non 127.0.0.1.
- `HEALTHCHECK` en Python (curl absent de l'image slim) : `urllib.request.urlopen('http://127.0.0.1:8080/health')`.
- `.dockerignore` : `.git/`, `.env`, `.env.*`, `!.env.example`, `**/__pycache__/`, `.venv/`, `backend/data/`, `backend/storage/`, `tools/`, `docs/`, `*.log`, `.claude/`.
- L'image démarre **sans** configuration fournisseur : `/health/provider` renvoie `UNCONFIGURED`, ce qui est normal.
- **Vérifications :** `docker build -t forma3d:1.0 .`, `docker run -d -p 8080:8080 --name forma3d-api forma3d:1.0`, `curl -fsS localhost:8080/health`, `docker exec forma3d-api whoami` → `appuser`, `docker inspect --format '{{.State.Health.Status}}' forma3d-api` → `healthy`, `docker image ls forma3d` (taille), `docker history forma3d:1.0`.
- **Incident pédagogique à documenter** : conteneur lancé avec une commande erronée → `docker ps -a` (Exited) → `docker logs` → première erreur utile.

### P3 — PostgreSQL et Docker Compose (`feature/compose-postgres`) — *point 4, 3 pts*
Le barème exige « application + base de données » dans Compose. SQLite étant un fichier, il faut une **vraie base dans un service séparé**.

**3a. Dépôt PostgreSQL derrière l'interface existante**
- Ajouter `backend/app/repositories/postgres_repository.py` implémentant **toutes** les méthodes du protocole `GenerationRepository` (`repositories/base.py`) avec le même comportement que `sqlite_repository.py` (catégories initiales, migrations idempotentes, compteurs de quota atomiques, transactions).
- Sélection par variable d'environnement : `DATABASE_URL` vide → SQLite (comportement actuel inchangé, `dev.ps1` et tests intacts) ; `DATABASE_URL=postgresql://...` → PostgreSQL. Documenter la variable dans `.env.example`.
- Dépendance : `psycopg[binary]` (légère, sans compilation). **Demander l'accord de l'étudiante avant l'ajout**, comme l'exige `AGENTS.md`.
- Tests : rendre les tests de dépôt paramétrables pour s'exécuter aussi sur PostgreSQL quand `TEST_DATABASE_URL` est défini (sinon ignorés proprement avec `pytest.skip`). En CI, un *service container* PostgreSQL les exécutera.

**3b. `compose.yaml`**
- Service `api` : `build: .`, image `forma3d:dev`, port `8080:8080`, `DATABASE_URL` construit avec l'hôte **`db`** (nom de service, pas `localhost`), `env_file: .env.compose` (ignoré par Git, modèle `.env.compose.example` versionné), `depends_on: db: condition: service_healthy`, volume nommé `storage` monté sur `/app/backend/storage`.
- Service `db` : `postgres:17-alpine`, **aucun port publié**, volume nommé `pgdata:/var/lib/postgresql/data`, `healthcheck` `pg_isready -U forma3d -d forma3d` (interval 5s, timeout 3s, retries 10).
- Défi atelier 4 : service `adminer` (port 8081) dans le **profil `debug`**, absent d'un `up` normal.
- **Vérifications et preuves :** `docker compose config` ; `docker compose up -d --build` ; `docker compose ps` (db *healthy*) ; `docker compose exec api getent hosts db` ; `psql -h localhost -p 5432` échoue (port non publié — expliquer pourquoi c'est voulu) ; **persistance** : créer une catégorie via l'API ou `psql`, `docker compose down` puis `up -d`, la donnée est toujours là ; `docker volume ls`.
- **Incident à documenter** : `DB_HOST`/`DATABASE_URL` pointant sur `localhost` → logs `connection refused` → `exec api env` → correction → revalidation.
- Tableau à savoir réciter : `stop` / `down` / `down -v` (seule commande destructive).

### P4 — Pipeline CI (`ci/pipeline`) — *point 5, 3 pts*
Remplacer `.github/workflows/ci.yml` par un workflow structuré (conserver les contrôles de documents existants dans le job `test` ou via `check-project.sh`).
```yaml
on:
  pull_request:
  push:
    branches: [main]
```
- **Job `test`** (`ubuntu-latest`) : checkout, `setup-python` (3.12, `cache: pip`, `cache-dependency-path: backend/requirements.txt`), installation, `./scripts/check-project.sh`, `pytest -q --junitxml=report.xml` (avec `PYTHON_DOTENV_DISABLED=true` et `HF_SPACE_ID` vide, comme `dev.ps1`), service `postgres:17-alpine` pour les tests PostgreSQL, puis `actions/upload-artifact@v4` **`if: always()`** nommé `rapport-tests`.
- **Job `docker-build`** : `needs: test`, `docker/setup-buildx-action@v3`, `docker/build-push-action@v6` avec `push: false`, `tags: forma3d:ci`. Optionnel : démarrer l'image et appeler `/health` (test de fumée).
- `permissions: contents: read` au niveau du workflow.
- Vérifier les versions d'actions réellement disponibles (le fichier actuel cite `checkout@v7` et Python 3.14 : à confirmer ou aligner).
- **Preuves exigées pour la soutenance :**
  - URL d'une exécution **verte** sur une PR.
  - URL d'une exécution **rouge** : PR volontaire `test/failing-demo` qui casse un test (ex. assertion sur `/health`), avec la **première erreur utile** repérée dans le journal (capture surlignée). Ne pas fusionner cette PR.
  - Démonstration que `docker-build` ne démarre pas quand `test` est rouge.

### P5 — Version immuable et publication (`ci/release`) — *point 6, partie 1*
- Workflow `.github/workflows/release.yml` déclenché par `push: tags: ['v*']` : rejoue les tests, puis construit et **publie** `ghcr.io/yas-sin-e/forma3d:${{ github.ref_name }}` (nom en minuscules obligatoire pour GHCR).
- `permissions: contents: read, packages: write` ; connexion par `docker/login-action@v3` avec `${{ secrets.GITHUB_TOKEN }}`. Aucun identifiant en clair.
- Labels OCI (`org.opencontainers.image.source`, `.revision`, `.version`) via `docker/metadata-action@v5`.
- Procédure : `git switch main && git pull --ff-only` → `./scripts/check-project.sh` → `git tag -a v1.0.0 -m "Release 1.0.0"` → `git show v1.0.0` → `git push origin v1.0.0`.
- Règle : **un tag publié ne bouge jamais**. Une erreur se corrige par `v1.0.1`.
- Le paquet GHCR d'un dépôt privé est privé : pour le `pull` local, `docker login ghcr.io` avec un jeton personnel *read:packages* saisi au terminal (jamais écrit dans un fichier). Alternative : rendre le paquet public après vérification qu'il ne contient aucun secret.
- **Preuves :** tag visible sur GitHub, image visible dans *Packages*, `docker pull ghcr.io/yas-sin-e/forma3d:v1.0.0`.

### P6 — Mise en service en staging (`feature/staging`) — *point 6, partie 2*
- `compose.staging.yaml` : `api` utilise `image: ghcr.io/yas-sin-e/forma3d:${IMAGE_TAG}` (**on ne reconstruit pas**), `restart: unless-stopped`, `env_file: .env.staging` (ignoré, modèle `.env.staging.example` versionné), même service `db` et volumes que P3.
- `.env.deploy` contient seulement `IMAGE_TAG=v1.0.0` (ignoré par Git ; expliquer pourquoi la version est une variable).
- `scripts/wait-healthy.sh` : 12 tentatives espacées de 5 s sur `curl -fsS http://localhost:8080/health`, « staging sain » → `exit 0`, sinon « staging non sain » sur stderr → `exit 1`. URL paramétrable (`HEALTH_URL`).
- Optionnel mais professionnel : `scripts/deploy.sh <tag>` qui écrit `.env.deploy`, fait `pull`, `up -d`, puis appelle `wait-healthy.sh` et **revient automatiquement au tag précédent** si la santé échoue (en conservant le tag sain dans `.last-good-tag`, ignoré par Git).
- Arrêter la pile de développement P3 avant (port 8080) ou utiliser un nom de projet distinct (`-p forma3d-staging`).
- **Preuves :** `docker compose -f compose.staging.yaml ps`, sortie de `wait-healthy.sh` (code 0), `git check-ignore -v .env.staging`.

### P7 — Incident et retour arrière (`docs/incident-rollback`) — *point 7, 1 pt*
Le projet étant individuel, l'étudiante fabrique elle-même la version défectueuse.
- Créer une version **`v1.1.0` volontairement défectueuse**, réaliste et explicable, par exemple l'application qui écoute sur `127.0.0.1` dans le conteneur (le conteneur tourne, mais `/health` est injoignable depuis l'hôte — panne vue à l'atelier 3), **ou** une variable d'environnement obligatoire manquante qui fait planter le démarrage. Faire passer cette version par une PR et un tag comme une vraie livraison.
- Déroulé à exécuter et à consigner avec horodatage :
  1. `IMAGE_TAG=v1.1.0` → `pull` → `up -d` → `wait-healthy.sh` **échoue** (code 1).
  2. `docker compose -f compose.staging.yaml logs --tail=50 api` → recopier la **première erreur utile**.
  3. Rollback : `IMAGE_TAG=v1.0.0` → `up -d` → `wait-healthy.sh` **réussit**. Aucune reconstruction pendant l'incident.
  4. Correction propre publiée en **`v1.1.1`** (on ne réécrit pas `v1.1.0`).
- `docs/devops/INCIDENT-v1.1.0.md` : compte rendu en **cinq lignes** — ce qui s'est passé, quand on l'a su, ce qui a été fait, durée d'indisponibilité mesurée, ce qui empêchera la récidive (ex. test de fumée `/health` sur l'image dans le job `docker-build`).
- **Preuves :** sorties de `wait-healthy.sh` avant/après, extrait de logs surligné.

### P8 — Documentation finale (`docs/devops-final`)
- **README** : section « Démarrer en une commande » (`docker compose up -d --build` puis `http://localhost:8080`), prérequis, lien vers `docs/devops/`.
- **`docs/devops/FICHE-PROJET.md`** (une page) : architecture (schéma §3), version en service, déroulé du rollback.
- **`docs/devops/PREUVES.md`** : URLs des PR et des exécutions (verte, rouge), sorties de commandes, captures référencées.
- **`docs/devops/QUIZ.md`** : réponses rédigées aux quiz de sortie des ateliers 1 à 5 (révision soutenance).
- Mettre à jour `docs/STRUCTURE.md` et `docs/ETAT.md`.

### P9 — Répétition de la soutenance
Scénario de **10 minutes** (4 pts) :
1. (1 min) Architecture : schéma, rôle de chaque brique.
2. (2 min) Une PR au pipeline **vert** : jobs `test` → `docker-build`, artefact `rapport-tests` téléchargé.
3. (2 min) Une PR au pipeline **rouge** : ouvrir le journal, montrer la première erreur utile, expliquer pourquoi `docker-build` n'a pas tourné (et pourquoi la fusion est bloquée si B1 est fait).
4. (2 min) Mise en service : `IMAGE_TAG=v1.0.0`, `up -d`, `wait-healthy.sh` → sain.
5. (2 min) Incident `v1.1.0` → échec santé → logs → rollback `v1.0.0` → sain. Lire le compte rendu.
6. (1 min) Bilan : ce qui changerait à l'échelle (Kubernetes rolling update, Ansible), et ce qui ne change pas (image immuable, santé, rollback).
- Préparer à l'avance : images déjà tirées en local (pas de dépendance réseau), onglets ouverts, commandes dans un mémo. Prévoir un plan B hors ligne (captures) si GitHub est lent.

---

## 5. Bonus (+4 max, uniquement si P1–P7 sont complets)

### B1 — Protection de `main` (+1)
- *Settings → Branches* (ou *Rulesets*) : PR obligatoire, check **`test`** requis (et `docker-build`), branche à jour avant fusion.
- Démonstration : la PR rouge de P4 affiche « Merging is blocked ». Capture à conserver.
- **Attention :** sur un compte GitHub gratuit, la protection de branche des **dépôts privés** n'est pas disponible. Options : rendre le dépôt public (après contrôle P0 : aucun secret dans l'historique), ou passer par l'offre GitHub Education. Décision à prendre par l'étudiante.

### B2 — Déploiement automatique sur tag (+2)
- Dans `release.yml`, job `deploy-staging` avec `needs: publish`, uniquement sur `refs/tags/v*` : sur le runner, `docker compose -f compose.staging.yaml up -d` avec `IMAGE_TAG=${{ github.ref_name }}`, puis `./scripts/wait-healthy.sh`. Le job échoue si la santé échoue ; `docker compose logs` affiché en cas d'échec (`if: failure()`).
- Utiliser un `environment: staging` GitHub pour tracer les déploiements.
- Expliquer honnêtement : le runner est un staging **jetable** (détruit à la fin du job), ce qui suffit à prouver la mise en service automatisée et contrôlée.

### B3 — Matrice de versions (+1)
- Job `test` avec `strategy: { fail-fast: false, matrix: { python-version: ['3.12', '3.13'] } }` et un artefact par version (`rapport-tests-${{ matrix.python-version }}`).
- Expliquer les deux résultats (et pourquoi `fail-fast: false` permet de voir les deux même si l'un échoue).

---

## 6. Fichiers attendus en fin de projet

| Chemin | Rôle |
|---|---|
| `scripts/check-project.sh` | Contrôle du dépôt, codes de sortie 0/1, option `--strict` |
| `scripts/wait-healthy.sh` | Contrôle de santé du staging (décide du rollback) |
| `scripts/deploy.sh` *(optionnel)* | Mise en service d'un tag avec rollback automatique |
| `.gitattributes` | Fins de ligne LF pour les scripts Bash |
| `Dockerfile`, `.dockerignore` | Image non root avec `HEALTHCHECK` |
| `compose.yaml` | Pile de développement api + PostgreSQL (+ adminer en profil `debug`) |
| `compose.staging.yaml` | Staging à partir de l'image publiée, version par `IMAGE_TAG` |
| `.env.compose.example`, `.env.staging.example` | Modèles de configuration sans secret |
| `backend/app/repositories/postgres_repository.py` | Persistance PostgreSQL derrière `GenerationRepository` |
| `.github/workflows/ci.yml` | `test` → `docker-build`, artefact JUnit |
| `.github/workflows/release.yml` | Publication GHCR sur tag (+ déploiement B2) |
| `docs/devops/*.md` | Phases, incident, fiche une page, preuves, quiz |

---

## 7. Pièges propres à ce dépôt

- **Chemins relatifs à la racine** : `main.py` calcule `_PROJECT_ROOT` à partir de son emplacement et sert `frontend/`. L'image doit reproduire `backend/` et `frontend/` côte à côte.
- **Données locales** : `backend/data/` (SQLite, GLB de faisabilité) et `backend/storage/` sont ignorés ; ils ne doivent entrer ni dans Git ni dans l'image. En Compose, `storage` est un volume.
- **`.env` chargé automatiquement** : `config.py` lit `backend/.env` puis `.env`. Dans le conteneur, ces fichiers sont absents (exclus par `.dockerignore`) : la configuration passe uniquement par l'environnement Compose.
- **Tests isolés** : lancer pytest avec `PYTHON_DOTENV_DISABLED=true` et `HF_SPACE_ID=` vide, comme `dev.ps1`, pour ne jamais contacter un fournisseur 3D.
- **Windows** : travailler sous WSL2 pour les scripts Bash ; vérifier LF ; Docker Desktop avec intégration WSL activée.
- **GHCR** : nom d'image en minuscules (`yas-sin-e`), paquet privé par défaut.
- **Port 8080** : arrêter la pile P3 avant le staging P6, ou changer le port hôte.
- **Fournisseur 3D** : la génération n'est pas nécessaire pour la démonstration DevOps ; `/health` suffit. Ne pas promettre une génération en direct (quotas gratuits instables).

---

## 8. Grille d'auto-évaluation finale

| # | Élément | Pts | Preuve |
|---|---|:-:|---|
| 1 | Git propre : commits clairs, branches, PR, `.gitignore`, aucun secret | 2 | `git log --graph`, liste des PR, contrôle P0 |
| 2 | Script de contrôle 0 / non nul | 2 | Sorties succès/échec de `check-project.sh` |
| 3 | Dockerfile, `.dockerignore`, tag explicite, non root, HEALTHCHECK | 3 | `whoami`, `healthy`, `docker image ls` |
| 4 | Compose : api + PostgreSQL, nom de service, 5432 non publié, volume, santé | 3 | `compose ps`, `getent hosts db`, preuve de persistance |
| 5 | CI sur PR, `test` → `docker-build` (`needs`), artefact | 3 | URL exécution verte + rouge, artefact |
| 6 | Tag `vX.Y.Z`, image publiée non reconstruite, staging + santé | 2 | Tag, paquet GHCR, sortie `wait-healthy.sh` |
| 7 | Retour arrière démontré | 1 | Sorties avant/après, `INCIDENT-v1.1.0.md` |
| — | Soutenance | 4 | Scénario P9 répété |
| B | Protection `main` / déploiement sur tag / matrice | +4 | Captures et URLs |

# Plan de lecture — comprendre tout le projet DevOps

Objectif : pouvoir tout expliquer seule devant le jury. Lire **dans cet ordre**, une étape par séance.
Pour chaque étape : lire le document, ouvrir les fichiers cités, **lancer** les commandes, puis répéter à
voix haute la section « À dire en soutenance » sans regarder.

Durée totale estimée : 8 à 10 heures, réparties sur 5 jours.

## Jour 1 — Vue d'ensemble et point de départ (1 h 30)

| # | Lire | Ouvrir à côté | Comprendre | Faire |
|---|---|---|---|---|
| 1 | `docs/devops/FICHE-PROJET.md` | — | Le schéma : qui appelle qui, dans quel ordre | Redessiner le schéma de mémoire sur une feuille |
| 2 | `docs/devops/CAHIER-DEVOPS.md` §1, §3, §8 | — | Ce que le barème exige (7 points + soutenance) | Cocher la grille §8 avec `PREUVES.md` |
| 3 | `docs/devops/phase-00.md` | `docs/devops/README.md` | Diagnostic avant action ; contrôle des secrets ; décisions D1 à D5 | Relancer les commandes du §5 |

## Jour 2 — Git, Bash, Docker (2 h)

| # | Lire | Ouvrir à côté | Comprendre | Faire |
|---|---|---|---|---|
| 4 | `phase-01.md` | `scripts/check-project.sh`, `.gitattributes` | Codes de sortie 0/1, stderr, `set -uo pipefail`, piège CRLF | Provoquer un échec (renommer `README.md`), lire `echo $?` |
| 5 | `phase-02.md` | `Dockerfile`, `.dockerignore` | Couches et cache, non root, `HEALTHCHECK`, 0.0.0.0 | `docker build`, `docker history`, rejouer l'incident `Exited (3)` |

## Jour 3 — La base de données PostgreSQL (2 h 30) — le cœur de ta demande

| # | Lire | Ouvrir à côté | Comprendre | Faire |
|---|---|---|---|---|
| 6 | `phase-03a.md` | `backend/app/repositories/base.py` puis `postgres_repository.py` | Patron Repository ; `%s` contre l'injection SQL ; `TIMESTAMPTZ` ; `FOR UPDATE` ; transactions | Lire les 19 méthodes, une par une, avec le tableau §3.3 |
| 7 | `phase-03c.md` | `factory.py`, `backend/tests/conftest.py`, `pg_support.py` | Pourquoi SQLite a été retiré ; `DATABASE_URL` obligatoire ; base de test séparée | `./scripts/dev.ps1` puis ouvrir DBeaver sur `127.0.0.1:5433` |
| 7b | `phase-03d.md` | `tools/migrate_sqlite_to_postgres.py` | Migration de données en une transaction, chemins relatifs, rejouabilité | Ouvrir DBeaver (§6) et retrouver tes 17 générations |
| 8 | `phase-03b.md` | `compose.yaml`, `compose.debug.yaml`, `.env.compose.example` | Nom de service `db`, port non publié, volumes, `service_healthy`, `down` / `down -v` | Rejouer la preuve de persistance et l'incident `localhost` |

**Exercice DBeaver :** ouvrir la table `categories`, créer une catégorie dans le Studio, rafraîchir
DBeaver et la voir apparaître ; puis `docker compose down` / `up -d` et vérifier qu'elle est toujours là.

## Jour 4 — CI/CD, livraison, staging, rollback (2 h 30)

| # | Lire | Ouvrir à côté | Comprendre | Faire |
|---|---|---|---|---|
| 9 | `phase-04.md` | `.github/workflows/ci.yml` | `needs`, service PostgreSQL, `if: always()`, test de fumée | Ouvrir l'onglet *Actions* de GitHub sur une PR verte et sur la PR rouge |
| 10 | `phase-05.md` | `.github/workflows/release.yml` | Tag immuable, `GITHUB_TOKEN`, `packages: write`, labels OCI | Taguer `v1.0.0` après fusion, regarder *Packages* |
| 11 | `phase-06.md` | `compose.staging.yaml`, `scripts/wait-healthy.sh`, `scripts/deploy.sh` | `IMAGE_TAG`, pas de `build:`, boucle de santé, `.last-good-tag` | `./scripts/deploy.sh v1.0.0` |
| 12 | `phase-07.md` puis `INCIDENT-v1.1.0.md` | `git diff feature/staging chore/align-port-8000 -- Dockerfile` | Pourquoi Docker disait `healthy` alors que l'hôte ne joignait rien | Rejouer v1.1.0 → rollback → v1.1.1 |

## Jour 5 — Révision et répétition (1 h 30)

| # | Lire | Faire |
|---|---|---|
| 13 | `QUIZ.md` | Répondre à voix haute avant de lire chaque réponse |
| 14 | `SOUTENANCE.md` | Chronométrer le scénario de 10 minutes deux fois |
| 15 | `PREUVES.md` | Remplir toutes les lignes ⏳ (URL, captures) |

## Les six questions à savoir répondre sans hésiter

1. Pourquoi `0.0.0.0` et pas `127.0.0.1` dans le conteneur ?
2. Pourquoi l'API écrit `db` et pas `localhost` dans `DATABASE_URL` ?
3. Différence entre `docker compose down` et `docker compose down -v` ?
4. Pourquoi ne reconstruit-on jamais l'image en staging ?
5. Pourquoi un tag publié ne bouge jamais ?
6. Pourquoi un `HEALTHCHECK` interne ne suffit pas (incident v1.1.0) ?

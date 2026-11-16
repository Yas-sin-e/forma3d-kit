# Projet DevOps — Forma3D Studio

Sommaire du projet de fin de module DevOps (Licence 3 DSI, ISET, projet individuel).
La référence complète est le cahier des charges : [CAHIER-DEVOPS.md](CAHIER-DEVOPS.md).
**Par où commencer :** [PLAN-LECTURE.md](PLAN-LECTURE.md) donne l'ordre de lecture, jour par jour.
Le code applicatif n'est pas noté : seule la chaîne DevOps l'est.

## Phases et état

| Phase | Branche | Sujet | Barème | État | Compte rendu |
|---|---|---|:-:|---|---|
| P0 | `docs/devops-kickoff` | Diagnostic d'entrée et cadrage | (point 1) | Fait (PR à fusionner) | [phase-00.md](phase-00.md) |
| P3a | `feature/postgres-repository` | Dépôt PostgreSQL derrière `GenerationRepository` | point 4 | Fait, tests observés (PR à fusionner) | [phase-03a.md](phase-03a.md) |
| P1 | `chore/check-project` | Script Bash de contrôle | 2 | Fait, observé (PR à fusionner) | [phase-01.md](phase-01.md) |
| P2 | `feature/dockerfile` | Conteneuriser l'application | 3 | Fait, observé (PR à fusionner) | [phase-02.md](phase-02.md) |
| P3c | `feature/postgres-only` | Suppression de SQLite : PostgreSQL seule base | point 4 | Fait, tests observés (PR à fusionner) | [phase-03c.md](phase-03c.md) |
| P3d | `feature/data-migration` | Migration des données SQLite, test complet de l'application, visualisation | point 4 | Fait, observé (PR à fusionner) | [phase-03d.md](phase-03d.md) |
| P3b | `feature/compose-postgres` | Docker Compose : api + PostgreSQL | 3 | Fait, observé (PR à fusionner) | [phase-03b.md](phase-03b.md) |
| P4 | `ci/pipeline` | Pipeline CI `test` → `docker-build` | 3 | Écrit, testé en local ; exécution GitHub à observer | [phase-04.md](phase-04.md) |
| P5 | `ci/release` | Tag `v1.0.0` et image GHCR | 2 (avec P6) | Écrit ; tag et publication à faire après fusion | [phase-05.md](phase-05.md) |
| P6 | `feature/staging` | Mise en service staging + santé | 2 (avec P5) | Répété en local ; à refaire avec l'image GHCR | [phase-06.md](phase-06.md) |
| P7 | `chore/align-port-8000`, `fix/port-contract`, `docs/incident-rollback` | Incident `v1.1.0` et retour arrière | 1 | Répété en local ; à rejouer avec tags publiés | [phase-07.md](phase-07.md) |
| P8 | `docs/devops-final` | Documentation finale | — | Fait (PR à fusionner) | [FICHE-PROJET.md](FICHE-PROJET.md), [PREUVES.md](PREUVES.md), [QUIZ.md](QUIZ.md) |
| P9 | — | Répétition de la soutenance | 4 | Scénario écrit ; à répéter | [SOUTENANCE.md](SOUTENANCE.md) |
| B1–B3 | — | Bonus : protection de `main`, déploiement sur tag, matrice | +4 | Après P1–P7 | — |

## Ordre de fusion des branches

Les branches sont **empilées** : chacune part de la précédente. Fusionner les PR dans cet ordre, chacune
vers `main` ; après chaque fusion, la PR suivante ne montre plus que ses propres commits.

1. `docs/devops-kickoff` (P0)
2. `feature/postgres-repository` (P3a)
3. `chore/check-project` (P1)
4. `feature/dockerfile` (P2)
5. `feature/compose-postgres` (P3b)
6. `ci/pipeline` (P4) — puis ouvrir `test/failing-demo` sans la fusionner (PR rouge)
7. `ci/release` (P5) — puis tag `v1.0.0`
8. `feature/staging` (P6)
9. `chore/align-port-8000` (version défectueuse) — puis tag `v1.1.0`
10. `fix/port-contract` — puis tag `v1.1.1`
11. `docs/incident-rollback` (P7)
12. `docs/devops-final` (P8–P9)
13. `feature/postgres-only` (P3c, suppression de SQLite)
14. `feature/data-migration` (P3d, migration des données et chemins portables)

## Décisions tracées

| # | Date | Décision | Raison |
|---|---|---|---|
| D1 | 16/11/2026 | Docker et PostgreSQL sont autorisés **pour le projet DevOps uniquement** (exception au périmètre d'`AGENTS.md`). | Le barème exige une application conteneurisée et une vraie base dans un service séparé. |
| D2 | 16/11/2026 | Le dépôt PostgreSQL (P3a) est réalisé juste après P0, avant P1 et P2. | Choix de l'étudiante : P3a ne dépend pas de Docker pour le code, et c'est le plus gros chantier technique. Le cahier reste suivi pour toutes les autres phases. |
| D3 | 16/11/2026 | ~~SQLite reste le comportement par défaut (`DATABASE_URL` vide).~~ Remplacée par D5. | Prudence initiale : ne pas casser `dev.ps1` ni les tests. |
| D5 | 16/11/2026 | SQLite est retiré du code ; PostgreSQL est la seule base, `DATABASE_URL` obligatoire, tests sur une base `*_test`. | Demande de l'étudiante ; même base partout (parité dev/prod). Détails : [phase-03c.md](phase-03c.md). |
| D4 | 16/11/2026 | Visualisation de la base avec DBeaver ou HeidiSQL (fournis par Laragon) via un fichier `compose.debug.yaml` qui publie PostgreSQL **uniquement** sur `127.0.0.1:5433`. | Le barème exige que 5432 ne soit pas publié en usage normal ; l'accès debug reste local et volontaire. |

## Règles rappelées

- Une phase = une branche + une pull request (Objectif / Changements / Vérification), fusionnée par l'étudiante.
- Commits courts au format `type: message` à l'impératif.
- Aucun secret dans Git, une image ou un journal ; `backend/.env` n'est jamais lu ni modifié.
- Aucun résultat déclaré sans l'avoir observé (pipeline, image, santé).
- Méthode de diagnostic : état → journaux (première erreur utile) → configuration effective → hypothèse → une seule correction → revalidation.

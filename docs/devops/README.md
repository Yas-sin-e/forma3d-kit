# Projet DevOps — Forma3D Studio

Sommaire du projet de fin de module DevOps (Licence 3 DSI, ISET, projet individuel).
La référence complète est le cahier des charges : [CAHIER-DEVOPS.md](CAHIER-DEVOPS.md).
Le code applicatif n'est pas noté : seule la chaîne DevOps l'est.

## Phases et état

| Phase | Branche | Sujet | Barème | État | Compte rendu |
|---|---|---|:-:|---|---|
| P0 | `docs/devops-kickoff` | Diagnostic d'entrée et cadrage | (point 1) | En cours | [phase-00.md](phase-00.md) |
| P3a | `feature/postgres-repository` | Dépôt PostgreSQL derrière `GenerationRepository` | point 4 | À faire (avancée, voir décision D2) | — |
| P1 | `chore/check-project` | Script Bash de contrôle | 2 | À faire | — |
| P2 | `feature/dockerfile` | Conteneuriser l'application | 3 | À faire | — |
| P3b | `feature/compose-postgres` | Docker Compose : api + PostgreSQL | 3 | À faire | — |
| P4 | `ci/pipeline` | Pipeline CI `test` → `docker-build` | 3 | À faire | — |
| P5 | `ci/release` | Tag `v1.0.0` et image GHCR | 2 (avec P6) | À faire | — |
| P6 | `feature/staging` | Mise en service staging + santé | 2 (avec P5) | À faire | — |
| P7 | `docs/incident-rollback` | Incident `v1.1.0` et retour arrière | 1 | À faire | — |
| P8 | `docs/devops-final` | Documentation finale | — | À faire | — |
| P9 | — | Répétition de la soutenance | 4 | À faire | — |
| B1–B3 | — | Bonus : protection de `main`, déploiement sur tag, matrice | +4 | Après P1–P7 | — |

## Décisions tracées

| # | Date | Décision | Raison |
|---|---|---|---|
| D1 | 16/11/2026 | Docker et PostgreSQL sont autorisés **pour le projet DevOps uniquement** (exception au périmètre d'`AGENTS.md`). | Le barème exige une application conteneurisée et une vraie base dans un service séparé. |
| D2 | 16/11/2026 | Le dépôt PostgreSQL (P3a) est réalisé juste après P0, avant P1 et P2. | Choix de l'étudiante : P3a ne dépend pas de Docker pour le code, et c'est le plus gros chantier technique. Le cahier reste suivi pour toutes les autres phases. |
| D3 | 16/11/2026 | SQLite reste le comportement par défaut (`DATABASE_URL` vide). | `scripts/dev.ps1` et les tests existants ne doivent pas casser. |
| D4 | 16/11/2026 | Visualisation de la base avec DBeaver ou HeidiSQL (fournis par Laragon) via un fichier `compose.debug.yaml` qui publie PostgreSQL **uniquement** sur `127.0.0.1:5433`. | Le barème exige que 5432 ne soit pas publié en usage normal ; l'accès debug reste local et volontaire. |

## Règles rappelées

- Une phase = une branche + une pull request (Objectif / Changements / Vérification), fusionnée par l'étudiante.
- Commits courts au format `type: message` à l'impératif.
- Aucun secret dans Git, une image ou un journal ; `backend/.env` n'est jamais lu ni modifié.
- Aucun résultat déclaré sans l'avoir observé (pipeline, image, santé).
- Méthode de diagnostic : état → journaux (première erreur utile) → configuration effective → hypothèse → une seule correction → revalidation.

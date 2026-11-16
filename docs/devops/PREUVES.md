# Preuves du projet DevOps

Légende : ✅ observé (date, sortie recopiée) · ⏳ à produire par l'étudiante (lien ou capture à ajouter).
Aucune ligne ⏳ ne doit être présentée comme faite en soutenance avant d'avoir été remplie.

## 1. Git propre (2 pts)

| Preuve | État | Référence |
|---|---|---|
| Aucun `.env` ni jeton `hf_`/`ghp_` dans l'historique | ✅ 16/11/2026 | `phase-00.md` §3 |
| Branches par phase, commits `type: message` | ✅ | `git log --oneline --graph --all` |
| Liste des PR fusionnées | ⏳ | URL de chaque PR à ajouter ici |

## 2. Script de contrôle (2 pts)

| Preuve | État | Référence |
|---|---|---|
| `[SUCCES]`, code 0 | ✅ | `phase-01.md` §4 |
| Fichier requis manquant → code 1 ; `--strict` sale → code 1 | ✅ | `phase-01.md` §4 |
| Bit exécutable `100755`, fins de ligne LF | ✅ | `git ls-files -s scripts/check-project.sh` |

## 3. Image Docker (3 pts)

| Preuve | État | Référence |
|---|---|---|
| `forma3d:1.0` 312 Mo, `healthy`, `/health` OK | ✅ | `phase-02.md` §4 |
| `whoami` → `appuser` ; aucun `.env` dans l'image | ✅ | `phase-02.md` §4 |
| Incident `Exited (3)` + `docker logs` | ✅ | `phase-02.md` §4 |

## 4. Compose + PostgreSQL (3 pts)

| Preuve | État | Référence |
|---|---|---|
| `api` et `db` healthy, 5432 non publié | ✅ | `phase-03b.md` §4 |
| `getent hosts db` → `172.19.0.2 db` | ✅ | `phase-03b.md` §4 |
| Catégorie `bench` conservée après `down` / `up` | ✅ | `phase-03b.md` §4 |
| Incident `localhost` → `Connection refused` → correction | ✅ | `phase-03b.md` §4 |
| Tests du dépôt PostgreSQL : 176 passed (P3a) ; 177 passed, PostgreSQL seule base (P3c) | ✅ | `phase-03a.md` §4, `phase-03c.md` §4 |
| Migration de tes données (17 générations, rejouée sans doublon) et test complet dans le navigateur | ✅ | `phase-03d.md` §4–5 |
| Capture DBeaver des tables | ⏳ | à capturer (`compose.debug.yaml`, 127.0.0.1:5433) |

## 5. Pipeline CI (3 pts)

| Preuve | État | Référence |
|---|---|---|
| Job `test` reproduit en local (Python 3.12 + PostgreSQL, 176 passed, report.xml) | ✅ | `phase-04.md` §4 |
| URL d'une exécution **verte** sur une PR | ⏳ | après `git push` de `ci/pipeline` |
| URL d'une exécution **rouge** (`test/failing-demo`) + capture de la première erreur | ⏳ | branche locale prête |
| `docker-build` « skipped » sur la PR rouge | ⏳ | capture |
| Artefact `rapport-tests` téléchargé | ⏳ | capture |

## 6. Livraison et staging (2 pts)

| Preuve | État | Référence |
|---|---|---|
| Répétition locale `deploy.sh v1.0.0` → staging sain | ✅ (image étiquetée localement) | `phase-06.md` §4 |
| Tag `v1.0.0` visible sur GitHub | ⏳ | après fusion dans `main` |
| Workflow « Release » vert, paquet visible dans *Packages* | ⏳ | URL |
| `docker pull ghcr.io/yas-sin-e/forma3d:v1.0.0` | ⏳ | sortie |

## 7. Retour arrière (1 pt)

| Preuve | État | Référence |
|---|---|---|
| `deploy.sh v1.1.0` échoue, retour automatique à v1.0.0 (39 s) | ✅ (répétition locale) | `phase-07.md` §4 |
| `deploy.sh v1.1.1` sain | ✅ (répétition locale) | `phase-07.md` §4 |
| Garde-fou « contrat de port » détecte la v1.1.0 | ✅ | `phase-07.md` §4 |
| Même déroulé avec les tags publiés | ⏳ | `phase-07.md` §5 |

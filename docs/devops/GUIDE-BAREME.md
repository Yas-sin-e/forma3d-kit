# Guide barème — chaque exigence, son explication, sa vérification

Ce document relie **chaque ligne du guide étudiant** (7 points essentiels, 3 bonus, 3 livrables,
soutenance) à quatre réponses : **où c'est** dans le projet, **comment c'est fait** (en mots simples),
**la commande pour le vérifier** et **le résultat attendu**. Si une commande ne donne pas le résultat
attendu, la colonne « Si ça manque » dit quoi faire.

Toutes les commandes se lancent à la racine du dépôt, dans un terminal Bash (Git Bash ou WSL2), Docker
Desktop démarré. Dernière vérification complète : 16 novembre 2026.

## 0. Tableau de bord

| # | Exigence | Pts | État | Preuve principale |
|---|---|:-:|---|---|
| 1 | Git propre | 2 | ✅ | PR #13, #14 fusionnées ; aucun secret dans l'historique |
| 2 | Script Bash 0 / non nul | 2 | ✅ | `scripts/check-project.sh` |
| 3 | Conteneuriser | 3 | ✅ | `Dockerfile` : `healthy`, `appuser`, 312 Mo |
| 4 | Compose + base | 3 | ✅ | `compose.yaml` : api + PostgreSQL, 17 générations persistées |
| 5 | Pipeline CI | 3 | ✅ | run vert et run rouge (URL au §9) |
| 6 | Livrer et mettre en service | 2 | ✅ | `v1.0.1` sur GHCR, staging sain |
| 7 | Revenir en arrière | 1 | ✅ | `v1.1.0` refusée → retour à `v1.0.1` |
| — | Soutenance | 4 | à répéter | `SOUTENANCE.md` |
| B1 | Protection de `main` | +1 | ⏳ décision à prendre | §8 |
| B2 | Déploiement automatique sur tag | +2 | code prêt, à prouver par un tag | §8 |
| B3 | Matrice de versions | +1 | code prêt, à observer sur la PR | §8 |

---

## 1. Git propre (2 pts)

**L'exigence :** commits clairs, branches et merge requests, `.gitignore`, aucun secret.

**Comment c'est fait :** chaque phase a été écrite sur sa propre branche (`feature/dockerfile`,
`ci/pipeline`…), avec des commits courts au format `type: message` (`feat:`, `fix:`, `docs:`, `ci:`,
`test:`, `chore:`). Rien n'est poussé directement sur `main` : tout passe par une pull request (GitHub
appelle « pull request » ce que GitLab appelle « merge request »). Le `.gitignore` exclut les fichiers
`.env`, les environnements Python et les données locales.

| Vérifier | Commande | Résultat attendu |
|---|---|---|
| Historique lisible | `git log --oneline --graph -n 20` | fusions de PR et messages `type: message` |
| Aucun `.env` suivi | `git ls-files \| grep -E '(^\|/)\.env$' \|\| echo aucun` | `aucun` |
| Aucun `.env` dans l'historique | `git log --all --full-history --oneline -- "*.env" ".env"` | rien |
| Aucun jeton dans l'historique | `git log --all -p \| grep -Ec '(hf_[A-Za-z0-9]{20,}\|ghp_[A-Za-z0-9]{20,})'` | `0` |
| `.env.compose` ignoré | `git check-ignore -v .env.compose` | une règle `.gitignore` |

**Si ça manque :** un secret trouvé → le **révoquer** d'abord, puis seulement nettoyer.
**À savoir (honnêteté) :** les 14 branches de phase ont été fusionnées d'un coup par la PR #13 ; les
commits et les branches par phase restent visibles (`git log --graph`, onglet *Branches*).
**Détails :** `phase-00.md`.

## 2. Script Bash de contrôle (2 pts)

**L'exigence :** un script qui renvoie 0 en succès et un code non nul en échec.

**Comment c'est fait :** `scripts/check-project.sh` vérifie les fichiers requis, l'absence de `.env`
ou de données suivies par Git, les marqueurs de conflit et le « contrat de port » (le port de l'image
doit être celui publié par Compose). Il affiche `[OK]` ou `[ERREUR]` pour chaque contrôle, puis sort avec
`exit 0` ou `exit 1`. C'est ce code de sortie que la CI lit pour passer au vert ou au rouge.

| Vérifier | Commande | Résultat attendu |
|---|---|---|
| Succès | `./scripts/check-project.sh; echo "code=$?"` | `[SUCCES]`, `code=0` |
| Échec provoqué | `mv README.md R.bak; ./scripts/check-project.sh; echo "code=$?"; mv R.bak README.md` | `[ERREUR] fichier manquant`, `code=1` |
| Garde-fou | `./scripts/check-project.sh --strict` | échoue s'il reste des changements non commités |
| Exécutable + LF | `git ls-files -s scripts/check-project.sh; git ls-files --eol scripts/check-project.sh` | `100755` ; `i/lf` |

**Si ça manque :** « Permission denied » → `git update-index --chmod=+x scripts/check-project.sh` ;
« bash\r » → fins de ligne Windows, corrigées par `.gitattributes`. **Détails :** `phase-01.md`.

## 3. Conteneuriser (3 pts)

**L'exigence :** Dockerfile, `.dockerignore`, tag explicite, utilisateur non root, HEALTHCHECK.

**Comment c'est fait :** le `Dockerfile` part de `python:3.12-slim` (version fixée, jamais `latest`),
installe les dépendances **avant** de copier le code (cache des couches), crée l'utilisateur `appuser`,
déclare un `HEALTHCHECK` qui appelle `/health`, et lance uvicorn sur `0.0.0.0:8080`. Le `.dockerignore`
empêche tout `.env` ou donnée locale d'entrer dans l'image.

| Vérifier | Commande | Résultat attendu |
|---|---|---|
| Construction, tag explicite | `docker build -t forma3d:1.0 .` | image `forma3d:1.0` |
| Taille | `docker image ls forma3d` | environ 312 Mo |
| Non root | `docker compose exec api whoami` | `appuser` |
| Santé | `docker inspect --format '{{.State.Health.Status}}' forma3d-api-1` | `healthy` |
| Aucun secret dans l'image | `docker compose exec api sh -c 'ls /app/.env /app/backend/.env'` | « No such file » |

**Si ça manque :** conteneur `Exited` → `docker ps -a` puis `docker logs <nom>`, lire la **première**
erreur. L'application exige `DATABASE_URL` : lancée seule sans base, elle s'arrête avec un message clair.
**Détails :** `phase-02.md`.

## 4. Assembler avec Compose (3 pts)

**L'exigence :** application + base, connexion par nom de service, port de la base non publié, volume
persistant, démarrage conditionné à la santé.

**Comment c'est fait :** `compose.yaml` décrit deux services. `api` se connecte à PostgreSQL par
`DATABASE_URL=...@db:5432/...` : `db` est le **nom du service**, résolu par le DNS interne de Compose.
Le service `db` n'a **pas** de `ports:` ; ses données sont dans le volume nommé `pgdata` ; `api` attend
la base grâce à `depends_on: condition: service_healthy` (test `pg_isready`).

| Vérifier | Commande | Résultat attendu |
|---|---|---|
| Démarrer | `cp -n .env.compose.example .env.compose; docker compose up -d --build --wait` | 2 services `healthy` |
| Port de la base non publié | `docker compose ps` | `db … 5432/tcp` **sans** `0.0.0.0:` ni `127.0.0.1:` |
| Nom de service | `docker compose exec api getent hosts db` | une adresse IP suivie de `db` |
| Persistance | `docker compose down && docker compose up -d --wait`, puis la requête ci-dessous | mêmes chiffres qu'avant |
| Volumes | `docker volume ls --filter name=forma3d_` | `forma3d_pgdata`, `forma3d_storage` |

```bash
docker compose exec db psql -U forma3d -d forma3d -c "SELECT count(*) FROM generations;"
```
Observé le 16/11/2026 : 5 catégories, 17 générations (3 terminées), 1 clé API.

**Si ça manque :** `Connection refused` dans `docker compose logs api` → `DATABASE_URL` pointe sur
`localhost` au lieu de `db`. **Ne jamais lancer `docker compose down -v`** : c'est la seule commande qui
efface les données. **Détails :** `phase-03a.md` à `phase-03d.md`.

### Voir la base de données (pour toi et pour le jury)

```bash
docker compose -f compose.yaml -f compose.debug.yaml up -d --wait
```
Puis `C:\laragon\bin\dbeaver\dbeaver.exe` → *Nouvelle connexion* → PostgreSQL → hôte `127.0.0.1`, port
`5433`, base `forma3d`, utilisateur `forma3d`, mot de passe `dev-password` (valeur fictive de
`.env.compose`). Tables dans `forma3d` → *Schémas* → `public` → *Tables*. Après : `docker compose up -d`
referme le port 5433. Sans DBeaver :

```bash
docker compose exec db psql -U forma3d -d forma3d -c "\dt"
docker compose exec db psql -U forma3d -d forma3d -c "SELECT slug, label, is_active FROM categories;"
```
Explication des tables et colonnes : `docs/COMPRENDRE-FORMA3D.md`, section 6.

## 5. Pipeline CI (3 pts)

**L'exigence :** workflow déclenché sur merge request, tests puis construction de l'image (`needs`),
rapport de tests en artefact.

**Comment c'est fait :** `.github/workflows/ci.yml` se déclenche sur `pull_request` (et sur `main`).
Le job `test` démarre un PostgreSQL jetable, lance `check-project.sh` puis pytest, et publie le rapport
JUnit en artefact **même en cas d'échec** (`if: always()`). Le job `docker-build` a `needs: test` : il ne
démarre que si les tests réussissent ; il construit l'image puis la démarre et appelle `/health`.

| Vérifier | Commande | Résultat attendu |
|---|---|---|
| Runs récents | `gh run list --workflow ci.yml --limit 5` | `success` sur `main` et sur les PR |
| PR verte | `gh pr checks 14` | `test pass`, `docker-build pass` |
| PR rouge | `gh pr checks 15` | `test fail`, `docker-build skipping` |
| Première erreur utile | `gh run view 43965191693 --log-failed \| grep -m1 AssertionError` | `AssertionError: assert {'status': 'ok'} == {'status': 'broken'}` |
| Artefact | onglet *Summary* du run → *Artifacts* | `rapport-tests` (présent aussi sur le run rouge) |
| Tests en local | voir §10 | `179 passed` |

**Si ça manque :** la CI ne démarre pas → elle ne tourne que sur une pull request ou sur `main`.
**Détails :** `phase-04.md`.

## 6. Livrer et mettre en service (2 pts)

**L'exigence :** tag `vX.Y.Z`, image publiée et jamais reconstruite, mise en service en environnement de
test avec contrôle de santé.

**Comment c'est fait :** pousser un tag `v…` déclenche `release.yml`, qui rejoue les tests puis publie
`ghcr.io/yas-sin-e/forma3d:<tag>` avec le `GITHUB_TOKEN` temporaire (aucun secret stocké).
`compose.staging.yaml` utilise cette image **sans `build:`** ; la version est la variable `IMAGE_TAG`.
`scripts/deploy.sh` tire l'image, démarre la pile, puis `scripts/wait-healthy.sh` interroge `/health`
jusqu'à 12 fois et renvoie 0 ou 1.

| Vérifier | Commande | Résultat attendu |
|---|---|---|
| Tags | `git ls-remote --tags origin` | `v1.0.1`, `v1.1.0`, `v1.1.1` (et `v1.0.0`, voir ci-dessous) |
| Publications | `gh run list --workflow release.yml --limit 5` | `success` pour les trois |
| Connexion GHCR | `gh auth token \| docker login ghcr.io -u Yas-sin-e --password-stdin` | `Login Succeeded` |
| Image tirée | `docker pull ghcr.io/yas-sin-e/forma3d:v1.0.1` | téléchargée, non construite |
| Mise en service | `docker compose down; cp -n .env.staging.example .env.staging; ./scripts/deploy.sh v1.0.1; echo "code=$?"` | `staging sain`, `code=0` |
| Version en service | `docker compose -p forma3d-staging -f compose.staging.yaml --env-file .env.deploy ps` | `api ghcr.io/…:v1.0.1 (healthy)` |

**À savoir :** `v1.0.0` a été posé avant la fusion, sur un commit sans `release.yml` : il n'a produit
aucune image et n'a **pas été déplacé** (un tag publié ne bouge jamais) ; la version saine est `v1.0.1`.
Le staging utilise le port 8080 : arrêter la pile de développement avant (`docker compose down`).
**Détails :** `phase-05.md`, `phase-06.md`.

## 7. Revenir en arrière (1 pt)

**L'exigence :** retour à la version précédente démontré.

**Comment c'est fait :** `v1.1.0` est une version volontairement défectueuse (elle écoute sur le port
8000 alors que le staging publie 8080). `deploy.sh` constate l'échec du contrôle de santé, affiche les
journaux, puis remet automatiquement le dernier tag sain, mémorisé dans `.last-good-tag`. Aucune image
n'est reconstruite. La correction est publiée en `v1.1.1`.

| Vérifier | Commande | Résultat attendu |
|---|---|---|
| Point de départ | `./scripts/deploy.sh v1.0.1` | `staging sain` |
| Incident | `ATTEMPTS=6 ./scripts/deploy.sh v1.1.0; echo "code=$?"` | `staging non sain`, `Uvicorn running on http://0.0.0.0:8000`, `RETOUR ARRIÈRE vers v1.0.1`, `Retour arrière réussi`, `code=1` |
| Après le retour | `cat .last-good-tag` | `v1.0.1` |
| Correction | `./scripts/deploy.sh v1.1.1` | `staging sain` |
| Retour manuel | `echo "IMAGE_TAG=v1.0.1" > .env.deploy && docker compose -p forma3d-staging -f compose.staging.yaml --env-file .env.deploy up -d && ./scripts/wait-healthy.sh` | `staging sain` |

Observé le 16/11/2026 avec les images de GHCR (sorties dans `phase-07.md` §4b).
**Détails :** `phase-07.md`, `INCIDENT-v1.1.0.md`.

---

## 8. Les bonus (+4, comptés seulement si les 7 points sont présents)

### B1 — Protection de `main` : une merge request rouge ne peut plus être fusionnée (+1)
**Blocage :** sur un compte GitHub gratuit, les règles de protection ne s'appliquent pas à un dépôt
**privé**. Deux solutions, à décider par l'étudiante :
1. rendre le dépôt public (*Settings → General → Danger Zone → Change visibility*) — sans risque pour
   les secrets, l'historique a été contrôlé (§1) ;
2. activer GitHub Education (Pro gratuit pour les étudiants).

Ensuite : *Settings → Rules → Rulesets → New branch ruleset* → cible `main` → cocher *Require a pull
request before merging* et *Require status checks to pass* → ajouter les checks `test (Python 3.12)`,
`test (Python 3.13)` et `docker-build`. **Preuve :** la PR #15 (rouge) affiche « Merging is blocked ».

### B2 — Déploiement automatique sur tag (+2)
**Comment c'est fait :** dans `release.yml`, le job `deploy-staging` (`needs: publish`,
`environment: staging`) met en service l'image du tag sur le runner avec `compose.staging.yaml`, puis
lance `wait-healthy.sh`. Si la santé échoue, le job est rouge et affiche les journaux. Le runner est un
staging **jetable** : il prouve que l'image publiée démarre avec sa base, puis il est détruit.

**À faire pour la preuve** (après fusion de la PR qui ajoute ce job) :
```bash
git switch main && git pull --ff-only
git cat-file -e HEAD:.github/workflows/release.yml && git tag -a v1.2.0 -m "Release 1.2.0" && git push origin v1.2.0
gh run watch
```
Attendu : trois jobs verts, `test` → `publish` → `deploy-staging`, et une entrée dans *Deployments*.

### B3 — Matrice de versions (+1)
**Comment c'est fait :** dans `ci.yml`, le job `test` a une `strategy.matrix` avec Python `3.12` et
`3.13`, et `fail-fast: false` pour voir les deux résultats même si l'un échoue. Un artefact par version :
`rapport-tests-3.12`, `rapport-tests-3.13`.

**Résultats à expliquer :** 3.12 est la version de l'image Docker (celle qui tourne réellement) ; 3.13
prouve que le code est prêt pour la version suivante. Si 3.13 échouait seule, on saurait que le problème
vient d'une incompatibilité du langage ou d'une dépendance, pas du code métier.
**Vérifier :** `gh pr checks <numéro de la PR>` → `test (Python 3.12)` et `test (Python 3.13)`.

---

## 9. Les livrables

| Livrable demandé | Où | État |
|---|---|---|
| Dépôt Git avec README pour démarrer en une commande | `README.md`, section « Démarrer en une commande (Docker) » | ✅ |
| Adresse d'une exécution **réussie** | https://github.com/Yas-sin-e/forma3d-kit/actions/runs/43965184922 (PR #14) | ✅ |
| Adresse d'une exécution **en échec** | https://github.com/Yas-sin-e/forma3d-kit/actions/runs/43965191693 (PR #15) | ✅ |
| Fiche d'une page (architecture, version, retour arrière) | `docs/devops/FICHE-PROJET.md` | ✅ |

Démarrage en une commande (après `cp .env.compose.example .env.compose`, une seule fois) :
```bash
docker compose up -d --build
```
Puis http://localhost:8080.

## 10. Tester toute l'application

```bash
# 1. La pile et la santé
docker compose -f compose.yaml -f compose.debug.yaml up -d --build --wait
curl -fsS http://localhost:8080/health                      # {"status":"ok"}

# 2. Les tests automatiques (base de test séparée, créée une seule fois)
docker compose exec db psql -U forma3d -d forma3d -c "CREATE DATABASE forma3d_test" 2>/dev/null
cd backend
PYTHON_DOTENV_DISABLED=true HF_SPACE_ID= \
  TEST_DATABASE_URL=postgresql://forma3d:dev-password@127.0.0.1:5433/forma3d_test \
  python -m pytest -q                                        # 179 passed
cd ..

# 3. Le contrôle du dépôt
./scripts/check-project.sh --strict                          # [SUCCES]
```
Sous Windows, `./scripts/dev.ps1` enchaîne base, tests et serveur. Dans le navigateur
(http://localhost:8080, mot de passe fictif de `.env.compose`) : Accueil → 3 modèles, 1 clé, 5 catégories ;
ouvrir un modèle → le viewer 3D s'affiche. Une génération 3D réelle n'est pas nécessaire pour la
démonstration (aucun fournisseur gratuit configuré : `/health/provider` répond `UNCONFIGURED`).

## 11. La soutenance (4 pts) : ce qu'il faut montrer en 10 minutes

| Demandé par le guide | Quoi montrer | Commande ou lien |
|---|---|---|
| Une merge request au pipeline vert | PR #14, onglet *Checks* | `gh pr view 14 --web` |
| Une autre qui échoue + première erreur utile | PR #15, job `test`, ligne `AssertionError` ; `docker-build` sauté | `gh pr view 15 --web` |
| La mise en service d'une version | `v1.0.1`, staging sain | `./scripts/deploy.sh v1.0.1` |
| Le retour arrière | `v1.1.0` refusée, retour à `v1.0.1` | `ATTEMPTS=6 ./scripts/deploy.sh v1.1.0` |

Scénario minuté : `SOUTENANCE.md`. Questions probables et réponses : `QUIZ.md`. La veille : tirer les
trois images (`docker pull …:v1.0.1`, `:v1.1.0`, `:v1.1.1`) pour ne pas dépendre du réseau.

## 12. Où trouver l'explication de chaque fichier

| Besoin | Document |
|---|---|
| Rôle de **chaque fichier et dossier** (176 fichiers suivis, tous référencés) | `docs/STRUCTURE.md` |
| Explication du code de l'application, ligne par ligne | `docs/COMPRENDRE-FORMA3D.md` |
| Explication de chaque phase DevOps | `docs/devops/phase-00.md` à `phase-07.md` |
| Ordre de lecture sur 5 jours | `docs/devops/PLAN-LECTURE.md` |
| Preuves observées | `docs/devops/PREUVES.md` |

Contrôlé le 16/11/2026 : chaque fichier suivi par Git est cité dans `STRUCTURE.md`, chaque fichier de code
commence par un en-tête « Rôle / Exécution », et aucun code SQLite ne reste dans le projet.

# Phase P4 — Pipeline CI : `test` → `docker-build`

- **Branche :** `ci/pipeline`
- **Barème :** point 5, « CI sur PR, `test` → `docker-build` (`needs`), artefact » (3 pts).

## 1. Objectif

À chaque pull request, GitHub vérifie **automatiquement** que le code est livrable : contrôle du dépôt,
tests sur SQLite **et** sur un vrai PostgreSQL, rapport de tests téléchargeable, puis construction de
l'image et test de fumée. Si les tests échouent, l'image n'est même pas construite. C'est
l'intégration continue : on détecte une régression en minutes, avant la fusion dans `main`.

## 2. Fichiers

| Fichier | Action | Rôle |
|---|---|---|
| `.github/workflows/ci.yml` | réécrit | Deux jobs chaînés, service PostgreSQL, artefact JUnit, test de fumée |
| `scripts/check-project.sh` | modifié | Reprend les contrôles de documents de l'ancien workflow (`AGENTS.md`, `docs/ETAT.md`…) |

## 3. Le workflow expliqué

| Élément | Pourquoi | Sans lui |
|---|---|---|
| `on: pull_request` + `push: branches: [main]` | Vérifie chaque PR avant fusion, puis `main` après fusion | L'ancien `push:` sans filtre lançait la CI deux fois par PR |
| `permissions: contents: read` | Moindre privilège : le jeton du pipeline ne peut rien modifier | Un script compromis pourrait écrire dans le dépôt |
| `concurrency … cancel-in-progress` | Un nouveau push annule l'exécution devenue obsolète | Minutes gratuites gaspillées |
| `services: postgres` + `--health-cmd pg_isready` | Un vrai PostgreSQL jetable à côté du job ; GitHub attend qu'il soit sain | Les 7 tests PostgreSQL seraient ignorés en CI |
| `PYTHON_DOTENV_DISABLED`, `HF_SPACE_ID: ""` | Tests isolés : aucun `.env`, aucun appel au fournisseur 3D | Tests dépendants d'un service gratuit instable |
| `setup-python` 3.12 + `cache: pip` | Même version que l'image ; dépendances mises en cache entre exécutions | Version différente de la production ; installation lente |
| `./scripts/check-project.sh` | Le script de l'atelier 2 devient une **porte** du pipeline (code ≠ 0 → job rouge) | Contrôles uniquement manuels |
| `pytest --junitxml=report.xml` | Rapport standard JUnit, lisible par les outils CI | Résultat seulement dans le journal texte |
| `upload-artifact` + **`if: always()`** | Le rapport est publié **même si** les tests échouent, c'est là qu'il sert | En cas d'échec, l'étape serait sautée et le rapport perdu |
| `needs: test` | `docker-build` attend le succès de `test` | On construirait une image à partir d'un code cassé |
| `push: false`, `load: true`, tag `forma3d:ci` | La CI vérifie que l'image se construit ; publier est le rôle de la release (P5) | Chaque PR publierait une image |
| Test de fumée `/health` | Prouve que l'image **démarre** et répond, pas seulement qu'elle se construit | Une image qui plante au démarrage passerait (cf. incident P7) |

Versions d'actions vérifiées le 16/11/2026 par `git ls-remote --tags` : `checkout@v7`, `setup-python@v7`,
`upload-artifact@v7`, `setup-buildx-action@v4`, `build-push-action@v7`.

## 4. Vérifications

**Observé en local le 16/11/2026** (reproduction du job `test` dans `python:3.12-slim` avec PostgreSQL) :
`176 passed in 13.21s`, `report.xml` de 22 Ko généré. Le YAML est valide (`yaml.safe_load` : jobs
`test`, `docker-build`, `needs: test`). L'image se construit et passe `/health` (P2).

**Non vérifiable depuis cette session :** l'exécution réelle sur GitHub Actions (pas de `gh`, branche non
poussée). À contrôler par l'étudiante après le push :

```bash
git push -u origin ci/pipeline
# puis ouvrir la PR et regarder l'onglet Actions :
# https://github.com/Yas-sin-e/forma3d-kit/actions
```

### PR rouge de démonstration (ne pas fusionner)
Une branche locale **`test/failing-demo`** est prête : elle modifie volontairement l'assertion de
`backend/tests/test_health.py` (`"ok"` → `"broken"`).
```bash
git push -u origin test/failing-demo     # puis ouvrir une PR vers main, sans la fusionner
```
Attendu : job `test` rouge, première erreur utile `AssertionError` dans `test_health.py`, artefact
`rapport-tests` quand même présent (grâce à `if: always()`), job `docker-build` **non démarré** (`needs`).

### Résultats observés sur GitHub (16/11/2026)

- PR #14 : `test` pass (49 s), `docker-build` pass (1 min 1 s) — https://github.com/Yas-sin-e/forma3d-kit/actions/runs/43965184922
- PR #15 (rouge, non fusionnée) : `test` fail, `docker-build` *skipping* ; première erreur utile `AssertionError: assert {'status': 'ok'} == {'status': 'broken'}` à `tests/test_health.py:27` — https://github.com/Yas-sin-e/forma3d-kit/actions/runs/43965191693
- L'artefact `rapport-tests` existe sur les deux runs (y compris le rouge, grâce à `if: always()`).

### Bonus B3 : matrice de versions

Le job `test` tourne désormais sur Python 3.12 et 3.13 (`strategy.matrix`, `fail-fast: false`), avec un
artefact par version (`rapport-tests-3.12`, `rapport-tests-3.13`). Vérifié en local : `179 passed` sous
3.12 et sous 3.13 (conteneurs `python:3.12-slim` et `python:3.13-slim`). Explication : `GUIDE-BAREME.md` §8.

## 5. Preuves à conserver

URL d'une exécution verte, URL de l'exécution rouge avec capture surlignée de la première erreur,
capture montrant `docker-build` « skipped », capture de l'artefact `rapport-tests` téléchargé.

## 6. À dire en soutenance

> Mon pipeline se déclenche sur chaque pull request et sur `main`. Le job `test` lance mon script de
> contrôle puis les tests, y compris contre un vrai PostgreSQL fourni par un service container, et publie
> le rapport JUnit même en cas d'échec grâce à `if: always()`. Le job `docker-build` dépend de `test`
> par `needs` : si un test échoue, l'image n'est pas construite, comme le montre ma PR rouge. Enfin, un
> test de fumée démarre l'image et appelle `/health`, car une image qui se construit n'est pas forcément
> une image qui démarre.

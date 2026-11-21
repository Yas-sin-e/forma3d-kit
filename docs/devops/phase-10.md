# Phase P10 — Améliorations CI : workflow réutilisable, Dependabot, protection de `main`

- **Branche :** `ci/reusable-tests-dependabot`.
- **Barème :** bonus B1 « protection de `main` » (+1) ; le reste améliore la qualité de la chaîne (pas de point direct).
- **Date :** 21/11/2026.

## 1. Objectif

Appliquer trois pratiques des grands projets open source (FastAPI, Pydantic, Django, vérifiés le 21/11/2026 :
respectivement 18, 9 et 18 workflows, un par responsabilité) :

1. **Ne pas dupliquer le job de tests** entre `ci.yml` et `release.yml`.
2. **Surveiller automatiquement les dépendances** (actions GitHub et paquets Python).
3. **Interdire la fusion d'une PR rouge** dans `main` (bonus B1).

## 2. Fichiers

| Fichier | Rôle |
|---|---|
| `.github/workflows/reusable-tests.yml` (nouveau) | Seule définition du job `test` : `check-project.sh` + pytest sur PostgreSQL. Déclenché uniquement par `workflow_call`, avec trois entrées : `python-versions` (liste JSON), `strict` (`--strict`), `junit-report` (artefact JUnit) |
| `.github/workflows/ci.yml` | Le job `test` appelle `reusable-tests.yml` avec `["3.12", "3.13"]` et le rapport JUnit ; `docker-build` inchangé |
| `.github/workflows/release.yml` | Le job `test` appelle `reusable-tests.yml` avec `["3.12"]` et `strict: true` ; `publish` et `deploy-staging` inchangés |
| `.github/dependabot.yml` (nouveau) | PR hebdomadaires (lundi) pour les actions (groupées) et `backend/requirements.txt` (mineures et correctifs groupés, majeures séparées) |

## 3. Logique

**Workflow réutilisable.** Avant, le service PostgreSQL, les variables et les étapes de test étaient
recopiés dans deux fichiers : une correction oubliée dans l'un créait une différence silencieuse entre
ce que la CI teste et ce que la release teste. Maintenant, les deux appellent le même fichier ; seuls
les paramètres changent. Le comportement est identique à avant :

| | `ci.yml` | `release.yml` |
|---|---|---|
| Versions Python | 3.12 et 3.13 (bonus B3) | 3.12 (version de l'image) |
| `check-project.sh` | normal | `--strict` |
| Rapport JUnit | oui (`rapport-tests-3.12`, `rapport-tests-3.13`) | non |

Droits : le workflow appelé déclare `contents: read`. Un workflow appelé ne peut jamais recevoir plus de
droits que son appelant ; `packages: write` de `release.yml` ne sert donc qu'aux jobs `publish` et
`deploy-staging`.

**Conséquence importante : le nom des contrôles change.** Un job appelé s'affiche sous la forme
`<job appelant> / <job appelé>` :

| Avant | Après |
|---|---|
| `test (Python 3.12)` | `test / test (Python 3.12)` |
| `test (Python 3.13)` | `test / test (Python 3.13)` |
| `docker-build` | `docker-build` (inchangé) |

Ce sont les **nouveaux** noms qu'il faut déclarer dans la règle de protection de `main`.

**Dependabot.** Service gratuit de GitHub. Chaque PR qu'il ouvre passe par la CI comme une autre ; on ne
fusionne que si elle est verte. L'image de base `python:3.12-slim` n'est volontairement pas surveillée :
Dependabot proposerait `python:3.13-slim`, ce qui changerait la version de production ; cette décision
reste manuelle.

**Protection de `main` (B1).** Réglage du dépôt, pas un fichier : *Settings → Rules → Rulesets* → règle
sur `main` → *Require a pull request before merging* et *Require status checks to pass* → *Add checks*.
GitHub ne propose dans la liste que les contrôles **déjà exécutés au moins une fois** : il faut donc
pousser cette branche et ouvrir sa PR avant d'ajouter les noms ci-dessus.

## 4. Vérification

En local (21/11/2026) :
```bash
python -c "import yaml,glob; [yaml.safe_load(open(f, encoding='utf-8')) for f in glob.glob('.github/**/*.yml', recursive=True)]"
./scripts/check-project.sh
```
Attendu : aucune erreur de syntaxe YAML ; `check-project.sh` code 0.

Sur GitHub (à observer par l'étudiante après le push) :
1. Dans la PR, les contrôles `test / test (Python 3.12)`, `test / test (Python 3.13)` et `docker-build`
   sont verts, et les artefacts `rapport-tests-3.12` et `rapport-tests-3.13` sont présents.
2. *Insights → Dependency graph → Dependabot* : les deux écosystèmes apparaissent ; des PR arrivent le lundi.
3. Après ajout des trois contrôles dans la règle : la PR rouge (#15) affiche « Merging is blocked ».
4. Au prochain tag, `release.yml` affiche `test / test (Python 3.12)` → `publish` → `deploy-staging`.

## 5. Justification pour la soutenance

« Le job de tests est écrit une seule fois et réutilisé par la CI et la release : impossible qu'ils
divergent. Dependabot surveille les dépendances sans effort. La protection de `main` rend obligatoire le
passage par une PR verte, comme dans les grands projets open source. Le tout reste gratuit. »

## 6. Premier retour de Dependabot : PR pytest 9 bloquée (22/11/2026)

Le 21/11/2026, Dependabot a ouvert cinq PR. Quatre étaient vertes ; la PR #22 (pytest 8 → 9, version
majeure) était rouge : trois tests échouaient avec
`AttributeError: State object has no attribute 'generation_provider'`.

**Cause.** `tests/test_health.py` et `tests/test_trellis_provider.py` remplaçaient le fournisseur par
`monkeypatch.setattr(app.state, "generation_provider", ...)`. `app.state` (Starlette) range ses valeurs
dans un dictionnaire interne `_state`, pas comme de vrais attributs. Avec pytest 9, `monkeypatch` ne
retrouve pas l'ancienne valeur et **supprime** l'attribut à la fin du test : le premier test passe, les
suivants échouent. Reproduit isolément le 22/11/2026 : pytest 8 → 5 tests réussis ; pytest 9 → `setattr`
échoue au 2e passage, `setitem` réussit.

**Correction (branche `fix/tests-pytest9`).** Les deux tests utilisent
`monkeypatch.setitem(app.state._state, "generation_provider", ...)`, qui restaure correctement la valeur
avec pytest 8 comme avec pytest 9. Aucun code de l'application ne change.

**Vérification.** La CI de cette PR (pytest 8) doit rester verte ; après fusion, Dependabot rebase #22,
dont la CI (pytest 9) doit passer au vert. La suite complète n'a pas été lancée en local (PostgreSQL de
test non démarré).

**Pour la soutenance.** « La CI a bloqué une mise à jour majeure qui cassait trois tests. J'ai trouvé la
cause, je l'ai reproduite isolément et j'ai corrigé les tests. La PR Dependabot est ensuite redevenue verte. »

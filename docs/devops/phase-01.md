# Phase P1 — Script Bash de contrôle

- **Branche :** `chore/check-project`
- **Barème :** point 2, « script Bash de contrôle 0 / non nul » (2 pts) — lien atelier 2 → atelier 5.

## 1. Objectif

Un script unique, rejouable par l'étudiante comme par le pipeline, qui répond « oui / non » à la
question « le dépôt est-il dans un état livrable ? ». La réponse est donnée par le **code de sortie** :
`0` = succès, `1` = échec. C'est la convention Unix sur laquelle reposent GitHub Actions, Docker
(`HEALTHCHECK`) et tous les outils d'automatisation : un job CI échoue dès qu'une commande renvoie
un code non nul.

## 2. Fichiers

| Fichier | Action | Rôle |
|---|---|---|
| `scripts/check-project.sh` | créé (bit exécutable `100755`) | Les 4 contrôles, messages `[OK]`/`[ERREUR]`, bilan `[SUCCES]`/`[ECHEC]`, code 0/1 |
| `.gitattributes` | créé | Force les fins de ligne LF pour `*.sh`, `Dockerfile`, `*.yml`, `*.yaml` |

## 3. Logique expliquée

| Instruction | Pourquoi | Sans elle |
|---|---|---|
| `#!/usr/bin/env bash` | Trouve `bash` dans le `PATH` (Linux, WSL2, runner GitHub) | Le système ne saurait pas quel interpréteur utiliser |
| `set -uo pipefail` | `-u` : variable non définie = erreur (faute de frappe détectée) ; `pipefail` : un pipeline échoue si une étape échoue | Une faute de frappe donnerait une chaîne vide silencieuse |
| pas de `set -e` | On veut **tous** les contrôles puis le total `N erreur(s)` | Le script s'arrêterait à la première erreur et cacherait les suivantes |
| `git rev-parse --show-toplevel` puis `cd` | Fonctionne depuis n'importe quel sous-dossier | Les chemins relatifs seraient faux hors de la racine |
| `git ls-files` | Liste ce qui est **suivi** par Git, pas ce qui existe sur le disque | Un `backend/.env` local (normal, ignoré) déclencherait une fausse alerte |
| `git grep -I` pour `<<<<<<<` | Détecte un conflit de fusion oublié, en ignorant les binaires (GLB, images) | Un fichier cassé pourrait être livré |
| `--strict` + `git status --porcelain` | Défi atelier 2 : refuse de valider s'il reste du travail non commité (ex. avant un tag) | On pourrait taguer une version différente de ce qui est dans Git |
| `fail` écrit sur **stderr** (`>&2`) | Sépare les erreurs de la sortie normale (`2>erreurs.txt`) | Impossible de filtrer les erreurs |
| `git update-index --chmod=+x` | Sous Windows, le système de fichiers n'a pas de bit exécutable : on l'inscrit dans Git | `./scripts/check-project.sh` → « Permission denied » en CI |
| `.gitattributes` `*.sh text eol=lf` | Git convertit en LF quel que soit `core.autocrlf` | Linux lit `bash\r` → « No such file or directory » |

## 4. Lancer et tester (bash / WSL2)

```bash
./scripts/check-project.sh; echo "code=$?"            # attendu : [SUCCES], code=0
./scripts/check-project.sh --strict; echo "code=$?"   # code=1 s'il reste des changements non commités
mv README.md README.bak; ./scripts/check-project.sh; echo "code=$?"; mv README.bak README.md   # code=1
git ls-files -s scripts/check-project.sh               # 100755 = exécutable dans Git
git ls-files --eol scripts/check-project.sh            # i/lf w/lf attr/text eol=lf
```

**Observé le 16/11/2026 (Git Bash) :** succès `code=0` ; `--strict` avec fichiers indexés non commités
`code=1` ; `README.md` renommé → `[ERREUR] fichier manquant : README.md`, `code=1` ; option inconnue `code=1`.
Le pipeline (P4) exécute ce script dans le job `test`. Les fichiers `Dockerfile`, `.dockerignore` et
`compose.yaml` sont ajoutés à la liste des fichiers requis dans les phases P2 et P3b.

## 5. Preuves à conserver

- Capture d'une exécution `[SUCCES]` suivie de `echo $?` → `0`.
- Capture d'un échec provoqué (fichier renommé) → `1`.
- Sortie de `git ls-files -s` montrant `100755`.

## 6. À dire en soutenance

> Mon script de contrôle vérifie les fichiers requis, l'absence de secret, de base SQLite ou de GLB
> suivis par Git, et l'absence de marqueurs de conflit. Il communique son résultat par le code de
> sortie, 0 ou 1, ce qui permet au pipeline de s'arrêter automatiquement en cas d'échec. Je n'utilise
> pas `set -e` pour que toutes les erreurs soient listées en une seule exécution. Comme je travaille
> sous Windows, j'ai forcé les fins de ligne LF avec `.gitattributes` et inscrit le bit exécutable dans
> Git, deux pièges classiques qui font échouer un script en CI.

# Phase P5 — Version immuable et publication sur GHCR

- **Branche :** `ci/release`
- **Barème :** point 6, première partie, « tag `vX.Y.Z`, image publiée non reconstruite » (2 pts avec P6).

## 1. Objectif

Transformer un commit validé de `main` en **version** : un tag Git `v1.0.0` et une image Docker
`ghcr.io/yas-sin-e/forma3d:v1.0.0` construite une seule fois puis réutilisée telle quelle partout
(staging, rollback). C'est la livraison continue : l'image est prête automatiquement ; la mise en
service reste une décision humaine (P6).

## 2. Fichier

| Fichier | Action | Rôle |
|---|---|---|
| `.github/workflows/release.yml` | créé | Sur tag `v*.*.*` : rejoue contrôles et tests, puis construit et publie l'image sur GHCR |

## 3. Logique expliquée

| Élément | Pourquoi | Sans lui |
|---|---|---|
| `on: push: tags: ["v*.*.*"]` | Seul un tag de version publie une image | Chaque push produirait une « version » |
| `permissions: packages: write` | Droit minimal pour écrire dans GHCR, rien d'autre | Publication refusée (ou droits excessifs) |
| `secrets.GITHUB_TOKEN` | Jeton créé par GitHub pour **cette** exécution, expiré ensuite ; jamais écrit nulle part | Il faudrait un jeton personnel stocké en secret, à faire tourner |
| job `test` puis `needs: test` | On ne publie pas une version dont les tests échouent | Image cassée publiée sous un numéro de version |
| `check-project.sh --strict` | Le code tagué est exactement celui de Git | — |
| `metadata-action` | Tag d'image = tag Git ; labels OCI `source`, `revision` (commit), `version` | Impossible de retrouver de quel commit vient une image |
| `ghcr.io/yas-sin-e/…` en minuscules | GHCR refuse les majuscules (`Yas-sin-e`) | `invalid reference format` |

**Règle d'immuabilité :** un tag publié ne bouge jamais. Une erreur dans `v1.0.0` se corrige par
`v1.0.1`, jamais en déplaçant ou en réécrivant `v1.0.0`. C'est ce qui rend le rollback fiable :
« revenir à v1.0.0 » désigne toujours exactement la même image.

## 4. Procédure de livraison (à exécuter par l'étudiante, après fusion des PR dans `main`)

```bash
git switch main && git pull --ff-only
./scripts/check-project.sh --strict
git tag -a v1.0.0 -m "Release 1.0.0"
git show v1.0.0 --stat | head -5
git push origin v1.0.0
# Suivre : https://github.com/Yas-sin-e/forma3d-kit-codex/actions  (workflow « Release »)
# Image  : https://github.com/Yas-sin-e?tab=packages
```

Le dépôt étant privé, le paquet GHCR est **privé** par défaut. Pour le tirer en local :
```bash
docker login ghcr.io -u Yas-sin-e      # coller un jeton personnel « read:packages » quand il est demandé
docker pull ghcr.io/yas-sin-e/forma3d:v1.0.1
```
Le jeton est saisi au terminal, jamais écrit dans un fichier ni dans le dépôt.

## 5. Incident de livraison réel : tag `v1.0.0` posé trop tôt (16/11/2026)

1. **Ce qui s'est passé :** le tag `v1.0.0` a été poussé sur `c447aca`, l'ancien `main`, **avant** la fusion de la PR n°13. Ce commit ne contient pas `release.yml`.
2. **Ce qu'on a observé :** dans *Actions*, le run #97 sur `v1.0.0` est l'**ancien** workflow « Project checks » (un seul job, vert) ; le workflow « Release » n'a pas tourné ; *Packages* est resté vide.
3. **Cause :** GitHub exécute les workflows **présents dans le commit tagué**. Un tag sur un commit sans `release.yml` ne publie rien.
4. **Décision :** on **ne déplace pas** `v1.0.0` (règle d'immuabilité, même sans image). On publie `v1.0.1` sur le bon commit.
5. **Prévention :** taguer seulement après `git switch main && git pull --ff-only`, et vérifier `git cat-file -e HEAD:.github/workflows/release.yml` avant `git push origin vX.Y.Z`.

### Versions retenues

| Tag | Commit | Contenu | Rôle |
|---|---|---|---|
| `v1.0.0` | `c447aca` (ancien `main`) | aucun `release.yml` | **posé par erreur avant la fusion : aucune image, jamais déplacé** |
| `v1.0.1` | `4b2d063` (fin de P6) | image port 8080, staging | version saine de référence |
| `v1.1.0` | `3552bb5` (port 8000) | version volontairement défectueuse | incident P7 |
| `v1.1.1` | `a17c181` (`main` après la PR n°13) | correction du port, contrôle du contrat de port, PostgreSQL seule base | correction de l'incident |

```bash
git fetch origin --tags
git tag -a v1.0.1 4b2d063 -m "Release 1.0.1 : version saine de reference"
git tag -a v1.1.0 3552bb5 -m "Release 1.1.0 : version defectueuse pour l'incident P7"
git tag -a v1.1.1 a17c181 -m "Release 1.1.1 : correction du port et PostgreSQL seule base"
git push origin v1.0.1 v1.1.0 v1.1.1
```

## 6. État de vérification

- YAML validé localement (jobs `test` → `publish`, permissions `contents: read`, `packages: write`).
- Observé (captures de l'étudiante) : tag `v1.0.0` poussé, run #97 « Project checks » vert, aucun « Release ».
- **Non observé :** les workflows « Release » de `v1.0.1`, `v1.1.0`, `v1.1.1` et les images sur GHCR (tags à pousser par l'étudiante).

## 7. Preuves à conserver

Tag visible sur GitHub (*Releases/Tags*), exécution verte du workflow « Release », paquet `forma3d`
visible dans *Packages* avec les tags `v1.0.1`, `v1.1.0`, `v1.1.1`, sortie de `docker pull`.

## 8. À dire en soutenance

> Une version est un tag Git annoté `v1.0.0` ; le pousser déclenche le workflow de release, qui rejoue
> les tests puis publie l'image sur GHCR avec le même numéro. La connexion utilise uniquement le
> `GITHUB_TOKEN` temporaire fourni par GitHub, avec la permission minimale `packages: write`. L'image
> porte des labels OCI qui indiquent le commit d'origine. Un tag publié ne bouge jamais : une correction
> devient `v1.0.1`, ce qui garantit que revenir à une version redonne exactement la même image. Je l'ai
> appliqué pour de vrai : mon tag `v1.0.0`, posé avant la fusion, ne contenait pas le workflow de release ;
> je ne l'ai pas déplacé, j'ai publié `v1.0.1`.

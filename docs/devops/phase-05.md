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
docker pull ghcr.io/yas-sin-e/forma3d:v1.0.0
```
Le jeton est saisi au terminal, jamais écrit dans un fichier ni dans le dépôt.

## 5. État de vérification

- YAML validé localement (jobs `test` → `publish`, permissions `contents: read`, `packages: write`).
- **Non observé :** l'exécution du workflow, le tag et l'image sur GHCR — ils nécessitent la fusion dans
  `main` et le push du tag, qui sont des actions de l'étudiante.

## 6. Preuves à conserver

Tag visible sur GitHub (*Releases/Tags*), exécution verte du workflow « Release », paquet `forma3d`
visible dans *Packages* avec le tag `v1.0.0`, sortie de `docker pull`.

## 7. À dire en soutenance

> Une version est un tag Git annoté `v1.0.0` ; le pousser déclenche le workflow de release, qui rejoue
> les tests puis publie l'image sur GHCR avec le même numéro. La connexion utilise uniquement le
> `GITHUB_TOKEN` temporaire fourni par GitHub, avec la permission minimale `packages: write`. L'image
> porte des labels OCI qui indiquent le commit d'origine. Un tag publié ne bouge jamais : une correction
> devient `v1.0.1`, ce qui garantit que revenir à `v1.0.0` redonne exactement la même image.

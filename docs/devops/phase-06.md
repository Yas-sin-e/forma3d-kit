# Phase P6 — Mise en service en staging

- **Branche :** `feature/staging`
- **Barème :** point 6, seconde partie, « staging + santé » (2 pts avec P5).

## 1. Objectif

Mettre en service une **version publiée** (pas du code source) dans un environnement proche de la
production, puis **décider automatiquement** si elle est saine. La version en service est une simple
variable, `IMAGE_TAG` : changer de version ou revenir en arrière ne demande ni reconstruction ni
modification du code.

## 2. Fichiers

| Fichier | Action | Rôle |
|---|---|---|
| `compose.staging.yaml` | créé | `api` = `ghcr.io/yas-sin-e/forma3d:${IMAGE_TAG}` (pas de `build:`), même `db` et volumes qu'en P3b |
| `.env.staging.example` | créé | Modèle sans secret de `.env.staging` (base `forma3d_staging`, valeurs fictives) |
| `.env.deploy.example` | créé | Modèle de `.env.deploy` : une seule ligne `IMAGE_TAG=v1.0.0` |
| `scripts/wait-healthy.sh` | créé | 12 tentatives × 5 s sur `/health` ; « staging sain » code 0, sinon « staging non sain » code 1 |
| `scripts/deploy.sh` | créé | Écrit `.env.deploy`, `pull`, `up -d`, appelle `wait-healthy.sh`, rollback automatique sinon |
| `.gitignore` | modifié | Ignore `.last-good-tag` (`.env.staging` et `.env.deploy` le sont déjà par `.env.*`) |

## 3. Logique expliquée

| Élément | Pourquoi | Sans lui |
|---|---|---|
| `image:` sans `build:` | On déploie **l'image testée par la CI et publiée**, octet pour octet | Reconstruire en staging produirait une image différente de celle testée |
| `${IMAGE_TAG:?…}` | Compose refuse de démarrer si la version n'est pas fixée, avec un message clair | Compose prendrait une valeur vide → `forma3d:` invalide |
| `IMAGE_TAG` dans `.env.deploy` | La version est une **donnée de configuration**, pas du code | Changer de version = modifier un fichier versionné et faire une PR en pleine panne |
| `-p forma3d-staging` | Nom de projet distinct : conteneurs, réseau et volumes séparés de la pile de dev | Le staging écraserait les volumes de développement |
| `restart: unless-stopped` | Le service revient seul après un redémarrage de Docker | Staging arrêté après un reboot |
| `wait-healthy.sh` : boucle bornée | L'API met quelques secondes à démarrer ; on attend au plus 60 s puis on **décide** | Un seul essai échouerait trop tôt ; une attente infinie bloquerait le déploiement |
| `curl -fsS --max-time 3` | `-f` transforme un HTTP ≥ 400 en échec ; `--max-time` évite d'attendre indéfiniment | Une page d'erreur 500 serait vue comme un succès |
| `HEALTH_URL`, `ATTEMPTS`, `DELAY` | Paramétrables par l'environnement (CI, autre port) | Script à modifier pour chaque usage |
| `.last-good-tag` | Mémorise la dernière version **prouvée saine** : c'est la cible du rollback | On ne saurait pas vers quoi revenir |
| `SKIP_PULL=1` | Répétition hors ligne avec des images déjà présentes (plan B de soutenance) | Démo dépendante du réseau et de GHCR |

## 4. Lancer et vérifier

```bash
cp .env.staging.example .env.staging
docker compose down                                  # libère le port 8080 de la pile de dev
docker login ghcr.io -u Yas-sin-e                    # paquet privé : jeton read:packages saisi au terminal
./scripts/deploy.sh v1.0.0; echo "code=$?"
docker compose -p forma3d-staging -f compose.staging.yaml --env-file .env.deploy ps
git check-ignore -v .env.staging .env.deploy .last-good-tag
```

**Répétition observée le 16/11/2026, en local et hors ligne.** L'image `forma3d:1.0` construite en P2
a été étiquetée localement `ghcr.io/yas-sin-e/forma3d:v1.0.0` (`docker tag`) : **elle n'a pas été
publiée sur GHCR**. Puis `SKIP_PULL=1 ./scripts/deploy.sh v1.0.0` :

```
== [17:07:34] Mise en service de v1.0.0
[17:07:42] tentative 1/12 : pas de réponse saine de http://localhost:8080/health
[17:07:47] tentative 2/12 : {"status":"ok"}
staging sain
== [17:07:47] v1.0.0 en service.
```
`ps` : `api ghcr.io/yas-sin-e/forma3d:v1.0.0 Up (healthy)`, `db postgres:17-alpine Up (healthy)` ;
`.last-good-tag` contient `v1.0.0`. La première tentative échoue normalement (API en démarrage) :
c'est précisément pourquoi le script réessaie.

**À refaire avec la vraie image** après le push du tag `v1.0.0` (P5), sans `SKIP_PULL`.

## 5. Preuves à conserver

Sortie de `deploy.sh` (code 0), `docker compose … ps`, `git check-ignore -v` des trois fichiers.

## 6. À dire en soutenance

> En staging, je ne reconstruis jamais : `compose.staging.yaml` utilise l'image publiée sur GHCR, dont
> le tag vient de la variable `IMAGE_TAG`. Mon script `deploy.sh` fixe cette variable, tire l'image,
> démarre la pile puis appelle `wait-healthy.sh`, qui interroge `/health` jusqu'à douze fois et renvoie
> 0 ou 1. Si la version est saine, elle devient la dernière version connue saine ; sinon, le script
> revient automatiquement à la précédente. Le staging reste local, car le Studio n'a qu'une
> authentification mono-propriétaire.

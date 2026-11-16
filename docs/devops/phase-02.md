# Phase P2 — Conteneuriser l'application

- **Branche :** `feature/dockerfile`
- **Barème :** point 3, « Dockerfile, `.dockerignore`, tag explicite, non root, HEALTHCHECK » (3 pts).

## 1. Objectif

Emballer l'API, ses dépendances et le Studio dans une **image** : un paquet immuable qui tourne
de la même façon sur le poste, sur le runner GitHub et en staging. On supprime le classique
« ça marche sur ma machine » : l'environnement d'exécution fait partie de la livraison.

## 2. Fichiers

| Fichier | Action | Rôle |
|---|---|---|
| `Dockerfile` | créé | Recette de l'image : base, dépendances, code, utilisateur, port, santé, commande |
| `.dockerignore` | créé | Ce qui n'entre jamais dans le contexte de construction (secrets, données, Git, docs) |
| `scripts/check-project.sh` | modifié | `Dockerfile` et `.dockerignore` deviennent des fichiers requis |

## 3. Le Dockerfile, ligne par ligne

| Instruction | Pourquoi | Sans elle |
|---|---|---|
| `FROM python:3.12-slim` | Version **fixée** : construction reproductible ; `slim` = moins de paquets, moins de failles | Avec `latest`, l'image changerait toute seule d'un jour à l'autre |
| `ENV PYTHONUNBUFFERED=1` | Les journaux sortent tout de suite dans `docker logs` | Messages retardés ou perdus si le conteneur plante |
| `WORKDIR /app/backend` | `main.py` sert `/app/frontend` depuis son propre emplacement : on reproduit `backend/` et `frontend/` côte à côte | Le Studio renverrait 404 |
| `COPY requirements.txt` **puis** `pip install` **puis** `COPY app` | Cache des couches : les dépendances (101 Mo, l'étape lente) ne sont réinstallées que si `requirements.txt` change | Chaque modification de code réinstallerait tout |
| `pip install --no-cache-dir` | Le cache de pip ne reste pas dans l'image | Image plus lourde pour rien |
| `useradd … appuser` + `chown` + `USER appuser` | Principe du moindre privilège : une faille dans l'application ne donne pas root dans le conteneur | Le processus tourne en root |
| `EXPOSE 8080` | Documente le port d'écoute | Rien ne casse, mais l'image est moins lisible ; c'est `-p` ou Compose qui **publie** réellement |
| `HEALTHCHECK` en Python | Docker sait si l'application **répond**, pas seulement si le processus existe ; `curl` absent de `slim` | Un conteneur « Up » mais bloqué paraîtrait sain |
| `CMD ["uvicorn", …, "--host", "0.0.0.0"]` | 0.0.0.0 = toutes les interfaces du conteneur ; forme JSON : uvicorn est le PID 1 et reçoit le signal d'arrêt | Avec 127.0.0.1, le port publié ne répond pas (c'est l'incident prévu pour P7) |

### `.dockerignore`
Exclut `.git/`, `.env`, `.env.*` (sauf `.env.example`), `backend/data/`, `backend/storage/`, les `.venv`,
caches, `tests/`, `docs/`, `tools/`. Effets : **aucun secret** ne peut entrer dans l'image même par erreur,
le contexte envoyé au moteur est petit, et l'image ne contient ni base SQLite ni GLB locaux.
Dans le conteneur, `backend/.env` n'existe donc pas : la configuration arrive uniquement par l'environnement.

## 4. Vérifications (observées le 16/11/2026)

```bash
docker build -t forma3d:1.0 .
docker run -d -p 8080:8080 --name forma3d-api forma3d:1.0
docker inspect --format '{{.State.Health.Status}}' forma3d-api   # healthy
curl -fsS localhost:8080/health                                   # {"status":"ok"}
curl -s localhost:8080/health/provider                            # UNCONFIGURED (normal : aucun fournisseur configuré)
docker exec forma3d-api whoami                                    # appuser
docker exec forma3d-api ls -A /app /app/backend                   # backend frontend / app data requirements.txt storage
docker image ls forma3d                                           # forma3d:1.0  312MB
docker history forma3d:1.0                                        # la couche pip install pèse 101 Mo
docker rm -f forma3d-api
```

| Contrôle | Résultat observé |
|---|---|
| État de santé | `healthy` |
| `/health` | `{"status":"ok"}` |
| Utilisateur | `appuser` |
| `.env` dans l'image | absent (`/app/.env` et `/app/backend/.env` introuvables) |
| Taille | 312 Mo (base Python slim + dépendances, dont gradio_client et Pillow) |

### Incident pédagogique (méthode de diagnostic)
1. **État :** `docker run -d --name forma3d-bad forma3d:1.0 uvicorn app.mainn:app …` puis `docker ps -a` → `forma3d-bad Exited (3)`.
2. **Journaux :** `docker logs forma3d-bad` → première erreur utile : `Error loading ASGI app. Could not import module "app.mainn".`
3. **Configuration effective :** la commande passée remplace le `CMD` de l'image ; on la compare au `CMD` (`docker inspect`).
4. **Hypothèse :** faute de frappe dans le module (`mainn`).
5. **Correction unique :** relancer sans surcharger la commande.
6. **Revalidation :** `healthy` et `/health` OK.

## 5. Preuves à conserver

Captures de : `docker image ls forma3d`, `whoami` → `appuser`, `healthy`, `curl /health`, et l'incident (`Exited (3)` + ligne de log).

## 6. À dire en soutenance

> Mon image part de `python:3.12-slim` à version fixée et copie les dépendances avant le code pour
> profiter du cache des couches. L'application tourne sous un utilisateur non root, `appuser`, et un
> `HEALTHCHECK` écrit en Python permet à Docker de savoir si l'API répond réellement. Elle écoute sur
> 0.0.0.0 parce que 127.0.0.1 ne serait joignable que depuis l'intérieur du conteneur. Le
> `.dockerignore` garantit qu'aucun fichier `.env`, base locale ou GLB n'entre dans l'image : la
> configuration passe uniquement par l'environnement.

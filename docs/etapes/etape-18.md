# Étape 18 — Connexion côté serveur du Studio (Sprint 5f)

Date : 11 novembre 2026. Demandée explicitement par l'étudiante pour remplacer le verrou navigateur de l'étape 16b.

## Objectif et livrable vérifiable

- Objectif : seule la propriétaire peut utiliser le Studio, avec un mot de passe vérifié par le serveur et jamais présent dans le code.
- Livrable vérifiable : sans cookie, les routes du Studio répondent 401 ; avec le bon mot de passe, un cookie HttpOnly ouvre l'accès ; l'API `/api/v1`, `/embed`, `/public`, `/static` et le widget restent accessibles comme avant.

## Fichiers

| Fichier | Rôle |
|---|---|
| `backend/app/services/owner_auth.py` | Comparaison du mot de passe (`hmac.compare_digest`), jetons signés HMAC-SHA256 avec expiration, limiteur 5 tentatives/minute/IP |
| `backend/app/routers/auth.py` | `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` et dépendance `require_owner` |
| `backend/app/main.py` | Applique `require_owner` aux routeurs `/models`, `/categories`, `/api-keys` |
| `.env.example` | Ajoute `FORMA3D_OWNER_PASSWORD=` (vide) |
| `frontend/js/api.js` | Appels `/auth/*` et signal `forma3d:unauthorized` sur un 401 |
| `frontend/js/auth.js` | Indicateur de session lu sur `/auth/me` ; plus aucun mot de passe |
| `frontend/js/main.js`, `pages/login.js` | Vérification de session avant le routeur ; message si le mot de passe n'est pas configuré |
| `backend/tests/test_auth.py`, `backend/tests/conftest.py` | Tests de la connexion ; surcharge de dépendance pour les tests existants |

## Logique

1. La page de connexion envoie `{"password": "…"}` à `POST /auth/login`.
2. Le serveur compte la tentative pour l'IP (au-delà de 5 par minute : 429 avec `Retry-After`), lit `FORMA3D_OWNER_PASSWORD` (absent : 503) et compare en temps constant (faux : 401).
3. En cas de succès, il pose le cookie `forma3d_session` : HttpOnly, SameSite=Lax, Secure si la requête est en HTTPS, durée 8 h. Le jeton vaut `owner.<expiration>.<signature HMAC>` : il ne contient pas le mot de passe et ne peut pas être fabriqué sans la clé du serveur.
4. Chaque route du Studio vérifie la signature et l'expiration. Un 401 côté navigateur ramène à `#/login`.

La clé de signature est tirée au hasard au démarrage : un redémarrage du serveur déconnecte la propriétaire. C'est voulu (aucun secret supplémentaire à gérer).

## Lancement

Dans `backend/.env` (ignoré par Git), définir un mot de passe choisi par la propriétaire :

```text
FORMA3D_OWNER_PASSWORD=un-mot-de-passe-long
```

Puis lancer le serveur depuis la racine du dépôt :

```bash
backend/.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --port 8000
```

## Tests

```bash
cd backend
.venv/Scripts/python.exe -m pytest -q tests/test_auth.py
```

`test_auth.py` vérifie : 401 sur sept routes du Studio sans cookie, cookie HttpOnly/SameSite/Max-Age après connexion, déconnexion, mot de passe faux, mot de passe non configuré (503), limite de 5 tentatives, jeton falsifié ou expiré, et routes publiques ouvertes (`/`, `/health`, `/static`, `/api/v1` en 401 de clé, `/embed` et `/public` en 404 pour un modèle inconnu). Les autres tests ouvrent la session par `app.dependency_overrides` dans `conftest.py`.

## Limites pour la soutenance

- Usage local uniquement tant que le Studio n'est pas déployé derrière HTTPS : en HTTP, le cookie circule en clair sur le réseau.
- Pas de jeton CSRF dédié : SameSite=Lax empêche l'envoi du cookie sur les requêtes POST/PATCH/DELETE venant d'un autre site.
- Le limiteur est en mémoire : il repart à zéro au redémarrage et ne se partage pas entre plusieurs processus.
- `/health/provider` reste public : il ne renvoie qu'un statut, jamais l'URL du fournisseur.
- Non vérifié : le parcours de connexion dans un vrai navigateur.

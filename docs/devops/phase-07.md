# Phase P7 — Incident et retour arrière

- **Branches :** `chore/align-port-8000` (version défectueuse v1.1.0), `fix/port-contract` (correction v1.1.1),
  `docs/incident-rollback` (ce compte rendu).
- **Barème :** point 7, « retour arrière démontré » (1 pt).

## 1. Objectif

Prouver qu'une mauvaise version **ne reste pas en service** : elle est détectée par le contrôle de santé,
la version précédente est remise en service **sans reconstruire**, puis une correction est livrée sous un
nouveau numéro. Le projet étant individuel, l'étudiante fabrique elle-même la panne.

## 2. La panne choisie et pourquoi elle est réaliste

Le commit `chore: align container port with dev.ps1 (8000)` change, dans le `Dockerfile`, `EXPOSE`, `CMD`
et `HEALTHCHECK` vers le port 8000, et met à jour le test de fumée de la CI en conséquence. Tout est
cohérent **dans l'image** : la CI de l'époque est verte et Docker affiche `healthy`. Mais
`compose.staging.yaml` publie toujours `127.0.0.1:8080:8080` : le contrat entre l'image et son
déploiement est rompu. C'est une panne classique de **dérive de configuration**.

Observation clé (vérifiée) : un conteneur v1.1.0 lancé seul passe `healthy` (son contrôle interne
appelle `127.0.0.1:8000`), alors que `curl localhost:8090/health` (8090→8080) renvoie
`curl: (52) Empty reply from server`. **Un contrôle de santé interne ne suffit pas** : il faut vérifier
depuis l'endroit où se trouvent les utilisateurs, ce que fait `wait-healthy.sh`.

## 3. Fichiers

| Fichier | Branche | Rôle |
|---|---|---|
| `Dockerfile`, `.github/workflows/ci.yml` | `chore/align-port-8000` | Introduisent la panne (port 8000) — **ne pas fusionner dans `main`** si l'on ne veut pas rejouer l'incident |
| `Dockerfile`, `.github/workflows/ci.yml` | `fix/port-contract` | `git revert` du changement de port (v1.1.1) |
| `scripts/check-project.sh` | `fix/port-contract` | Nouveau contrôle « contrat de port » (image ↔ Compose) |
| `docs/devops/INCIDENT-v1.1.0.md` | `docs/incident-rollback` | Compte rendu en cinq lignes |
| `docs/devops/phase-07.md` | `docs/incident-rollback` | Ce document |

## 4. Déroulé observé le 16/11/2026 (répétition locale)

Images construites localement et étiquetées `ghcr.io/yas-sin-e/forma3d:v1.1.0` et `:v1.1.1` (non publiées),
déploiement avec `SKIP_PULL=1`. Point de départ : `v1.0.0` en service et saine (P6). Dans les versions
**publiées**, cette version saine s'appelle `v1.0.1` (voir `phase-05.md` §5).

**1. Mise en service de v1.1.0 → échec de santé (code 1)**
```
== [17:09:00] Mise en service de v1.1.0
[17:09:03] tentative 1/6 : pas de réponse saine de http://localhost:8080/health
...
[17:09:30] tentative 6/6 : pas de réponse saine de http://localhost:8080/health
staging non sain après 6 tentatives (http://localhost:8080/health)
```
**2. Journaux — première erreur utile**
```
api-1  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```
Il n'y a pas de trace d'erreur : l'application va bien, mais elle écoute sur 8000 alors que le port publié
est `127.0.0.1:8080->8080/tcp`. La méthode de diagnostic compare donc la **configuration effective**
(port d'écoute) à la configuration attendue (port publié).

**3. Retour arrière automatique → succès, sans reconstruction**
```
== [17:09:31] RETOUR ARRIÈRE vers v1.0.0
[17:09:39] tentative 2/6 : {"status":"ok"}
staging sain
== [17:09:39] Retour arrière réussi : v1.0.0 en service ; v1.1.0 refusé.
```
`ps` : `api ghcr.io/yas-sin-e/forma3d:v1.0.0 Up (healthy)`. Indisponibilité : **39 s**.

**4. Correction publiée en v1.1.1** (on ne réécrit pas v1.1.0)
```
== [17:10:35] Mise en service de v1.1.1
[17:10:44] tentative 2/12 : {"status":"ok"}
staging sain
== [17:10:44] v1.1.1 en service.
```
**5. Prévention vérifiée :** avec le `Dockerfile` de v1.1.0, `check-project.sh` échoue désormais :
```
[ERREUR] compose.yaml ne publie pas le port 8000 de l'image (contrat de port rompu)
[ERREUR] compose.staging.yaml ne publie pas le port 8000 de l'image (contrat de port rompu)
[ECHEC] 2 erreur(s).
```
La PR de v1.1.0 aurait donc été **rouge** en CI.

### Retour arrière manuel (sans `deploy.sh`), à savoir faire
```bash
echo "IMAGE_TAG=v1.0.1" > .env.deploy
docker compose -p forma3d-staging -f compose.staging.yaml --env-file .env.deploy up -d
./scripts/wait-healthy.sh; echo "code=$?"
```

## 5. Rejouer avec de vraies versions publiées (étudiante)

Tout le code est déjà dans `main` (PR n°13). Les trois versions sont des tags sur des commits de son historique :

1. Pousser les tags `v1.0.1`, `v1.1.0`, `v1.1.1` (`phase-05.md` §5) ; attendre les trois workflows « Release » verts.
2. `docker login ghcr.io -u Yas-sin-e` (jeton *read:packages* saisi au terminal), puis `./scripts/deploy.sh v1.0.1` → sain.
3. `./scripts/deploy.sh v1.1.0` → échec de santé, journaux, retour automatique à `v1.0.1`.
4. `./scripts/deploy.sh v1.1.1` → sain.
5. Compléter les heures réelles dans `INCIDENT-v1.1.0.md`.

## 6. Preuves à conserver

Sortie complète de `deploy.sh v1.1.0` (échec + retour arrière), extrait de log surligné, sortie
`deploy.sh v1.1.1`, sortie de `check-project.sh` sur le Dockerfile de v1.1.0, `INCIDENT-v1.1.0.md`.

## 7. À dire en soutenance

> J'ai livré volontairement une version v1.1.0 qui faisait écouter l'API sur le port 8000 alors que le
> staging publiait 8080 : Docker la disait saine, mais `/health` était injoignable depuis l'hôte.
> Mon script `wait-healthy.sh` l'a détecté et `deploy.sh` est revenu automatiquement à v1.0.0, sans
> reconstruire, avec 39 secondes d'indisponibilité. La correction a été publiée en v1.1.1, car un tag
> ne se réécrit jamais. Pour éviter la récidive, mon script de contrôle vérifie maintenant que le port
> de l'image correspond à celui des fichiers Compose, ce qui aurait fait échouer la CI de v1.1.0.

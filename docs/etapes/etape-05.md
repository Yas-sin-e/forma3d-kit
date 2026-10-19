# Sprint 1 — Étape 5 : page de génération et viewer

## Objectif et livrable vérifiable

Servir une page web simple depuis FastAPI pour envoyer une photo, suivre l'état réel d'une génération, afficher un GLB terminé avec `<model-viewer>` et le télécharger. Le livrable vérifiable est GET `/` qui renvoie la page complète et ses éléments d'interface, plus un test HTTP sans appel à Hugging Face.

Le parcours n'est pas présenté comme une génération réussie : les cinq appels réels à Stable Fast 3D ont échoué et aucun GLB n'existe. La page reste vide tant que le backend n'annonce pas `DONE` avec un vrai lien de modèle.

## Fichiers concernés

### `frontend/index.html`

Cette page autonome contient le HTML, le CSS et le JavaScript du prototype. Il n'y a pas de serveur React séparé. Les couleurs, la typographie, les panneaux, les états, les espacements et le mouvement reprennent `DESIGN.md`.

Le formulaire accepte JPG, PNG ou WebP et affiche le nom du fichier. Il contrôle extension, type MIME et taille pour aider la personne, puis laisse le backend refaire les contrôles de sécurité. Le bouton envoie le fichier réel à POST `/models` avec `FormData`.

Le navigateur interroge l'URL d'état renvoyée par l'API toutes les 1,5 secondes, sans inventer de barre de progression. Un verrou évite deux interrogations simultanées. À `FAILED`, il affiche le message serveur et arrête le suivi. À `DONE`, il attribue au viewer le lien GLB réel, révèle le téléchargement et les contrôles. Le chemin n'affiche donc jamais de modèle de démonstration fabriqué.

Le composant `<model-viewer>` fournit les gestes natifs de rotation et de zoom, le déplacement avec le geste souris/tactile documenté par le composant et les contrôles clavier. Les boutons supplémentaires tournent par pas de 15 degrés, déplacent la cible de caméra selon la taille du modèle, zooment et réinitialisent le cadrage. Les boutons restent cachés tant qu'un modèle n'a pas été livré.

`<model-viewer>` est chargé depuis la version 4.4.0 du CDN Google. Cela évite une compilation supplémentaire, mais le navigateur a besoin d'Internet pour charger ce composant. Le HTML reste servi localement par l'API.

### `backend/app/main.py`

Le point d'entrée importe `Path`, localise la racine du dépôt à partir de ce fichier, puis sert `frontend/index.html` sur GET `/` avec le type `text/html`. L'API et la page sont de même origine ; le navigateur peut donc appeler `/models` sans réglage CORS ni serveur frontend distinct.

### `backend/tests/test_frontend.py`

TestClient vérifie que GET `/` renvoie HTTP 200, le HTML français, le champ de fichier, le viewer, le suivi d'état et les contrôles de caméra. Ce test ne démarre ni navigateur réel, ni fournisseur distant, ni génération.

## Lancer et vérifier sous Windows PowerShell

Depuis `backend` :

    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

Ouvrir `http://127.0.0.1:8000/`. L'API de santé est à `/health` et la documentation OpenAPI à `/docs`. Depuis un autre terminal :

    .\.venv\Scripts\python.exe -m pytest -q

Résultat contrôlé : TestClient confirme la page et ses contrôles ; Uvicorn a aussi servi GET `/` sur localhost avec HTTP 200 et `text/html`, et l'affichage initial vide a été vérifié dans un navigateur. La suite et cette vérification ne chargent pas un GLB réel ; la manipulation dans le viewer reste à faire dès qu'une génération aboutit. La skill `playwright-cli` n'est pas installée dans l'environnement de travail.

## Pourquoi ces choix et limites

- Un seul serveur réduit les dépendances et simplifie la démonstration de soutenance.
- L'état reste une copie exacte de la réponse backend ; il n'y a ni progression fictive ni modèle simulé.
- Les contrôles de caméra visibles rendent les actions accessibles même si la personne ne connaît pas les gestes du viewer.
- Le CDN évite d'ajouter une chaîne Node au Sprint 1, avec la limite de connexion Internet signalée ci-dessus.
- Un viewer sans GLB ne valide pas la reconstruction. Le Sprint 1 reste ouvert tant que l'essai fournisseur et le parcours réel `DONE` n'ont pas abouti.

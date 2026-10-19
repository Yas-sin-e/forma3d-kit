# Sprint 1 — Étape 1 : structure et contrôle de santé

## Objectif et livrable vérifiable

Poser la base minimale du service de génération et prouver qu'il démarre. Le livrable de cette étape est une application FastAPI avec un endpoint réel GET /health et un test automatisé de son code HTTP et de son JSON.

Cette étape ne réalise pas encore l'envoi d'image, la génération Hugging Face, le stockage, le viewer ou le téléchargement. Ces tâches appartiennent aux étapes suivantes.

## Fichiers de code

### backend/app/__init__.py

Ce fichier marque le dossier app comme paquet Python importable. Il contient seulement sa documentation de module et n'exécute pas de serveur. Python le charge lorsqu'un module app est importé.

### backend/app/main.py

Ce module crée l'objet FastAPI nommé app et déclare le endpoint GET /health. La fonction health_check renvoie le statut JSON {"status":"ok"}. Uvicorn importe ce module pour servir l'API ; le test l'importe sans lancer un processus serveur.

### backend/tests/test_health.py

Pytest découvre la fonction test_health_endpoint_returns_ok_status. TestClient envoie une vraie requête à l'application en mémoire et vérifie la réponse HTTP 200 et le contenu JSON exact. Le test ne contacte aucun fournisseur distant.

## Configuration et documents créés ou adaptés

- backend/requirements.txt déclare FastAPI, Uvicorn, HTTPX2 et pytest nécessaires au serveur et au test. HTTPX2 est utilisé par la version actuelle de Starlette TestClient ; Gradio Client n'est pas ajouté avant l'étape du fournisseur.
- .env.example précise qu'aucune variable d'environnement n'est lue par le code à cette étape ; il ne contient aucun secret ni valeur fictive.
- .github/workflows/ci.yml exécute les tests backend et vérifie les fichiers de projet sur GitHub Actions.
- PRODUCT.md décrit le SaaS e-commerce, le parcours essentiel et les limites de reconstruction à partir d'une photo.
- DESIGN.md fixe les règles visuelles à suivre lors de la future interface.
- README.md donne l'état du projet et les commandes PowerShell pour installer, lancer et tester.
- AGENTS.md fixe le périmètre actif et rappelle le processus d'accord avant l'étape suivante.
- docs/STRUCTURE.md distingue les éléments présents des éléments futurs.
- docs/ETAT.md mémorise l'avancement, les décisions et la prochaine étape.
- docs/archive/v1/ conserve les anciennes instructions et les deux anciens guides sans les supprimer.
- docs/archive/v1/PROMPT-1-v1.md conserve l'ancien prompt ; PROMPT-1.md contient maintenant le prompt v2 local, ignoré par Git.
- backend/README.md et frontend/README.md expliquent le rôle réel et prévu de ces répertoires.
- .gitignore exclut les environnements virtuels, caches, données locales et fichiers de stockage.

## Installation et lancement sous Windows PowerShell

Depuis la racine du dépôt :

    cd backend
    python -m venv --without-pip .venv
    pip --python .venv\Scripts\python.exe install -r requirements.txt
    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

Dans le navigateur, ouvrir http://127.0.0.1:8000/health. Résultat attendu :

    {"status":"ok"}

La documentation interactive de l'API se trouve sur http://127.0.0.1:8000/docs.

Dans un second terminal PowerShell :

    cd backend
    .\.venv\Scripts\python.exe -m pytest -q

Résultat attendu : un test réussi. Ce poste Python 3.14 ne fournit pas ensurepip ; la commande pip --python installe ici dans le venv plutôt que dans Python global.

## Pourquoi cette conception

- FastAPI expose un endpoint HTTP réel avec peu de code et fournit une documentation interactive.
- Le point d'entrée reste unique et minimal avant les routes métier.
- TestClient valide l'application sans réseau, Space Hugging Face ni serveur séparé.
- Les dépendances sont limitées aux besoins actuels ; le client Hugging Face sera ajouté à l'étape 3.
- Les documents v1 sont archivés pour préserver l'historique et éviter qu'ils guident par erreur le nouveau SaaS.
- La CI lance le même test que le poste local, afin de repérer une erreur avant la soutenance.

## Vérifications effectuées

Sous Python 3.14.2, le test s'est exécuté dans backend/.venv : 1 test réussi, sans avertissement. Le test utilise l'application ASGI locale et n'appelle aucun service externe. Sous l'environnement Codex Windows, son exécution a nécessité l'autorisation d'accès aux sockets locales utilisées par asyncio ; sur un poste Windows normal, lancer la commande pytest ci-dessus.

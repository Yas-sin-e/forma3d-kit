# Backend

Le backend est le service HTTP de Forma3D Studio. Il sert la page sur GET /, expose GET /health, POST /models, GET /models/{id} et GET /models/{id}/glb. L'upload est validé puis stocké localement ; FastAPI démarre une tâche de fond et le service suit PENDING, RUNNING, DONE ou FAILED. Le modèle téléchargeable n'est disponible qu'après DONE.

## Fichiers
- app/main.py crée l'application FastAPI, sert `frontend/index.html` et branche les routes.
- app/routers/models.py reçoit l'upload, démarre la génération et expose état/téléchargement.
- app/schemas.py fixe le format JSON de l'état de génération.
- app/services/upload_validator.py vérifie extension, MIME, signature et taille maximale.
- app/services/generation_service.py coordonne les états, le fournisseur et le stockage.
- app/config.py charge les paramètres Hugging Face locaux et les valide.
- app/providers/base.py définit le contrat commun Image3DProvider.
- app/providers/huggingface.py inspecte le Space puis soumet une photo et contrôle la sortie GLB.
- app/storage/base.py définit l'interface de stockage.
- app/storage/local_storage.py enregistre les photos et GLB sous backend/storage/.
- app/models.py représente les états et métadonnées uniquement en mémoire.
- tests/test_huggingface_provider.py vérifie le contrat observé sans réseau et sans consommer de quota.
- tests/test_generation_service.py, tests/test_local_storage.py et tests/test_models_api.py vérifient le cycle sans appeler un fournisseur.
- app/__init__.py marque app comme paquet Python.
- tests/test_health.py appelle réellement l'application avec TestClient et vérifie la réponse HTTP.
- tests/test_upload_validator.py couvre les formats acceptés et les erreurs d'upload.
- tests/test_frontend.py vérifie que GET / sert la page, le viewer et ses contrôles, et que le parcours GLB local n'utilise pas fetch ni FormData.
- requirements.txt déclare les dépendances du serveur et du test.

## Lancer et tester sous PowerShell
Depuis le dossier backend :

    python -m venv --without-pip .venv
    pip --python .venv\Scripts\python.exe install -r requirements.txt
    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

Dans un second terminal placé dans backend :

    .\.venv\Scripts\python.exe -m pytest -q

Pour configurer HF_SPACE_ID, le jeton facultatif et les délais, copiez `.env.example` vers `backend/.env` (prioritaire) ou vers `.env` à la racine. Ces fichiers sont ignorés par Git. Sans jeton, l'accès anonyme dépend du quota gratuit partagé. Le registre des états disparaît au redémarrage ; les photos et modèles restent sous `backend/storage/`. Les essais de Stable Fast 3D et le blocage runtime de TripoSR sont détaillés dans `docs/etapes/etape-03.md`, `docs/etapes/etape-06.md` et `docs/ETAT.md`.

Sur le poste actuel, Python 3.14 ne fournit pas ensurepip ; le venv est créé sans pip puis le pip global cible explicitement le venv. Les paquets restent isolés de Python global.

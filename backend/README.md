# Backend

Le backend est le service HTTP de Forma3D Studio. Il sert la page sur GET /, ses fichiers CSS et JavaScript sous /static/, expose GET /health, POST /models, GET /models/{id}, GET /models/{id}/glb, GET /models/gallery et GET /models/gallery/{model_id}. L'upload est validé puis stocké localement ; FastAPI démarre une tâche de fond et le service suit PENDING, RUNNING, DONE ou FAILED. Le GLB d'une génération courante n'est disponible qu'après DONE.

## Fichiers

- app/main.py crée l'application FastAPI, sert frontend/index.html, publie les modules statiques et configure le catalogue de démonstration.
- app/routers/models.py reçoit l'upload, démarre la génération, expose l'état et le téléchargement ainsi que les routes de galerie.
- app/schemas.py fixe le format JSON de l'état de génération et de chaque entrée de galerie.
- app/services/upload_validator.py vérifie extension, MIME, signature et taille maximale.
- app/services/generation_service.py coordonne les états, le fournisseur et le stockage.
- app/services/demo_gallery.py n'autorise que les cinq noms GLB de faisabilité connus et vérifie leur structure avant de les lister ou de les servir.
- app/config.py charge les paramètres locaux ; HF_SPACE_ID accepte un identifiant de Space ou une URL HTTP(S) Gradio.
- app/providers/base.py définit le contrat commun Image3DProvider.
- app/providers/huggingface.py appelle view_api() à chaque génération, choisit les fonctions et paramètres publiés par Gradio, puis valide le conteneur GLB 2.0.
- app/storage/base.py définit l'interface de stockage.
- app/storage/local_storage.py enregistre les photos et GLB sous backend/storage/.
- app/models.py représente les états et métadonnées uniquement en mémoire.
- tests/test_huggingface_provider.py vérifie le contrat observé sans réseau et sans consommer de quota.
- tests/test_generation_service.py, tests/test_local_storage.py et tests/test_models_api.py vérifient le cycle sans appeler un fournisseur.
- tests/test_health.py appelle l'application avec TestClient et vérifie la réponse HTTP.
- tests/test_upload_validator.py couvre les formats acceptés et les erreurs d'upload.
- tests/test_frontend.py vérifie la page modulaire, les ressources statiques, l'isolation des appels HTTP dans api.js et l'absence d'envoi réseau des fichiers locaux.
- tests/test_demo_gallery.py vérifie le filtrage des GLB, la liste autorisée et le téléchargement sans réseau.
- requirements.txt déclare les dépendances du serveur et des tests.

## Lancer et tester sous PowerShell

Depuis le dossier backend :

    python -m venv --without-pip .venv
    pip --python .venv\Scripts\python.exe install -r requirements.txt
    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

Dans un second terminal placé dans backend :

    .\.venv\Scripts\python.exe -m pytest -q

Pour configurer HF_SPACE_ID, le jeton facultatif et les délais, copiez .env.example vers backend/.env (prioritaire) ou vers .env à la racine. Ces fichiers sont ignorés par Git. La variable accepte un identifiant de Space ou une URL complète Gradio. Le jeton Hugging Face n'est utilisé que pour contacter Hugging Face ; il n'est pas transmis à une URL externe. Le registre des générations disparaît au redémarrage ; les photos et modèles restent sous backend/storage/. Les essais et le serveur Colab sont détaillés dans docs/etapes/etape-03.md, docs/etapes/etape-06.md et docs/etapes/etape-06-colab.md.

Le CDN Google model-viewer version 4.4.0 est chargé dans le navigateur ; un accès Internet reste nécessaire pour afficher un modèle. La galerie utilise les fichiers locaux de backend/data/feasibility-results/ et renvoie une liste vide si les GLB ne sont pas présents sur un autre poste.

Sur le poste actuel, Python 3.14 ne fournit pas ensurepip ; le venv est créé sans pip puis le pip global cible explicitement le venv. Les paquets restent isolés de Python global.

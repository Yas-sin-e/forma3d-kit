# Backend

Le backend est le service HTTP de Forma3D Studio. Il sert la page sur GET / et ses fichiers CSS/JavaScript sous /static/. Il expose GET /health, GET /health/provider, POST /models, le suivi et le téléchargement des générations, la galerie ainsi que les photos sources disponibles. L'upload est validé puis stocké localement ; FastAPI suit PENDING, RUNNING, DONE ou FAILED. Le GLB d'une génération courante n'est disponible qu'après DONE.

## Fichiers

- app/main.py crée FastAPI, journalise une configuration locale absente sans révéler sa valeur et expose la santé du fournisseur.
- app/routers/models.py reçoit l'upload, démarre la génération, expose l'état, les fichiers et la galerie avec ses photos sources bornées.
- app/schemas.py fixe le format JSON de l'état, des modèles démo et de leur URL photo facultative.
- app/services/upload_validator.py vérifie extension, MIME, signature et taille maximale.
- app/services/generation_service.py coordonne les états, le fournisseur et le stockage.
- app/services/demo_gallery.py n'autorise que les cinq GLB connus, vérifie leur structure et ajoute la photo source seulement si elle existe.
- app/config.py charge la cible, les délais et les réglages TripoSR facultatifs ; aucune plage n'est devinée.
- app/providers/base.py définit le contrat commun Image3DProvider.
- app/providers/huggingface.py vérifie la cible en 5 secondes, appelle view_api() à chaque génération, utilise les bornes publiées et valide le conteneur GLB 2.0.
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

Copiez le `.env.example` racine vers `backend/.env` pour configurer `HF_SPACE_ID`, le jeton facultatif, les délais et, le cas échéant, `FOREGROUND_RATIO`/`MC_RESOLUTION`. Ces fichiers sont ignorés par Git. Les valeurs de qualité ne sont appliquées que si le contrat TripoSR courant publie ces champs et leurs bornes. Un jeton Hugging Face n'est jamais transmis à une URL publique externe. Le registre des générations disparaît au redémarrage ; les photos et modèles restent sous `backend/storage/`. Les essais et les limites Colab sont détaillés dans `docs/etapes/etape-06.md`, `docs/etapes/etape-06-colab.md` et `docs/etapes/etape-07.md`.

Le CDN Google model-viewer version 4.4.0 est chargé dans le navigateur ; un accès Internet reste nécessaire pour afficher un modèle. La galerie utilise les fichiers locaux de backend/data/feasibility-results/ et renvoie une liste vide si les GLB ne sont pas présents sur un autre poste.

Sur le poste actuel, Python 3.14 ne fournit pas ensurepip ; le venv est créé sans pip puis le pip global cible explicitement le venv. Les paquets restent isolés de Python global.

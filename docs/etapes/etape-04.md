# Sprint 1 — Étape 4 : génération, états et stockage local

## Objectif et livrable vérifiable

Accepter une photo validée, créer une demande suivable, lancer le fournisseur dans une tâche de fond, conserver les fichiers localement et exposer les états `PENDING`, `RUNNING`, `DONE` ou `FAILED`. Le livrable vérifiable est un contrat HTTP qui crée un travail en `202`, permet de consulter son état et refuse le téléchargement tant qu'aucun modèle n'est terminé.

Le fournisseur Hugging Face a renvoyé une exception interne sur trois photos ; le chemin `DONE` n'a donc pas été démontré par un modèle réel. Aucun test ni fichier de l'application ne fabrique de GLB pour masquer cet échec. Les tests de cette étape vérifient l'acceptation, l'enregistrement local de l'image et le chemin `FAILED`.

## Fichiers de code

### `backend/app/models.py`

`GenerationStatus` définit les quatre états du cycle. `GenerationRecord` garde l'identifiant, le nom client nettoyé, le type de fichier, le chemin d'image côté serveur, les dates, le chemin du GLB et une erreur éventuelle. `frozen=True` évite qu'une route modifie directement un état partagé.

Ces métadonnées sont en mémoire. Elles disparaissent si le processus Uvicorn redémarre ; aucun compte, historique permanent ou base de données n'est encore prévu au Sprint 1.

### `backend/app/storage/base.py` et `backend/app/storage/local_storage.py`

Le protocole `Storage` sépare la génération de la persistance. `LocalStorage` écrit sous `backend/storage/images/` et `backend/storage/models/`, crée les noms à partir de l'identifiant UUID serveur, refuse les extensions non prévues et utilise un fichier temporaire suivi d'un renommage atomique. `get_model_path()` ne reçoit jamais de chemin fourni par le navigateur.

Le contenu GLB est contrôlé par le fournisseur avant l'appel à `save_model()`. Les tests du stockage utilisent des octets ordinaires de test qui ne sont ni affichés ni annoncés comme un modèle 3D. Les fichiers sous `backend/storage/` sont ignorés par Git et restent présents localement jusqu'à leur suppression manuelle.

### `backend/app/services/generation_service.py`

`create_generation()` sauvegarde la photo validée et crée une fiche `PENDING`. `run()` marque ensuite le travail `RUNNING`, appelle le protocole `Image3DProvider`, sauvegarde le résultat, puis passe à `DONE`. Une erreur du fournisseur passe à `FAILED` avec le message prévu ; une erreur inattendue renvoie un message public neutre et journalise uniquement la classe de l'erreur.

Un verrou protège le dictionnaire en mémoire contre les tâches de fond et les requêtes HTTP concurrentes. Une demande inconnue ou déjà démarrée n'est pas exécutée une seconde fois.

### `backend/app/schemas.py` et `backend/app/routers/models.py`

`GenerationResponse` fixe les états et liens HTTP publics. `POST /models` lit au maximum 10 Mo plus un octet, valide l'image, la stocke et programme `GenerationService.run()` avec `BackgroundTasks`, puis renvoie HTTP 202 et le statut `PENDING`.

`GET /models/{id}` fournit le statut courant. `GET /models/{id}/glb` renvoie le fichier `model/gltf-binary` seulement si le statut est `DONE` et le modèle présent ; une demande inconnue renvoie 404, une génération non terminée renvoie 409. Aucun chemin du disque n'est exposé dans le JSON.

### `backend/app/main.py`

Le démarrage configure un seul `GenerationService` dans `app.state`, avec `HuggingFaceSpaceProvider` et `LocalStorage`. La création des objets ne déclenche pas d'appel réseau ; le fournisseur n'est appelé qu'après un POST valide.

### Tests

- `backend/tests/test_generation_service.py` vérifie `PENDING`, la sauvegarde d'image et le passage à `FAILED` avec un fournisseur de test qui renvoie uniquement une erreur.
- `backend/tests/test_local_storage.py` vérifie les noms UUID, les écritures et le refus d'un chemin malveillant. Son payload est explicitement du texte de test et pas un modèle.
- `backend/tests/test_models_api.py` vérifie HTTP 202, l'état d'échec après tâche de fond, le refus de téléchargement et les erreurs d'upload.
- `backend/tests/test_upload_validator.py` reste limité aux règles de fichier ; les tests de routes ont été déplacés vers `test_models_api.py` puisque le contrat de `POST /models` a évolué.

## Lancer et tester sous Windows PowerShell

Depuis `backend` :

    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

Essayer `POST /models` et `GET /models/{id}` dans `http://127.0.0.1:8000/docs`. Une erreur Hugging Face doit faire évoluer le suivi vers `FAILED`. Si le Space fonctionne, le modèle devient téléchargeable avec `GET /models/{id}/glb`.

Pour les tests locaux, dans un autre terminal :

    .\.venv\Scripts\python.exe -m pytest -q

Résultat vérifié sous Python 3.14.2 : 26 tests réussis. Cette suite ne fait aucun appel à Hugging Face. Le succès de génération `DONE` et une réponse de téléchargement 200 restent à vérifier dès qu'un fournisseur retourne un vrai GLB.

## Pourquoi cette conception et ses limites

- `BackgroundTasks` convient au prototype local et évite de bloquer la réponse d'upload ; pour une file durable à grande échelle, il faudra réévaluer l'architecture dans un sprint ultérieur.
- Le stockage local ne coûte rien et se remplace plus tard derrière `Storage` ; il ne convient pas à plusieurs instances backend qui partagent des fichiers.
- Le statut en mémoire est explicable et sans installation de base, mais il disparaît au redémarrage.
- Le serveur conserve les photos localement et n'a pas encore de route de suppression ni de politique d'expiration ; ne pas héberger d'images sensibles ni ouvrir ce backend au public.
- Cette étape ne garantit pas une génération réussie : le Space observé a échoué avec une exception interne générique.

# Sprint 1 — Étape 2 : valider l'upload

## Objectif et résultat

Recevoir une photo avec POST /models, n'accepter que les formats JPG, PNG et WebP, limiter sa taille à 10 Mo et expliquer les refus. Le résultat vérifiable est une réponse VALIDATED pour une signature reconnue, ou un code d'erreur et un message clair pour une entrée invalide.

Cette route ne conserve pas l'image et ne lance pas de génération. Son message le précise. Le stockage et la génération arrivent aux étapes suivantes.

Cette documentation décrit le jalon de l'étape 2. À l'étape 4, le même `POST /models` a été étendu : il conserve maintenant la photo localement, lance une tâche de fond et renvoie HTTP 202 avec un identifiant de suivi. Le contrat HTTP actuel est expliqué dans `docs/etapes/etape-04.md`.

## Fichiers de code

### backend/app/services/upload_validator.py

UploadValidator vérifie successivement que le contenu n'est pas vide, que sa taille reste sous la limite, que le nom de fichier est présent, que l'extension et le type MIME correspondent et que les premiers octets ont la signature attendue. Le nom est réduit au dernier segment pour ne pas renvoyer un chemin fourni par le navigateur. Les erreurs portent un code HTTP et un message.

La signature identifie le format du conteneur ; elle ne décode pas les pixels et ne certifie pas que tout le fichier est une image complète. Le prétraitement ou le fournisseur détectera d'autres corruptions éventuelles aux étapes suivantes.

### backend/app/schemas.py

UploadValidationResponse définit la réponse JSON : état VALIDATED, nom nettoyé, type reconnu, taille et message de transparence. Les limites de la taille sont aussi contraintes dans le schéma.

### backend/app/routers/models.py

La route POST /models lit au maximum 10 Mo plus un octet, appelle UploadValidator puis renvoie le schéma. L'octet supplémentaire permet de distinguer un fichier trop grand sans charger le reste en mémoire. Le fichier uploadé est fermé dans tous les cas. Une erreur de validation devient une réponse HTTP correspondante.

### backend/app/main.py

L'application branche le routeur models en plus de GET /health. Elle reste le point unique importé par Uvicorn.

### backend/tests/test_upload_validator.py

Les tests vérifient les signatures des trois formats, le nettoyage du nom, le fichier vide, l'extension inconnue, le MIME incohérent, la signature incorrecte, le dépassement de taille et les réponses HTTP de POST /models. Les corps de test sont des octets de fixture servant uniquement à vérifier les signatures, pas des sorties 3D.

## Configuration

backend/requirements.txt ajoute python-multipart, utilisé par FastAPI pour parser un formulaire multipart. Il n'ajoute pas de fournisseur 3D ni de bibliothèque de prétraitement.

## Lancer et tester sous PowerShell

Depuis backend, si l'environnement virtuel doit être créé sur le poste Python 3.14 actuel :

    python -m venv --without-pip .venv
    pip --python .venv\Scripts\python.exe install -r requirements.txt
    .\.venv\Scripts\python.exe -m pytest -q

Résultat vérifié : 12 tests réussis sous Python 3.14.2.

Pour lancer le serveur :

    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

POST /models attend un formulaire multipart avec le champ file. La documentation interactive à /docs permet d'essayer le contrat HTTP après lancement local.

## Pourquoi ces choix

- Contrôler signature, extension et MIME ensemble limite l'acceptation d'un mauvais format déclaré.
- Limiter la lecture à la taille maximale plus un octet garde le coût mémoire borné.
- Séparer route, schéma et validateur rend chaque décision explicable et testable.
- Une réponse de validation ne prétend pas que le fichier est stocké ou converti.
- La validation reste locale : les photos ne partent pas vers Hugging Face à cette étape.

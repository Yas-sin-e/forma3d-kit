# Étape 12 — Import de modèles GLB et bibliothèque unifiée

## But et livrable

Un vendeur peut enregistrer un modèle GLB déjà disponible sur son ordinateur, ou ajouter une copie d'un exemple, puis retrouver le modèle dans **Mes modèles** et ouvrir sa fiche. L'origine est persistée afin de distinguer un modèle généré depuis une photo, un import et un exemple copié.

Cette étape est un incrément isolé. Elle ne démarre pas le Sprint 5. Elle ne change ni le fournisseur image-vers-3D ni le modèle retenu.

## Parcours d'import

1. Dans `frontend/js/pages/models.js`, le vendeur ouvre le formulaire, choisit un fichier `.glb`, ajuste si besoin le titre automatiquement nettoyé, puis choisit une catégorie active chargée par `listCategories()`.
2. `frontend/js/api.js` envoie les champs à `POST /models/import`. Cette couche est l'unique point d'appel HTTP du frontend.
3. `backend/app/routers/models.py` lit au plus la limite configurée plus un octet, vérifie l'extension et traduit les erreurs en réponses HTTP claires.
4. `GenerationService.create_library_model()` contrôle la taille, le conteneur GLB 2.0 et la catégorie active. Le validateur partagé `DemoGallery.is_valid_glb_2()` vérifie l'en-tête, la taille déclarée, la version glTF et les limites des chunks.
5. `LocalStorage` choisit un UUID comme nom de fichier ; le nom fourni par le navigateur n'est jamais utilisé comme chemin. Le dépôt SQLite crée la fiche `DONE`, avec `origin=imported`, sans photo source et sans durée de génération.
6. `GET /models/gallery` relit cette fiche avec les autres modèles terminés. La carte affiche son titre, sa catégorie, sa date et « Importé » ; la fiche permet l'aperçu et le téléchargement.

## Copier un exemple

Sur **Exemples de modèles**, le bouton **Ajouter à mes modèles** demande une catégorie active. `POST /models/examples/{example_id}/copy` résout l'identifiant uniquement dans l'allowlist de `DemoGallery`, relit et valide le fichier, puis enregistre une copie avec un nouvel UUID et `origin=example`. L'exemple d'origine n'est jamais renommé ni remplacé.

## Persistance et limites d'upload

La colonne SQLite `origin` est ajoutée sans reconstruire la table ; les lignes antérieures reçoivent `generated`. La colonne historique `source_photo_path` reste non nulle : une valeur vide représente une absence de photo et est convertie en `None` dans le modèle Python.

`MAX_GLB_UPLOAD_MB` dans `.env.example` configure la limite en mégaoctets. La valeur par défaut est 30 Mo et la configuration accepte 1 à 512 Mo. Les réponses n'incluent aucun chemin local.

Les modèles sont conservés dans le stockage local partagé de cette instance, sans comptes utilisateurs. Les tests de cette étape utilisent des bases temporaires et un GLB minimal construit pour le test ; ils ne représentent pas une génération IA ni la validation visuelle d'un produit réel.

## Fichiers à connaître

- `backend/app/models.py` décrit l'origine et l'absence possible de photo.
- `backend/app/repositories/sqlite_repository.py` migre et relit les lignes SQLite.
- `backend/app/services/generation_service.py` porte les règles communes d'import et de copie.
- `backend/app/services/demo_gallery.py` garde l'allowlist d'exemples et le validateur GLB 2.0.
- `backend/app/storage/local_storage.py` crée les fichiers avec un identifiant aléatoire et sans écrasement.
- `backend/app/routers/models.py` expose l'import, la copie et la liste unifiée.
- `frontend/js/pages/models.js`, `frontend/js/pages/examples.js`, `frontend/js/pages/model-detail.js` et `frontend/js/views/gallery.js` affichent le parcours et la provenance.
- `backend/tests/test_model_library.py` vérifie les cas de réussite, erreurs, catégories, copie et migration.

## Vérifications et revue manuelle

- Tests ciblés : `backend/tests/test_model_library.py`, `test_demo_gallery.py`, `test_models_api.py`, `test_generation_repository.py`, `test_local_storage.py` et `test_frontend.py` — 31 réussis.
- Suite complète : `backend/tests` — 83 réussis. Les tests n'appellent pas le fournisseur 3D.
- Les modules JavaScript ont passé `node --check`; `git diff --check` est propre.
- À vérifier par l'étudiante dans le navigateur : sélection et titre par défaut d'un vrai GLB, catégories actives, import valide, message d'erreur pour un fichier invalide/trop gros, affichage de la carte et de son origine, ouverture de la fiche, aperçu et téléchargement, copie d'un exemple avec catégorie, état vide, navigation retour, et affichage mobile à 360 px.

## État

Le code et les vérifications automatiques sont terminés. Aucun import réel depuis un navigateur, contrôle visuel, fournisseur en ligne ou résultat GLB réel n'est revendiqué. La CI GitHub doit être vérifiée par son exécution distante.

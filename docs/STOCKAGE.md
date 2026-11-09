# Stockage local des modèles

## Décision

Les métadonnées de catégorie et de modèle restent dans SQLite, via `SQLiteGenerationRepository`. Les fichiers restent sous `backend/storage/`. SQLite est fourni par Python ; l'étape n'ajoute aucun serveur de base de données.

La base garde son chemin fixe `backend/data/forma3d.sqlite3`, ignoré par Git. Le plafond des imports est configurable séparément par `MAX_GLB_UPLOAD_MB` dans `.env.example` ; il vaut 30 Mo par défaut.

## Tables et origines

`categories` contient le slug, le libellé, l'état actif et la date de création. Les générations et modèles de bibliothèque référencent une catégorie par sa clé étrangère.

`generations` contient l'identifiant UUID, la catégorie, le statut, le nom d'affichage, le type de contenu, les chemins source/GLB, la durée, l'erreur, l'avertissement photo, les dates et l'origine. `origin` vaut `generated`, `imported` ou `example`.

La migration ajoute `origin` avec la valeur historique `generated` par défaut. Elle conserve les anciennes lignes et leurs chemins. `source_photo_path` reste non nul pour éviter de reconstruire la table SQLite : pour un modèle importé ou copié sans photo, le dépôt stocke une chaîne vide puis la convertit en `image_path=None` lors de la lecture. Cette convention évite une migration destructive.

Les cinq exemples restent un catalogue de fichiers autorisés, pas des lignes SQLite au premier démarrage. Le clic « Ajouter à mes modèles » copie l'exemple dans `backend/storage/models/`, crée une ligne terminée avec `origin=example` et la catégorie choisie.

## Parcours d'import

`POST /models/import` reçoit le GLB, son titre et une catégorie active. Le service vérifie l'extension, la taille configurée, l'en-tête et la structure GLB 2.0 avec le validateur commun à `DemoGallery`. Il nettoie le titre et ne reprend jamais le nom client comme chemin. `LocalStorage` crée le fichier sous un UUID aléatoire et refuse d'écraser un chemin existant.

`POST /models/examples/{example_id}/copy` ne résout qu'un identifiant de l'allowlist d'exemples, puis passe par la même validation métier et le même stockage. Les deux parcours créent un enregistrement `DONE` sans durée de génération et sans photo source. Un import n'est donc jamais présenté comme une conversion photo-vers-3D.

## Connexions et lecture de la bibliothèque

Chaque opération SQLite ouvre, utilise puis ferme sa propre connexion. C'est important car le traitement photo peut continuer dans une tâche de fond pendant que d'autres requêtes lisent l'historique ; aucune connexion ne traverse les threads ou un appel au fournisseur.

La route `GET /models/gallery`, dans `backend/app/routers/models.py`, rassemble les exemples autorisés et les modèles terminés du service. `GenerationService.list_completed_generations()` garde les entrées dont le GLB existe ; une photo source est exigée seulement pour les modèles `generated`, jamais pour `imported` ou `example`. La page Mes modèles ne retient que les identifiants UUID persistés, tandis que la page Exemples ne montre que le catalogue fixe. La fiche réutilise les routes d'état, GLB et photo source existantes.

Les badges visibles sont dérivés d'`origin` : « Généré par l'application », « Importé » et « Exemple ». Le champ historique `source` suit également la provenance afin d'éviter de présenter un import comme une génération.

## Vérifications et limites

`backend/tests/test_model_library.py` contrôle l'import valide, l'extension et le contenu incorrects, la taille maximale, les catégories absentes/inactives, la copie d'un exemple et la migration sans perte. `backend/tests/test_generation_repository.py` contrôle la persistance SQLite générale. Tous les cas utilisent des fichiers temporaires, des conteneurs GLB minimaux de test et des appels HTTP locaux ; aucun fichier test n'est un modèle réel généré par le fournisseur.

La liste locale n'est pas un compte multi-utilisateur : les modèles sont partagés dans le stockage local de cette instance. Aucune génération réelle, import depuis le navigateur, inspection visuelle ou vérification CI GitHub n'est déduite des tests automatiques.

# Stockage local des modèles

## Décision

Les métadonnées de catégorie et de modèle restent dans SQLite, via `SQLiteGenerationRepository`. Les fichiers restent sous `backend/storage/`. SQLite est fourni par Python ; l'étape n'ajoute aucun serveur de base de données.

La base garde son chemin fixe `backend/data/forma3d.sqlite3`, ignoré par Git. Les plafonds API `API_DAILY_GENERATION_LIMIT` (20 créations/jour) et `API_RATE_LIMIT_PER_MINUTE` (10 requêtes/minute), les origines CORS exactes `API_CORS_ORIGINS` et les origines autorisées à intégrer un viewer `EMBED_ALLOWED_ORIGINS` sont configurables dans `.env.example`. Les deux listes sont vides par défaut et refusent le joker `*`.

## Tables et origines

`categories` contient le slug, le libellé, l'état actif et la date de création. Les générations et modèles de bibliothèque référencent une catégorie par sa clé étrangère.

`generations` contient l'identifiant UUID interne, l'UUID public, l'activation d'intégration, la catégorie, le statut, le nom d'affichage, le type de contenu, les chemins source/GLB, la durée, l'erreur, l'avertissement photo, les dates et l'origine. `origin` vaut `generated`, `imported` ou `example` ; `embed_enabled` est faux par défaut.

La migration ajoute `origin` avec la valeur historique `generated` par défaut. Elle conserve les anciennes lignes et leurs chemins. `source_photo_path` reste non nul pour éviter de reconstruire la table SQLite : pour un modèle importé ou copié sans photo, le dépôt stocke une chaîne vide puis la convertit en `image_path=None` lors de la lecture. Cette convention évite une migration destructive.

`api_keys` conserve l'identifiant, le nom choisi, le préfixe lisible, l'empreinte SHA-256, la date de création et l'état de révocation. `api_usage_daily` compte atomiquement les créations pour chaque clé et journée UTC ; `api_rate_events` conserve les horodatages récents qui servent à la fenêtre glissante de débit. Les deux tables référencent `api_keys` et ne contiennent aucune valeur secrète. La clé complète n'est jamais stockée : elle est retournée uniquement par la réponse de création et doit être copiée à ce moment-là. La révocation garde la trace administrative, mais empêche immédiatement l'authentification.

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

Les compteurs de quota et de débit sont persistants : une relance du serveur ne remet pas les limites à zéro. Les événements de débit plus anciens que 60 secondes sont nettoyés lorsqu'une nouvelle requête est acceptée. La liste locale n'est pas un compte multi-utilisateur : les modèles sont partagés dans le stockage local de cette instance. Les clés protègent les routes versionnées `/api/v1` via `require_api_key` et une limite de débit par clé ; le quota quotidien ne s'applique qu'aux créations valides de modèles. La console de gestion du Studio n'a pas d'authentification et reste réservée à un usage local ou de démonstration. Aucune génération réelle, import depuis le navigateur, inspection visuelle ou vérification CI GitHub n'est déduite des tests automatiques.

## Intégration sur un site tiers

Un modèle public n'est consultable qu'après activation explicite depuis sa fiche. `/embed/{public_id}` vérifie qu'il est terminé, activé et que son GLB est disponible ; sinon la réponse est 404. La page ne révèle ni nom de chemin local, ni clé API, ni donnée de la photo source. Le widget `frontend/widget.js` crée une iframe et laisse le rendu 3D isolé du site marchand. Le code d'intégration est fourni par `/api/v1/models/{id}/integration-code` et affiché sur la fiche dans le Studio.

La réponse CSP définit `frame-ancestors 'self'` et ajoute uniquement les origines HTTP(S) exactes de `EMBED_ALLOWED_ORIGINS`. Une liste vide signifie qu'un site d'une autre origine ne pourra pas encadrer le viewer. CORS (`API_CORS_ORIGINS`) est un réglage distinct : il autorise les requêtes JavaScript vers l'API, tandis que `EMBED_ALLOWED_ORIGINS` autorise l'inclusion de la page viewer dans une iframe. Aucune des deux listes ne permet `*`.

Le guide `docs/INTEGRATION.md` accompagne ce schéma avec des appels `curl`, les statuts, les erreurs et les limites de quota. La page `examples/integration.html` ne modifie pas SQLite : elle ne fait qu'insérer le composant `<forma3d-viewer>` à partir d'un UUID public choisi. Aucun identifiant ou GLB de démonstration n'est prérempli.

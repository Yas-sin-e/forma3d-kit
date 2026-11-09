# Stockage local des générations

## Choix retenu

Les métadonnées de l'application sont conservées dans `backend/data/forma3d.sqlite3`. Le chemin est fixe dans `backend/app/main.py` : il n'y a donc pas de variable de configuration à ajouter dans `config.py` ou `.env.example`. Le dossier `backend/data/` et les extensions SQLite sont ignorés par Git. Les photos sources et les fichiers GLB restent dans le stockage local existant, sous `backend/storage/`.

Cette base SQLite locale ne nécessite ni service distant, ni abonnement, ni nouvelle dépendance Python. Elle est adaptée au prototype exécuté sur une seule machine. Elle n'apporte pas de réplication ni de sauvegarde automatique ; les fichiers locaux doivent être sauvegardés séparément si l'historique doit être conservé.

## Tables

`categories` contient `id`, `slug` unique, `label`, `is_active` et `created_at`. Au premier démarrage, le dépôt insère `chair` / « Chaise », `stool` / « Tabouret » et `side-table` / « Table d’appoint » si ces catégories n'existent pas. Les conflits de slug sont ignorés pour préserver les catégories existantes.

`generations` contient l'identifiant, la catégorie liée, l'état, le nom et le type du fichier source, les chemins locaux de la photo et du GLB, la durée, le message d'erreur, ainsi que les dates de création et de mise à jour. Les champs `filename`, `content_type` et `updated_at` complètent les données métier demandées afin de reconstruire les réponses API actuelles sans changer leur contrat. Le statut est limité à `PENDING`, `RUNNING`, `DONE` ou `FAILED`.

La base stocke les chemins et métadonnées, pas les octets des images ou des modèles. Le stockage de fichiers reste donc distinct de l'historique relationnel.

## Dépôt et connexions

`backend/app/repositories/base.py` définit le contrat `GenerationRepository`. `backend/app/repositories/sqlite_repository.py` l'implémente avec le module standard `sqlite3`. `GenerationService` dépend de l'interface et n'a pas besoin de connaître les requêtes SQL.

Chaque opération du dépôt ouvre sa propre connexion SQLite, effectue sa lecture ou transaction, puis la ferme. Le fournisseur 3D s'exécute comme tâche de fond et peut prendre plusieurs minutes. Une connexion conservée et partagée entre requêtes ou threads risquerait d'être utilisée depuis un autre thread ; les connexions courtes isolent les opérations et évitent de partager un objet SQLite entre le thread HTTP et la tâche de génération. Le travail distant ne garde aucune transaction SQLite ouverte.

## Redémarrage et galerie

À l'initialisation du dépôt au démarrage, les lignes restées `PENDING` ou `RUNNING` sont passées à `FAILED`, avec le message « Génération interrompue au redémarrage du serveur. » Cela reflète le fait qu'une tâche Python en mémoire ne reprend pas après l'arrêt du processus ; aucune génération interrompue n'est annoncée comme réussie.

La galerie est assemblée par `backend/app/routers/models.py`, dans la route `GET /models/gallery`. Cette route garde les modèles de démonstration autorisés puis demande à `GenerationService.list_completed_generations()` les productions de l'application. Le service lit le dépôt SQLite et ne retourne que les entrées `DONE` dont le GLB et la photo source existent encore. L'API et le viewer gardent leur format et leurs interactions.

## Vérification et limites

`backend/tests/test_generation_repository.py` utilise une base temporaire et un fournisseur simulé local. Il vérifie les catégories initiales, l'ouverture d'une nouvelle connexion par opération, la récupération d'une génération terminée par un nouveau dépôt/service, et l'échec des travaux interrompus. Le GLB minimal du test sert uniquement à tester le cycle de persistance : ce n'est pas un résultat de génération ni un modèle de démonstration.

La persistance concerne les données écrites après l'introduction de SQLite. Les anciennes entrées qui n'existaient qu'en mémoire avant le changement ne peuvent pas être récupérées automatiquement. La base locale et les fichiers `backend/storage/` sont ignorés par Git et ne sont pas partagés entre clones.

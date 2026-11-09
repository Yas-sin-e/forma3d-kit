# Étape 8 — SQLite et historique persistant

## Objectif et livrable

Conserver les catégories et les métadonnées de génération après le redémarrage du backend, tout en gardant le contrat API et le viewer existants. Le livrable vérifiable est une entrée `DONE` relue par un nouveau service après redémarrage, et une récupération correcte des tâches `PENDING` ou `RUNNING` interrompues.

## Fichiers et responsabilités

- `backend/app/repositories/base.py` définit l'interface de dépôt utilisée par la logique métier.
- `backend/app/repositories/sqlite_repository.py` crée les tables, insère les catégories initiales, lit/écrit les générations et transforme en échec les travaux périmés.
- `backend/app/repositories/__init__.py` marque le paquet Python des dépôts.
- `backend/app/models.py` représente aussi la durée mesurée d'une génération terminée.
- `backend/app/services/generation_service.py` orchestre les états et délègue désormais la persistance au dépôt.
- `backend/app/main.py` sélectionne `backend/data/forma3d.sqlite3` et initialise le schéma au démarrage.
- `backend/tests/test_generation_repository.py` vérifie le schéma, les catégories par défaut, les connexions indépendantes, la persistance après redémarrage et la fermeture des tâches interrompues.
- `backend/tests/test_generation_service.py` et `backend/tests/test_models_api.py` construisent leurs dépôts temporaires pour isoler chaque test.
- `docs/STOCKAGE.md` explique le schéma, les connexions et le parcours de lecture de la galerie.
- `docs/STRUCTURE.md` et `docs/ETAT.md` décrivent l'organisation et les preuves de cette étape.

## Pourquoi SQLite et une interface de dépôt

`sqlite3` fait partie de Python, fonctionne hors ligne et ne demande aucun service ni dépendance additionnelle. Le service de génération connaît le contrat `GenerationRepository`, pas SQLite ; cette séparation garde l'accès aux données remplaçable et testable.

Chaque opération ouvre et ferme sa connexion. La génération se déroule en arrière-plan et ne doit pas partager une connexion SQLite avec le thread des requêtes HTTP. Les opérations de base restent courtes ; aucune connexion ni transaction ne reste ouverte pendant l'appel au fournisseur.

Le chemin de la base est fixe : `backend/data/forma3d.sqlite3`. Il n'y a pas de paramètre dans `config.py` ni de variable à ajouter à `.env.example`. `.gitignore` exclut `backend/data/`, `*.db`, `*.sqlite` et `*.sqlite3`.

## Parcours de la galerie

Le navigateur appelle toujours `GET /models/gallery`. `backend/app/routers/models.py` combine la galerie de démonstration avec `GenerationService.list_completed_generations()`. Le service interroge `GenerationRepository.list_completed_generations()` ; l'adaptateur SQLite renvoie les lignes `DONE`, puis le service filtre celles dont les fichiers GLB et photo source sont encore présents. La réponse et le viewer ne changent pas.

## Redémarrage et erreurs

À chaque initialisation, les travaux restés `PENDING` ou `RUNNING` deviennent `FAILED` avec le message « Génération interrompue au redémarrage du serveur. » Une génération de fond n'est pas reprise, car le fournisseur et sa tâche Python ne survivent pas à l'arrêt du processus.

## Vérification

Commande complète : `backend/.venv/Scripts/python.exe -m pytest backend/tests` depuis la racine du dépôt. Les tests utilisent une base dans le dossier temporaire de pytest ; ils n'appellent aucun réseau ni fournisseur réel. Un GLB minimal construit dans le test sert à vérifier le stockage et la relecture, pas à prouver une génération 3D.

Le test de redémarrage crée une génération avec le fournisseur de test, la termine, construit un nouveau dépôt et un nouveau `GenerationService` sur le même fichier SQLite, puis vérifie l'état, la catégorie, la photo, le modèle et la présence de l'entrée dans la galerie métier.

Résultat de vérification : 61 tests ont réussi en 2,52 s. Dans le navigateur intégré, l'application locale a indiqué le fournisseur non configuré et désactivé le bouton de création ; les cinq modèles réels de démonstration étaient listés. La sélection de « Chaise en bois cintré » a ouvert le viewer avec sa photo source et le lien de téléchargement. Cette vérification n'a déclenché aucune génération. Microsoft Edge n'a pas pu être piloté ; cette session a été vérifiée dans le navigateur intégré.

## Limites

La base est locale à une installation et n'offre pas de sauvegarde distante, de réplication ou de synchronisation. Les médias sont toujours dans `backend/storage/`. Les générations uniquement en mémoire avant cette étape ne sont pas migrées. Le CRUD des catégories et la préparation d'image restent les étapes 9 et 10 ; aucune de ces fonctions n'est commencée ici.

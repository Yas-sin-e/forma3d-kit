# Forma3D Studio

Forma3D Studio transforme la photo d’un petit meuble en modèle 3D GLB, puis l’affiche dans un viewer interactif. Le périmètre du MVP vise le tabouret, la chaise et la table d’appoint.

## Contraintes du projet

- Gratuit : aucune API payante, carte bancaire ou abonnement.
- Sans entraînement : modèles image-vers-3D pré-entraînés uniquement.
- Transparence : signaler les limites des fournisseurs gratuits et étiqueter tout modèle pré-généré.
- Compréhension : expliquer les fichiers et décisions dans la documentation.

## État

L’étape 2 prépare la structure du dépôt et une vérification documentaire sur GitHub Actions. Aucun backend ou frontend applicatif n’est encore implémenté. Les étapes 4 et 8 introduiront respectivement l’API et l’interface.

## Structure

- .github/workflows/ci.yml : contrôle des documents requis à chaque push et pull request.
- backend/README.md : rôle prévu du backend avant son implémentation à l’étape 4.
- frontend/README.md : rôle prévu du frontend avant son implémentation à l’étape 8.
- docs/ : état du projet et guides des étapes.
- AGENTS.md : contraintes et méthode de travail.
- PRODUCT.md : périmètre et critères d’acceptation.
- DESIGN.md : fondations visuelles.

## Stack prévue

Frontend : Next.js, TypeScript, Tailwind, React Three Fiber, drei et Zustand.

Backend : FastAPI, SQLAlchemy et SQLite au départ. Prétraitement avec OpenCV et rembg ; nettoyage de maillage avec trimesh.

Le stockage local sera isolé derrière une interface. Celery, Redis et MinIO ne font pas partie du MVP.

## Commandes

Les commandes de lancement seront ajoutées lorsque les applications existeront : backend à l’étape 4 et frontend à l’étape 8. Cette étape ne contient pas encore de serveur à lancer.

## Vérifications

La CI vérifie que les documents de projet requis existent. Elle ne prétend pas exécuter des tests backend ou frontend avant l’ajout de ces applications.

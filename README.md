# Forma3D Studio

Forma3D Studio est un module 3D intégrable dans tout site : son API expose des modèles avec une clé et son widget affiche les modèles activés. Le Studio est la console privée mono-propriétaire ; aucun catalogue public n'est prévu.

## Contraintes

- Gratuit : aucun fournisseur payant, aucune carte bancaire et aucun abonnement.
- Sans entraînement : uniquement des modèles pré-entraînés.
- Transparent : expliquer les quotas des fournisseurs gratuits et étiqueter les modèles pré-générés.
- Compréhensible : chaque fichier et dossier est expliqué dans docs/STRUCTURE.md.

## État actuel

À l'étape 6, l'API Forma3D a produit cinq GLB réels avec le serveur TripoSR officiel. Ces résultats restent locaux dans `backend/data/feasibility-results/`. La session Colab suivante a répondu « Échec : backend non attribué » le 1 novembre 2026. En outre, la FAQ Colab restreint les serveurs web de génération sur ses runtimes gérés gratuits ; cette intégration n'est pas présentée comme disponible ou garantie.

L'étape 7 ajoute `/health/provider`, un badge de disponibilité, une solution de démonstration hors ligne, les conseils photo et la comparaison avec la photo source. La page ne permet de lancer une génération que si le fournisseur répond. Les photos libres et les modèles démo restent des fichiers locaux ignorés par Git.

Le frontend reste sans framework : CSS et JavaScript séparés en modules, sans serveur de développement ni build. La palette sombre, les tailles de texte et les composants sont définis dans DESIGN.md. Les étapes techniques, les mesures des cinq essais et leurs limites sont documentées dans docs/ETAT.md.

Le Sprint 1 a établi le trajet photo vers GLB, viewer et téléchargement, avec essais sur petit mobilier opaque. Les limites et résultats historiques sont décrits dans docs/ETAT.md. Les Sprints 3 (comptes) et 4 (vitrine) sont retirés. Le Sprint 5, validé le 10 novembre 2026, construit l'API et le widget intégrables ; le Sprint 6 attend un OK explicite.

## Démarrer en une commande (Docker)

Prérequis : Docker Desktop avec intégration WSL2 (ou Docker Engine + Compose v2), port 8080 libre.

```bash
cp .env.compose.example .env.compose
docker compose up -d --build
```

Puis ouvrir http://localhost:8080 (mot de passe fictif du Studio : celui de `.env.compose`). La pile
contient l'API et une base PostgreSQL 17 dans un conteneur séparé, avec des données conservées dans des
volumes. `docker compose down` arrête sans effacer ; `docker compose down -v` efface les données.
PostgreSQL est la seule base de données. `scripts/dev.ps1` démarre lui-même le conteneur PostgreSQL (Docker Desktop requis) puis lance les tests et le serveur en local.

Chaîne DevOps (contrôle, image, Compose, CI, release GHCR, staging, rollback) : voir
[docs/devops/README.md](docs/devops/README.md) et la fiche d'une page
[docs/devops/FICHE-PROJET.md](docs/devops/FICHE-PROJET.md).

## Répertoires et documents

- backend/app : application FastAPI, validation, service de génération, fournisseur, stockage et catalogue limité de modèles de démonstration.
- backend/tests : vérifications automatisées du backend sans appels à Hugging Face.
- frontend : page du Sprint 1, thème, composants et vues JavaScript servis par FastAPI.
- docs : état, structure et explications de chaque étape.
- tools/colab/triposr_server.ipynb : notebook de vérification et d'installation pédagogique ; sa cellule de serveur s'arrête pour respecter les restrictions actuelles de Colab géré gratuit.
- scripts/dev.ps1 : prépare le venv, lance pytest, démarre Uvicorn en arrière-plan et ouvre Edge.
- docs/archive/v1 : historique de l'ancienne vision, conservé sans être la référence active.
- .github/workflows : vérifications automatiques sur GitHub.
- PRODUCT.md définit vision, périmètre et limites ; DESIGN.md fixe les règles visuelles ; AGENTS.md décrit les contraintes et le cycle de travail.

## Installation et commandes — PowerShell Windows

Depuis la racine du dépôt :

    cd backend
    python -m venv --without-pip .venv
    pip --python .venv\Scripts\python.exe install -r requirements.txt
    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

Ouvrez http://127.0.0.1:8000/ pour le studio. La santé de l'API se vérifie sur http://127.0.0.1:8000/health et sa documentation interactive sur http://127.0.0.1:8000/docs.

Ou lancez le script de développement depuis la racine du dépôt :

    .\scripts\dev.ps1

Il exécute d'abord pytest, démarre l'API puis ouvre Edge sur le studio. L'état du fournisseur est vérifiable sur `/health/provider` ; `/health` ne teste que l'API locale.

Pour lancer les tests manuellement dans un second terminal :

    cd backend
    .\.venv\Scripts\python.exe -m pytest -q

Les tests n'appellent pas Hugging Face afin de préserver le quota. La galerie est alimentée par backend/data/feasibility-results/, un dossier local ignoré par Git. Sans ces fichiers, la page indique qu'aucun modèle réel n'est disponible.

Sur le poste utilisé pour ce projet, Python 3.14 installé ne fournit pas ensurepip. Le venv est donc créé sans pip, puis le pip déjà disponible installe les dépendances uniquement dans le venv grâce à l'option --python.

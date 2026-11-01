# Forma3D Studio

Forma3D Studio est un SaaS 3D pour le commerce en ligne : le vendeur envoie une photo de produit, obtient un modèle GLB interactif et pourra l'intégrer dans sa boutique. Le produit complet prévoit un service de génération, un widget intégrable et une boutique de démonstration.

## Contraintes

- Gratuit : aucun fournisseur payant, aucune carte bancaire et aucun abonnement.
- Sans entraînement : uniquement des modèles pré-entraînés.
- Transparent : expliquer les quotas des fournisseurs gratuits et étiqueter les modèles pré-générés.
- Compréhensible : chaque fichier et dossier est expliqué dans docs/STRUCTURE.md.

## État actuel

Le Sprint 1 a produit cinq GLB réels avec l'API Forma3D connectée au serveur TripoSR officiel sur Google Colab. La page de génération affiche les états de l'API, puis le GLB validé dans un viewer interactif. La galerie recense seulement les cinq fichiers locaux autorisés et les filtre par catégorie. Aucun résultat n'est simulé.

Le frontend reste sans framework : CSS et JavaScript séparés en modules, sans serveur de développement ni build. La palette sombre, les tailles de texte et les composants sont définis dans DESIGN.md. Les étapes techniques, les mesures des cinq essais et leurs limites sont documentées dans docs/ETAT.md.

Le Sprint 1 se concentre sur le trajet photo vers GLB, viewer et téléchargement, en commençant par le petit mobilier opaque : tabouret, chaise et table d'appoint. Les notes qualitatives bon/moyen/mauvais des cinq résultats restent à donner par l'étudiante après examen. Le guide Colab est dans docs/etapes/etape-06-colab.md. Les comptes vendeurs, la boutique vitrine et le widget distribuable relèvent des sprints suivants.

## Répertoires et documents

- backend/app : application FastAPI, validation, service de génération, fournisseur, stockage et catalogue limité de modèles de démonstration.
- backend/tests : vérifications automatisées du backend sans appels à Hugging Face.
- frontend : page du Sprint 1, thème, composants et vues JavaScript servis par FastAPI.
- docs : état, structure et explications de chaque étape.
- tools/colab/triposr_server.ipynb : notebook Colab de démarrage du serveur TripoSR sur un runtime GPU temporaire.
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

Dans un second terminal :

    cd backend
    .\.venv\Scripts\python.exe -m pytest -q

Les tests n'appellent pas Hugging Face afin de préserver le quota. La galerie est alimentée par backend/data/feasibility-results/, un dossier local ignoré par Git. Sans ces fichiers, la page indique qu'aucun modèle réel n'est disponible.

Sur le poste utilisé pour ce projet, Python 3.14 installé ne fournit pas ensurepip. Le venv est donc créé sans pip, puis le pip déjà disponible installe les dépendances uniquement dans le venv grâce à l'option --python.

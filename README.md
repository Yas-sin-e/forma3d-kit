# Forma3D Studio

Forma3D Studio est un SaaS 3D pour le commerce en ligne : le vendeur envoie une photo de produit, obtient un modèle GLB interactif et pourra l'intégrer dans sa boutique. Le produit complet prévoit un service de génération, un widget intégrable et une boutique de démonstration.

## Contraintes
- Gratuit : aucun fournisseur payant, aucune carte bancaire et aucun abonnement.
- Sans entraînement : uniquement des modèles pré-entraînés.
- Transparent : expliquer les quotas des fournisseurs gratuits et étiqueter les modèles pré-générés.
- Compréhensible : chaque fichier et dossier est expliqué dans docs/STRUCTURE.md.

## État actuel
Sprint 1 : les fondations, la validation, le fournisseur Stable Fast 3D, le service de suivi, le stockage local et la page viewer sont implémentés. Cinq photos libres ont échoué sur le Space Stable Fast 3D ; le Space officiel TripoSR était en `RUNTIME_ERROR` avant l'inspection de son API. Aucun GLB réel n'a été obtenu. Le viewer permet maintenant d'ouvrir un GLB choisi localement, marqué comme non généré par l'application, mais son affichage et ses contrôles restent à vérifier avec un vrai modèle. Consultez `docs/ETAT.md` avant de présenter la faisabilité.

Le Sprint 1 se concentre sur le trajet essentiel photo vers GLB, viewer et téléchargement, en commençant par le petit mobilier opaque : tabouret, chaise et table d'appoint. L'étape 6 prépare un serveur TripoSR exécuté par l'étudiante sur Colab ; son URL, l'inspection live de l'API et une génération réelle sont encore attendues. Aucun GLB réel n'a été obtenu. Le mode d'emploi est dans docs/etapes/etape-06-colab.md. Les comptes vendeurs, la boutique vitrine et le widget distribuable relèvent des sprints suivants.

## Répertoires et documents
- backend/app : application FastAPI, validation, service de génération, fournisseur et stockage local.
- backend/tests : vérifications automatisées du backend sans appels à Hugging Face.
- frontend : page HTML du Sprint 1 servie par FastAPI, sans Next.js.
- docs : état, structure et explications de chaque étape.
- tools/colab/triposr_server.ipynb : notebook Colab de démarrage du serveur TripoSR, à exécuter sur un runtime GPU temporaire.
- docs/archive/v1 : historique de l'ancienne vision, conservé sans être la référence active.
- .github/workflows : vérifications automatiques sur GitHub.
- PRODUCT.md définit vision, périmètre et limites ; DESIGN.md fixe les règles visuelles ; AGENTS.md décrit les contraintes et le cycle de travail.

## Installation et commandes — PowerShell Windows
Depuis la racine du dépôt :

    cd backend
    python -m venv --without-pip .venv
    pip --python .venv\Scripts\python.exe install -r requirements.txt
    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

Ouvrez http://127.0.0.1:8000/ pour la page de génération. http://127.0.0.1:8000/health doit répondre avec le statut ok. La documentation interactive est sur http://127.0.0.1:8000/docs.

Dans un second terminal :

    cd backend
    .\.venv\Scripts\python.exe -m pytest -q

Résultat attendu : les tests automatisés du backend réussissent. Ils n'appellent pas Hugging Face afin d'éviter de consommer le quota en CI.

Sur le poste utilisé pour ce projet, le Python 3.14 installé ne fournit pas ensurepip. La première commande crée donc le venv sans pip, puis le pip déjà disponible sur le poste installe les dépendances uniquement dans ce venv grâce à l'option --python.

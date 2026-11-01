# Frontend

Cette interface française de Sprint 1 est servie par FastAPI. Elle n'a ni framework, ni serveur de développement distinct, ni étape de compilation. La structure en modules sépare les styles, les appels HTTP, l'état de session et les vues afin que chaque fichier ait un rôle facile à expliquer.

## Parcours

1. La personne choisit ou dépose une photo JPG, PNG ou WebP de 10 Mo maximum.
2. L'interface rappelle de ne pas envoyer de visages ni de données personnelles.
3. Le navigateur envoie réellement la photo à POST /models et suit l'URL renvoyée par le serveur.
4. L'interface reflète les réponses PENDING, RUNNING, DONE ou FAILED. Elle montre le temps écoulé réellement mesuré, sans pourcentage.
5. À DONE, le GLB validé par le fournisseur apparaît dans le viewer et le bouton de téléchargement est révélé.
6. La galerie récupère seulement les cinq noms de fichiers de faisabilité autorisés. Les modèles absents ou invalides sont exclus. Les filtres portent sur la chaise, le tabouret et la table d'appoint.
7. « Ouvrir un GLB local » charge le fichier dans le navigateur, sans le transmettre au serveur ; son origine est affichée comme importée manuellement.

## Structure et responsabilités

- css/theme.css définit la palette sombre, la typographie système, les tailles minimales, le focus et la réduction des animations.
- css/components.css contient la mise en page et les styles des panneaux, du suivi, du viewer, de la galerie et des états.
- js/api.js est le seul module qui appelle les routes HTTP.
- js/state.js conserve l'état transitoire du formulaire et du suivi, sans base de données.
- js/views/uploader.js gère le choix, le dépôt et la validation visuelle du fichier avant la vérification serveur.
- js/views/progress.js montre les phases connues, le délai réellement écoulé et les erreurs.
- js/views/viewer.js charge model-viewer, ses commandes de caméra et les modèles GLB locaux ou générés.
- js/views/gallery.js présente et filtre les vrais fichiers renvoyés par l'API.
- js/main.js relie les vues et les appels d'API sans contenir d'appel HTTP.
- index.html expose la structure HTML et charge model-viewer 4.4.0 ainsi que les deux feuilles de style et le module principal.

Les commentaires d'en-tête de chaque module donnent son rôle et son exécution. La table de docs/STRUCTURE.md complète ces descriptions.

## Lancer

Depuis le dossier backend, lancer Uvicorn puis ouvrir http://127.0.0.1:8000/. La page, les feuilles de style et les modules JavaScript sont servis par la même application. Le navigateur a besoin d'Internet pour récupérer model-viewer depuis le CDN Google.

Le parcours de génération requiert aussi que le fournisseur distant soit disponible. La galerie dépend des cinq fichiers locaux de backend/data/feasibility-results/ ; elle n'invente pas de modèle si ces fichiers ne sont pas présents.

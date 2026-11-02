# Frontend

Cette interface française de Sprint 1 est servie par FastAPI. Elle n'a ni framework, ni serveur de développement distinct, ni étape de compilation. La structure en modules sépare les styles, les appels HTTP, l'état de session et les vues afin que chaque fichier ait un rôle facile à expliquer.

## Parcours

1. La personne choisit ou dépose une photo JPG, PNG ou WebP de 10 Mo maximum.
2. L'interface rappelle de ne pas envoyer de visages ni de données personnelles.
3. Le navigateur envoie réellement la photo à POST /models et suit l'URL renvoyée par le serveur.
4. L'interface reflète les réponses PENDING, RUNNING, DONE ou FAILED. Elle montre le temps écoulé réellement mesuré, sans pourcentage.
5. À DONE, le GLB validé par le fournisseur apparaît dans le viewer et le bouton de téléchargement est révélé.
6. La galerie combine les cinq GLB de faisabilité dont les identifiants sont autorisés et les générations réussies de la session backend. Les fichiers absents ou invalides sont exclus. Chaque nouvel envoi exige une catégorie ; le modèle et sa photo source apparaissent sous le filtre choisi.
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

Depuis la racine du projet, lancer `.\scripts\dev.ps1` ; le script vérifie les tests, démarre Uvicorn et ouvre Edge. Pour choisir un port, utiliser `.\scripts\dev.ps1 -Port 8003`. La page, les feuilles de style et les modules JavaScript sont servis par la même application. Le navigateur a besoin d'Internet pour récupérer model-viewer depuis le CDN Google.

Le parcours de génération requiert aussi que le fournisseur distant soit disponible ; vérifier `/health/provider` avant d'envoyer une photo. Si le statut est `OFFLINE`, relancer le notebook Colab pour une session personnelle acceptée, puis inscrire son nouveau lien uniquement dans `backend/.env` et relancer le serveur. La galerie garde les cinq modèles locaux valides et ajoute les générations récentes terminées ; l'historique des envois est en mémoire et repart au redémarrage du backend.

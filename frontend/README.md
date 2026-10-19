# Frontend

`index.html` contient la page française du Sprint 1 : choix de photo, suivi d'une demande réelle, viewer `<model-viewer>`, contrôles de caméra et téléchargement du GLB quand le backend indique `DONE`. Le bouton « Ouvrir un GLB local » charge aussi un fichier `.glb` sélectionné dans le navigateur, sans l'envoyer au serveur ; l'interface le marque comme un fichier non généré par l'application.

FastAPI sert cette page sur `/`. Il n'y a pas de serveur frontend séparé ni de compilation JavaScript. La page suit `DESIGN.md` ; son composant `<model-viewer>` est chargé depuis le CDN Google et nécessite une connexion Internet dans le navigateur. Les contrôles natifs `camera-controls` permettent aussi d'interagir directement avec la souris ou le tactile.

La page commence avec un état vide honnête et ne contient aucun modèle d'exemple. Les erreurs de génération restent visibles. Un GLB chargé localement sert à vérifier le viewer sans appeler le backend ; aucun fichier réel n'était disponible dans `backend/data/feasibility-results/` au moment de la dernière vérification, donc la caméra reste à valider avec un GLB réel.

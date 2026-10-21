# Frontend

`index.html` contient la page française du Sprint 1 : choix de photo, suivi d'une demande réelle, viewer `<model-viewer>`, contrôles de caméra et téléchargement du GLB quand le backend indique `DONE`. Le bouton « Ouvrir un GLB local » charge aussi un fichier `.glb` sélectionné dans le navigateur, sans l'envoyer au serveur ; l'interface le marque comme un fichier non généré par l'application.

FastAPI sert cette page sur `/`. Il n'y a pas de serveur frontend séparé ni de compilation JavaScript. La page suit `DESIGN.md` ; son composant `<model-viewer>` est chargé depuis le CDN Google et nécessite une connexion Internet dans le navigateur. Les contrôles natifs `camera-controls` permettent aussi d'interagir directement avec la souris ou le tactile.

La page démarre dans un état vide, sans modèle d'exemple. Les erreurs de génération restent visibles. Un GLB chargé avec le bouton local est identifié comme fichier local, non généré par l'application. Cinq GLB réels générés par Forma3D sont disponibles localement dans backend/data/feasibility-results/ ; le viewer a déjà affiché un modèle et ses contrôles ont été manipulés sur une génération réelle à faible résolution. Les cinq sorties aux paramètres TripoSR normaux doivent encore être examinées visuellement.

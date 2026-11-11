# Sprint 1 — Étape 5 : interface modulaire et viewer professionnel

## Objectif et livrable vérifiable

Donner à la propriétaire une page sombre et lisible pour transmettre une photo, suivre les états réels du backend, examiner un GLB dans un viewer interactif et télécharger le résultat. La même page permet d'ouvrir des modèles de faisabilité présents sur ce poste et de les distinguer d'un résultat venant de la génération courante.

La structure est organisée en modules sans framework. Les appels HTTP du navigateur sont centralisés dans frontend/js/api.js ; les vues du formulaire, du suivi, du viewer et de la galerie restent séparées. FastAPI sert la page et ces ressources sur la même origine.

## Fichiers frontend

- frontend/index.html contient la sémantique de page, les noms accessibles, les points de montage et les libellés. Il charge model-viewer 4.4.0 depuis le CDN Google, puis le module principal.
- frontend/css/theme.css définit le thème sombre, les tailles globales, le focus clavier et prefers-reduced-motion.
- frontend/css/components.css met en page le studio, ses panneaux, les indicateurs, le viewer, les filtres et les cartes réelles.
- frontend/js/api.js est le seul fichier JavaScript qui appelle l'API avec fetch. Il crée la demande de génération, lit son état et demande la galerie.
- frontend/js/state.js garde en mémoire le fichier sélectionné, le statut courant, le temps écoulé et les minuteries du navigateur.
- frontend/js/views/uploader.js gère le dépôt de photo et vérifie localement les extensions, MIME connus et la limite de 10 Mo avant l'envoi ; le backend refait sa validation.
- frontend/js/views/progress.js traduit SENDING (activité navigateur), PENDING, RUNNING, DONE et FAILED en libellés et étapes. L'indicateur est indéterminé ; aucun pourcentage n'est présenté.
- frontend/js/views/viewer.js charge les modèles, libère les URL blob locales, règle les commandes de caméra et n'affiche la réalité augmentée que si model-viewer indique que l'appareil la prend en charge.
- frontend/js/views/gallery.js affiche les modèles renvoyés par l'API, filtre leurs catégories et rend de vrais aperçus 3D, sans image ou objet fictif.
- frontend/js/main.js relie les vues, suit l'URL renvoyée par l'API et relance une demande échouée avec la même photo si l'étudiante le souhaite.

## Galerie de faisabilité et routes backend

- backend/app/services/demo_gallery.py contient une liste fixe de cinq identifiants/fichiers. Il vérifie que le nom est autorisé et que l'en-tête, le chunk JSON et les chunks restants forment un GLB 2.0.
- backend/app/schemas.py décrit le JSON de la galerie.
- backend/app/routers/models.py expose GET /models/gallery pour lister les fichiers réels et GET /models/gallery/{model_id} pour servir seulement un modèle autorisé.
- backend/app/main.py configure le catalogue et expose les ressources du dossier frontend sous /static/.
- backend/tests/test_demo_gallery.py vérifie les fichiers autorisés, le filtrage d'un fichier invalide, le refus d'un identifiant inconnu et le téléchargement.
- backend/tests/test_frontend.py vérifie les modules servis, la centralisation des appels HTTP et le fait qu'un GLB local ne part pas vers le serveur.

Les cinq résultats apparaissent uniquement quand ils sont présents et valides dans backend/data/feasibility-results/. Ils sont étiquetés « Généré par l’application · modèle d’essai » parce qu'ils ont été créés lors de la faisabilité, pas pendant la génération nouvellement soumise. Un fichier ouvert depuis l'ordinateur porte l'étiquette « Importé manuellement » et reste dans le navigateur.

## Suivi honnête

- Pendant l'envoi, l'interface mesure le temps réel en secondes.
- PENDING signifie que le serveur a accepté et mis la demande en file ; RUNNING signifie que le fournisseur traite l'image.
- Le fournisseur valide le conteneur GLB 2.0 avant de publier DONE. La page ne marque « Validation du GLB » comme acquise qu'après cette réponse terminale ; elle n'invente pas un état de validation intermédiaire.
- FAILED affiche le message de l'API et un bouton de relance.
- Les cinq générations précédentes ont duré de 83,1 à 215,0 secondes. L'indication « environ 1 à 4 minutes » est une observation de ces essais, pas une garantie. Le GPU gratuit et sa disponibilité peuvent changer.

## Lancer et vérifier sous Windows

Depuis le dossier backend, lancer le serveur :

    .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

Ouvrir http://127.0.0.1:8000/. Vérifier GET /health et la documentation API sur /docs.

Dans un second terminal depuis backend :

    .\.venv\Scripts\python.exe -m pytest -q

Résultat de cette refonte : 43 tests passent avec TestClient et fichiers temporaires, sans appeler le fournisseur. Cela comprend les tests antérieurs ainsi que le contrat statique des modules et les tests de galerie. Les tests automatiques ne prouvent pas le comportement visuel d'un navigateur, la disponibilité AR ni une génération distante nouvelle.

## Pourquoi ces choix

- Des modules ES natifs séparent les responsabilités sans ajouter React, Next.js, Node ou une chaîne de compilation au Sprint 1.
- Une seule application FastAPI sert HTML, CSS, JavaScript et API, ce qui évite le CORS et simplifie la démonstration.
- La galerie permet de réexaminer les vraies sorties de faisabilité sans les présenter comme une nouvelle génération.
- Les contrôles caméra, le focus clavier, les tailles lisibles, le contraste et la réduction des animations améliorent l'accès à l'outil.
- model-viewer est fixé à la version 4.4.0, mais le navigateur doit accéder au CDN Google.

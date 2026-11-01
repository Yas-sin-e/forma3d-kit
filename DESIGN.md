# Forma3D Studio — Fondations visuelles v2

## 1. Intention

L’interface présente un atelier de génération 3D pour des vendeurs en ligne. Elle reprend l’organisation claire d’un espace de travail sombre : outils à gauche, grande scène 3D au centre et galerie de résultats en dessous. La référence de style est une inspiration de composition et de densité ; la marque, les images et le code d’autres produits ne sont pas réutilisés.

Le Sprint 1 reste une démonstration de faisabilité. Il n’y a ni compte vendeur, ni produit commercial, ni paiement. Le modèle produit par une seule photo est une approximation visuelle, pas une mesure.

## 2. Couleurs

| Jeton | Valeur | Utilisation |
|---|---|---|
| Fond principal | #0E1218 | Page et navigation |
| Surface | #161C26 | Panneaux, cartes et champs |
| Surface élevée | #1C2430 | Commandes et zones secondaires |
| Scène 3D | #121923 | Fond du viewer et aperçu des modèles |
| Texte principal | #F1F5F9 | Titres, commandes et texte courant |
| Texte secondaire | #A9B4C4 | Aide, détails, métadonnées |
| Accent | #2DD4BF | Action principale, focus, sélection et état actif |
| Texte sur accent | #0E1218 | Texte des boutons accentués |
| Avertissement | #FBBF24 | Message de prudence |
| Erreur | #F87171 | Échec accompagné d’un libellé |
| Succès | #4ADE80 | Génération terminée et étape validée |
| Bordure | #303B49 | Séparation des cartes et commandes |
| Focus clavier | #2DD4BF | Contour visible autour du contrôle actif |

Les couleurs des états sont toujours accompagnées d’un texte ou d’une forme. Le texte secondaire et l’accent sur le fond principal dépassent le contraste WCAG AA pour du texte normal. Les boutons accentués utilisent le fond sombre comme couleur de texte.

## 3. Typographie et lisibilité

- Famille système : Inter, puis fontes système et Segoe UI. Le rendu reste disponible sans chargement de police distante.
- Le texte d’interface, les aides, les filtres, les métadonnées et les badges ont une taille minimale de 16 px.
- Les titres utilisent une graisse de 650 à 750 ; le texte courant reste à 400–600.
- Interligne de 1,4 ou plus pour le texte courant. Les titres restent courts et distincts.
- La page reste lisible à partir d’une largeur de 360 px. Les colonnes s’empilent et la galerie se réorganise avant de réduire les cibles de contrôle.

## 4. Composants

- **En-tête :** nom de Forma3D et navigation vers le studio et les vrais modèles d’essai.
- **Dépôt photo :** glisser-déposer et sélecteur clavier. JPG, PNG ou WebP, 10 Mo maximum, avec rappel de ne pas transmettre de visage ni de donnée personnelle.
- **Action principale :** une seule commande dominante, « Créer le modèle 3D ». Elle reste indisponible tant qu’aucune photo acceptée n’est choisie.
- **Suivi :** la demande envoi, PENDING, RUNNING, puis DONE ou FAILED. Le GLB est marqué validé uniquement quand l’API renvoie DONE, après le contrôle GLB 2.0 du fournisseur. La validation n’est pas présentée comme une étape active séparée si le backend ne publie pas cet état.
- **Temps :** secondes réellement écoulées depuis l’envoi ; aucun pourcentage ni délai restant inventé. La page indique que les cinq essais ont duré environ 1 à 4 minutes, sans garantir ce temps.
- **Erreur :** message compréhensible et possibilité de réessayer la même photo après FAILED.
- **Viewer :** model-viewer en version 4.4.0 fixée. Rotation, déplacement, zoom, remise à zéro, rotation automatique activée sur demande et plein écran sont disponibles après chargement.
- **Réalité augmentée :** le bouton n’apparaît que si model-viewer déclare canActivateAR.
- **Téléchargement :** le lien vers le GLB apparaît seulement quand l’API renvoie DONE ou quand un modèle historique réel de la galerie est ouvert.
- **Galerie :** API limitée aux cinq fichiers autorisés dans backend/data/feasibility-results/. Une entrée absente ou qui ne passe pas la validation GLB 2.0 n’est pas affichée. Les filtres portent sur les catégories chaise, tabouret et table d’appoint.
- **Origine :** un résultat de galerie est étiqueté « Généré par l’application ». Un fichier choisi depuis l’ordinateur est étiqueté « Importé manuellement » et reste dans le navigateur.
- **État vide :** décrit comment commencer sans montrer de modèle fictif.

## 5. Mise en page

- Navigation haute, photo et suivi regroupés dans la colonne latérale, viewer dans la zone la plus large.
- La galerie des cinq résultats réels est séparée du parcours de génération courant.
- Fond de scène discret, grille légère et bordures lisibles ; aucun décor ne doit détourner l’attention du produit.
- Les boutons ne dépendent pas d’un survol pour révéler leur fonction.
- À 980 px, les colonnes s’empilent ; à 680 px, l’en-tête et les cartes s’adaptent au téléphone.
- La page reste utilisable à 360 px sans défilement horizontal.

## 6. Mouvement et interactions

- Les changements de couleur, de bordure et de position utilisent une transition de 150 ms.
- Le suivi utilise un indicateur d’attente indéterminé. Sa longueur ne représente ni pourcentage ni progression estimée.
- La caméra reste immobile par défaut. La rotation automatique commence seulement après une activation claire.
- Le chargement du modèle utilise un indicateur animé sobre. prefers-reduced-motion réduit les transitions, animations et défilement animé.
- Toutes les fonctions importantes sont accessibles sans geste 3D : commandes explicites de caméra, bouton d’ouverture, filtres et téléchargement.

## 7. Accessibilité et source de vérité

- Chaque commande a un nom accessible ; les filtres exposent aria-pressed, les états sont annoncés et la navigation clavier a un contour net.
- Une erreur, un succès ou une sélection ne sont jamais exprimés par la couleur seule.
- Les champs et cibles tactiles gardent une hauteur pratique d’au moins 40 px.
- Les fichiers frontend/css/theme.css et frontend/css/components.css sont la mise en œuvre de cette source de vérité. Modifier ce document avant de changer les règles visuelles.

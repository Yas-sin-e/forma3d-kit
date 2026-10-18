# Forma3D Studio — Design foundations

## 1. Intention visuelle

Forma3D Studio doit évoquer un atelier de conception calme et précis : des surfaces chaudes, des outils sobres et une scène 3D mise en valeur. L’interface privilégie la lisibilité et la confiance dans l’état réel de la génération.

Éviter les décorations qui détournent l’attention du meuble ou laissent croire que le résultat est une mesure technique exacte.

## 2. Couleurs

| Jeton | Valeur | Usage |
|---|---|---|
| Fond principal | #F6F5F1 | Fond général de l’application |
| Surface | #FFFFFF | Cartes, panneaux et champs |
| Texte principal | #252B27 | Titres et contenu principal |
| Texte secondaire | #59635D | Aide, métadonnées et descriptions |
| Primaire | #285C4D | Actions principales, liens et états sélectionnés |
| Primaire au survol | #204B3F | Survol et pression du bouton principal |
| Accent chaud | #D28A47 | Petits repères, illustrations et détails décoratifs |
| Fond de scène 3D | #ECEBE5 | Espace visuel du viewer |
| Bordure | #D9DDD8 | Limites de cartes, champs et séparateurs |
| Erreur | #A43D35 | Erreurs accompagnées d’un message textuel |
| Succès | #286247 | Confirmation textuelle de génération réussie |
| Focus clavier | #8A5100 | Contour visible de focus, indépendant de la couleur de fond |

L’accent chaud ne doit pas porter seul un texte de petite taille. Les états d’erreur, de succès et de sélection doivent aussi utiliser un libellé ou une icône afin de ne pas dépendre uniquement de la couleur. Vérifier le contraste réel des combinaisons lors de l’implémentation.

## 3. Typographie

Utiliser une pile de polices système afin de ne pas dépendre d’un service réseau ou d’une police téléchargée :

- Famille : system-ui, Segoe UI, sans-serif.
- Titres : graisse 600 ou 700, lignes courtes.
- Texte courant : graisse 400, interligne confortable.
- Étiquettes et aide : taille lisible, jamais réduite pour faire tenir un contenu.

Échelle de départ : 12 px pour les métadonnées, 14 px pour les aides, 16 px pour le texte, 20 px pour les sous-titres, 28 px pour le titre de page et 40 px pour le titre d’accueil. Adapter les tailles sur petit écran plutôt que de couper le contenu.

## 4. Composants et règles d’usage

- **Barre supérieure :** nom du produit, accès à la création et liens de navigation essentiels.
- **Bouton principal :** une seule action dominante par écran, par exemple choisir une photo ou lancer la génération lorsqu’elle est disponible.
- **Bouton secondaire :** action complémentaire comme réinitialiser la caméra ou choisir une autre image.
- **Zone de dépôt :** indique les formats et contraintes effectivement acceptés par l’implémentation ; permet aussi de parcourir les fichiers.
- **État de génération :** affiche un statut réel et un texte compréhensible ; ne prétend pas connaître un pourcentage lorsque le backend n’en fournit pas.
- **Message d’erreur :** explique ce qui s’est produit et propose une prochaine action quand elle existe.
- **Viewer :** fournit une zone visuelle distincte et des commandes visibles et accessibles au clavier.
- **État vide :** indique ce que la personne peut faire ensuite, sans afficher de faux objet généré.
- **Modèle de démonstration :** porte un libellé explicite « modèle pré-généré » ou « objet de démonstration ».

Les composants du canevas d’aménagement appartiennent à l’étape 10 et ne doivent pas être ajoutés au périmètre visuel du MVP sans décision de cadrage.

## 5. Mise en page

- Donner la priorité au viewer et au modèle lorsqu’un GLB est disponible.
- Regrouper l’entrée photo, le statut et les explications dans des panneaux distincts.
- Utiliser un espacement régulier et des bordures discrètes plutôt que des ombres fortes.
- Sur petit écran, empiler les panneaux et conserver les commandes principales visibles.
- Ne jamais masquer le statut d’échec, les contraintes d’image ou les commandes de caméra derrière une interaction au survol uniquement.

## 6. Mouvement et interactions

- Les transitions d’interface sont courtes et fonctionnelles : environ 120 à 180 ms avec une courbe douce de sortie.
- Ne pas utiliser de rebond, de parallaxe décorative ou d’animation en boucle qui détourne l’attention.
- Respecter la préférence système de réduction des animations.
- La caméra 3D reste sous le contrôle de la personne ; aucune rotation automatique n’est activée par défaut.
- Ne pas créer de fausse progression visuelle. Si la durée est inconnue, utiliser un statut d’attente sobre, sans pourcentage fictif.
- Les commandes désactivées indiquent clairement pourquoi elles ne sont pas disponibles.

## 7. Accessibilité

- Tous les contrôles ont un nom accessible et un état compréhensible.
- Le parcours fonctionne au clavier, avec un focus visible.
- Les erreurs et statuts ne sont pas communiqués uniquement par une couleur.
- Les cibles tactiles restent faciles à sélectionner.
- Les préférences de mouvement réduit sont respectées.
- Les commandes du viewer disposent d’alternatives visibles aux gestes de souris.

## 8. Évolution

Ce fichier est la source de vérité visuelle. Toute modification d’interface doit mettre à jour les jetons ou règles concernés ici avant de diverger dans les composants. Les valeurs proposées sont les fondations de l’étape 1 ; leur rendu et leur contraste seront vérifiés lors de l’étape UI.

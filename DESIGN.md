# Forma3D Studio — Fondations visuelles v2

## 1. Intention
L'interface du SaaS aide un vendeur à préparer et examiner une fiche produit. Elle donne la priorité au produit et au viewer. Elle doit inspirer confiance sans prétendre que le modèle est une mesure ou une reproduction parfaite.

Le Sprint 1 ne comprend pas de tableau de bord SaaS complet. Ces fondations guident la page simple de génération et les futures interfaces sans imposer une bibliothèque frontend.

## 2. Couleurs

| Jeton | Valeur | Utilisation |
|---|---|---|
| Fond principal | #F6F5F1 | Fond général |
| Surface | #FFFFFF | Panneaux, cartes et champs |
| Texte principal | #252B27 | Titres et contenu |
| Texte secondaire | #59635D | Aide et métadonnées |
| Primaire | #285C4D | Action principale, liens et sélection |
| Primaire au survol | #204B3F | Survol et pression |
| Accent chaud | #D28A47 | Repères ponctuels et détails décoratifs |
| Fond de scène 3D | #ECEBE5 | Arrière-plan du viewer |
| Bordure | #D9DDD8 | Limites et séparateurs |
| Erreur | #A43D35 | État d'erreur avec texte explicatif |
| Succès | #286247 | État réussi avec libellé |
| Focus clavier | #8A5100 | Contour de focus visible |

L'accent chaud ne porte pas seul un texte de petite taille. Les états ont aussi un libellé ou une icône. Le contraste réel est vérifié lors de l'implémentation.

## 3. Typographie
- Famille système : system-ui, Segoe UI, sans-serif. Pas de police distante nécessaire au fonctionnement.
- Titres : graisse 600 ou 700, formulation courte.
- Texte courant : graisse 400, interligne confortable.
- Échelle de départ : métadonnées 12 px, aide 14 px, texte 16 px, sous-titre 20 px, titre de page 28 px, titre d'accueil 40 px.
- Sur petit écran, adapter la taille et empiler les panneaux plutôt que couper le contenu.

## 4. Composants et règles
- Navigation vendeur : marque et accès directs aux fonctions disponibles ; ne pas suggérer que des comptes sont déjà livrés au Sprint 1.
- Action principale : une seule action dominante, par exemple choisir une photo ou lancer une génération.
- Zone de dépôt : accepter uniquement les formats et tailles que l'API valide réellement.
- État de génération : refléter l'état retourné par le backend, sans pourcentage inventé.
- Erreur : expliquer le problème dans des termes compréhensibles.
- Viewer produit : zone visuelle distincte, contrôles accessibles au clavier et alternatives visibles aux gestes.
- Téléchargement : disponible seulement quand un GLB existe réellement.
- État vide : indiquer l'action possible sans afficher un résultat fictif.
- Objet de démonstration : porter la mention « modèle pré-généré » ou « objet de démonstration ».
- Widget distribuable et boutique vitrine : réservés aux sprints ultérieurs.

## 5. Mise en page
- Donner l'espace principal au produit et au viewer.
- Regrouper l'entrée photo, l'état du traitement et l'aide sans les confondre.
- Préférer des bordures discrètes et un espacement régulier aux ombres fortes.
- Sur petit écran, empiler les panneaux et garder l'action ainsi que les états visibles.
- Ne jamais cacher une erreur ou une commande importante derrière le survol.

## 6. Mouvement et interactions
- Transitions d'interface de 120 à 180 ms, courbe de sortie douce, seulement si elles clarifient un changement.
- Pas de rebond, de parallaxe décorative ou d'animation répétée qui détourne l'attention.
- Respecter la préférence système de réduction des animations.
- La caméra reste sous le contrôle de la personne ; rotation automatique désactivée par défaut.
- Pas de fausse barre de progression : sans durée ou pourcentage fourni par le backend, afficher un statut d'attente sobre.
- Un contrôle désactivé explique pourquoi il est indisponible.

## 7. Accessibilité et source de vérité
- Donner un nom accessible à chaque contrôle ; prendre en charge clavier et focus visible.
- Rendre erreurs et états compréhensibles sans dépendre seulement de la couleur.
- Garder des cibles tactiles faciles à sélectionner et des commandes de caméra alternatives aux gestes.
- DESIGN.md est la source de vérité visuelle. Mettre ce document à jour avant de modifier les règles dans le code.

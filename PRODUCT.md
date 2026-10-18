# Forma3D Studio — Product brief

## 1. Vision

Forma3D Studio aide une personne à partir d’une photo d’un petit meuble et à obtenir un modèle 3D consultable dans un navigateur. Le projet sert aussi de démonstrateur pédagogique : chaque choix technique doit pouvoir être expliqué pendant la soutenance.

## 2. Public visé et problème

Le public principal est une personne qui souhaite visualiser un meuble simple dans un viewer 3D avant d’imaginer son aménagement. Le projet est réalisé et défendu par une étudiante ; les parcours et les explications doivent rester compréhensibles sans expertise en modélisation 3D.

Le MVP cible les petits meubles simples : tabouret, chaise et table d’appoint. Cette sélection garde le lien avec l’aménagement tout en limitant le nombre de formes à évaluer au début.

## 3. Promesse et limites

À partir d’une photo appropriée, l’application tente de produire un fichier GLB avec un modèle image-vers-3D pré-entraîné, puis de l’afficher dans un viewer interactif.

Le résultat est une visualisation de démonstration. Une seule photo ne permet pas de garantir des dimensions exactes, une géométrie fidèle sur les faces invisibles ou un modèle prêt pour la fabrication. La qualité dépend de la photo, du modèle pré-entraîné et de la disponibilité du fournisseur gratuit.

Aucune garantie de disponibilité, de délai ou de quota n’est associée aux services gratuits externes. Le produit doit afficher clairement les échecs et les limites observés.

## 4. Parcours principal du MVP

1. La personne choisit une photo d’un meuble simple.
2. L’application vérifie que le fichier peut être traité et explique les erreurs d’entrée.
3. Le backend envoie l’image au fournisseur retenu, derrière l’interface Image3DProvider.
4. L’application expose l’état réel du traitement et présente un message clair si le fournisseur est indisponible ou si la génération échoue.
5. En cas de succès, le navigateur charge le GLB dans le viewer.
6. La personne fait tourner le modèle, déplace la caméra autour de lui et zoome.

Les états de chargement et de progression doivent provenir du traitement réel. L’interface ne simule pas une génération ou une progression.

## 5. Périmètre

### Inclus dans le MVP — étapes 1 à 9

- Une photo d’entrée à la fois pour les essais initiaux.
- Le contrôle et le prétraitement de l’image nécessaires à la génération.
- Un fournisseur image-vers-3D gratuit et pré-entraîné, choisi après un essai de faisabilité sur trois photos.
- Un fichier GLB réellement généré par le fournisseur pour le parcours de génération.
- Une interface de viewer avec rotation, déplacement de caméra, zoom et chargement d’objets de démonstration clairement identifiés.
- Une documentation pédagogique qui explique le rôle et le fonctionnement des fichiers importants.

### Hors MVP — étape 10 et au-delà

- Le canevas d’aménagement avec déplacement, rotation, redimensionnement, renommage et export.
- La reconstruction précise de dimensions ou la conception de pièces fabriquables.
- La prise en charge garantie de toutes les catégories d’objets, de photos ou de fournisseurs.
- Toute API payante, tout abonnement ou toute carte bancaire.
- Tout entraînement ou ajustement d’un modèle.

Un modèle GLB pré-généré peut servir de repli fiable pour une démonstration, mais il doit être présenté comme pré-généré. Il ne remplace pas le parcours de génération réelle.

## 6. Principes produit

- **Gratuité :** ne pas dépendre d’un service payant ni d’une clé associée à une facturation.
- **Aucun entraînement :** utiliser exclusivement des modèles pré-entraînés.
- **Transparence :** distinguer génération en direct, échec du fournisseur et modèle pré-généré.
- **Confidentialité :** ne pas envoyer de photo contenant des données personnelles à un Space public.
- **Compréhension :** privilégier une architecture simple et expliquer les décisions pour la soutenance.
- **Résilience :** rendre visibles les délais, files d’attente, indisponibilités et quotas des solutions gratuites.

## 7. Critères d’acceptation du MVP

Le MVP sera démontrable lorsque :

- une photo de petit mobilier peut suivre le parcours de contrôle, génération et affichage ;
- le fournisseur et le modèle employés sont identifiés et leurs licences sont vérifiées pour l’usage prévu ;
- l’application peut afficher une erreur exploitable lorsque le fournisseur gratuit ne répond pas ;
- un GLB réellement généré peut être chargé et manipulé dans le viewer ;
- les gestes de rotation, déplacement de caméra et zoom sont compréhensibles ;
- tout objet de secours pré-généré est étiqueté comme tel ;
- aucune étape ne dépend d’un entraînement de modèle ou d’un service payant ;
- la documentation permet à l’étudiante d’expliquer les fichiers réalisés.

## 8. Contexte de réalisation

Le suivi des tâches est prévu dans GitHub Projects. Le niveau déclaré de l’étudiante est avancé en Python et en React. La soutenance est estimée à environ deux semaines après le 18 octobre 2026, soit autour du 1er novembre 2026 ; la date exacte reste à confirmer.

# Étape 10 — Préparation locale de la photo

## Objectif

Améliorer la composition envoyée au fournisseur avec un traitement local et léger, sans modifier la photo source et sans ajouter de modèle de vision.

## Fonctionnement

- `backend/app/services/image_preparer.py` utilise Pillow 13.0.0. Pillow n'était pas installé dans le venv avant l'étape ; `Pillow>=11.3,<14` est désormais déclaré dans `backend/requirements.txt` et installé dans le venv local.
- La préparation redresse l'orientation EXIF, conserve les proportions, place le sujet au centre d'un canevas carré avec 12 % de marge et redimensionne avec LANCZOS. Le côté du canevas de sortie fait au moins 512 px.
- Si un côté de la photo originale est inférieur à 512 px ou si la variance des contours est sous le seuil local, l'API renvoie un avertissement non bloquant. Le frontend l'affiche avec un conseil photo.
- Le fichier source reste intact et sert à la miniature ; le fournisseur reçoit une copie PNG temporaire supprimée à la fin de l'appel. En cas de décodage impossible, l'envoi n'est pas bloqué : l'original est transmis avec un avertissement.
- `image_warning` est enregistré en SQLite. L'initialisation ajoute la colonne aux bases existantes sans supprimer ni réécrire les générations.

## Vérifications et limites

- Suite complète : 74 tests réussis, sans appel réseau au fournisseur. Les tests couvrent images synthétiques nettes, floues, petites et invalides, dimensions du canevas, conservation de l'original, copie réellement transmise au fournisseur simulé, persistance/migration et réponse de suivi.
- Aucun vrai fournisseur n'a été appelé, aucune génération GLB n'a été faite et aucun affichage navigateur n'a été vérifié pour cette étape.
- La netteté est une heuristique de contours ; l'avertissement ne juge pas le résultat 3D. Le redimensionnement ne crée pas de détails absents de l'image.

## À regarder dans le navigateur

Choisir une image petite puis une image nette de bonne taille ; confirmer le message d'avertissement lorsqu'il s'applique, vérifier qu'une génération peut quand même continuer et que la photo source affichée correspond au fichier original.

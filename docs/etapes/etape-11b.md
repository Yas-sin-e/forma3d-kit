# Étape 11b — Refonte du layout de Créer

## Objectif

Montrer tout le parcours de création de modèle en un coup d'œil sur ordinateur, sans toucher aux routes ou au traitement backend. L'étape est une évolution frontend ponctuelle ; elle ne démarre pas le Sprint 5.

## Schéma du layout

```text
┌─────────────────────────────────────────────────────────────────────┐
│ Titre de la page                                                     │
│ ① Photo ───────────────── ② Création ───────────────── ③ Résultat   │
├──────────────────────────────┬──────────────────────────────────────┤
│ PHOTO ET CATÉGORIE            │ VIEWER 3D                            │
│ Dépôt + catégorie             │ Modèle ou état vide                  │
│ Hors ligne + raison du bouton │ Barre de commandes caméra            │
│ Créer · Conseils · Technique  │                                      │
├──────────────────────────────┴──────────────────────────────────────┤
│ Suivi : photo → file → création → validation du GLB → terminé       │
│ Messages accessibles · durée écoulée                                │
└─────────────────────────────────────────────────────────────────────┘
```

Sous 1024 px, les deux cartes se placent l'une sous l'autre. Sur petit écran, le suivi conserve ses cinq étapes en bande défilante dans son propre conteneur ; le document ne reçoit pas de largeur de défilement supplémentaire.

## Comportement

- Le stepper supérieur est informatif : il montre Photo, Création et Résultat ; la ligne secondaire reflète le manque de photo, de catégorie, la disponibilité ou le résultat réel.
- La carte de gauche rassemble dépôt, choix de catégorie, indisponibilité compacte, raison lisible du bouton désactivé, bouton de création, conseils repliables et détails techniques repliables.
- Le viewer occupe la colonne droite, étirée à la même hauteur que la carte. Sa hauteur utilise les unités de viewport et `clamp()` ; une règle dédiée aux fenêtres de faible hauteur resserre le layout.
- Le suivi se place sous les deux colonnes. Il garde les cinq états et le temps écoulé. Les messages sont dans une région `aria-live="polite"`. Aucun pourcentage ni état distant hypothétique n'est affiché.
- Le focus visible, l'ordre naturel des champs, les libellés et `aria-current="step"` sont conservés.

## Fichiers à comprendre

- `frontend/js/pages/create.js` assemble l'étape supérieure, le formulaire, le viewer et le suivi.
- `frontend/js/views/uploader.js` recalcule l'état réel du formulaire et explique pourquoi le bouton est désactivé.
- `frontend/js/views/progress.js` représente les cinq étapes de suivi et les états renvoyés par l'API.
- `frontend/css/components.css` définit la grille, les hauteurs adaptatives et le repli mobile.
- `backend/tests/test_frontend.py` teste les contrats statiques du layout sans ajouter de route ou changer la logique backend.

## Vérifications

- Tests ciblés : `backend/tests/test_frontend.py` — 5 réussis.
- Suite complète : `backend/tests` — 83 réussis en 2,65 s ; aucun fournisseur distant n'est sollicité.
- `node --check` a été exécuté sur tous les modules frontend JavaScript et `git diff --check` n'a trouvé aucune erreur.
- Aucun navigateur n'a été piloté. Le rendu réel, les hauteurs de scroll à 100 % (1366×768 et 1920×1080), les interactions, le lecteur d'écran et le layout à 360 px restent à contrôler manuellement.

## À vérifier manuellement

1. À 100 % de zoom sur 1366×768 puis 1920×1080, vérifier que le parcours, les deux colonnes, le suivi et le pied de page tiennent sans scroll vertical au repos.
2. Tester le stepper après le choix d'une photo, d'une catégorie, lors d'une génération, d'un échec et d'un résultat terminé.
3. Avec le serveur hors ligne, vérifier la ligne « Création momentanément indisponible », le lien « Voir les exemples » et la raison visible du bouton.
4. Ouvrir Conseils photo et Détails techniques ; vérifier la tabulation et le focus visible.
5. À 360 px, vérifier les colonnes empilées, la lisibilité des libellés et le scroll horizontal contenu aux cinq étapes du suivi, sans scroll horizontal de page.

## Limites

Les tests sont des contrôles statiques et ne prouvent pas le rendu visuel, l'absence réelle de scrollbar sur une configuration donnée, ni l'accessibilité avec une technologie d'assistance. Aucun code backend, fournisseur, fichier `backend/.env` ou choix de modèle n'a été modifié. Le Sprint 5 reste non démarré.

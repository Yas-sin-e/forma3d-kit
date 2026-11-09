# Étape 9 — CRUD des catégories

## Objectif et résultat

Rendre les catégories modifiables sans les inscrire en dur dans le formulaire ou la galerie. SQLite est la source de vérité partagée.

## Backend (9a)

- `CategoryService` applique les règles sur les slugs et libellés ; `categories.py` expose `GET`, `POST`, `PATCH` et `DELETE /categories`.
- Un slug est unique et un libellé ne peut pas être vide. Les conflits sont expliqués par l'API.
- Une catégorie utilisée par une génération ne peut pas être supprimée : l'API renvoie HTTP 409. Une catégorie inutilisée peut l'être.
- Désactiver/réactiver n'efface pas les données : les catégories inactives sont exclues des nouveaux uploads, mais les générations déjà liées restent dans l'historique et la galerie.
- Tests repository, service et API : 68 tests complets après l'étape 9a. Commit : `cb82ece`.

## Frontend (9b)

- `frontend/js/views/categories.js` charge les catégories et fournit les actions créer, renommer, activer/désactiver et supprimer ; les erreurs de l'API sont affichées.
- Le menu d'envoi ne propose que les catégories actives. Les filtres de galerie sont générés depuis l'API et gardent visibles les catégories inactives déjà utilisées.
- Vérification automatisée : suite complète de 68 tests après l'étape 9b, incluant les ressources HTML/JS. Aucun navigateur n'a été piloté pour cette livraison.
- Commit : `1c3f1ac`.

## À regarder dans le navigateur

Vérifier la création et le renommage, les messages de conflit, la désactivation/réactivation, le refus de supprimer une catégorie utilisée, puis l'actualisation du formulaire et des filtres de galerie. Vérifier aussi que l'écran reste utilisable à 360 px.

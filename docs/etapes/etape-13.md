# Étape 13 — Sprint 5a : identifiant public et activation d’intégration

## Objectif

Autoriser la propriétaire à exposer individuellement un modèle terminé, sans rendre les modèles publics par défaut. Chaque modèle persistant reçoit un identifiant public UUID4 stable ; le GLB et ses métadonnées ne sont accessibles qu’après activation explicite.

## Changements et responsabilités

- `backend/app/repositories/sqlite_repository.py` ajoute et migre `public_id` et `embed_enabled`, attribue un UUID4 aux anciennes lignes terminées et conserve l’identifiant lors des mises à jour.
- `backend/app/services/generation_service.py` vérifie qu’un modèle est terminé et que son GLB existe avant l’activation.
- `backend/app/routers/models.py` expose le réglage local et des routes publiques ne donnant que les métadonnées minimales et le fichier GLB.
- `frontend/js/pages/model-detail.js` et `frontend/js/api.js` permettent d’activer ou de désactiver l’intégration depuis la fiche Studio.
- La galerie de démonstration fixe reste inactivable ; un exemple copié devient un modèle persistant désactivé par défaut.

## Contrat HTTP

- `PATCH /models/{id}/integration` reçoit `{"enabled": true}` ou `false`.
- `GET /public/models/{public_id}` donne les métadonnées publiques minimales.
- `GET /public/models/{public_id}/glb` sert le GLB.
- Les deux routes publiques répondent 404 si le modèle est absent, désactivé, non terminé ou si son GLB manque. Aucun identifiant interne, chemin local ou photo source n’est exposé.

## Vérification

- `PYTHON_DOTENV_DISABLED=true`, `HF_SPACE_ID` vide : `python -m pytest -v -x -o faulthandler_timeout=30 backend/tests` — 87 tests réussis en 4,02 s.
- `node --check` sur les modules JavaScript et `git diff --check` réussis.
- Aucun appel au fournisseur 3D ; aucun navigateur lancé.

## Limites

Le Studio reste mono-propriétaire sans authentification : il est réservé à un usage local ou de démonstration. Cette étape fournit le partage public opt-in du modèle ; les clés d’API, l’authentification de l’API et le widget arrivent dans les sous-étapes suivantes. La génération réelle et le rendu visuel du bouton dans un navigateur ne sont pas vérifiés ici.

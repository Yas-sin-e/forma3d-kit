# Étape 23 — Supprimer un modèle depuis sa fiche

Date : 15 novembre 2026. Validée par l'étudiante (« Oui, ajoute-la ») après la présentation des fichiers et du comportement.

## But et livrable vérifiable

- But : la propriétaire peut retirer de son Studio un modèle raté ou inutile, ce qui était impossible jusqu'ici.
- Livrable vérifiable : dans la fiche d'un modèle de « Mes modèles », le bouton « Supprimer ce modèle » demande une confirmation, puis la ligne SQLite, le fichier GLB et la photo source disparaissent ; la fiche renvoie vers « Mes modèles », où le modèle n'apparaît plus.

## Fichiers

| Fichier | Rôle |
|---|---|
| `backend/app/repositories/base.py` | Ajoute `delete_generation` au contrat du dépôt |
| `backend/app/repositories/sqlite_repository.py` | `DELETE FROM generations WHERE id = ?` ; aucune autre table ne référence une génération |
| `backend/app/storage/base.py` et `local_storage.py` | `delete_files` : efface le GLB et la photo dont le nom est reconstruit par le serveur à partir de l'UUID (aucun chemin reçu du client) |
| `backend/app/services/generation_service.py` | `delete_generation` : refuse PENDING/RUNNING, retire la ligne puis les fichiers |
| `backend/app/routers/models.py` | `DELETE /models/{id}` : 204, 404 (inconnu ou exemple), 409 (création en cours) ; protégé par la session propriétaire comme tout le routeur |
| `frontend/js/api.js` | `deleteModel(modelId)` |
| `frontend/js/pages/model-detail.js` | Bouton, fenêtre de confirmation, avertissement si l'intégration est active, retour à `#/modeles` |
| `frontend/css/components.css` | Style du bouton et du message d'erreur |
| `backend/tests/test_model_deletion.py` (nouveau) | 7 tests : suppression complète, fin de l'accès public, 404, 409, dépôt, garde-fou de chemin, fichiers absents |
| `backend/tests/test_auth.py`, `test_frontend.py` | Route refusée sans session ; contrat statique du bouton |

## Logique

1. La propriétaire clique sur « Supprimer ce modèle ». Le bouton n'existe que pour un modèle de l'historique (pas pour les cinq exemples de démonstration) et il est caché pendant la création.
2. `confirmDialog` explique que l'action est irréversible ; si l'intégration est activée, il précise que l'iframe ou le widget des sites cessera de fonctionner.
3. Le service vérifie l'état sous verrou : une génération PENDING ou RUNNING est refusée, sinon la tâche de fond écrirait un GLB pour une ligne disparue.
4. La ligne est supprimée d'abord : le modèle disparaît immédiatement du Studio, de l'API et de `/embed`, même si un fichier résistait. Les fichiers sont ensuite effacés.

## Choix pour la soutenance

- Suppression définitive plutôt qu'une corbeille : un seul utilisateur, des fichiers locaux, et un besoin simple (nettoyer les essais ratés). La confirmation explicite compense l'absence de corbeille.
- L'API externe `/api/v1` ne reçoit pas de suppression : une clé API volée ne peut pas effacer la bibliothèque.
- Les modèles copiés depuis les exemples sont des copies de la bibliothèque : ils peuvent être supprimés ; les cinq fichiers d'exemple d'origine restent intacts.

## Lancement et test

```bash
cd backend
python -m pytest tests/test_model_deletion.py tests/test_auth.py tests/test_frontend.py -q
```

Test manuel : lancer `./scripts/dev.ps1`, ouvrir un modèle dans « Mes modèles », cliquer sur « Supprimer ce modèle », confirmer, vérifier qu'il a disparu de la liste. Après mise à jour, recharger la page avec Ctrl+F5 pour que le navigateur prenne le nouveau `api.js`.

## Limites

- Aucune restauration possible après confirmation.
- Le bouton n'a pas été vérifié visuellement dans un navigateur pendant cette étape ; les tests vérifient le contrat HTTP, les fichiers et le code de la page.

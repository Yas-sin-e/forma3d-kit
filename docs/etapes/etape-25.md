# Étape 25 — Renommer un modèle depuis sa fiche

## Objectif et livrable vérifiable

- Objectif : pouvoir corriger le nom d'un modèle (par exemple « th », hérité du nom de la photo `th.webp`) sans le supprimer ni le recréer.
- Livrable vérifiable : sur la fiche d'un modèle enregistré, le bouton « ✎ Renommer » ouvre un champ ; après « Enregistrer », le nouveau nom apparaît sur la fiche et dans « Mes modèles », y compris après un redémarrage.

## Fichiers créés ou modifiés

| Fichier | Rôle dans l'étape |
|---|---|
| `backend/app/repositories/base.py` | Ajoute la méthode `rename_generation` au contrat du dépôt. |
| `backend/app/repositories/postgres_repository.py` | `UPDATE generations SET filename = …` puis relit la ligne. |
| `backend/app/services/generation_service.py` | Nettoie et valide le nom (1 à 80 caractères, pas de `/` ni `\`), garde l'extension d'origine. |
| `backend/app/schemas.py` | `ModelRenameRequest` : corps JSON `{"name": "..."}`, 1 à 80 caractères. |
| `backend/app/routers/models.py` | Route `PATCH /models/{id}/name` : 200, 404 (inconnu) ou 422 (nom refusé). |
| `frontend/js/api.js` | Fonction `renameModel(modelId, name)`. |
| `frontend/js/pages/model-detail.js` | Bouton « ✎ Renommer » et formulaire en ligne (Entrée enregistre, Échap annule). |
| `frontend/css/components.css` | Mise en page du bouton et du formulaire. |
| `backend/tests/test_model_rename.py` | 10 tests du renommage. |
| Fichiers frontend et `test_frontend.py` | Clé de cache `?v=` passée de `20261115-e1` à `20261117-r1` pour que le navigateur charge le nouveau `api.js`. |

## Logique

- La galerie affiche `Path(filename).stem` : le nom visible vient de la colonne `filename`. Renommer revient donc à remplacer cette colonne, en conservant l'extension (`th.webp` → `Canapé blanc.webp`).
- Aucune migration de base : aucune colonne n'est ajoutée.
- Les fichiers sur le disque sont nommés par identifiant (`{id}.glb`) : ils ne bougent pas. L'UUID public ne change pas non plus, donc une iframe ou un widget déjà intégré continue de fonctionner.
- Les exemples de démonstration non enregistrés en base n'ont pas de bouton (route → 404).

## Lancement et test

```bash
cd backend
python -m pytest -q tests/test_model_rename.py
```

Résultat observé le 17 novembre 2026 : suite complète `189 passed` sur la base PostgreSQL de test (`forma3d_test`). Le bouton n'a pas été vérifié visuellement dans le navigateur par l'assistant.

## Justification pour la soutenance

Le plus petit changement utile : une route, une méthode de dépôt, une validation côté service (double contrôle avec Pydantic), aucun changement de schéma SQL ni de fournisseur 3D.

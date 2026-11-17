# Étape 26 — Modifier la catégorie d'un modèle (et comprendre le « Not Found »)

## Objectif et livrable vérifiable

- Objectif : corriger la catégorie d'un modèle déjà créé (par exemple un canapé envoyé par erreur dans « Chaise ») sans le supprimer.
- Livrable vérifiable : sur la fiche d'un modèle enregistré, « ✎ Modifier » ouvre un formulaire avec le nom et la catégorie. Après « Enregistrer », le modèle apparaît dans le filtre de sa nouvelle catégorie dans « Mes modèles ».

## Le « Not Found » observé à l'étape 25

- Symptôme : en renommant un modèle, la fiche affichait « Not Found ».
- Cause : le serveur Uvicorn du port 8001 avait été démarré avant la récupération de l'étape 25. Il est lancé sans rechargement automatique et garde donc l'ancien code Python, où la route `PATCH /models/{id}/name` n'existait pas. FastAPI répond alors `{"detail": "Not Found"}`. Les fichiers du frontend, eux, sont relus depuis le disque : le nouveau bouton s'affichait quand même.
- Preuve : la route du code actuel répond « Modèle introuvable. » pour un identifiant inconnu, jamais « Not Found ».
- Correction : arrêter l'ancien serveur puis relancer `scripts/dev.ps1`. Le script affiche désormais un avertissement quand il réutilise un serveur déjà démarré.

## Fichiers modifiés

| Fichier | Rôle dans l'étape |
|---|---|
| `backend/app/repositories/base.py` | Ajoute `set_generation_category` au contrat du dépôt. |
| `backend/app/repositories/postgres_repository.py` | `UPDATE generations SET category_id = (SELECT id FROM categories WHERE slug = …)`. |
| `backend/app/services/generation_service.py` | `change_category` : refuse une catégorie inconnue ou désactivée (même règle qu'à l'envoi d'une photo). |
| `backend/app/schemas.py` | `ModelCategoryRequest` : corps JSON `{"category": "slug"}`. |
| `backend/app/routers/models.py` | Route `PATCH /models/{id}/category` : 200, 404 ou 422. |
| `frontend/js/api.js` | Fonction `changeModelCategory(modelId, category)`. |
| `frontend/js/pages/model-detail.js` | Bouton « ✎ Modifier », liste des catégories actives ; n'envoie que ce qui a changé. |
| `scripts/dev.ps1` | Avertissement quand un serveur déjà lancé est réutilisé. |
| `backend/tests/test_model_rename.py` | 4 tests de plus pour la catégorie (14 au total). |
| Fichiers frontend et `test_frontend.py` | Clé de cache passée à `20261117-r2`. |

## Logique

- Deux routes séparées (`/name` et `/category`) : chacune a une seule responsabilité et ses propres erreurs. Le formulaire appelle seulement celle dont la valeur a changé.
- Une catégorie désactivée encore portée par le modèle reste visible dans la liste, avec la mention « (désactivée) ». Sans cela, ouvrir puis enregistrer le formulaire la remplacerait sans le vouloir.
- Les fichiers, l'UUID public et l'intégration ne changent pas.

## Lancement et test

```bash
cd backend
python -m pytest -q tests/test_model_rename.py
```

Résultat observé le 17 novembre 2026 : suite complète `193 passed` sur la base PostgreSQL de test. Le formulaire n'a pas été vérifié dans le navigateur par l'assistant.

## Justification pour la soutenance

C'est le même schéma que le renommage : une route, une méthode de dépôt et une validation dans le service. Il n'y a aucune migration SQL, car `category_id` existe déjà. Le diagnostic du « Not Found » montre la différence entre le code chargé en mémoire et le code présent sur le disque.

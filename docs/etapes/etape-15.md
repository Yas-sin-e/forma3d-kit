# Étape 15 — Sprint 5c : API versionnée

## Objectif

Permettre à un site intégrateur d’envoyer une photo, de suivre la création d’un modèle et d’obtenir le GLB avec une clé API. Toutes les routes du contrat commencent par `/api/v1` et passent par `X-API-Key`.

## Routes

- `POST /api/v1/models` reçoit une photo JPG, PNG ou WebP de 10 Mo maximum et le slug d’une catégorie active. Il réutilise `UploadValidator`, `CategoryService` et `GenerationService`, puis lance le travail asynchrone existant.
- `GET /api/v1/models/{id}` renvoie l’état observé et des liens versionnés ; l’intégrateur interroge cette route pour suivre `PENDING`, `RUNNING`, `DONE` ou `FAILED`.
- `GET /api/v1/models/{id}/glb` ne sert le GLB que quand le statut est `DONE`.
- `GET /api/v1/models/{id}/integration-code` donne l’iframe si le modèle est terminé et si la propriétaire l’a activé dans le Studio. La route `/embed/{public_id}` sera créée à l’étape 16.

Les erreurs des routes versionnées ont une forme JSON stable : `{ "error": { "code": "…", "message": "…" } }`. Les états courants comprennent 401 (clé manquante/invalide/révoquée), 403 (catégorie ou intégration interdite), 404 (modèle inconnu), 409 (modèle pas encore prêt), 413/415 (photo refusée) et 429 (quota ou débit atteint). `Retry-After` accompagne les réponses 429.

## Quota, débit et CORS

- `API_DAILY_GENERATION_LIMIT=20` limite les créations valides par clé et par jour UTC.
- `API_RATE_LIMIT_PER_MINUTE=10` limite toutes les requêtes versionnées par clé sur une fenêtre glissante de 60 secondes.
- Les usages sont persistés atomiquement dans `api_usage_daily` et `api_rate_events`, donc un redémarrage ne remet pas les compteurs à zéro.
- `API_CORS_ORIGINS` contient une liste séparée par des virgules d’origines HTTP(S) exactes. Elle est vide par défaut et le joker `*` est refusé. Les sites intégrateurs doivent configurer leurs propres origines avant les appels cross-origin.

Aucun nouveau paquet n’a été installé ; les paramètres sont dans `.env.example`. Les routes internes du Studio restent disponibles avec leur contrat existant.

## Fichiers

- `backend/app/config.py` lit et valide les limites et origines CORS.
- `backend/app/repositories/base.py` et `sqlite_repository.py` exposent les compteurs persistants et atomiques.
- `backend/app/services/api_key_service.py` consomme le débit et le quota par clé.
- `backend/app/routers/api_v1.py` regroupe le contrat externe ; `main.py` ajoute CORS précis et la forme stable des erreurs HTTP.
- `backend/app/schemas.py` décrit les réponses versionnées ; `backend/app/routers/api_keys.py` conserve le contrôle de clé mis en place à l’étape 14.
- `.env.example`, `docs/STOCKAGE.md`, `docs/STRUCTURE.md` et `docs/ETAT.md` décrivent les réglages et le stockage.
- `backend/tests/test_api_v1.py`, `test_api_settings.py` et `test_api_keys.py` testent la voie API et les limites avec SQLite temporaire et fournisseur simulé.

## Vérification et limites

- Tests ciblés : 10 réussis.
- Suite complète : 97 tests réussis en 9,43 s, avec `PYTHON_DOTENV_DISABLED=true`, `HF_SPACE_ID` vide et TestClient local.
- `node --check` accepte tous les modules JavaScript ; `git diff --check` passe.
- Aucun fournisseur distant ou navigateur n’a été utilisé. La génération réelle, l’accès CORS depuis un site réellement autorisé, la page d’embed et la CI GitHub restent à vérifier aux étapes suivantes.

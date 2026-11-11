# Étape 14 — Sprint 5b : clés API

## Objectif

Donner à la propriétaire les moyens de créer et révoquer des clés pour les futures routes du module intégrable. Une clé complète ne peut être lue qu’une fois au moment de sa création.

## Stockage SQLite

La table `api_keys` contient `id`, `name`, `prefix`, `fingerprint`, `created_at` et `revoked`. La valeur secrète aléatoire ne figure ni dans SQLite, ni dans les réponses de liste, ni dans les journaux. Le préfixe `f3d_live_` suivi de caractères aléatoires permet d’identifier la famille de jetons ; la base ne conserve que le préfixe lisible et l’empreinte SHA-256 complète.

## Contrat HTTP

- `POST /api-keys` crée une clé et renvoie sa valeur complète une seule fois dans le corps de réponse.
- `GET /api-keys` retourne le nom, le préfixe tronqué par l’interface, la date et l’état, sans empreinte ni secret.
- `DELETE /api-keys/{id}` marque la clé révoquée et conserve son historique.
- `require_api_key` lit l’en-tête `X-API-Key`, calcule une empreinte SHA-256 et la compare avec `hmac.compare_digest`. Les clés absentes, invalides ou révoquées reçoivent 401.

## Page Studio

La page `#/cles-api` permet de nommer, créer, copier et révoquer les clés. La valeur complète reste uniquement dans la réponse de création et le DOM de la page courante ; la page ne l’écrit ni en stockage local ni dans la base. Après avoir quitté la page, le Studio ne peut pas la révéler à nouveau.

## Fichiers et responsabilités

- `backend/app/models.py` et `backend/app/schemas.py` décrivent les données et réponses sans renvoyer l’empreinte.
- `backend/app/repositories/base.py` définit les opérations de persistance ; `sqlite_repository.py` les implémente avec des connexions séparées.
- `backend/app/services/api_key_service.py` génère, empreinte, vérifie et révoque les clés.
- `backend/app/routers/api_keys.py` expose les routes locales de gestion et la dépendance réutilisable pour protéger les routes externes.
- `frontend/js/api.js`, `frontend/js/pages/api-keys.js`, `frontend/js/router.js`, `frontend/index.html` et `frontend/css/components.css` forment la page de gestion.
- `backend/tests/test_api_keys.py` et `backend/tests/test_frontend.py` couvrent le contrat sans serveur externe.

## Vérification et limites

- Tests ciblés clés API + frontend : 10 réussis.
- Suite complète : 90 tests réussis en 7,57 s avec `PYTHON_DOTENV_DISABLED=true`, `HF_SPACE_ID` vide et TestClient local.
- `node --check` a accepté tous les modules JavaScript ; `git diff --check` n’a relevé aucun problème d’espacement.
- Aucun appel au fournisseur 3D, à Internet ou à une route externe n’a été effectué.
- Le Studio est mono-propriétaire mais n’a pas encore d’authentification ; les routes de gestion sont donc réservées à l’instance locale ou à une démonstration. Les routes `/api/v1` consommeront la dépendance à l’étape 15. La CI GitHub et l’affichage visuel dans un navigateur ne sont pas vérifiés ici.
- Aucune variable d’environnement n’est nécessaire à cette étape ; `.env.example` n’a pas été changé.

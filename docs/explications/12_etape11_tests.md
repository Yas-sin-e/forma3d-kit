# 12. Étape 11 — Les tests automatiques (`backend/tests/`)

## Pourquoi des tests ?

Au lieu de cliquer partout après chaque modification, de petits programmes vérifient **tout seuls**
que le projet fonctionne. Une commande : `python -m pytest -q`. La CI GitHub les relance à chaque pull request.

## Les outils

### `TestClient` : des requêtes sans serveur

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.get("/health")
assert response.status_code == 200
assert response.json() == {"status": "ok"}
```

`TestClient` envoie de **fausses requêtes** directement à l'application, sans lancer Uvicorn.
`assert` = « je suis sûr que… » ; si c'est faux, le test échoue en rouge.

### Des faux à la place du réseau

Les tests ne contactent **jamais** TRELLIS ni Colab. On donne aux fournisseurs un **faux client** :

```python
provider = TrellisSpaceProvider(settings, client_factory=FakeClient, clock=fake_clock)
```

C'est possible grâce à l'injection de dépendances (étapes 1 et 4) : les tests sont rapides,
gratuits et ne dépendent pas de la disponibilité du Space.

## La préparation commune

### `conftest.py` (lu automatiquement par pytest)

```python
os.environ["DATABASE_URL"] = pg_support.test_database_url()   # base forma3d_test, jamais la vraie
from app.main import app

@pytest.fixture(autouse=True)
def owner_session_override(request):
    if request.node.get_closest_marker("real_auth"):          # tests de connexion : vraie vérification
        app.dependency_overrides.pop(require_owner, None)
        yield
        return
    app.dependency_overrides[require_owner] = lambda: None     # autres tests : session considérée ouverte
    yield
    app.dependency_overrides.pop(require_owner, None)

@pytest.fixture(autouse=True)
def clean_database():
    pg_support.reset_database()                                # base remise à zéro avant CHAQUE test
    yield
```

- **Fixture** = préparation exécutée avant un test. `autouse=True` = avant **tous** les tests.
- `dependency_overrides` remplace `require_owner` : les tests métier n'ont pas besoin de se connecter.
- Les tests marqués `@pytest.mark.real_auth` gardent la **vraie** vérification de session.
- Chaque test part d'une base **vide** : un test ne peut pas en influencer un autre.

### `pg_support.py`

Outils des tests : lit `TEST_DATABASE_URL`, refuse une base dont le nom ne finit pas par `_test`,
supprime et recrée le schéma, exécute des requêtes de vérification.

## Ce que vérifie chaque fichier

| Fichier | Ce qu'il vérifie |
|---|---|
| `test_health.py` | `/health` et `/health/provider` (ONLINE / OFFLINE / UNCONFIGURED, jamais l'adresse) |
| `test_upload_validator.py` | Photo vide (400), trop grosse (413), mauvais format, faux JPEG (415) |
| `test_image_preparer.py` | Copie carrée, original intact, avertissements photo petite ou floue |
| `test_local_storage.py` | Écriture atomique, refus d'un identifiant qui n'est pas un UUID |
| `test_generation_service.py` | États PENDING → RUNNING → DONE ou FAILED, photo préparée envoyée |
| `test_glb_finisher.py` | Matériau et normales ajoutés **sans modifier la géométrie** |
| `test_trellis_provider.py` | TRELLIS avec faux client : contrat, délai, quota, jeton masqué |
| `test_huggingface_provider.py` | Fournisseur TripoSR avec faux client |
| `test_models_api.py` | Routes `/models` : envoi, suivi, téléchargement (409 avant DONE) |
| `test_model_library.py` | Import GLB et copie d'un exemple |
| `test_model_rename.py` | Renommage et changement de catégorie (14 tests : nom vide, trop long, `/`, catégorie désactivée…) |
| `test_model_deletion.py` | Suppression : ligne, GLB et photo effacés ; refus pendant la création, pour un exemple ou sans connexion |
| `test_demo_gallery.py` | Seuls les exemples connus et valides sont publiés |
| `test_category_service.py` | Règles du slug et du libellé |
| `test_category_repository.py` | Catégories en base PostgreSQL |
| `test_categories_api.py` | Routes `/categories` (201, 404, 409, 422) |
| `test_generation_repository.py` | Historique en base, persistance après redémarrage, migrations |
| `test_postgres_repository.py` | Cas limites, chemins portables, **concurrence** (`FOR UPDATE`) |
| `test_repository_factory.py` | `DATABASE_URL` obligatoire, mot de passe masqué |
| `test_auth.py` | 401 sans cookie, mot de passe faux, limite de 5 essais, routes publiques ouvertes |
| `test_api_keys.py` | Empreinte seule en base, secret affiché une fois, révocation, suppression, quotas |
| `test_api_settings.py` | Validation des quotas et des origines CORS / iframe (`*` refusé) |
| `test_api_v1.py` | API externe : clé, statuts, format d'erreur `{"error": ...}`, quota |
| `test_embed.py` | Page `/embed` et en-tête CSP `frame-ancestors` |
| `test_frontend.py` | Fichiers du frontend présents ; `fetch` **seulement** dans `api.js` |
| `test_trial_tools.py` | Outils d'essai de fournisseurs |

## Les deux sortes de tests

| Sorte | Exemple | But |
|---|---|---|
| Le cas normal | photo valide → 202, puis DONE | Le service rend ce qu'on attend |
| Le cas d'erreur | PDF → 415 ; clé révoquée → 401 ; 21e création du jour → 429 | Le serveur **refuse proprement**, sans planter (500) |

`@pytest.mark.parametrize` lance le même test avec plusieurs valeurs, c'est pourquoi il y a plus
de tests que de fonctions.

## À retenir

> Les tests tournent **sans réseau** (faux fournisseurs), sur une **base de test séparée** remise à zéro,
> et vérifient autant les refus (400, 401, 409, 413, 415, 422, 429) que les réussites.

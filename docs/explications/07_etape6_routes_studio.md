# 7. Étape 6 — Les routes du Studio : modèles, catégories, exemples

Fichiers : `backend/app/routers/models.py`, `backend/app/routers/categories.py`,
`backend/app/services/category_service.py`, `backend/app/services/demo_gallery.py`.

## C'est quoi un routeur ?

Un **routeur** regroupe des routes qui ont le même préfixe d'URL.

```python
router = APIRouter(prefix="/models", tags=["models"])                 # Studio (protégé)
public_router = APIRouter(prefix="/public/models", tags=["public-models"])   # public
```

Une route = une **méthode HTTP** + une **adresse** + une **fonction** :

```python
@router.get("/{generation_id}", response_model=GenerationResponse)
def get_model_generation(generation_id: str, service = Depends(get_generation_service)):
    ...
```

- `{generation_id}` est lu dans l'adresse et passé à la fonction.
- `response_model` : FastAPI vérifie et filtre la réponse avec le schéma Pydantic.
- `Depends(get_generation_service)` : FastAPI appelle `get_generation_service(request)` et donne
  le résultat à la fonction. Dans les tests, on peut le remplacer (comme un `@MockBean`).

```python
def get_generation_service(request: Request) -> GenerationService:
    return request.app.state.generation_service
```

## Étape 6.1 — Les routes des modèles (`routers/models.py`)

### Créer une génération : `POST /models`

```python
@router.post("", response_model=GenerationResponse, status_code=202)
async def create_model_generation(file: UploadFile, category: str = Form(...),
                                  background_tasks: BackgroundTasks, service = Depends(...)):
    try:
        content = await file.read(MAX_UPLOAD_BYTES + 1)          # lit au plus 10 Mo + 1 octet
        validated = UploadValidator.validate(file.filename, file.content_type, content)
    except UploadValidationError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    finally:
        await file.close()
    try:
        record = service.create_generation(validated, content, category)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    background_tasks.add_task(service.run, record.id)            # la génération démarre APRÈS la réponse
    return _to_response(record)
```

- **`file.read(MAX_UPLOAD_BYTES + 1)`** : on ne lit jamais plus que nécessaire. Si on obtient 10 Mo + 1 octet, le fichier est trop gros.
- **`BackgroundTasks`** : FastAPI exécute `service.run(id)` **après** avoir envoyé la réponse 202.
- **`_to_response()`** traduit la fiche interne en JSON public, sans aucun chemin de fichier :

```python
status_url=f"/models/{record.id}",
model_url=f"/models/{record.id}/glb" if is_done else None,
```

### Toutes les routes du Studio

| Méthode | Adresse | Rôle | Erreurs possibles |
|---|---|---|---|
| POST | `/models` | Envoie une photo → **202** + suivi | 400, 413, 415, 422 |
| GET | `/models/{id}` | Lit l'état (le navigateur l'appelle toutes les 1,5 s) | 404 |
| GET | `/models/{id}/glb` | Télécharge le GLB | 404, **409 si pas encore DONE** |
| GET | `/models/{id}/source-image` | Photo source (carte de galerie, mode Comparer) | 404 |
| GET | `/models/gallery` | Exemples + tous les modèles enregistrés | — |
| GET | `/models/gallery/{id}` | GLB d'un exemple | 404 |
| POST | `/models/import` | Importe un GLB (≤ 30 Mo) → **201** | 413, 415, 422 |
| POST | `/models/examples/{id}/copy` | Copie un exemple dans « Mes modèles » → **201** | 404, 422 |
| PATCH | `/models/{id}/integration` | Active ou désactive l'intégration publique | 404, 409 |
| PATCH | `/models/{id}/name` | Renomme | 404, 422 |
| PATCH | `/models/{id}/category` | Change la catégorie | 404, 422 |
| DELETE | `/models/{id}` | Supprime → **204** | 404, **409 si en cours** |

Rappel : **202** = « accepté, traitement en cours » ; **201** = « créé » ; **204** = « fait, rien à renvoyer » ;
**409** = « conflit avec l'état actuel ».

### L'ordre des routes compte

`/models/gallery` est déclarée **avant** `/models/{generation_id}`. Sinon FastAPI croirait que
`gallery` est un identifiant de génération.

### Les routes publiques : une seule réponse pour tous les refus

```python
def _get_enabled_public_model(public_id, service):
    record = service.get_generation_by_public_id(public_id)
    if record is None or not record.embed_enabled or record.status is not GenerationStatus.DONE:
        raise HTTPException(status_code=404, detail="Ce modèle n'est pas disponible pour l'intégration.")
    ...
```

| Adresse publique | Rôle |
|---|---|
| `GET /public/models/{public_id}` | Nom, catégorie, adresse du GLB |
| `GET /public/models/{public_id}/glb` | Le fichier GLB |

Modèle inconnu, non terminé ou **désactivé** : toujours la **même** 404. Un visiteur ne peut pas
deviner si un modèle existe mais est privé.

## Étape 6.2 — Les catégories (`category_service.py` + `routers/categories.py`)

### Les règles (`category_service.py`)

```python
_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

@staticmethod
def validate_slug(slug: str) -> str:
    value = slug.strip().casefold()
    if len(value) > 64 or not _SLUG_PATTERN.fullmatch(value):
        raise CategoryValidationError("Le slug doit contenir uniquement des lettres minuscules, chiffres et tirets, ...")
    return value
```

- **Slug** = identifiant technique lisible dans une URL : `side-table`, `chair`.
- Le motif accepte `table-basse` ; il refuse `-table`, `Table Basse`, `table--basse`.
- Le **libellé** (`label`) est le texte affiché : 1 à 100 caractères.
- `require_active(slug)` lève `CategoryNotFoundError` si la catégorie est inconnue ou désactivée.

### Les routes (`routers/categories.py`)

| Méthode | Adresse | Rôle |
|---|---|---|
| GET | `/categories?include_inactive=true` | Liste (avec les désactivées si demandé) |
| POST | `/categories` | Crée → 201 |
| PATCH | `/categories/{slug}` | Renomme, change le slug, active ou désactive |
| DELETE | `/categories/{slug}` | Supprime → 204, **409 si un modèle l'utilise** |

```python
def _raise_http_error(error):
    if isinstance(error, CategoryValidationError): raise HTTPException(422, ...)
    if isinstance(error, CategoryNotFoundError):   raise HTTPException(404, ...)
    if isinstance(error, CategoryConflictError):   raise HTTPException(409, ...)
```

Une seule fonction traduit les erreurs métier en codes HTTP : les règles restent dans le service,
le routeur ne fait que **traduire**.

> **Désactiver plutôt que supprimer** : une catégorie désactivée disparaît du formulaire d'envoi,
> mais les modèles qui l'utilisent la gardent.

## Étape 6.3 — Les exemples (`demo_gallery.py`)

`DemoGallery` publie **une liste fixe de 5 GLB réels**, produits pendant les essais de faisabilité,
avec leur photo source quand elle existe.

```python
class DemoGallery:
    """Résout uniquement les cinq noms connus, sans exposer de chemin arbitraire."""
    def list_models(self) -> list[DemoModel]: ...
    def get_model_path(self, model_id: str) -> Path | None: ...
    def get_source_image_path(self, model_id: str) -> Path | None: ...
    @staticmethod
    def is_valid_glb_2(content: bytes) -> bool: ...
```

- Seuls les **identifiants connus** sont acceptés : on ne peut pas demander un fichier quelconque du disque.
- Un exemple dont le fichier manque ou n'est pas un GLB 2.0 valide est **ignoré** (jamais de faux résultat).
- `is_valid_glb_2()` vérifie l'en-tête `glTF`, la version 2 et la structure. Elle est aussi utilisée
  par l'import et par la finition du GLB.
- Ces exemples sont **pré-générés** : ils sont signalés comme tels et ne comptent pas comme une génération en direct.

## À retenir

> Le routeur **lit** la requête, **appelle** le service, **traduit** le résultat en JSON et les erreurs en codes HTTP.
> Il ne contient aucune règle métier.

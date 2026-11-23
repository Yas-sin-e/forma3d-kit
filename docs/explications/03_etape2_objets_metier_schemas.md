# 3. Étape 2 — Les objets métier et la forme du JSON

Fichiers : `backend/app/models.py`, `backend/app/schemas.py`.

Deux fichiers, deux rôles bien séparés :

| Fichier | Ce qu'il décrit | Qui l'utilise | Équivalent Spring |
|---|---|---|---|
| `models.py` | Les objets **internes** du serveur (avec chemins de fichiers) | services, base de données | `@Entity` |
| `schemas.py` | Ce qui **sort** et **entre** par HTTP (sans chemins internes) | routes | DTO |

## Étape 2.1 — Les objets métier (`models.py`)

### Les états d'une génération

```python
class GenerationStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"
```

`StrEnum` = une liste fermée de valeurs qui se comportent aussi comme du texte.
On ne peut pas écrire un état mal orthographié comme `"DONNE"`.

### L'origine d'un modèle

```python
class ModelOrigin(StrEnum):
    GENERATED = "generated"   # créé à partir d'une photo
    IMPORTED = "imported"     # GLB importé depuis l'ordinateur
    EXAMPLE = "example"       # copié depuis les 5 exemples fournis
```

Le jury peut ainsi distinguer honnêtement une **génération en direct** d'un modèle importé.

### La fiche d'une génération

```python
@dataclass(frozen=True, slots=True)
class GenerationRecord:
    id: str                       # UUID interne
    status: GenerationStatus
    filename: str                 # nom affiché, ex. « chaise.jpg »
    content_type: str             # ex. « image/jpeg »
    category: str                 # slug, ex. « chair »
    image_path: Path | None       # photo source sur le disque
    created_at: datetime
    updated_at: datetime
    model_path: Path | None = None        # GLB sur le disque (quand DONE)
    error_message: str | None = None      # quand FAILED
    duration_seconds: float | None = None
    image_warning: str | None = None      # « photo floue », « photo petite »
    origin: ModelOrigin = ModelOrigin.GENERATED
    public_id: str | None = None          # UUID PUBLIC pour l'intégration
    embed_enabled: bool = False           # intégration activée ? NON par défaut
```

- `frozen=True` : on ne modifie jamais une fiche ; on en crée une **copie modifiée** avec
  `dataclasses.replace(record, status=DONE)`. Cela évite qu'un morceau de code change une fiche
  par erreur pendant qu'un autre la lit.
- `slots=True` : objet plus léger en mémoire.
- **Deux identifiants** : `id` reste privé (Studio) ; `public_id` est donné aux sites partenaires.
  Connaître le `public_id` ne donne accès à rien tant que `embed_enabled` vaut `False`.

### Les autres objets

```python
@dataclass(frozen=True, slots=True)
class CategoryRecord:
    id: int
    slug: str          # identifiant technique : « side-table »
    label: str         # libellé affiché : « Table d'appoint »
    is_active: bool    # désactivée = cachée du formulaire d'envoi
    created_at: datetime

@dataclass(frozen=True, slots=True)
class APIKeyRecord:
    id: str
    name: str
    prefix: str        # début lisible de la clé : « f3d_live_AbCd1234 »
    fingerprint: str   # empreinte SHA-256 : la clé elle-même n'est JAMAIS gardée
    created_at: datetime
    revoked: bool = False
```

`ProductCategory` (chaise, tabouret, table d'appoint) liste les trois catégories créées au premier démarrage.

## Étape 2.2 — La forme du JSON (`schemas.py`)

Ce fichier utilise **Pydantic** : une bibliothèque qui vérifie la forme des données.

### Ce que le serveur renvoie pour une génération

```python
class GenerationResponse(BaseModel):
    id: str
    status: Literal["PENDING", "RUNNING", "DONE", "FAILED"]
    filename: str
    category: str
    status_url: str                    # « /models/{id} »
    model_url: str | None = None       # « /models/{id}/glb », seulement si DONE
    error_message: str | None = None
    image_warning: str | None = None
    origin: Literal["generated", "imported", "example"] = "generated"
    public_id: str | None = None
    embed_enabled: bool = False
    ...
```

**Remarque importante :** il n'y a **aucun chemin de fichier** (`image_path`, `model_path`).
Le visiteur reçoit des **adresses HTTP**, jamais l'emplacement des fichiers sur le disque.

### Ce que le serveur accepte

```python
class ModelRenameRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)

class APIKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)

class EmbedIntegrationRequest(BaseModel):
    enabled: bool
```

Si le JSON reçu n'a pas la bonne forme (champ manquant, texte trop long, `"oui"` au lieu de `true`),
FastAPI répond **automatiquement 422** sans même appeler la fonction.

### La clé API : secret montré une seule fois

```python
class APIKeyResponse(BaseModel):          # utilisée pour LISTER les clés
    id: str
    name: str
    prefix: str
    created_at: datetime
    revoked: bool

class APIKeyCreatedResponse(APIKeyResponse):   # utilisée UNE fois, à la création
    key: str
```

La liste ne contient ni la clé ni son empreinte. Seule la réponse de création contient `key`.

### Les autres schémas

| Schéma | Rôle |
|---|---|
| `DemoModelResponse`, `DemoGalleryResponse` | Cartes de la galerie (exemples + modèles enregistrés) |
| `PublicModelResponse` | Informations minimales d'un modèle activé, pour le public |
| `CategoryResponse`, `CategoryCreateRequest`, `CategoryUpdateRequest` | Catégories |
| `ModelCategoryRequest` | Changer la catégorie d'un modèle |
| `APIModelResponse` | Même idée que `GenerationResponse`, avec des adresses `/api/v1/...` |
| `APIIntegrationCodeResponse` | Code `<iframe>` et code widget prêts à copier |

## À retenir

> `models.py` = ce que le serveur **sait**. `schemas.py` = ce qu'il **montre**.
> La fonction `_to_response()` des routeurs fait la traduction de l'un vers l'autre.

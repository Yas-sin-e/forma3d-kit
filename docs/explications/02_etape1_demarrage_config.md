# 2. Étape 1 — Le démarrage du serveur et sa configuration

Fichiers : `backend/requirements.txt`, `backend/README.md`, `backend/app/__init__.py`,
`backend/app/main.py`, `backend/app/config.py`.

## Étape 1.1 — Les bibliothèques (`requirements.txt`)

C'est la liste de courses de Python. `pip install -r requirements.txt` installe tout.

| Bibliothèque | À quoi elle sert | Équivalent connu |
|---|---|---|
| `fastapi` | Transformer des fonctions Python en routes HTTP | Spring Boot (MVC) |
| `uvicorn` | Le serveur HTTP qui exécute FastAPI | Tomcat |
| `pytest` | Lancer les tests | JUnit |
| `python-multipart` | Lire un formulaire qui contient un fichier (photo, GLB) | — |
| `gradio_client` | Appeler un Space d'IA Gradio (TRELLIS, TripoSR) | un client REST |
| `httpx2` | Faire de petites requêtes HTTP (vérifier si le Space est réveillé) | RestTemplate |
| `python-dotenv` | Lire le fichier `backend/.env` | `application.properties` |
| `Pillow` | Modifier une image (mettre la photo au carré) | — |
| `psycopg[binary]` | Parler à PostgreSQL | pilote JDBC |

`backend/README.md` résume comment lancer et tester le backend.

## Étape 1.2 — Les fichiers `__init__.py`

```python
"""Paquet de l'application backend Forma3D Studio."""
```

Un dossier qui contient `__init__.py` devient un **paquet** Python : on peut écrire
`from app.services.generation_service import GenerationService`. Ces fichiers sont vides
(ou presque) dans `app/`, `providers/`, `repositories/`, `routers/`, `services/` et `storage/`.

## Étape 1.3 — La configuration (`config.py`)

### Lire le fichier `.env`

```python
def get_settings() -> Settings:
    load_dotenv(_PROJECT_ROOT / "backend" / ".env", override=False)
    load_dotenv(_PROJECT_ROOT / ".env", override=False)
    ...
    return Settings(
        hf_space_id=os.getenv("HF_SPACE_ID", "").strip(),
        hf_timeout_seconds=int(os.getenv("HF_TIMEOUT_SECONDS", "300")),
        image3d_provider=os.getenv("IMAGE3D_PROVIDER", "triposr").strip().casefold() or "triposr",
        ...
    )
```

- `backend/.env` est lu **en premier**, puis le `.env` de la racine.
- `override=False` : une variable déjà définie dans le terminal (ou par Docker) **garde la priorité**.
- Chaque réglage a une **valeur par défaut** (300 secondes, TripoSR…).
- Les secrets (`HF_TOKEN`, mot de passe) restent dans `.env`, **ignoré par Git**. Le modèle à copier est `.env.example`.

### Vérifier la configuration tout de suite

```python
@dataclass(frozen=True)
class Settings:
    hf_timeout_seconds: int = 300
    hf_max_attempts: int = 2
    api_daily_generation_limit: int = 20
    api_cors_origins: tuple[str, ...] = ()
    image3d_provider: str = "triposr"
    ...
    def __post_init__(self) -> None:
        if self.hf_timeout_seconds <= 0:
            raise ValueError("HF_TIMEOUT_SECONDS doit être positif.")
        if self.image3d_provider not in {"triposr", "trellis"}:
            raise ValueError("IMAGE3D_PROVIDER doit valoir « triposr » ou « trellis ».")
        ...
```

- `@dataclass` crée automatiquement le constructeur à partir des champs.
- `frozen=True` : l'objet ne peut plus être modifié après sa création (immuable).
- `__post_init__` est appelé **juste après** la création : si une valeur est dangereuse, le serveur
  **refuse de démarrer**. Mieux vaut une erreur au démarrage qu'au milieu d'une démonstration.
- Exemples refusés : délai nul, plus de 2 tentatives, fournisseur inconnu, origine `*` dans
  `API_CORS_ORIGINS` (ce qui ouvrirait l'API à tous les sites), URL contenant un mot de passe.

## Étape 1.4 — Le point d'entrée (`main.py`)

C'est **le chef d'orchestre**. Uvicorn l'importe, et il assemble tout le reste.

### a) Créer les objets une seule fois

```python
provider = HuggingFaceSpaceProvider()               # lit aussi la configuration
generation_provider = (
    TrellisSpaceProvider(provider.settings)
    if provider.settings.image3d_provider == "trellis"
    else provider
)
local_storage = LocalStorage()                       # dossier backend/storage
generation_repository = create_repository(storage_root=local_storage.root)
generation_repository.initialize()                   # crée les tables si besoin
```

La variable `IMAGE3D_PROVIDER` choisit le fournisseur : TRELLIS ou TripoSR (défaut).

### b) Créer l'application et ranger les services

```python
app = FastAPI(title="Forma3D Studio API", version="0.1.0", lifespan=lifespan)

app.state.generation_service = GenerationService(
    provider=generation_provider,
    storage=local_storage,
    repository=generation_repository,
)
app.state.category_service = CategoryService(generation_repository)
app.state.api_key_service = APIKeyService(generation_repository)
app.state.owner_auth = OwnerAuthService(signing_key=session_key_from_environment())
```

`app.state` est un **sac d'objets partagés**. Les routes y retrouvent leurs services.
C'est une **injection de dépendances** très simple : le service reçoit ses outils par le constructeur,
il ne les crée pas lui-même. Avantage : un test peut lui donner un faux fournisseur.

### c) Brancher les routeurs (et les protéger)

```python
studio_protection = [Depends(require_owner)]
app.include_router(auth_router)                                         # libre : il faut pouvoir se connecter
app.include_router(models_router, dependencies=studio_protection)       # protégé
app.include_router(categories_router, dependencies=studio_protection)   # protégé
app.include_router(api_keys_router, dependencies=studio_protection)     # protégé
app.include_router(public_models_router)                                # public (modèles activés)
app.include_router(api_v1_router)                                       # protégé par clé API
app.include_router(embed_router)                                        # public (page iframe)
```

`dependencies=[Depends(require_owner)]` applique la vérification de session à **toutes** les routes
d'un routeur d'un coup. Équivalent d'une règle `.authenticated()` de Spring Security sur un préfixe d'URL.

### d) CORS : qui peut appeler l'API depuis un autre site

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(provider.settings.api_cors_origins),   # vide par défaut = personne
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Accept", "Content-Type", "X-API-Key"],
    allow_credentials=False,                                  # aucun cookie envoyé par un autre site
)
```

- **CORS** = règle du navigateur : une page de `boutique.com` ne peut lire une réponse de notre serveur
  que si notre serveur l'autorise explicitement.
- **Middleware** = code exécuté avant chaque requête, comme un filtre de servlet.

### e) Un format d'erreur stable pour l'API externe

```python
@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request, error):
    if request.url.path.startswith("/api/v1/"):
        codes = {401: "unauthorized", 404: "not_found", 429: "rate_limited", ...}
        return JSONResponse({"error": {"code": codes.get(error.status_code, "http_error"),
                                       "message": str(error.detail)}}, ...)
    return JSONResponse({"detail": error.detail}, ...)
```

Un intégrateur reçoit toujours `{"error": {"code": ..., "message": ...}}`. Le Studio garde le format
FastAPI habituel `{"detail": ...}`. Équivalent d'un `@ControllerAdvice`.

### f) Servir la page et les contrôles de santé

| Route | Ce qu'elle renvoie |
|---|---|
| `GET /` | `frontend/index.html` |
| `/static/...` | tout le dossier `frontend/` (CSS, JS, icône) |
| `GET /health` | `{"status": "ok"}` : le serveur tourne (utilisé par Docker et la CI) |
| `GET /health/provider` | `ONLINE`, `OFFLINE` ou `UNCONFIGURED` + un message clair, **jamais l'adresse du serveur 3D** |

### g) Le cycle de vie (`lifespan`)

```python
@asynccontextmanager
async def lifespan(_app):
    generation_repository.initialize()
    logger.info("Base de données PostgreSQL : %s", mask_database_url(os.getenv("DATABASE_URL", "")))
    if not app.state.owner_auth.is_configured():
        logger.warning("FORMA3D_OWNER_PASSWORD est vide ; la connexion au Studio est refusée.")
    yield
```

Le code **avant `yield`** s'exécute au démarrage. Il écrit des **avertissements** (sans bloquer)
si le mot de passe ou le serveur 3D manquent. L'adresse de la base est journalisée avec le mot de
passe remplacé par `***`.

## À retenir

> `main.py` ne contient **aucune règle métier** : il crée les objets, les relie, branche les routes
> et les protections. Les règles sont dans `services/`.

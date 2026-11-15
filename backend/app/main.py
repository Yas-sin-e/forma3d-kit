# Rôle : construit l'API FastAPI, initialise le dépôt SQLite et configure les services.
# Exécution : Uvicorn importe ce module ; FastAPI sert la page, les ressources et les routes.
"""Point d'entrée HTTP et initialisation du dépôt SQLite de Forma3D Studio.

Uvicorn importe ce module au démarrage ; les tests l'importent aussi. FastAPI
expose le contrôle GET /health et initialise le stockage des métadonnées.
"""

# logging (bibliothèque standard) : écrit des messages dans le journal du serveur.
# Ici : avertissements au démarrage. Équivalent de SLF4J / Logback en Java.
import logging
# contextlib (standard) : fabrique des « gestionnaires de contexte » (blocs with).
# asynccontextmanager sert au cycle de vie de l'application (démarrage / arrêt).
from contextlib import asynccontextmanager
# pathlib (standard) : manipule les chemins de fichiers comme des objets (Path / "dossier").
# Équivalent de java.nio.file.Path ; fonctionne sous Windows comme sous Linux.
from pathlib import Path
from typing import AsyncIterator

# FastAPI : le framework web du projet. Il transforme des fonctions Python en routes HTTP,
# valide les données et génère la documentation /docs. Équivalent de Spring Boot (Spring MVC).
# Depends = injection de dépendances ; Request = la requête HTTP reçue.
from fastapi import Depends, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
# Starlette : la boîte à outils HTTP sur laquelle FastAPI est construit (middlewares, erreurs).
# CORSMiddleware gère les appels venant d'autres sites (CORS).
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
# StaticFiles : sert un dossier de fichiers tel quel (ici frontend/ sous /static).
from fastapi.staticfiles import StaticFiles

from app.providers.huggingface import HuggingFaceSpaceProvider
from app.providers.trellis import TrellisSpaceProvider
from app.repositories.sqlite_repository import SQLiteGenerationRepository
from app.routers.api_keys import router as api_keys_router
from app.routers.auth import require_owner
from app.routers.auth import router as auth_router
from app.routers.api_v1 import router as api_v1_router
from app.routers.embed import router as embed_router
from app.routers.categories import router as categories_router
from app.routers.models import public_router as public_models_router
from app.routers.models import router as models_router
from app.services.api_key_service import APIKeyService
from app.services.category_service import CategoryService
from app.services.demo_gallery import DemoGallery
from app.services.generation_service import GenerationService
from app.services.owner_auth import OwnerAuthService, session_key_from_environment
from app.storage.local_storage import LocalStorage

# Racine du dépôt calculée depuis ce fichier : backend/app/main.py -> on remonte de 2 dossiers.
# Le serveur ne dépend donc pas du dossier d'où il est lancé.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
logger = logging.getLogger(__name__)
# Objets créés UNE fois, au chargement du module (comme des beans singleton de Spring).
# Le fournisseur TripoSR lit la configuration (Settings) à sa création.
provider = HuggingFaceSpaceProvider()
# IMAGE3D_PROVIDER choisit le fournisseur de génération ; TripoSR reste le défaut (sous-étape C3).
generation_provider = (
    TrellisSpaceProvider(provider.settings)
    if provider.settings.image3d_provider == "trellis"
    else provider
)
generation_repository = SQLiteGenerationRepository(
    _PROJECT_ROOT / "backend" / "data" / "forma3d.sqlite3"
)
# Le schéma existe aussi pour les tests qui utilisent TestClient sans cycle lifespan.
generation_repository.initialize()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Cycle de vie de l'application : le code avant « yield » s'exécute au démarrage.

    Initialise la base SQLite puis écrit des avertissements (sans bloquer le démarrage) si
    backend/.env, le mot de passe propriétaire ou HF_SPACE_ID manquent.
    Équivalent d'un @PostConstruct / ApplicationRunner de Spring Boot.
    """
    generation_repository.initialize()
    backend_env = _PROJECT_ROOT / "backend" / ".env"
    if not backend_env.is_file():
        logger.warning("backend/.env est absent ; vérifiez le fichier local avant une génération distante.")
    if not app.state.owner_auth.is_configured():
        logger.warning("FORMA3D_OWNER_PASSWORD est vide ; la connexion au Studio est refusée.")
    if provider.settings.image3d_provider == "triposr" and not provider.settings.hf_space_id.strip():
        logger.warning("HF_SPACE_ID est vide ; les générations distantes sont désactivées.")
    yield

# L'application elle-même : c'est cet objet « app » qu'Uvicorn (le serveur HTTP) exécute.
app = FastAPI(
    title="Forma3D Studio API",
    version="0.1.0",
    description="API de base du prototype SaaS 3D Forma3D Studio.",
    lifespan=lifespan,
)
# app.state : sac d'objets partagés de l'application. Les routes y retrouvent les services
# (voir les fonctions get_... des routeurs). C'est notre conteneur d'injection, en très simple.
app.state.generation_service = GenerationService(
    provider=generation_provider,
    storage=LocalStorage(),
    repository=generation_repository,
)
app.state.generation_repository = generation_repository
app.state.category_service = CategoryService(generation_repository)
app.state.api_key_service = APIKeyService(generation_repository)
app.state.api_daily_generation_limit = provider.settings.api_daily_generation_limit
app.state.api_rate_limit_per_minute = provider.settings.api_rate_limit_per_minute
app.state.api_cors_origins = provider.settings.api_cors_origins
app.state.embed_allowed_origins = provider.settings.embed_allowed_origins
app.state.generation_provider = generation_provider
app.state.max_glb_upload_bytes = provider.settings.max_glb_upload_mb * 1024 * 1024
app.state.demo_gallery = DemoGallery()
app.state.owner_auth = OwnerAuthService(signing_key=session_key_from_environment())

# Routes du Studio : protégées par la session de la propriétaire (cookie signé, étape 5f).
# dependencies=[Depends(require_owner)] applique la vérification de session à TOUTES les routes
# d'un routeur. Équivalent d'une règle .authenticated() de Spring Security sur un préfixe d'URL.
studio_protection = [Depends(require_owner)]
app.include_router(auth_router)
app.include_router(models_router, dependencies=studio_protection)
app.include_router(categories_router, dependencies=studio_protection)
app.include_router(api_keys_router, dependencies=studio_protection)
# Routes publiques ou authentifiées autrement : /public (modèle activé), /api/v1 (X-API-Key), /embed.
app.include_router(public_models_router)
app.include_router(api_v1_router)
app.include_router(embed_router)
# Middleware CORS : code exécuté avant chaque requête. Il n'autorise que les origines listées
# dans API_CORS_ORIGINS (aucune par défaut), sans cookies (allow_credentials=False).
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(provider.settings.api_cors_origins),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Accept", "Content-Type", "X-API-Key"],
    expose_headers=["Retry-After"],
    allow_credentials=False,
    max_age=600,
)


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
    """Gestionnaire global des erreurs HTTP (équivalent d'un @ControllerAdvice de Spring).

    Pour /api/v1 : renvoie toujours {"error": {"code": ..., "message": ...}} (contrat stable
    pour les intégrateurs). Pour le Studio : garde le format FastAPI {"detail": ...}.
    Les en-têtes de l'erreur (par exemple Retry-After) sont conservés.
    """
    if request.url.path == "/api/v1" or request.url.path.startswith("/api/v1/"):
        codes = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            409: "conflict",
            413: "payload_too_large",
            415: "unsupported_media_type",
            422: "invalid_request",
            429: "rate_limited",
        }
        return JSONResponse(
            {"error": {"code": codes.get(error.status_code, "http_error"), "message": str(error.detail)}},
            status_code=error.status_code,
            headers=error.headers,
        )
    return JSONResponse(
        {"detail": error.detail}, status_code=error.status_code, headers=error.headers
    )


# mount : branche une sous-application. Tout le dossier frontend/ est servi sous /static.
app.mount(
    "/static",
    StaticFiles(directory=_PROJECT_ROOT / "frontend"),
    name="frontend-static",
)


@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    """Sert la page HTML du Sprint 1 depuis le dossier frontend."""
    return FileResponse(_PROJECT_ROOT / "frontend" / "index.html", media_type="text/html")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Retourne un statut simple pour vérifier que l'API répond."""
    return {"status": "ok"}


@app.get("/health/provider", tags=["health"])
def provider_health_check(request: Request) -> dict[str, str]:
    """Retourne la disponibilité du fournisseur 3D sans révéler l'URL ou les détails réseau.

    Retour : {"status": "ONLINE" | "OFFLINE" | "UNCONFIGURED", "message": texte lisible}.
    Le message diffère selon le fournisseur (Colab pour TripoSR, Space pour TRELLIS).
    """
    # On lit le fournisseur réellement utilisé (TripoSR ou TRELLIS), rangé dans app.state.
    generation_provider = request.app.state.generation_provider
    status = generation_provider.health_status()
    if status == "OFFLINE" and isinstance(generation_provider, TrellisSpaceProvider):
        message = (
            "Le Space TRELLIS est en veille, en panne ou indisponible. "
            "Réessayez plus tard ; le quota GPU gratuit est limité par jour."
        )
    elif status == "OFFLINE":
        message = (
            "Le serveur 3D (Colab) est arrêté ou son lien a expiré (72 h). "
            "Relance le notebook, copie la nouvelle ligne dans backend/.env, redémarre le serveur."
        )
    elif status == "UNCONFIGURED":
        message = (
            "HF_SPACE_ID est vide. Configure le serveur dans backend/.env, "
            "puis redémarre le serveur."
        )
    else:
        message = "Le serveur 3D est joignable."
    return {"status": status, "message": message}

# Rôle : construit l'API FastAPI, initialise le dépôt PostgreSQL et configure les services.
# Exécution : Uvicorn importe ce module ; FastAPI sert la page, les ressources et les routes.
"""Point d'entrée HTTP et initialisation du dépôt PostgreSQL de Forma3D Studio.

Uvicorn importe ce module au démarrage ; les tests l'importent aussi. FastAPI
expose le contrôle GET /health et initialise le stockage des métadonnées.
"""

# logging (bibliothèque standard) : écrit des messages dans le journal du serveur.
# Ici : avertissements au démarrage. Équivalent de SLF4J / Logback en Java.
import logging
# os (standard) : lit DATABASE_URL pour journaliser l'adresse de la base (mot de passe masqué).
import os
# contextlib (standard) : fabrique des « gestionnaires de contexte » (blocs with).
# asynccontextmanager sert au cycle de vie de l'application (démarrage / arrêt).
from contextlib import asynccontextmanager
# pathlib (standard) : manipule les chemins de fichiers comme des objets (Path / "dossier").
# Équivalent de java.nio.file.Path ; fonctionne sous Windows comme sous Linux.
from pathlib import Path
# AsyncIterator : type de retour de la fonction lifespan (générateur asynchrone).
from typing import AsyncIterator

# FastAPI : le framework web du projet. Il transforme des fonctions Python en routes HTTP,
# valide les données et génère la documentation /docs. Équivalent de Spring Boot (Spring MVC).
# Depends = injection de dépendances ; Request = la requête HTTP reçue.
from fastapi import Depends, FastAPI, Request
# FileResponse renvoie un fichier (index.html) ; JSONResponse renvoie un objet JSON.
from fastapi.responses import FileResponse, JSONResponse
# Starlette : la boîte à outils HTTP sur laquelle FastAPI est construit (middlewares, erreurs).
# CORSMiddleware gère les appels venant d'autres sites (CORS).
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
# StaticFiles : sert un dossier de fichiers tel quel (ici frontend/ sous /static).
from fastapi.staticfiles import StaticFiles

# Fournisseur TripoSR (Colab ou Space) : sert aussi de porteur de la configuration Settings.
from app.providers.huggingface import HuggingFaceSpaceProvider
# Fournisseur TRELLIS, utilisé quand IMAGE3D_PROVIDER=trellis.
from app.providers.trellis import TrellisSpaceProvider
# Fabrique du dépôt PostgreSQL et fonction qui masque le mot de passe de DATABASE_URL.
from app.repositories.factory import create_repository, mask_database_url
# Routeur des clés API du Studio (/api-keys).
from app.routers.api_keys import router as api_keys_router
# Dépendance qui vérifie la session de la propriétaire.
from app.routers.auth import require_owner
# Routeur de connexion / déconnexion du Studio (/auth).
from app.routers.auth import router as auth_router
# Routeur de l'API externe versionnée (/api/v1), protégée par clé API.
from app.routers.api_v1 import router as api_v1_router
# Routeur de la page d'intégration (/embed) affichée dans une iframe.
from app.routers.embed import router as embed_router
# Routeur des catégories du Studio (/categories).
from app.routers.categories import router as categories_router
# Routeur public : lecture d'un modèle activé par son UUID public.
from app.routers.models import public_router as public_models_router
# Routeur des modèles du Studio (/models).
from app.routers.models import router as models_router
# Service qui crée, vérifie et révoque les clés API.
from app.services.api_key_service import APIKeyService
# Service des catégories (règles de création, renommage, suppression).
from app.services.category_service import CategoryService
# Service de la galerie d'exemples pré-générés.
from app.services.demo_gallery import DemoGallery
# Service qui orchestre une génération (photo -> fournisseur -> GLB).
from app.services.generation_service import GenerationService
# Service d'authentification de la propriétaire et lecture de la clé de signature des sessions.
from app.services.owner_auth import OwnerAuthService, session_key_from_environment
# Stockage des fichiers (photos et GLB) sur le disque local.
from app.storage.local_storage import LocalStorage

# Racine du dépôt calculée depuis ce fichier : backend/app/main.py -> on remonte de 2 dossiers.
# Le serveur ne dépend donc pas du dossier d'où il est lancé.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Journal de ce module ; __name__ vaut « app.main ».
logger = logging.getLogger(__name__)
# Objets créés UNE fois, au chargement du module (comme des beans singleton de Spring).
# Le fournisseur TripoSR lit la configuration (Settings) à sa création.
# Crée le fournisseur TripoSR ; il lit la configuration au passage.
provider = HuggingFaceSpaceProvider()
# IMAGE3D_PROVIDER choisit le fournisseur de génération ; TripoSR reste le défaut (sous-étape C3).
# Choisit le fournisseur réellement utilisé pour générer.
generation_provider = (
    # Si la configuration demande TRELLIS, on crée ce fournisseur avec la même configuration...
    TrellisSpaceProvider(provider.settings)
    # ...condition : la variable IMAGE3D_PROVIDER vaut « trellis ».
    if provider.settings.image3d_provider == "trellis"
    # ...sinon on garde le fournisseur TripoSR.
    else provider
)
# PostgreSQL est la seule base : DATABASE_URL (postgresql://...) est obligatoire, sinon erreur claire.
# Un seul dossier de stockage partagé : le dépôt y enregistre des chemins relatifs (portables Windows/Linux).
# Crée le stockage local (dossier backend/storage par défaut).
local_storage = LocalStorage()
# Crée le dépôt PostgreSQL ; il connaît le dossier de stockage pour enregistrer des chemins relatifs.
generation_repository = create_repository(storage_root=local_storage.root)
# Le schéma existe aussi pour les tests qui utilisent TestClient sans cycle lifespan.
# Crée les tables et les catégories initiales si elles manquent (idempotent).
generation_repository.initialize()


# Transforme la fonction ci-dessous en gestionnaire de contexte asynchrone pour FastAPI.
@asynccontextmanager
# Fonction appelée par FastAPI au démarrage (avant yield) et à l'arrêt (après yield).
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Cycle de vie de l'application : le code avant « yield » s'exécute au démarrage.

    Initialise la base PostgreSQL puis écrit des avertissements (sans bloquer le démarrage) si
    backend/.env, le mot de passe propriétaire ou HF_SPACE_ID manquent.
    Équivalent d'un @PostConstruct / ApplicationRunner de Spring Boot.
    """
    # Revérifie le schéma au démarrage réel du serveur.
    generation_repository.initialize()
    # On journalise l'adresse de la base avec le mot de passe masqué (jamais en clair).
    # Journalise l'adresse de la base, mot de passe remplacé par ***.
    logger.info("Base de données PostgreSQL : %s", mask_database_url(os.getenv("DATABASE_URL", "")))
    # Chemin attendu du fichier de secrets local backend/.env.
    backend_env = _PROJECT_ROOT / "backend" / ".env"
    # Si le fichier n'existe pas...
    if not backend_env.is_file():
        # ...on prévient sans bloquer le démarrage.
        logger.warning("backend/.env est absent ; vérifiez le fichier local avant une génération distante.")
    # Si aucun mot de passe propriétaire n'est configuré...
    if not app.state.owner_auth.is_configured():
        # ...on prévient : personne ne pourra se connecter au Studio.
        logger.warning("FORMA3D_OWNER_PASSWORD est vide ; la connexion au Studio est refusée.")
    # Si TripoSR est choisi mais qu'aucun serveur 3D n'est configuré...
    if provider.settings.image3d_provider == "triposr" and not provider.settings.hf_space_id.strip():
        # ...on prévient : les générations distantes sont impossibles.
        logger.warning("HF_SPACE_ID est vide ; les générations distantes sont désactivées.")
    # Rend la main à FastAPI : le serveur traite les requêtes jusqu'à son arrêt.
    yield

# L'application elle-même : c'est cet objet « app » qu'Uvicorn (le serveur HTTP) exécute.
# Crée l'application FastAPI.
app = FastAPI(
    # Titre affiché dans la documentation /docs.
    title="Forma3D Studio API",
    # Version de l'API affichée dans /docs.
    version="0.1.0",
    # Description affichée dans /docs.
    description="API de base du prototype SaaS 3D Forma3D Studio.",
    # Branche la fonction de cycle de vie définie plus haut.
    lifespan=lifespan,
)
# app.state : sac d'objets partagés de l'application. Les routes y retrouvent les services
# (voir les fonctions get_... des routeurs). C'est notre conteneur d'injection, en très simple.
# Range le service de génération, construit avec ses trois dépendances.
app.state.generation_service = GenerationService(
    # Fournisseur 3D choisi (TripoSR ou TRELLIS).
    provider=generation_provider,
    # Stockage des fichiers.
    storage=local_storage,
    # Dépôt des métadonnées.
    repository=generation_repository,
)
# Range le dépôt pour les routes qui lisent directement la base.
app.state.generation_repository = generation_repository
# Range le service des catégories.
app.state.category_service = CategoryService(generation_repository)
# Range le service des clés API.
app.state.api_key_service = APIKeyService(generation_repository)
# Quota journalier de créations par clé API (lu dans .env).
app.state.api_daily_generation_limit = provider.settings.api_daily_generation_limit
# Limite de requêtes par minute et par clé API.
app.state.api_rate_limit_per_minute = provider.settings.api_rate_limit_per_minute
# Origines autorisées à lire l'API depuis un navigateur (CORS).
app.state.api_cors_origins = provider.settings.api_cors_origins
# Origines autorisées à afficher /embed dans une iframe (CSP frame-ancestors).
app.state.embed_allowed_origins = provider.settings.embed_allowed_origins
# Fournisseur réellement utilisé, lu par /health/provider.
app.state.generation_provider = generation_provider
# Taille maximale d'un GLB importé, convertie de Mo en octets.
app.state.max_glb_upload_bytes = provider.settings.max_glb_upload_mb * 1024 * 1024
# Service de la galerie d'exemples.
app.state.demo_gallery = DemoGallery()
# Service d'authentification, avec la clé qui signe les cookies de session.
app.state.owner_auth = OwnerAuthService(signing_key=session_key_from_environment())

# Routes du Studio : protégées par la session de la propriétaire (cookie signé, étape 5f).
# dependencies=[Depends(require_owner)] applique la vérification de session à TOUTES les routes
# d'un routeur. Équivalent d'une règle .authenticated() de Spring Security sur un préfixe d'URL.
studio_protection = [Depends(require_owner)]
# Branche les routes /auth (connexion), sans protection : il faut pouvoir se connecter.
app.include_router(auth_router)
# Branche les routes /models, protégées par la session.
app.include_router(models_router, dependencies=studio_protection)
# Branche les routes /categories, protégées par la session.
app.include_router(categories_router, dependencies=studio_protection)
# Branche les routes /api-keys, protégées par la session.
app.include_router(api_keys_router, dependencies=studio_protection)
# Routes publiques ou authentifiées autrement : /public (modèle activé), /api/v1 (X-API-Key), /embed.
# Branche la lecture publique d'un modèle activé.
app.include_router(public_models_router)
# Branche l'API externe /api/v1 (la clé API est vérifiée dans le routeur).
app.include_router(api_v1_router)
# Branche la page /embed.
app.include_router(embed_router)
# Middleware CORS : code exécuté avant chaque requête. Il n'autorise que les origines listées
# dans API_CORS_ORIGINS (aucune par défaut), sans cookies (allow_credentials=False).
# Ajoute le middleware CORS à l'application.
app.add_middleware(
    # Classe du middleware fournie par Starlette.
    CORSMiddleware,
    # Liste des origines autorisées (vide par défaut = aucun site externe).
    allow_origins=list(provider.settings.api_cors_origins),
    # Méthodes HTTP autorisées depuis un autre site.
    allow_methods=["GET", "POST", "OPTIONS"],
    # En-têtes autorisés ; X-API-Key porte la clé de l'intégrateur.
    allow_headers=["Accept", "Content-Type", "X-API-Key"],
    # En-tête lisible par le navigateur du client (délai avant de réessayer).
    expose_headers=["Retry-After"],
    # Pas de cookies envoyés par un autre site : l'API externe s'authentifie par clé.
    allow_credentials=False,
    # Le navigateur garde la réponse de pré-vérification (preflight) 600 secondes.
    max_age=600,
)


# Enregistre cette fonction comme gestionnaire de toutes les erreurs HTTP.
@app.exception_handler(StarletteHTTPException)
# Reçoit la requête et l'erreur ; renvoie une réponse JSON.
async def handle_http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
    """Gestionnaire global des erreurs HTTP (équivalent d'un @ControllerAdvice de Spring).

    Pour /api/v1 : renvoie toujours {"error": {"code": ..., "message": ...}} (contrat stable
    pour les intégrateurs). Pour le Studio : garde le format FastAPI {"detail": ...}.
    Les en-têtes de l'erreur (par exemple Retry-After) sont conservés.
    """
    # Si l'URL appartient à l'API externe /api/v1...
    if request.url.path == "/api/v1" or request.url.path.startswith("/api/v1/"):
        # ...table de correspondance statut HTTP -> code d'erreur stable.
        codes = {
            # Requête mal formée.
            400: "bad_request",
            # Clé API absente ou invalide.
            401: "unauthorized",
            # Accès refusé.
            403: "forbidden",
            # Ressource introuvable.
            404: "not_found",
            # Conflit (par exemple un doublon).
            409: "conflict",
            # Fichier trop volumineux.
            413: "payload_too_large",
            # Format de fichier non pris en charge.
            415: "unsupported_media_type",
            # Données invalides.
            422: "invalid_request",
            # Trop de requêtes (quota ou limite de débit).
            429: "rate_limited",
        }
        # Renvoie le format d'erreur de l'API externe.
        return JSONResponse(
            # {"error": {"code": ..., "message": ...}} ; code générique si le statut n'est pas dans la table.
            {"error": {"code": codes.get(error.status_code, "http_error"), "message": str(error.detail)}},
            # Même statut HTTP que l'erreur d'origine.
            status_code=error.status_code,
            # Conserve les en-têtes (par exemple Retry-After).
            headers=error.headers,
        )
    # Pour le Studio : format FastAPI habituel {"detail": ...}.
    return JSONResponse(
        {"detail": error.detail}, status_code=error.status_code, headers=error.headers
    )


# mount : branche une sous-application. Tout le dossier frontend/ est servi sous /static.
# Branche le dossier frontend sous l'URL /static.
app.mount(
    # Préfixe d'URL.
    "/static",
    # Dossier servi : frontend/ à la racine du dépôt.
    StaticFiles(directory=_PROJECT_ROOT / "frontend"),
    # Nom interne de ce montage.
    name="frontend-static",
)


# Route GET / ; masquée de la documentation /docs.
@app.get("/", include_in_schema=False)
# Fonction qui renvoie la page du Studio.
def serve_frontend() -> FileResponse:
    """Sert la page HTML du Sprint 1 depuis le dossier frontend."""
    # Renvoie frontend/index.html avec le type HTML.
    return FileResponse(_PROJECT_ROOT / "frontend" / "index.html", media_type="text/html")


# Route GET /health, rangée sous l'étiquette « health » dans /docs.
@app.get("/health", tags=["health"])
# Fonction du contrôle de santé de l'API.
def health_check() -> dict[str, str]:
    """Retourne un statut simple pour vérifier que l'API répond."""
    # Répond {"status": "ok"} : le serveur tourne (utilisé par Docker et la CI).
    return {"status": "ok"}


# Route GET /health/provider : état du fournisseur 3D.
@app.get("/health/provider", tags=["health"])
# Reçoit la requête pour accéder à app.state.
def provider_health_check(request: Request) -> dict[str, str]:
    """Retourne la disponibilité du fournisseur 3D sans révéler l'URL ou les détails réseau.

    Retour : {"status": "ONLINE" | "OFFLINE" | "UNCONFIGURED", "message": texte lisible}.
    Le message diffère selon le fournisseur (Colab pour TripoSR, Space pour TRELLIS).
    """
    # On lit le fournisseur réellement utilisé (TripoSR ou TRELLIS), rangé dans app.state.
    # Récupère le fournisseur choisi au démarrage.
    generation_provider = request.app.state.generation_provider
    # Lui demande son état : ONLINE, OFFLINE ou UNCONFIGURED.
    status = generation_provider.health_status()
    # Cas : TRELLIS hors ligne.
    if status == "OFFLINE" and isinstance(generation_provider, TrellisSpaceProvider):
        # Message adapté au Space TRELLIS (veille, panne, quota).
        message = (
            "Le Space TRELLIS est en veille, en panne ou indisponible. "
            "Réessayez plus tard ; le quota GPU gratuit est limité par jour."
        )
    # Cas : TripoSR (Colab) hors ligne.
    elif status == "OFFLINE":
        # Message adapté à Colab (lien expiré, notebook arrêté).
        message = (
            "Le serveur 3D (Colab) est arrêté ou son lien a expiré (72 h). "
            "Relance le notebook, copie la nouvelle ligne dans backend/.env, redémarre le serveur."
        )
    # Cas : aucun serveur configuré.
    elif status == "UNCONFIGURED":
        # Message qui indique quoi configurer.
        message = (
            "HF_SPACE_ID est vide. Configure le serveur dans backend/.env, "
            "puis redémarre le serveur."
        )
    # Sinon : le serveur 3D est joignable.
    else:
        # Message de succès.
        message = "Le serveur 3D est joignable."
    # Renvoie l'état et le message, sans jamais l'adresse du serveur.
    return {"status": status, "message": message}

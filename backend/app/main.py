# Rôle : construit l'API FastAPI, initialise le dépôt SQLite et configure les services.
# Exécution : Uvicorn importe ce module ; FastAPI sert la page, les ressources et les routes.
"""Point d'entrée HTTP et initialisation du dépôt SQLite de Forma3D Studio.

Uvicorn importe ce module au démarrage ; les tests l'importent aussi. FastAPI
expose le contrôle GET /health et initialise le stockage des métadonnées.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.providers.huggingface import HuggingFaceSpaceProvider
from app.repositories.sqlite_repository import SQLiteGenerationRepository
from app.routers.models import router as models_router
from app.services.demo_gallery import DemoGallery
from app.services.generation_service import GenerationService
from app.storage.local_storage import LocalStorage

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
logger = logging.getLogger(__name__)
provider = HuggingFaceSpaceProvider()
generation_repository = SQLiteGenerationRepository(
    _PROJECT_ROOT / "backend" / "data" / "forma3d.sqlite3"
)
# Le schéma existe aussi pour les tests qui utilisent TestClient sans cycle lifespan.
generation_repository.initialize()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialise l'historique et signale l'absence de configuration sensible."""
    generation_repository.initialize()
    backend_env = _PROJECT_ROOT / "backend" / ".env"
    if not backend_env.is_file():
        logger.warning("backend/.env est absent ; vérifiez le fichier local avant une génération distante.")
    if not provider.settings.hf_space_id.strip():
        logger.warning("HF_SPACE_ID est vide ; les générations distantes sont désactivées.")
    yield

app = FastAPI(
    title="Forma3D Studio API",
    version="0.1.0",
    description="API de base du prototype SaaS 3D Forma3D Studio.",
    lifespan=lifespan,
)
app.state.generation_service = GenerationService(
    provider=provider,
    storage=LocalStorage(),
    repository=generation_repository,
)
app.state.generation_repository = generation_repository
app.state.generation_provider = provider
app.state.demo_gallery = DemoGallery()

app.include_router(models_router)
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
    """Retourne la disponibilité sans révéler l'URL ou les détails réseau."""
    status = request.app.state.generation_provider.health_status()
    if status == "OFFLINE":
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

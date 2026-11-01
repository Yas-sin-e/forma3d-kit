# Rôle : construit l'API FastAPI, sert le frontend et configure les services du Sprint 1.
# Exécution : Uvicorn importe ce module ; FastAPI sert la page, les ressources et les routes.
"""Point d'entrée HTTP de Forma3D Studio.

Ce module crée l'application FastAPI et expose le contrôle GET /health.
Uvicorn l'importe au démarrage du serveur ; les tests l'importent aussi.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.providers.huggingface import HuggingFaceSpaceProvider
from app.routers.models import router as models_router
from app.services.demo_gallery import DemoGallery
from app.services.generation_service import GenerationService
from app.storage.local_storage import LocalStorage

_PROJECT_ROOT = Path(__file__).resolve().parents[2]

app = FastAPI(
    title="Forma3D Studio API",
    version="0.1.0",
    description="API de base du prototype SaaS 3D Forma3D Studio.",
)
app.state.generation_service = GenerationService(
    provider=HuggingFaceSpaceProvider(),
    storage=LocalStorage(),
)
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

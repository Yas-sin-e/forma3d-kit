# Rôle : expose l’API d’intégration versionnée pour créer et consulter des modèles.
# Exécution : les intégrateurs envoient X-API-Key ; les services internes conservent la logique métier.
"""Routes versionnées de l’API destinée aux sites intégrateurs."""

from datetime import UTC, datetime, timedelta
from html import escape
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse

from app.models import APIKeyRecord, GenerationRecord, GenerationStatus
from app.routers.api_keys import get_api_key_service, require_api_key
from app.routers.categories import get_category_service
from app.routers.models import get_generation_service
from app.schemas import APIIntegrationCodeResponse, APIModelResponse
from app.services.api_key_service import APIKeyService
from app.services.category_service import CategoryNotFoundError, CategoryService
from app.services.generation_service import GenerationService
from app.services.upload_validator import MAX_UPLOAD_BYTES, UploadValidationError, UploadValidator

router = APIRouter(prefix="/api/v1", tags=["integration-v1"])


def require_api_v1_key(
    request: Request,
    key: Annotated[APIKeyRecord, Depends(require_api_key)],
    key_service: Annotated[APIKeyService, Depends(get_api_key_service)],
) -> APIKeyRecord:
    """Authentifie la clé puis applique une limite glissante aux routes versionnées."""
    reason = key_service.consume_rate_limit(
        key, request.app.state.api_rate_limit_per_minute
    )
    if reason == "revoked":
        raise HTTPException(status_code=401, detail="Clé API absente, invalide ou révoquée.")
    if reason == "rate_limit":
        raise HTTPException(
            status_code=429,
            detail="Limite de débit atteinte ; réessayez dans une minute.",
            headers={"Retry-After": "60"},
        )
    return key


def _model_response(record: GenerationRecord) -> APIModelResponse:
    """Construit un état externe sans exposer les chemins locaux ni les URL internes."""
    return APIModelResponse(
        id=record.id,
        status=record.status.value,
        filename=record.filename,
        category=record.category,
        created_at=record.created_at,
        updated_at=record.updated_at,
        status_url=f"/api/v1/models/{record.id}",
        model_url=f"/api/v1/models/{record.id}/glb" if record.status is GenerationStatus.DONE else None,
        error_message=record.error_message,
        duration_seconds=record.duration_seconds,
        public_id=record.public_id,
        embed_enabled=record.embed_enabled,
    )


@router.post("/models", response_model=APIModelResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_model(
    file: Annotated[UploadFile, File(description="Photo JPG, PNG ou WebP, jusqu’à 10 Mo.")],
    category: Annotated[str, Form(description="Slug d’une catégorie active.")],
    background_tasks: BackgroundTasks,
    _key: Annotated[APIKeyRecord, Depends(require_api_v1_key)],
    request: Request,
    service: Annotated[GenerationService, Depends(get_generation_service)],
    category_service: Annotated[CategoryService, Depends(get_category_service)],
    key_service: Annotated[APIKeyService, Depends(get_api_key_service)],
) -> APIModelResponse:
    """Valide une photo, consomme le quota et relance le service de génération existant."""
    try:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        validated = UploadValidator.validate(file.filename, file.content_type, content)
    except UploadValidationError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    finally:
        await file.close()

    try:
        category_service.require_active(category)
    except CategoryNotFoundError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error

    reason = key_service.consume_daily_quota(
        _key, request.app.state.api_daily_generation_limit
    )
    if reason == "revoked":
        raise HTTPException(status_code=401, detail="Clé API absente, invalide ou révoquée.")
    if reason == "daily_quota":
        now = datetime.now(UTC)
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        wait_seconds = max(1, int((tomorrow - now).total_seconds()))
        raise HTTPException(
            status_code=429,
            detail="Quota quotidien de créations atteint pour cette clé.",
            headers={"Retry-After": str(wait_seconds)},
        )

    try:
        record = service.create_generation(validated, content, category)
    except ValueError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    background_tasks.add_task(service.run, record.id)
    return _model_response(record)


@router.get("/models/{generation_id}", response_model=APIModelResponse)
def get_model_status(
    generation_id: str,
    _key: Annotated[APIKeyRecord, Depends(require_api_v1_key)],
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> APIModelResponse:
    """Retourne l’état d’un modèle sans révéler de chemins locaux."""
    record = service.get_generation(generation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    return _model_response(record)


@router.get("/models/{generation_id}/glb")
def download_model(
    generation_id: str,
    _key: Annotated[APIKeyRecord, Depends(require_api_v1_key)],
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> FileResponse:
    """Télécharge le GLB après une génération terminée."""
    record = service.get_generation(generation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    if record.status is not GenerationStatus.DONE:
        raise HTTPException(status_code=409, detail="Le modèle n’est pas encore prêt.")
    path = service.get_model_path(generation_id)
    if path is None:
        raise HTTPException(status_code=404, detail="Le fichier GLB est introuvable.")
    return FileResponse(path, media_type="model/gltf-binary", filename=record.filename)


@router.get("/models/{generation_id}/integration-code", response_model=APIIntegrationCodeResponse)
def get_integration_code(
    generation_id: str,
    request: Request,
    _key: Annotated[APIKeyRecord, Depends(require_api_v1_key)],
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> APIIntegrationCodeResponse:
    """Retourne un iframe uniquement pour un modèle terminé dont l’intégration est activée."""
    record = service.get_generation(generation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    if record.status is not GenerationStatus.DONE:
        raise HTTPException(status_code=409, detail="Le modèle n’est pas encore prêt.")
    if not record.embed_enabled or not record.public_id:
        raise HTTPException(status_code=403, detail="Activez l’intégration sur la fiche du modèle avant de copier son code.")
    base_url = str(request.base_url).rstrip("/")
    source = escape(f"{base_url}/embed/{record.public_id}", quote=True)
    title = escape(Path(record.filename).stem, quote=True)
    iframe = (
        f'<iframe src="{source}" title="Aperçu 3D : {title}" width="100%" height="480" '
        'loading="lazy" style="border:0" allow="fullscreen; xr-spatial-tracking"></iframe>'
    )
    widget_script = escape(f"{base_url}/static/widget.js?v=20261111-5d", quote=True)
    widget = (
        f'<script src="{widget_script}" defer></script>\n'
        f'<forma3d-viewer model="{record.public_id}" height="480"></forma3d-viewer>'
    )
    return APIIntegrationCodeResponse(
        public_id=record.public_id, iframe_html=iframe, widget_html=widget
    )

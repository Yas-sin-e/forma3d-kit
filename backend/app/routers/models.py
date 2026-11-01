# Rôle : expose l'envoi, le suivi, les téléchargements et la galerie des GLB autorisés.
# Exécution : FastAPI appelle ces routes aux requêtes photo, statut ou modèles d'essai.
"""Routes HTTP associées aux modèles 3D et aux images reçues."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app.models import GenerationRecord, GenerationStatus
from app.schemas import DemoGalleryResponse, GenerationResponse
from app.services.generation_service import GenerationService
from app.services.demo_gallery import DemoGallery
from app.services.upload_validator import (
    MAX_UPLOAD_BYTES,
    UploadValidationError,
    UploadValidator,
)

router = APIRouter(prefix="/models", tags=["models"])


def get_generation_service(request: Request) -> GenerationService:
    """Récupère le service unique créé au démarrage de l'application."""
    return request.app.state.generation_service


def get_demo_gallery(request: Request) -> DemoGallery:
    """Récupère le catalogue local borné aux cinq modèles de faisabilité."""
    return request.app.state.demo_gallery


def _to_response(record: GenerationRecord) -> GenerationResponse:
    """Transforme le modèle interne en réponse sans exposer les chemins locaux."""
    is_done = record.status is GenerationStatus.DONE
    return GenerationResponse(
        id=record.id,
        status=record.status.value,
        filename=record.filename,
        content_type=record.content_type,
        created_at=record.created_at,
        updated_at=record.updated_at,
        status_url=f"/models/{record.id}",
        model_url=f"/models/{record.id}/glb" if is_done else None,
        error_message=record.error_message,
    )


@router.post("", response_model=GenerationResponse, status_code=202)
async def create_model_generation(
    file: Annotated[UploadFile, File(description="Photo JPG, PNG ou WebP, jusqu'à 10 Mo.")],
    background_tasks: BackgroundTasks,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> GenerationResponse:
    """Valide et stocke la photo puis démarre une tâche de génération en arrière-plan."""
    try:
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        validated = UploadValidator.validate(
            filename=file.filename,
            content_type=file.content_type,
            content=content,
        )
    except UploadValidationError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=error.detail,
        ) from error
    finally:
        await file.close()

    record = service.create_generation(validated, content)
    background_tasks.add_task(service.run, record.id)
    return _to_response(record)


@router.get("/gallery", response_model=DemoGalleryResponse)
def list_demo_models(
    gallery: Annotated[DemoGallery, Depends(get_demo_gallery)],
) -> DemoGalleryResponse:
    """Liste uniquement les GLB de faisabilité autorisés et encore valides."""
    return DemoGalleryResponse(items=gallery.list_models())


@router.get("/gallery/{model_id}")
def download_demo_model(
    model_id: str,
    gallery: Annotated[DemoGallery, Depends(get_demo_gallery)],
) -> FileResponse:
    """Sert un GLB réel de démonstration par identifiant autorisé."""
    model_path = gallery.get_model_path(model_id)
    if model_path is None:
        raise HTTPException(status_code=404, detail="Modèle de démonstration introuvable.")
    return FileResponse(
        path=model_path,
        media_type="model/gltf-binary",
        filename=model_path.name,
    )


@router.get("/gallery/{model_id}/source-image")
def serve_demo_source_image(
    model_id: str,
    gallery: Annotated[DemoGallery, Depends(get_demo_gallery)],
) -> FileResponse:
    """Sert la photo source d'un modèle autorisé seulement si elle est présente."""
    image_path = gallery.get_source_image_path(model_id)
    if image_path is None:
        raise HTTPException(status_code=404, detail="Photo source introuvable.")
    media_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    return FileResponse(path=image_path, media_type=media_types[image_path.suffix.casefold()])


@router.get("/{generation_id}", response_model=GenerationResponse)
def get_model_generation(
    generation_id: str,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> GenerationResponse:
    """Retourne l'état connu d'une génération sans déclencher de nouveau travail."""
    record = service.get_generation(generation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Génération introuvable.")
    return _to_response(record)


@router.get("/{generation_id}/glb")
def download_model_glb(
    generation_id: str,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> FileResponse:
    """Télécharge le GLB seulement après l'état DONE."""
    record = service.get_generation(generation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Génération introuvable.")
    if record.status is not GenerationStatus.DONE:
        raise HTTPException(
            status_code=409,
            detail="Le modèle n'est pas encore disponible ; consultez son état.",
        )
    model_path = service.get_model_path(generation_id)
    if model_path is None:
        raise HTTPException(
            status_code=500,
            detail="Le modèle terminé est absent du stockage local.",
        )
    return FileResponse(
        path=model_path,
        media_type="model/gltf-binary",
        filename=f"{generation_id}.glb",
    )

# Rôle : expose l'envoi, le suivi, les téléchargements et la galerie des GLB autorisés.
# Exécution : FastAPI appelle ces routes aux requêtes photo, statut ou modèles d'essai.
"""Routes HTTP associées aux modèles 3D et aux images reçues."""

from pathlib import Path
from typing import Annotated

# FastAPI : UploadFile/File/Form lisent un formulaire multipart (fichier + champs texte) ;
# BackgroundTasks exécute un travail après la réponse.
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
# FileResponse envoie un fichier du disque ; Response sert aux réponses sans contenu (204).
from fastapi.responses import FileResponse, Response

from app.models import GenerationRecord, GenerationStatus, ModelOrigin
from app.schemas import (
    DemoGalleryResponse,
    DemoModelResponse,
    EmbedIntegrationRequest,
    GenerationResponse,
    ModelCategoryRequest,
    ModelRenameRequest,
    PublicModelResponse,
)
from app.services.generation_service import GenerationService
from app.services.demo_gallery import DemoGallery
from app.services.upload_validator import (
    MAX_UPLOAD_BYTES,
    UploadValidationError,
    UploadValidator,
)

router = APIRouter(prefix="/models", tags=["models"])
public_router = APIRouter(prefix="/public/models", tags=["public-models"])


def get_generation_service(request: Request) -> GenerationService:
    """Retourne le service de génération créé au démarrage (app.state).

    Fonction de dépendance : les routes la reçoivent par Depends, et les tests la remplacent
    avec app.dependency_overrides (équivalent d'un @MockBean).
    """
    return request.app.state.generation_service


def get_demo_gallery(request: Request) -> DemoGallery:
    """Récupère le catalogue local borné aux cinq modèles de faisabilité."""
    return request.app.state.demo_gallery


def _to_response(record: GenerationRecord) -> GenerationResponse:
    """Transforme le modèle interne en réponse sans exposer les chemins locaux.

    C'est le « mapper » entité -> DTO : status_url et model_url sont des adresses HTTP,
    jamais des chemins du disque. model_url n'existe que pour un modèle DONE.
    """
    is_done = record.status is GenerationStatus.DONE
    return GenerationResponse(
        id=record.id,
        status=record.status.value,
        filename=record.filename,
        content_type=record.content_type,
        category=record.category,
        created_at=record.created_at,
        updated_at=record.updated_at,
        status_url=f"/models/{record.id}",
        model_url=f"/models/{record.id}/glb" if is_done else None,
        error_message=record.error_message,
        image_warning=record.image_warning,
        origin=record.origin.value,
        duration_seconds=record.duration_seconds,
        public_id=record.public_id,
        embed_enabled=record.embed_enabled,
    )


@router.post("", response_model=GenerationResponse, status_code=202)
async def create_model_generation(
    file: Annotated[UploadFile, File(description="Photo JPG, PNG ou WebP, jusqu'à 10 Mo.")],
    category: Annotated[str, Form(description="Slug d'une catégorie active du catalogue.")],
    background_tasks: BackgroundTasks,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> GenerationResponse:
    """Valide et stocke la photo puis démarre une tâche de génération en arrière-plan.

    Paramètres : file (photo), category (slug). Retour : 202 + GenerationResponse (statut PENDING).
    Erreurs : 400/413/415 (photo refusée par UploadValidator), 422 (catégorie inconnue ou désactivée).
    """
    try:
        # Lecture bornée : au plus 10 Mo + 1 octet. Un fichier trop gros est détecté sans le charger entier.
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

    try:
        record = service.create_generation(validated, content, category)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    # FastAPI envoie d'abord la réponse 202, puis exécute service.run (équivalent d'un @Async Spring).
    background_tasks.add_task(service.run, record.id)
    return _to_response(record)


@router.get("/gallery", response_model=DemoGalleryResponse)
def list_demo_models(
    gallery: Annotated[DemoGallery, Depends(get_demo_gallery)],
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> DemoGalleryResponse:
    """Liste les cinq GLB de faisabilité et les générations réussies de la session."""
    items = [DemoModelResponse.model_validate(item) for item in gallery.list_models()]
    for record in service.list_completed_generations():
        model_path = service.get_model_path(record.id)
        source_path = service.get_source_image_path(record.id)
        if model_path is None:
            continue
        items.append(
            DemoModelResponse(
                id=record.id,
                name=Path(record.filename).stem,
                filename=f"{record.id}.glb",
                category=record.category,
                source=("generated_by_app" if record.origin is ModelOrigin.GENERATED else record.origin.value),
                origin=record.origin.value,
                created_at=record.created_at,
                size_bytes=model_path.stat().st_size,
                model_url=f"/models/{record.id}/glb",
                source_image_url=f"/models/{record.id}/source-image" if source_path else None,
                public_id=record.public_id,
                embed_enabled=record.embed_enabled,
            )
        )
    return DemoGalleryResponse(items=items)


@router.patch("/{generation_id}/integration", response_model=GenerationResponse)
def update_model_integration(
    generation_id: str,
    payload: EmbedIntegrationRequest,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> GenerationResponse:
    """Active ou désactive l'exposition publique d'un modèle terminé."""
    try:
        record = service.set_integration_enabled(generation_id, payload.enabled)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if record is None:
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    return _to_response(record)


@router.patch("/{generation_id}/name", response_model=GenerationResponse)
def rename_model(
    generation_id: str,
    payload: ModelRenameRequest,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> GenerationResponse:
    """Renomme un modèle enregistré ; 404 si inconnu, 422 si le nom est refusé."""
    try:
        record = service.rename_generation(generation_id, payload.name)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if record is None:
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    return _to_response(record)


@router.patch("/{generation_id}/category", response_model=GenerationResponse)
def change_model_category(
    generation_id: str,
    payload: ModelCategoryRequest,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> GenerationResponse:
    """Change la catégorie d'un modèle enregistré ; 404 si inconnu, 422 si la catégorie est refusée."""
    try:
        record = service.change_category(generation_id, payload.category)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if record is None:
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    return _to_response(record)


@router.delete("/{generation_id}", status_code=204)
def delete_model(
    generation_id: str,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> Response:
    """Supprime définitivement un modèle du Studio : ligne en base, GLB et photo source."""
    try:
        deleted = service.delete_generation(generation_id)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if not deleted:
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    return Response(status_code=204)


def _get_enabled_public_model(
    public_id: str,
    service: GenerationService,
) -> tuple[GenerationRecord, Path]:
    """Résout uniquement un GLB terminé et explicitement autorisé à l'intégration.

    Retour : (enregistrement, chemin du GLB). Lève toujours la même 404 si le modèle est inconnu,
    pas terminé, non activé ou sans fichier : on ne révèle pas la raison au public.
    """
    record = service.get_generation_by_public_id(public_id)
    if record is None or not record.embed_enabled or record.status is not GenerationStatus.DONE:
        raise HTTPException(status_code=404, detail="Ce modèle n'est pas disponible pour l'intégration.")
    model_path = service.get_model_path(record.id)
    if model_path is None:
        raise HTTPException(status_code=404, detail="Ce modèle n'est pas disponible pour l'intégration.")
    return record, model_path


@public_router.get("/{public_id}", response_model=PublicModelResponse)
def read_public_model(
    public_id: str,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> PublicModelResponse:
    """Expose les seules métadonnées nécessaires à un modèle autorisé."""
    record, _model_path = _get_enabled_public_model(public_id, service)
    return PublicModelResponse(
        public_id=public_id,
        name=Path(record.filename).stem,
        filename=record.filename,
        category=record.category,
        origin=record.origin.value,
        created_at=record.created_at,
        model_url=f"/public/models/{public_id}/glb",
    )


@public_router.get("/{public_id}/glb")
def download_public_model(
    public_id: str,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> FileResponse:
    """Sert le GLB uniquement tant que son intégration est activée."""
    record, model_path = _get_enabled_public_model(public_id, service)
    return FileResponse(
        path=model_path,
        media_type="model/gltf-binary",
        filename=record.filename,
    )


@router.post("/import", response_model=GenerationResponse, status_code=201)
async def import_model(
    request: Request,
    file: Annotated[UploadFile, File(description="Un modèle GLB 2.0 jusqu'à 30 Mo.")],
    category: Annotated[str, Form(description="Slug d'une catégorie active.")],
    service: GenerationService = Depends(get_generation_service),
    title: Annotated[str, Form()] = "",
) -> GenerationResponse:
    """Valide et enregistre un fichier GLB local dans la bibliothèque."""
    max_bytes = request.app.state.max_glb_upload_bytes
    filename = file.filename or "modele.glb"
    try:
        if Path(filename.replace("\\", "/")).suffix.casefold() != ".glb":
            raise HTTPException(status_code=415, detail="Choisissez un fichier avec l'extension .glb.")
        content = await file.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail="Le fichier dépasse la taille maximale autorisée.")
        record = service.create_library_model(
            content=content,
            title=title,
            filename=filename,
            category=category,
            origin=ModelOrigin.IMPORTED,
            max_upload_bytes=max_bytes,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    finally:
        await file.close()
    return _to_response(record)


@router.post("/examples/{example_id}/copy", response_model=GenerationResponse, status_code=201)
def copy_example_to_library(
    example_id: str,
    request: Request,
    category: Annotated[str, Form()],
    service: GenerationService = Depends(get_generation_service),
    gallery: DemoGallery = Depends(get_demo_gallery),
    title: Annotated[str, Form()] = "",
) -> GenerationResponse:
    """Copie un exemple autorisé dans l'historique avec son origine conservée."""
    source = gallery.get_model_path(example_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Cet exemple n'est plus disponible.")
    try:
        record = service.create_library_model(
            content=source.read_bytes(),
            title=title or source.stem,
            filename=source.name,
            category=category,
            origin=ModelOrigin.EXAMPLE,
            max_upload_bytes=request.app.state.max_glb_upload_bytes,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _to_response(record)


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


@router.get("/{generation_id}/source-image")
def serve_generation_source_image(
    generation_id: str,
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> FileResponse:
    """Sert la photo d'une génération DONE pour sa carte de galerie."""
    record = service.get_generation(generation_id)
    image_path = service.get_source_image_path(generation_id)
    if record is None or image_path is None:
        raise HTTPException(status_code=404, detail="Photo source introuvable.")
    return FileResponse(path=image_path, media_type=record.content_type)

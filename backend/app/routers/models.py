# Rôle : expose l'envoi, le suivi, les téléchargements et la galerie des GLB autorisés.
# Exécution : FastAPI appelle ces routes aux requêtes photo, statut ou modèles d'essai.
"""Routes HTTP associées aux modèles 3D et aux images reçues."""

# Path : pour retirer l'extension d'un nom de fichier.
from pathlib import Path
# Annotated : associe un type et une dépendance FastAPI.
from typing import Annotated

# FastAPI : UploadFile/File/Form lisent un formulaire multipart (fichier + champs texte) ;
# BackgroundTasks exécute un travail après la réponse.
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
# FileResponse envoie un fichier du disque ; Response sert aux réponses sans contenu (204).
from fastapi.responses import FileResponse, Response

# Objets métier et énumérations.
from app.models import GenerationRecord, GenerationStatus, ModelOrigin
# Schémas JSON utilisés par ces routes...
from app.schemas import (
    # ...galerie...
    DemoGalleryResponse,
    # ...un modèle de la galerie...
    DemoModelResponse,
    # ...activation de l'intégration...
    EmbedIntegrationRequest,
    # ...une génération...
    GenerationResponse,
    # ...changement de catégorie...
    ModelCategoryRequest,
    # ...renommage...
    ModelRenameRequest,
    # ...modèle public.
    PublicModelResponse,
)
# Service de génération.
from app.services.generation_service import GenerationService
# Galerie des exemples.
from app.services.demo_gallery import DemoGallery
# Validation des photos...
from app.services.upload_validator import (
    # ...taille maximale...
    MAX_UPLOAD_BYTES,
    # ...erreur de validation...
    UploadValidationError,
    # ...validateur.
    UploadValidator,
)

# Routes du Studio, préfixées par /models.
router = APIRouter(prefix="/models", tags=["models"])
# Routes publiques, préfixées par /public/models (sans session).
public_router = APIRouter(prefix="/public/models", tags=["public-models"])


# Fournit le service de génération aux routes.
def get_generation_service(request: Request) -> GenerationService:
    """Retourne le service de génération créé au démarrage (app.state).

    Fonction de dépendance : les routes la reçoivent par Depends, et les tests la remplacent
    avec app.dependency_overrides (équivalent d'un @MockBean).
    """
    # Lu dans app.state.
    return request.app.state.generation_service


# Fournit la galerie d'exemples aux routes.
def get_demo_gallery(request: Request) -> DemoGallery:
    """Récupère le catalogue local borné aux cinq modèles de faisabilité."""
    # Lu dans app.state.
    return request.app.state.demo_gallery


# Convertit une génération en réponse JSON du Studio.
def _to_response(record: GenerationRecord) -> GenerationResponse:
    """Transforme le modèle interne en réponse sans exposer les chemins locaux.

    C'est le « mapper » entité -> DTO : status_url et model_url sont des adresses HTTP,
    jamais des chemins du disque. model_url n'existe que pour un modèle DONE.
    """
    # Vrai si la génération est terminée.
    is_done = record.status is GenerationStatus.DONE
    # Construit la réponse...
    return GenerationResponse(
        # ...identifiant...
        id=record.id,
        # ...état en texte...
        status=record.status.value,
        # ...nom de fichier...
        filename=record.filename,
        # ...type MIME...
        content_type=record.content_type,
        # ...catégorie...
        category=record.category,
        # ...date de création...
        created_at=record.created_at,
        # ...date de mise à jour...
        updated_at=record.updated_at,
        # ...URL de suivi...
        status_url=f"/models/{record.id}",
        # ...URL du GLB seulement si terminé...
        model_url=f"/models/{record.id}/glb" if is_done else None,
        # ...message d'erreur...
        error_message=record.error_message,
        # ...avertissement photo...
        image_warning=record.image_warning,
        # ...provenance en texte...
        origin=record.origin.value,
        # ...durée...
        duration_seconds=record.duration_seconds,
        # ...UUID public...
        public_id=record.public_id,
        # ...état de l'intégration.
        embed_enabled=record.embed_enabled,
    )


# Route POST /models (réponse 202 Accepted).
@router.post("", response_model=GenerationResponse, status_code=202)
# Fonction asynchrone : attend la lecture du fichier sans bloquer le serveur.
async def create_model_generation(
    # Fichier photo du formulaire.
    file: Annotated[UploadFile, File(description="Photo JPG, PNG ou WebP, jusqu'à 10 Mo.")],
    # Champ « category » du formulaire.
    category: Annotated[str, Form(description="Slug d'une catégorie active du catalogue.")],
    # File des tâches lancées après la réponse.
    background_tasks: BackgroundTasks,
    # Service de génération.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> GenerationResponse:
    """Valide et stocke la photo puis démarre une tâche de génération en arrière-plan.

    Paramètres : file (photo), category (slug). Retour : 202 + GenerationResponse (statut PENDING).
    Erreurs : 400/413/415 (photo refusée par UploadValidator), 422 (catégorie inconnue ou désactivée).
    """
    # Essaie...
    try:
        # Lecture bornée : au plus 10 Mo + 1 octet. Un fichier trop gros est détecté sans le charger entier.
        # ...de lire au plus 10 Mo + 1 octet...
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        # ...puis de valider la photo...
        validated = UploadValidator.validate(
            # ...nom...
            filename=file.filename,
            # ...type annoncé...
            content_type=file.content_type,
            # ...octets.
            content=content,
        )
    # Photo refusée...
    except UploadValidationError as error:
        # ...erreur HTTP...
        raise HTTPException(
            # ...avec le code choisi par le validateur...
            status_code=error.status_code,
            # ...et son message.
            detail=error.detail,
        ) from error
    # Dans tous les cas...
    finally:
        # ...ferme le fichier reçu.
        await file.close()

    # Essaie...
    try:
        # ...de créer la génération PENDING.
        record = service.create_generation(validated, content, category)
    # Catégorie refusée...
    except ValueError as error:
        # ...422.
        raise HTTPException(status_code=422, detail=str(error)) from error
    # FastAPI envoie d'abord la réponse 202, puis exécute service.run (équivalent d'un @Async Spring).
    # Programme la génération après l'envoi de la réponse.
    background_tasks.add_task(service.run, record.id)
    # Renvoie l'état PENDING.
    return _to_response(record)


# Route GET /models/gallery.
@router.get("/gallery", response_model=DemoGalleryResponse)
# Liste la galerie...
def list_demo_models(
    # ...galerie d'exemples...
    gallery: Annotated[DemoGallery, Depends(get_demo_gallery)],
    # ...service de génération.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> DemoGalleryResponse:
    """Liste les cinq GLB de faisabilité et les générations réussies de la session."""
    # Commence par les exemples présents.
    items = [DemoModelResponse.model_validate(item) for item in gallery.list_models()]
    # Pour chaque modèle terminé...
    for record in service.list_completed_generations():
        # ...chemin de son GLB...
        model_path = service.get_model_path(record.id)
        # ...chemin de sa photo...
        source_path = service.get_source_image_path(record.id)
        # ...GLB absent...
        if model_path is None:
            # ...on l'ignore.
            continue
        # Sinon on l'ajoute...
        items.append(
            # ...comme élément de galerie...
            DemoModelResponse(
                # ...identifiant...
                id=record.id,
                # ...nom sans extension...
                name=Path(record.filename).stem,
                # ...nom de fichier technique...
                filename=f"{record.id}.glb",
                # ...catégorie...
                category=record.category,
                # ...source affichée (générée par l'application, ou provenance)...
                source=("generated_by_app" if record.origin is ModelOrigin.GENERATED else record.origin.value),
                # ...provenance...
                origin=record.origin.value,
                # ...date de création...
                created_at=record.created_at,
                # ...taille du fichier...
                size_bytes=model_path.stat().st_size,
                # ...URL du GLB...
                model_url=f"/models/{record.id}/glb",
                # ...URL de la photo si elle existe...
                source_image_url=f"/models/{record.id}/source-image" if source_path else None,
                # ...UUID public...
                public_id=record.public_id,
                # ...état de l'intégration.
                embed_enabled=record.embed_enabled,
            )
        )
    # Renvoie la liste enveloppée dans « items ».
    return DemoGalleryResponse(items=items)


# Route PATCH /models/{generation_id}/integration.
@router.patch("/{generation_id}/integration", response_model=GenerationResponse)
# Active ou désactive l'intégration...
def update_model_integration(
    # ...identifiant lu dans l'URL...
    generation_id: str,
    # ...corps JSON validé...
    payload: EmbedIntegrationRequest,
    # ...service injecté.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> GenerationResponse:
    """Active ou désactive l'exposition publique d'un modèle terminé."""
    # Essaie...
    try:
        # ...de changer l'activation.
        record = service.set_integration_enabled(generation_id, payload.enabled)
    # Modèle pas terminé...
    except ValueError as error:
        # ...409.
        raise HTTPException(status_code=409, detail=str(error)) from error
    # Modèle inconnu...
    if record is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    # Renvoie le modèle à jour.
    return _to_response(record)


# Route PATCH /models/{generation_id}/name.
@router.patch("/{generation_id}/name", response_model=GenerationResponse)
# Renomme un modèle...
def rename_model(
    # ...identifiant lu dans l'URL...
    generation_id: str,
    # ...corps JSON validé...
    payload: ModelRenameRequest,
    # ...service injecté.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> GenerationResponse:
    """Renomme un modèle enregistré ; 404 si inconnu, 422 si le nom est refusé."""
    # Essaie...
    try:
        # ...de renommer.
        record = service.rename_generation(generation_id, payload.name)
    # Nom refusé...
    except ValueError as error:
        # ...422.
        raise HTTPException(status_code=422, detail=str(error)) from error
    # Modèle inconnu...
    if record is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    # Renvoie le modèle à jour.
    return _to_response(record)


# Route PATCH /models/{generation_id}/category.
@router.patch("/{generation_id}/category", response_model=GenerationResponse)
# Change la catégorie...
def change_model_category(
    # ...identifiant lu dans l'URL...
    generation_id: str,
    # ...corps JSON validé...
    payload: ModelCategoryRequest,
    # ...service injecté.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> GenerationResponse:
    """Change la catégorie d'un modèle enregistré ; 404 si inconnu, 422 si la catégorie est refusée."""
    # Essaie...
    try:
        # ...de changer la catégorie.
        record = service.change_category(generation_id, payload.category)
    # Catégorie refusée...
    except ValueError as error:
        # ...422.
        raise HTTPException(status_code=422, detail=str(error)) from error
    # Modèle inconnu...
    if record is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    # Renvoie le modèle à jour.
    return _to_response(record)


# Route DELETE /models/{generation_id} (réponse 204).
@router.delete("/{generation_id}", status_code=204)
# Supprime un modèle...
def delete_model(
    # ...identifiant lu dans l'URL...
    generation_id: str,
    # ...service injecté.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> Response:
    """Supprime définitivement un modèle du Studio : ligne en base, GLB et photo source."""
    # Essaie...
    try:
        # ...de supprimer.
        deleted = service.delete_generation(generation_id)
    # Génération encore en cours...
    except ValueError as error:
        # ...409.
        raise HTTPException(status_code=409, detail=str(error)) from error
    # Modèle inconnu...
    if not deleted:
        # ...404.
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    # Réponse vide 204.
    return Response(status_code=204)


# Lit un modèle public autorisé, ou lève une 404.
def _get_enabled_public_model(
    # UUID public.
    public_id: str,
    # Service de génération.
    service: GenerationService,
) -> tuple[GenerationRecord, Path]:
    """Résout uniquement un GLB terminé et explicitement autorisé à l'intégration.

    Retour : (enregistrement, chemin du GLB). Lève toujours la même 404 si le modèle est inconnu,
    pas terminé, non activé ou sans fichier : on ne révèle pas la raison au public.
    """
    # Cherche le modèle par UUID public.
    record = service.get_generation_by_public_id(public_id)
    # Inconnu, non activé ou pas terminé...
    if record is None or not record.embed_enabled or record.status is not GenerationStatus.DONE:
        # ...404 (même message dans tous les cas).
        raise HTTPException(status_code=404, detail="Ce modèle n'est pas disponible pour l'intégration.")
    # Chemin du GLB.
    model_path = service.get_model_path(record.id)
    # Fichier absent...
    if model_path is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Ce modèle n'est pas disponible pour l'intégration.")
    # Renvoie le modèle et son chemin.
    return record, model_path


# Route publique GET /public/models/{public_id}.
@public_router.get("/{public_id}", response_model=PublicModelResponse)
# Lit les métadonnées publiques...
def read_public_model(
    # ...UUID lu dans l'URL...
    public_id: str,
    # ...service injecté.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> PublicModelResponse:
    """Expose les seules métadonnées nécessaires à un modèle autorisé."""
    # Vérifie que le modèle est autorisé (le chemin n'est pas utilisé ici).
    record, _model_path = _get_enabled_public_model(public_id, service)
    # Renvoie les métadonnées minimales...
    return PublicModelResponse(
        # ...UUID public...
        public_id=public_id,
        # ...nom sans extension...
        name=Path(record.filename).stem,
        # ...nom de fichier...
        filename=record.filename,
        # ...catégorie...
        category=record.category,
        # ...provenance...
        origin=record.origin.value,
        # ...date de création...
        created_at=record.created_at,
        # ...URL publique du GLB.
        model_url=f"/public/models/{public_id}/glb",
    )


# Route publique GET /public/models/{public_id}/glb.
@public_router.get("/{public_id}/glb")
# Télécharge le GLB public...
def download_public_model(
    # ...UUID lu dans l'URL...
    public_id: str,
    # ...service injecté.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> FileResponse:
    """Sert le GLB uniquement tant que son intégration est activée."""
    # Vérifie que le modèle est autorisé et récupère son chemin.
    record, model_path = _get_enabled_public_model(public_id, service)
    # Renvoie le fichier...
    return FileResponse(
        # ...chemin...
        path=model_path,
        # ...type MIME glTF binaire...
        media_type="model/gltf-binary",
        # ...nom proposé au téléchargement.
        filename=record.filename,
    )


# Route POST /models/import (réponse 201 Created).
@router.post("/import", response_model=GenerationResponse, status_code=201)
# Importe un GLB...
async def import_model(
    # ...requête (pour lire la taille maximale)...
    request: Request,
    # ...fichier GLB du formulaire...
    file: Annotated[UploadFile, File(description="Un modèle GLB 2.0 jusqu'à 30 Mo.")],
    # ...champ « category »...
    category: Annotated[str, Form(description="Slug d'une catégorie active.")],
    # ...service injecté...
    service: GenerationService = Depends(get_generation_service),
    # ...titre facultatif.
    title: Annotated[str, Form()] = "",
) -> GenerationResponse:
    """Valide et enregistre un fichier GLB local dans la bibliothèque."""
    # Taille maximale autorisée en octets.
    max_bytes = request.app.state.max_glb_upload_bytes
    # Nom du fichier, ou un nom par défaut.
    filename = file.filename or "modele.glb"
    # Essaie...
    try:
        # ...extension différente de .glb...
        if Path(filename.replace("\\", "/")).suffix.casefold() != ".glb":
            # ...415.
            raise HTTPException(status_code=415, detail="Choisissez un fichier avec l'extension .glb.")
        # Lit au plus la taille maximale + 1 octet.
        content = await file.read(max_bytes + 1)
        # Trop gros...
        if len(content) > max_bytes:
            # ...413.
            raise HTTPException(status_code=413, detail="Le fichier dépasse la taille maximale autorisée.")
        # Crée le modèle dans la bibliothèque...
        record = service.create_library_model(
            # ...octets...
            content=content,
            # ...titre...
            title=title,
            # ...nom de fichier...
            filename=filename,
            # ...catégorie...
            category=category,
            # ...provenance : importé...
            origin=ModelOrigin.IMPORTED,
            # ...taille maximale.
            max_upload_bytes=max_bytes,
        )
    # GLB ou catégorie refusés...
    except ValueError as error:
        # ...422.
        raise HTTPException(status_code=422, detail=str(error)) from error
    # Dans tous les cas...
    finally:
        # ...ferme le fichier reçu.
        await file.close()
    # Renvoie le modèle créé.
    return _to_response(record)


# Route POST /models/examples/{example_id}/copy (réponse 201).
@router.post("/examples/{example_id}/copy", response_model=GenerationResponse, status_code=201)
# Copie un exemple dans la bibliothèque...
def copy_example_to_library(
    # ...identifiant de l'exemple lu dans l'URL...
    example_id: str,
    # ...requête...
    request: Request,
    # ...champ « category »...
    category: Annotated[str, Form()],
    # ...service de génération...
    service: GenerationService = Depends(get_generation_service),
    # ...galerie d'exemples...
    gallery: DemoGallery = Depends(get_demo_gallery),
    # ...titre facultatif.
    title: Annotated[str, Form()] = "",
) -> GenerationResponse:
    """Copie un exemple autorisé dans l'historique avec son origine conservée."""
    # Chemin du GLB de l'exemple.
    source = gallery.get_model_path(example_id)
    # Exemple inconnu ou absent...
    if source is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Cet exemple n'est plus disponible.")
    # Essaie...
    try:
        # ...de créer le modèle...
        record = service.create_library_model(
            # ...octets lus depuis l'exemple...
            content=source.read_bytes(),
            # ...titre saisi ou nom de l'exemple...
            title=title or source.stem,
            # ...nom du fichier...
            filename=source.name,
            # ...catégorie...
            category=category,
            # ...provenance : exemple...
            origin=ModelOrigin.EXAMPLE,
            # ...taille maximale.
            max_upload_bytes=request.app.state.max_glb_upload_bytes,
        )
    # Refusé...
    except ValueError as error:
        # ...422.
        raise HTTPException(status_code=422, detail=str(error)) from error
    # Renvoie le modèle créé.
    return _to_response(record)


# Route GET /models/gallery/{model_id} : GLB d'un exemple.
@router.get("/gallery/{model_id}")
# Télécharge un exemple...
def download_demo_model(
    # ...identifiant lu dans l'URL...
    model_id: str,
    # ...galerie injectée.
    gallery: Annotated[DemoGallery, Depends(get_demo_gallery)],
) -> FileResponse:
    """Sert un GLB réel de démonstration par identifiant autorisé."""
    # Chemin du GLB.
    model_path = gallery.get_model_path(model_id)
    # Inconnu...
    if model_path is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Modèle de démonstration introuvable.")
    # Renvoie le fichier...
    return FileResponse(
        # ...chemin...
        path=model_path,
        # ...type MIME...
        media_type="model/gltf-binary",
        # ...nom proposé.
        filename=model_path.name,
    )


# Route GET /models/gallery/{model_id}/source-image.
@router.get("/gallery/{model_id}/source-image")
# Renvoie la photo d'un exemple...
def serve_demo_source_image(
    # ...identifiant lu dans l'URL...
    model_id: str,
    # ...galerie injectée.
    gallery: Annotated[DemoGallery, Depends(get_demo_gallery)],
) -> FileResponse:
    """Sert la photo source d'un modèle autorisé seulement si elle est présente."""
    # Chemin de la photo.
    image_path = gallery.get_source_image_path(model_id)
    # Absente...
    if image_path is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Photo source introuvable.")
    # Type MIME selon l'extension...
    media_types = {
        # ...JPG...
        ".jpg": "image/jpeg",
        # ...JPEG...
        ".jpeg": "image/jpeg",
        # ...PNG...
        ".png": "image/png",
        # ...WebP.
        ".webp": "image/webp",
    }
    # Renvoie l'image avec le bon type MIME.
    return FileResponse(path=image_path, media_type=media_types[image_path.suffix.casefold()])


# Route GET /models/{generation_id} : état d'une génération.
@router.get("/{generation_id}", response_model=GenerationResponse)
# Lit l'état...
def get_model_generation(
    # ...identifiant lu dans l'URL...
    generation_id: str,
    # ...service injecté.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> GenerationResponse:
    """Retourne l'état connu d'une génération sans déclencher de nouveau travail."""
    # Lit la génération.
    record = service.get_generation(generation_id)
    # Inconnue...
    if record is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Génération introuvable.")
    # Renvoie son état.
    return _to_response(record)


# Route GET /models/{generation_id}/glb.
@router.get("/{generation_id}/glb")
# Télécharge le GLB...
def download_model_glb(
    # ...identifiant lu dans l'URL...
    generation_id: str,
    # ...service injecté.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> FileResponse:
    """Télécharge le GLB seulement après l'état DONE."""
    # Lit la génération.
    record = service.get_generation(generation_id)
    # Inconnue...
    if record is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Génération introuvable.")
    # Pas encore terminée...
    if record.status is not GenerationStatus.DONE:
        # ...409...
        raise HTTPException(
            # ...code HTTP...
            status_code=409,
            # ...message.
            detail="Le modèle n'est pas encore disponible ; consultez son état.",
        )
    # Chemin du GLB.
    model_path = service.get_model_path(generation_id)
    # Fichier absent alors que le modèle est terminé...
    if model_path is None:
        # ...500 (incohérence côté serveur)...
        raise HTTPException(
            # ...code HTTP...
            status_code=500,
            # ...message.
            detail="Le modèle terminé est absent du stockage local.",
        )
    # Renvoie le fichier...
    return FileResponse(
        # ...chemin...
        path=model_path,
        # ...type MIME...
        media_type="model/gltf-binary",
        # ...nom proposé.
        filename=f"{generation_id}.glb",
    )


# Route GET /models/{generation_id}/source-image.
@router.get("/{generation_id}/source-image")
# Renvoie la photo d'une génération...
def serve_generation_source_image(
    # ...identifiant lu dans l'URL...
    generation_id: str,
    # ...service injecté.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> FileResponse:
    """Sert la photo d'une génération DONE pour sa carte de galerie."""
    # Lit la génération.
    record = service.get_generation(generation_id)
    # Chemin de la photo (seulement si terminée).
    image_path = service.get_source_image_path(generation_id)
    # Génération ou photo absente...
    if record is None or image_path is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Photo source introuvable.")
    # Renvoie l'image avec son type MIME d'origine.
    return FileResponse(path=image_path, media_type=record.content_type)

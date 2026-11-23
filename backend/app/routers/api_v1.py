# Rôle : expose l’API d’intégration versionnée pour créer et consulter des modèles.
# Exécution : les intégrateurs envoient X-API-Key ; les services internes conservent la logique métier.
"""Routes versionnées de l’API destinée aux sites intégrateurs."""

# datetime (standard) : dates et durées. Tout est calculé en UTC pour un quota journalier stable.
from datetime import UTC, datetime, timedelta
# escape : protège le HTML du code d'intégration.
from html import escape
# Path : pour retirer l'extension du nom de fichier.
from pathlib import Path
# Annotated : associe un type et une dépendance FastAPI.
from typing import Annotated

# FastAPI : BackgroundTasks lance un travail après l'envoi de la réponse ; File/Form/UploadFile
# lisent un formulaire avec fichier (multipart).
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile, status
# FileResponse : renvoie un fichier (le GLB).
from fastapi.responses import FileResponse

# Objets métier.
from app.models import APIKeyRecord, GenerationRecord, GenerationStatus
# Fourniture du service des clés et vérification de la clé.
from app.routers.api_keys import get_api_key_service, require_api_key
# Fourniture du service des catégories.
from app.routers.categories import get_category_service
# Fourniture du service de génération.
from app.routers.models import get_generation_service
# Schémas JSON de l'API externe.
from app.schemas import APIIntegrationCodeResponse, APIModelResponse
# Service des clés.
from app.services.api_key_service import APIKeyService
# Service des catégories et son erreur « introuvable ».
from app.services.category_service import CategoryNotFoundError, CategoryService
# Service de génération.
from app.services.generation_service import GenerationService
# Taille maximale, erreur et validateur des photos.
from app.services.upload_validator import MAX_UPLOAD_BYTES, UploadValidationError, UploadValidator

# Groupe de routes préfixées par /api/v1.
router = APIRouter(prefix="/api/v1", tags=["integration-v1"])


# Dépendance commune à toutes les routes /api/v1.
def require_api_v1_key(
    # Requête (pour lire la configuration).
    request: Request,
    # Clé déjà authentifiée par require_api_key.
    key: Annotated[APIKeyRecord, Depends(require_api_key)],
    # Service des clés.
    key_service: Annotated[APIKeyService, Depends(get_api_key_service)],
) -> APIKeyRecord:
    """Authentifie la clé puis applique une limite glissante aux routes versionnées.

    Dépendance en chaîne : require_api_key valide d'abord la clé, puis on consomme une requête
    dans la fenêtre d'une minute. Lève 401 (clé révoquée entre-temps) ou 429 + Retry-After: 60.
    """
    # Consomme une requête dans la limite par minute...
    reason = key_service.consume_rate_limit(
        # ...de cette clé, selon la limite configurée.
        key, request.app.state.api_rate_limit_per_minute
    )
    # Clé révoquée entre-temps...
    if reason == "revoked":
        # ...401.
        raise HTTPException(status_code=401, detail="Clé API absente, invalide ou révoquée.")
    # Limite atteinte...
    if reason == "rate_limit":
        # ...429...
        raise HTTPException(
            # ...code HTTP...
            status_code=429,
            # ...message...
            detail="Limite de débit atteinte ; réessayez dans une minute.",
            # ...réessayer dans 60 secondes.
            headers={"Retry-After": "60"},
        )
    # Renvoie la clé à la route.
    return key


# Convertit une génération en réponse JSON de l'API externe.
def _model_response(record: GenerationRecord) -> APIModelResponse:
    """Construit un état externe sans exposer les chemins locaux ni les URL internes."""
    # Construit la réponse...
    return APIModelResponse(
        # ...identifiant...
        id=record.id,
        # ...état en texte...
        status=record.status.value,
        # ...nom de fichier...
        filename=record.filename,
        # ...catégorie...
        category=record.category,
        # ...date de création...
        created_at=record.created_at,
        # ...date de mise à jour...
        updated_at=record.updated_at,
        # ...URL de suivi versionnée...
        status_url=f"/api/v1/models/{record.id}",
        # ...URL du GLB seulement si le modèle est terminé...
        model_url=f"/api/v1/models/{record.id}/glb" if record.status is GenerationStatus.DONE else None,
        # ...message d'erreur...
        error_message=record.error_message,
        # ...durée...
        duration_seconds=record.duration_seconds,
        # ...UUID public...
        public_id=record.public_id,
        # ...état de l'intégration.
        embed_enabled=record.embed_enabled,
    )


# Route POST /api/v1/models (réponse 202 Accepted).
@router.post("/models", response_model=APIModelResponse, status_code=status.HTTP_202_ACCEPTED)
# Fonction asynchrone : elle attend la lecture du fichier sans bloquer le serveur.
async def create_model(
    # Fichier envoyé dans le formulaire.
    file: Annotated[UploadFile, File(description="Photo JPG, PNG ou WebP, jusqu’à 10 Mo.")],
    # Champ « category » du formulaire.
    category: Annotated[str, Form(description="Slug d’une catégorie active.")],
    # File des tâches à lancer après la réponse.
    background_tasks: BackgroundTasks,
    # Clé vérifiée et limite par minute consommée.
    _key: Annotated[APIKeyRecord, Depends(require_api_v1_key)],
    # Requête.
    request: Request,
    # Service de génération.
    service: Annotated[GenerationService, Depends(get_generation_service)],
    # Service des catégories.
    category_service: Annotated[CategoryService, Depends(get_category_service)],
    # Service des clés.
    key_service: Annotated[APIKeyService, Depends(get_api_key_service)],
) -> APIModelResponse:
    """Valide une photo, consomme le quota et relance le service de génération existant.

    Étapes : lecture bornée du fichier (10 Mo + 1 octet), validation, catégorie active (sinon 403),
    quota du jour par clé (sinon 429 avec Retry-After jusqu'à minuit UTC), création PENDING,
    puis génération en tâche de fond. Retour : 202 avec l'adresse de suivi.
    """
    # Essaie...
    try:
        # ...de lire au plus 10 Mo + 1 octet (pour détecter un fichier trop gros)...
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        # ...puis de valider la photo.
        validated = UploadValidator.validate(file.filename, file.content_type, content)
    # Photo refusée...
    except UploadValidationError as error:
        # ...erreur HTTP avec le code choisi par le validateur.
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    # Dans tous les cas...
    finally:
        # ...ferme le fichier reçu.
        await file.close()

    # Essaie...
    try:
        # ...de vérifier que la catégorie est active.
        category_service.require_active(category)
    # Catégorie inconnue ou désactivée...
    except CategoryNotFoundError as error:
        # ...403.
        raise HTTPException(status_code=403, detail=str(error)) from error

    # Consomme une création dans le quota du jour...
    reason = key_service.consume_daily_quota(
        # ...de cette clé, selon la limite configurée.
        _key, request.app.state.api_daily_generation_limit
    )
    # Clé révoquée entre-temps...
    if reason == "revoked":
        # ...401.
        raise HTTPException(status_code=401, detail="Clé API absente, invalide ou révoquée.")
    # Quota atteint...
    if reason == "daily_quota":
        # ...instant présent...
        now = datetime.now(UTC)
        # ...minuit UTC du lendemain...
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        # ...secondes restantes (au moins 1)...
        wait_seconds = max(1, int((tomorrow - now).total_seconds()))
        # ...429...
        raise HTTPException(
            # ...code HTTP...
            status_code=429,
            # ...message...
            detail="Quota quotidien de créations atteint pour cette clé.",
            # ...réessayer à minuit UTC.
            headers={"Retry-After": str(wait_seconds)},
        )

    # Essaie...
    try:
        # ...de créer la génération PENDING.
        record = service.create_generation(validated, content, category)
    # Erreur de catégorie...
    except ValueError as error:
        # ...403.
        raise HTTPException(status_code=403, detail=str(error)) from error
    # La génération (1 à 2 minutes) démarre APRÈS l'envoi de la réponse 202. Équivalent d'un @Async Spring.
    # Programme la génération après l'envoi de la réponse.
    background_tasks.add_task(service.run, record.id)
    # Renvoie l'état PENDING.
    return _model_response(record)


# Route GET /api/v1/models/{generation_id}.
@router.get("/models/{generation_id}", response_model=APIModelResponse)
# Lit l'état d'un modèle...
def get_model_status(
    # ...identifiant lu dans l'URL...
    generation_id: str,
    # ...clé vérifiée...
    _key: Annotated[APIKeyRecord, Depends(require_api_v1_key)],
    # ...service injecté.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> APIModelResponse:
    """Retourne l’état d’un modèle sans révéler de chemins locaux."""
    # Lit la génération.
    record = service.get_generation(generation_id)
    # Inconnue...
    if record is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    # Renvoie son état.
    return _model_response(record)


# Route GET /api/v1/models/{generation_id}/glb.
@router.get("/models/{generation_id}/glb")
# Télécharge le GLB...
def download_model(
    # ...identifiant lu dans l'URL...
    generation_id: str,
    # ...clé vérifiée...
    _key: Annotated[APIKeyRecord, Depends(require_api_v1_key)],
    # ...service injecté.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> FileResponse:
    """Télécharge le GLB après une génération terminée."""
    # Lit la génération.
    record = service.get_generation(generation_id)
    # Inconnue...
    if record is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    # Pas encore terminée...
    if record.status is not GenerationStatus.DONE:
        # ...409.
        raise HTTPException(status_code=409, detail="Le modèle n’est pas encore prêt.")
    # Chemin du GLB.
    path = service.get_model_path(generation_id)
    # Fichier absent...
    if path is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Le fichier GLB est introuvable.")
    # Renvoie le fichier avec le type MIME glTF binaire.
    return FileResponse(path, media_type="model/gltf-binary", filename=record.filename)


# Route GET /api/v1/models/{generation_id}/integration-code.
@router.get("/models/{generation_id}/integration-code", response_model=APIIntegrationCodeResponse)
# Renvoie le code à copier...
def get_integration_code(
    # ...identifiant lu dans l'URL...
    generation_id: str,
    # ...requête (pour connaître l'adresse du serveur)...
    request: Request,
    # ...clé vérifiée...
    _key: Annotated[APIKeyRecord, Depends(require_api_v1_key)],
    # ...service injecté.
    service: Annotated[GenerationService, Depends(get_generation_service)],
) -> APIIntegrationCodeResponse:
    """Retourne un iframe uniquement pour un modèle terminé dont l’intégration est activée."""
    # Lit la génération.
    record = service.get_generation(generation_id)
    # Inconnue...
    if record is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Modèle introuvable.")
    # Pas encore terminée...
    if record.status is not GenerationStatus.DONE:
        # ...409.
        raise HTTPException(status_code=409, detail="Le modèle n’est pas encore prêt.")
    # Intégration non activée...
    if not record.embed_enabled or not record.public_id:
        # ...403.
        raise HTTPException(status_code=403, detail="Activez l’intégration sur la fiche du modèle avant de copier son code.")
    # Adresse du serveur sans « / » final.
    base_url = str(request.base_url).rstrip("/")
    # URL de la page /embed, échappée.
    source = escape(f"{base_url}/embed/{record.public_id}", quote=True)
    # Nom du modèle sans extension, échappé.
    title = escape(Path(record.filename).stem, quote=True)
    # Code <iframe>...
    iframe = (
        # ...source, titre, largeur et hauteur...
        f'<iframe src="{source}" title="Aperçu 3D : {title}" width="100%" height="480" '
        # ...chargement différé, sans bordure, plein écran et réalité augmentée autorisés.
        'loading="lazy" style="border:0" allow="fullscreen; xr-spatial-tracking"></iframe>'
    )
    # URL du script du widget (le paramètre v force le rechargement après une mise à jour).
    widget_script = escape(f"{base_url}/static/widget.js?v=20261111-5d", quote=True)
    # Code du widget...
    widget = (
        # ...balise qui charge le script...
        f'<script src="{widget_script}" defer></script>\n'
        # ...balise du composant Web avec l'UUID public.
        f'<forma3d-viewer model="{record.public_id}" height="480"></forma3d-viewer>'
    )
    # Renvoie les deux codes.
    return APIIntegrationCodeResponse(
        public_id=record.public_id, iframe_html=iframe, widget_html=widget
    )

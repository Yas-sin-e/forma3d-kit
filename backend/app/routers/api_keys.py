# Rôle : expose la gestion locale des clés et la dépendance X-API-Key réutilisable.
# Exécution : le Studio administre les clés ; les futures routes publiques protègent leurs appels avec require_api_key.
# Révoquer (DELETE /{id}) coupe l'accès en gardant une trace ; supprimer (DELETE /{id}/permanent) efface une clé déjà révoquée.
"""Routes de gestion et vérification des clés API d’intégration."""

# typing.Annotated (standard) : attache une information à un type. FastAPI s'en sert pour
# l'injection : Annotated[Service, Depends(fonction)] = « appelle fonction et donne-moi le résultat ».
from typing import Annotated

# FastAPI : Depends = injection de dépendances ; Header = lecture d'un en-tête HTTP.
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status

from app.models import APIKeyRecord
from app.schemas import APIKeyCreateRequest, APIKeyCreatedResponse, APIKeyListResponse, APIKeyResponse
from app.services.api_key_service import APIKeyService, APIKeyValidationError

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def get_api_key_service(request: Request) -> APIKeyService:
    """Retourne le service de clés configuré au démarrage."""
    return request.app.state.api_key_service


def _response(record: APIKeyRecord) -> APIKeyResponse:
    """Construit une réponse sans empreinte cryptographique ni secret."""
    return APIKeyResponse(
        id=record.id,
        name=record.name,
        prefix=record.prefix,
        created_at=record.created_at,
        revoked=record.revoked,
    )


@router.get("", response_model=APIKeyListResponse)
def list_api_keys(
    service: Annotated[APIKeyService, Depends(get_api_key_service)],
) -> APIKeyListResponse:
    """Liste les noms, préfixes et statuts des clés existantes."""
    return APIKeyListResponse(items=[_response(record) for record in service.list()])


@router.post("", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: APIKeyCreateRequest,
    service: Annotated[APIKeyService, Depends(get_api_key_service)],
    response: Response,
) -> APIKeyCreatedResponse:
    """Crée une clé et révèle sa valeur uniquement dans cette réponse."""
    try:
        record, secret = service.create(payload.name)
    except APIKeyValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    # Le secret n'apparaît que dans cette réponse : on interdit au navigateur de la garder en cache.
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return APIKeyCreatedResponse(**_response(record).model_dump(), key=secret)


@router.delete("/{key_id}", response_model=APIKeyResponse)
def revoke_api_key(
    key_id: str,
    service: Annotated[APIKeyService, Depends(get_api_key_service)],
) -> APIKeyResponse:
    """Révoque une clé sans supprimer sa trace dans l’écran de gestion."""
    record = service.revoke(key_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Clé API introuvable.")
    return _response(record)


@router.delete("/{key_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
def delete_revoked_api_key(
    key_id: str,
    service: Annotated[APIKeyService, Depends(get_api_key_service)],
) -> Response:
    """Supprime définitivement une clé déjà révoquée (la révocation reste l'étape obligatoire)."""
    outcome = service.delete_revoked(key_id)
    if outcome == "not_found":
        raise HTTPException(status_code=404, detail="Clé API introuvable.")
    if outcome == "active":
        raise HTTPException(status_code=409, detail="Révoquez la clé avant de la supprimer définitivement.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def require_api_key(
    service: Annotated[APIKeyService, Depends(get_api_key_service)],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> APIKeyRecord:
    """Dépendance des routes d'intégration ; refuse les clés absentes, fausses ou révoquées.

    Lit l'en-tête X-API-Key (Header(alias=...)). Retour : la clé authentifiée.
    Lève 401 avec l'en-tête WWW-Authenticate si la clé n'est pas acceptée.
    """
    record = service.authenticate(x_api_key)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente, invalide ou révoquée.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return record

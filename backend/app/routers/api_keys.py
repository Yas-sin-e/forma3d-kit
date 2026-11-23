# Rôle : expose la gestion locale des clés et la dépendance X-API-Key réutilisable.
# Exécution : le Studio administre les clés ; les futures routes publiques protègent leurs appels avec require_api_key.
# Révoquer (DELETE /{id}) coupe l'accès en gardant une trace ; supprimer (DELETE /{id}/permanent) efface une clé déjà révoquée.
"""Routes de gestion et vérification des clés API d’intégration."""

# typing.Annotated (standard) : attache une information à un type. FastAPI s'en sert pour
# l'injection : Annotated[Service, Depends(fonction)] = « appelle fonction et donne-moi le résultat ».
from typing import Annotated

# FastAPI : Depends = injection de dépendances ; Header = lecture d'un en-tête HTTP.
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status

# Objet métier d'une clé.
from app.models import APIKeyRecord
# Schémas JSON des clés.
from app.schemas import APIKeyCreateRequest, APIKeyCreatedResponse, APIKeyListResponse, APIKeyResponse
# Service des clés et son erreur de validation.
from app.services.api_key_service import APIKeyService, APIKeyValidationError

# Groupe de routes préfixées par /api-keys.
router = APIRouter(prefix="/api-keys", tags=["api-keys"])


# Fournit le service aux routes.
def get_api_key_service(request: Request) -> APIKeyService:
    """Retourne le service de clés configuré au démarrage."""
    # Lu dans app.state.
    return request.app.state.api_key_service


# Convertit un enregistrement en réponse JSON sûre.
def _response(record: APIKeyRecord) -> APIKeyResponse:
    """Construit une réponse sans empreinte cryptographique ni secret."""
    # Construit la réponse...
    return APIKeyResponse(
        # ...identifiant...
        id=record.id,
        # ...nom...
        name=record.name,
        # ...préfixe visible...
        prefix=record.prefix,
        # ...date de création...
        created_at=record.created_at,
        # ...état révoqué (jamais l'empreinte).
        revoked=record.revoked,
    )


# Route GET /api-keys.
@router.get("", response_model=APIKeyListResponse)
# Liste les clés...
def list_api_keys(
    # ...service injecté.
    service: Annotated[APIKeyService, Depends(get_api_key_service)],
) -> APIKeyListResponse:
    """Liste les noms, préfixes et statuts des clés existantes."""
    # Convertit chaque clé et enveloppe dans « items ».
    return APIKeyListResponse(items=[_response(record) for record in service.list()])


# Route POST /api-keys (réponse 201).
@router.post("", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
# Crée une clé...
def create_api_key(
    # ...corps JSON validé...
    payload: APIKeyCreateRequest,
    # ...service injecté...
    service: Annotated[APIKeyService, Depends(get_api_key_service)],
    # ...réponse, pour ajouter des en-têtes.
    response: Response,
) -> APIKeyCreatedResponse:
    """Crée une clé et révèle sa valeur uniquement dans cette réponse."""
    # Essaie...
    try:
        # ...de créer la clé ; récupère l'enregistrement et le secret.
        record, secret = service.create(payload.name)
    # Nom invalide...
    except APIKeyValidationError as error:
        # ...422.
        raise HTTPException(status_code=422, detail=str(error)) from error
    # Le secret n'apparaît que dans cette réponse : on interdit au navigateur de la garder en cache.
    # Interdit la mise en cache de la réponse.
    response.headers["Cache-Control"] = "no-store"
    # Même consigne pour les anciens navigateurs.
    response.headers["Pragma"] = "no-cache"
    # Réponse : métadonnées + secret (seule fois où il est renvoyé).
    return APIKeyCreatedResponse(**_response(record).model_dump(), key=secret)


# Route DELETE /api-keys/{key_id} : révocation.
@router.delete("/{key_id}", response_model=APIKeyResponse)
# Révoque une clé...
def revoke_api_key(
    # ...identifiant lu dans l'URL...
    key_id: str,
    # ...service injecté.
    service: Annotated[APIKeyService, Depends(get_api_key_service)],
) -> APIKeyResponse:
    """Révoque une clé sans supprimer sa trace dans l’écran de gestion."""
    # Révoque la clé.
    record = service.revoke(key_id)
    # Clé inconnue...
    if record is None:
        # ...404.
        raise HTTPException(status_code=404, detail="Clé API introuvable.")
    # Renvoie la clé révoquée.
    return _response(record)


# Route DELETE /api-keys/{key_id}/permanent (réponse 204).
@router.delete("/{key_id}/permanent", status_code=status.HTTP_204_NO_CONTENT)
# Supprime une clé révoquée...
def delete_revoked_api_key(
    # ...identifiant lu dans l'URL...
    key_id: str,
    # ...service injecté.
    service: Annotated[APIKeyService, Depends(get_api_key_service)],
) -> Response:
    """Supprime définitivement une clé déjà révoquée (la révocation reste l'étape obligatoire)."""
    # Résultat de la suppression.
    outcome = service.delete_revoked(key_id)
    # Clé inconnue...
    if outcome == "not_found":
        # ...404.
        raise HTTPException(status_code=404, detail="Clé API introuvable.")
    # Clé encore active...
    if outcome == "active":
        # ...409 : il faut la révoquer d'abord.
        raise HTTPException(status_code=409, detail="Révoquez la clé avant de la supprimer définitivement.")
    # Réponse vide 204.
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Dépendance des routes /api/v1 : exige une clé valide.
def require_api_key(
    # Service injecté.
    service: Annotated[APIKeyService, Depends(get_api_key_service)],
    # Valeur de l'en-tête HTTP X-API-Key (None s'il est absent).
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> APIKeyRecord:
    """Dépendance des routes d'intégration ; refuse les clés absentes, fausses ou révoquées.

    Lit l'en-tête X-API-Key (Header(alias=...)). Retour : la clé authentifiée.
    Lève 401 avec l'en-tête WWW-Authenticate si la clé n'est pas acceptée.
    """
    # Vérifie la clé.
    record = service.authenticate(x_api_key)
    # Clé refusée...
    if record is None:
        # ...401...
        raise HTTPException(
            # ...code HTTP...
            status_code=status.HTTP_401_UNAUTHORIZED,
            # ...message...
            detail="Clé API absente, invalide ou révoquée.",
            # ...en-tête qui indique la méthode d'authentification attendue.
            headers={"WWW-Authenticate": "ApiKey"},
        )
    # Renvoie la clé acceptée à la route.
    return record

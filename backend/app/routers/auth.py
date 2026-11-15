# Rôle : expose la connexion de la propriétaire (login, logout, me) et la dépendance qui protège le Studio.
# Exécution : main.py inclut ce routeur et ajoute require_owner aux routeurs modèles, catégories et clés API.
"""Routes de session du Studio : POST /auth/login, POST /auth/logout, GET /auth/me."""

from __future__ import annotations

# FastAPI : APIRouter regroupe des routes (comme un @RestController) ; HTTPException renvoie une
# erreur HTTP ; Response permet de poser un cookie ; status contient les codes HTTP nommés.
from fastapi import APIRouter, HTTPException, Request, Response, status
# Pydantic : décrit et valide le JSON reçu (ici le corps de la connexion).
from pydantic import BaseModel, Field

from app.services.owner_auth import (
    SESSION_COOKIE_NAME,
    LoginRateLimitedError,
    OwnerAuthService,
    OwnerPasswordNotConfiguredError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Corps JSON de connexion : uniquement le mot de passe (Studio mono-propriétaire)."""

    password: str = Field(min_length=1, max_length=256)


def _service(request: Request) -> OwnerAuthService:
    """Retourne le service d'authentification créé au démarrage (rangé dans app.state)."""
    return request.app.state.owner_auth


def require_owner(request: Request) -> None:
    """Dépendance FastAPI : refuse avec 401 toute requête sans cookie de session valide.

    FastAPI l'exécute AVANT la route ; si elle lève HTTPException, la route n'est jamais appelée.
    Équivalent d'un filtre Spring Security ou d'un garde CanActivate d'Angular, côté serveur.
    """
    if not _service(request).validate_token(request.cookies.get(SESSION_COOKIE_NAME)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Connexion requise.")


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response) -> dict[str, bool]:
    """Vérifie le mot de passe puis pose un cookie HttpOnly, SameSite=Lax, signé et expirant.

    Ordre des contrôles : limite de tentatives par IP (429 + Retry-After), mot de passe non
    configuré (503), mot de passe faux (401). Retour : {"authenticated": true}.
    """
    service = _service(request)
    client_ip = request.client.host if request.client else "unknown"
    try:
        service.limiter.register(client_ip)
    except LoginRateLimitedError as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives. Patientez une minute avant de réessayer.",
            headers={"Retry-After": str(error.retry_after_seconds)},
        ) from error
    try:
        valid = service.verify_password(payload.password)
    except OwnerPasswordNotConfiguredError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Mot de passe incorrect.")
    # httponly : JavaScript ne peut pas lire le cookie (protection contre le vol par script).
    # samesite="lax" : non envoyé par les formulaires d'autres sites. secure : seulement en HTTPS.
    # max_age : durée de vie (8 h).
    response.set_cookie(
        SESSION_COOKIE_NAME,
        service.issue_token(),
        max_age=service.ttl_seconds,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        path="/",
    )
    return {"authenticated": True}


@router.post("/logout")
def logout(response: Response) -> dict[str, bool]:
    """Supprime le cookie de session (sans erreur si aucune session n'existait)."""
    response.delete_cookie(SESSION_COOKIE_NAME, path="/", httponly=True, samesite="lax")
    return {"authenticated": False}


@router.get("/me")
def me(request: Request) -> dict[str, bool]:
    """Indique si la session est valide et si un mot de passe est configuré côté serveur."""
    service = _service(request)
    return {
        "authenticated": service.validate_token(request.cookies.get(SESSION_COOKIE_NAME)),
        "configured": service.is_configured(),
    }

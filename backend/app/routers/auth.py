# Rôle : expose la connexion de la propriétaire (login, logout, me) et la dépendance qui protège le Studio.
# Exécution : main.py inclut ce routeur et ajoute require_owner aux routeurs modèles, catégories et clés API.
"""Routes de session du Studio : POST /auth/login, POST /auth/logout, GET /auth/me."""

# Les annotations de type restent du texte.
from __future__ import annotations

# FastAPI : APIRouter regroupe des routes (comme un @RestController) ; HTTPException renvoie une
# erreur HTTP ; Response permet de poser un cookie ; status contient les codes HTTP nommés.
from fastapi import APIRouter, HTTPException, Request, Response, status
# Pydantic : décrit et valide le JSON reçu (ici le corps de la connexion).
from pydantic import BaseModel, Field

# Importe du service d'authentification...
from app.services.owner_auth import (
    # ...le nom du cookie de session...
    SESSION_COOKIE_NAME,
    # ...l'erreur « trop de tentatives »...
    LoginRateLimitedError,
    # ...le service...
    OwnerAuthService,
    # ...l'erreur « mot de passe non configuré ».
    OwnerPasswordNotConfiguredError,
)

# Groupe de routes préfixées par /auth, rangées sous « auth » dans /docs.
router = APIRouter(prefix="/auth", tags=["auth"])


# Corps JSON attendu par POST /auth/login.
class LoginRequest(BaseModel):
    """Corps JSON de connexion : uniquement le mot de passe (Studio mono-propriétaire)."""

    # Mot de passe : 1 à 256 caractères.
    password: str = Field(min_length=1, max_length=256)


# Récupère le service d'authentification.
def _service(request: Request) -> OwnerAuthService:
    """Retourne le service d'authentification créé au démarrage (rangé dans app.state)."""
    # Lu dans app.state, rempli par main.py.
    return request.app.state.owner_auth


# Dépendance qui protège les routes du Studio.
def require_owner(request: Request) -> None:
    """Dépendance FastAPI : refuse avec 401 toute requête sans cookie de session valide.

    FastAPI l'exécute AVANT la route ; si elle lève HTTPException, la route n'est jamais appelée.
    Équivalent d'un filtre Spring Security ou d'un garde CanActivate d'Angular, côté serveur.
    """
    # Cookie de session absent, faux ou expiré...
    if not _service(request).validate_token(request.cookies.get(SESSION_COOKIE_NAME)):
        # ...refus 401.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Connexion requise.")


# Route POST /auth/login.
@router.post("/login")
# Reçoit le JSON validé, la requête et la réponse (pour poser le cookie).
def login(payload: LoginRequest, request: Request, response: Response) -> dict[str, bool]:
    """Vérifie le mot de passe puis pose un cookie HttpOnly, SameSite=Lax, signé et expirant.

    Ordre des contrôles : limite de tentatives par IP (429 + Retry-After), mot de passe non
    configuré (503), mot de passe faux (401). Retour : {"authenticated": true}.
    """
    # Service d'authentification.
    service = _service(request)
    # Adresse IP du client (ou « unknown » si elle est inconnue).
    client_ip = request.client.host if request.client else "unknown"
    # Essaie d'enregistrer la tentative...
    try:
        # ...dans le compteur de cette IP.
        service.limiter.register(client_ip)
    # Trop de tentatives...
    except LoginRateLimitedError as error:
        # ...refus 429...
        raise HTTPException(
            # ...code HTTP...
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            # ...message...
            detail="Trop de tentatives. Patientez une minute avant de réessayer.",
            # ...secondes à attendre.
            headers={"Retry-After": str(error.retry_after_seconds)},
        ) from error
    # Essaie de vérifier le mot de passe...
    try:
        # ...vrai s'il est correct.
        valid = service.verify_password(payload.password)
    # Aucun mot de passe configuré sur le serveur...
    except OwnerPasswordNotConfiguredError as error:
        # ...refus 503 (service indisponible).
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    # Mot de passe faux...
    if not valid:
        # ...refus 401.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Mot de passe incorrect.")
    # httponly : JavaScript ne peut pas lire le cookie (protection contre le vol par script).
    # samesite="lax" : non envoyé par les formulaires d'autres sites. secure : seulement en HTTPS.
    # max_age : durée de vie (8 h).
    # Pose le cookie de session...
    response.set_cookie(
        # ...nom du cookie...
        SESSION_COOKIE_NAME,
        # ...jeton signé...
        service.issue_token(),
        # ...durée de vie...
        max_age=service.ttl_seconds,
        # ...illisible par JavaScript...
        httponly=True,
        # ...pas envoyé par les formulaires d'autres sites...
        samesite="lax",
        # ...réservé au HTTPS quand le site est en HTTPS...
        secure=request.url.scheme == "https",
        # ...valable sur tout le site.
        path="/",
    )
    # Réponse : connecté.
    return {"authenticated": True}


# Route POST /auth/logout.
@router.post("/logout")
# Reçoit la réponse pour effacer le cookie.
def logout(response: Response) -> dict[str, bool]:
    """Supprime le cookie de session (sans erreur si aucune session n'existait)."""
    # Efface le cookie (mêmes options qu'à la création).
    response.delete_cookie(SESSION_COOKIE_NAME, path="/", httponly=True, samesite="lax")
    # Réponse : déconnecté.
    return {"authenticated": False}


# Route GET /auth/me.
@router.get("/me")
# Reçoit la requête pour lire le cookie.
def me(request: Request) -> dict[str, bool]:
    """Indique si la session est valide et si un mot de passe est configuré côté serveur."""
    # Service d'authentification.
    service = _service(request)
    # Réponse JSON...
    return {
        # ...session valide ou non...
        "authenticated": service.validate_token(request.cookies.get(SESSION_COOKIE_NAME)),
        # ...mot de passe configuré ou non.
        "configured": service.is_configured(),
    }

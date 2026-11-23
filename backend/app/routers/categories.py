# Rôle : expose le CRUD des catégories partagées sans mélanger HTTP et SQL.
# Exécution : FastAPI appelle ces routes pour le formulaire et l'écran de gestion.
"""Routes HTTP de gestion des catégories de produits."""

# Annotated : associe un type et une dépendance FastAPI.
from typing import Annotated

# FastAPI : Query lit un paramètre d'URL (?include_inactive=true).
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

# Erreurs métier des catégories.
from app.repositories.base import CategoryConflictError, CategoryNotFoundError
# Schémas JSON reçus et renvoyés...
from app.schemas import (
    # ...création...
    CategoryCreateRequest,
    # ...liste...
    CategoryListResponse,
    # ...une catégorie...
    CategoryResponse,
    # ...modification.
    CategoryUpdateRequest,
)
# Service des catégories et son erreur de validation.
from app.services.category_service import CategoryService, CategoryValidationError

# Groupe de routes préfixées par /categories.
router = APIRouter(prefix="/categories", tags=["categories"])


# Fournit le service aux routes (injection).
def get_category_service(request: Request) -> CategoryService:
    """Retourne le service de catégories créé au démarrage de l'application."""
    # Lu dans app.state.
    return request.app.state.category_service


# Traduit une erreur métier en erreur HTTP.
def _raise_http_error(error: Exception) -> None:
    """Traduit une erreur métier de catégorie en erreur HTTP (404 introuvable, 409 conflit, 422 invalide).

    Les services ne connaissent pas HTTP : c'est le routeur qui choisit le code de réponse.
    """
    # Valeur invalide...
    if isinstance(error, CategoryValidationError):
        # ...422.
        raise HTTPException(status_code=422, detail=str(error)) from error
    # Catégorie introuvable...
    if isinstance(error, CategoryNotFoundError):
        # ...404.
        raise HTTPException(status_code=404, detail=str(error)) from error
    # Conflit (doublon ou catégorie utilisée)...
    if isinstance(error, CategoryConflictError):
        # ...409.
        raise HTTPException(status_code=409, detail=str(error)) from error
    # Autre erreur : on la relance telle quelle.
    raise error


# Route GET /categories.
@router.get("", response_model=CategoryListResponse)
# Liste les catégories...
def list_categories(
    # ...service injecté...
    service: Annotated[CategoryService, Depends(get_category_service)],
    # ...paramètre d'URL facultatif, faux par défaut.
    include_inactive: Annotated[bool, Query(description="Inclure les catégories désactivées.")] = False,
) -> CategoryListResponse:
    """Liste les catégories actives ; le mode gestion peut demander les inactives."""
    # Renvoie la liste enveloppée dans « items ».
    return CategoryListResponse(items=service.list_categories(include_inactive))


# Route POST /categories (réponse 201 Created).
@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
# Crée une catégorie...
def create_category(
    # ...corps JSON validé...
    payload: CategoryCreateRequest,
    # ...service injecté.
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    """Crée une catégorie avec un slug unique et un libellé non vide."""
    # Essaie...
    try:
        # ...de créer la catégorie.
        return service.create(payload.slug, payload.label)
    # Erreur métier...
    except (CategoryValidationError, CategoryConflictError) as error:
        # ...traduite en erreur HTTP.
        _raise_http_error(error)


# Route PATCH /categories/{slug}.
@router.patch("/{slug}", response_model=CategoryResponse)
# Modifie une catégorie...
def update_category(
    # ...slug lu dans l'URL...
    slug: str,
    # ...corps JSON validé...
    payload: CategoryUpdateRequest,
    # ...service injecté.
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    """Renomme, change le slug, ou désactive/réactive une catégorie."""
    # Essaie...
    try:
        # ...la mise à jour...
        return service.update(
            # ...slug actuel...
            slug,
            # ...nouveau slug ou None...
            slug=payload.slug,
            # ...nouveau libellé ou None...
            label=payload.label,
            # ...nouvel état ou None.
            is_active=payload.is_active,
        )
    # Erreur métier...
    except (CategoryValidationError, CategoryNotFoundError, CategoryConflictError) as error:
        # ...traduite en erreur HTTP.
        _raise_http_error(error)


# Route DELETE /categories/{slug} (réponse 204 sans contenu).
@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
# Supprime une catégorie...
def delete_category(
    # ...slug lu dans l'URL...
    slug: str,
    # ...service injecté.
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> Response:
    """Supprime seulement une catégorie qui ne possède aucune génération."""
    # Essaie...
    try:
        # ...la suppression.
        service.delete(slug)
    # Erreur métier...
    except (CategoryNotFoundError, CategoryConflictError) as error:
        # ...traduite en erreur HTTP.
        _raise_http_error(error)
    # Réponse vide 204.
    return Response(status_code=status.HTTP_204_NO_CONTENT)

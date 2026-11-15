# Rôle : expose le CRUD des catégories partagées sans mélanger HTTP et SQL.
# Exécution : FastAPI appelle ces routes pour le formulaire et l'écran de gestion.
"""Routes HTTP de gestion des catégories de produits."""

from typing import Annotated

# FastAPI : Query lit un paramètre d'URL (?include_inactive=true).
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.repositories.base import CategoryConflictError, CategoryNotFoundError
from app.schemas import (
    CategoryCreateRequest,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdateRequest,
)
from app.services.category_service import CategoryService, CategoryValidationError

router = APIRouter(prefix="/categories", tags=["categories"])


def get_category_service(request: Request) -> CategoryService:
    """Retourne le service de catégories créé au démarrage de l'application."""
    return request.app.state.category_service


def _raise_http_error(error: Exception) -> None:
    """Traduit une erreur métier de catégorie en erreur HTTP (404 introuvable, 409 conflit, 422 invalide).

    Les services ne connaissent pas HTTP : c'est le routeur qui choisit le code de réponse.
    """
    if isinstance(error, CategoryValidationError):
        raise HTTPException(status_code=422, detail=str(error)) from error
    if isinstance(error, CategoryNotFoundError):
        raise HTTPException(status_code=404, detail=str(error)) from error
    if isinstance(error, CategoryConflictError):
        raise HTTPException(status_code=409, detail=str(error)) from error
    raise error


@router.get("", response_model=CategoryListResponse)
def list_categories(
    service: Annotated[CategoryService, Depends(get_category_service)],
    include_inactive: Annotated[bool, Query(description="Inclure les catégories désactivées.")] = False,
) -> CategoryListResponse:
    """Liste les catégories actives ; le mode gestion peut demander les inactives."""
    return CategoryListResponse(items=service.list_categories(include_inactive))


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreateRequest,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    """Crée une catégorie avec un slug unique et un libellé non vide."""
    try:
        return service.create(payload.slug, payload.label)
    except (CategoryValidationError, CategoryConflictError) as error:
        _raise_http_error(error)


@router.patch("/{slug}", response_model=CategoryResponse)
def update_category(
    slug: str,
    payload: CategoryUpdateRequest,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryResponse:
    """Renomme, change le slug, ou désactive/réactive une catégorie."""
    try:
        return service.update(
            slug,
            slug=payload.slug,
            label=payload.label,
            is_active=payload.is_active,
        )
    except (CategoryValidationError, CategoryNotFoundError, CategoryConflictError) as error:
        _raise_http_error(error)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    slug: str,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> Response:
    """Supprime seulement une catégorie qui ne possède aucune génération."""
    try:
        service.delete(slug)
    except (CategoryNotFoundError, CategoryConflictError) as error:
        _raise_http_error(error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

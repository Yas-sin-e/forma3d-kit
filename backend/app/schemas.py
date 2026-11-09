# Rôle : définit le contrat JSON renvoyé par les routes du backend.
# Exécution : FastAPI valide et sérialise ce schéma lors de chaque réponse.
"""Schémas des réponses HTTP de Forma3D Studio."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GenerationResponse(BaseModel):
    """État public d'un travail de génération image-vers-GLB."""

    id: str = Field(description="Identifiant de suivi créé par le serveur.")
    status: Literal["PENDING", "RUNNING", "DONE", "FAILED"]
    filename: str = Field(description="Nom de fichier nettoyé, sans chemin local.")
    content_type: Literal["image/jpeg", "image/png", "image/webp"]
    category: str = Field(description="Slug de la catégorie choisie avant l'envoi de la photo.")
    created_at: datetime
    updated_at: datetime
    status_url: str
    model_url: str | None = None
    error_message: str | None = None


class DemoModelResponse(BaseModel):
    """Modèle de faisabilité consultable dans la galerie du viewer."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    filename: str
    category: str
    source: Literal["generated_by_app"]
    size_bytes: int
    model_url: str
    source_image_url: str | None = None


class DemoGalleryResponse(BaseModel):
    """Liste des fichiers GLB réels connus et valides sur ce poste."""

    items: list[DemoModelResponse]


class CategoryResponse(BaseModel):
    """Catégorie partagée exposée au formulaire et à la gestion."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    label: str
    is_active: bool
    created_at: datetime


class CategoryListResponse(BaseModel):
    """Liste de catégories retournée par l'API."""

    items: list[CategoryResponse]


class CategoryCreateRequest(BaseModel):
    """Valeurs à fournir pour créer une catégorie."""

    slug: str
    label: str


class CategoryUpdateRequest(BaseModel):
    """Champs facultatifs modifiables sur une catégorie existante."""

    slug: str | None = None
    label: str | None = None
    is_active: bool | None = None

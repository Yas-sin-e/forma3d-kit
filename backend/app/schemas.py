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
    content_type: str
    category: str = Field(description="Slug de la catégorie choisie avant l'envoi de la photo.")
    created_at: datetime
    updated_at: datetime
    status_url: str
    model_url: str | None = None
    error_message: str | None = None
    duration_seconds: float | None = None
    image_warning: str | None = Field(
        default=None,
        description="Avertissement non bloquant issu de la préparation locale de la photo.",
    )
    origin: Literal["generated", "imported", "example"] = "generated"
    public_id: str | None = None
    embed_enabled: bool = False


class DemoModelResponse(BaseModel):
    """Modèle de faisabilité consultable dans la galerie du viewer."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    filename: str
    category: str
    source: Literal["generated_by_app", "imported", "example"]
    origin: Literal["generated", "imported", "example"] = "example"
    created_at: datetime | None = None
    size_bytes: int
    model_url: str
    source_image_url: str | None = None
    public_id: str | None = None
    embed_enabled: bool = False


class EmbedIntegrationRequest(BaseModel):
    """Demande d'activation ou de désactivation pour une fiche terminée."""

    enabled: bool


class PublicModelResponse(BaseModel):
    """Métadonnées minimales exposées lorsque l'intégration est activée."""

    public_id: str
    name: str
    filename: str
    category: str
    origin: Literal["generated", "imported", "example"]
    created_at: datetime
    model_url: str


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


class APIKeyCreateRequest(BaseModel):
    """Nom donné par la propriétaire à une nouvelle clé API."""

    name: str = Field(min_length=1, max_length=80)


class APIKeyResponse(BaseModel):
    """Métadonnées d’une clé sans sa valeur secrète ni son empreinte."""

    id: str
    name: str
    prefix: str
    created_at: datetime
    revoked: bool


class APIKeyCreatedResponse(APIKeyResponse):
    """Réponse de création contenant le secret, qui n’est renvoyé qu’ici."""

    key: str


class APIKeyListResponse(BaseModel):
    """Collection des clés connues pour la page de gestion du Studio."""

    items: list[APIKeyResponse]


class APIModelResponse(BaseModel):
    """État d'un modèle visible par une clé API, avec des URL versionnées."""

    id: str
    status: Literal["PENDING", "RUNNING", "DONE", "FAILED"]
    filename: str
    category: str
    created_at: datetime
    updated_at: datetime
    status_url: str
    model_url: str | None = None
    error_message: str | None = None
    duration_seconds: float | None = None
    public_id: str | None = None
    embed_enabled: bool = False


class APIIntegrationCodeResponse(BaseModel):
    """Code iframe prêt à copier pour un modèle déjà activé."""

    public_id: str
    iframe_html: str
    widget_html: str

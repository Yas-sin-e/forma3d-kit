# Rôle : décrit les catégories et les générations conservées par l'application.
# Exécution : le dépôt PostgreSQL reconstruit ces objets pour GenerationService et les routes.
"""Modèles métier des catégories et des générations image-vers-GLB."""

# dataclasses (standard) : classes de données générées (constructeur, égalité). Équivalent d'un record Java.
from dataclasses import dataclass
from datetime import datetime
# enum.StrEnum (standard) : énumération dont chaque valeur est aussi une chaîne (pratique pour SQL et JSON).
from enum import StrEnum
from pathlib import Path


# frozen=True : objet immuable ; slots=True : seuls les attributs déclarés existent.
# Pour « modifier » un enregistrement, on en crée une copie avec dataclasses.replace().
@dataclass(frozen=True, slots=True)
class CategoryRecord:
    """Catégorie persistée, éventuellement masquée aux nouveaux uploads."""

    id: int
    slug: str
    label: str
    is_active: bool
    created_at: datetime


# Machine à états d'un modèle : PENDING -> RUNNING -> DONE ou FAILED.
class GenerationStatus(StrEnum):
    """États publics du parcours asynchrone de génération."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class ModelOrigin(StrEnum):
    """Origine persistée d'un modèle visible dans la bibliothèque."""

    GENERATED = "generated"
    IMPORTED = "imported"
    EXAMPLE = "example"


class ProductCategory(StrEnum):
    """Catégories de mobilier prises en charge par le Sprint 1."""

    CHAIR = "chair"
    STOOL = "stool"
    SIDE_TABLE = "side-table"


@dataclass(frozen=True, slots=True)
class GenerationRecord:
    """Métadonnées persistées d'une génération et de ses fichiers locaux."""

    id: str
    status: GenerationStatus
    filename: str
    content_type: str
    category: str
    image_path: Path | None
    created_at: datetime
    updated_at: datetime
    model_path: Path | None = None
    error_message: str | None = None
    duration_seconds: float | None = None
    image_warning: str | None = None
    origin: ModelOrigin = ModelOrigin.GENERATED
    public_id: str | None = None
    embed_enabled: bool = False


@dataclass(frozen=True, slots=True)
class APIKeyRecord:
    """Métadonnées persistées d'une clé API sans sa valeur secrète."""

    id: str
    name: str
    prefix: str
    fingerprint: str
    created_at: datetime
    revoked: bool = False

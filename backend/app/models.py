# Rôle : décrit les catégories et les générations conservées par l'application.
# Exécution : le dépôt SQLite reconstruit ces objets pour GenerationService et les routes.
"""Modèles métier des catégories et des générations image-vers-GLB."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path


class GenerationStatus(StrEnum):
    """États publics du parcours asynchrone de génération."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


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
    category: ProductCategory
    image_path: Path
    created_at: datetime
    updated_at: datetime
    model_path: Path | None = None
    error_message: str | None = None
    duration_seconds: float | None = None

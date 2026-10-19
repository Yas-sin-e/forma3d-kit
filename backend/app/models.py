# Rôle : décrit un travail de génération et ses états en mémoire.
# Exécution : GenerationService crée et met à jour ces objets pendant le processus API.
"""Modèle de données en mémoire pour les demandes de génération du Sprint 1."""

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


@dataclass(frozen=True, slots=True)
class GenerationRecord:
    """Métadonnées gardées pendant la vie du serveur, sans base de données."""

    id: str
    status: GenerationStatus
    filename: str
    content_type: str
    image_path: Path
    created_at: datetime
    updated_at: datetime
    model_path: Path | None = None
    error_message: str | None = None

# Rôle : définit le contrat JSON renvoyé par les routes du backend.
# Exécution : FastAPI valide et sérialise ce schéma lors de chaque réponse.
"""Schémas des réponses HTTP de Forma3D Studio."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class GenerationResponse(BaseModel):
    """État public d'un travail de génération image-vers-GLB."""

    id: str = Field(description="Identifiant de suivi créé par le serveur.")
    status: Literal["PENDING", "RUNNING", "DONE", "FAILED"]
    filename: str = Field(description="Nom de fichier nettoyé, sans chemin local.")
    content_type: Literal["image/jpeg", "image/png", "image/webp"]
    created_at: datetime
    updated_at: datetime
    status_url: str
    model_url: str | None = None
    error_message: str | None = None

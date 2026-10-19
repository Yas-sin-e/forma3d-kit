# Rôle : définit le contrat de stockage utilisé par la génération.
# Exécution : GenerationService type sa dépendance sur cette interface.
"""Contrat de persistance des photos et des modèles GLB."""

from pathlib import Path
from typing import Protocol


class Storage(Protocol):
    """Interface minimale de stockage utilisée par GenerationService."""

    def save_image(self, generation_id: str, extension: str, content: bytes) -> Path:
        """Enregistre la photo validée et renvoie son chemin local."""
        ...

    def save_model(self, generation_id: str, content: bytes) -> Path:
        """Enregistre les octets GLB retournés par un Image3DProvider."""
        ...

    def get_model_path(self, generation_id: str) -> Path | None:
        """Renvoie le modèle présent, ou None si aucun modèle n'est enregistré."""
        ...

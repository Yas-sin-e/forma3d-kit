# Rôle : définit le contrat de stockage utilisé par la génération.
# Exécution : GenerationService type sa dépendance sur cette interface.
"""Contrat de persistance des photos et des modèles GLB."""

# Path : type des chemins renvoyés par le stockage.
from pathlib import Path
# typing.Protocol (standard) : interface du stockage de fichiers (disque local aujourd'hui,
# stockage d'objets demain) ; GenerationService ne connaît que ce contrat.
from typing import Protocol


# Contrat du stockage : toute classe qui possède ces quatre méthodes convient.
class Storage(Protocol):
    """Interface minimale de stockage utilisée par GenerationService."""

    # Enregistre la photo reçue et renvoie son chemin.
    def save_image(self, generation_id: str, extension: str, content: bytes) -> Path:
        """Enregistre la photo validée et renvoie son chemin local."""
        ...

    # Enregistre le GLB produit et renvoie son chemin.
    def save_model(self, generation_id: str, content: bytes) -> Path:
        """Enregistre les octets GLB retournés par un Image3DProvider."""
        ...

    # Renvoie le chemin du GLB s'il existe, sinon None.
    def get_model_path(self, generation_id: str) -> Path | None:
        """Renvoie le modèle présent, ou None si aucun modèle n'est enregistré."""
        ...

    # Efface les fichiers (GLB et photo) d'une génération.
    def delete_files(self, generation_id: str) -> None:
        """Supprime le GLB et la photo source d'une génération, s'ils existent."""
        ...

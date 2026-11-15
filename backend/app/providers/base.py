# Rôle : définit le contrat commun des fournisseurs de génération 3D.
# Exécution : les services typent leur dépendance sur ce contrat.
"""Contrat commun pour transformer une image en octets GLB."""

from pathlib import Path
# typing.Protocol (standard) : décrit une interface. Toute classe qui possède ces méthodes convient,
# sans mot-clé « implements » (typage structurel). Équivalent d'une interface Java.
from typing import Protocol


class ProviderError(RuntimeError):
    """Erreur compréhensible émise par un fournisseur image-vers-3D."""


class Image3DProvider(Protocol):
    """Interface d'un fournisseur image-vers-GLB pré-entraîné."""

    def generate(self, image_path: Path) -> bytes:
        """Renvoie un modèle GLB réellement produit pour cette image."""
        ...

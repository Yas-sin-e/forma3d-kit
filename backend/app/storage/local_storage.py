# Rôle : écrit et lit les photos et les GLB dans backend/storage/.
# Exécution : GenerationService l'utilise après validation et génération.
"""Stockage local atomique des fichiers d'une génération."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID, uuid4

_ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class LocalStorage:
    """Conserve les fichiers sous un dossier dédié au backend."""

    def __init__(self, root: Path | None = None) -> None:
        default_root = Path(__file__).resolve().parents[2] / "storage"
        self.root = (root or default_root).resolve()
        self.images_dir = self.root / "images"
        self.models_dir = self.root / "models"

    def save_image(self, generation_id: str, extension: str, content: bytes) -> Path:
        """Écrit une image validée avec un nom choisi par le serveur."""
        self._validate_generation_id(generation_id)
        normalized_extension = extension.lower()
        if normalized_extension not in _ALLOWED_IMAGE_EXTENSIONS:
            raise ValueError("Extension d'image non autorisée pour le stockage local.")
        if not content:
            raise ValueError("Impossible d'enregistrer une image vide.")
        destination = self.images_dir / f"{generation_id}{normalized_extension}"
        self._write_atomically(destination, content)
        return destination

    def save_model(self, generation_id: str, content: bytes) -> Path:
        """Écrit le GLB déjà contrôlé par Image3DProvider."""
        self._validate_generation_id(generation_id)
        if not content:
            raise ValueError("Impossible d'enregistrer un modèle vide.")
        destination = self.models_dir / f"{generation_id}.glb"
        if destination.exists():
            raise FileExistsError("Un modèle portant cet identifiant existe déjà.")
        self._write_atomically(destination, content)
        return destination

    def get_model_path(self, generation_id: str) -> Path | None:
        """Retourne le chemin d'un GLB présent sans accepter de chemin client."""
        self._validate_generation_id(generation_id)
        path = self.models_dir / f"{generation_id}.glb"
        return path if path.is_file() else None

    def delete_files(self, generation_id: str) -> None:
        """Efface le GLB et la photo source ; les noms sont reconstruits par le serveur, jamais reçus du client."""
        self._validate_generation_id(generation_id)
        candidates = [self.models_dir / f"{generation_id}.glb"]
        candidates += [self.images_dir / f"{generation_id}{extension}" for extension in sorted(_ALLOWED_IMAGE_EXTENSIONS)]
        for path in candidates:
            path.unlink(missing_ok=True)

    @staticmethod
    def _validate_generation_id(generation_id: str) -> None:
        """Refuse toute valeur qui n'est pas un UUID généré par l'application."""
        try:
            UUID(generation_id)
        except (ValueError, AttributeError) as error:
            raise ValueError("Identifiant de génération invalide.") from error

    @staticmethod
    def _write_atomically(destination: Path, content: bytes) -> None:
        """Écrit dans un fichier temporaire du même dossier puis le renomme."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
        try:
            with temporary_path.open("xb") as temporary_file:
                temporary_file.write(content)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.link(temporary_path, destination)
            temporary_path.unlink()
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

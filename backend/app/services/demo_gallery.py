# Rôle : ne publie qu'une liste fixe de GLB réels générés pendant la faisabilité.
# Exécution : la route /models/gallery liste ces fichiers et les routes de lecture résolvent leur identifiant.
"""Catalogue borné des modèles GLB de démonstration présents sur le poste."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_DEMO_FILES = (
    ("chair-bentwood", "Chaise en bois cintré", "chair", "chair-bentwood.glb"),
    ("chair-metal-01", "Chaise métal 01", "chair", "chair-met-01.glb"),
    ("chair-metal-02", "Chaise métal 02", "chair", "chair-met-02.glb"),
    ("side-table-metal", "Table d’appoint en métal", "side-table", "side-table-met.glb"),
    ("stool-metal-01", "Tabouret métal 01", "stool", "stool-met-01.glb"),
)
_JSON_CHUNK_TYPE = 0x4E4F534A


@dataclass(frozen=True, slots=True)
class DemoModel:
    """Métadonnées publiques d'un modèle de faisabilité réellement disponible."""

    id: str
    name: str
    filename: str
    category: str
    source: str
    size_bytes: int
    model_url: str


class DemoGallery:
    """Résout uniquement les cinq noms connus, sans exposer de chemin arbitraire."""

    def __init__(self, root: Path | None = None) -> None:
        default_root = Path(__file__).resolve().parents[2] / "data" / "feasibility-results"
        self.root = (root or default_root).resolve()

    def list_models(self) -> list[DemoModel]:
        """Retourne les modèles dont le fichier existe et porte une structure GLB 2.0."""
        models = []
        for model_id, name, category, filename in _DEMO_FILES:
            path = self.root / filename
            if not path.is_file() or not self._is_valid_glb_2(path):
                continue
            models.append(
                DemoModel(
                    id=model_id,
                    name=name,
                    filename=filename,
                    category=category,
                    source="generated_by_app",
                    size_bytes=path.stat().st_size,
                    model_url=f"/models/gallery/{model_id}",
                )
            )
        return models

    def get_model_path(self, model_id: str) -> Path | None:
        """Renvoie le chemin d'un seul identifiant autorisé si son GLB reste valide."""
        entry = next((item for item in _DEMO_FILES if item[0] == model_id), None)
        if entry is None:
            return None
        path = self.root / entry[3]
        return path if path.is_file() and self._is_valid_glb_2(path) else None

    @staticmethod
    def _is_valid_glb_2(path: Path) -> bool:
        """Vérifie l'en-tête, le JSON glTF 2.0 et les limites de chaque chunk."""
        try:
            data = path.read_bytes()
        except OSError:
            return False
        if len(data) < 20 or data[:4] != b"glTF":
            return False
        if int.from_bytes(data[4:8], "little") != 2:
            return False
        if int.from_bytes(data[8:12], "little") != len(data):
            return False

        json_length = int.from_bytes(data[12:16], "little")
        json_end = 20 + json_length
        if (
            int.from_bytes(data[16:20], "little") != _JSON_CHUNK_TYPE
            or json_length == 0
            or json_length % 4 != 0
            or json_end > len(data)
        ):
            return False
        try:
            document = json.loads(data[20:json_end].decode("utf-8").rstrip(" \t\r\n\0"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return False
        if not isinstance(document, dict) or not isinstance(document.get("asset"), dict):
            return False
        if document["asset"].get("version") != "2.0":
            return False

        offset = json_end
        while offset < len(data):
            if offset + 8 > len(data):
                return False
            chunk_length = int.from_bytes(data[offset : offset + 4], "little")
            if chunk_length % 4 != 0 or offset + 8 + chunk_length > len(data):
                return False
            offset += 8 + chunk_length
        return offset == len(data)

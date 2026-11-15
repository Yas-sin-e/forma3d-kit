# Rôle : vérifie que l'API ne publie et ne sert que les GLB réels de la liste autorisée.
# Exécution : Pytest prépare des fichiers GLB temporaires et appelle les routes sans réseau.
"""Tests locaux du catalogue de modèles de démonstration."""

import json
import struct
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.routers.models import get_demo_gallery, get_generation_service
from app.services.demo_gallery import DemoGallery


class _NoGenerations:
    """Remplace le service réel : la base SQLite locale de la développeuse n'entre pas dans ces tests."""

    def list_completed_generations(self) -> list:
        """Aucune génération enregistrée : la galerie testée ne contient que les exemples."""
        return []


@pytest.fixture(autouse=True)
def isolate_from_local_generations():
    """Sans cela, un modèle réellement généré dans backend/data/ apparaît dans la galerie testée."""
    app.dependency_overrides[get_generation_service] = _NoGenerations
    yield
    app.dependency_overrides.pop(get_generation_service, None)


def _minimal_glb_20() -> bytes:
    """Construit un conteneur glTF 2.0 minimal pour tester le contrat local."""
    document = json.dumps({"asset": {"version": "2.0"}}, separators=(",", ":")).encode()
    document += b" " * (-len(document) % 4)
    json_chunk = struct.pack("<I4s", len(document), b"JSON") + document
    return struct.pack("<4sII", b"glTF", 2, 12 + len(json_chunk)) + json_chunk


def test_gallery_lists_only_existing_valid_allowlisted_glb_files(tmp_path: Path) -> None:
    """Prouve que la galerie ne liste que les GLB autorisés, présents et valides."""
    valid_glb = _minimal_glb_20()
    (tmp_path / "chair-bentwood.glb").write_bytes(valid_glb)
    (tmp_path / "chair-met-01.glb").write_bytes(b"not a GLB")
    (tmp_path / "unlisted-chair.glb").write_bytes(valid_glb)
    app.dependency_overrides[get_demo_gallery] = lambda: DemoGallery(tmp_path)
    try:
        response = TestClient(app).get("/models/gallery")
    finally:
        app.dependency_overrides.pop(get_demo_gallery, None)

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": "chair-bentwood",
                "name": "Chaise en bois cintré",
                "filename": "chair-bentwood.glb",
                "category": "chair",
                "source": "example",
                "origin": "example",
                "created_at": None,
                "size_bytes": len(valid_glb),
                "model_url": "/models/gallery/chair-bentwood",
                "source_image_url": None,
                "public_id": None,
                "embed_enabled": False,
            }
        ]
    }


def test_gallery_download_serves_the_real_allowlisted_glb(tmp_path: Path) -> None:
    """Prouve que le téléchargement d'un exemple renvoie le vrai fichier GLB autorisé."""
    valid_glb = _minimal_glb_20()
    (tmp_path / "stool-met-01.glb").write_bytes(valid_glb)
    app.dependency_overrides[get_demo_gallery] = lambda: DemoGallery(tmp_path)
    try:
        response = TestClient(app).get("/models/gallery/stool-metal-01")
    finally:
        app.dependency_overrides.pop(get_demo_gallery, None)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("model/gltf-binary")
    assert response.content == valid_glb


def test_gallery_lists_and_serves_source_photo_only_when_present(tmp_path: Path) -> None:
    """Prouve que la photo source d'un exemple n'est proposée que si elle existe."""
    valid_glb = _minimal_glb_20()
    (tmp_path / "chair-met-01.glb").write_bytes(valid_glb)
    source_dir = tmp_path.parent / "feasibility-inputs"
    source_dir.mkdir()
    source_bytes = b"\xff\xd8\xffphoto source fixture"
    (source_dir / "chair-met-01.jpg").write_bytes(source_bytes)
    app.dependency_overrides[get_demo_gallery] = lambda: DemoGallery(tmp_path)
    try:
        client = TestClient(app)
        listing = client.get("/models/gallery")
        photo = client.get("/models/gallery/chair-metal-01/source-image")
    finally:
        app.dependency_overrides.pop(get_demo_gallery, None)

    assert listing.status_code == 200
    assert listing.json()["items"][0]["source_image_url"] == "/models/gallery/chair-metal-01/source-image"
    assert photo.status_code == 200
    assert photo.headers["content-type"].startswith("image/jpeg")
    assert photo.content == source_bytes


def test_gallery_refuses_unknown_or_invalid_models(tmp_path: Path) -> None:
    """Prouve qu'un exemple inconnu, un chemin piège ou un GLB invalide donne 404."""
    (tmp_path / "chair-bentwood.glb").write_bytes(b"not a GLB")
    app.dependency_overrides[get_demo_gallery] = lambda: DemoGallery(tmp_path)
    try:
        client = TestClient(app)
        listing = client.get("/models/gallery")
        unknown = client.get("/models/gallery/../../secret")
        invalid = client.get("/models/gallery/chair-bentwood")
    finally:
        app.dependency_overrides.pop(get_demo_gallery, None)

    assert listing.status_code == 200
    assert listing.json()["items"] == []
    assert unknown.status_code == 404
    assert invalid.status_code == 404

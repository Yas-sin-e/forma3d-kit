# Rôle : vérifie la page iframe, le statut d’activation et la CSP frame-ancestors.
# Exécution : Pytest utilise un GLB minimal et un dépôt SQLite temporaires, sans réseau externe.
"""Tests HTTP de la page viewer qui sera intégrée dans les sites clients."""

import json
import struct
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.routers.models import get_generation_service
from app.repositories.sqlite_repository import SQLiteGenerationRepository
from app.services.generation_service import GenerationService
from app.storage.local_storage import LocalStorage


def _valid_glb() -> bytes:
    """Construit un conteneur GLB 2.0 minimal pour le test d’import."""
    document = json.dumps({"asset": {"version": "2.0"}}, separators=(",", ":")).encode()
    document += b" " * (-len(document) % 4)
    chunk = struct.pack("<I4s", len(document), b"JSON") + document
    return struct.pack("<4sII", b"glTF", 2, 12 + len(chunk)) + chunk


def test_embed_page_requires_activation_and_sets_restrictive_frame_ancestors(tmp_path: Path) -> None:
    repository = SQLiteGenerationRepository(tmp_path / "embed.sqlite3")
    repository.initialize()
    service = GenerationService(object(), LocalStorage(tmp_path / "storage"), repository)
    app.dependency_overrides[get_generation_service] = lambda: service
    previous_origins = app.state.embed_allowed_origins
    app.state.embed_allowed_origins = ("https://shop.example",)
    try:
        with TestClient(app) as client:
            imported = client.post(
                "/models/import",
                files={"file": ("fixture.glb", _valid_glb(), "model/gltf-binary")},
                data={"title": "Chaise test", "category": "chair"},
            ).json()
            public_id = imported["public_id"]
            unavailable = client.get(f"/embed/{public_id}")
            assert unavailable.status_code == 404
            assert "Ce modèle 3D n’est pas disponible" in unavailable.text
            assert unavailable.headers["content-security-policy"] == "frame-ancestors 'self' https://shop.example"

            enabled = client.patch(f"/models/{imported['id']}/integration", json={"enabled": True})
            assert enabled.status_code == 200
            view = client.get(f"/embed/{public_id}?auto-rotate=1")
            assert view.status_code == 200
            assert f"/public/models/{public_id}/glb" in view.text
            assert "<model-viewer" in view.text and "auto-rotate" in view.text
            assert "<header" not in view.text and "#app" not in view.text
            assert view.headers["content-security-policy"] == "frame-ancestors 'self' https://shop.example"
            assert view.headers["cache-control"] == "no-store"
            assert view.headers["x-content-type-options"] == "nosniff"

            disabled = client.patch(f"/models/{imported['id']}/integration", json={"enabled": False})
            assert disabled.status_code == 200
            assert client.get(f"/embed/{public_id}").status_code == 404
            assert client.get("/embed/unknown-public-id").status_code == 404

            app.state.embed_allowed_origins = ()
            same_origin_only = client.get("/embed/unknown-public-id")
            assert same_origin_only.headers["content-security-policy"] == "frame-ancestors 'self'"
    finally:
        app.dependency_overrides.pop(get_generation_service, None)
        app.state.embed_allowed_origins = previous_origins

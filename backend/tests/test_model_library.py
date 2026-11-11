# Rôle : vérifie l'import GLB, la copie d'exemples et la migration de provenance.
# Exécution : Pytest utilise des fichiers temporaires et des requêtes locales sans fournisseur.
"""Tests de l'import et de la bibliothèque unifiée de modèles."""

from __future__ import annotations

import json
import sqlite3
import struct
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.models import get_demo_gallery, get_generation_service
from app.repositories.sqlite_repository import SQLiteGenerationRepository
from app.services.demo_gallery import DemoGallery
from app.services.generation_service import GenerationService
from app.storage.local_storage import LocalStorage


def _valid_glb() -> bytes:
    """Construit le plus petit conteneur glTF 2.0 structurellement valide pour les tests."""
    document = json.dumps({"asset": {"version": "2.0"}}, separators=(",", ":")).encode()
    document += b" " * (-len(document) % 4)
    chunk = struct.pack("<I4s", len(document), b"JSON") + document
    return struct.pack("<4sII", b"glTF", 2, 12 + len(chunk)) + chunk


@pytest.fixture
def library_client(tmp_path: Path):
    """Configure un client local, un dépôt temporaire et un petit plafond d'upload."""
    database = SQLiteGenerationRepository(tmp_path / "library.sqlite3")
    database.initialize()
    storage = LocalStorage(tmp_path / "storage")
    service = GenerationService(provider=object(), storage=storage, repository=database)
    gallery = DemoGallery(tmp_path / "examples")
    previous_limit = getattr(app.state, "max_glb_upload_bytes", None)
    app.state.max_glb_upload_bytes = 1024
    app.dependency_overrides[get_generation_service] = lambda: service
    app.dependency_overrides[get_demo_gallery] = lambda: gallery
    with TestClient(app) as client:
        yield client, database, storage, gallery
    app.dependency_overrides.pop(get_generation_service, None)
    app.dependency_overrides.pop(get_demo_gallery, None)
    if previous_limit is not None:
        app.state.max_glb_upload_bytes = previous_limit


def test_import_glb_is_saved_with_random_name_and_appears_in_library(library_client) -> None:
    client, repository, storage, _ = library_client
    response = client.post(
        "/models/import",
        files={"file": ("C:\\private\\Chair.glb", _valid_glb(), "model/gltf-binary")},
        data={"title": "../Chaise de jardin", "category": "chair"},
    )

    assert response.status_code == 201
    record = response.json()
    assert record["status"] == "DONE"
    assert record["origin"] == "imported"
    assert UUID(record["public_id"]).version == 4
    assert record["embed_enabled"] is False
    assert record["filename"] == "Chaise de jardin.glb"
    assert Path(record["model_url"]).name == "glb"
    stored = storage.get_model_path(record["id"])
    assert stored is not None and stored.name != "Chair.glb"
    assert stored.stem == record["id"]
    assert stored.read_bytes() == _valid_glb()
    persisted = repository.get_generation(record["id"])
    assert persisted is not None and persisted.image_path is None
    assert persisted.public_id == record["public_id"]
    assert persisted.embed_enabled is False
    gallery = client.get("/models/gallery").json()["items"]
    assert any(item["id"] == record["id"] and item["origin"] == "imported" for item in gallery)
    detail = client.get(f"/models/{record['id']}").json()
    assert detail["status"] == "DONE" and detail["origin"] == "imported"
    assert detail["duration_seconds"] is None
    assert client.get(f"/models/{record['id']}/glb").content == _valid_glb()
    assert client.get(f"/models/{record['id']}/source-image").status_code == 404
    default_title = client.post(
        "/models/import",
        files={"file": ("New_stool-01.glb", _valid_glb(), "model/gltf-binary")},
        data={"category": "stool"},
    )
    assert default_title.status_code == 201
    assert default_title.json()["filename"] == "New stool 01.glb"


@pytest.mark.parametrize(
    ("filename", "content", "expected_status"),
    [("model.obj", _valid_glb(), 415), ("broken.glb", b"not a GLB", 422)],
)
def test_import_rejects_non_glb_files(library_client, filename, content, expected_status) -> None:
    client, *_ = library_client
    response = client.post(
        "/models/import",
        files={"file": (filename, content, "application/octet-stream")},
        data={"title": "Essai", "category": "chair"},
    )
    assert response.status_code == expected_status
    assert response.json()["detail"]


def test_import_rejects_a_file_above_the_configured_size(library_client) -> None:
    client, *_ = library_client
    app.state.max_glb_upload_bytes = 16
    response = client.post(
        "/models/import",
        files={"file": ("large.glb", _valid_glb(), "model/gltf-binary")},
        data={"title": "Trop gros", "category": "chair"},
    )
    assert response.status_code == 413
    assert "taille maximale" in response.json()["detail"]


@pytest.mark.parametrize("category", ["unknown", "inactive"])
def test_import_rejects_unknown_or_inactive_categories(library_client, category) -> None:
    client, repository, *_ = library_client
    if category == "inactive":
        repository.update_category("stool", is_active=False)
        selected_category = "stool"
    else:
        selected_category = "does-not-exist"
    response = client.post(
        "/models/import",
        files={"file": ("model.glb", _valid_glb(), "model/gltf-binary")},
        data={"title": "Objet", "category": selected_category},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Cette catégorie est inconnue ou désactivée."


def test_copy_example_preserves_example_origin_and_uses_separate_file(library_client) -> None:
    client, repository, storage, gallery = library_client
    gallery.root.mkdir(parents=True)
    source = gallery.root / "chair-bentwood.glb"
    source.write_bytes(_valid_glb())
    response = client.post(
        "/models/examples/chair-bentwood/copy",
        data={"title": "Chaise cintrée", "category": "chair"},
    )
    assert response.status_code == 201
    copied = response.json()
    assert copied["origin"] == "example"
    assert copied["status"] == "DONE"
    model_path = storage.get_model_path(copied["id"])
    assert model_path is not None and model_path != source
    assert model_path.read_bytes() == source.read_bytes()
    assert repository.get_generation(copied["id"]).origin.value == "example"
    assert UUID(copied["public_id"]).version == 4
    assert copied["embed_enabled"] is False


def test_public_model_and_glb_require_explicit_integration_activation(library_client) -> None:
    client, repository, _, _ = library_client
    imported = client.post(
        "/models/import",
        files={"file": ("model.glb", _valid_glb(), "model/gltf-binary")},
        data={"title": "Lampe test", "category": "chair"},
    ).json()
    public_id = imported["public_id"]
    metadata_url = f"/public/models/{public_id}"

    assert client.get(metadata_url).status_code == 404
    assert client.get(metadata_url + "/glb").status_code == 404

    activated = client.patch(
        f"/models/{imported['id']}/integration",
        json={"enabled": True},
    )
    assert activated.status_code == 200
    assert activated.json()["embed_enabled"] is True
    assert activated.json()["public_id"] == public_id

    metadata = client.get(metadata_url)
    assert metadata.status_code == 200
    assert metadata.json() == {
        "public_id": public_id,
        "name": "Lampe test",
        "filename": "Lampe test.glb",
        "category": "chair",
        "origin": "imported",
        "created_at": imported["created_at"],
        "model_url": f"/public/models/{public_id}/glb",
    }
    assert imported["id"] not in metadata.text
    assert "source_image" not in metadata.text
    assert client.get(metadata.json()["model_url"]).content == _valid_glb()

    deactivated = client.patch(
        f"/models/{imported['id']}/integration",
        json={"enabled": False},
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["public_id"] == public_id
    assert deactivated.json()["embed_enabled"] is False
    assert repository.get_generation(imported["id"]).embed_enabled is False
    assert client.get(metadata_url).status_code == 404
    assert client.get(metadata_url + "/glb").status_code == 404


def test_initialize_migrates_origin_without_losing_existing_generation(tmp_path: Path) -> None:
    database_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT NOT NULL UNIQUE,
                label TEXT NOT NULL, is_active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL
            );
            CREATE TABLE generations (
                id TEXT PRIMARY KEY, category_id INTEGER NOT NULL REFERENCES categories(id),
                status TEXT NOT NULL, filename TEXT NOT NULL, content_type TEXT NOT NULL,
                source_photo_path TEXT NOT NULL, glb_path TEXT, duration_seconds REAL,
                error_message TEXT, image_warning TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            INSERT INTO categories (id, slug, label, is_active, created_at)
                VALUES (1, 'chair', 'Chaise', 1, '2026-01-01T00:00:00+00:00');
            INSERT INTO generations (id, category_id, status, filename, content_type,
                source_photo_path, glb_path, duration_seconds, error_message, image_warning,
                created_at, updated_at)
                VALUES ('existing-id', 1, 'DONE', 'old.png', 'image/png', 'old.png', 'old.glb',
                4.5, NULL, NULL, '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00');
            """
        )

    repository = SQLiteGenerationRepository(database_path)
    repository.initialize()
    with sqlite3.connect(database_path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(generations)")}
        old = connection.execute(
            "SELECT filename, glb_path, duration_seconds, origin, public_id, embed_enabled "
            "FROM generations WHERE id='existing-id'"
        ).fetchone()
    restored = repository.get_generation("existing-id")

    assert "origin" in columns
    assert old[:4] == ("old.png", "old.glb", 4.5, "generated")
    assert UUID(old[4]).version == 4
    assert old[5] == 0
    assert restored is not None and restored.filename == "old.png"
    assert restored.model_path == Path("old.glb")
    assert restored.public_id == old[4]
    assert restored.embed_enabled is False

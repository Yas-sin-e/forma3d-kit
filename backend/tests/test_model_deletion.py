# Rôle : vérifie la suppression définitive d'un modèle (ligne SQLite, GLB, photo source) et ses refus.
# Exécution : Pytest appelle FastAPI en mémoire avec un dépôt et un stockage temporaires, sans réseau.
"""Tests de DELETE /models/{id}, de GenerationService.delete_generation et du stockage associé."""

import json
import struct
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories.sqlite_repository import SQLiteGenerationRepository
from app.routers.models import get_generation_service
from app.services.generation_service import GenerationService
from app.services.upload_validator import ValidatedUpload
from app.storage.local_storage import LocalStorage


class SuccessfulProvider:
    """Fournisseur simulé : renvoie un GLB 2.0 minimal, ce n'est pas une vraie génération."""

    def generate(self, image_path: Path) -> bytes:
        """Faux fournisseur : remplace l'appel au service d'IA (aucun réseau, aucune vraie génération)."""
        document = json.dumps({"asset": {"version": "2.0"}}, separators=(",", ":")).encode()
        document += b" " * (-len(document) % 4)
        json_chunk = struct.pack("<I4s", len(document), b"JSON") + document
        return struct.pack("<4sII", b"glTF", 2, 12 + len(json_chunk)) + json_chunk


PNG_BYTES = b"\x89PNG\r\n\x1a\nsample"


@pytest.fixture
def setup(tmp_path: Path):
    """Service réel sur un dépôt SQLite et un dossier de stockage temporaires."""
    # tmp_path (fixture pytest) : dossier temporaire propre à ce test, effacé ensuite.
    # La vraie base backend/data/ n'est jamais touchée.
    repository = SQLiteGenerationRepository(tmp_path / "history.sqlite3")
    repository.initialize()
    storage = LocalStorage(tmp_path / "storage")
    service = GenerationService(SuccessfulProvider(), storage, repository)
    app.dependency_overrides[get_generation_service] = lambda: service
    yield TestClient(app), service, storage
    app.dependency_overrides.pop(get_generation_service, None)


def _create_done_model(client: TestClient) -> str:
    """Crée par l'API un modèle terminé (fournisseur simulé) et renvoie son identifiant."""
    response = client.post(
        "/models",
        files={"file": ("chair.png", PNG_BYTES, "image/png")},
        data={"category": "chair"},
    )
    assert response.status_code == 202
    generation_id = response.json()["id"]
    assert client.get(f"/models/{generation_id}").json()["status"] == "DONE"
    return generation_id


def test_delete_removes_row_glb_and_source_photo(setup) -> None:
    """Prouve que la suppression efface la ligne SQLite, le GLB et la photo source."""
    client, _service, storage = setup
    generation_id = _create_done_model(client)
    glb_path = storage.models_dir / f"{generation_id}.glb"
    photo_path = storage.images_dir / f"{generation_id}.png"
    assert glb_path.is_file() and photo_path.is_file()

    response = client.delete(f"/models/{generation_id}")

    assert response.status_code == 204
    assert not glb_path.exists()
    assert not photo_path.exists()
    assert client.get(f"/models/{generation_id}").status_code == 404
    gallery_ids = [item["id"] for item in client.get("/models/gallery").json()["items"]]
    assert generation_id not in gallery_ids


def test_deleted_model_is_no_longer_public_even_if_integration_was_enabled(setup) -> None:
    """Prouve qu'un modèle supprimé n'est plus visible publiquement, même s'il était intégré."""
    client, _service, _storage = setup
    generation_id = _create_done_model(client)
    enabled = client.patch(f"/models/{generation_id}/integration", json={"enabled": True}).json()
    public_id = enabled["public_id"]
    assert client.get(f"/public/models/{public_id}").status_code == 200

    assert client.delete(f"/models/{generation_id}").status_code == 204

    assert client.get(f"/public/models/{public_id}").status_code == 404


def test_delete_unknown_or_demo_model_returns_404(setup) -> None:
    """Prouve qu'un identifiant inconnu ou un exemple de démonstration donne 404."""
    client, _service, _storage = setup

    assert client.delete(f"/models/{uuid4()}").status_code == 404
    # Les exemples de démonstration ne sont pas dans l'historique : ils ne peuvent pas être supprimés.
    assert client.delete("/models/chair-bentwood").status_code == 404


def test_delete_refuses_a_generation_still_in_progress(setup) -> None:
    """Prouve qu'une génération en cours ne peut pas être supprimée (409)."""
    client, service, storage = setup
    upload = ValidatedUpload(filename="chair.png", content_type="image/png", size_bytes=len(PNG_BYTES))
    record = service.create_generation(upload, PNG_BYTES, "chair")  # reste PENDING : run() n'est pas appelé

    response = client.delete(f"/models/{record.id}")

    assert response.status_code == 409
    assert "en cours de création" in response.json()["detail"]
    assert service.get_generation(record.id) is not None
    assert (storage.images_dir / f"{record.id}.png").is_file()


def test_repository_delete_reports_whether_a_row_existed(tmp_path: Path) -> None:
    """Prouve que le dépôt indique si une ligne a réellement été supprimée."""
    repository = SQLiteGenerationRepository(tmp_path / "history.sqlite3")
    repository.initialize()

    assert repository.delete_generation(str(uuid4())) is False


def test_storage_delete_files_refuses_a_non_uuid_identifier(tmp_path: Path) -> None:
    """Prouve que la suppression de fichiers refuse un identifiant qui n'est pas un UUID."""
    storage = LocalStorage(tmp_path)
    outside = tmp_path / "secret.glb"
    outside.write_bytes(b"keep")

    with pytest.raises(ValueError):
        storage.delete_files("../secret")
    assert outside.is_file()


def test_storage_delete_files_ignores_missing_files(tmp_path: Path) -> None:
    """Prouve que la suppression ne plante pas si les fichiers sont déjà absents."""
    LocalStorage(tmp_path).delete_files(str(uuid4()))

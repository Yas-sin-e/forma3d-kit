# Rôle : vérifie le renommage d'un modèle du Studio (PATCH /models/{id}/name) et ses refus.
# Exécution : Pytest appelle FastAPI en mémoire avec la base PostgreSQL de test et un stockage temporaire, sans réseau.
"""Tests de PATCH /models/{id}/name, de GenerationService.rename_generation et du dépôt associé."""

import json
import struct
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from pg_support import make_repository
from app.routers.models import get_generation_service
from app.services.generation_service import GenerationService
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
    """Service réel sur la base PostgreSQL de test et un dossier de stockage temporaire."""
    repository = make_repository()
    repository.initialize()
    service = GenerationService(SuccessfulProvider(), LocalStorage(tmp_path / "storage"), repository)
    app.dependency_overrides[get_generation_service] = lambda: service
    yield TestClient(app), service
    app.dependency_overrides.pop(get_generation_service, None)


def _create_done_model(client: TestClient, filename: str = "chair.png") -> str:
    """Crée par l'API un modèle terminé (fournisseur simulé) et renvoie son identifiant."""
    response = client.post(
        "/models",
        files={"file": (filename, PNG_BYTES, "image/png")},
        data={"category": "chair"},
    )
    assert response.status_code == 202
    return response.json()["id"]


def _gallery_name(client: TestClient, generation_id: str) -> str:
    """Retourne le nom affiché par la galerie pour un identifiant donné."""
    items = client.get("/models/gallery").json()["items"]
    return next(item["name"] for item in items if item["id"] == generation_id)


def test_rename_changes_gallery_name_and_keeps_extension(setup) -> None:
    """Prouve que le nouveau nom apparaît dans la galerie et que l'extension d'origine reste."""
    client, _service = setup
    generation_id = _create_done_model(client, "chair.png")

    response = client.patch(f"/models/{generation_id}/name", json={"name": "Canapé blanc"})

    assert response.status_code == 200
    assert response.json()["filename"] == "Canapé blanc.png"
    assert _gallery_name(client, generation_id) == "Canapé blanc"
    # Le GLB reste téléchargeable : seul le nom affiché a changé.
    assert client.get(f"/models/{generation_id}/glb").status_code == 200


def test_rename_collapses_spaces(setup) -> None:
    """Prouve que les espaces superflus sont nettoyés avant l'enregistrement."""
    client, _service = setup
    generation_id = _create_done_model(client, "chair.png")

    response = client.patch(f"/models/{generation_id}/name", json={"name": "  Fauteuil   rétro  "})

    assert response.status_code == 200
    assert response.json()["filename"] == "Fauteuil rétro.png"


@pytest.mark.parametrize("bad_name", ["", "   ", "a/b", "a\\b", "x" * 81])
def test_rename_refuses_invalid_names(setup, bad_name: str) -> None:
    """Prouve qu'un nom vide, trop long ou contenant un séparateur de chemin est refusé en 422."""
    client, _service = setup
    generation_id = _create_done_model(client, "chair.png")

    response = client.patch(f"/models/{generation_id}/name", json={"name": bad_name})

    assert response.status_code == 422
    assert _gallery_name(client, generation_id) == "chair"


def test_rename_unknown_model_returns_404(setup) -> None:
    """Prouve qu'un identifiant inconnu (par exemple un exemple de démonstration) renvoie 404."""
    client, _service = setup

    response = client.patch(f"/models/{uuid4()}/name", json={"name": "Nouveau"})

    assert response.status_code == 404


def test_service_rename_returns_none_for_unknown_id(setup) -> None:
    """Prouve que le service renvoie None sans rien écrire pour un identifiant inconnu."""
    _client, service = setup

    assert service.rename_generation(str(uuid4()), "Nouveau") is None


def test_rename_persists_in_repository(setup) -> None:
    """Prouve que le nouveau nom est relu depuis PostgreSQL par un nouveau dépôt."""
    client, _service = setup
    generation_id = _create_done_model(client, "chair.png")
    client.patch(f"/models/{generation_id}/name", json={"name": "Chaise métal 01"})

    record = make_repository().get_generation(generation_id)

    assert record is not None
    assert record.filename == "Chaise métal 01.png"

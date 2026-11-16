# Rôle : vérifie les routes du cycle de génération avec un dépôt persistant temporaire.
# Exécution : Pytest appelle FastAPI en mémoire, sans appel à un fournisseur distant.
"""Tests HTTP locaux du cycle asynchrone et de sa galerie persistante."""

import json
import struct
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.models import ProductCategory
from app.providers.base import ProviderError
from pg_support import make_repository
from app.routers.models import get_demo_gallery, get_generation_service
from app.services.generation_service import GenerationService
from app.services.demo_gallery import DemoGallery
from app.storage.local_storage import LocalStorage


class UnavailableProvider:
    """Fournisseur de test qui échoue sans produire de données de modèle."""

    def generate(self, image_path: Path) -> bytes:
        """Faux fournisseur : remplace l'appel au service d'IA (aucun réseau, aucune vraie génération)."""
        raise ProviderError("Space public indisponible pour ce test.")


class SuccessfulProvider:
    """Fournisseur local simulé qui renvoie un conteneur GLB 2.0 minimal."""

    def generate(self, image_path: Path) -> bytes:
        """Faux fournisseur : remplace l'appel au service d'IA (aucun réseau, aucune vraie génération)."""
        document = json.dumps({"asset": {"version": "2.0"}}, separators=(",", ":")).encode()
        document += b" " * (-len(document) % 4)
        json_chunk = struct.pack("<I4s", len(document), b"JSON") + document
        return struct.pack("<4sII", b"glTF", 2, 12 + len(json_chunk)) + json_chunk


def test_upload_returns_job_and_status_records_provider_failure(tmp_path: Path) -> None:
    """Prouve que l'envoi répond 202 PENDING puis que l'état final enregistre l'échec du fournisseur."""
    repository = make_repository()
    repository.initialize()
    service = GenerationService(UnavailableProvider(), LocalStorage(tmp_path), repository)
    app.dependency_overrides[get_generation_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.post(
            "/models",
            files={"file": ("chair.png", b"\x89PNG\r\n\x1a\nsample", "image/png")},
            data={"category": "chair"},
        )
        assert response.status_code == 202
        assert response.json()["status"] == "PENDING"
        assert response.json()["category"] == "chair"
        assert response.json()["model_url"] is None

        generation_id = response.json()["id"]
        status_response = client.get(f"/models/{generation_id}")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "FAILED"
        assert status_response.json()["error_message"] == (
            "Space public indisponible pour ce test."
        )
        assert "n'a pas pu être préparée localement" in status_response.json()["image_warning"]

        download_response = client.get(f"/models/{generation_id}/glb")
        assert download_response.status_code == 409
        assert download_response.json()["detail"].startswith("Le modèle n'est pas encore")
    finally:
        app.dependency_overrides.pop(get_generation_service, None)


def test_upload_rejects_invalid_image_before_scheduling_generation(tmp_path: Path) -> None:
    """Prouve qu'une image invalide est refusée avant de lancer la moindre génération."""
    repository = make_repository()
    repository.initialize()
    service = GenerationService(UnavailableProvider(), LocalStorage(tmp_path), repository)
    app.dependency_overrides[get_generation_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.post(
            "/models",
            files={"file": ("chair.png", b"not-an-image", "image/png")},
            data={"category": "chair"},
        )

        assert response.status_code == 415
        assert response.json()["detail"] == (
            "Le contenu du fichier ne correspond pas à son format déclaré."
        )
    finally:
        app.dependency_overrides.pop(get_generation_service, None)


def test_upload_requires_a_supported_category() -> None:
    """Prouve qu'une catégorie inconnue est refusée (422)."""
    client = TestClient(app)
    file = {"file": ("chair.png", b"\x89PNG\r\n\x1a\nsample", "image/png")}
    try:
        missing = client.post("/models", files=file)
        invalid = client.post("/models", files=file, data={"category": "lamp"})
    finally:
        app.dependency_overrides.pop(get_generation_service, None)

    assert missing.status_code == 422
    assert invalid.status_code == 422


def test_completed_upload_appears_in_its_category_with_source_and_glb(tmp_path: Path) -> None:
    """Prouve qu'un modèle terminé apparaît dans sa catégorie avec sa photo source et son GLB."""
    repository = make_repository()
    repository.initialize()
    service = GenerationService(
        SuccessfulProvider(),
        LocalStorage(tmp_path / "storage"),
        repository,
    )
    app.dependency_overrides[get_generation_service] = lambda: service
    app.dependency_overrides[get_demo_gallery] = lambda: DemoGallery(tmp_path / "demos")
    client = TestClient(app)
    image_bytes = b"\x89PNG\r\n\x1a\nsample"
    try:
        upload = client.post(
            "/models",
            files={"file": ("stool-essai.png", image_bytes, "image/png")},
            data={"category": ProductCategory.STOOL.value},
        )
        generation_id = upload.json()["id"]
        status = client.get(upload.json()["status_url"])
        gallery = client.get("/models/gallery")
        source = client.get(f"/models/{generation_id}/source-image")
        model = client.get(f"/models/{generation_id}/glb")
    finally:
        app.dependency_overrides.pop(get_generation_service, None)
        app.dependency_overrides.pop(get_demo_gallery, None)

    assert upload.status_code == 202
    assert status.json()["status"] == "DONE"
    assert status.json()["category"] == "stool"
    generated = next(item for item in gallery.json()["items"] if item["id"] == generation_id)
    assert generated["category"] == "stool"
    assert generated["source_image_url"] == f"/models/{generation_id}/source-image"
    assert source.content == image_bytes
    assert model.status_code == 200
    assert model.content[:4] == b"glTF"


def test_status_route_returns_not_found_for_unknown_id(tmp_path: Path) -> None:
    """Prouve qu'un identifiant inconnu donne 404 sur la route de suivi."""
    repository = make_repository()
    repository.initialize()
    service = GenerationService(UnavailableProvider(), LocalStorage(tmp_path), repository)
    app.dependency_overrides[get_generation_service] = lambda: service
    try:
        response = TestClient(app).get("/models/not-a-generation")
    finally:
        app.dependency_overrides.pop(get_generation_service, None)

    assert response.status_code == 404

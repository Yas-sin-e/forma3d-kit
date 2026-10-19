# Rôle : vérifie l'acceptation, le suivi et le refus de téléchargement prématuré.
# Exécution : Pytest appelle l'application FastAPI en mémoire depuis le dossier backend.
"""Tests HTTP locaux du cycle asynchrone sans appel à un fournisseur distant."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.providers.base import ProviderError
from app.routers.models import get_generation_service
from app.services.generation_service import GenerationService
from app.storage.local_storage import LocalStorage


class UnavailableProvider:
    """Fournisseur de test qui échoue sans produire de données de modèle."""

    def generate(self, image_path: Path) -> bytes:
        raise ProviderError("Space public indisponible pour ce test.")


def test_upload_returns_job_and_status_records_provider_failure(tmp_path: Path) -> None:
    service = GenerationService(UnavailableProvider(), LocalStorage(tmp_path))
    app.dependency_overrides[get_generation_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.post(
            "/models",
            files={"file": ("chair.png", b"\x89PNG\r\n\x1a\nsample", "image/png")},
        )
        assert response.status_code == 202
        assert response.json()["status"] == "PENDING"
        assert response.json()["model_url"] is None

        generation_id = response.json()["id"]
        status_response = client.get(f"/models/{generation_id}")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "FAILED"
        assert status_response.json()["error_message"] == (
            "Space public indisponible pour ce test."
        )

        download_response = client.get(f"/models/{generation_id}/glb")
        assert download_response.status_code == 409
        assert download_response.json()["detail"].startswith("Le modèle n'est pas encore")
    finally:
        app.dependency_overrides.pop(get_generation_service, None)


def test_upload_rejects_invalid_image_before_scheduling_generation(tmp_path: Path) -> None:
    service = GenerationService(UnavailableProvider(), LocalStorage(tmp_path))
    app.dependency_overrides[get_generation_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.post(
            "/models",
            files={"file": ("chair.png", b"not-an-image", "image/png")},
        )

        assert response.status_code == 415
        assert response.json()["detail"] == (
            "Le contenu du fichier ne correspond pas à son format déclaré."
        )
    finally:
        app.dependency_overrides.pop(get_generation_service, None)


def test_status_route_returns_not_found_for_unknown_id() -> None:
    response = TestClient(app).get("/models/not-a-generation")

    assert response.status_code == 404

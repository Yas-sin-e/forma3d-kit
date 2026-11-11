# Rôle : teste le contrat HTTP externe v1 avec clé, quota, génération simulée et CORS fermé.
# Exécution : FastAPI TestClient utilise des services temporaires, sans fournisseur réel ni réseau externe.
"""Tests HTTP de l’API d’intégration versionnée du Sprint 5c."""

import json
import struct
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.sqlite_repository import SQLiteGenerationRepository
from app.routers.api_keys import get_api_key_service
from app.routers.categories import get_category_service
from app.routers.models import get_generation_service
from app.services.api_key_service import APIKeyService
from app.services.category_service import CategoryService
from app.services.generation_service import GenerationService
from app.storage.local_storage import LocalStorage


class StaticProvider:
    """Retourne une fixture GLB déterministe au lieu d’appeler un fournisseur distant."""

    def generate(self, image_path: Path) -> bytes:
        assert image_path.is_file()
        payload = json.dumps({"asset": {"version": "2.0"}}, separators=(",", ":")).encode()
        padding = (-len(payload)) % 4
        payload += b" " * padding
        total_length = 12 + 8 + len(payload)
        return b"glTF" + struct.pack("<II", 2, total_length) + struct.pack("<I4s", len(payload), b"JSON") + payload


def test_api_v1_creates_tracks_downloads_and_returns_embed_code(tmp_path: Path) -> None:
    repository = SQLiteGenerationRepository(tmp_path / "api.sqlite3")
    repository.initialize()
    key_service = APIKeyService(repository)
    _key, secret = key_service.create("Site de démonstration")
    service = GenerationService(StaticProvider(), LocalStorage(tmp_path / "storage"), repository)
    app.dependency_overrides[get_api_key_service] = lambda: key_service
    app.dependency_overrides[get_category_service] = lambda: CategoryService(repository)
    app.dependency_overrides[get_generation_service] = lambda: service
    previous_daily, previous_rate = app.state.api_daily_generation_limit, app.state.api_rate_limit_per_minute
    app.state.api_daily_generation_limit, app.state.api_rate_limit_per_minute = 1, 100
    try:
        with TestClient(app) as client:
            unauthenticated = client.get("/api/v1/models/not-a-model")
            assert unauthenticated.status_code == 401
            assert unauthenticated.json()["error"]["code"] == "unauthorized"
            headers = {"X-API-Key": secret}
            missing = client.get("/api/v1/models/not-a-model", headers=headers)
            assert missing.status_code == 404 and missing.json()["error"]["code"] == "not_found"

            disabled = client.post(
                "/api/v1/models", headers=headers,
                files={"file": ("chair.jpg", b"\xff\xd8\xffphoto", "image/jpeg")},
                data={"category": "unknown"},
            )
            assert disabled.status_code == 403 and disabled.json()["error"]["code"] == "forbidden"

            created = client.post(
                "/api/v1/models", headers=headers,
                files={"file": ("chair.jpg", b"\xff\xd8\xffphoto", "image/jpeg")},
                data={"category": "chair"},
            )
            assert created.status_code == 202
            model_id = created.json()["id"]
            assert created.json()["status_url"] == f"/api/v1/models/{model_id}"
            status_response = client.get(created.json()["status_url"], headers=headers)
            assert status_response.status_code == 200
            assert status_response.json()["status"] == "DONE"
            assert status_response.json()["model_url"] == f"/api/v1/models/{model_id}/glb"
            downloaded = client.get(status_response.json()["model_url"], headers=headers)
            assert downloaded.status_code == 200 and downloaded.content.startswith(b"glTF")

            unavailable_code = client.get(f"/api/v1/models/{model_id}/integration-code", headers=headers)
            assert unavailable_code.status_code == 403
            activated = client.patch(f"/models/{model_id}/integration", json={"enabled": True})
            assert activated.status_code == 200
            code = client.get(f"/api/v1/models/{model_id}/integration-code", headers=headers)
            assert code.status_code == 200
            assert f"/embed/{status_response.json()['public_id']}" in code.json()["iframe_html"]
            assert "<forma3d-viewer" in code.json()["widget_html"]
            assert "/static/widget.js" in code.json()["widget_html"]

            over_quota = client.post(
                "/api/v1/models", headers=headers,
                files={"file": ("chair.jpg", b"\xff\xd8\xffphoto", "image/jpeg")},
                data={"category": "chair"},
            )
            assert over_quota.status_code == 429
            assert over_quota.json()["error"]["code"] == "rate_limited"
            assert int(over_quota.headers["retry-after"]) > 0
    finally:
        app.state.api_daily_generation_limit, app.state.api_rate_limit_per_minute = previous_daily, previous_rate
        app.dependency_overrides.pop(get_api_key_service, None)
        app.dependency_overrides.pop(get_category_service, None)
        app.dependency_overrides.pop(get_generation_service, None)


def test_api_v1_rate_limit_has_consistent_json_and_retry_after(tmp_path: Path) -> None:
    repository = SQLiteGenerationRepository(tmp_path / "rate.sqlite3")
    repository.initialize()
    key_service = APIKeyService(repository)
    _key, secret = key_service.create("Débit")
    app.dependency_overrides[get_api_key_service] = lambda: key_service
    previous_rate = app.state.api_rate_limit_per_minute
    app.state.api_rate_limit_per_minute = 1
    try:
        with TestClient(app) as client:
            headers = {"X-API-Key": secret}
            assert client.get("/api/v1/models/unknown", headers=headers).status_code == 404
            limited = client.get("/api/v1/models/unknown", headers=headers)
            assert limited.status_code == 429
            assert limited.json() == {
                "error": {"code": "rate_limited", "message": "Limite de débit atteinte ; réessayez dans une minute."}
            }
            assert limited.headers["retry-after"] == "60"
    finally:
        app.state.api_rate_limit_per_minute = previous_rate
        app.dependency_overrides.pop(get_api_key_service, None)


def test_cors_does_not_reflect_an_unconfigured_external_origin() -> None:
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/models",
            headers={
                "Origin": "https://unconfigured-shop.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "x-api-key,content-type",
            },
        )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers

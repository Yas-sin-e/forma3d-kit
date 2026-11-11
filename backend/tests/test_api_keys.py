# Rôle : vérifie le stockage privé, la gestion HTTP et l’authentification des clés d’intégration.
# Exécution : Pytest utilise SQLite temporaire et TestClient local, sans réseau externe.
"""Tests de régression pour les clés API du Sprint 5b."""

import hashlib
import sqlite3
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.main import app
from app.models import APIKeyRecord
from app.repositories.sqlite_repository import SQLiteGenerationRepository
from app.routers.api_keys import get_api_key_service, require_api_key
from app.services.api_key_service import APIKeyService


def test_key_creation_persists_only_fingerprint_and_revocation_survives_restart(tmp_path: Path) -> None:
    database = tmp_path / "keys.sqlite3"
    repository = SQLiteGenerationRepository(database)
    repository.initialize()
    service = APIKeyService(repository)
    record, secret = service.create("  Boutique démo  ")

    assert record.name == "Boutique démo"
    assert secret.startswith("f3d_live_")
    assert record.prefix == secret[:17]
    assert record.fingerprint == hashlib.sha256(secret.encode()).hexdigest()
    assert service.authenticate(secret) == record
    assert service.authenticate(secret + "x") is None

    restarted = APIKeyService(SQLiteGenerationRepository(database))
    assert restarted.list() == [record]
    assert restarted.authenticate(secret) == record
    with sqlite3.connect(database) as connection:
        raw_rows = connection.execute("SELECT name, prefix, fingerprint, revoked FROM api_keys").fetchall()
    assert raw_rows == [("Boutique démo", record.prefix, record.fingerprint, 0)]
    assert secret not in repr(raw_rows)

    revoked = restarted.revoke(record.id)
    assert revoked is not None and revoked.revoked is True
    assert restarted.authenticate(secret) is None
    assert APIKeyService(SQLiteGenerationRepository(database)).list()[0].revoked is True
    assert restarted.revoke("missing") is None


def test_key_management_routes_reveal_secret_once_and_revoke(tmp_path: Path) -> None:
    repository = SQLiteGenerationRepository(tmp_path / "api.sqlite3")
    repository.initialize()
    service = APIKeyService(repository)
    app.dependency_overrides[get_api_key_service] = lambda: service
    try:
        with TestClient(app) as client:
            created = client.post("/api-keys", json={"name": "Intégration test"})
            assert created.status_code == 201
            secret = created.json()["key"]
            assert secret.startswith("f3d_live_")
            assert "fingerprint" not in created.text

            listed = client.get("/api-keys")
            assert listed.status_code == 200
            assert len(listed.json()["items"]) == 1
            assert secret not in listed.text
            assert "fingerprint" not in listed.text

            blank_name = client.post("/api-keys", json={"name": "   "})
            assert blank_name.status_code == 422
            key_id = created.json()["id"]
            revoked = client.delete(f"/api-keys/{key_id}")
            assert revoked.status_code == 200
            assert revoked.json()["revoked"] is True
            assert client.delete("/api-keys/missing").status_code == 404
    finally:
        app.dependency_overrides.pop(get_api_key_service, None)


def test_fastapi_key_dependency_accepts_only_active_key(tmp_path: Path) -> None:
    repository = SQLiteGenerationRepository(tmp_path / "auth.sqlite3")
    repository.initialize()
    service = APIKeyService(repository)
    record, secret = service.create("Test local")
    test_app = FastAPI()
    test_app.state.api_key_service = service

    @test_app.get("/protected")
    def protected_api(api_key: Annotated[APIKeyRecord, Depends(require_api_key)]) -> dict[str, str]:
        return {"name": api_key.name}

    with TestClient(test_app) as client:
        assert client.get("/protected").status_code == 401
        wrong = client.get("/protected", headers={"X-API-Key": secret + "wrong"})
        assert wrong.status_code == 401
        assert wrong.headers["www-authenticate"] == "ApiKey"
        accepted = client.get("/protected", headers={"X-API-Key": secret})
        assert accepted.status_code == 200 and accepted.json() == {"name": "Test local"}
        service.revoke(record.id)
        assert client.get("/protected", headers={"X-API-Key": secret}).status_code == 401

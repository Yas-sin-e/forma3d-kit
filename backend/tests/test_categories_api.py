# Rôle : vérifie les routes CRUD catégorie et le refus des uploads non autorisés.
# Exécution : TestClient utilise un dépôt SQLite temporaire et aucun fournisseur réel.
"""Tests HTTP de l'administration des catégories."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.repositories.sqlite_repository import SQLiteGenerationRepository
from app.routers.categories import get_category_service
from app.routers.models import get_generation_service
from app.services.category_service import CategoryService
from app.services.generation_service import GenerationService
from app.storage.local_storage import LocalStorage


class UnavailableProvider:
    """Fournisseur simulé, utilisé seulement si une requête est mise en tâche de fond."""

    def generate(self, image_path: Path) -> bytes:
        """Faux fournisseur : remplace l'appel au service d'IA (aucun réseau, aucune vraie génération)."""
        raise RuntimeError("Le fournisseur ne doit pas être appelé par ce test.")


def _client(tmp_path: Path) -> TestClient:
    """Prépare un client de test relié à une base SQLite temporaire."""
    repository = SQLiteGenerationRepository(tmp_path / "history.sqlite3")
    repository.initialize()
    service = GenerationService(
        UnavailableProvider(), LocalStorage(tmp_path / "storage"), repository
    )
    app.dependency_overrides[get_category_service] = lambda: CategoryService(repository)
    app.dependency_overrides[get_generation_service] = lambda: service
    return TestClient(app)


def test_category_routes_create_rename_toggle_and_delete(tmp_path: Path) -> None:
    """Prouve que les routes /categories créent, renomment, désactivent, réactivent et suppriment."""
    client = _client(tmp_path)
    try:
        listed = client.get("/categories")
        assert listed.status_code == 200
        assert [item["slug"] for item in listed.json()["items"]] == [
            "chair", "stool", "side-table"
        ]

        created = client.post("/categories", json={"slug": "lamp", "label": "Lampe"})
        assert created.status_code == 201
        assert created.json()["is_active"] is True

        renamed = client.patch(
            "/categories/lamp", json={"slug": "lighting", "label": "Éclairage"}
        )
        assert renamed.status_code == 200
        assert renamed.json()["slug"] == "lighting"

        disabled = client.patch("/categories/lighting", json={"is_active": False})
        assert disabled.status_code == 200
        assert disabled.json()["is_active"] is False
        assert all(item["slug"] != "lighting" for item in client.get("/categories").json()["items"])
        assert any(
            item["slug"] == "lighting"
            for item in client.get("/categories?include_inactive=true").json()["items"]
        )

        reenabled = client.patch("/categories/lighting", json={"is_active": True})
        assert reenabled.json()["is_active"] is True
        assert client.delete("/categories/lighting").status_code == 204
    finally:
        app.dependency_overrides.pop(get_category_service, None)
        app.dependency_overrides.pop(get_generation_service, None)


def test_category_routes_report_duplicates_blank_labels_and_used_delete(tmp_path: Path) -> None:
    """Prouve les refus : slug en double, libellé vide, suppression d'une catégorie utilisée (409)."""
    client = _client(tmp_path)
    try:
        duplicate = client.post("/categories", json={"slug": "chair", "label": "Autre"})
        blank = client.post("/categories", json={"slug": "empty", "label": "  "})
        invalid_slug = client.post("/categories", json={"slug": "Two words", "label": "X"})
        upload = client.post(
            "/models",
            files={"file": ("chair.png", b"\x89PNG\r\n\x1a\nfixture", "image/png")},
            data={"category": "chair"},
        )
        used_delete = client.delete("/categories/chair")
        unknown_upload = client.post(
            "/models",
            files={"file": ("new.png", b"\x89PNG\r\n\x1a\nfixture", "image/png")},
            data={"category": "unknown"},
        )
    finally:
        app.dependency_overrides.pop(get_category_service, None)
        app.dependency_overrides.pop(get_generation_service, None)

    assert duplicate.status_code == 409
    assert "slug" in duplicate.json()["detail"]
    assert blank.status_code == 422
    assert "libellé" in blank.json()["detail"]
    assert invalid_slug.status_code == 422
    assert "slug" in invalid_slug.json()["detail"]
    assert upload.status_code == 202
    assert used_delete.status_code == 409
    assert "utilisée" in used_delete.json()["detail"]
    assert unknown_upload.status_code == 422
    assert "inconnue ou désactivée" in unknown_upload.json()["detail"]


def test_inactive_category_rejects_generation_submission(tmp_path: Path) -> None:
    """Prouve qu'une catégorie désactivée ne peut plus recevoir de nouvelle photo."""
    client = _client(tmp_path)
    try:
        client.patch("/categories/stool", json={"is_active": False})
        response = client.post(
            "/models",
            files={"file": ("stool.png", b"\x89PNG\r\n\x1a\nfixture", "image/png")},
            data={"category": "stool"},
        )
    finally:
        app.dependency_overrides.pop(get_category_service, None)
        app.dependency_overrides.pop(get_generation_service, None)

    assert response.status_code == 422
    assert response.json()["detail"] == "Cette catégorie est inconnue ou désactivée."

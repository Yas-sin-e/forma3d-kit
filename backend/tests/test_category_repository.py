# Rôle : vérifie les règles SQL du CRUD catégorie et la conservation des références.
# Exécution : Pytest utilise la base PostgreSQL de test, sans service externe.
"""Tests du dépôt PostgreSQL des catégories partagées."""

from pathlib import Path

import pytest

from app.models import GenerationStatus, ProductCategory
from app.repositories.base import CategoryConflictError, CategoryInUseError
from pg_support import make_repository
from app.services.generation_service import GenerationService
from app.services.upload_validator import ValidatedUpload
from app.storage.local_storage import LocalStorage


def test_category_crud_and_active_listing(tmp_path: Path) -> None:
    """Prouve le CRUD des catégories dans PostgreSQL et la liste limitée aux catégories actives."""
    repository = make_repository()
    repository.initialize()

    created = repository.create_category("lamp", "Lampe")
    assert created.is_active is True
    assert {category.slug for category in repository.list_categories()} == {
        "chair", "stool", "side-table", "lamp"
    }

    renamed = repository.update_category("lamp", slug="lighting", label="Éclairage")
    assert (renamed.slug, renamed.label) == ("lighting", "Éclairage")
    inactive = repository.update_category("lighting", is_active=False)
    assert inactive.is_active is False
    assert "lighting" not in {category.slug for category in repository.list_categories()}
    assert repository.get_category("lighting") is None
    assert repository.get_category("lighting", include_inactive=True) == inactive

    reactivated = repository.update_category("lighting", is_active=True)
    assert reactivated.is_active is True
    repository.delete_category("lighting")
    assert repository.get_category("lighting", include_inactive=True) is None


def test_repository_rejects_duplicate_slug_and_deleting_used_category(tmp_path: Path) -> None:
    """Prouve que le dépôt refuse un slug en double et la suppression d'une catégorie utilisée."""
    repository = make_repository()
    repository.initialize()
    with pytest.raises(CategoryConflictError, match="slug.*existe déjà"):
        repository.create_category("chair", "Autre chaise")

    service = GenerationService(
        provider=type("UnusedProvider", (), {"generate": lambda self, path: b"x"})(),
        storage=LocalStorage(tmp_path / "storage"),
        repository=repository,
    )
    upload = ValidatedUpload("chair.jpg", "image/jpeg", 8)
    record = service.create_generation(upload, b"\xff\xd8\xfffixture", ProductCategory.CHAIR)

    persisted = repository.get_generation(record.id)
    assert persisted is not None and persisted.status is GenerationStatus.PENDING
    assert persisted.category == "chair"
    with pytest.raises(CategoryInUseError, match="utilisée par des générations"):
        repository.delete_category("chair")

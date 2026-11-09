# Rôle : couvre les validations métier des slugs et libellés de catégorie.
# Exécution : Pytest exerce CategoryService avec un SQLite temporaire.
"""Tests du service de gestion des catégories."""

from pathlib import Path

import pytest

from app.repositories.sqlite_repository import SQLiteGenerationRepository
from app.services.category_service import CategoryService, CategoryValidationError


def test_service_trims_values_and_rejects_empty_or_invalid_values(tmp_path: Path) -> None:
    repository = SQLiteGenerationRepository(tmp_path / "history.sqlite3")
    repository.initialize()
    service = CategoryService(repository)

    category = service.create(" custom-item ", "  Objet personnalisé  ")
    assert (category.slug, category.label) == ("custom-item", "Objet personnalisé")

    with pytest.raises(CategoryValidationError, match="libellé.*vide"):
        service.create("empty-label", "  ")
    with pytest.raises(CategoryValidationError, match="slug"):
        service.create("Bad Slug", "Invalide")


def test_service_renames_and_preserves_slug_for_optional_updates(tmp_path: Path) -> None:
    repository = SQLiteGenerationRepository(tmp_path / "history.sqlite3")
    repository.initialize()
    service = CategoryService(repository)

    updated = service.update("chair", label="  Sièges  ")

    assert updated.slug == "chair"
    assert updated.label == "Sièges"

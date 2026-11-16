# Rôle : couvre les validations métier des slugs et libellés de catégorie.
# Exécution : Pytest exerce CategoryService avec la base PostgreSQL de test.
"""Tests du service de gestion des catégories."""

from pathlib import Path

import pytest

from pg_support import make_repository
from app.services.category_service import CategoryService, CategoryValidationError


def test_service_trims_values_and_rejects_empty_or_invalid_values(tmp_path: Path) -> None:
    """Prouve que le service nettoie les espaces et refuse un libellé vide ou un slug invalide."""
    repository = make_repository()
    repository.initialize()
    service = CategoryService(repository)

    category = service.create(" custom-item ", "  Objet personnalisé  ")
    assert (category.slug, category.label) == ("custom-item", "Objet personnalisé")

    with pytest.raises(CategoryValidationError, match="libellé.*vide"):
        service.create("empty-label", "  ")
    with pytest.raises(CategoryValidationError, match="slug"):
        service.create("Bad Slug", "Invalide")


def test_service_renames_and_preserves_slug_for_optional_updates(tmp_path: Path) -> None:
    """Prouve qu'un renommage partiel garde le slug inchangé."""
    repository = make_repository()
    repository.initialize()
    service = CategoryService(repository)

    updated = service.update("chair", label="  Sièges  ")

    assert updated.slug == "chair"
    assert updated.label == "Sièges"

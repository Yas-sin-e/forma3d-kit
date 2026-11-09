# Rôle : applique les règles métier aux catégories partagées stockées dans SQLite.
# Exécution : les routes /categories et l'upload appellent ce service.
"""Service de gestion et de validation des catégories de produits."""

from __future__ import annotations

import re

from app.models import CategoryRecord
from app.repositories.base import (
    CategoryConflictError,
    CategoryInUseError,
    CategoryNotFoundError,
    GenerationRepository,
)

_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class CategoryValidationError(ValueError):
    """Libellé ou slug incompatible avec les règles de gestion."""


class CategoryService:
    """Expose le CRUD en validant les valeurs avant leur écriture."""

    def __init__(self, repository: GenerationRepository) -> None:
        self._repository = repository

    @staticmethod
    def validate_slug(slug: str) -> str:
        """Normalise et valide un slug ASCII en minuscules et tirets."""
        value = slug.strip().casefold()
        if len(value) > 64 or not _SLUG_PATTERN.fullmatch(value):
            raise CategoryValidationError(
                "Le slug doit contenir uniquement des lettres minuscules, chiffres et tirets, sans tiret initial ou final."
            )
        return value

    @staticmethod
    def validate_label(label: str) -> str:
        """Retire les espaces de bord et refuse un libellé vide."""
        value = label.strip()
        if not value:
            raise CategoryValidationError("Le libellé de catégorie ne peut pas être vide.")
        if len(value) > 100:
            raise CategoryValidationError("Le libellé ne peut pas dépasser 100 caractères.")
        return value

    def list_categories(self, include_inactive: bool = False) -> list[CategoryRecord]:
        """Liste les catégories actives, ou aussi les inactives pour la gestion."""
        return self._repository.list_categories(include_inactive=include_inactive)

    def require_active(self, slug: str) -> CategoryRecord:
        """Retourne la catégorie active ou lève une erreur claire pour un upload."""
        category = self._repository.get_category(slug)
        if category is None:
            raise CategoryNotFoundError("Cette catégorie est inconnue ou désactivée.")
        return category

    def create(self, slug: str, label: str) -> CategoryRecord:
        """Crée une catégorie après validation du slug et du libellé."""
        return self._repository.create_category(
            self.validate_slug(slug), self.validate_label(label)
        )

    def update(
        self,
        current_slug: str,
        *,
        slug: str | None = None,
        label: str | None = None,
        is_active: bool | None = None,
    ) -> CategoryRecord:
        """Renomme, réactive ou désactive une catégorie existante."""
        validated_slug = self.validate_slug(slug) if slug is not None else None
        validated_label = self.validate_label(label) if label is not None else None
        return self._repository.update_category(
            current_slug,
            slug=validated_slug,
            label=validated_label,
            is_active=is_active,
        )

    def delete(self, slug: str) -> None:
        """Supprime une catégorie inutilisée ; le dépôt refuse les références."""
        self._repository.delete_category(slug)


__all__ = [
    "CategoryConflictError",
    "CategoryInUseError",
    "CategoryNotFoundError",
    "CategoryService",
    "CategoryValidationError",
]

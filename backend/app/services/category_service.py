# Rôle : applique les règles métier aux catégories partagées stockées dans PostgreSQL.
# Exécution : les routes /categories et l'upload appellent ce service.
"""Service de gestion et de validation des catégories de produits."""

# Les annotations de type restent du texte.
from __future__ import annotations

# re (standard) : expressions régulières ; ici le motif autorisé pour un slug (minuscules, chiffres, tirets).
import re

# Objet métier d'une catégorie.
from app.models import CategoryRecord
# Erreurs métier et contrat du dépôt.
from app.repositories.base import (
    CategoryConflictError,
    CategoryInUseError,
    CategoryNotFoundError,
    GenerationRepository,
)

# Slug autorisé : mots en minuscules et chiffres séparés par un seul tiret.
_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


# Erreur : slug ou libellé invalide (la route répond 422 ou 400).
class CategoryValidationError(ValueError):
    """Libellé ou slug incompatible avec les règles de gestion."""


# Service des catégories : valide puis délègue au dépôt.
class CategoryService:
    """Expose le CRUD en validant les valeurs avant leur écriture."""

    # Constructeur : reçoit le dépôt.
    def __init__(self, repository: GenerationRepository) -> None:
        """Reçoit le dépôt des catégories (injection par constructeur)."""
        # Mémorise le dépôt.
        self._repository = repository

    # Méthode sans self.
    @staticmethod
    # Valide un slug.
    def validate_slug(slug: str) -> str:
        """Normalise et valide un slug ASCII en minuscules et tirets."""
        # Retire les espaces et passe en minuscules.
        value = slug.strip().casefold()
        # Plus de 64 caractères ou forme incorrecte...
        if len(value) > 64 or not _SLUG_PATTERN.fullmatch(value):
            # ...erreur.
            raise CategoryValidationError(
                "Le slug doit contenir uniquement des lettres minuscules, chiffres et tirets, sans tiret initial ou final."
            )
        # Renvoie le slug normalisé.
        return value

    # Méthode sans self.
    @staticmethod
    # Valide un libellé.
    def validate_label(label: str) -> str:
        """Retire les espaces de bord et refuse un libellé vide."""
        # Retire les espaces autour.
        value = label.strip()
        # Libellé vide...
        if not value:
            # ...erreur.
            raise CategoryValidationError("Le libellé de catégorie ne peut pas être vide.")
        # Plus de 100 caractères...
        if len(value) > 100:
            # ...erreur.
            raise CategoryValidationError("Le libellé ne peut pas dépasser 100 caractères.")
        # Renvoie le libellé nettoyé.
        return value

    # Liste les catégories.
    def list_categories(self, include_inactive: bool = False) -> list[CategoryRecord]:
        """Liste les catégories actives, ou aussi les inactives pour la gestion."""
        # Délègue au dépôt.
        return self._repository.list_categories(include_inactive=include_inactive)

    # Vérifie qu'une catégorie existe et est active (avant un envoi de photo).
    def require_active(self, slug: str) -> CategoryRecord:
        """Retourne la catégorie active ou lève une erreur claire pour un upload."""
        # Lit la catégorie active.
        category = self._repository.get_category(slug)
        # Inconnue ou désactivée...
        if category is None:
            # ...erreur 404.
            raise CategoryNotFoundError("Cette catégorie est inconnue ou désactivée.")
        # Renvoie la catégorie.
        return category

    # Crée une catégorie.
    def create(self, slug: str, label: str) -> CategoryRecord:
        """Crée une catégorie après validation du slug et du libellé."""
        # Valide le slug et le libellé, puis délègue au dépôt.
        return self._repository.create_category(
            self.validate_slug(slug), self.validate_label(label)
        )

    # Modifie une catégorie.
    def update(
        self,
        current_slug: str,
        *,
        slug: str | None = None,
        label: str | None = None,
        is_active: bool | None = None,
    ) -> CategoryRecord:
        """Renomme, réactive ou désactive une catégorie existante."""
        # Valide le nouveau slug, s'il est fourni.
        validated_slug = self.validate_slug(slug) if slug is not None else None
        # Valide le nouveau libellé, s'il est fourni.
        validated_label = self.validate_label(label) if label is not None else None
        # Délègue la mise à jour au dépôt...
        return self._repository.update_category(
            # ...slug actuel...
            current_slug,
            # ...nouveau slug ou None...
            slug=validated_slug,
            # ...nouveau libellé ou None...
            label=validated_label,
            # ...nouvel état ou None.
            is_active=is_active,
        )

    # Supprime une catégorie.
    def delete(self, slug: str) -> None:
        """Supprime une catégorie inutilisée ; le dépôt refuse les références."""
        # Délègue au dépôt, qui refuse si elle est utilisée.
        self._repository.delete_category(slug)


# Noms exportés par ce module (les routes importent les erreurs depuis ici).
__all__ = [
    "CategoryConflictError",
    "CategoryInUseError",
    "CategoryNotFoundError",
    "CategoryService",
    "CategoryValidationError",
]

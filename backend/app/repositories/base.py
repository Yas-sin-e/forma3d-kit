# Rôle : définit le contrat des catégories et générations sans imposer SQLite au métier.
# Exécution : les services dépendent de cette interface pour lire et modifier l'historique.
"""Interface de dépôt utilisée par le service de génération."""

from typing import Protocol

from app.models import APIKeyRecord, CategoryRecord, GenerationRecord


class CategoryConflictError(Exception):
    """Conflit d'unicité ou suppression interdite pour une catégorie."""


class CategoryNotFoundError(Exception):
    """Catégorie demandée introuvable."""


class CategoryInUseError(CategoryConflictError):
    """Une génération référence encore cette catégorie."""


class GenerationRepository(Protocol):
    """Contrat minimal pour les générations visibles dans l'application."""

    def initialize(self) -> None:
        """Crée le schéma et les catégories initiales, puis ferme les tâches périmées."""
        ...

    def save_generation(self, record: GenerationRecord) -> None:
        """Insère ou met à jour une génération et ses métadonnées."""
        ...

    def get_generation(self, generation_id: str) -> GenerationRecord | None:
        """Retourne une génération par son identifiant, ou None si elle est inconnue."""
        ...

    def get_generation_by_public_id(self, public_id: str) -> GenerationRecord | None:
        """Retourne une génération par UUID public, ou None si elle n'existe pas."""
        ...

    def set_embed_enabled(self, generation_id: str, enabled: bool) -> GenerationRecord | None:
        """Active ou désactive l'intégration d'un modèle terminé."""
        ...

    def list_completed_generations(self) -> list[GenerationRecord]:
        """Retourne les générations terminées, de la plus récente à la plus ancienne."""
        ...

    def get_category(self, slug: str, include_inactive: bool = False) -> CategoryRecord | None:
        """Retourne une catégorie par slug, éventuellement inactive."""
        ...

    def list_categories(self, include_inactive: bool = False) -> list[CategoryRecord]:
        """Liste les catégories actives ou l'ensemble demandé par l'administration."""
        ...

    def create_category(self, slug: str, label: str) -> CategoryRecord:
        """Crée une catégorie ; l'adaptateur signale un slug déjà utilisé."""
        ...

    def update_category(
        self,
        current_slug: str,
        *,
        slug: str | None = None,
        label: str | None = None,
        is_active: bool | None = None,
    ) -> CategoryRecord:
        """Modifie le slug, le libellé ou l'état sans détacher les générations."""
        ...

    def delete_category(self, slug: str) -> None:
        """Supprime une catégorie inutilisée et refuse si une génération la référence."""
        ...


    def create_api_key(self, record: APIKeyRecord) -> APIKeyRecord:
        """Enregistre les métadonnées et l'empreinte d'une clé, jamais sa valeur."""
        ...

    def list_api_keys(self) -> list[APIKeyRecord]:
        """Liste les métadonnées de toutes les clés, y compris révoquées."""
        ...

    def find_api_keys_by_prefix(self, prefix: str) -> list[APIKeyRecord]:
        """Trouve les empreintes candidates à comparer en temps constant."""
        ...

    def revoke_api_key(self, key_id: str) -> APIKeyRecord | None:
        """Révoque une clé existante et retourne ses métadonnées."""
        ...

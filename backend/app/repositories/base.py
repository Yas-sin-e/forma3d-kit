# Rôle : définit le contrat de persistance des générations sans imposer SQLite au métier.
# Exécution : GenerationService dépend de cette interface pour créer et relire l'historique.
"""Interface de dépôt utilisée par le service de génération."""

from typing import Protocol

from app.models import GenerationRecord


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

    def list_completed_generations(self) -> list[GenerationRecord]:
        """Retourne les générations terminées, de la plus récente à la plus ancienne."""
        ...

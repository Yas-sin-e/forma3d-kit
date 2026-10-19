# Rôle : orchestre l'acceptation, la génération et l'enregistrement des modèles.
# Exécution : les routes lancent run() comme tâche de fond après un upload validé.
"""Service de génération et registre des états conservé en mémoire."""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from uuid import uuid4

from app.models import GenerationRecord, GenerationStatus
from app.providers.base import Image3DProvider, ProviderError
from app.services.upload_validator import ValidatedUpload
from app.storage.base import Storage

logger = logging.getLogger(__name__)


class GenerationService:
    """Coordonne un fournisseur et un stockage sans base de données."""

    def __init__(self, provider: Image3DProvider, storage: Storage) -> None:
        self._provider = provider
        self._storage = storage
        self._records: dict[str, GenerationRecord] = {}
        self._lock = RLock()

    def create_generation(self, upload: ValidatedUpload, content: bytes) -> GenerationRecord:
        """Enregistre l'image, crée un identifiant et initialise PENDING."""
        generation_id = str(uuid4())
        extension = Path(upload.filename).suffix.lower()
        image_path = self._storage.save_image(generation_id, extension, content)
        now = datetime.now(UTC)
        record = GenerationRecord(
            id=generation_id,
            status=GenerationStatus.PENDING,
            filename=upload.filename,
            content_type=upload.content_type,
            image_path=image_path,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._records[generation_id] = record
        return record

    def get_generation(self, generation_id: str) -> GenerationRecord | None:
        """Retourne l'état courant d'une génération connue."""
        with self._lock:
            return self._records.get(generation_id)

    def get_model_path(self, generation_id: str) -> Path | None:
        """Retourne uniquement un modèle lié à une génération DONE."""
        record = self.get_generation(generation_id)
        if record is None or record.status is not GenerationStatus.DONE:
            return None
        return self._storage.get_model_path(generation_id)

    def run(self, generation_id: str) -> None:
        """Exécute le fournisseur et publie DONE ou FAILED de façon atomique."""
        with self._lock:
            record = self._records.get(generation_id)
            if record is None or record.status is not GenerationStatus.PENDING:
                return
            running_record = replace(
                record,
                status=GenerationStatus.RUNNING,
                updated_at=datetime.now(UTC),
            )
            self._records[generation_id] = running_record

        try:
            model_bytes = self._provider.generate(running_record.image_path)
            model_path = self._storage.save_model(generation_id, model_bytes)
        except ProviderError as error:
            failed_record = replace(
                running_record,
                status=GenerationStatus.FAILED,
                updated_at=datetime.now(UTC),
                error_message=str(error),
            )
            logger.warning("Generation %s failed in image provider", generation_id)
        except Exception as error:
            failed_record = replace(
                running_record,
                status=GenerationStatus.FAILED,
                updated_at=datetime.now(UTC),
                error_message="La génération a échoué à cause d'une erreur interne.",
            )
            logger.error(
                "Generation %s failed with %s",
                generation_id,
                type(error).__name__,
            )
        else:
            completed_record = replace(
                running_record,
                status=GenerationStatus.DONE,
                updated_at=datetime.now(UTC),
                model_path=model_path,
                error_message=None,
            )
            with self._lock:
                self._records[generation_id] = completed_record
            return

        with self._lock:
            self._records[generation_id] = failed_record

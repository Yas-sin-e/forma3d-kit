# Rôle : orchestre les états de génération via un dépôt persistant et le stockage de fichiers.
# Exécution : les routes lancent run() comme tâche de fond après un upload validé.
"""Service de génération indépendant du fournisseur et du dépôt de métadonnées."""

from __future__ import annotations

import logging
import re
import tempfile
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from time import monotonic
from uuid import uuid4

from app.models import GenerationRecord, GenerationStatus, ModelOrigin
from app.providers.base import Image3DProvider, ProviderError
from app.repositories.base import GenerationRepository
from app.services.upload_validator import ValidatedUpload
from app.services.image_preparer import ImagePreparer, ImagePreparationError
from app.storage.base import Storage
from app.services.demo_gallery import DemoGallery

logger = logging.getLogger(__name__)


class GenerationService:
    """Coordonne le fournisseur, les fichiers locaux et l'historique persistant."""

    def __init__(
        self,
        provider: Image3DProvider,
        storage: Storage,
        repository: GenerationRepository,
        image_preparer: ImagePreparer | None = None,
    ) -> None:
        self._provider = provider
        self._storage = storage
        self._repository = repository
        self._image_preparer = image_preparer or ImagePreparer()
        self._lock = RLock()

    def create_generation(
        self,
        upload: ValidatedUpload,
        content: bytes,
        category: str,
    ) -> GenerationRecord:
        """Enregistre l'image et sa catégorie, puis initialise PENDING."""
        category_slug = str(getattr(category, "value", category))
        if self._repository.get_category(category_slug) is None:
            raise ValueError("Cette catégorie est inconnue ou désactivée.")
        generation_id = str(uuid4())
        extension = Path(upload.filename).suffix.lower()
        image_path = self._storage.save_image(generation_id, extension, content)
        now = datetime.now(UTC)
        record = GenerationRecord(
            id=generation_id,
            status=GenerationStatus.PENDING,
            filename=upload.filename,
            content_type=upload.content_type,
            category=category_slug,
            image_path=image_path,
            created_at=now,
            updated_at=now,
            origin=ModelOrigin.GENERATED,
        )
        with self._lock:
            self._repository.save_generation(record)
        return record

    def get_generation(self, generation_id: str) -> GenerationRecord | None:
        """Retourne l'état courant d'une génération connue."""
        with self._lock:
            return self._repository.get_generation(generation_id)

    def get_generation_by_public_id(self, public_id: str) -> GenerationRecord | None:
        """Retourne un modèle via son identifiant public d'intégration."""
        with self._lock:
            return self._repository.get_generation_by_public_id(public_id)

    def set_integration_enabled(
        self,
        generation_id: str,
        enabled: bool,
    ) -> GenerationRecord | None:
        """Change l'autorisation publique d'un modèle DONE dont le GLB existe."""
        with self._lock:
            record = self._repository.get_generation(generation_id)
            if record is None:
                return None
            if record.status is not GenerationStatus.DONE or self.get_model_path(generation_id) is None:
                raise ValueError("Seuls les modèles terminés avec un GLB disponible peuvent être intégrés.")
            return self._repository.set_embed_enabled(generation_id, enabled)

    def get_model_path(self, generation_id: str) -> Path | None:
        """Retourne uniquement un modèle lié à une génération DONE."""
        record = self.get_generation(generation_id)
        if (
            record is None
            or record.status is not GenerationStatus.DONE
            or record.model_path is None
            or not record.model_path.is_file()
        ):
            return None
        model_path = self._storage.get_model_path(generation_id)
        return model_path if model_path == record.model_path and model_path.is_file() else None

    def get_source_image_path(self, generation_id: str) -> Path | None:
        """Retourne la photo source locale d'une génération réellement terminée."""
        record = self.get_generation(generation_id)
        if record is None or record.status is not GenerationStatus.DONE:
            return None
        return record.image_path if record.image_path is not None and record.image_path.is_file() else None

    def list_completed_generations(self) -> list[GenerationRecord]:
        """Liste les générations persistées terminées, de la plus récente à l'ancienne."""
        with self._lock:
            records = self._repository.list_completed_generations()
        return [
            record
            for record in records
            if record.model_path is not None
            and record.model_path.is_file()
            and (record.origin is not ModelOrigin.GENERATED or (
                record.image_path is not None and record.image_path.is_file()
            ))
        ]

    @staticmethod
    def _clean_model_title(title: str, filename: str) -> str:
        """Nettoie un titre importé sans conserver de chemin ou de caractère de contrôle."""
        candidate = title.strip()
        if not candidate:
            candidate = re.sub(r"[._-]+", " ", Path(filename.replace("\\", "/")).stem)
        else:
            candidate = Path(candidate).stem
        candidate = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", " ", candidate)
        candidate = " ".join(candidate.split())[:100].strip()
        if not candidate:
            raise ValueError("Le titre du modèle ne peut pas être vide.")
        return candidate

    def create_library_model(
        self,
        *,
        content: bytes,
        title: str,
        filename: str,
        category: str,
        origin: ModelOrigin,
        max_upload_bytes: int,
    ) -> GenerationRecord:
        """Valide et persiste un GLB importé ou copié dans la bibliothèque du vendeur."""
        if not content:
            raise ValueError("Le fichier GLB est vide.")
        if len(content) > max_upload_bytes:
            raise ValueError("Le fichier dépasse la taille maximale autorisée.")
        if not DemoGallery.is_valid_glb_2(content):
            raise ValueError("Le fichier n'est pas un modèle GLB 2.0 valide.")
        category_slug = str(getattr(category, "value", category)).strip()
        if self._repository.get_category(category_slug) is None:
            raise ValueError("Cette catégorie est inconnue ou désactivée.")
        if origin not in {ModelOrigin.IMPORTED, ModelOrigin.EXAMPLE}:
            raise ValueError("L'origine du modèle est invalide.")

        clean_title = self._clean_model_title(title, filename)
        model_id = str(uuid4())
        model_path = self._storage.save_model(model_id, content)
        now = datetime.now(UTC)
        record = GenerationRecord(
            id=model_id,
            status=GenerationStatus.DONE,
            filename=f"{clean_title}.glb",
            content_type="model/gltf-binary",
            category=category_slug,
            image_path=None,
            created_at=now,
            updated_at=now,
            model_path=model_path,
            origin=origin,
        )
        with self._lock:
            self._repository.save_generation(record)
            persisted = self._repository.get_generation(model_id)
        return persisted or record

    def run(self, generation_id: str) -> None:
        """Exécute le fournisseur et publie DONE ou FAILED de façon atomique."""
        started_at = monotonic()
        with self._lock:
            record = self._repository.get_generation(generation_id)
            if record is None or record.status is not GenerationStatus.PENDING:
                return
            running_record = replace(
                record,
                status=GenerationStatus.RUNNING,
                updated_at=datetime.now(UTC),
            )
            self._repository.save_generation(running_record)

        try:
            with tempfile.TemporaryDirectory(prefix="forma3d-photo-") as temporary_directory:
                prepared_path = Path(temporary_directory) / "prepared.png"
                provider_image_path = running_record.image_path
                try:
                    preparation = self._image_preparer.prepare(
                        running_record.image_path,
                        prepared_path,
                    )
                    provider_image_path = preparation.prepared_path
                    image_warning = preparation.warning
                except ImagePreparationError:
                    image_warning = (
                        "La photo n'a pas pu être préparée localement ; la photo originale sera envoyée. "
                        "Vérifiez qu'il s'agit d'une image JPG, PNG ou WebP lisible."
                    )
                running_record = replace(
                    running_record,
                    image_warning=image_warning,
                    updated_at=datetime.now(UTC),
                )
                with self._lock:
                    self._repository.save_generation(running_record)
                model_bytes = self._provider.generate(provider_image_path)
                model_path = self._storage.save_model(generation_id, model_bytes)
        except ProviderError as error:
            provider_settings = getattr(self._provider, "settings", None)
            protected_values = (
                getattr(provider_settings, "hf_token", None),
                getattr(provider_settings, "hf_space_id", None),
            )

            def redact(text: str) -> str:
                """Masque le jeton et l'adresse configurée avant toute exposition."""
                for protected_value in protected_values:
                    if isinstance(protected_value, str) and protected_value:
                        text = text.replace(protected_value, "[valeur masquée]")
                return text

            def safe_repr(value: object) -> str:
                """Masque le jeton et l'adresse temporaire dans les diagnostics locaux."""
                return redact(repr(value))

            failed_record = replace(
                running_record,
                status=GenerationStatus.FAILED,
                updated_at=datetime.now(UTC),
                error_message=redact(str(error)),
                duration_seconds=max(0.0, monotonic() - started_at),
            )

            cause = error.__cause__
            nested_cause = cause.__cause__ if cause is not None else None
            logger.warning(
                "Generation %s failed in image provider: error_type=%s error_repr=%s "
                "cause_type=%s cause_repr=%s nested_cause_repr=%s",
                generation_id,
                type(error).__name__,
                safe_repr(error),
                type(cause).__name__ if cause is not None else None,
                safe_repr(cause) if cause is not None else None,
                safe_repr(nested_cause) if nested_cause is not None else None,
            )
        except Exception as error:
            failed_record = replace(
                running_record,
                status=GenerationStatus.FAILED,
                updated_at=datetime.now(UTC),
                error_message="La génération a échoué à cause d'une erreur interne.",
                duration_seconds=max(0.0, monotonic() - started_at),
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
                duration_seconds=max(0.0, monotonic() - started_at),
            )
            with self._lock:
                self._repository.save_generation(completed_record)
            return

        with self._lock:
            self._repository.save_generation(failed_record)

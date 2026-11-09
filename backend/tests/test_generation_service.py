# Rôle : teste les états persistés et les erreurs sans faux résultat de génération.
# Exécution : Pytest lance ces tests avec un dépôt SQLite temporaire et sans réseau.
"""Tests du cycle de génération indépendant d'un Space Hugging Face."""

from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.models import GenerationStatus, ProductCategory
from app.providers.base import ProviderError
from app.repositories.sqlite_repository import SQLiteGenerationRepository
from app.services.generation_service import GenerationService
from app.services.upload_validator import ValidatedUpload
from app.storage.local_storage import LocalStorage


class UnavailableProvider:
    """Fournisseur de test qui signale l'échec observé sans fabriquer de résultat."""

    def generate(self, image_path: Path) -> bytes:
        raise ProviderError("Space indisponible dans ce test.")


def _validated_upload() -> ValidatedUpload:
    """Construit les métadonnées issues d'un fichier validé par le test."""
    return ValidatedUpload(
        filename="chair.jpg",
        content_type="image/jpeg",
        size_bytes=12,
    )


def test_create_generation_stores_image_and_starts_pending(tmp_path: Path) -> None:
    repository = SQLiteGenerationRepository(tmp_path / "history.sqlite3")
    repository.initialize()
    service = GenerationService(UnavailableProvider(), LocalStorage(tmp_path), repository)
    image_content = b"\xff\xd8\xffvalidated test photo"

    record = service.create_generation(_validated_upload(), image_content, ProductCategory.CHAIR)

    assert record.status is GenerationStatus.PENDING
    assert record.image_path.read_bytes() == image_content
    assert service.get_generation(record.id) == record


def test_run_records_provider_failure_without_creating_a_model(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    repository = SQLiteGenerationRepository(tmp_path / "history.sqlite3")
    repository.initialize()
    service = GenerationService(UnavailableProvider(), storage, repository)
    record = service.create_generation(_validated_upload(), b"\xff\xd8\xffphoto", ProductCategory.CHAIR)

    service.run(record.id)

    updated = service.get_generation(record.id)
    assert updated is not None
    assert updated.status is GenerationStatus.FAILED
    assert updated.error_message == "Space indisponible dans ce test."
    assert service.get_model_path(record.id) is None


def test_run_logs_provider_cause_while_masking_remote_credentials(
    tmp_path: Path,
    caplog,
) -> None:
    class DetailedUnavailableProvider:
        settings = SimpleNamespace(
            hf_token="test-token-never-log",
            hf_space_id="https://temporary-space.gradio.live",
        )

        def generate(self, image_path: Path) -> bytes:
            raise ProviderError(
                "Échec avec le jeton test-token-never-log"
            ) from TimeoutError(
                "écriture en échec pour https://temporary-space.gradio.live"
            )

    repository = SQLiteGenerationRepository(tmp_path / "history.sqlite3")
    repository.initialize()
    service = GenerationService(DetailedUnavailableProvider(), LocalStorage(tmp_path), repository)
    record = service.create_generation(_validated_upload(), b"\xff\xd8\xffphoto", ProductCategory.CHAIR)

    service.run(record.id)

    assert "error_type=ProviderError" in caplog.text
    assert "cause_type=TimeoutError" in caplog.text
    assert "test-token-never-log" not in caplog.text
    assert "temporary-space.gradio.live" not in caplog.text
    result = service.get_generation(record.id)
    assert result is not None
    assert result.error_message is not None
    assert "test-token-never-log" not in result.error_message
    assert "temporary-space.gradio.live" not in result.error_message


def test_run_ignores_unknown_generation_ids(tmp_path: Path) -> None:
    repository = SQLiteGenerationRepository(tmp_path / "history.sqlite3")
    repository.initialize()
    service = GenerationService(UnavailableProvider(), LocalStorage(tmp_path), repository)

    service.run(str(uuid4()))

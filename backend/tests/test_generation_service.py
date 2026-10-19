# Rôle : teste le registre et le passage d'une génération en échec sans faux modèle.
# Exécution : Pytest lance ces tests depuis le dossier backend.
"""Tests du cycle d'état qui n'ont pas besoin d'un Space Hugging Face."""

from pathlib import Path
from uuid import uuid4

from app.models import GenerationStatus
from app.providers.base import ProviderError
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
    service = GenerationService(UnavailableProvider(), LocalStorage(tmp_path))
    image_content = b"\xff\xd8\xffvalidated test photo"

    record = service.create_generation(_validated_upload(), image_content)

    assert record.status is GenerationStatus.PENDING
    assert record.image_path.read_bytes() == image_content
    assert service.get_generation(record.id) == record


def test_run_records_provider_failure_without_creating_a_model(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    service = GenerationService(UnavailableProvider(), storage)
    record = service.create_generation(_validated_upload(), b"\xff\xd8\xffphoto")

    service.run(record.id)

    updated = service.get_generation(record.id)
    assert updated is not None
    assert updated.status is GenerationStatus.FAILED
    assert updated.error_message == "Space indisponible dans ce test."
    assert service.get_model_path(record.id) is None


def test_run_ignores_unknown_generation_ids(tmp_path: Path) -> None:
    service = GenerationService(UnavailableProvider(), LocalStorage(tmp_path))

    service.run(str(uuid4()))

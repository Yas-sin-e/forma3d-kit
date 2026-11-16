# Rôle : vérifie que le dépôt PostgreSQL respecte le contrat GenerationRepository (cas limites, concurrence).
# Exécution : pytest, contre la base PostgreSQL de test (TEST_DATABASE_URL), remise à zéro par conftest.py.
"""Tests d'intégration du dépôt PostgreSQL : cycle de vie, catégories, clés API, quotas et concurrence."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from app.models import GenerationRecord, GenerationStatus, ModelOrigin
from app.repositories.base import CategoryConflictError, CategoryInUseError, CategoryNotFoundError
from app.services.api_key_service import APIKeyService
from pg_support import make_repository


@pytest.fixture()
def repository():
    """Dépôt PostgreSQL sur un schéma neuf (conftest.py vient de réinitialiser la base)."""
    return make_repository()


def _record(tmp_path: Path, generation_id: str = "gen-1", **changes: object) -> GenerationRecord:
    """Construit une génération de test (aucun fichier 3D réel)."""
    now = datetime(2026, 11, 16, 10, 0, tzinfo=UTC)
    base = GenerationRecord(
        id=generation_id,
        status=GenerationStatus.PENDING,
        filename="chaise.jpg",
        content_type="image/jpeg",
        category="chair",
        image_path=tmp_path / "chaise.jpg",
        created_at=now,
        updated_at=now,
    )
    return replace(base, **changes)


def test_initialize_seeds_categories_and_is_idempotent(repository) -> None:
    """Le schéma et les trois catégories initiales existent, même après plusieurs initialisations."""
    repository.initialize()
    repository.initialize()
    assert [c.slug for c in repository.list_categories()] == ["chair", "stool", "side-table"]


def test_generation_lifecycle_and_public_id(repository, tmp_path: Path) -> None:
    """Création PENDING, passage DONE avec UUID public, relecture, activation et suppression."""
    repository.save_generation(_record(tmp_path))
    pending = repository.get_generation("gen-1")
    assert pending is not None and pending.status is GenerationStatus.PENDING and pending.public_id is None

    done_at = datetime(2026, 11, 16, 10, 2, tzinfo=UTC)
    repository.save_generation(
        _record(tmp_path, status=GenerationStatus.DONE, model_path=tmp_path / "m.glb",
                duration_seconds=12.5, updated_at=done_at)
    )
    done = repository.get_generation("gen-1")
    assert done.status is GenerationStatus.DONE and done.duration_seconds == 12.5
    assert UUID(done.public_id).version == 4
    assert done.updated_at == done_at and done.origin is ModelOrigin.GENERATED

    # Un nouvel enregistrement ne change ni l'UUID public ni l'activation.
    enabled = repository.set_embed_enabled("gen-1", True)
    assert enabled.embed_enabled is True
    repository.save_generation(replace(done, error_message=None, public_id=None))
    again = repository.get_generation("gen-1")
    assert again.public_id == done.public_id and again.embed_enabled is True
    assert repository.get_generation_by_public_id(done.public_id).id == "gen-1"
    assert [g.id for g in repository.list_completed_generations()] == ["gen-1"]

    assert repository.delete_generation("gen-1") is True
    assert repository.delete_generation("gen-1") is False
    assert repository.get_generation("gen-1") is None


def test_embed_requires_done_generation(repository, tmp_path: Path) -> None:
    """Un modèle non terminé ne peut pas être activé pour l'intégration."""
    repository.save_generation(_record(tmp_path))
    assert repository.set_embed_enabled("gen-1", True) is None
    assert repository.set_embed_enabled("inconnu", True) is None


def test_restart_marks_interrupted_generations_failed(repository, tmp_path: Path) -> None:
    """Au redémarrage, une génération restée RUNNING devient FAILED avec un message clair."""
    repository.save_generation(_record(tmp_path, status=GenerationStatus.RUNNING))
    repository.initialize()
    record = repository.get_generation("gen-1")
    assert record.status is GenerationStatus.FAILED
    assert "interrompue" in record.error_message


def test_category_crud_rules(repository, tmp_path: Path) -> None:
    """Création, conflit de slug, renommage, désactivation et suppression protégée."""
    created = repository.create_category("bench", "Banc")
    assert created.is_active and created.slug == "bench"
    with pytest.raises(CategoryConflictError):
        repository.create_category("bench", "Autre banc")

    renamed = repository.update_category("bench", slug="long-bench", label="Banc long", is_active=False)
    assert (renamed.id, renamed.slug, renamed.is_active) == (created.id, "long-bench", False)
    assert repository.get_category("long-bench") is None
    assert repository.get_category("long-bench", include_inactive=True) is not None
    assert "long-bench" not in [c.slug for c in repository.list_categories()]
    with pytest.raises(CategoryConflictError):
        repository.update_category("long-bench", slug="chair")
    with pytest.raises(CategoryNotFoundError):
        repository.update_category("absent", label="x")

    repository.save_generation(_record(tmp_path, category="stool"))
    with pytest.raises(CategoryInUseError):
        repository.delete_category("stool")
    repository.delete_category("long-bench")
    with pytest.raises(CategoryNotFoundError):
        repository.delete_category("long-bench")


def test_api_keys_quota_rate_limit_and_deletion(repository) -> None:
    """Clés : empreinte seule, débit par minute, quota par jour UTC, révocation, suppression."""
    service = APIKeyService(repository)
    key, secret = service.create("Intégrateur")
    assert service.authenticate(secret).id == key.id
    assert all(secret not in (k.fingerprint, k.prefix) for k in repository.list_api_keys())

    start = datetime(2026, 11, 11, 12, 0, tzinfo=UTC)
    assert service.consume_rate_limit(key, 1, start) is None
    assert service.consume_rate_limit(key, 1, start + timedelta(seconds=10)) == "rate_limit"
    assert service.consume_rate_limit(key, 1, start + timedelta(seconds=61)) is None
    assert service.consume_daily_quota(key, 1, start) is None
    assert service.consume_daily_quota(key, 1, start + timedelta(minutes=1)) == "daily_quota"
    assert service.consume_daily_quota(key, 1, start + timedelta(days=1)) is None

    assert repository.delete_revoked_api_key(key.id) == "active"
    service.revoke(key.id)
    assert service.consume_rate_limit(key, 1, start + timedelta(days=2)) == "revoked"
    assert service.authenticate(secret) is None
    assert repository.delete_revoked_api_key(key.id) == "deleted"
    assert repository.delete_revoked_api_key(key.id) == "not_found"
    assert repository.list_api_keys() == []


def test_rate_limit_is_atomic_under_concurrency(repository) -> None:
    """Huit requêtes simultanées avec une limite de 3 : exactement 3 acceptées (verrou FOR UPDATE)."""
    service = APIKeyService(repository)
    key, _secret = service.create("Concurrence")
    now = datetime.now(UTC)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: repository.consume_api_rate_limit(key.id, 3, now), range(8)))
    assert results.count(None) == 3
    assert results.count("rate_limit") == 5


def test_paths_under_storage_root_are_stored_relative_and_portable(tmp_path: Path) -> None:
    """Sous storage_root, la base garde « models/x.glb » ; un autre dossier racine relit le même modèle."""
    from app.repositories.postgres_repository import PostgresGenerationRepository
    from pg_support import query, test_database_url

    windows_like_root = tmp_path / "poste" / "storage"
    container_like_root = tmp_path / "conteneur" / "storage"
    writer = PostgresGenerationRepository(test_database_url(), storage_root=windows_like_root)
    writer.save_generation(
        _record(
            tmp_path,
            image_path=windows_like_root / "images" / "gen-1.jpg",
            model_path=windows_like_root / "models" / "gen-1.glb",
            status=GenerationStatus.DONE,
        )
    )

    assert query("SELECT source_photo_path, glb_path FROM generations WHERE id = 'gen-1'") == [
        ("images/gen-1.jpg", "models/gen-1.glb")
    ]
    reader = PostgresGenerationRepository(test_database_url(), storage_root=container_like_root)
    record = reader.get_generation("gen-1")
    assert record.model_path == container_like_root.resolve() / "models" / "gen-1.glb"
    assert record.image_path == container_like_root.resolve() / "images" / "gen-1.jpg"


def test_paths_outside_storage_root_stay_absolute(tmp_path: Path, repository) -> None:
    """Un fichier hors du stockage (ou un dépôt sans storage_root) garde son chemin absolu."""
    repository.save_generation(_record(tmp_path, model_path=tmp_path / "ailleurs" / "m.glb"))
    record = repository.get_generation("gen-1")
    assert record.model_path == (tmp_path / "ailleurs" / "m.glb").resolve()
    assert record.image_path == (tmp_path / "chaise.jpg").resolve()

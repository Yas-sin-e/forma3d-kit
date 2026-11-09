# Rôle : vérifie le schéma SQLite, la reprise après redémarrage et l'historique terminé.
# Exécution : Pytest emploie un fichier SQLite temporaire et un fournisseur simulé local.
"""Tests du dépôt de générations sans réseau ni génération 3D réelle."""

from __future__ import annotations

import json
import sqlite3
import struct
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from app.models import GenerationStatus, ProductCategory
from app.repositories.sqlite_repository import SQLiteGenerationRepository
from app.services.generation_service import GenerationService
from app.services.upload_validator import ValidatedUpload
from app.storage.local_storage import LocalStorage


def _minimal_glb() -> bytes:
    """Construit uniquement un conteneur glTF minimal pour les tests locaux."""
    document = json.dumps({"asset": {"version": "2.0"}}, separators=(",", ":")).encode()
    document += b" " * (-len(document) % 4)
    json_chunk = struct.pack("<I4s", len(document), b"JSON") + document
    return struct.pack("<4sII", b"glTF", 2, 12 + len(json_chunk)) + json_chunk


class SuccessfulProvider:
    """Fournisseur de test local dont la sortie n'est pas un résultat du produit."""

    def generate(self, image_path: Path) -> bytes:
        assert image_path.is_file()
        return _minimal_glb()


def test_initialize_creates_categories_table_and_seeds_defaults(tmp_path: Path) -> None:
    database_path = tmp_path / "data" / "history.sqlite3"
    repository = SQLiteGenerationRepository(database_path)

    repository.initialize()

    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(categories)").fetchall()
        }
        categories = connection.execute(
            "SELECT slug, label, is_active FROM categories ORDER BY slug"
        ).fetchall()

    assert columns == {"id", "slug", "label", "is_active", "created_at"}
    assert categories == [
        ("chair", "Chaise", 1),
        ("side-table", "Table d’appoint", 1),
        ("stool", "Tabouret", 1),
    ]


def test_completed_generation_survives_repository_and_service_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "data" / "history.sqlite3"
    storage_root = tmp_path / "storage"
    first_repository = SQLiteGenerationRepository(database_path)
    first_repository.initialize()
    first_service = GenerationService(
        SuccessfulProvider(),
        LocalStorage(storage_root),
        first_repository,
    )
    upload = ValidatedUpload(filename="stool.png", content_type="image/png", size_bytes=12)
    record = first_service.create_generation(upload, b"\x89PNG\r\n\x1a\ntest", ProductCategory.STOOL)

    first_service.run(record.id)

    completed = first_service.get_generation(record.id)
    assert completed is not None
    assert completed.status is GenerationStatus.DONE
    assert completed.duration_seconds is not None
    assert completed.duration_seconds >= 0

    restarted_repository = SQLiteGenerationRepository(database_path)
    restarted_repository.initialize()
    restarted_service = GenerationService(
        SuccessfulProvider(),
        LocalStorage(storage_root),
        restarted_repository,
    )
    restored = restarted_service.get_generation(record.id)

    assert restored is not None
    assert restored.status is GenerationStatus.DONE
    assert restored.category == ProductCategory.STOOL
    assert restored.image_path.read_bytes() == b"\x89PNG\r\n\x1a\ntest"
    assert restored.model_path is not None and restored.model_path.is_file()
    assert restarted_service.get_model_path(record.id) == restored.model_path
    assert restarted_service.get_source_image_path(record.id) == restored.image_path
    assert [item.id for item in restarted_service.list_completed_generations()] == [record.id]


def test_initialize_fails_pending_and_running_generations_after_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "data" / "history.sqlite3"
    storage_root = tmp_path / "storage"
    repository = SQLiteGenerationRepository(database_path)
    repository.initialize()
    service = GenerationService(SuccessfulProvider(), LocalStorage(storage_root), repository)
    upload = ValidatedUpload(filename="chair.jpg", content_type="image/jpeg", size_bytes=12)

    pending = service.create_generation(upload, b"\xff\xd8\xfftest", ProductCategory.CHAIR)
    running = service.create_generation(upload, b"\xff\xd8\xfftest", ProductCategory.CHAIR)
    repository.save_generation(
        replace(
            running,
            status=GenerationStatus.RUNNING,
            updated_at=datetime.now(UTC),
        )
    )

    restarted_repository = SQLiteGenerationRepository(database_path)
    restarted_repository.initialize()

    for generation_id in (pending.id, running.id):
        restored = restarted_repository.get_generation(generation_id)
        assert restored is not None
        assert restored.status is GenerationStatus.FAILED
        assert restored.error_message == "Génération interrompue au redémarrage du serveur."
        assert restored.duration_seconds is None


def test_repository_opens_a_fresh_connection_for_each_operation(
    monkeypatch,
    tmp_path: Path,
) -> None:
    import app.repositories.sqlite_repository as sqlite_repository_module

    opened_connections: list[sqlite3.Connection] = []
    original_connect = sqlite_repository_module.sqlite3.connect

    def track_connect(*args, **kwargs) -> sqlite3.Connection:
        connection = original_connect(*args, **kwargs)
        opened_connections.append(connection)
        return connection

    monkeypatch.setattr(sqlite_repository_module.sqlite3, "connect", track_connect)
    repository = SQLiteGenerationRepository(tmp_path / "history.sqlite3")

    repository.initialize()
    repository.list_completed_generations()

    assert len(opened_connections) == 2
    assert opened_connections[0] is not opened_connections[1]

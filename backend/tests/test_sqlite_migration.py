# Rôle : vérifie l'outil de reprise tools/migrate_sqlite_to_postgres.py (SQLite -> PostgreSQL).
# Exécution : pytest ; une petite base SQLite de test est créée dans un dossier temporaire,
# puis copiée vers la base PostgreSQL de test.
"""Tests de la migration ponctuelle des anciennes données SQLite."""

from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path

import pytest

from pg_support import make_repository, query, test_database_url

_TOOL = Path(__file__).resolve().parents[2] / "tools" / "migrate_sqlite_to_postgres.py"
_spec = importlib.util.spec_from_file_location("migrate_sqlite_to_postgres", _TOOL)
migration = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migration)

_OLD_ROOT = r"C:\Users\demo\forma3d\backend\storage"


def _legacy_database(path: Path) -> Path:
    """Construit une base SQLite au format de l'ancienne application (valeurs fictives)."""
    with sqlite3.connect(path) as connection:
        connection.executescript(
            f"""
            CREATE TABLE categories (id INTEGER PRIMARY KEY, slug TEXT UNIQUE, label TEXT,
                is_active INTEGER, created_at TEXT);
            CREATE TABLE generations (id TEXT PRIMARY KEY, category_id INTEGER, status TEXT, filename TEXT,
                content_type TEXT, source_photo_path TEXT, glb_path TEXT, duration_seconds REAL,
                error_message TEXT, image_warning TEXT, origin TEXT, public_id TEXT, embed_enabled INTEGER,
                created_at TEXT, updated_at TEXT);
            CREATE TABLE api_keys (id TEXT PRIMARY KEY, name TEXT, prefix TEXT, fingerprint TEXT,
                created_at TEXT, revoked INTEGER);
            CREATE TABLE api_usage_daily (api_key_id TEXT, usage_date TEXT, generation_count INTEGER);
            CREATE TABLE api_rate_events (id INTEGER PRIMARY KEY, api_key_id TEXT, occurred_at TEXT);
            INSERT INTO categories VALUES (1, 'chair', 'Chaise', 1, '2026-10-01T10:00:00+00:00');
            INSERT INTO categories VALUES (106, 'canape', 'Canapé', 0, '2026-11-01T10:00:00+00:00');
            INSERT INTO generations VALUES ('gen-done', 106, 'DONE', 'canape.jpg', 'image/jpeg',
                '{_OLD_ROOT}\\images\\gen-done.jpg', '{_OLD_ROOT}\\models\\gen-done.glb', 42.5, NULL, NULL,
                'generated', '11111111-1111-4111-8111-111111111111', 1,
                '2026-11-02T10:00:00+00:00', '2026-11-02T10:01:00+00:00');
            INSERT INTO generations VALUES ('gen-failed', 1, 'FAILED', 'chaise.png', 'image/png',
                '{_OLD_ROOT}\\images\\gen-failed.png', NULL, NULL, 'Délai dépassé', NULL,
                'generated', NULL, 0, '2026-11-03T10:00:00+00:00', '2026-11-03T10:05:00+00:00');
            INSERT INTO api_keys VALUES ('key-1', 'Boutique', 'f3d_live_abc', 'empreinte-sha256',
                '2026-11-04T10:00:00+00:00', 0);
            INSERT INTO api_usage_daily VALUES ('key-1', '2026-11-04', 3);
            INSERT INTO api_rate_events VALUES (1, 'key-1', '2026-11-04T10:00:00+00:00');
            """
        )
    return path


def test_portable_path_makes_windows_storage_paths_relative() -> None:
    """Un chemin Windows sous l'ancien stockage devient relatif ; un autre chemin est conservé."""
    root = Path(_OLD_ROOT)
    assert migration.portable_path(_OLD_ROOT + r"\models\a.glb", root) == "models/a.glb"
    assert migration.portable_path(r"c:\users\DEMO\forma3d\backend\storage\images\b.png", root) == "images/b.png"
    assert migration.portable_path(r"D:\ailleurs\c.glb", root) == r"D:\ailleurs\c.glb"
    assert migration.portable_path("", root) == ""
    assert migration.portable_path(None, root) is None


def test_migration_copies_all_tables_and_is_repeatable(tmp_path: Path) -> None:
    """Tout est copié, les chemins deviennent portables, et une seconde exécution n'insère rien."""
    source = _legacy_database(tmp_path / "old.sqlite3")
    before = source.read_bytes()

    report = migration.migrate(source, test_database_url(), Path(_OLD_ROOT))

    # « chair » existe déjà (catégorie de départ) : seule « canape » est insérée.
    assert report == {
        "categories": (1, 1),
        "generations": (2, 0),
        "api_keys": (1, 0),
        "api_usage_daily": (1, 0),
    }
    assert query("SELECT source_photo_path, glb_path, embed_enabled FROM generations WHERE id = 'gen-done'") == [
        ("images/gen-done.jpg", "models/gen-done.glb", True)
    ]
    storage = tmp_path / "storage"
    done = make_repository().__class__(test_database_url(), storage_root=storage).get_generation("gen-done")
    assert done.category == "canape" and done.public_id == "11111111-1111-4111-8111-111111111111"
    assert done.model_path == storage.resolve() / "models" / "gen-done.glb"
    assert query("SELECT is_active FROM categories WHERE slug = 'canape'") == [(False,)]
    assert query("SELECT COUNT(*) FROM api_rate_events") == [(0,)]
    assert source.read_bytes() == before  # la source n'a pas été modifiée

    again = migration.migrate(source, test_database_url(), Path(_OLD_ROOT))
    assert all(inserted == 0 for inserted, _skipped in again.values())


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    """La simulation rapporte les chiffres mais annule la transaction."""
    source = _legacy_database(tmp_path / "old.sqlite3")
    report = migration.migrate(source, test_database_url(), Path(_OLD_ROOT), dry_run=True)
    assert report["generations"] == (2, 0)
    assert query("SELECT COUNT(*) FROM generations") == [(0,)]


def test_missing_source_and_cli_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Source absente : erreur claire et code 1 ; succès : code 0 et rapport lisible."""
    with pytest.raises(FileNotFoundError):
        migration.migrate(tmp_path / "absent.sqlite3", test_database_url(), Path(_OLD_ROOT))
    assert migration.main(["--sqlite", str(tmp_path / "absent.sqlite3"), "--database-url", test_database_url()]) == 1
    source = _legacy_database(tmp_path / "old.sqlite3")
    code = migration.main(
        ["--sqlite", str(source), "--database-url", test_database_url(), "--storage-root", _OLD_ROOT, "--dry-run"]
    )
    output = capsys.readouterr().out
    assert code == 0 and "SIMULATION" in output and "dev-password" not in output

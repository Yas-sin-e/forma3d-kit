# Rôle : vérifie le choix SQLite/PostgreSQL selon DATABASE_URL et le masquage du mot de passe.
# Exécution : pytest, sans base PostgreSQL ni réseau (aucune connexion n'est ouverte).
"""Tests de la fabrique de dépôt (repositories/factory.py)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.repositories.factory import DatabaseUrlError, create_repository, describe_backend, mask_database_url
from app.repositories.postgres_repository import PostgresGenerationRepository
from app.repositories.sqlite_repository import SQLiteGenerationRepository


def test_empty_database_url_keeps_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sans DATABASE_URL, le comportement historique (SQLite) est conservé."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    repository = create_repository(tmp_path / "local.sqlite3")
    assert isinstance(repository, SQLiteGenerationRepository)
    assert isinstance(create_repository(tmp_path / "x.sqlite3", "   "), SQLiteGenerationRepository)


def test_postgres_url_from_environment_selects_postgres(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """DATABASE_URL=postgresql://... choisit PostgreSQL sans ouvrir de connexion."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://forma3d:dev-password@db:5432/forma3d")
    repository = create_repository(tmp_path / "unused.sqlite3")
    assert isinstance(repository, PostgresGenerationRepository)
    assert not (tmp_path / "unused.sqlite3").exists()


def test_sqlalchemy_style_url_is_normalized(tmp_path: Path) -> None:
    """La forme postgresql+psycopg:// est acceptée et convertie pour psycopg."""
    repository = create_repository(tmp_path / "x.sqlite3", "postgresql+psycopg://u:p@db:5432/forma3d")
    assert isinstance(repository, PostgresGenerationRepository)
    assert repository._database_url == "postgresql://u:p@db:5432/forma3d"


@pytest.mark.parametrize("url", ["mysql://u:p@db/x", "sqlite:///tmp/x.db", "db:5432/forma3d"])
def test_unsupported_database_url_is_rejected_with_clear_message(url: str) -> None:
    """Une URL d'un autre moteur échoue tôt, avec un message lisible, au lieu d'une erreur obscure."""
    with pytest.raises(DatabaseUrlError, match="postgresql://"):
        describe_backend(url)


def test_describe_backend_names_engine() -> None:
    """Le type de base est journalisable sans exposer l'URL."""
    assert describe_backend(None) == "sqlite"
    assert describe_backend("") == "sqlite"
    assert describe_backend("postgres://u:p@db/x") == "postgresql"


def test_mask_database_url_hides_password() -> None:
    """Le mot de passe n'apparaît jamais dans la version journalisable de l'URL."""
    masked = mask_database_url("postgresql://forma3d:dev-password@db:5432/forma3d")
    assert masked == "postgresql://forma3d:***@db:5432/forma3d"
    assert "dev-password" not in masked
    assert mask_database_url("postgresql://db/forma3d") == "postgresql://db/forma3d"

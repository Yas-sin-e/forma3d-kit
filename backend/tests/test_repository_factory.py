# Rôle : vérifie la création du dépôt PostgreSQL depuis DATABASE_URL et le masquage du mot de passe.
# Exécution : pytest ; aucune connexion n'est ouverte par ces tests (la fabrique ne se connecte pas).
"""Tests de la fabrique de dépôt (repositories/factory.py)."""

from __future__ import annotations

import pytest

from app.repositories.factory import DatabaseUrlError, create_repository, mask_database_url, normalize_database_url
from app.repositories.postgres_repository import PostgresGenerationRepository


def test_database_url_from_environment_creates_postgres_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    """DATABASE_URL=postgresql://... donne un dépôt PostgreSQL, sans ouvrir de connexion."""
    monkeypatch.setenv("DATABASE_URL", "postgresql://forma3d:dev-password@db:5432/forma3d")
    repository = create_repository()
    assert isinstance(repository, PostgresGenerationRepository)
    assert repository._database_url == "postgresql://forma3d:dev-password@db:5432/forma3d"


@pytest.mark.parametrize("missing", [None, "", "   "])
def test_missing_database_url_fails_with_clear_message(monkeypatch: pytest.MonkeyPatch, missing) -> None:
    """Sans DATABASE_URL, l'application refuse de démarrer et explique quoi faire."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(DatabaseUrlError, match="PostgreSQL est obligatoire"):
        create_repository(missing) if missing is not None else create_repository()


def test_sqlalchemy_style_url_is_normalized() -> None:
    """La forme postgresql+psycopg:// est acceptée et convertie pour psycopg."""
    assert normalize_database_url("postgresql+psycopg://u:p@db:5432/forma3d") == "postgresql://u:p@db:5432/forma3d"
    assert normalize_database_url("postgres://u:p@db/x") == "postgresql://u:p@db/x"


@pytest.mark.parametrize("url", ["mysql://u:p@db/x", "sqlite:///tmp/x.db", "db:5432/forma3d"])
def test_other_engines_are_rejected(url: str) -> None:
    """Une URL d'un autre moteur (dont SQLite, retiré du projet) échoue tôt avec un message lisible."""
    with pytest.raises(DatabaseUrlError, match="postgresql://"):
        normalize_database_url(url)


def test_mask_database_url_hides_password() -> None:
    """Le mot de passe n'apparaît jamais dans la version journalisable de l'URL."""
    masked = mask_database_url("postgresql://forma3d:dev-password@db:5432/forma3d")
    assert masked == "postgresql://forma3d:***@db:5432/forma3d"
    assert "dev-password" not in masked
    assert mask_database_url("postgresql://db/forma3d") == "postgresql://db/forma3d"

# Rôle : choisit le dépôt de persistance (SQLite ou PostgreSQL) selon la variable DATABASE_URL.
# Exécution : appelé une fois par backend/app/main.py au chargement de l'application.
"""Fabrique de dépôt : un seul endroit décide où les données sont stockées.

- DATABASE_URL vide ou absente  -> SQLite (fichier local, comportement historique de dev.ps1 et des tests) ;
- DATABASE_URL=postgresql://... -> PostgreSQL (service « db » de Docker Compose).
C'est le principe « configuration par l'environnement » (méthode 12-factor) : la même image Docker
fonctionne partout, seule la variable change.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from app.repositories.base import GenerationRepository

_POSTGRES_SCHEMES = ("postgresql", "postgres")


class DatabaseUrlError(ValueError):
    """DATABASE_URL est renseignée mais n'est pas une URL PostgreSQL utilisable."""


def mask_database_url(database_url: str) -> str:
    """Retourne l'URL avec le mot de passe remplacé par *** pour pouvoir la journaliser sans fuite."""
    parts = urlsplit(database_url)
    if parts.password is None:
        return database_url
    host = parts.hostname or ""
    if parts.port is not None:
        host = f"{host}:{parts.port}"
    netloc = f"{parts.username}:***@{host}" if parts.username else f"***@{host}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def describe_backend(database_url: str | None) -> str:
    """Indique « sqlite » ou « postgresql » pour une URL donnée, sans se connecter."""
    url = (database_url or "").strip()
    if not url:
        return "sqlite"
    scheme = urlsplit(url).scheme.split("+", 1)[0].casefold()
    if scheme not in _POSTGRES_SCHEMES:
        raise DatabaseUrlError(
            "DATABASE_URL doit commencer par postgresql:// (ou rester vide pour SQLite) ; "
            f"schéma reçu : « {scheme or 'aucun'} »."
        )
    return "postgresql"


def create_repository(sqlite_path: Path, database_url: str | None = None) -> GenerationRepository:
    """Crée le dépôt adapté ; sans argument, lit DATABASE_URL dans l'environnement.

    psycopg n'est importé que si PostgreSQL est demandé : le mode SQLite n'en dépend pas.
    """
    url = (os.getenv("DATABASE_URL", "") if database_url is None else database_url).strip()
    if describe_backend(url) == "sqlite":
        from app.repositories.sqlite_repository import SQLiteGenerationRepository

        return SQLiteGenerationRepository(sqlite_path)
    from app.repositories.postgres_repository import PostgresGenerationRepository

    # psycopg n'accepte pas la forme « postgresql+psycopg:// » utilisée par SQLAlchemy : on la normalise.
    parts = urlsplit(url)
    normalized = urlunsplit(("postgresql", parts.netloc, parts.path, parts.query, parts.fragment))
    return PostgresGenerationRepository(normalized)

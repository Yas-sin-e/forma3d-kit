# Rôle : crée le dépôt PostgreSQL à partir de la variable d'environnement DATABASE_URL.
# Exécution : appelé une fois par backend/app/main.py au chargement de l'application.
"""Fabrique de dépôt : un seul endroit lit et valide l'adresse de la base de données.

PostgreSQL est la seule base du projet. DATABASE_URL est obligatoire :
- Docker Compose : postgresql://forma3d:...@db:5432/forma3d (hôte = nom du service « db ») ;
- scripts/dev.ps1 : postgresql://forma3d:...@127.0.0.1:5433/forma3d (base de Compose ouverte en debug) ;
- tests : la valeur de TEST_DATABASE_URL (voir backend/tests/conftest.py).
C'est le principe « configuration par l'environnement » (méthode 12-factor) : la même image Docker
fonctionne partout, seule la variable change.
"""

from __future__ import annotations

import os
from urllib.parse import urlsplit, urlunsplit

from app.repositories.base import GenerationRepository

_POSTGRES_SCHEMES = ("postgresql", "postgres")


class DatabaseUrlError(ValueError):
    """DATABASE_URL est absente ou n'est pas une URL PostgreSQL utilisable."""


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


def normalize_database_url(database_url: str | None) -> str:
    """Valide l'URL et la convertit à la forme attendue par psycopg (postgresql://…).

    Lève DatabaseUrlError avec un message clair si l'URL est vide ou d'un autre moteur.
    """
    url = (database_url or "").strip()
    if not url:
        raise DatabaseUrlError(
            "DATABASE_URL est vide : PostgreSQL est obligatoire. "
            "Exemple fictif : postgresql://forma3d:dev-password@db:5432/forma3d (voir .env.example)."
        )
    parts = urlsplit(url)
    scheme = parts.scheme.split("+", 1)[0].casefold()
    if scheme not in _POSTGRES_SCHEMES:
        raise DatabaseUrlError(
            f"DATABASE_URL doit commencer par postgresql:// ; schéma reçu : « {scheme or 'aucun'} »."
        )
    # psycopg n'accepte pas la forme « postgresql+psycopg:// » utilisée par SQLAlchemy : on la normalise.
    return urlunsplit(("postgresql", parts.netloc, parts.path, parts.query, parts.fragment))


def create_repository(database_url: str | None = None) -> GenerationRepository:
    """Crée le dépôt PostgreSQL ; sans argument, lit DATABASE_URL dans l'environnement.

    Aucune connexion n'est ouverte ici : la première a lieu dans initialize().
    """
    from app.repositories.postgres_repository import PostgresGenerationRepository

    url = os.getenv("DATABASE_URL") if database_url is None else database_url
    return PostgresGenerationRepository(normalize_database_url(url))

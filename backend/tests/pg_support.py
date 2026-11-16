# Rôle : outils partagés des tests pour la base PostgreSQL de test (connexion, remise à zéro, requêtes).
# Exécution : importé par conftest.py et par les modules de tests ; jamais exécuté seul.
"""Accès à la base PostgreSQL de TEST, désignée par la variable TEST_DATABASE_URL.

Sécurité : chaque test supprime puis recrée les tables. Le nom de la base doit donc contenir
« test » (ex. forma3d_test), sinon les tests refusent de démarrer.
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlsplit

# psycopg : pilote PostgreSQL, utilisé ici pour inspecter la base comme le ferait DBeaver.
import psycopg

from app.repositories.postgres_repository import PostgresGenerationRepository

TABLES = ("api_rate_events", "api_usage_daily", "api_keys", "generations", "categories")


def test_database_url() -> str:
    """Retourne TEST_DATABASE_URL après avoir vérifié qu'elle désigne bien une base de test."""
    url = os.getenv("TEST_DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "TEST_DATABASE_URL est vide : les tests exigent une base PostgreSQL de test. Exemple local : "
            "postgresql://forma3d:dev-password@127.0.0.1:5433/forma3d_test (scripts/dev.ps1 la prépare)."
        )
    database_name = urlsplit(url).path.lstrip("/")
    if "test" not in database_name:
        raise RuntimeError(
            f"Refus : la base « {database_name} » ne contient pas « test » ; ses tables seraient supprimées."
        )
    return url


# Le nom commence par « test_ » mais pytest ne le collecte pas : ce fichier ne s'appelle pas test_*.py.
test_database_url.__test__ = False  # type: ignore[attr-defined]


def make_repository() -> PostgresGenerationRepository:
    """Crée un dépôt sur la base de test, SANS la vider (sert aussi à simuler un redémarrage)."""
    return PostgresGenerationRepository(test_database_url())


def drop_all_tables() -> None:
    """Supprime toutes les tables de l'application dans la base de test (schéma vierge)."""
    with psycopg.connect(test_database_url()) as connection:
        connection.execute(f"DROP TABLE IF EXISTS {', '.join(TABLES)} CASCADE")


def reset_database() -> None:
    """Vide toutes les tables puis réinitialise (trois catégories de départ, compteurs remis à 1).

    TRUNCATE ... RESTART IDENTITY est beaucoup plus rapide que supprimer et recréer les tables.
    Si une table manque (un test de migration a recréé un ancien schéma), on repart d'un schéma vierge.
    """
    try:
        with psycopg.connect(test_database_url()) as connection:
            connection.execute(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE")
    except psycopg.errors.UndefinedTable:
        drop_all_tables()
    make_repository().initialize()


def query(sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    """Exécute une requête de lecture sur la base de test et renvoie toutes les lignes."""
    with psycopg.connect(test_database_url()) as connection:
        return connection.execute(sql, params).fetchall()


def execute(sql: str, params: tuple[Any, ...] = ()) -> None:
    """Exécute une instruction d'écriture (création de schéma ancien, insertion) sur la base de test."""
    with psycopg.connect(test_database_url()) as connection:
        connection.execute(sql, params)


def table_columns(table: str) -> set[str]:
    """Liste les colonnes d'une table, lues dans information_schema (catalogue standard SQL)."""
    return {
        row[0]
        for row in query(
            "SELECT column_name FROM information_schema.columns WHERE table_name = %s", (table,)
        )
    }

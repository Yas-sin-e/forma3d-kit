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

# Les annotations de type restent du texte : pas d'évaluation au chargement du module.
from __future__ import annotations

# os : lecture de la variable d'environnement DATABASE_URL.
import os
# Path : type du dossier de stockage.
from pathlib import Path
# Outils standard pour découper et recomposer une URL sans erreur.
from urllib.parse import urlsplit, urlunsplit

# Contrat du dépôt, utilisé comme type de retour.
from app.repositories.base import GenerationRepository

# Préfixes d'URL acceptés pour PostgreSQL.
_POSTGRES_SCHEMES = ("postgresql", "postgres")


# Erreur levée quand DATABASE_URL est absente ou d'un autre moteur.
class DatabaseUrlError(ValueError):
    """DATABASE_URL est absente ou n'est pas une URL PostgreSQL utilisable."""


# Fonction qui cache le mot de passe d'une URL de base de données.
def mask_database_url(database_url: str) -> str:
    """Retourne l'URL avec le mot de passe remplacé par *** pour pouvoir la journaliser sans fuite."""
    # Découpe l'URL en morceaux (schéma, utilisateur, mot de passe, hôte, port, chemin).
    parts = urlsplit(database_url)
    # Pas de mot de passe dans l'URL...
    if parts.password is None:
        # ...rien à masquer : on la renvoie telle quelle.
        return database_url
    # Nom d'hôte (ex. « db » ou « 127.0.0.1 »).
    host = parts.hostname or ""
    # Si un port est indiqué...
    if parts.port is not None:
        # ...on l'ajoute après l'hôte.
        host = f"{host}:{parts.port}"
    # Recompose « utilisateur:***@hôte » (ou « ***@hôte » sans utilisateur).
    netloc = f"{parts.username}:***@{host}" if parts.username else f"***@{host}"
    # Recompose l'URL complète avec le mot de passe remplacé.
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


# Fonction qui vérifie et normalise l'URL de la base.
def normalize_database_url(database_url: str | None) -> str:
    """Valide l'URL et la convertit à la forme attendue par psycopg (postgresql://…).

    Lève DatabaseUrlError avec un message clair si l'URL est vide ou d'un autre moteur.
    """
    # Remplace None par une chaîne vide et retire les espaces autour.
    url = (database_url or "").strip()
    # URL vide...
    if not url:
        # ...erreur claire avec un exemple fictif.
        raise DatabaseUrlError(
            "DATABASE_URL est vide : PostgreSQL est obligatoire. "
            "Exemple fictif : postgresql://forma3d:dev-password@db:5432/forma3d (voir .env.example)."
        )
    # Découpe l'URL.
    parts = urlsplit(url)
    # Garde la partie avant « + » (ex. « postgresql+psycopg » -> « postgresql ») en minuscules.
    scheme = parts.scheme.split("+", 1)[0].casefold()
    # Si ce n'est pas PostgreSQL...
    if scheme not in _POSTGRES_SCHEMES:
        # ...erreur claire qui montre le schéma reçu.
        raise DatabaseUrlError(
            f"DATABASE_URL doit commencer par postgresql:// ; schéma reçu : « {scheme or 'aucun'} »."
        )
    # psycopg n'accepte pas la forme « postgresql+psycopg:// » utilisée par SQLAlchemy : on la normalise.
    # Recompose l'URL avec le schéma « postgresql » attendu par psycopg.
    return urlunsplit(("postgresql", parts.netloc, parts.path, parts.query, parts.fragment))


# Fonction appelée par main.py pour obtenir le dépôt.
def create_repository(database_url: str | None = None, *, storage_root: Path | None = None) -> GenerationRepository:
    """Crée le dépôt PostgreSQL ; sans URL, lit DATABASE_URL dans l'environnement.

    storage_root : dossier des photos et GLB, pour enregistrer des chemins relatifs portables.
    Aucune connexion n'est ouverte ici : la première a lieu dans initialize().
    """
    # Import placé ici : psycopg n'est chargé que si l'on crée réellement le dépôt.
    from app.repositories.postgres_repository import PostgresGenerationRepository

    # URL fournie par l'appelant (tests) ou, à défaut, lue dans l'environnement.
    url = os.getenv("DATABASE_URL") if database_url is None else database_url
    # Crée le dépôt avec l'URL validée et le dossier de stockage.
    return PostgresGenerationRepository(normalize_database_url(url), storage_root=storage_root)

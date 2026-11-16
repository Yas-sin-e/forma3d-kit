# Rôle : configuration pytest partagée ; base PostgreSQL de test et session propriétaire du Studio.
# Exécution : chargé automatiquement par pytest avant chaque module de tests.
"""Prépare la base PostgreSQL de test et surcharge require_owner sauf pour les tests « real_auth »."""

import os

# pytest : outil de tests automatiques du projet (équivalent de JUnit).
# conftest.py est lu automatiquement : ses « fixtures » (préparations) servent à tous les tests.
import pytest

import pg_support

# L'application lit DATABASE_URL dès son import : on la fait pointer vers la base de TEST AVANT
# d'importer app.main. Sans TEST_DATABASE_URL valide, pytest s'arrête avec un message clair.
try:
    os.environ["DATABASE_URL"] = pg_support.test_database_url()
except RuntimeError as error:
    pytest.exit(str(error), returncode=4)

from app.main import app  # noqa: E402  (import volontairement placé après la configuration)
from app.routers.auth import require_owner


def pytest_configure(config: pytest.Config) -> None:
    """Déclare le marqueur « real_auth » (tests qui gardent la vraie vérification de session)."""
    config.addinivalue_line("markers", "real_auth: exécute la vraie vérification de session du Studio")


# autouse=True : cette fixture s'applique à chaque test sans qu'il la demande (comme un @BeforeEach commun).
@pytest.fixture(autouse=True)
def owner_session_override(request: pytest.FixtureRequest):
    """Les tests existants ciblent la logique métier : la session est considérée comme ouverte."""
    if request.node.get_closest_marker("real_auth"):
        app.dependency_overrides.pop(require_owner, None)
        app.state.owner_auth.limiter.reset()
        yield
        app.state.owner_auth.limiter.reset()
        return
    # dependency_overrides remplace une dépendance FastAPI pendant le test (équivalent d'un @MockBean Spring) :
    # ici la vérification de session est neutralisée pour tester la logique métier.
    app.dependency_overrides[require_owner] = lambda: None
    yield
    app.dependency_overrides.pop(require_owner, None)


# autouse=True : chaque test part d'une base PostgreSQL vierge et initialisée (tables + 3 catégories),
# pour que les tests restent indépendants les uns des autres.
@pytest.fixture(autouse=True)
def clean_database():
    """Supprime puis recrée le schéma de la base de test avant chaque test."""
    pg_support.reset_database()
    yield

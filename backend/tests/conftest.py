# Rôle : configuration pytest partagée ; ouvre la session propriétaire pour les tests du Studio.
# Exécution : chargé automatiquement par pytest avant chaque module de tests.
"""Surcharge la dépendance require_owner sauf pour les tests marqués « real_auth »."""

import pytest

from app.main import app
from app.routers.auth import require_owner


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "real_auth: exécute la vraie vérification de session du Studio")


@pytest.fixture(autouse=True)
def owner_session_override(request: pytest.FixtureRequest):
    """Les tests existants ciblent la logique métier : la session est considérée comme ouverte."""
    if request.node.get_closest_marker("real_auth"):
        app.dependency_overrides.pop(require_owner, None)
        app.state.owner_auth.limiter.reset()
        yield
        app.state.owner_auth.limiter.reset()
        return
    app.dependency_overrides[require_owner] = lambda: None
    yield
    app.dependency_overrides.pop(require_owner, None)

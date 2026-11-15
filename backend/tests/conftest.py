# Rôle : configuration pytest partagée ; ouvre la session propriétaire pour les tests du Studio.
# Exécution : chargé automatiquement par pytest avant chaque module de tests.
"""Surcharge la dépendance require_owner sauf pour les tests marqués « real_auth »."""

# pytest : outil de tests automatiques du projet (équivalent de JUnit).
# conftest.py est lu automatiquement : ses « fixtures » (préparations) servent à tous les tests.
import pytest

from app.main import app
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

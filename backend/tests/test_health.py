# Rôle : vérifie le contrat HTTP de GET /health.
# Exécution : Pytest découvre et lance ce fichier pendant la suite de tests.
"""Tests HTTP du contrôle de santé Forma3D Studio.

Pytest exécute ce fichier ; TestClient appelle l'application en mémoire sans
démarrer Uvicorn ni contacter un service externe.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok_status() -> None:
    """Vérifie le code HTTP et le contrat JSON de GET /health."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

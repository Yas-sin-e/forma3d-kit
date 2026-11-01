# Rôle : vérifie le contrat HTTP de GET /health.
# Exécution : Pytest découvre et lance ce fichier pendant la suite de tests.
"""Tests HTTP du contrôle de santé Forma3D Studio.

Pytest exécute ce fichier ; TestClient appelle l'application en mémoire sans
démarrer Uvicorn ni contacter un service externe.
"""

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.config import Settings
from app.providers.huggingface import HuggingFaceSpaceProvider
import app.main as main_module

client = TestClient(app)


def test_health_endpoint_returns_ok_status() -> None:
    """Vérifie le code HTTP et le contrat JSON de GET /health."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize("status", ["ONLINE", "OFFLINE", "UNCONFIGURED"])
def test_provider_health_endpoint_exposes_only_the_status(status: str, monkeypatch) -> None:
    monkeypatch.setattr(main_module.provider, "health_status", lambda: status)

    response = client.get("/health/provider")

    assert response.status_code == 200
    assert response.json()["status"] == status
    assert "secret.gradio.live" not in response.text
    if status == "OFFLINE":
        assert response.json()["message"] == (
            "Le serveur 3D (Colab) est arrêté ou son lien a expiré (72 h). "
            "Relance le notebook, copie la nouvelle ligne dans backend/.env, redémarre le serveur."
        )


def test_provider_health_is_unconfigured_without_a_target() -> None:
    provider = HuggingFaceSpaceProvider(settings=Settings(hf_space_id=""))

    assert provider.health_status() == "UNCONFIGURED"


def test_startup_warns_if_local_env_is_missing_or_provider_is_empty(
    tmp_path, monkeypatch, caplog
) -> None:
    monkeypatch.setattr(main_module, "_PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(main_module.provider, "settings", Settings(hf_space_id=""))

    with TestClient(app):
        pass

    assert "backend/.env est absent" in caplog.text
    assert "HF_SPACE_ID est vide" in caplog.text
    assert "gradio.live" not in caplog.text

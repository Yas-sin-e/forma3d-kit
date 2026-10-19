# Rôle : vérifie que FastAPI sert la page de génération et les vrais contrôles du viewer.
# Exécution : Pytest appelle GET / sans charger de modèle ni appeler de fournisseur.
"""Tests HTTP statiques de la page HTML du Sprint 1."""

from fastapi.testclient import TestClient

from app.main import app


def test_home_serves_upload_viewer_and_status_controls() -> None:
    response = TestClient(app).get("/")
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'lang="fr"' in html
    assert "<model-viewer" in html
    assert 'accept=".jpg,.jpeg,.png,.webp' in html
    assert 'fetch("/models"' in html
    assert "window.setInterval" in html
    assert "pollingInFlight" in html
    assert "function isAcceptedFile(file)" in html
    assert "Le viewer attend une génération réelle ou l'ouverture d'un fichier GLB local." in html
    assert "cameraOrbit" in html
    assert 'id="pan-left"' in html
    assert 'id="zoom-in"' in html
    assert 'id="open-local-glb"' in html
    assert 'accept=".glb,model/gltf-binary"' in html
    assert "Fichier local, non généré par l'application" in html
    assert "URL.createObjectURL(file)" in html
    assert "URL.revokeObjectURL(localObjectUrl)" in html
    local_handler = html.split('localGlbInput.addEventListener("change", () => {', 1)[1].split("\n      });", 1)[0]
    assert "fetch(" not in local_handler
    assert "FormData" not in local_handler

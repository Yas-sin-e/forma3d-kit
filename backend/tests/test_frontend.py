# Rôle : vérifie le HTML servi, le chargement des modules et l'isolation des appels HTTP.
# Exécution : Pytest appelle FastAPI avec TestClient, sans navigateur ni fournisseur distant.
"""Tests statiques de la page modulaire du Sprint 1."""

from fastapi.testclient import TestClient

from app.main import app


def test_home_serves_the_modular_studio_and_model_viewer() -> None:
    client = TestClient(app)
    response = client.get("/")
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'lang="fr"' in html
    assert "<model-viewer" in html
    assert "model-viewer/4.4.0/model-viewer.min.js" in html
    assert 'accept=".jpg,.jpeg,.png,.webp' in html
    assert "/static/css/theme.css" in html
    assert "/static/css/components.css" in html
    assert "/static/js/main.js" in html
    assert 'id="progress-steps"' in html
    assert 'id="gallery-filters"' in html
    assert 'id="gallery-grid"' in html
    assert 'id="open-local-glb"' in html
    assert 'accept=".glb,model/gltf-binary"' in html
    assert 'id="ar-button"' in html
    assert 'id="provider-badge"' in html
    assert 'id="provider-notice"' in html
    assert 'id="open-demo-model"' in html
    assert 'id="photo-guidance-title"' in html
    assert 'id="source-photo-image"' in html
    assert 'id="category-management"' in html
    assert 'id="category-create-form"' in html
    assert "Modèle approximatif créé à partir d’une seule photo" in html


def test_static_frontend_assets_are_served_and_only_api_module_calls_fetch() -> None:
    client = TestClient(app)
    api_response = client.get("/static/js/api.js")
    css_response = client.get("/static/css/components.css")
    module_paths = (
        "/static/js/main.js",
        "/static/js/state.js",
        "/static/js/views/uploader.js",
        "/static/js/views/progress.js",
        "/static/js/views/viewer.js",
        "/static/js/views/gallery.js",
        "/static/js/views/categories.js",
    )

    assert api_response.status_code == 200
    assert "fetch(" in api_response.text
    assert css_response.status_code == 200
    for path in module_paths:
        response = client.get(path)
        assert response.status_code == 200
        assert "fetch(" not in response.text


def test_provider_health_polling_and_offline_demo_fallback_are_in_api_modules() -> None:
    client = TestClient(app)
    api = client.get("/static/js/api.js").text
    main = client.get("/static/js/main.js").text
    uploader = client.get("/static/js/views/uploader.js").text
    gallery = client.get("/static/js/views/gallery.js").text
    categories = client.get("/static/js/views/categories.js").text

    assert 'fetch("/health/provider"' in api
    assert "30_000" in main
    assert "uploader.setProviderAvailable(false)" in main
    assert "uploader.setProviderAvailable(available)" in main
    assert "Le serveur 3D (Colab) est arrêté ou son lien a expiré (72 h)." in main
    assert "gallery.openFirstModel()" in main
    assert "providerAvailable" in uploader
    assert "openFirstModel" in gallery
    assert "setCategories(categories)" in uploader
    assert "setCategories(nextCategories)" in gallery
    assert "category.is_active" in gallery
    assert "createCategory" in categories
    assert "updateCategory" in categories
    assert "deleteCategory" in categories


def test_local_model_controls_do_not_send_files_to_the_backend() -> None:
    client = TestClient(app)
    viewer = client.get("/static/js/views/viewer.js").text

    local_handler = viewer.split('localInput.addEventListener("change", () => {', 1)[1].split(
        "\n  });", 1
    )[0]

    assert "URL.createObjectURL(url)" in viewer
    assert "URL.revokeObjectURL(localObjectUrl)" in viewer
    assert "fetch(" not in local_handler
    assert "FormData" not in local_handler

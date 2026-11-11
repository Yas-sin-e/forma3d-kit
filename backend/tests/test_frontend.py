# Rôle : vérifie le HTML servi, le chargement des modules et l'isolation des appels HTTP.
# Exécution : Pytest appelle FastAPI avec TestClient, sans navigateur ni fournisseur distant.
"""Tests statiques de la page modulaire du Sprint 1."""

import re

from fastapi.testclient import TestClient

from app.main import app


def test_home_serves_the_studio_shell_and_separate_navigation() -> None:
    client = TestClient(app)
    response = client.get("/")
    html = response.content.decode("utf-8")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'lang="fr"' in html
    assert 'id="app"' in html
    assert "model-viewer/4.4.0/model-viewer.min.js" in html
    assert "/static/css/theme.css" in html
    assert "/static/css/components.css" in html
    assert "/static/js/main.js" in html
    assert 'href="#/creer"' in html
    assert 'href="#/modeles"' in html
    assert 'href="#/categories"' in html
    assert 'href="#/cles-api"' in html
    assert 'href="#/exemples"' in html
    assert 'id="provider-badge"' in html

    create_page = client.get("/static/js/pages/create.js").text
    viewer = client.get("/static/js/pages/viewer-markup.js").text
    assert 'id="progress-steps"' in create_page
    assert 'id="photo-guidance-title"' in create_page
    assert 'id="image-preparation-warning"' in create_page
    assert 'id="model-viewer"' in viewer
    assert 'id="source-photo-image"' in viewer
    assert "Modèle approximatif créé à partir d’une seule photo" in create_page
    assert "Parcours de création" in create_page
    assert "Photo et catégorie" in create_page
    assert "submit-reason" in create_page
    assert "Détails techniques" in create_page
    assert "Conseils photo" in create_page
    assert "Validation du GLB" in create_page

    components = client.get("/static/css/components.css").text
    assert "grid-template-columns: minmax(340px" in components
    assert "max-width: 1023px" in components
    assert "grid-template-columns: repeat(5, 112px)" in components
    assert "@media (min-width: 1024px) and (max-height: 850px)" in components


def test_static_frontend_assets_are_served_and_only_api_module_calls_fetch() -> None:
    client = TestClient(app)
    api_response = client.get("/static/js/api.js")
    css_response = client.get("/static/css/components.css")
    module_paths = (
        "/static/js/main.js",
        "/static/js/router.js",
        "/static/js/state.js",
        "/static/js/pages/create.js",
        "/static/js/pages/models.js",
        "/static/js/pages/model-detail.js",
        "/static/js/pages/categories.js",
        "/static/js/pages/examples.js",
        "/static/js/pages/api-keys.js",
        "/static/js/pages/viewer-markup.js",
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
    assert "publishHealth" in main
    assert 'window.dispatchEvent(new CustomEvent("forma3d:health"' in main
    assert "providerAvailable" in uploader
    assert "setCategories(categories)" in uploader
    assert "setCategories(nextCategories)" in gallery
    assert "category.is_active" in gallery
    assert "createCategory" in categories
    assert "updateCategory" in categories
    assert "deleteCategory" in categories
    create = client.get("/static/js/pages/create.js").text
    assert "data.image_warning" in create
    assert "photo nette" in create


def test_hash_router_and_pages_cover_accessible_seller_routes() -> None:
    client = TestClient(app)
    router = client.get("/static/js/router.js").text
    models = client.get("/static/js/pages/models.js").text
    detail = client.get("/static/js/pages/model-detail.js").text
    categories_page = client.get("/static/js/pages/categories.js").text
    examples = client.get("/static/js/pages/examples.js").text
    category_view = client.get("/static/js/views/categories.js").text

    assert 'window.addEventListener("hashchange", renderRoute)' in router
    assert 'setAttribute("aria-current", "page")' in router
    assert "document.title" in router
    assert "heading.focus({ preventScroll: true })" in router
    assert "generationIdPattern.test(model.id)" in models
    assert "Ce modèle est introuvable" in detail
    assert "detail-duration" in detail
    assert "Catégories" in categories_page
    assert "Exemples de modèles" in examples
    assert "window.confirm" in category_view
    assert "Ce nom de catégorie est déjà utilisé" in category_view
    assert "Importer un modèle (.glb)" in models
    assert "Créer à partir d’une photo" in models
    assert "originLabels" in client.get("/static/js/views/gallery.js").text
    assert "Ajouter à mes modèles" in examples
    assert "copyExampleModel" in examples
    api_keys_page = client.get("/static/js/pages/api-keys.js").text
    assert "Clés API" in api_keys_page
    assert "ne sera affichée qu’une seule fois" in api_keys_page
    assert "createApiKey" in api_keys_page and "revokeApiKey" in api_keys_page
    assert "fetch(" not in api_keys_page
    assert 'parts[0] === "cles-api"' in router
    assert "detail-origin" in detail


def test_model_detail_has_an_opt_in_integration_control() -> None:
    client = TestClient(app)
    detail = client.get("/static/js/pages/model-detail.js").text
    api = client.get("/static/js/api.js").text

    assert 'id="detail-integration-toggle"' in detail
    assert "Désactivée par défaut" in detail
    assert "setModelIntegrationEnabled" in detail
    assert 'fetch(`/models/${encodeURIComponent(modelId)}/integration`' in api

    api = client.get("/static/js/api.js").text
    viewer_markup = client.get("/static/js/pages/viewer-markup.js").text
    assert 'fetch("/models/import"' in api
    assert "/copy" in api
    assert "Aperçu d’un fichier GLB (sans enregistrer)" in viewer_markup


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


def test_create_page_keeps_horizontal_journey_and_progress_layout() -> None:
    client = TestClient(app)
    shell = client.get("/").text
    create_page = client.get("/static/js/pages/create.js").text
    router = client.get("/static/js/router.js").text
    components = client.get("/static/css/components.css").text

    journey = create_page.index('<ol class="creation-steps"')
    workspace = create_page.index('<section class="workspace"')
    progress = create_page.index('<section class="panel progress-panel"')
    assert journey < workspace < progress
    assert 'aria-current="step"' in create_page

    section_depth = 0
    for tag in re.finditer(r"</?section\b", create_page[workspace:progress]):
        section_depth += -1 if tag.group().startswith("</") else 1
    assert section_depth == 0, "Le suivi doit venir après les deux colonnes du workspace"

    assert 'grid-template-columns: repeat(3, minmax(0, 1fr));' in components
    assert 'grid-template-columns: repeat(5, minmax(0, 1fr));' in components
    assert "components.css?v=20261111-5b" in shell
    assert '"./pages/create.js?v=20261111-5b"' in router

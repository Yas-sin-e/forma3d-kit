# Rôle : vérifie le HTML servi, le chargement des modules et l'isolation des appels HTTP.
# Exécution : Pytest appelle FastAPI avec TestClient, sans navigateur ni fournisseur distant.
"""Tests statiques de la page modulaire du Sprint 1."""

import re
from pathlib import Path

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
    assert "La géométrie est une estimation" in viewer
    assert "Parcours de création" not in create_page
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
        "/static/js/auth.js",
        "/static/js/format.js",
        "/static/js/pages/login.js",
        "/static/js/pages/dashboard.js",
        "/static/js/views/confirm-dialog.js",
        "/static/js/views/illustrations.js",
        "/static/js/views/model-appearance.js",
        "/static/js/state.js",
        "/static/js/pages/create.js",
        "/static/js/pages/models.js",
        "/static/js/pages/model-detail.js",
        "/static/js/pages/categories.js",
        "/static/js/pages/examples.js",
        "/static/js/pages/api-keys.js",
        "/static/widget.js",
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
    assert "confirmDialog" in category_view and "window.confirm" not in category_view
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
    assert 'id="detail-integration-code"' in detail
    assert "<forma3d-viewer" in detail
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


def test_create_page_keeps_workspace_then_progress_layout() -> None:
    client = TestClient(app)
    shell = client.get("/").text
    create_page = client.get("/static/js/pages/create.js").text
    router = client.get("/static/js/router.js").text
    components = client.get("/static/css/components.css").text

    # Refonte 16b : le stepper en 3 étapes, redondant avec le suivi, a été retiré.
    assert '<ol class="creation-steps"' not in create_page
    workspace = create_page.index('<section class="workspace"')
    progress = create_page.index('<section class="panel progress-panel"')
    assert workspace < progress

    section_depth = 0
    for tag in re.finditer(r"</?section\b", create_page[workspace:progress]):
        section_depth += -1 if tag.group().startswith("</") else 1
    assert section_depth == 0, "Le suivi doit venir après les deux colonnes du workspace"

    assert 'grid-template-columns: repeat(3, minmax(0, 1fr));' in components
    assert 'grid-template-columns: repeat(5, minmax(0, 1fr));' in components
    assert "components.css?v=20261115-e1" in shell
    assert '"./pages/create.js?v=20261115-e1"' in router


def test_widget_script_defines_the_integrator_tag_and_uses_embed_iframe() -> None:
    client = TestClient(app)
    response = client.get("/static/widget.js")
    assert response.status_code == 200
    assert "customElements.define(\"forma3d-viewer\"" in response.text
    assert "new URL(scriptUrl, document.baseURI).origin" in response.text
    assert "auto-rotate" in response.text
    assert "/embed/" in response.text
    assert "fetch(" not in response.text


def test_integration_example_loads_widget_for_a_real_public_model_id() -> None:
    """Empêche de distribuer une démonstration qui inventerait un modèle ou une URL."""
    repository_root = Path(__file__).resolve().parents[2]
    example = (repository_root / "examples" / "integration.html").read_text(encoding="utf-8")

    assert 'id="service-origin"' in example
    assert 'id="public-id"' in example
    assert 'new URL("/static/widget.js", service).href' in example
    assert "publicIdPattern.test(publicId)" in example
    assert 'viewer.setAttribute("model", publicId)' in example
    assert 'viewer.setAttribute("auto-rotate", "")' in example
    assert "innerHTML" not in example


def test_integrator_guide_documents_the_real_contract_and_security_limits() -> None:
    """Maintient les chemins réellement fournis et les restrictions lisibles par intégrateur."""
    repository_root = Path(__file__).resolve().parents[2]
    guide = (repository_root / "docs" / "INTEGRATION.md").read_text(encoding="utf-8")

    assert "/api/v1/models" in guide
    assert "/integration-code" in guide
    assert "X-API-Key" in guide
    assert "EMBED_ALLOWED_ORIGINS" in guide
    assert "API_DAILY_GENERATION_LIMIT" in guide
    assert "pas un service de production" in guide


def test_login_screen_guards_every_studio_route() -> None:
    client = TestClient(app)
    shell = client.get("/").text
    router = client.get("/static/js/router.js").text
    auth = client.get("/static/js/auth.js").text
    login = client.get("/static/js/pages/login.js").text
    dashboard = client.get("/static/js/pages/dashboard.js").text

    assert 'href="#/accueil"' in shell
    assert 'id="logout-button"' in shell
    assert 'id="admin-nav-group"' in shell
    assert "/static/favicon.svg" in shell
    assert client.get("/static/favicon.svg").status_code == 200
    assert 'parts[0] === "login"' in router
    assert "isAuthenticated()" in router
    assert "#/login" in router
    # Étape 5f : plus aucun mot de passe dans le navigateur ; la session vient du serveur.
    assert "forma3d-demo" not in auth and "TEMPORARY_STUDIO_PASSWORD" not in auth
    assert "getSession" in auth and "loginOwner" in auth
    api = client.get("/static/js/api.js").text
    assert 'fetch("/auth/me"' in api and 'fetch("/auth/login"' in api
    assert "forma3d:unauthorized" in api
    assert "Accéder au Studio" in login
    assert "Transformez vos photos en" in dashboard
    assert "listApiKeys" in dashboard and "listGalleryModels" in dashboard


def test_redesigned_pages_offer_guides_counts_and_honest_examples() -> None:
    client = TestClient(app)
    api_keys = client.get("/static/js/pages/api-keys.js").text
    detail = client.get("/static/js/pages/model-detail.js").text
    gallery = client.get("/static/js/views/gallery.js").text
    formatters = client.get("/static/js/format.js").text

    assert "/api/v1/models" in api_keys and "X-API-Key" in api_keys
    assert "confirmDialog" in api_keys and "window.confirm" not in api_keys
    assert 'role="switch"' in detail and 'role="tab"' in detail
    assert "/embed/" in detail
    assert "filter-count" in gallery
    assert "formatRelativeDate" in gallery
    # Durées mesurées : TripoSR (étape 6) ou TRELLIS (C2) selon le fournisseur affiché.
    assert '"chair-bentwood": 75.8' in formatters and '"chair-metal-01": 99.0' in formatters
    assert '"chair-bentwood": "TRELLIS"' in formatters and '"chair-metal-01": "TripoSR"' in formatters


def test_integration_guide_page_is_reachable_from_the_studio() -> None:
    client = TestClient(app)
    shell = client.get("/").text
    router = client.get("/static/js/router.js").text
    dashboard = client.get("/static/js/pages/dashboard.js").text
    guide = client.get("/static/js/pages/guide.js")

    assert guide.status_code == 200
    assert "fetch(" not in guide.text
    assert 'parts[0] === "guide"' in router
    assert 'href="#/guide"' in shell and 'href="#/guide"' in dashboard
    for fragment in ("/api/v1/models", "X-API-Key", "/embed/", "<forma3d-viewer", "EMBED_ALLOWED_ORIGINS", "API_DAILY_GENERATION_LIMIT"):
        assert fragment in guide.text


def test_viewers_fix_default_gltf_material_and_refit_in_compare_mode() -> None:
    """Sous-étape A : correction d'affichage seulement, le GLB n'est jamais modifié côté serveur."""
    client = TestClient(app)
    appearance = client.get("/static/js/views/model-appearance.js").text
    viewer = client.get("/static/js/views/viewer.js").text
    detail = client.get("/static/js/pages/model-detail.js").text
    gallery = client.get("/static/js/views/gallery.js").text
    dashboard = client.get("/static/js/pages/dashboard.js").text

    # Le défaut glTF (metallic = roughness = 1, sans texture) est seul remplacé par un matériau mat.
    assert "pbr.metallicFactor === 1 && pbr.roughnessFactor === 1" in appearance
    assert "setMetallicFactor(PRODUCT_METALLIC)" in appearance
    assert "PRODUCT_ROUGHNESS = 0.8" in appearance
    assert "updateFraming()" in appearance
    for module in (viewer, detail, gallery, dashboard):
        assert "watchProductAppearance(" in module
        assert "model-appearance.js?v=20261115-e1" in module
    assert "refitCamera(viewer)" in viewer and "refitCamera(modelViewer)" in detail
    assert 'removeAttribute("auto-rotate")' in detail


def test_create_page_shows_the_server_failure_reason() -> None:
    """Un quota épuisé ne doit pas être présenté comme un problème de photo."""
    create = TestClient(app).get("/static/js/pages/create.js").text
    assert "showFailure(data.error_message ||" in create


def test_compare_mode_keeps_photo_and_model_whole() -> None:
    """Photo contenue dans la scène et caméra reculée quand la scène devient plus haute que large."""
    client = TestClient(app)
    css = client.get("/static/css/components.css").text
    appearance = client.get("/static/js/views/model-appearance.js").text
    photo_rule = css.split(".stage-photo img {", 1)[1].split("}", 1)[0]
    assert "height: 100%" in photo_rule and "object-fit: contain" in photo_rule
    assert "export function radiusForAspect(aspect)" in appearance
    assert "Math.max(1, 1 / aspect)" in appearance
    assert "radiusForAspect(width / height)" in appearance
    assert 'window.dispatchEvent(new Event("resize"))' in appearance
    stage_rule = css.split(".detail-stage model-viewer {", 1)[1].split("}", 1)[0]
    assert "width: auto" in stage_rule and "height: auto" in stage_rule


def test_gallery_model_urls_change_when_the_file_changes() -> None:
    """Un exemple remplacé (TripoSR → TRELLIS) ne doit pas être resservi depuis le cache du navigateur."""
    client = TestClient(app)
    api = client.get("/static/js/api.js").text
    assert "export function withFileVersion(url, sizeBytes)" in api
    assert "withFileVersion(item.model_url, item.size_bytes)" in api
    # La route du GLB accepte et ignore le paramètre de version.
    assert client.get("/models/gallery/inconnu?v=123").status_code == 404


def test_revoked_api_keys_offer_a_confirmed_permanent_delete() -> None:
    client = TestClient(app)
    page = client.get("/static/js/pages/api-keys.js").text
    api = client.get("/static/js/api.js").text
    assert "Supprimer définitivement" in page and "deleteRevokedApiKey(key.id)" in page
    assert "Cette action est irréversible" in page
    assert "/permanent`" in api
    # Le secret affiché disparaît dès que sa clé est révoquée ou supprimée.
    assert page.count("hideRevealFor(key.id)") == 2


def test_confirm_dialog_settles_without_relying_on_the_close_event() -> None:
    """Certains navigateurs n'envoient pas « close » : les boutons concluent eux-mêmes."""
    dialog = TestClient(app).get("/static/js/views/confirm-dialog.js").text
    assert 'confirm.addEventListener("click", () => finish(true))' in dialog
    assert 'cancel.addEventListener("click", () => finish(false))' in dialog
    assert "if (settled) return;" in dialog and "dialog.remove();" in dialog


def test_model_detail_offers_a_confirmed_permanent_delete() -> None:
    client = TestClient(app)
    detail = client.get("/static/js/pages/model-detail.js").text
    api = client.get("/static/js/api.js").text
    assert 'id="detail-delete"' in detail and "Supprimer ce modèle" in detail
    assert "confirmDialog(" in detail and "Cette action est irréversible" in detail
    # Le bouton n'apparaît que pour un modèle de l'historique, jamais pendant la création.
    assert "storedInHistory = true" in detail and '["PENDING", "RUNNING"].includes(record.status)' in detail
    assert "deleteModel(route.id)" in detail and 'window.location.hash = "#/modeles"' in detail
    assert "export async function deleteModel" in api and 'method: "DELETE"' in api


def test_create_page_explains_each_upload_failure_with_cause_and_action() -> None:
    client = TestClient(app)
    create = client.get("/static/js/pages/create.js").text
    api = client.get("/static/js/api.js").text
    # api.js transmet le code HTTP, le message du serveur et Retry-After sans changer le message existant.
    assert "error.status = response.status;" in api
    assert "error.serverDetail" in api and 'response.headers.get("Retry-After")' in api
    assert "throw new Error(detail)" not in api
    # La page Créer traduit chaque cause réelle de POST /models en message + action.
    assert "describeUploadError(error)" in create
    assert "error instanceof TypeError" in create and "Le Studio ne répond pas." in create
    for code in ("case 400:", "case 413:", "case 415:", "case 422:", "case 401:", "case 429:", "case 503:"):
        assert code in create
    assert "Votre photo dépasse 10 Mo. Réduisez-la ou choisissez une image plus légère." in create
    assert "renommer le fichier ne suffit pas" in create
    assert "Votre session a expiré." in create
    assert "Réessayez dans ${formatWait(error.retryAfterSeconds)}." in create
    assert "Administration → Catégories" in create
    assert "Impossible de lancer la création. Vérifiez la photo et réessayez." not in create


def test_expired_session_is_announced_on_the_login_page() -> None:
    client = TestClient(app)
    auth = client.get("/static/js/auth.js").text
    login = client.get("/static/js/pages/login.js").text
    assert 'window.sessionStorage.setItem(SESSION_EXPIRED_KEY, "1");' in auth
    assert "export function consumeSessionExpired()" in auth
    assert "consumeSessionExpired()" in login and "Votre session a expiré. Reconnectez-vous pour continuer." in login

# Rôle : vérifie la connexion serveur du Studio (étape 5f) : cookie, refus, limite et routes publiques.
# Exécution : pytest ; aucune requête réseau externe, mot de passe de test injecté par monkeypatch.
"""Tests de l'authentification mono-propriétaire et de la protection des routes du Studio."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.owner_auth import (
    OWNER_PASSWORD_ENV,
    SESSION_COOKIE_NAME,
    LoginAttemptLimiter,
    LoginRateLimitedError,
    OwnerAuthService,
    session_key_from_environment,
)

pytestmark = pytest.mark.real_auth
TEST_PASSWORD = "mot-de-passe-de-test"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Client de test avec un mot de passe propriétaire défini pour la durée du test."""
    monkeypatch.setenv(OWNER_PASSWORD_ENV, TEST_PASSWORD)
    return TestClient(app)


@pytest.mark.parametrize("method, path", [
    ("get", "/models/gallery"),
    ("get", "/categories"),
    ("get", "/api-keys"),
    ("post", "/api-keys"),
    ("post", "/models"),
    ("post", "/models/import"),
    ("patch", "/models/00000000-0000-4000-8000-000000000000/integration"),
    ("delete", "/models/00000000-0000-4000-8000-000000000000"),
    ("delete", "/api-keys/00000000-0000-4000-8000-000000000000/permanent"),
])
def test_studio_routes_return_401_without_session_cookie(client: TestClient, method: str, path: str) -> None:
    """Prouve que chaque route du Studio répond 401 « Connexion requise. » sans cookie de session."""
    response = getattr(client, method)(path)
    assert response.status_code == 401
    assert response.json()["detail"] == "Connexion requise."


def test_successful_login_sets_a_secure_cookie_and_opens_studio_routes(client: TestClient) -> None:
    """Prouve qu'une connexion réussie pose un cookie HttpOnly, SameSite=Lax, 8 h, sans le mot de passe, puis que la déconnexion referme l'accès."""
    response = client.post("/auth/login", json={"password": TEST_PASSWORD})

    assert response.status_code == 200
    cookie_header = response.headers["set-cookie"]
    assert SESSION_COOKIE_NAME in cookie_header
    assert "HttpOnly" in cookie_header
    assert "samesite=lax" in cookie_header.lower()
    assert "Max-Age=28800" in cookie_header
    assert TEST_PASSWORD not in cookie_header
    assert client.get("/auth/me").json() == {"authenticated": True, "configured": True}
    assert client.get("/categories").status_code == 200

    client.post("/auth/logout")
    assert client.get("/auth/me").json()["authenticated"] is False
    assert client.get("/categories").status_code == 401


def test_wrong_password_is_refused(client: TestClient) -> None:
    """Prouve qu'un mot de passe faux est refusé (401)."""
    response = client.post("/auth/login", json={"password": "faux"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Mot de passe incorrect."
    assert "set-cookie" not in response.headers


def test_login_is_refused_with_a_clear_message_when_password_is_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prouve qu'en l'absence de mot de passe configuré, la connexion est refusée avec un message clair (503)."""
    monkeypatch.delenv(OWNER_PASSWORD_ENV, raising=False)
    client = TestClient(app)
    response = client.post("/auth/login", json={"password": "nimporte"})
    assert response.status_code == 503
    assert OWNER_PASSWORD_ENV in response.json()["detail"]
    assert client.get("/auth/me").json() == {"authenticated": False, "configured": False}


def test_sixth_attempt_in_a_minute_is_rate_limited(client: TestClient) -> None:
    """Prouve que la sixième tentative en moins d'une minute est bloquée (429)."""
    for _ in range(5):
        assert client.post("/auth/login", json={"password": "faux"}).status_code == 401
    response = client.post("/auth/login", json={"password": TEST_PASSWORD})
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) >= 1


def test_forged_or_expired_tokens_are_rejected(client: TestClient) -> None:
    """Prouve qu'un jeton falsifié ou expiré est refusé."""
    client.cookies.set(SESSION_COOKIE_NAME, "owner.9999999999.signature-inventee")
    assert client.get("/categories").status_code == 401

    now = [1_000_000.0]
    service = OwnerAuthService(ttl_seconds=60, clock=lambda: now[0], password_reader=lambda: "x")
    token = service.issue_token()
    assert service.validate_token(token)
    now[0] += 61
    assert not service.validate_token(token)


def test_public_routes_stay_open_without_session(client: TestClient) -> None:
    """Prouve que les routes publiques (/health, /embed, /public, /api/v1) ne demandent pas la session du Studio."""
    assert client.get("/").status_code == 200
    assert client.get("/health").status_code == 200
    assert client.get("/static/widget.js").status_code == 200
    assert client.get("/static/js/main.js").status_code == 200
    # /api/v1 reste protégée par X-API-Key (401 de clé), pas par la session du Studio.
    api_response = client.get("/api/v1/models/00000000-0000-4000-8000-000000000000")
    assert api_response.status_code == 401
    assert api_response.json()["error"]["code"] == "unauthorized"
    assert "Clé API" in api_response.json()["error"]["message"]
    # /embed et /public répondent 404 pour un modèle inconnu, sans exiger de connexion.
    assert client.get("/embed/00000000-0000-4000-8000-000000000000").status_code == 404
    assert client.get("/public/models/00000000-0000-4000-8000-000000000000").status_code == 404


def test_limiter_window_slides() -> None:
    """Prouve que la fenêtre de la limite de tentatives glisse : les anciennes tentatives sont oubliées après 60 s."""
    now = [0.0]
    limiter = LoginAttemptLimiter(max_attempts=2, window_seconds=60, clock=lambda: now[0])
    limiter.register("1.2.3.4")
    limiter.register("1.2.3.4")
    with pytest.raises(LoginRateLimitedError):
        limiter.register("1.2.3.4")
    limiter.register("5.6.7.8")
    now[0] = 61.0
    limiter.register("1.2.3.4")


SECRET = "x" * 32


def test_session_survives_a_restart_when_a_fixed_secret_is_configured() -> None:
    """Deux services = deux processus successifs : la même clé fixe valide l'ancien jeton."""
    reader = {"FORMA3D_SESSION_SECRET": SECRET}.get
    before_restart = OwnerAuthService(signing_key=session_key_from_environment(reader))
    token = before_restart.issue_token()

    after_restart = OwnerAuthService(signing_key=session_key_from_environment(reader))

    assert after_restart.validate_token(token)


def test_without_secret_a_restart_still_invalidates_the_session() -> None:
    """Prouve que sans FORMA3D_SESSION_SECRET, un redémarrage invalide toujours la session."""
    assert session_key_from_environment({}.get) is None
    token = OwnerAuthService(signing_key=session_key_from_environment({}.get)).issue_token()

    assert not OwnerAuthService(signing_key=session_key_from_environment({}.get)).validate_token(token)


def test_changing_the_secret_disconnects_existing_sessions() -> None:
    """Prouve que changer la clé de session déconnecte les sessions existantes."""
    token = OwnerAuthService(signing_key=session_key_from_environment({"FORMA3D_SESSION_SECRET": SECRET}.get)).issue_token()
    other = OwnerAuthService(signing_key=session_key_from_environment({"FORMA3D_SESSION_SECRET": "y" * 32}.get))

    assert not other.validate_token(token)


def test_a_too_short_session_secret_is_refused_at_startup() -> None:
    """Prouve qu'une clé de session de moins de 32 caractères est refusée au démarrage."""
    with pytest.raises(ValueError, match="au moins 32 caractères"):
        session_key_from_environment({"FORMA3D_SESSION_SECRET": "trop-court"}.get)

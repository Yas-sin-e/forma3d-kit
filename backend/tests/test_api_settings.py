# Rôle : vérifie les réglages gratuits de quota, de débit et de CORS du module intégrable.
# Exécution : tests unitaires purs, sans lire le fichier local backend/.env.
"""Tests des paramètres d’accès à l’API publique versionnée."""

import pytest

from app.config import Settings, get_settings, parse_api_cors_origins, parse_embed_allowed_origins


def test_api_limits_have_safe_free_defaults_and_cors_is_closed() -> None:
    settings = Settings()
    assert settings.api_daily_generation_limit == 20
    assert settings.api_rate_limit_per_minute == 10
    assert settings.api_cors_origins == ()


def test_cors_origin_parser_deduplicates_exact_origins_without_open_wildcard() -> None:
    assert parse_api_cors_origins("https://shop.example, https://shop.example/, http://localhost:3000") == (
        "https://shop.example",
        "http://localhost:3000",
    )
    with pytest.raises(ValueError, match=r"origines HTTP\(S\) précises"):
        Settings(api_cors_origins=("*",))
    with pytest.raises(ValueError, match=r"origines HTTP\(S\) précises"):
        Settings(api_cors_origins=("https://shop.example/path",))
    assert parse_embed_allowed_origins("https://shop.example") == ("https://shop.example",)
    with pytest.raises(ValueError, match="EMBED_ALLOWED_ORIGINS"):
        Settings(embed_allowed_origins=("*",))


def test_api_settings_read_limits_and_cors_from_process_environment(monkeypatch) -> None:
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "true")
    monkeypatch.setenv("API_DAILY_GENERATION_LIMIT", "7")
    monkeypatch.setenv("API_RATE_LIMIT_PER_MINUTE", "3")
    monkeypatch.setenv("API_CORS_ORIGINS", "https://shop.example,https://admin.example")
    monkeypatch.setenv("EMBED_ALLOWED_ORIGINS", "https://frames.example")
    settings = get_settings()
    assert settings.api_daily_generation_limit == 7
    assert settings.api_rate_limit_per_minute == 3
    assert settings.api_cors_origins == ("https://shop.example", "https://admin.example")
    assert settings.embed_allowed_origins == ("https://frames.example",)

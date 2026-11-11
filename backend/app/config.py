# Rôle : charge et valide les réglages d'un Space Hugging Face ou d'un serveur Gradio.
# Exécution : appelé à la première génération ; jamais besoin d'un secret pour démarrer l'API.
"""Configuration locale du fournisseur image-vers-3D."""

import math
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Réglages d'un Space ou serveur Gradio et des limites d'attente."""

    hf_space_id: str = ""
    hf_token: str | None = None
    hf_timeout_seconds: int = 300
    hf_max_attempts: int = 2
    hf_retry_delay_seconds: float = 5.0
    foreground_ratio: float | None = None
    mc_resolution: int | None = None
    max_glb_upload_mb: int = 30
    api_daily_generation_limit: int = 20
    api_rate_limit_per_minute: int = 10
    api_cors_origins: tuple[str, ...] = ()
    embed_allowed_origins: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Refuse une cible distante invalide ou des délais non positifs."""
        target = self.hf_space_id.strip()
        if "://" in target:
            parsed = urlsplit(target)
            if (
                parsed.scheme.casefold() not in {"http", "https"}
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError(
                    "HF_SPACE_ID doit être un identifiant de Space ou une URL HTTP(S) "
                    "sans identifiants, paramètres ni fragment."
                )
        if self.hf_timeout_seconds <= 0:
            raise ValueError("HF_TIMEOUT_SECONDS doit être positif.")
        if self.hf_max_attempts < 1 or self.hf_max_attempts > 2:
            raise ValueError("HF_MAX_ATTEMPTS doit être égal à 1 ou 2.")
        if self.hf_retry_delay_seconds < 0:
            raise ValueError("HF_RETRY_DELAY_SECONDS ne peut pas être négatif.")
        if self.foreground_ratio is not None and not math.isfinite(self.foreground_ratio):
            raise ValueError("FOREGROUND_RATIO doit être un nombre fini.")
        if self.mc_resolution is not None and self.mc_resolution <= 0:
            raise ValueError("MC_RESOLUTION doit être un entier positif.")
        if self.max_glb_upload_mb < 1 or self.max_glb_upload_mb > 512:
            raise ValueError("MAX_GLB_UPLOAD_MB doit être compris entre 1 et 512.")
        if self.api_daily_generation_limit < 1:
            raise ValueError("API_DAILY_GENERATION_LIMIT doit être au moins égal à 1.")
        if self.api_rate_limit_per_minute < 1:
            raise ValueError("API_RATE_LIMIT_PER_MINUTE doit être au moins égal à 1.")
        for setting_name, origins in (
            ("API_CORS_ORIGINS", self.api_cors_origins),
            ("EMBED_ALLOWED_ORIGINS", self.embed_allowed_origins),
        ):
            for origin in origins:
                parsed_origin = urlsplit(origin)
                try:
                    parsed_origin.port
                except ValueError as error:
                    raise ValueError(f"{setting_name} contient un port invalide.") from error
                if (
                    not origin
                    or origin == "*"
                    or parsed_origin.scheme.casefold() not in {"http", "https"}
                    or not parsed_origin.hostname
                    or parsed_origin.username
                    or parsed_origin.password
                    or parsed_origin.path not in {"", "/"}
                    or parsed_origin.query
                    or parsed_origin.fragment
                ):
                    raise ValueError(f"{setting_name} doit contenir des origines HTTP(S) précises, jamais *.")


def parse_api_cors_origins(value: str) -> tuple[str, ...]:
    """Convertit une liste séparée par des virgules en origines explicites."""
    return tuple(dict.fromkeys(item.strip().rstrip("/") for item in value.split(",") if item.strip()))


def parse_embed_allowed_origins(value: str) -> tuple[str, ...]:
    """Convertit la liste des origines autorisées par CSP frame-ancestors."""
    return parse_api_cors_origins(value)


def get_settings() -> Settings:
    """Charge backend/.env en priorité, puis .env racine, sans écraser l'environnement."""
    load_dotenv(_PROJECT_ROOT / "backend" / ".env", override=False)
    load_dotenv(_PROJECT_ROOT / ".env", override=False)
    token = os.getenv("HF_TOKEN", "").strip() or None
    foreground_ratio = os.getenv("FOREGROUND_RATIO", "").strip()
    mc_resolution = os.getenv("MC_RESOLUTION", "").strip()
    return Settings(
        hf_space_id=os.getenv("HF_SPACE_ID", "").strip(),
        hf_token=token,
        hf_timeout_seconds=int(os.getenv("HF_TIMEOUT_SECONDS", "300")),
        hf_max_attempts=int(os.getenv("HF_MAX_ATTEMPTS", "2")),
        hf_retry_delay_seconds=float(os.getenv("HF_RETRY_DELAY_SECONDS", "5")),
        foreground_ratio=float(foreground_ratio) if foreground_ratio else None,
        mc_resolution=int(mc_resolution) if mc_resolution else None,
        max_glb_upload_mb=int(os.getenv("MAX_GLB_UPLOAD_MB", "30")),
        api_daily_generation_limit=int(os.getenv("API_DAILY_GENERATION_LIMIT", "20")),
        api_rate_limit_per_minute=int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "10")),
        api_cors_origins=parse_api_cors_origins(os.getenv("API_CORS_ORIGINS", "")),
        embed_allowed_origins=parse_embed_allowed_origins(os.getenv("EMBED_ALLOWED_ORIGINS", "")),
    )

# Rôle : charge et valide les réglages d'un Space Hugging Face ou d'un serveur Gradio.
# Exécution : appelé à la première génération ; jamais besoin d'un secret pour démarrer l'API.
"""Configuration locale du fournisseur image-vers-3D."""

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    """Réglages d'un Space ou serveur Gradio et des limites d'attente."""

    hf_space_id: str = "stabilityai/stable-fast-3d"
    hf_token: str | None = None
    hf_timeout_seconds: int = 300
    hf_max_attempts: int = 2
    hf_retry_delay_seconds: float = 5.0

    def __post_init__(self) -> None:
        """Refuse une cible distante invalide ou des délais non positifs."""
        target = self.hf_space_id.strip()
        if not target:
            raise ValueError("HF_SPACE_ID ne peut pas être vide.")
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


def get_settings() -> Settings:
    """Charge backend/.env en priorité, puis .env racine, sans écraser l'environnement."""
    load_dotenv(_PROJECT_ROOT / "backend" / ".env", override=False)
    load_dotenv(_PROJECT_ROOT / ".env", override=False)
    token = os.getenv("HF_TOKEN", "").strip() or None
    return Settings(
        hf_space_id=os.getenv("HF_SPACE_ID", "stabilityai/stable-fast-3d").strip(),
        hf_token=token,
        hf_timeout_seconds=int(os.getenv("HF_TIMEOUT_SECONDS", "300")),
        hf_max_attempts=int(os.getenv("HF_MAX_ATTEMPTS", "2")),
        hf_retry_delay_seconds=float(os.getenv("HF_RETRY_DELAY_SECONDS", "5")),
    )

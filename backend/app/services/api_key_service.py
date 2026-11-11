# Rôle : crée, révoque et vérifie les clés destinées à l’API d’intégration.
# Exécution : les routes de gestion et la dépendance FastAPI délèguent ici la logique sensible.
"""Service de clés API : secret révélé une fois, empreinte SHA-256 persistée."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from uuid import uuid4

from app.models import APIKeyRecord
from app.repositories.base import GenerationRepository

_KEY_PREFIX = "f3d_live_"
_PREFIX_RANDOM_LENGTH = 8
_DUMMY_FINGERPRINT = hashlib.sha256(b"forma3d-invalid-api-key").hexdigest()


class APIKeyValidationError(ValueError):
    """Erreur de nommage d’une clé API."""


class APIKeyService:
    """Gère les secrets sans jamais les conserver ni les journaliser."""

    def __init__(self, repository: GenerationRepository) -> None:
        self._repository = repository

    def create(self, name: str) -> tuple[APIKeyRecord, str]:
        """Crée une clé aléatoire et retourne son secret une seule fois à l’appelant."""
        clean_name = name.strip()
        if not clean_name:
            raise APIKeyValidationError("Donnez un nom à cette clé API.")
        if len(clean_name) > 80:
            raise APIKeyValidationError("Le nom d’une clé API ne peut pas dépasser 80 caractères.")
        secret = _KEY_PREFIX + secrets.token_urlsafe(32)
        prefix = secret[: len(_KEY_PREFIX) + _PREFIX_RANDOM_LENGTH]
        record = APIKeyRecord(
            id=str(uuid4()),
            name=clean_name,
            prefix=prefix,
            fingerprint=self._fingerprint(secret),
            created_at=datetime.now(UTC),
        )
        return self._repository.create_api_key(record), secret

    def list(self) -> list[APIKeyRecord]:
        """Retourne les métadonnées de gestion, sans valeur secrète."""
        return self._repository.list_api_keys()

    def revoke(self, key_id: str) -> APIKeyRecord | None:
        """Désactive une clé existante ; la révocation est persistante et idempotente."""
        return self._repository.revoke_api_key(key_id)

    def consume_rate_limit(
        self, key: APIKeyRecord, limit_per_minute: int, now: datetime | None = None
    ) -> str | None:
        """Réserve une requête API pour cette clé dans la fenêtre d’une minute."""
        return self._repository.consume_api_rate_limit(
            key.id, limit_per_minute, now or datetime.now(UTC)
        )

    def consume_daily_quota(
        self, key: APIKeyRecord, daily_limit: int, now: datetime | None = None
    ) -> str | None:
        """Réserve une création pour cette clé dans la journée UTC courante."""
        return self._repository.consume_api_daily_quota(
            key.id, daily_limit, now or datetime.now(UTC)
        )

    def authenticate(self, candidate: str | None) -> APIKeyRecord | None:
        """Vérifie une clé active avec comparaison d’empreintes à temps constant."""
        supplied = candidate or ""
        prefix_length = len(_KEY_PREFIX) + _PREFIX_RANDOM_LENGTH
        prefix = supplied[:prefix_length] if supplied.startswith(_KEY_PREFIX) else ""
        fingerprint = self._fingerprint(supplied)
        matches = self._repository.find_api_keys_by_prefix(prefix) if prefix else []
        if not matches:
            hmac.compare_digest(fingerprint, _DUMMY_FINGERPRINT)
            return None
        accepted: APIKeyRecord | None = None
        for record in matches:
            is_match = hmac.compare_digest(fingerprint, record.fingerprint)
            if is_match:
                accepted = record
        return accepted

    @staticmethod
    def _fingerprint(secret: str) -> str:
        """Calcule l’empreinte persistée sans conserver la clé en clair."""
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()

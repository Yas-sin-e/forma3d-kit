# Rôle : vérifie le mot de passe unique de la propriétaire, signe les jetons de session et limite les tentatives.
# Exécution : créé au démarrage dans main.py ; utilisé par app/routers/auth.py et la dépendance require_owner.
"""Authentification mono-propriétaire du Studio (mot de passe unique, session signée HMAC)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from typing import Callable

OWNER_PASSWORD_ENV = "FORMA3D_OWNER_PASSWORD"
SESSION_COOKIE_NAME = "forma3d_session"
SESSION_TTL_SECONDS = 8 * 60 * 60
LOGIN_ATTEMPTS_PER_MINUTE = 5


class OwnerPasswordNotConfiguredError(RuntimeError):
    """Levée quand FORMA3D_OWNER_PASSWORD est absente : toute connexion est refusée."""


class LoginRateLimitedError(RuntimeError):
    """Levée quand une adresse IP dépasse le nombre de tentatives autorisées."""

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("Trop de tentatives de connexion.")
        self.retry_after_seconds = retry_after_seconds


class LoginAttemptLimiter:
    """Compte les tentatives par IP sur une fenêtre glissante, uniquement en mémoire."""

    def __init__(self, max_attempts: int = LOGIN_ATTEMPTS_PER_MINUTE, window_seconds: float = 60.0,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        self._clock = clock
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def register(self, client_ip: str) -> None:
        """Enregistre une tentative ou lève LoginRateLimitedError si la limite est atteinte."""
        now = self._clock()
        with self._lock:
            attempts = self._attempts[client_ip]
            while attempts and now - attempts[0] >= self._window_seconds:
                attempts.popleft()
            if len(attempts) >= self._max_attempts:
                retry_after = max(1, int(self._window_seconds - (now - attempts[0])) + 1)
                raise LoginRateLimitedError(retry_after)
            attempts.append(now)

    def reset(self) -> None:
        """Vide les compteurs (tests et redémarrage)."""
        with self._lock:
            self._attempts.clear()


class OwnerAuthService:
    """Vérifie le mot de passe et émet/valide des jetons « owner.<expiration>.<signature> »."""

    def __init__(self, signing_key: bytes | None = None, ttl_seconds: int = SESSION_TTL_SECONDS,
                 clock: Callable[[], float] = time.time,
                 password_reader: Callable[[], str | None] | None = None) -> None:
        # Clé aléatoire par processus : un redémarrage du serveur invalide les sessions ouvertes.
        self._signing_key = signing_key or secrets.token_bytes(32)
        self.ttl_seconds = ttl_seconds
        self._clock = clock
        self._password_reader = password_reader or (lambda: os.getenv(OWNER_PASSWORD_ENV))
        self.limiter = LoginAttemptLimiter()

    def is_configured(self) -> bool:
        return bool((self._password_reader() or "").strip())

    def verify_password(self, candidate: str) -> bool:
        """Compare en temps constant ; lève une erreur claire si aucun mot de passe n'est configuré."""
        expected = (self._password_reader() or "").strip()
        if not expected:
            raise OwnerPasswordNotConfiguredError(
                f"Connexion impossible : la variable {OWNER_PASSWORD_ENV} n'est pas configurée sur le serveur."
            )
        return hmac.compare_digest(candidate.encode("utf-8"), expected.encode("utf-8"))

    def _sign(self, payload: str) -> str:
        digest = hmac.new(self._signing_key, payload.encode("ascii"), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    def issue_token(self) -> str:
        expires_at = int(self._clock()) + self.ttl_seconds
        payload = f"owner.{expires_at}"
        return f"{payload}.{self._sign(payload)}"

    def validate_token(self, token: str | None) -> bool:
        """Accepte uniquement un jeton bien formé, signé par ce serveur et non expiré."""
        if not token or token.count(".") != 2:
            return False
        subject, expires_text, signature = token.split(".")
        if subject != "owner" or not expires_text.isdigit():
            return False
        if not hmac.compare_digest(signature, self._sign(f"{subject}.{expires_text}")):
            return False
        return int(expires_text) > int(self._clock())

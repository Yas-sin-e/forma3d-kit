# Rôle : vérifie le mot de passe unique de la propriétaire, signe les jetons de session et limite les tentatives.
# Exécution : créé au démarrage dans main.py ; utilisé par app/routers/auth.py et la dépendance require_owner.
"""Authentification mono-propriétaire du Studio (mot de passe unique, session signée HMAC)."""

from __future__ import annotations

# base64 (standard) : transforme des octets en texte ASCII (ici la signature mise dans le cookie).
import base64
# hashlib (standard) : fonctions de hachage (SHA-256). Un hachage est à sens unique :
# on peut vérifier une valeur, pas la retrouver. Équivalent de java.security.MessageDigest.
import hashlib
# hmac (standard) : signature avec clé secrète (HMAC) et comparaison en temps constant.
# Ici : signe le jeton de session et compare les secrets sans fuite par le temps de réponse.
import hmac
import os
# secrets (standard) : hasard de qualité cryptographique (jamais le module random pour un secret).
import secrets
# threading (standard) : verrou (Lock) pour protéger des données partagées entre requêtes simultanées.
import threading
import time
# collections (standard) : deque = file rapide aux deux bouts ; defaultdict = dictionnaire qui crée
# la valeur manquante. Ici : une file des dernières tentatives par adresse IP.
from collections import defaultdict, deque
from typing import Callable

OWNER_PASSWORD_ENV = "FORMA3D_OWNER_PASSWORD"
SESSION_SECRET_ENV = "FORMA3D_SESSION_SECRET"
SESSION_SECRET_MIN_LENGTH = 32
SESSION_COOKIE_NAME = "forma3d_session"
SESSION_TTL_SECONDS = 8 * 60 * 60
LOGIN_ATTEMPTS_PER_MINUTE = 5


class OwnerPasswordNotConfiguredError(RuntimeError):
    """Levée quand FORMA3D_OWNER_PASSWORD est absente : toute connexion est refusée."""


class LoginRateLimitedError(RuntimeError):
    """Levée quand une adresse IP dépasse le nombre de tentatives autorisées."""

    def __init__(self, retry_after_seconds: int) -> None:
        """Mémorise dans l'erreur le nombre de secondes à attendre (renvoyé dans l'en-tête Retry-After)."""
        super().__init__("Trop de tentatives de connexion.")
        self.retry_after_seconds = retry_after_seconds


class LoginAttemptLimiter:
    """Compte les tentatives par IP sur une fenêtre glissante, uniquement en mémoire."""

    def __init__(self, max_attempts: int = LOGIN_ATTEMPTS_PER_MINUTE, window_seconds: float = 60.0,
                 clock: Callable[[], float] = time.monotonic) -> None:
        """Prépare le compteur : nombre maximal de tentatives, taille de la fenêtre en secondes, horloge.

        L'horloge est un paramètre pour que les tests puissent simuler le temps qui passe.
        """
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        self._clock = clock
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def register(self, client_ip: str) -> None:
        """Enregistre une tentative ou lève LoginRateLimitedError si la limite est atteinte.

        Fenêtre glissante : on retire d'abord les tentatives plus vieilles que 60 s, puis on compte.
        Paramètre : client_ip (adresse du client). Le verrou évite deux mises à jour simultanées.
        """
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


def session_key_from_environment(reader: Callable[[str], str | None] = os.getenv) -> bytes | None:
    """Clé de signature fixe tirée de FORMA3D_SESSION_SECRET, ou None pour une clé aléatoire par processus.

    Remplie, elle garde la session ouverte après un redémarrage du serveur (toujours 8 h au plus).
    Un secret trop court est refusé au démarrage plutôt que d'affaiblir silencieusement les sessions.
    """
    secret = (reader(SESSION_SECRET_ENV) or "").strip()
    if not secret:
        return None
    if len(secret) < SESSION_SECRET_MIN_LENGTH:
        raise ValueError(
            f"{SESSION_SECRET_ENV} doit contenir au moins {SESSION_SECRET_MIN_LENGTH} caractères "
            "(générez-le avec secrets.token_urlsafe(32)) ou rester vide."
        )
    # SHA-256 ramène n'importe quel secret assez long à une clé HMAC de 32 octets.
    return hashlib.sha256(secret.encode("utf-8")).digest()


class OwnerAuthService:
    """Vérifie le mot de passe et émet/valide des jetons « owner.<expiration>.<signature> »."""

    def __init__(self, signing_key: bytes | None = None, ttl_seconds: int = SESSION_TTL_SECONDS,
                 clock: Callable[[], float] = time.time,
                 password_reader: Callable[[], str | None] | None = None) -> None:
        """Prépare le service : clé de signature, durée de session, horloge et lecteur du mot de passe.

        signing_key=None -> clé aléatoire (les sessions ne survivent pas à un redémarrage).
        Les paramètres clock et password_reader existent pour les tests.
        """
        # Sans clé fournie : clé aléatoire par processus, un redémarrage invalide les sessions ouvertes.
        # main.py fournit la clé de FORMA3D_SESSION_SECRET quand elle est configurée.
        self._signing_key = signing_key or secrets.token_bytes(32)
        self.ttl_seconds = ttl_seconds
        self._clock = clock
        self._password_reader = password_reader or (lambda: os.getenv(OWNER_PASSWORD_ENV))
        self.limiter = LoginAttemptLimiter()

    def is_configured(self) -> bool:
        """Vrai si un mot de passe propriétaire non vide est défini dans l'environnement."""
        return bool((self._password_reader() or "").strip())

    def verify_password(self, candidate: str) -> bool:
        """Compare en temps constant ; lève une erreur claire si aucun mot de passe n'est configuré.

        Paramètre : candidate (mot de passe saisi). Retour : True si correct.
        Lève OwnerPasswordNotConfiguredError si FORMA3D_OWNER_PASSWORD est vide.
        """
        expected = (self._password_reader() or "").strip()
        if not expected:
            raise OwnerPasswordNotConfiguredError(
                f"Connexion impossible : la variable {OWNER_PASSWORD_ENV} n'est pas configurée sur le serveur."
            )
        # compare_digest : durée identique quel que soit le nombre de caractères corrects.
        # Avec « == », un attaquant pourrait deviner le mot de passe caractère par caractère en mesurant le temps.
        return hmac.compare_digest(candidate.encode("utf-8"), expected.encode("utf-8"))

    def _sign(self, payload: str) -> str:
        """Calcule la signature HMAC-SHA256 du texte avec la clé du serveur, encodée en base64 « URL ».

        Sans la clé, personne ne peut fabriquer une signature valide.
        """
        digest = hmac.new(self._signing_key, payload.encode("ascii"), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    def issue_token(self) -> str:
        """Fabrique le jeton de session « owner.<expiration>.<signature> » valable ttl_seconds."""
        expires_at = int(self._clock()) + self.ttl_seconds
        payload = f"owner.{expires_at}"
        return f"{payload}.{self._sign(payload)}"

    def validate_token(self, token: str | None) -> bool:
        """Accepte uniquement un jeton bien formé, signé par ce serveur et non expiré.

        Paramètre : token (valeur du cookie, ou None). Retour : True si la session est valide.
        Si quelqu'un modifie la date dans son cookie, la signature ne correspond plus : refus.
        """
        if not token or token.count(".") != 2:
            return False
        subject, expires_text, signature = token.split(".")
        if subject != "owner" or not expires_text.isdigit():
            return False
        if not hmac.compare_digest(signature, self._sign(f"{subject}.{expires_text}")):
            return False
        return int(expires_text) > int(self._clock())

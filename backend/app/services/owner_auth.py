# Rôle : vérifie le mot de passe unique de la propriétaire, signe les jetons de session et limite les tentatives.
# Exécution : créé au démarrage dans main.py ; utilisé par app/routers/auth.py et la dépendance require_owner.
"""Authentification mono-propriétaire du Studio (mot de passe unique, session signée HMAC)."""

# Les annotations de type restent du texte.
from __future__ import annotations

# base64 (standard) : transforme des octets en texte ASCII (ici la signature mise dans le cookie).
import base64
# hashlib (standard) : fonctions de hachage (SHA-256). Un hachage est à sens unique :
# on peut vérifier une valeur, pas la retrouver. Équivalent de java.security.MessageDigest.
import hashlib
# hmac (standard) : signature avec clé secrète (HMAC) et comparaison en temps constant.
# Ici : signe le jeton de session et compare les secrets sans fuite par le temps de réponse.
import hmac
# os : lecture des variables d'environnement.
import os
# secrets (standard) : hasard de qualité cryptographique (jamais le module random pour un secret).
import secrets
# threading (standard) : verrou (Lock) pour protéger des données partagées entre requêtes simultanées.
import threading
# time : horloges (time.time pour l'expiration, time.monotonic pour les tentatives).
import time
# collections (standard) : deque = file rapide aux deux bouts ; defaultdict = dictionnaire qui crée
# la valeur manquante. Ici : une file des dernières tentatives par adresse IP.
from collections import defaultdict, deque
# Callable : type d'une fonction passée en paramètre.
from typing import Callable

# Nom de la variable qui contient le mot de passe de la propriétaire.
OWNER_PASSWORD_ENV = "FORMA3D_OWNER_PASSWORD"
# Nom de la variable qui contient le secret de signature des sessions.
SESSION_SECRET_ENV = "FORMA3D_SESSION_SECRET"
# Longueur minimale de ce secret.
SESSION_SECRET_MIN_LENGTH = 32
# Nom du cookie de session.
SESSION_COOKIE_NAME = "forma3d_session"
# Durée d'une session : 8 heures en secondes.
SESSION_TTL_SECONDS = 8 * 60 * 60
# Nombre maximal de tentatives de connexion par minute et par adresse IP.
LOGIN_ATTEMPTS_PER_MINUTE = 5


# Erreur : aucun mot de passe configuré.
class OwnerPasswordNotConfiguredError(RuntimeError):
    """Levée quand FORMA3D_OWNER_PASSWORD est absente : toute connexion est refusée."""


# Erreur : trop de tentatives.
class LoginRateLimitedError(RuntimeError):
    """Levée quand une adresse IP dépasse le nombre de tentatives autorisées."""

    # Constructeur : reçoit le délai d'attente.
    def __init__(self, retry_after_seconds: int) -> None:
        """Mémorise dans l'erreur le nombre de secondes à attendre (renvoyé dans l'en-tête Retry-After)."""
        # Initialise l'exception avec un message fixe.
        super().__init__("Trop de tentatives de connexion.")
        # Garde le délai pour l'en-tête Retry-After.
        self.retry_after_seconds = retry_after_seconds


# Compteur de tentatives de connexion par adresse IP.
class LoginAttemptLimiter:
    """Compte les tentatives par IP sur une fenêtre glissante, uniquement en mémoire."""

    # Constructeur : maximum de tentatives, taille de la fenêtre...
    def __init__(self, max_attempts: int = LOGIN_ATTEMPTS_PER_MINUTE, window_seconds: float = 60.0,
                 # ...et horloge remplaçable.
                 clock: Callable[[], float] = time.monotonic) -> None:
        """Prépare le compteur : nombre maximal de tentatives, taille de la fenêtre en secondes, horloge.

        L'horloge est un paramètre pour que les tests puissent simuler le temps qui passe.
        """
        # Mémorise le maximum.
        self._max_attempts = max_attempts
        # Mémorise la taille de la fenêtre.
        self._window_seconds = window_seconds
        # Mémorise l'horloge.
        self._clock = clock
        # File des instants de tentative pour chaque IP (créée vide à la première demande).
        self._attempts: dict[str, deque[float]] = defaultdict(deque)
        # Verrou partagé entre les requêtes simultanées.
        self._lock = threading.Lock()

    # Enregistre une tentative.
    def register(self, client_ip: str) -> None:
        """Enregistre une tentative ou lève LoginRateLimitedError si la limite est atteinte.

        Fenêtre glissante : on retire d'abord les tentatives plus vieilles que 60 s, puis on compte.
        Paramètre : client_ip (adresse du client). Le verrou évite deux mises à jour simultanées.
        """
        # Instant présent.
        now = self._clock()
        # Prend le verrou...
        with self._lock:
            # ...file des tentatives de cette IP...
            attempts = self._attempts[client_ip]
            # ...tant que la plus ancienne est sortie de la fenêtre...
            while attempts and now - attempts[0] >= self._window_seconds:
                # ...on la retire.
                attempts.popleft()
            # Limite atteinte...
            if len(attempts) >= self._max_attempts:
                # ...secondes à attendre avant que la plus ancienne sorte de la fenêtre (au moins 1)...
                retry_after = max(1, int(self._window_seconds - (now - attempts[0])) + 1)
                # ...refus.
                raise LoginRateLimitedError(retry_after)
            # Sinon on enregistre la tentative.
            attempts.append(now)

    # Vide tous les compteurs.
    def reset(self) -> None:
        """Vide les compteurs (tests et redémarrage)."""
        # Prend le verrou...
        with self._lock:
            # ...efface tout.
            self._attempts.clear()


# Lit le secret de session ; reader est remplaçable par les tests.
def session_key_from_environment(reader: Callable[[str], str | None] = os.getenv) -> bytes | None:
    """Clé de signature fixe tirée de FORMA3D_SESSION_SECRET, ou None pour une clé aléatoire par processus.

    Remplie, elle garde la session ouverte après un redémarrage du serveur (toujours 8 h au plus).
    Un secret trop court est refusé au démarrage plutôt que d'affaiblir silencieusement les sessions.
    """
    # Lit la variable, ou chaîne vide.
    secret = (reader(SESSION_SECRET_ENV) or "").strip()
    # Pas de secret...
    if not secret:
        # ...None : une clé aléatoire sera utilisée.
        return None
    # Secret trop court...
    if len(secret) < SESSION_SECRET_MIN_LENGTH:
        # ...refusé au démarrage.
        raise ValueError(
            f"{SESSION_SECRET_ENV} doit contenir au moins {SESSION_SECRET_MIN_LENGTH} caractères "
            "(générez-le avec secrets.token_urlsafe(32)) ou rester vide."
        )
    # SHA-256 ramène n'importe quel secret assez long à une clé HMAC de 32 octets.
    # Renvoie la clé de 32 octets dérivée du secret.
    return hashlib.sha256(secret.encode("utf-8")).digest()


# Service d'authentification de la propriétaire.
class OwnerAuthService:
    """Vérifie le mot de passe et émet/valide des jetons « owner.<expiration>.<signature> »."""

    # Constructeur : clé de signature et durée de session...
    def __init__(self, signing_key: bytes | None = None, ttl_seconds: int = SESSION_TTL_SECONDS,
                 # ...horloge...
                 clock: Callable[[], float] = time.time,
                 # ...lecteur du mot de passe.
                 password_reader: Callable[[], str | None] | None = None) -> None:
        """Prépare le service : clé de signature, durée de session, horloge et lecteur du mot de passe.

        signing_key=None -> clé aléatoire (les sessions ne survivent pas à un redémarrage).
        Les paramètres clock et password_reader existent pour les tests.
        """
        # Sans clé fournie : clé aléatoire par processus, un redémarrage invalide les sessions ouvertes.
        # main.py fournit la clé de FORMA3D_SESSION_SECRET quand elle est configurée.
        # Clé fournie, ou 32 octets aléatoires.
        self._signing_key = signing_key or secrets.token_bytes(32)
        # Durée de validité d'une session.
        self.ttl_seconds = ttl_seconds
        # Mémorise l'horloge.
        self._clock = clock
        # Lecteur du mot de passe (par défaut : la variable d'environnement).
        self._password_reader = password_reader or (lambda: os.getenv(OWNER_PASSWORD_ENV))
        # Compteur de tentatives de connexion.
        self.limiter = LoginAttemptLimiter()

    # Le mot de passe est-il configuré ?
    def is_configured(self) -> bool:
        """Vrai si un mot de passe propriétaire non vide est défini dans l'environnement."""
        # Vrai si le mot de passe n'est pas vide.
        return bool((self._password_reader() or "").strip())

    # Vérifie le mot de passe saisi.
    def verify_password(self, candidate: str) -> bool:
        """Compare en temps constant ; lève une erreur claire si aucun mot de passe n'est configuré.

        Paramètre : candidate (mot de passe saisi). Retour : True si correct.
        Lève OwnerPasswordNotConfiguredError si FORMA3D_OWNER_PASSWORD est vide.
        """
        # Mot de passe attendu.
        expected = (self._password_reader() or "").strip()
        # Pas de mot de passe configuré...
        if not expected:
            # ...erreur claire.
            raise OwnerPasswordNotConfiguredError(
                f"Connexion impossible : la variable {OWNER_PASSWORD_ENV} n'est pas configurée sur le serveur."
            )
        # compare_digest : durée identique quel que soit le nombre de caractères corrects.
        # Avec « == », un attaquant pourrait deviner le mot de passe caractère par caractère en mesurant le temps.
        # Compare en temps constant les deux mots de passe encodés.
        return hmac.compare_digest(candidate.encode("utf-8"), expected.encode("utf-8"))

    # Signe un texte.
    def _sign(self, payload: str) -> str:
        """Calcule la signature HMAC-SHA256 du texte avec la clé du serveur, encodée en base64 « URL ».

        Sans la clé, personne ne peut fabriquer une signature valide.
        """
        # HMAC-SHA256 du texte avec la clé du serveur.
        digest = hmac.new(self._signing_key, payload.encode("ascii"), hashlib.sha256).digest()
        # Encode en base64 « URL », sans les « = » de fin.
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    # Crée un jeton de session.
    def issue_token(self) -> str:
        """Fabrique le jeton de session « owner.<expiration>.<signature> » valable ttl_seconds."""
        # Expiration : maintenant + durée de session.
        expires_at = int(self._clock()) + self.ttl_seconds
        # Texte signé : « owner.<expiration> ».
        payload = f"owner.{expires_at}"
        # Jeton complet : texte + « . » + signature.
        return f"{payload}.{self._sign(payload)}"

    # Vérifie un jeton de session.
    def validate_token(self, token: str | None) -> bool:
        """Accepte uniquement un jeton bien formé, signé par ce serveur et non expiré.

        Paramètre : token (valeur du cookie, ou None). Retour : True si la session est valide.
        Si quelqu'un modifie la date dans son cookie, la signature ne correspond plus : refus.
        """
        # Absent ou pas exactement deux points...
        if not token or token.count(".") != 2:
            # ...refus.
            return False
        # Découpe le jeton en trois morceaux.
        subject, expires_text, signature = token.split(".")
        # Sujet inattendu ou expiration qui n'est pas un nombre...
        if subject != "owner" or not expires_text.isdigit():
            # ...refus.
            return False
        # Signature différente de celle recalculée...
        if not hmac.compare_digest(signature, self._sign(f"{subject}.{expires_text}")):
            # ...refus.
            return False
        # Accepté seulement si l'expiration n'est pas passée.
        return int(expires_text) > int(self._clock())

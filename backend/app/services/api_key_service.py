# Rôle : crée, révoque et vérifie les clés destinées à l’API d’intégration.
# Exécution : les routes de gestion et la dépendance FastAPI délèguent ici la logique sensible.
"""Service de clés API : secret révélé une fois, empreinte SHA-256 persistée."""

# Les annotations de type restent du texte.
from __future__ import annotations

# hashlib (standard) : SHA-256 pour l'empreinte des clés (on ne stocke jamais la clé elle-même).
import hashlib
# hmac (standard) : compare_digest compare deux empreintes en temps constant.
import hmac
# secrets (standard) : génère la partie aléatoire de la clé avec un hasard cryptographique.
import secrets
# UTC et datetime : date de création de la clé et instant des quotas.
from datetime import UTC, datetime
# uuid (standard) : identifiants uniques aléatoires (UUID version 4), impossibles à deviner en pratique.
from uuid import uuid4

# Objet métier d'une clé (sans secret).
from app.models import APIKeyRecord
# Contrat du dépôt.
from app.repositories.base import GenerationRepository

# Début fixe de toute clé : on reconnaît une clé Forma3D au premier coup d'œil.
_KEY_PREFIX = "f3d_live_"
# Nombre de caractères aléatoires gardés dans le préfixe visible.
_PREFIX_RANDOM_LENGTH = 8
# Empreinte factice : sert à faire une comparaison « pour rien » quand aucune clé ne correspond,
# afin que le temps de réponse ne révèle pas si un préfixe existe.
# Empreinte SHA-256 d'un texte fixe, jamais égale à une vraie clé.
_DUMMY_FINGERPRINT = hashlib.sha256(b"forma3d-invalid-api-key").hexdigest()


# Erreur : nom de clé invalide.
class APIKeyValidationError(ValueError):
    """Erreur de nommage d’une clé API."""


# Service des clés API.
class APIKeyService:
    """Gère les secrets sans jamais les conserver ni les journaliser."""

    # Constructeur : reçoit le dépôt.
    def __init__(self, repository: GenerationRepository) -> None:
        """Reçoit le dépôt (injection par constructeur, comme un @Service Spring qui reçoit son @Repository)."""
        # Mémorise le dépôt.
        self._repository = repository

    # Crée une clé et renvoie (métadonnées, secret).
    def create(self, name: str) -> tuple[APIKeyRecord, str]:
        """Crée une clé aléatoire et retourne son secret une seule fois à l'appelant.

        Paramètre : name (nom choisi par la propriétaire, 1 à 80 caractères).
        Retour : (enregistrement sans secret, secret en clair). Lève APIKeyValidationError si le nom est invalide.
        Seuls le préfixe lisible et l'empreinte SHA-256 sont enregistrés en base.
        """
        # Retire les espaces autour du nom.
        clean_name = name.strip()
        # Nom vide...
        if not clean_name:
            # ...erreur.
            raise APIKeyValidationError("Donnez un nom à cette clé API.")
        # Nom trop long...
        if len(clean_name) > 80:
            # ...erreur.
            raise APIKeyValidationError("Le nom d’une clé API ne peut pas dépasser 80 caractères.")
        # token_urlsafe(32) : 32 octets aléatoires encodés en texte utilisable dans une URL ou un en-tête.
        # Secret complet : préfixe fixe + partie aléatoire.
        secret = _KEY_PREFIX + secrets.token_urlsafe(32)
        # Préfixe visible : « f3d_live_ » + 8 caractères aléatoires.
        prefix = secret[: len(_KEY_PREFIX) + _PREFIX_RANDOM_LENGTH]
        # Construit l'enregistrement à stocker...
        record = APIKeyRecord(
            # ...identifiant aléatoire...
            id=str(uuid4()),
            # ...nom nettoyé...
            name=clean_name,
            # ...préfixe visible...
            prefix=prefix,
            # ...empreinte du secret (jamais le secret)...
            fingerprint=self._fingerprint(secret),
            # ...date de création.
            created_at=datetime.now(UTC),
        )
        # Enregistre puis renvoie l'enregistrement et le secret (montré une seule fois).
        return self._repository.create_api_key(record), secret

    # Liste les clés.
    def list(self) -> list[APIKeyRecord]:
        """Retourne les métadonnées de gestion, sans valeur secrète."""
        # Délègue au dépôt.
        return self._repository.list_api_keys()

    # Révoque une clé.
    def revoke(self, key_id: str) -> APIKeyRecord | None:
        """Désactive une clé existante ; la révocation est persistante et idempotente."""
        # Délègue au dépôt (None si la clé est inconnue).
        return self._repository.revoke_api_key(key_id)

    # Supprime une clé révoquée.
    def delete_revoked(self, key_id: str) -> str:
        """Supprime définitivement une clé, uniquement si elle a déjà été révoquée."""
        # Délègue au dépôt (« deleted », « active » ou « not_found »).
        return self._repository.delete_revoked_api_key(key_id)

    # Consomme une requête dans la limite par minute.
    def consume_rate_limit(
        self, key: APIKeyRecord, limit_per_minute: int, now: datetime | None = None
    ) -> str | None:
        """Réserve une requête API pour cette clé dans la fenêtre d’une minute."""
        # Délègue au dépôt ; « now » par défaut = instant présent en UTC.
        return self._repository.consume_api_rate_limit(
            key.id, limit_per_minute, now or datetime.now(UTC)
        )

    # Consomme une création dans le quota du jour.
    def consume_daily_quota(
        self, key: APIKeyRecord, daily_limit: int, now: datetime | None = None
    ) -> str | None:
        """Réserve une création pour cette clé dans la journée UTC courante."""
        # Délègue au dépôt ; « now » par défaut = instant présent en UTC.
        return self._repository.consume_api_daily_quota(
            key.id, daily_limit, now or datetime.now(UTC)
        )

    # Vérifie la clé reçue dans l'en-tête X-API-Key.
    def authenticate(self, candidate: str | None) -> APIKeyRecord | None:
        """Vérifie une clé active avec comparaison d'empreintes à temps constant.

        Paramètre : candidate (valeur de l'en-tête X-API-Key, ou None).
        Retour : l'enregistrement de la clé acceptée, sinon None (absente, fausse ou révoquée).
        Le préfixe sert à retrouver vite les candidates ; l'empreinte complète décide.
        """
        # Clé reçue, ou chaîne vide.
        supplied = candidate or ""
        # Longueur du préfixe visible.
        prefix_length = len(_KEY_PREFIX) + _PREFIX_RANDOM_LENGTH
        # Préfixe extrait seulement si la clé commence par « f3d_live_ ».
        prefix = supplied[:prefix_length] if supplied.startswith(_KEY_PREFIX) else ""
        # Empreinte de la clé reçue.
        fingerprint = self._fingerprint(supplied)
        # Clés actives candidates partageant ce préfixe.
        matches = self._repository.find_api_keys_by_prefix(prefix) if prefix else []
        # Aucune candidate...
        if not matches:
            # Comparaison factice : même durée que pour une clé existante (pas de fuite d'information par le temps).
            hmac.compare_digest(fingerprint, _DUMMY_FINGERPRINT)
            # ...refus.
            return None
        # Clé acceptée (aucune pour l'instant).
        accepted: APIKeyRecord | None = None
        # Compare l'empreinte avec chaque candidate...
        for record in matches:
            # On ne sort pas de la boucle au premier succès : la durée reste la même dans tous les cas.
            is_match = hmac.compare_digest(fingerprint, record.fingerprint)
            # ...si elle correspond...
            if is_match:
                # ...on retient cette clé.
                accepted = record
        # Renvoie la clé acceptée ou None.
        return accepted

    # Méthode sans self : simple calcul.
    @staticmethod
    # Calcule l'empreinte d'un secret.
    def _fingerprint(secret: str) -> str:
        """Calcule l’empreinte persistée sans conserver la clé en clair."""
        # SHA-256 du texte encodé en UTF-8, rendu en hexadécimal.
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()

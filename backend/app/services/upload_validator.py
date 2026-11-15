# Rôle : contrôle le nom, le type déclaré, la signature et la taille d'une image.
# Exécution : la route POST /models l'appelle avant d'accepter une photo.
"""Validation bornée des photos envoyées au backend."""

# dataclasses (standard) : classe de données immuable pour le résultat de la validation.
from dataclasses import dataclass

MAX_UPLOAD_BYTES = 10 * 1024 * 1024

_FORMATS_BY_EXTENSION = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

# Signature = premiers octets réels du fichier. Renommer un fichier ne change pas sa signature :
# un AVIF renommé en .jpg est donc refusé (protection contre un contenu déguisé).
_SIGNATURES_BY_MEDIA_TYPE = {
    "image/jpeg": lambda content: content.startswith(b"\xff\xd8\xff"),
    "image/png": lambda content: content.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/webp": lambda content: (
        len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    ),
}


class UploadValidationError(ValueError):
    """Erreur de validation avec le code HTTP à renvoyer au client."""

    def __init__(self, detail: str, status_code: int = 415) -> None:
        """Garde le message et le code HTTP que la route devra renvoyer (415 par défaut)."""
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


@dataclass(frozen=True)
class ValidatedUpload:
    """Métadonnées sûres d'une image, sans conserver son contenu."""

    filename: str
    content_type: str
    size_bytes: int


class UploadValidator:
    """Vérifie les limites d'entrée du Sprint 1 avant tout traitement."""

    @staticmethod
    def validate(
        filename: str | None,
        content_type: str | None,
        content: bytes,
    ) -> ValidatedUpload:
        """Valide une photo par extension, MIME, signature et taille.

        Paramètres : filename, content_type (type annoncé par le navigateur), content (octets lus).
        Retour : ValidatedUpload (nom nettoyé, type, taille).
        Lève UploadValidationError : 400 (vide ou nom invalide), 413 (plus de 10 Mo), 415 (format refusé).
        """
        if not content:
            raise UploadValidationError(
                "Le fichier est vide.",
                status_code=400,
            )

        if len(content) > MAX_UPLOAD_BYTES:
            raise UploadValidationError(
                "La taille maximale autorisée est de 10 Mo.",
                status_code=413,
            )

        # On ne garde que le nom, sans dossier : un nom comme « ../../secret » ne peut pas viser un autre chemin.
        safe_filename = (filename or "").replace("\\", "/").rsplit("/", maxsplit=1)[-1]
        if not safe_filename or safe_filename in {".", ".."}:
            raise UploadValidationError(
                "Le nom du fichier est manquant ou invalide.",
                status_code=400,
            )

        extension = (
            safe_filename.rsplit(".", maxsplit=1)[-1].lower()
            if "." in safe_filename
            else ""
        )
        extension = f".{extension}" if extension else ""
        expected_type = _FORMATS_BY_EXTENSION.get(extension)
        if expected_type is None:
            raise UploadValidationError(
                "Format refusé. Utilisez un fichier JPG, PNG ou WebP.",
                status_code=415,
            )

        if content_type != expected_type:
            raise UploadValidationError(
                "Le type MIME ne correspond pas à l'extension du fichier.",
                status_code=415,
            )

        signature_matches = _SIGNATURES_BY_MEDIA_TYPE[expected_type](content)
        if not signature_matches:
            raise UploadValidationError(
                "Le contenu du fichier ne correspond pas à son format déclaré.",
                status_code=415,
            )

        return ValidatedUpload(
            filename=safe_filename,
            content_type=expected_type,
            size_bytes=len(content),
        )

# Rôle : contrôle le nom, le type déclaré, la signature et la taille d'une image.
# Exécution : la route POST /models l'appelle avant d'accepter une photo.
"""Validation bornée des photos envoyées au backend."""

# dataclasses (standard) : classe de données immuable pour le résultat de la validation.
from dataclasses import dataclass

# Taille maximale d'une photo : 10 Mo en octets.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

# Type MIME attendu pour chaque extension autorisée.
_FORMATS_BY_EXTENSION = {
    # JPG.
    ".jpg": "image/jpeg",
    # JPEG (autre écriture).
    ".jpeg": "image/jpeg",
    # PNG.
    ".png": "image/png",
    # WebP.
    ".webp": "image/webp",
}

# Signature = premiers octets réels du fichier. Renommer un fichier ne change pas sa signature :
# un AVIF renommé en .jpg est donc refusé (protection contre un contenu déguisé).
# Pour chaque type, une petite fonction qui vérifie les premiers octets.
_SIGNATURES_BY_MEDIA_TYPE = {
    # JPEG commence toujours par FF D8 FF.
    "image/jpeg": lambda content: content.startswith(b"\xff\xd8\xff"),
    # PNG commence toujours par cette suite de 8 octets.
    "image/png": lambda content: content.startswith(b"\x89PNG\r\n\x1a\n"),
    # WebP : au moins 12 octets...
    "image/webp": lambda content: (
        # ...« RIFF » au début et « WEBP » aux octets 8 à 11.
        len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
    ),
}


# Erreur de validation qui porte aussi le code HTTP à renvoyer.
class UploadValidationError(ValueError):
    """Erreur de validation avec le code HTTP à renvoyer au client."""

    # Constructeur : message et code HTTP (415 par défaut).
    def __init__(self, detail: str, status_code: int = 415) -> None:
        """Garde le message et le code HTTP que la route devra renvoyer (415 par défaut)."""
        # Initialise l'exception avec le message.
        super().__init__(detail)
        # Garde le message pour la route.
        self.detail = detail
        # Garde le code HTTP pour la route.
        self.status_code = status_code


# Décorateur : résultat immuable.
@dataclass(frozen=True)
# Résultat d'une validation réussie.
class ValidatedUpload:
    """Métadonnées sûres d'une image, sans conserver son contenu."""

    # Nom de fichier nettoyé.
    filename: str
    # Type MIME vérifié.
    content_type: str
    # Taille en octets.
    size_bytes: int


# Classe qui regroupe les règles de validation.
class UploadValidator:
    """Vérifie les limites d'entrée du Sprint 1 avant tout traitement."""

    # Méthode sans self : la validation n'a besoin d'aucun état.
    @staticmethod
    # Valide une photo...
    def validate(
        # ...nom fourni par le navigateur...
        filename: str | None,
        # ...type annoncé par le navigateur...
        content_type: str | None,
        # ...octets lus.
        content: bytes,
    ) -> ValidatedUpload:
        """Valide une photo par extension, MIME, signature et taille.

        Paramètres : filename, content_type (type annoncé par le navigateur), content (octets lus).
        Retour : ValidatedUpload (nom nettoyé, type, taille).
        Lève UploadValidationError : 400 (vide ou nom invalide), 413 (plus de 10 Mo), 415 (format refusé).
        """
        # Fichier vide...
        if not content:
            # ...erreur 400.
            raise UploadValidationError(
                "Le fichier est vide.",
                status_code=400,
            )

        # Plus de 10 Mo...
        if len(content) > MAX_UPLOAD_BYTES:
            # ...erreur 413.
            raise UploadValidationError(
                "La taille maximale autorisée est de 10 Mo.",
                status_code=413,
            )

        # On ne garde que le nom, sans dossier : un nom comme « ../../secret » ne peut pas viser un autre chemin.
        # Remplace « \ » par « / » puis garde seulement la dernière partie (le nom).
        safe_filename = (filename or "").replace("\\", "/").rsplit("/", maxsplit=1)[-1]
        # Nom vide, « . » ou « .. »...
        if not safe_filename or safe_filename in {".", ".."}:
            # ...erreur 400.
            raise UploadValidationError(
                "Le nom du fichier est manquant ou invalide.",
                status_code=400,
            )

        # Extension en minuscules...
        extension = (
            # ...texte après le dernier point...
            safe_filename.rsplit(".", maxsplit=1)[-1].lower()
            # ...seulement s'il y a un point...
            if "." in safe_filename
            # ...sinon vide.
            else ""
        )
        # Ajoute le point devant l'extension (« jpg » -> « .jpg »).
        extension = f".{extension}" if extension else ""
        # Type MIME attendu pour cette extension, ou None.
        expected_type = _FORMATS_BY_EXTENSION.get(extension)
        # Extension inconnue...
        if expected_type is None:
            # ...erreur 415.
            raise UploadValidationError(
                "Format refusé. Utilisez un fichier JPG, PNG ou WebP.",
                status_code=415,
            )

        # Type annoncé différent du type attendu...
        if content_type != expected_type:
            # ...erreur 415.
            raise UploadValidationError(
                "Le type MIME ne correspond pas à l'extension du fichier.",
                status_code=415,
            )

        # Appelle la fonction de signature du format attendu.
        signature_matches = _SIGNATURES_BY_MEDIA_TYPE[expected_type](content)
        # Les premiers octets ne correspondent pas...
        if not signature_matches:
            # ...erreur 415 (contenu déguisé).
            raise UploadValidationError(
                "Le contenu du fichier ne correspond pas à son format déclaré.",
                status_code=415,
            )

        # Tout est valide : on renvoie le résultat...
        return ValidatedUpload(
            # ...nom nettoyé...
            filename=safe_filename,
            # ...type vérifié...
            content_type=expected_type,
            # ...taille.
            size_bytes=len(content),
        )

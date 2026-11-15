# Rôle : prépare une copie carrée de la photo et signale les images petites ou floues.
# Exécution : GenerationService traite la copie juste avant l'appel au fournisseur.
"""Préparation locale et légère des photos avec Pillow."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Pillow (module PIL) : bibliothèque de traitement d'images (ouvrir, redimensionner, convertir).
# Ici : prépare une copie carrée de la photo, sans IA. Équivalent de BufferedImage/ImageIO en Java.
from PIL import Image, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError

_MINIMUM_SIDE = 512
_MARGIN_RATIO = 0.12
_BLUR_VARIANCE_THRESHOLD = 500.0
_CANVAS_COLOR = (241, 245, 249)


class ImagePreparationError(ValueError):
    """La source ne peut pas être décodée comme une image par Pillow."""


@dataclass(frozen=True, slots=True)
class ImagePreparationResult:
    """Chemin temporaire de l'image préparée et avertissement facultatif."""

    prepared_path: Path
    warning: str | None


class ImagePreparer:
    """Crée une composition carrée avec marges sans modifier la photo originale."""

    def prepare(self, source_path: Path, destination_path: Path) -> ImagePreparationResult:
        """Redresse, mesure, met au carré et enregistre une copie PNG locale.

        Paramètres : source_path (photo d'origine, jamais modifiée), destination_path (copie préparée).
        Retour : ImagePreparationResult (chemin + avertissement éventuel, non bloquant).
        Lève ImagePreparationError si l'image ne peut pas être décodée.
        """
        try:
            # Image.open n'ouvre que l'en-tête ; le bloc « with » garantit la fermeture du fichier.
            with Image.open(source_path) as opened:
                # exif_transpose : applique la rotation enregistrée par l'appareil photo (photo prise en portrait).
                image = ImageOps.exif_transpose(opened)
                image.load()
                original_width, original_height = image.size
                if original_width < 1 or original_height < 1:
                    raise ImagePreparationError("La photo n'a pas de dimensions valides.")
                sharpness = self._sharpness_variance(image)
                rgba = image.convert("RGBA")
                rgb = Image.new("RGB", rgba.size, _CANVAS_COLOR)
                rgb.paste(rgba, mask=rgba.getchannel("A"))
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as error:
            raise ImagePreparationError(
                "La photo n'a pas pu être décodée pour sa préparation locale."
            ) from error

        canvas_side = max(_MINIMUM_SIDE, original_width, original_height)
        content_side = max(1, round(canvas_side * (1 - _MARGIN_RATIO)))
        # contain : réduit ou agrandit en gardant les proportions ; LANCZOS = filtre de bonne qualité.
        contained = ImageOps.contain(
            rgb,
            (content_side, content_side),
            method=Image.Resampling.LANCZOS,
        )
        canvas = Image.new("RGB", (canvas_side, canvas_side), _CANVAS_COLOR)
        offset = ((canvas_side - contained.width) // 2, (canvas_side - contained.height) // 2)
        canvas.paste(contained, offset)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(destination_path, format="PNG", optimize=True)

        warnings: list[str] = []
        if min(original_width, original_height) < _MINIMUM_SIDE:
            warnings.append(
                "La photo est petite (un côté fait moins de 512 px) ; elle a été agrandie et centrée. "
                "Pour plus de détails, rapprochez-vous de l'objet."
            )
        if sharpness < _BLUR_VARIANCE_THRESHOLD:
            warnings.append(
                "La photo semble floue ou manque de détails. Reprenez-la avec une lumière douce "
                "et la mise au point sur l'objet."
            )
        return ImagePreparationResult(
            prepared_path=destination_path,
            warning=" ".join(warnings) if warnings else None,
        )

    @staticmethod
    def _sharpness_variance(image: Image.Image) -> float:
        """Estime les détails par la variance des contours, sans bloquer le traitement."""
        grayscale = image.convert("L")
        # Mesure du flou : on détecte les contours ; peu de variation = peu de détails = photo probablement floue.
        edges = grayscale.filter(ImageFilter.FIND_EDGES)
        return float(ImageStat.Stat(edges).var[0])

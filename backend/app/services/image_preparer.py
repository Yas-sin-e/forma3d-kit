# Rôle : prépare une copie carrée de la photo et signale les images petites ou floues.
# Exécution : GenerationService traite la copie juste avant l'appel au fournisseur.
"""Préparation locale et légère des photos avec Pillow."""

# Les annotations de type restent du texte.
from __future__ import annotations

# Classe de données immuable pour le résultat.
from dataclasses import dataclass
# Path : chemins de la photo d'origine et de la copie.
from pathlib import Path

# Pillow (module PIL) : bibliothèque de traitement d'images (ouvrir, redimensionner, convertir).
# Ici : prépare une copie carrée de la photo, sans IA. Équivalent de BufferedImage/ImageIO en Java.
from PIL import Image, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError

# Côté minimal de l'image préparée (512 px).
_MINIMUM_SIDE = 512
# Marge autour de l'objet : 12 % du côté.
_MARGIN_RATIO = 0.12
# En dessous de ce seuil, la photo est jugée floue.
_BLUR_VARIANCE_THRESHOLD = 500.0
# Couleur de fond (gris très clair) en rouge, vert, bleu.
_CANVAS_COLOR = (241, 245, 249)


# Erreur : la photo ne peut pas être décodée.
class ImagePreparationError(ValueError):
    """La source ne peut pas être décodée comme une image par Pillow."""


# Décorateur : résultat immuable.
@dataclass(frozen=True, slots=True)
# Résultat de la préparation.
class ImagePreparationResult:
    """Chemin temporaire de l'image préparée et avertissement facultatif."""

    # Chemin de la copie préparée.
    prepared_path: Path
    # Avertissement facultatif (None si tout va bien).
    warning: str | None


# Classe qui prépare la photo avant l'envoi au fournisseur.
class ImagePreparer:
    """Crée une composition carrée avec marges sans modifier la photo originale."""

    # Méthode principale : photo d'origine -> copie carrée.
    def prepare(self, source_path: Path, destination_path: Path) -> ImagePreparationResult:
        """Redresse, mesure, met au carré et enregistre une copie PNG locale.

        Paramètres : source_path (photo d'origine, jamais modifiée), destination_path (copie préparée).
        Retour : ImagePreparationResult (chemin + avertissement éventuel, non bloquant).
        Lève ImagePreparationError si l'image ne peut pas être décodée.
        """
        # Essaie de décoder la photo...
        try:
            # Image.open n'ouvre que l'en-tête ; le bloc « with » garantit la fermeture du fichier.
            with Image.open(source_path) as opened:
                # exif_transpose : applique la rotation enregistrée par l'appareil photo (photo prise en portrait).
                # ...applique la rotation EXIF...
                image = ImageOps.exif_transpose(opened)
                # ...charge réellement les pixels en mémoire...
                image.load()
                # ...lit largeur et hauteur...
                original_width, original_height = image.size
                # ...dimensions impossibles...
                if original_width < 1 or original_height < 1:
                    # ...erreur.
                    raise ImagePreparationError("La photo n'a pas de dimensions valides.")
                # Mesure la netteté de la photo.
                sharpness = self._sharpness_variance(image)
                # Convertit en RGBA (avec canal de transparence).
                rgba = image.convert("RGBA")
                # Crée un fond RGB de la même taille, de couleur claire.
                rgb = Image.new("RGB", rgba.size, _CANVAS_COLOR)
                # Colle l'image sur ce fond en utilisant la transparence comme masque.
                rgb.paste(rgba, mask=rgba.getchannel("A"))
        # Fichier illisible, format inconnu ou image anormalement énorme...
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as error:
            # ...erreur claire, cause conservée.
            raise ImagePreparationError(
                "La photo n'a pas pu être décodée pour sa préparation locale."
            ) from error

        # Côté du carré final : au moins 512 px, et au moins le plus grand côté de la photo.
        canvas_side = max(_MINIMUM_SIDE, original_width, original_height)
        # Côté réservé à l'objet : le carré moins les marges.
        content_side = max(1, round(canvas_side * (1 - _MARGIN_RATIO)))
        # contain : réduit ou agrandit en gardant les proportions ; LANCZOS = filtre de bonne qualité.
        # Redimensionne l'image pour qu'elle tienne dans ce côté...
        contained = ImageOps.contain(
            # ...image source...
            rgb,
            # ...taille maximale...
            (content_side, content_side),
            # ...filtre de bonne qualité.
            method=Image.Resampling.LANCZOS,
        )
        # Crée le carré final de couleur claire.
        canvas = Image.new("RGB", (canvas_side, canvas_side), _CANVAS_COLOR)
        # Décalage pour centrer l'image dans le carré.
        offset = ((canvas_side - contained.width) // 2, (canvas_side - contained.height) // 2)
        # Colle l'image centrée.
        canvas.paste(contained, offset)
        # Crée le dossier de destination si besoin.
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        # Enregistre la copie en PNG compressé.
        canvas.save(destination_path, format="PNG", optimize=True)

        # Liste des avertissements.
        warnings: list[str] = []
        # Si le plus petit côté fait moins de 512 px...
        if min(original_width, original_height) < _MINIMUM_SIDE:
            # ...on ajoute l'avertissement « photo petite ».
            warnings.append(
                "La photo est petite (un côté fait moins de 512 px) ; elle a été agrandie et centrée. "
                "Pour plus de détails, rapprochez-vous de l'objet."
            )
        # Si la netteté est sous le seuil...
        if sharpness < _BLUR_VARIANCE_THRESHOLD:
            # ...on ajoute l'avertissement « photo floue ».
            warnings.append(
                "La photo semble floue ou manque de détails. Reprenez-la avec une lumière douce "
                "et la mise au point sur l'objet."
            )
        # Renvoie le résultat...
        return ImagePreparationResult(
            # ...chemin de la copie...
            prepared_path=destination_path,
            # ...avertissements joints en un texte, ou None.
            warning=" ".join(warnings) if warnings else None,
        )

    # Méthode sans self : simple calcul.
    @staticmethod
    # Mesure de netteté.
    def _sharpness_variance(image: Image.Image) -> float:
        """Estime les détails par la variance des contours, sans bloquer le traitement."""
        # Convertit en niveaux de gris.
        grayscale = image.convert("L")
        # Mesure du flou : on détecte les contours ; peu de variation = peu de détails = photo probablement floue.
        # Fait ressortir les contours.
        edges = grayscale.filter(ImageFilter.FIND_EDGES)
        # Renvoie la variance des contours (grande = beaucoup de détails).
        return float(ImageStat.Stat(edges).var[0])

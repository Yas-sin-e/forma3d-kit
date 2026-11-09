# Rôle : vérifie le cadrage carré, le redimensionnement et les avertissements de photo.
# Exécution : Pytest exécute ces cas avec Pillow et des images créées localement.
"""Tests unitaires du préparateur de photos sans réseau ni modèle."""

from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFilter

from app.services.image_preparer import ImagePreparationError, ImagePreparer


def _save_sharp_photo(path: Path, size: tuple[int, int]) -> None:
    """Crée une image déterministe avec des contours nets pour les tests."""
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    for x in range(0, size[0], 16):
        draw.rectangle((x, 0, min(x + 7, size[0] - 1), size[1] - 1), fill="black")
    image.save(path, format="PNG")


def test_preparer_square_resizes_small_image_and_keeps_original(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    _save_sharp_photo(source, (256, 192))
    original_bytes = source.read_bytes()
    destination = tmp_path / "work" / "prepared.png"

    result = ImagePreparer().prepare(source, destination)

    with Image.open(destination) as prepared:
        assert prepared.size == (512, 512)
    assert source.read_bytes() == original_bytes
    assert "moins de 512 px" in (result.warning or "")


def test_preparer_warns_for_blurry_image_without_blocking(tmp_path: Path) -> None:
    source = tmp_path / "blurred.png"
    _save_sharp_photo(source, (640, 640))
    with Image.open(source) as image:
        blurred = image.filter(ImageFilter.GaussianBlur(radius=18))
    blurred.save(source)

    result = ImagePreparer().prepare(source, tmp_path / "prepared.png")

    assert result.prepared_path.is_file()
    assert "semble floue" in (result.warning or "")


def test_preparer_does_not_warn_for_detailed_large_image(tmp_path: Path) -> None:
    source = tmp_path / "sharp.png"
    _save_sharp_photo(source, (640, 640))

    result = ImagePreparer().prepare(source, tmp_path / "prepared.png")

    assert result.warning is None
    with Image.open(result.prepared_path) as prepared:
        assert prepared.size == (640, 640)


def test_preparer_rejects_undecodable_source(tmp_path: Path) -> None:
    source = tmp_path / "not-an-image.png"
    source.write_bytes(b"not an image")

    with pytest.raises(ImagePreparationError, match="n'a pas pu être décodée"):
        ImagePreparer().prepare(source, tmp_path / "prepared.png")

# Rôle : vérifie les formats, limites et réponses de la validation d'image.
# Exécution : Pytest lance ces tests automatiquement depuis le dossier backend.
"""Tests unitaires et HTTP pour l'étape d'envoi d'image."""

import pytest

from app.services.upload_validator import (
    MAX_UPLOAD_BYTES,
    UploadValidationError,
    UploadValidator,
)

_IMAGE_FIXTURES = [
    ("chair.jpg", "image/jpeg", b"\xff\xd8\xffsample"),
    ("chair.png", "image/png", b"\x89PNG\r\n\x1a\nsample"),
    ("chair.webp", "image/webp", b"RIFF\x04\x00\x00\x00WEBPsample"),
]


@pytest.mark.parametrize(("filename", "content_type", "content"), _IMAGE_FIXTURES)
def test_validator_accepts_supported_image_signatures(
    filename: str,
    content_type: str,
    content: bytes,
) -> None:
    result = UploadValidator.validate(filename, content_type, content)

    assert result.filename == filename
    assert result.content_type == content_type
    assert result.size_bytes == len(content)


def test_validator_removes_client_path_from_filename() -> None:
    result = UploadValidator.validate(
        r"C:\fakepath\chair.png",
        "image/png",
        b"\x89PNG\r\n\x1a\nsample",
    )

    assert result.filename == "chair.png"


def test_validator_rejects_an_empty_file() -> None:
    with pytest.raises(UploadValidationError) as error:
        UploadValidator.validate("chair.png", "image/png", b"")

    assert error.value.status_code == 400


def test_validator_rejects_an_unsupported_extension() -> None:
    with pytest.raises(UploadValidationError) as error:
        UploadValidator.validate("chair.gif", "image/gif", b"GIF89a")

    assert error.value.status_code == 415


def test_validator_rejects_a_mismatched_mime_type() -> None:
    with pytest.raises(UploadValidationError) as error:
        UploadValidator.validate("chair.png", "image/jpeg", b"\x89PNG\r\n\x1a\nsample")

    assert error.value.status_code == 415


def test_validator_rejects_a_mismatched_file_signature() -> None:
    with pytest.raises(UploadValidationError) as error:
        UploadValidator.validate("chair.png", "image/png", b"not-an-image")

    assert error.value.status_code == 415


def test_validator_rejects_files_larger_than_ten_megabytes() -> None:
    content = b"\x89PNG\r\n\x1a\n" + (b"x" * MAX_UPLOAD_BYTES)
    with pytest.raises(UploadValidationError) as error:
        UploadValidator.validate("chair.png", "image/png", content)

    assert error.value.status_code == 413

# Rôle : vérifie les écritures locales et la validation des identifiants.
# Exécution : Pytest lance ces tests depuis le dossier backend.
"""Tests du stockage local sans générer de modèle 3D."""

from pathlib import Path
from uuid import uuid4

import pytest

from app.storage.local_storage import LocalStorage


def test_storage_saves_image_with_server_generated_filename(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)
    generation_id = str(uuid4())
    content = b"\xff\xd8\xfflocal storage test payload"

    image_path = storage.save_image(generation_id, ".jpg", content)

    assert image_path == tmp_path / "images" / f"{generation_id}.jpg"
    assert image_path.read_bytes() == content


def test_storage_saves_and_reads_arbitrary_test_bytes_without_claiming_a_glb(
    tmp_path: Path,
) -> None:
    storage = LocalStorage(tmp_path)
    generation_id = str(uuid4())
    test_payload = b"unit test storage payload; not a 3D model"

    model_path = storage.save_model(generation_id, test_payload)

    assert model_path == tmp_path / "models" / f"{generation_id}.glb"
    assert model_path.read_bytes() == test_payload
    assert storage.get_model_path(generation_id) == model_path


def test_storage_returns_none_when_no_model_exists(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)

    assert storage.get_model_path(str(uuid4())) is None


def test_storage_rejects_path_traversal_and_unknown_image_extension(tmp_path: Path) -> None:
    storage = LocalStorage(tmp_path)

    with pytest.raises(ValueError, match="Identifiant de génération invalide"):
        storage.get_model_path("..\\outside")
    with pytest.raises(ValueError, match="Extension d'image non autorisée"):
        storage.save_image(str(uuid4()), ".gif", b"image bytes")

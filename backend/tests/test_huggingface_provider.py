# Rôle : vérifie le contrat du fournisseur sans appeler Hugging Face ni produire de GLB.
# Exécution : Pytest lance ces tests depuis le dossier backend.
"""Tests locaux du contrat et des garde-fous du fournisseur Hugging Face."""

from pathlib import Path

import pytest

from app.config import Settings, get_settings
from app.providers.huggingface import (
    HuggingFaceSpaceProvider,
    ProviderError,
)


def _observed_api_description() -> dict[str, object]:
    """Décrit la forme observée par view_api() ; aucun appel réseau n'est effectué."""
    return {
        "named_endpoints": {
            "/run_button": {
                "parameters": [
                    {
                        "parameter_name": "input_image",
                        "parameter_has_default": False,
                        "type": {"type": "image"},
                    },
                    {
                        "parameter_name": "foreground_ratio",
                        "parameter_has_default": True,
                        "parameter_default": 0.85,
                        "type": {"type": "number"},
                    },
                    {
                        "parameter_name": "remesh_option",
                        "parameter_has_default": True,
                        "parameter_default": "None",
                        "type": {"type": "enum", "enum": ["None", "Triangle", "Quad"]},
                    },
                    {
                        "parameter_name": "vertex_count",
                        "parameter_has_default": True,
                        "parameter_default": -1,
                        "type": {"type": "number"},
                    },
                    {
                        "parameter_name": "texture_size",
                        "parameter_has_default": True,
                        "parameter_default": 1024,
                        "type": {"type": "number"},
                    },
                ],
                "returns": [
                    {"label": "Preview Background Removal", "python_type": {"type": "filepath"}},
                    {"label": "3D Model", "python_type": {"type": "filepath"}},
                ],
            }
        }
    }


def test_api_contract_uses_the_observed_parameter_defaults_and_model_output() -> None:
    contract = HuggingFaceSpaceProvider._read_api_contract(_observed_api_description())

    assert contract == {
        "endpoint": "/run_button",
        "inputs": {
            "foreground_ratio": 0.85,
            "vertex_count": -1,
            "texture_size": 1024,
            "remesh_option": "None",
        },
        "model_output_index": 1,
        "output_count": 2,
    }


def test_api_contract_refuses_unexpected_parameter_names() -> None:
    description = _observed_api_description()
    parameters = description["named_endpoints"]["/run_button"]["parameters"]
    parameters[-1]["parameter_name"] = "unknown_texture_option"

    with pytest.raises(ProviderError, match="paramètres du Space ont changé"):
        HuggingFaceSpaceProvider._read_api_contract(description)


def test_api_contract_refuses_missing_glb_output() -> None:
    description = _observed_api_description()
    description["named_endpoints"]["/run_button"]["returns"][1]["label"] = "Other output"

    with pytest.raises(ProviderError, match="sortie fichier 3D"):
        HuggingFaceSpaceProvider._read_api_contract(description)


def test_model_output_path_selects_the_actual_file_and_requires_glb(tmp_path: Path) -> None:
    model_path = tmp_path / "generated.glb"
    model_path.write_bytes(b"glTF")

    assert HuggingFaceSpaceProvider._model_output_path(
        ["preview.png", {"path": str(model_path)}],
        1,
    ) == model_path

    wrong_format_path = tmp_path / "generated.obj"
    wrong_format_path.write_text("not a GLB", encoding="utf-8")
    with pytest.raises(ProviderError, match="fichier GLB local"):
        HuggingFaceSpaceProvider._model_output_path(
            ["preview.png", {"path": str(wrong_format_path)}],
            1,
        )


def test_glb_reader_checks_version_and_declared_length(tmp_path: Path) -> None:
    model_path = tmp_path / "header.glb"
    model_path.write_bytes(b"glTF" + (2).to_bytes(4, "little") + (12).to_bytes(4, "little"))

    assert HuggingFaceSpaceProvider._read_glb(model_path) == model_path.read_bytes()

    model_path.write_bytes(b"glTF" + (1).to_bytes(4, "little") + (12).to_bytes(4, "little"))
    with pytest.raises(ProviderError, match="incomplet ou incompatible"):
        HuggingFaceSpaceProvider._read_glb(model_path)


def test_settings_reads_backend_env_before_root_env(monkeypatch, tmp_path: Path) -> None:
    backend_folder = tmp_path / "backend"
    backend_folder.mkdir()
    (backend_folder / ".env").write_text(
        "HF_SPACE_ID=stabilityai/TripoSR\nHF_TOKEN=backend-test-token\n",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text(
        "HF_SPACE_ID=stabilityai/stable-fast-3d\nHF_TOKEN=root-test-token\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("app.config._PROJECT_ROOT", tmp_path)
    monkeypatch.delenv("HF_SPACE_ID", raising=False)
    monkeypatch.delenv("HF_TOKEN", raising=False)

    settings = get_settings()

    assert settings.hf_space_id == "stabilityai/TripoSR"
    assert settings.hf_token == "backend-test-token"


def test_settings_rejects_more_than_two_attempts() -> None:
    with pytest.raises(ValueError, match="égal à 1 ou 2"):
        Settings(hf_max_attempts=3)

# Rôle : vérifie le contrat du fournisseur sans appeler Hugging Face ni produire de GLB.
# Exécution : Pytest lance ces tests depuis le dossier backend.
"""Tests locaux du contrat et des garde-fous du fournisseur Hugging Face."""

from pathlib import Path
import json
import struct
from typing import Any

import pytest

from app.config import Settings, get_settings
from app.providers.huggingface import (
    HuggingFaceSpaceProvider,
    ProviderError,
)


def _observed_sf3d_api_description() -> dict[str, object]:
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


def _triposr_combined_api_description() -> dict[str, object]:
    """Décrit un endpoint de clic qui expose toute la chaîne et les trois sorties."""
    return {
        "named_endpoints": {
            "/submit": {
                "parameters": [
                    {
                        "parameter_name": "input_image",
                        "label": "Input Image",
                        "component": "Image",
                        "parameter_has_default": False,
                    },
                    {
                        "parameter_name": "do_remove_background",
                        "label": "Remove Background",
                        "component": "Checkbox",
                        "parameter_has_default": True,
                        "parameter_default": True,
                    },
                    {
                        "parameter_name": "foreground_ratio",
                        "label": "Foreground Ratio",
                        "component": "Slider",
                        "parameter_has_default": True,
                        "parameter_default": 0.85,
                    },
                    {
                        "parameter_name": "mc_resolution",
                        "label": "Marching Cubes Resolution",
                        "component": "Slider",
                        "parameter_has_default": True,
                        "parameter_default": 256,
                    },
                ],
                "returns": [
                    {
                        "label": "Processed Image",
                        "component": "Image",
                        "python_type": {"type": "filepath"},
                    },
                    {
                        "label": "Output Model (OBJ Format)",
                        "component": "Model3D",
                        "python_type": {"type": "filepath"},
                    },
                    {
                        "label": "Output Model (GLB Format)",
                        "component": "Model3D",
                        "python_type": {"type": "filepath"},
                    },
                ],
            },
            "/run_example": {
                "parameters": [
                    {
                        "parameter_name": "image_pil",
                        "label": "Image",
                        "component": "Image",
                        "parameter_has_default": False,
                    }
                ],
                "returns": [
                    {
                        "label": "Output Model (OBJ Format)",
                        "component": "Model3D",
                        "python_type": {"type": "filepath"},
                    },
                    {
                        "label": "Output Model (GLB Format)",
                        "component": "Model3D",
                        "python_type": {"type": "filepath"},
                    },
                ],
            },
        },
        "unnamed_endpoints": {},
    }


def _triposr_separate_api_description() -> dict[str, object]:
    """Reproduit les endpoints et examples_input observés sur le Space officiel."""
    return {
        "named_endpoints": {
            "/check_input_image": {
                "parameters": [
                    {
                        "parameter_name": "input_image",
                        "component": "Image",
                        "example_input": "https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png",
                    }
                ],
                "returns": [],
            },
            "/preprocess": {
                "parameters": [
                    {
                        "parameter_name": "input_image",
                        "component": "Image",
                        "example_input": "https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png",
                    },
                    {
                        "parameter_name": "do_remove_background",
                        "component": "Checkbox",
                        "example_input": True,
                    },
                    {
                        "parameter_name": "foreground_ratio",
                        "component": "Slider",
                        "example_input": 0.5,
                    },
                ],
                "returns": [
                    {
                        "label": "Processed Image",
                        "component": "Image",
                        "python_type": {"type": "filepath"},
                    }
                ],
            },
            "/generate": {
                "parameters": [
                    {
                        "parameter_name": "image",
                        "component": "Image",
                        "example_input": "https://raw.githubusercontent.com/gradio-app/gradio/main/test/test_files/bus.png",
                    },
                    {
                        "parameter_name": "mc_resolution",
                        "component": "Slider",
                        "example_input": 32,
                    },
                ],
                "returns": [
                    {
                        "label": "Output Model (OBJ Format)",
                        "component": "Model3D",
                        "python_type": {"type": "filepath"},
                    },
                    {
                        "label": "Output Model (GLB Format)",
                        "component": "Model3D",
                        "python_type": {"type": "filepath"},
                    },
                ],
            },
        },
        "unnamed_endpoints": {},
    }


def _triposr_gradio_config() -> dict[str, object]:
    """Valeurs de composants et liens de paramètres observés dans Client.config."""
    return {
        "dependencies": [
            {"api_name": "check_input_image", "inputs": [5]},
            {"api_name": "preprocess", "inputs": [5, 9, 10]},
            {"api_name": "generate", "inputs": [6, 11]},
        ],
        "components": [
            {"id": 5, "type": "image", "props": {"label": "Input Image"}},
            {"id": 6, "type": "image", "props": {"label": "Processed Image"}},
            {"id": 9, "type": "checkbox", "props": {"label": "Remove Background", "value": True}},
            {"id": 10, "type": "slider", "props": {"label": "Foreground Ratio", "value": 0.85}},
            {"id": 11, "type": "slider", "props": {"label": "Marching Cubes Resolution", "value": 256}},
        ],
    }


def _minimal_glb_20_bytes() -> bytes:
    """Construit uniquement une fixture de conteneur GLB pour tester son lecteur."""
    document = json.dumps({"asset": {"version": "2.0"}}, separators=(",", ":")).encode()
    document += b" " * (-len(document) % 4)
    chunk = struct.pack("<I4s", len(document), b"JSON") + document
    return struct.pack("<4sII", b"glTF", 2, 12 + len(chunk)) + chunk


class _CompletedJob:
    """Remplace Job.result dans les tests locaux sans contacter de serveur."""

    def __init__(self, result: Any) -> None:
        """Prépare le faux objet avec les valeurs voulues par le test."""
        self._result = result

    def result(self, timeout: float) -> Any:
        """Imite job.result() de gradio_client : renvoie la valeur prévue ou lève l'erreur prévue."""
        assert timeout > 0
        return self._result

    def cancel(self) -> None:
        """Imite job.cancel() ; ne fait rien dans le test."""
        return None


class _TemporaryDownloadDirectory:
    """Remplace le dossier temporaire système bloqué par le dossier de pytest."""

    def __init__(self, path: Path) -> None:
        """Prépare le faux objet avec les valeurs voulues par le test."""
        self.path = path

    def __enter__(self) -> str:
        """Permet d'utiliser le faux objet dans un bloc « with »."""
        return str(self.path)

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        """Fin du bloc « with » : rien à libérer pour ce faux objet."""
        return None


def test_api_contract_uses_the_observed_parameter_defaults_and_model_output() -> None:
    """Prouve que le contrat lu reprend les valeurs par défaut publiées et la bonne sortie GLB."""
    contract = HuggingFaceSpaceProvider._read_sf3d_api_contract(
        _observed_sf3d_api_description()
    )

    assert contract["strategy"] == "single"
    assert contract["selector"] == {"api_name": "/run_button"}
    assert contract["model_output_index"] == 1
    assert len(contract["inputs"]) == 5
    assert contract["inputs"][1:] == [0.85, "None", -1, 1024]


def test_api_contract_refuses_unexpected_parameter_names() -> None:
    """Prouve qu'un nom de paramètre inattendu arrête l'appel (on n'invente jamais un paramètre)."""
    description = _observed_sf3d_api_description()
    parameters = description["named_endpoints"]["/run_button"]["parameters"]
    parameters[-1]["parameter_name"] = "unknown_texture_option"

    with pytest.raises(ProviderError, match="paramètres de Stable Fast 3D ont changé"):
        HuggingFaceSpaceProvider._read_sf3d_api_contract(description)


def test_api_contract_refuses_missing_glb_output() -> None:
    """Prouve qu'un contrat sans sortie GLB est refusé."""
    description = _observed_sf3d_api_description()
    description["named_endpoints"]["/run_button"]["returns"][1]["label"] = "Other output"

    with pytest.raises(ProviderError, match="sortie fichier 3D"):
        HuggingFaceSpaceProvider._read_sf3d_api_contract(description)


def test_triposr_api_contract_selects_the_observed_generation_chain() -> None:
    """Prouve que le contrat TripoSR choisit l'enchaînement de fonctions réellement exposé."""
    contract = HuggingFaceSpaceProvider._read_triphosr_api_contract(
        _triposr_combined_api_description()
    )

    assert contract["strategy"] == "single"
    assert contract["selector"] == {"api_name": "/submit"}
    assert contract["model_output_index"] == 2
    assert contract["inputs"][1:] == [True, 0.85, 256]


def test_triposr_api_contract_finds_separate_functions_without_guessing_indexes() -> None:
    """Prouve que les fonctions séparées sont trouvées par leur nom, sans deviner de position."""
    contract = HuggingFaceSpaceProvider._read_triphosr_api_contract(
        _triposr_separate_api_description(),
        _triposr_gradio_config(),
    )

    assert contract["strategy"] == "separate"
    assert contract["check_step"]["selector"] == {"api_name": "/check_input_image"}
    assert contract["preprocess_step"]["selector"] == {"api_name": "/preprocess"}
    assert contract["generate_step"]["selector"] == {"api_name": "/generate"}
    assert contract["model_output_index"] == 1


def test_triposr_contract_uses_component_values_instead_of_examples() -> None:
    """Prouve que les valeurs par défaut viennent des composants de l'interface, pas des exemples."""
    description = _triposr_separate_api_description()

    with pytest.raises(ProviderError, match="Client.config"):
        HuggingFaceSpaceProvider._read_triphosr_api_contract(description)

    contract = HuggingFaceSpaceProvider._read_triphosr_api_contract(
        description,
        _triposr_gradio_config(),
    )

    assert contract["preprocess_step"]["inputs"][1:] == [True, 0.85]
    assert contract["generate_step"]["inputs"][1:] == [256]


def test_triposr_settings_use_only_bounds_published_by_api_metadata() -> None:
    """Prouve que les réglages TripoSR respectent les bornes publiées par l'API."""
    client_config = {
        "dependencies": [{"api_name": "submit", "inputs": [5, 9, 10, 11]}],
        "components": [
            {"id": 9, "type": "checkbox", "props": {"value": True}},
            {"id": 10, "type": "slider", "props": {"minimum": 0.2, "maximum": 1.0}},
            {"id": 11, "type": "slider", "props": {"minimum": 32, "maximum": 512}},
        ],
    }
    contract = HuggingFaceSpaceProvider._read_triphosr_api_contract(
        _triposr_combined_api_description(),
        client_config,
        foreground_ratio=0.9,
        mc_resolution=512,
    )

    assert contract["inputs"][1:] == [True, 0.9, 512]


def test_triposr_settings_refuse_values_outside_discovered_bounds() -> None:
    """Prouve qu'un réglage hors des bornes publiées est refusé."""
    client_config = {
        "dependencies": [{"api_name": "submit", "inputs": [5, 9, 10, 11]}],
        "components": [
            {"id": 9, "type": "checkbox", "props": {"value": True}},
            {"id": 10, "type": "slider", "props": {"minimum": 0.2, "maximum": 1.0}},
            {"id": 11, "type": "slider", "props": {"minimum": 32, "maximum": 512}},
        ],
    }

    with pytest.raises(ProviderError, match="hors des bornes publiées par l'API"):
        HuggingFaceSpaceProvider._read_triphosr_api_contract(
            _triposr_combined_api_description(),
            client_config,
            foreground_ratio=1.1,
        )


def test_triposr_settings_refuse_to_guess_missing_bounds() -> None:
    """Prouve qu'un réglage sans bornes publiées est refusé plutôt que deviné."""
    with pytest.raises(ProviderError, match="ne publie pas les bornes de foreground_ratio"):
        HuggingFaceSpaceProvider._read_triphosr_api_contract(
            _triposr_combined_api_description(),
            foreground_ratio=0.9,
        )


def test_public_provider_health_uses_a_five_second_timeout_and_hides_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prouve que le contrôle de santé attend au plus 5 s et ne révèle aucun détail d'erreur."""
    observations: dict[str, Any] = {}

    def fail_request(url: str, **kwargs: Any) -> Any:
        """Simule une panne réseau pendant le contrôle de santé."""
        observations["timeout"] = kwargs.get("timeout")
        observations["url"] = url
        raise TimeoutError("failed to reach https://secret-demo.gradio.live/config")

    monkeypatch.setattr("app.providers.huggingface.httpx2.get", fail_request)
    provider = HuggingFaceSpaceProvider(
        settings=Settings(hf_space_id="https://secret-demo.gradio.live")
    )

    assert provider.health_status() == "OFFLINE"
    assert observations["timeout"] == 5.0
    assert "secret-demo.gradio.live" not in provider.health_status()


def test_provider_uses_url_view_api_and_does_not_send_hf_token_to_gradio_share(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prouve que le jeton HF n'est jamais envoyé à une adresse Gradio publique."""
    input_path = tmp_path / "furniture.png"
    input_path.write_bytes(b"image test")
    glb_path = tmp_path / "generated.glb"
    glb_path.write_bytes(_minimal_glb_20_bytes())
    observations: dict[str, Any] = {}

    class FakeClient:
        """Faux client Gradio : enregistre les appels et renvoie des réponses prévues, sans réseau."""
        def view_api(self, **kwargs: Any) -> dict[str, object]:
            """Imite view_api() : renvoie le contrat d'API prévu par le test."""
            observations["view_api"] = kwargs
            return _triposr_combined_api_description()

        def submit(self, *args: Any, **kwargs: Any) -> _CompletedJob:
            """Imite submit() : enregistre l'appel et renvoie un faux travail."""
            observations["submit_args"] = args
            observations["submit_kwargs"] = kwargs
            return _CompletedJob(["processed.png", "model.obj", {"path": str(glb_path)}])

    def fake_client_factory(src: str, **kwargs: Any) -> FakeClient:
        """Fabrique de faux client Gradio : remplace la vraie connexion réseau."""
        observations["src"] = src
        observations["client_kwargs"] = kwargs
        return FakeClient()

    provider = HuggingFaceSpaceProvider(
        settings=Settings(
            hf_space_id="https://my-tripodemo.gradio.live",
            hf_token="private-test-token",
            hf_timeout_seconds=20,
            hf_max_attempts=1,
        ),
        client_factory=fake_client_factory,
    )
    monkeypatch.setattr(
        "app.providers.huggingface.TemporaryDirectory",
        lambda **kwargs: _TemporaryDownloadDirectory(tmp_path),
    )

    result = provider.generate(input_path)

    assert result == _minimal_glb_20_bytes()
    assert observations["src"] == "https://my-tripodemo.gradio.live"
    assert observations["client_kwargs"]["token"] is False
    assert "httpx_kwargs" not in observations["client_kwargs"]
    assert observations["view_api"] == {
        "print_info": False,
        "return_format": "dict",
    }
    assert observations["submit_kwargs"] == {"api_name": "/submit"}
    assert observations["submit_args"][1:] == (True, 0.85, 256)


def test_provider_executes_separate_triposr_steps_in_source_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prouve que les étapes TripoSR séparées sont appelées dans l'ordre de la source."""
    input_path = tmp_path / "furniture.png"
    input_path.write_bytes(b"image test")
    processed_path = tmp_path / "processed.png"
    processed_path.write_bytes(b"processed test image")
    glb_path = tmp_path / "generated.glb"
    glb_path.write_bytes(_minimal_glb_20_bytes())
    calls: list[str] = []

    class FakeClient:
        """Faux client Gradio : enregistre les appels et renvoie des réponses prévues, sans réseau."""
        config = _triposr_gradio_config()

        def view_api(self, **kwargs: Any) -> dict[str, object]:
            """Imite view_api() : renvoie le contrat d'API prévu par le test."""
            return _triposr_separate_api_description()

        def submit(self, *args: Any, **kwargs: Any) -> _CompletedJob:
            """Imite submit() : enregistre l'appel et renvoie un faux travail."""
            endpoint = kwargs["api_name"]
            calls.append(endpoint)
            if endpoint == "/preprocess":
                return _CompletedJob({"path": str(processed_path)})
            if endpoint == "/generate":
                return _CompletedJob(["model.obj", {"path": str(glb_path)}])
            return _CompletedJob(None)

    provider = HuggingFaceSpaceProvider(
        settings=Settings(
            hf_space_id="https://my-tripodemo.gradio.live",
            hf_timeout_seconds=20,
            hf_max_attempts=1,
        ),
        client_factory=lambda src, **kwargs: FakeClient(),
    )
    monkeypatch.setattr(
        "app.providers.huggingface.TemporaryDirectory",
        lambda **kwargs: _TemporaryDownloadDirectory(tmp_path),
    )

    result = provider.generate(input_path)

    assert result == _minimal_glb_20_bytes()
    assert calls == ["/check_input_image", "/preprocess", "/generate"]


def test_model_output_path_selects_the_actual_file_and_requires_glb(tmp_path: Path) -> None:
    """Prouve que la sortie retenue est un vrai fichier local au format .glb."""
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
    """Prouve que la lecture du GLB vérifie la version 2 et la longueur déclarée."""
    model_path = tmp_path / "header.glb"
    valid_glb = _minimal_glb_20_bytes()
    model_path.write_bytes(valid_glb)

    assert HuggingFaceSpaceProvider._read_glb(model_path) == valid_glb

    invalid_version = bytearray(valid_glb)
    invalid_version[4:8] = (1).to_bytes(4, "little")
    model_path.write_bytes(invalid_version)
    with pytest.raises(ProviderError, match="incomplet ou incompatible"):
        HuggingFaceSpaceProvider._read_glb(model_path)

    invalid_json = bytearray(valid_glb)
    json_length = int.from_bytes(valid_glb[12:16], "little")
    invalid_json[20 : 20 + json_length] = b"x" * json_length
    model_path.write_bytes(invalid_json)
    with pytest.raises(ProviderError, match="chunk JSON"):
        HuggingFaceSpaceProvider._read_glb(model_path)


def test_settings_reads_backend_env_before_root_env(monkeypatch, tmp_path: Path) -> None:
    """Prouve que backend/.env est lu avant le .env racine."""
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
    monkeypatch.delenv("FOREGROUND_RATIO", raising=False)
    monkeypatch.delenv("MC_RESOLUTION", raising=False)
    monkeypatch.delenv("PYTHON_DOTENV_DISABLED", raising=False)

    settings = get_settings()

    assert settings.hf_space_id == "stabilityai/TripoSR"
    assert settings.hf_token == "backend-test-token"


def test_settings_reads_optional_triposr_quality_values(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Prouve la lecture des réglages TripoSR facultatifs."""
    monkeypatch.setattr("app.config._PROJECT_ROOT", tmp_path)
    monkeypatch.setenv("HF_SPACE_ID", "https://triposr.example.gradio.live")
    monkeypatch.setenv("FOREGROUND_RATIO", "0.9")
    monkeypatch.setenv("MC_RESOLUTION", "320")

    settings = get_settings()

    assert settings.foreground_ratio == 0.9
    assert settings.mc_resolution == 320


def test_settings_accepts_a_public_gradio_url_without_credentials_or_query() -> None:
    """Prouve qu'une adresse Gradio publique simple est acceptée."""
    settings = Settings(hf_space_id="https://my-tripodemo.gradio.live/")

    assert settings.hf_space_id == "https://my-tripodemo.gradio.live/"


@pytest.mark.parametrize(
    "target",
    [
        "https://user:password@demo.gradio.live",
        "https://demo.gradio.live/?token=secret",
        "ftp://demo.gradio.live",
    ],
)
def test_settings_rejects_unsafe_or_unsupported_urls(target: str) -> None:
    """Prouve qu'une adresse dangereuse (identifiants, paramètres, autre protocole) est refusée."""
    with pytest.raises(ValueError, match="URL HTTP"):
        Settings(hf_space_id=target)


def test_settings_rejects_more_than_two_attempts() -> None:
    """Prouve qu'on ne peut pas configurer plus de deux tentatives."""
    with pytest.raises(ValueError, match="égal à 1 ou 2"):
        Settings(hf_max_attempts=3)

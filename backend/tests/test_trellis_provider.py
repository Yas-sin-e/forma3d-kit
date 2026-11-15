# Rôle : vérifie le fournisseur TRELLIS (enchaînement, contrat, erreurs, jeton) et sa configuration, sans réseau.
# Exécution : pytest ; un faux client Gradio remplace le Space et renvoie un GLB minimal construit en mémoire.
"""Tests de app/providers/trellis.py et de la sélection IMAGE3D_PROVIDER."""

import json
import struct
from pathlib import Path

import pytest

from app.config import Settings
from app.providers.base import ProviderError
from app.providers.trellis import GENERATION_SETTINGS, TrellisSpaceProvider, output_file_path
from app.services.glb_finisher import finish_glb
from test_glb_finisher import _parse, _raw_triangle_glb

ENDPOINTS = {"/start_session": {}, "/preprocess_image": {}, "/generate_and_extract_glb": {}}


class _Job:
    def __init__(self, value=None, error=None):
        self._value, self._error = value, error

    def result(self, timeout=None):
        if self._error:
            raise self._error
        return self._value

    def cancel(self):
        pass


class FakeClient:
    """Imite gradio_client.Client : enregistre les appels et renvoie des fichiers locaux."""

    instances: list["FakeClient"] = []

    def __init__(self, src, token=None, endpoints=ENDPOINTS, glb: bytes | None = None, fail_with=None, **kwargs):
        self.src, self.token, self.kwargs = src, token, kwargs
        self.endpoints, self.fail_with, self.calls = endpoints, fail_with, []
        self.glb = glb if glb is not None else _raw_triangle_glb()
        FakeClient.instances.append(self)

    def view_api(self, print_info=False, return_format="dict"):
        return {"named_endpoints": self.endpoints}

    def submit(self, api_name, **kwargs):
        self.calls.append((api_name, kwargs))
        if self.fail_with and api_name == "/generate_and_extract_glb":
            return _Job(error=self.fail_with)
        folder = Path(self.kwargs["download_files"])
        if api_name == "/preprocess_image":
            prepared = folder / "prepared.png"
            prepared.write_bytes(b"\x89PNG fake")
            return _Job({"path": str(prepared)})
        if api_name == "/generate_and_extract_glb":
            glb = folder / "model.glb"
            glb.write_bytes(self.glb)
            return _Job(({"video": "x.mp4"}, str(glb), str(glb)))
        return _Job(None)


def _provider(tmp_path: Path, token=None, **client_options) -> tuple[TrellisSpaceProvider, Path]:
    FakeClient.instances.clear()
    photo = tmp_path / "chair.jpg"
    photo.write_bytes(b"\xff\xd8\xffphoto")
    settings = Settings(hf_token=token, image3d_provider="trellis")
    provider = TrellisSpaceProvider(settings, client_factory=lambda src, **kw: FakeClient(src, **{**kw, **client_options}))
    return provider, photo


def test_generate_follows_the_observed_trellis_sequence_and_returns_glb(tmp_path: Path) -> None:
    provider, photo = _provider(tmp_path)
    data = provider.generate(photo)

    client = FakeClient.instances[0]
    assert client.src == "trellis-community/TRELLIS"
    assert [name for name, _ in client.calls] == ["/start_session", "/preprocess_image", "/generate_and_extract_glb"]
    generation_kwargs = client.calls[2][1]
    assert generation_kwargs["image"]["path"].endswith("prepared.png")  # l'image détourée, pas la photo brute
    for key, value in GENERATION_SETTINGS.items():
        assert generation_kwargs[key] == value
    assert data[:4] == b"glTF"


def test_client_uses_a_long_http_timeout_for_a_slow_free_space(tmp_path: Path) -> None:
    """Le délai httpx par défaut (5 s) provoquait un ReadTimeout quand le Space était chargé."""
    provider, photo = _provider(tmp_path)
    provider.generate(photo)

    assert FakeClient.instances[0].kwargs["httpx_kwargs"] == {"timeout": 120.0}


def test_contract_change_stops_before_sending_the_photo(tmp_path: Path) -> None:
    provider, photo = _provider(tmp_path, endpoints={"/start_session": {}})
    with pytest.raises(ProviderError, match="contrat du Space TRELLIS a changé"):
        provider.generate(photo)
    assert FakeClient.instances[0].calls == []


def test_quota_error_is_explained_without_leaking_the_token(tmp_path: Path) -> None:
    secret = "hf_secret_de_test_123"
    provider, photo = _provider(tmp_path, token=secret, fail_with=RuntimeError(f"ZeroGPU quota exceeded for {secret}"))
    with pytest.raises(ProviderError) as error:
        provider.generate(photo)
    assert "Quota GPU gratuit" in str(error.value)
    assert secret not in str(error.value)
    assert FakeClient.instances[0].token == secret  # envoyé au seul identifiant de Space Hugging Face


def test_invalid_glb_from_space_is_refused(tmp_path: Path) -> None:
    provider, photo = _provider(tmp_path, glb=b"pas un glb")
    with pytest.raises(ProviderError):
        provider.generate(photo)


def test_missing_photo_is_refused(tmp_path: Path) -> None:
    provider, _ = _provider(tmp_path)
    with pytest.raises(ProviderError, match="introuvable"):
        provider.generate(tmp_path / "absente.jpg")


def test_output_file_path_shapes() -> None:
    assert output_file_path("C:/a.glb") == Path("C:/a.glb")
    assert output_file_path({"path": "/b.glb"}) == Path("/b.glb")
    assert output_file_path({"path": None}) is None
    assert output_file_path(None) is None


def test_settings_validate_provider_choice_and_space_identifier() -> None:
    assert Settings().image3d_provider == "triposr"
    assert Settings(image3d_provider="trellis").trellis_space_id == "trellis-community/TRELLIS"
    with pytest.raises(ValueError, match="IMAGE3D_PROVIDER"):
        Settings(image3d_provider="meshy")
    with pytest.raises(ValueError, match="TRELLIS_SPACE_ID"):
        Settings(trellis_space_id="https://example.com/space")


def test_finisher_sets_metallic_zero_for_textured_material_without_factor() -> None:
    """Cas TRELLIS : matériau texturé sans metallicFactor (donc métal par défaut selon glTF)."""
    raw = _raw_triangle_glb(with_material=True, with_normals=True)
    document, binary = _parse(raw)
    document["materials"] = [{"pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "roughnessFactor": 1.0}}]
    json_bytes = json.dumps(document).encode()
    json_bytes += b" " * (-len(json_bytes) % 4)
    rebuilt = (b"glTF" + struct.pack("<II", 2, 12 + 8 + len(json_bytes) + 8 + len(binary))
               + struct.pack("<II", len(json_bytes), 0x4E4F534A) + json_bytes
               + struct.pack("<II", len(binary), 0x004E4942) + binary)

    finished, report = finish_glb(rebuilt)
    assert report.changed and report.metallic_fixed == 1
    assert _parse(finished)[0]["materials"][0]["pbrMetallicRoughness"]["metallicFactor"] == 0.0


def test_health_route_explains_trellis_offline_without_colab_wording(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    offline = TrellisSpaceProvider(Settings(image3d_provider="trellis"))
    monkeypatch.setattr(offline, "health_status", lambda: "OFFLINE")
    monkeypatch.setattr(app.state, "generation_provider", offline)
    body = TestClient(app).get("/health/provider").json()
    assert body["status"] == "OFFLINE"
    assert "TRELLIS" in body["message"] and "Colab" not in body["message"]

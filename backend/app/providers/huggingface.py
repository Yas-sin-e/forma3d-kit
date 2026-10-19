# Rôle : adapte l'API réelle du Space Stable Fast 3D au contrat Image3DProvider.
# Exécution : appelé par le service de génération ; le client distant n'est créé qu'à ce moment.
"""Fournisseur image-vers-3D utilisant un Space public Hugging Face."""

from __future__ import annotations

import time
from concurrent.futures import TimeoutError as JobTimeoutError
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable
from urllib.parse import quote

import httpx2
from gradio_client import Client, handle_file

from app.config import Settings, get_settings
from app.providers.base import ProviderError

_ENDPOINT = "/run_button"
_PARAMETER_NAMES = {
    "input_image",
    "foreground_ratio",
    "remesh_option",
    "vertex_count",
    "texture_size",
}
_BUILDING_STAGES = {
    "BUILDING",
    "RUNNING_BUILDING",
    "APP_STARTING",
    "RUNNING_APP_STARTING",
}
_PAUSED_STAGES = {"PAUSED", "SLEEPING", "STOPPED"}


class HuggingFaceSpaceProvider:
    """Appelle le Space après inspection de son API, puis vérifie le GLB reçu."""

    def __init__(
        self,
        settings: Settings | None = None,
        client_factory: Callable[..., Any] = Client,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.settings = settings or get_settings()
        self._client_factory = client_factory
        self._sleep = sleep

    def generate(self, image_path: Path) -> bytes:
        """Envoie une image au Space et retourne seulement un GLB vérifié."""
        source = Path(image_path)
        if not source.is_file():
            raise ProviderError("La photo à convertir est introuvable sur le serveur.")

        deadline = time.monotonic() + self.settings.hf_timeout_seconds
        last_error: Exception | None = None
        for attempt in range(1, self.settings.hf_max_attempts + 1):
            try:
                self._wait_for_space(deadline)
                return self._generate_once(source, deadline)
            except ProviderError:
                raise
            except JobTimeoutError as error:
                raise ProviderError(
                    f"La génération Hugging Face a dépassé "
                    f"{self.settings.hf_timeout_seconds} secondes."
                ) from error
            except Exception as error:
                last_error = error
                if attempt >= self.settings.hf_max_attempts or not self._is_retryable(error):
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self._sleep(min(self.settings.hf_retry_delay_seconds, remaining))

        message = str(last_error)
        if self.settings.hf_token:
            message = message.replace(self.settings.hf_token, "[jeton masqué]")
        raise ProviderError(
            f"Le Space Hugging Face {self.settings.hf_space_id} est indisponible "
            f"ou a refusé la génération : {message}"
        ) from last_error

    def _wait_for_space(self, deadline: float) -> None:
        """Attend seulement les états de démarrage, avec un délai maximal."""
        runtime_url = (
            "https://huggingface.co/api/spaces/"
            f"{quote(self.settings.hf_space_id, safe='/')}/runtime"
        )
        headers = {}
        if self.settings.hf_token:
            headers["Authorization"] = f"Bearer {self.settings.hf_token}"

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProviderError("Délai maximal atteint en attendant le Space Hugging Face.")
            response = httpx2.get(
                runtime_url,
                headers=headers,
                timeout=min(10.0, remaining),
            )
            response.raise_for_status()
            stage = response.json().get("stage")
            if stage == "RUNNING":
                return
            if stage in _PAUSED_STAGES:
                # Le client Gradio déclenche la reprise lorsqu'il contacte l'application.
                return
            if stage not in _BUILDING_STAGES:
                raise ProviderError(
                    f"Le Space Hugging Face est dans l'état {stage!r} ; "
                    "aucune génération n'a été lancée."
                )
            self._sleep(min(self.settings.hf_retry_delay_seconds, remaining))

    def _generate_once(self, image_path: Path, deadline: float) -> bytes:
        """Découvre le contrat courant, soumet l'image et lit la sortie .glb."""
        with TemporaryDirectory(prefix="forma3d-hf-") as download_dir:
            client = self._client_factory(
                self.settings.hf_space_id,
                token=self.settings.hf_token if self.settings.hf_token else False,
                verbose=False,
                analytics_enabled=False,
                download_files=download_dir,
                httpx_kwargs={"timeout": max(1.0, deadline - time.monotonic())},
            )
            api_description = client.view_api(
                print_info=False,
                return_format="dict",
            )
            contract = self._read_api_contract(api_description)
            job = client.submit(
                input_image=handle_file(str(image_path)),
                **contract["inputs"],
                api_name=contract["endpoint"],
            )
            try:
                result = job.result(timeout=max(0.01, deadline - time.monotonic()))
            except JobTimeoutError:
                job.cancel()
                raise
            model_path = self._model_output_path(
                result,
                contract["model_output_index"],
            )
            return self._read_glb(model_path)

    @staticmethod
    def _read_api_contract(api_description: Any) -> dict[str, Any]:
        """Valide les noms, défauts et sorties réellement découverts par view_api()."""
        if not isinstance(api_description, dict):
            raise ProviderError("view_api() n'a pas renvoyé une description exploitable.")
        endpoints = api_description.get("named_endpoints")
        endpoint = endpoints.get(_ENDPOINT) if isinstance(endpoints, dict) else None
        if not isinstance(endpoint, dict):
            raise ProviderError(
                f"Le Space ne publie plus {_ENDPOINT} ; son API doit être inspectée."
            )

        parameters = endpoint.get("parameters")
        if not isinstance(parameters, list):
            raise ProviderError("view_api() ne décrit pas les paramètres du bouton de génération.")
        by_name = {
            parameter.get("parameter_name"): parameter
            for parameter in parameters
            if isinstance(parameter, dict)
        }
        if set(by_name) != _PARAMETER_NAMES:
            raise ProviderError(
                "Les paramètres du Space ont changé ; vérifiez view_api() avant de l'utiliser."
            )

        remesh_type = by_name["remesh_option"].get("type", {})
        remesh_options = remesh_type.get("enum", []) if isinstance(remesh_type, dict) else []
        if "None" not in remesh_options:
            raise ProviderError(
                "L'option sans remeshing n'existe plus dans l'API réelle du Space."
            )

        inputs: dict[str, Any] = {}
        for name in ("foreground_ratio", "vertex_count", "texture_size"):
            parameter = by_name[name]
            if not parameter.get("parameter_has_default"):
                raise ProviderError(
                    f"Le paramètre {name} n'a pas de valeur par défaut vérifiée."
                )
            inputs[name] = parameter.get("parameter_default")
        inputs["remesh_option"] = "None"

        outputs = endpoint.get("returns")
        if not isinstance(outputs, list):
            raise ProviderError("view_api() ne décrit pas la sortie du modèle 3D.")
        model_output_index = next(
            (
                index
                for index, output in enumerate(outputs)
                if isinstance(output, dict)
                and output.get("label") == "3D Model"
                and output.get("python_type", {}).get("type") == "filepath"
            ),
            None,
        )
        if model_output_index is None:
            raise ProviderError(
                "La sortie fichier 3D n'a pas été trouvée dans la description réelle."
            )
        return {
            "endpoint": _ENDPOINT,
            "inputs": inputs,
            "model_output_index": model_output_index,
            "output_count": len(outputs),
        }

    @staticmethod
    def _model_output_path(result: Any, output_index: int) -> Path:
        """Récupère le chemin local associé à la sortie de type filepath."""
        if not isinstance(result, (list, tuple)) or output_index >= len(result):
            raise ProviderError("Le Space n'a pas renvoyé la sortie de modèle attendue.")
        output = result[output_index]
        if isinstance(output, dict):
            path_value = output.get("path")
        elif isinstance(output, (str, Path)):
            path_value = output
        else:
            path_value = getattr(output, "path", None)
        if not path_value:
            raise ProviderError("La sortie du Space ne contient aucun chemin de fichier.")
        model_path = Path(path_value)
        if model_path.suffix.lower() != ".glb" or not model_path.is_file():
            raise ProviderError("La sortie du Space n'est pas un fichier GLB local.")
        return model_path

    @staticmethod
    def _read_glb(model_path: Path) -> bytes:
        """Vérifie l'en-tête GLB 2.0 et la longueur déclarée avant de renvoyer le fichier."""
        data = model_path.read_bytes()
        if len(data) < 12 or data[:4] != b"glTF":
            raise ProviderError("Le fichier renvoyé ne possède pas l'en-tête GLB attendu.")
        version = int.from_bytes(data[4:8], byteorder="little")
        declared_length = int.from_bytes(data[8:12], byteorder="little")
        if version != 2 or declared_length != len(data):
            raise ProviderError("Le fichier GLB renvoyé est incomplet ou incompatible.")
        return data

    @staticmethod
    def _is_retryable(error: Exception) -> bool:
        """Autorise une seule relance pour les erreurs de démarrage ou réseau temporaires."""
        message = str(error).casefold()
        transient_markers = (
            "starting",
            "building",
            "paused",
            "sleeping",
            "not running",
            "temporarily unavailable",
            "connection reset",
            "connection aborted",
            "503",
        )
        return any(marker in message for marker in transient_markers)

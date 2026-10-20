# Rôle : adapte les APIs Gradio observées à Image3DProvider et vérifie le GLB reçu.
# Exécution : appelé par GenerationService ; le client distant est créé à la génération.
"""Fournisseur image-vers-3D compatible avec un Space ou une URL Gradio publique."""

from __future__ import annotations

import json
import time
from concurrent.futures import TimeoutError as JobTimeoutError
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable
from urllib.parse import quote, urlsplit

import httpx2
from gradio_client import Client, handle_file

from app.config import Settings, get_settings
from app.providers.base import ProviderError

_SF3D_ENDPOINT = "/run_button"
_SF3D_PARAMETER_NAMES = {
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
_JSON_CHUNK_TYPE = 0x4E4F534A


class HuggingFaceSpaceProvider:
    """Appelle une API Gradio découverte à l'exécution, puis vérifie le GLB."""

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
        """Envoie une image et ne retourne que des octets GLB 2.0 valides."""
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
                    f"La génération a dépassé {self.settings.hf_timeout_seconds} secondes."
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
        target_label = (
            "le serveur Gradio configuré"
            if self._is_http_url(self.settings.hf_space_id)
            else f"le Space Hugging Face {self.settings.hf_space_id}"
        )
        raise ProviderError(
            f"{target_label} est indisponible ou a refusé la génération : {message}"
        ) from last_error

    def _wait_for_space(self, deadline: float) -> None:
        """Attend le démarrage d'un Space HF ; une URL Gradio publique n'a pas ce runtime."""
        if self._is_http_url(self.settings.hf_space_id):
            return

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
                raise ProviderError(
                    "Délai maximal atteint en attendant le Space Hugging Face."
                )
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
        """Inspecte view_api à chaque appel et exécute le contrat réellement exposé."""
        with TemporaryDirectory(prefix="forma3d-gradio-") as download_dir:
            client = self._client_factory(
                self.settings.hf_space_id,
                token=self._client_token(),
                verbose=False,
                analytics_enabled=False,
                download_files=download_dir,
                httpx_kwargs={"timeout": max(1.0, deadline - time.monotonic())},
            )
            api_description = client.view_api(
                print_info=False,
                return_format="dict",
            )
            if not isinstance(api_description, dict):
                raise ProviderError("view_api() n'a pas renvoyé une description exploitable.")

            named_endpoints = api_description.get("named_endpoints")
            if isinstance(named_endpoints, dict) and _SF3D_ENDPOINT in named_endpoints:
                contract = self._read_sf3d_api_contract(api_description)
                result = self._submit(
                    client,
                    contract["selector"],
                    contract["inputs"],
                    image_path,
                    deadline,
                )
            else:
                contract = self._read_triphosr_api_contract(api_description)
                result = self._run_triphosr_contract(
                    client,
                    contract,
                    image_path,
                    deadline,
                )

            model_path = self._model_output_path(
                result,
                contract["model_output_index"],
            )
            return self._read_glb(model_path)

    def _run_triphosr_contract(
        self,
        client: Any,
        contract: dict[str, Any],
        image_path: Path,
        deadline: float,
    ) -> Any:
        """Exécute soit le clic complet, soit les fonctions séparées décrites par l'API."""
        if contract["strategy"] == "single":
            return self._submit(
                client,
                contract["selector"],
                contract["inputs"],
                image_path,
                deadline,
            )

        check_step = contract.get("check_step")
        if check_step is not None:
            self._submit_step(client, check_step, image_path, deadline)

        processed_result = self._submit_step(
            client,
            contract["preprocess_step"],
            image_path,
            deadline,
        )
        processed_path = self._single_output_path(
            processed_result,
            contract["preprocess_output_index"],
            "L'étape preprocess n'a pas renvoyé son image de sortie.",
        )
        return self._submit_step(
            client,
            contract["generate_step"],
            processed_path,
            deadline,
        )

    def _submit(
        self,
        client: Any,
        selector: dict[str, Any],
        input_values: list[Any],
        image_path: Path,
        deadline: float,
    ) -> Any:
        """Prépare les arguments d'après view_api et attend le travail avec le délai restant."""
        values = list(input_values)
        input_index = next(
            index
            for index, value in enumerate(values)
            if isinstance(value, _ImageInput)
        )
        values[input_index] = handle_file(str(image_path))
        job = client.submit(*values, **selector)
        return self._result_before_deadline(job, deadline)

    def _submit_step(
        self,
        client: Any,
        step: dict[str, Any],
        image_path: Path,
        deadline: float,
    ) -> Any:
        """Appelle une fonction Gradio avec le sélecteur et les valeurs découverts."""
        values = list(step["inputs"])
        values[step["input_index"]] = handle_file(str(image_path))
        job = client.submit(*values, **step["selector"])
        return self._result_before_deadline(job, deadline)

    @staticmethod
    def _result_before_deadline(job: Any, deadline: float) -> Any:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            job.cancel()
            raise JobTimeoutError("Le délai global de génération est atteint.")
        try:
            return job.result(timeout=remaining)
        except JobTimeoutError:
            job.cancel()
            raise

    def _client_token(self) -> str | bool:
        """N'envoie un jeton HF qu'à HF, jamais à un serveur public tiers."""
        if not self.settings.hf_token:
            return False
        if not self._is_http_url(self.settings.hf_space_id):
            return self.settings.hf_token
        host = (urlsplit(self.settings.hf_space_id).hostname or "").casefold()
        if host in {"huggingface.co", "www.huggingface.co"}:
            return self.settings.hf_token
        return False

    @staticmethod
    def _is_http_url(value: str) -> bool:
        return value.startswith(("http://", "https://"))

    @classmethod
    def _read_sf3d_api_contract(cls, api_description: Any) -> dict[str, Any]:
        """Valide les noms, valeurs par défaut et sortie SF3D observés précédemment."""
        endpoints = api_description.get("named_endpoints")
        endpoint = endpoints.get(_SF3D_ENDPOINT) if isinstance(endpoints, dict) else None
        if not isinstance(endpoint, dict):
            raise ProviderError(
                f"Le Space ne publie plus {_SF3D_ENDPOINT} ; son API doit être inspectée."
            )

        parameters = endpoint.get("parameters")
        if not isinstance(parameters, list):
            raise ProviderError("view_api() ne décrit pas les paramètres du bouton.")
        by_name = {
            cls._parameter_name(parameter): parameter
            for parameter in parameters
            if isinstance(parameter, dict)
        }
        if set(by_name) != _SF3D_PARAMETER_NAMES:
            raise ProviderError(
                "Les paramètres de Stable Fast 3D ont changé ; "
                "vérifiez view_api() avant de l'utiliser."
            )

        remesh_type = by_name["remesh_option"].get("type", {})
        remesh_options = remesh_type.get("enum", []) if isinstance(remesh_type, dict) else []
        if "None" not in remesh_options:
            raise ProviderError(
                "L'option sans remeshing n'existe plus dans l'API réelle du Space."
            )

        inputs = []
        input_name = None
        for parameter in parameters:
            name = cls._parameter_name(parameter)
            if name == "input_image":
                input_name = name
                inputs.append(_ImageInput())
            elif name == "remesh_option":
                inputs.append("None")
            elif parameter.get("parameter_has_default"):
                inputs.append(parameter.get("parameter_default"))
            else:
                raise ProviderError(
                    f"Le paramètre {name} n'a pas de valeur par défaut vérifiée."
                )
        if input_name is None:
            raise ProviderError("view_api() ne décrit pas le paramètre image de SF3D.")

        outputs = endpoint.get("returns")
        if not isinstance(outputs, list):
            raise ProviderError("view_api() ne décrit pas la sortie du modèle 3D.")
        model_output_index = cls._find_glb_output(outputs)
        if model_output_index is None:
            model_output_index = next(
                (
                    index
                    for index, output in enumerate(outputs)
                    if isinstance(output, dict)
                    and output.get("label") == "3D Model"
                    and cls._is_file_output(output)
                ),
                None,
            )
        if model_output_index is None:
            raise ProviderError(
                "La sortie fichier 3D n'a pas été trouvée dans la description réelle."
            )
        return {
            "strategy": "single",
            "selector": {"api_name": _SF3D_ENDPOINT},
            "inputs": inputs,
            "model_output_index": model_output_index,
        }

    @classmethod
    def _read_triphosr_api_contract(cls, api_description: Any) -> dict[str, Any]:
        """Trouve la chaîne TripoSR à partir des entrées et sorties de view_api()."""
        endpoints = cls._all_endpoints(api_description)
        direct_candidates = []
        preprocess_candidates = []
        generate_candidates = []
        check_candidates = []

        for selector, endpoint in endpoints:
            parameters = endpoint.get("parameters")
            outputs = endpoint.get("returns")
            if not isinstance(parameters, list) or not isinstance(outputs, list):
                continue
            parameter_names = [cls._parameter_name(value) for value in parameters]
            image_index = cls._image_input_index(parameters)
            if image_index is None:
                continue
            has_background = cls._has_background_control(parameters)
            has_foreground = cls._has_foreground_control(parameters)
            has_resolution = cls._has_resolution_control(parameters)
            glb_index = cls._find_glb_output(outputs)

            if glb_index is not None and has_background and has_foreground and has_resolution:
                direct_candidates.append(
                    cls._make_call_contract(
                        selector,
                        parameters,
                        image_index,
                        glb_index,
                    )
                )
            elif glb_index is not None and has_resolution:
                generate_candidates.append(
                    cls._make_call_contract(
                        selector,
                        parameters,
                        image_index,
                        glb_index,
                    )
                )
            elif has_background and has_foreground and cls._find_image_output(outputs) is not None:
                preprocess_candidates.append(
                    {
                        "selector": selector,
                        "inputs": cls._defaulted_inputs(parameters, image_index),
                        "input_index": image_index,
                        "output_index": cls._find_image_output(outputs),
                    }
                )
            elif not outputs and len(parameters) == 1:
                check_candidates.append(
                    {
                        "selector": selector,
                        "inputs": cls._defaulted_inputs(parameters, image_index),
                        "input_index": image_index,
                    }
                )

        if direct_candidates:
            direct = max(direct_candidates, key=lambda value: len(value["inputs"]))
            return {
                "strategy": "single",
                **direct,
            }
        if not preprocess_candidates or not generate_candidates:
            raise ProviderError(
                "L'API TripoSR ne publie pas une chaîne vérifiable vers la sortie GLB "
                "(prétraitement, résolution et modèle GLB). Aucun appel n'a été envoyé."
            )

        preprocess_step = max(
            preprocess_candidates,
            key=lambda value: len(value["inputs"]),
        )
        generate_step = max(generate_candidates, key=lambda value: len(value["inputs"]))
        check_step = check_candidates[0] if check_candidates else None
        return {
            "strategy": "separate",
            "preprocess_step": preprocess_step,
            "preprocess_output_index": preprocess_step["output_index"],
            "generate_step": generate_step,
            "model_output_index": generate_step["model_output_index"],
            "check_step": check_step,
        }

    @classmethod
    def _make_call_contract(
        cls,
        selector: dict[str, Any],
        parameters: list[dict[str, Any]],
        image_index: int,
        model_output_index: int,
    ) -> dict[str, Any]:
        return {
            "selector": selector,
            "inputs": cls._defaulted_inputs(parameters, image_index),
            "input_index": image_index,
            "model_output_index": model_output_index,
        }

    @classmethod
    def _defaulted_inputs(
        cls,
        parameters: list[dict[str, Any]],
        image_index: int,
    ) -> list[Any]:
        values = []
        for index, parameter in enumerate(parameters):
            if index == image_index:
                values.append(_ImageInput())
            elif parameter.get("parameter_has_default"):
                values.append(parameter.get("parameter_default"))
            else:
                name = cls._parameter_name(parameter) or f"position {index + 1}"
                raise ProviderError(
                    f"view_api() ne donne aucune valeur par défaut vérifiée pour {name}."
                )
        return values

    @staticmethod
    def _all_endpoints(api_description: dict[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        """Retourne les endpoints nommés et anonymes avec le sélecteur attendu par Client."""
        endpoints = []
        named = api_description.get("named_endpoints", {})
        if isinstance(named, dict):
            for api_name, endpoint in named.items():
                if isinstance(api_name, str) and isinstance(endpoint, dict):
                    endpoints.append(({"api_name": api_name}, endpoint))
        unnamed = api_description.get("unnamed_endpoints", {})
        if isinstance(unnamed, dict):
            for raw_index, endpoint in unnamed.items():
                if isinstance(endpoint, dict):
                    try:
                        fn_index = int(raw_index)
                    except (TypeError, ValueError):
                        continue
                    endpoints.append(({"fn_index": fn_index}, endpoint))
        return endpoints

    @classmethod
    def _parameter_name(cls, parameter: dict[str, Any]) -> str:
        raw_name = parameter.get("parameter_name") or parameter.get("label") or parameter.get("name")
        return cls._normalize_name(str(raw_name)) if raw_name else ""

    @staticmethod
    def _normalize_name(value: str) -> str:
        """Reproduit le nettoyage de nom documenté par gradio_client.view_api()."""
        return "".join(
            character for character in value if character.isalnum() or character in " _"
        ).replace(" ", "_").lower()

    @classmethod
    def _image_input_index(cls, parameters: list[dict[str, Any]]) -> int | None:
        for index, parameter in enumerate(parameters):
            name = cls._parameter_name(parameter)
            component = str(parameter.get("component", "")).casefold()
            if name in {"input_image", "image"} or component == "image":
                return index
        return None

    @classmethod
    def _has_background_control(cls, parameters: list[dict[str, Any]]) -> bool:
        return any(
            cls._parameter_name(parameter) in {"do_remove_background", "remove_background"}
            or (
                str(parameter.get("component", "")).casefold() == "checkbox"
                and "background" in cls._parameter_name(parameter)
            )
            for parameter in parameters
        )

    @classmethod
    def _has_foreground_control(cls, parameters: list[dict[str, Any]]) -> bool:
        return any("foreground" in cls._parameter_name(parameter) for parameter in parameters)

    @classmethod
    def _has_resolution_control(cls, parameters: list[dict[str, Any]]) -> bool:
        return any(
            "resolution" in cls._parameter_name(parameter)
            or cls._parameter_name(parameter) == "mc_resolution"
            for parameter in parameters
        )

    @classmethod
    def _find_image_output(cls, outputs: list[Any]) -> int | None:
        for index, output in enumerate(outputs):
            if not isinstance(output, dict):
                continue
            label = cls._normalize_name(str(output.get("label", "")))
            component = str(output.get("component", "")).casefold()
            if component == "image" or "processed_image" in label:
                return index
        return None

    @classmethod
    def _find_glb_output(cls, outputs: list[Any]) -> int | None:
        for index, output in enumerate(outputs):
            if (
                isinstance(output, dict)
                and "glb" in str(output.get("label", "")).casefold()
                and cls._is_file_output(output)
            ):
                return index
        return None

    @staticmethod
    def _is_file_output(output: dict[str, Any]) -> bool:
        python_type = output.get("python_type")
        if isinstance(python_type, dict):
            return (
                python_type.get("type") == "filepath"
                or str(output.get("component", "")).casefold() == "model3d"
            )
        if isinstance(python_type, str):
            return (
                "filepath" in python_type.casefold()
                or str(output.get("component", "")).casefold() == "model3d"
            )
        return str(output.get("component", "")).casefold() == "model3d"

    @classmethod
    def _model_output_path(cls, result: Any, output_index: int) -> Path:
        """Récupère le chemin local associé à la sortie GLB décrite par l'API."""
        return cls._file_output_path(
            result,
            output_index,
            "Le Space n'a pas renvoyé la sortie de modèle attendue.",
            require_glb=True,
        )

    @classmethod
    def _single_output_path(
        cls,
        result: Any,
        output_index: int,
        error_message: str,
    ) -> Path:
        """Extrait un fichier image de prétraitement retourné par le client Gradio."""
        return cls._file_output_path(result, output_index, error_message, require_glb=False)

    @staticmethod
    def _file_output_path(
        result: Any,
        output_index: int,
        error_message: str,
        require_glb: bool,
    ) -> Path:
        if isinstance(result, (list, tuple)):
            if output_index >= len(result):
                raise ProviderError(error_message)
            output = result[output_index]
        elif output_index == 0:
            # Gradio peut renvoyer directement la valeur quand l'endpoint a une sortie.
            output = result
        else:
            raise ProviderError(error_message)
        if isinstance(output, dict):
            path_value = output.get("path")
        elif isinstance(output, (str, Path)):
            path_value = output
        else:
            path_value = getattr(output, "path", None)
        if not path_value:
            raise ProviderError(error_message)
        file_path = Path(path_value)
        if not file_path.is_file():
            raise ProviderError("La sortie Gradio ne correspond pas à un fichier local disponible.")
        if require_glb and file_path.suffix.casefold() != ".glb":
            raise ProviderError("La sortie du fournisseur n'est pas un fichier GLB local.")
        return file_path

    @staticmethod
    def _read_glb(model_path: Path) -> bytes:
        """Contrôle l'en-tête GLB 2.0, son chunk JSON, l'asset et les limites de chunks."""
        data = model_path.read_bytes()
        if len(data) < 20 or data[:4] != b"glTF":
            raise ProviderError("Le fichier renvoyé ne possède pas un en-tête GLB complet.")
        version = int.from_bytes(data[4:8], byteorder="little")
        declared_length = int.from_bytes(data[8:12], byteorder="little")
        if version != 2 or declared_length != len(data):
            raise ProviderError("Le fichier GLB renvoyé est incomplet ou incompatible.")

        json_length = int.from_bytes(data[12:16], byteorder="little")
        json_chunk_type = int.from_bytes(data[16:20], byteorder="little")
        json_end = 20 + json_length
        if (
            json_chunk_type != _JSON_CHUNK_TYPE
            or json_length == 0
            or json_length % 4 != 0
            or json_end > len(data)
        ):
            raise ProviderError("Le premier chunk JSON du GLB 2.0 est invalide.")
        try:
            document = json.loads(data[20:json_end].decode("utf-8").rstrip(" \t\r\n\0"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProviderError("Le chunk JSON du GLB 2.0 n'est pas lisible.") from error
        if not isinstance(document, dict) or not isinstance(document.get("asset"), dict):
            raise ProviderError("Le chunk JSON ne décrit pas un asset glTF.")
        if document["asset"].get("version") != "2.0":
            raise ProviderError("Le document embarqué n'annonce pas glTF 2.0.")

        offset = json_end
        while offset < len(data):
            if offset + 8 > len(data):
                raise ProviderError("Un en-tête de chunk GLB est tronqué.")
            chunk_length = int.from_bytes(data[offset : offset + 4], byteorder="little")
            if chunk_length % 4 != 0 or offset + 8 + chunk_length > len(data):
                raise ProviderError("Un chunk GLB dépasse les limites du fichier.")
            offset += 8 + chunk_length
        if offset != len(data):
            raise ProviderError("Les chunks GLB ne couvrent pas exactement le fichier.")
        return data

    @staticmethod
    def _is_retryable(error: Exception) -> bool:
        """Autorise une relance seulement pour les erreurs de démarrage ou réseau temporaires."""
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


class _ImageInput:
    """Marque temporairement la position d'une image découverte dans view_api()."""

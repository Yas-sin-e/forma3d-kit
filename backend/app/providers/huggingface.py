# Rôle : adapte les APIs Gradio observées à Image3DProvider et vérifie le GLB reçu.
# Exécution : appelé par GenerationService ; le client distant est créé à la génération.
"""Fournisseur image-vers-3D compatible avec un Space ou une URL Gradio publique."""

from __future__ import annotations

# json (standard) : lit le bloc JSON d'un fichier GLB pour le vérifier.
import json
import time
# concurrent.futures.TimeoutError (standard) : erreur levée quand un travail dépasse le délai d'attente.
from concurrent.futures import TimeoutError as JobTimeoutError
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable
from urllib.parse import quote, urlsplit

# httpx2 : client HTTP ; ici, interroge l'état d'un Space Hugging Face (démarré, en veille…).
import httpx2
# gradio_client : appelle une application Gradio depuis Python. view_api() décrit les fonctions
# réellement exposées ; le projet lit toujours ce contrat avant d'envoyer une photo.
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
_MISSING_COMPONENT_VALUE = object()
_PROVIDER_HEALTH_TIMEOUT_SECONDS = 5.0


class HuggingFaceSpaceProvider:
    """Appelle une API Gradio découverte à l'exécution, puis vérifie le GLB."""

    def __init__(
        self,
        settings: Settings | None = None,
        client_factory: Callable[..., Any] = Client,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Reçoit la configuration, la fabrique de client Gradio et la fonction d'attente.

        client_factory et sleep sont remplaçables par les tests (faux client, pas d'attente réelle).
        """
        self.settings = settings or get_settings()
        self._client_factory = client_factory
        self._sleep = sleep

    def generate(self, image_path: Path) -> bytes:
        """Envoie une image et ne retourne que des octets GLB 2.0 valides.

        Paramètre : image_path (photo préparée). Retour : octets du GLB.
        Une ou deux tentatives dans un délai global ; on ne relance que les erreurs passagères
        (Space en cours de démarrage, coupure réseau). Lève ProviderError avec un message sans jeton.
        """
        if not self.settings.hf_space_id.strip():
            raise ProviderError(
                "HF_SPACE_ID est vide dans backend/.env ; le serveur 3D n'est pas configuré."
            )
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

    def health_status(self) -> str:
        """Teste la joignabilité sans jamais inclure l'adresse dans la réponse."""
        target = self.settings.hf_space_id.strip()
        if not target:
            return "UNCONFIGURED"

        try:
            if self._is_http_url(target):
                host = (urlsplit(target).hostname or "").casefold()
                if host in {"huggingface.co", "www.huggingface.co"}:
                    parts = urlsplit(target).path.strip("/").split("/")
                    if len(parts) < 2 or parts[0] != "spaces":
                        return "OFFLINE"
                    space_id = "/".join(parts[1:])
                    runtime_url = (
                        "https://huggingface.co/api/spaces/"
                        f"{quote(space_id, safe='/')}/runtime"
                    )
                    headers = {}
                    if self.settings.hf_token:
                        headers["Authorization"] = f"Bearer {self.settings.hf_token}"
                    response = httpx2.get(
                        runtime_url,
                        headers=headers,
                        timeout=_PROVIDER_HEALTH_TIMEOUT_SECONDS,
                    )
                    response.raise_for_status()
                    return (
                        "ONLINE"
                        if response.json().get("stage") == "RUNNING"
                        else "OFFLINE"
                    )

                response = httpx2.get(
                    f"{target.rstrip('/')}/config",
                    timeout=_PROVIDER_HEALTH_TIMEOUT_SECONDS,
                )
                return "ONLINE" if response.status_code == 200 else "OFFLINE"

            runtime_url = (
                "https://huggingface.co/api/spaces/"
                f"{quote(target, safe='/')}/runtime"
            )
            headers = {}
            if self.settings.hf_token:
                headers["Authorization"] = f"Bearer {self.settings.hf_token}"
            response = httpx2.get(
                runtime_url,
                headers=headers,
                timeout=_PROVIDER_HEALTH_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            return (
                "ONLINE"
                if response.json().get("stage") == "RUNNING"
                else "OFFLINE"
            )
        except Exception:
            return "OFFLINE"

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
            )
            # view_api : on demande au serveur la liste réelle de ses fonctions et paramètres (le « contrat »).
            api_description = client.view_api(
                print_info=False,
                return_format="dict",
            )
            if not isinstance(api_description, dict):
                raise ProviderError("view_api() n'a pas renvoyé une description exploitable.")

            named_endpoints = api_description.get("named_endpoints")
            if isinstance(named_endpoints, dict) and _SF3D_ENDPOINT in named_endpoints:
                if (
                    self.settings.foreground_ratio is not None
                    or self.settings.mc_resolution is not None
                ):
                    raise ProviderError(
                        "FOREGROUND_RATIO et MC_RESOLUTION sont des réglages TripoSR ; "
                        "l'API Stable Fast 3D n'expose pas ces paramètres."
                    )
                contract = self._read_sf3d_api_contract(api_description)
                result = self._submit(
                    client,
                    contract["selector"],
                    contract["inputs"],
                    image_path,
                    deadline,
                )
            else:
                contract = self._read_triphosr_api_contract(
                    api_description,
                    getattr(client, "config", None),
                    foreground_ratio=self.settings.foreground_ratio,
                    mc_resolution=self.settings.mc_resolution,
                )
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
        # client.submit : lance le travail sur le serveur distant sans bloquer ; on attend ensuite son résultat.
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
        """Attend le résultat d'un travail Gradio sans dépasser le délai global ; annule le travail sinon."""
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
        """Vrai si la cible est une URL http(s) (serveur Gradio direct) et non un identifiant de Space."""
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
    def _read_triphosr_api_contract(
        cls,
        api_description: Any,
        client_config: Any = None,
        foreground_ratio: float | None = None,
        mc_resolution: int | None = None,
    ) -> dict[str, Any]:
        """Trouve la chaîne d'API et lit les valeurs réelles des composants Gradio."""
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
            component_values = cls._client_component_values(
                client_config,
                selector,
                len(parameters),
            )
            component_props = cls._client_component_props(
                client_config,
                selector,
                len(parameters),
            )

            if glb_index is not None and has_background and has_foreground and has_resolution:
                direct_candidates.append(
                    cls._make_call_contract(
                        selector,
                        parameters,
                        image_index,
                        glb_index,
                        component_values,
                        component_props,
                        {
                            "foreground_ratio": foreground_ratio,
                            "mc_resolution": mc_resolution,
                        },
                    )
                )
            elif glb_index is not None and has_resolution:
                generate_candidates.append(
                    cls._make_call_contract(
                        selector,
                        parameters,
                        image_index,
                        glb_index,
                        component_values,
                        component_props,
                        {"mc_resolution": mc_resolution},
                    )
                )
            elif has_background and has_foreground and cls._find_image_output(outputs) is not None:
                inputs = cls._defaulted_inputs(
                    parameters,
                    image_index,
                    component_values,
                )
                applied_settings = cls._apply_triposr_settings(
                    parameters,
                    inputs,
                    component_props,
                    {"foreground_ratio": foreground_ratio},
                )
                preprocess_candidates.append(
                    {
                        "selector": selector,
                        "inputs": inputs,
                        "applied_settings": applied_settings,
                        "input_index": image_index,
                        "output_index": cls._find_image_output(outputs),
                    }
                )
            elif not outputs and len(parameters) == 1:
                check_candidates.append(
                    {
                        "selector": selector,
                        "inputs": cls._defaulted_inputs(
                            parameters,
                            image_index,
                            component_values,
                        ),
                        "input_index": image_index,
                    }
                )

        if direct_candidates:
            direct = max(direct_candidates, key=lambda value: len(value["inputs"]))
            cls._require_configured_triposr_settings(
                direct.get("applied_settings", set()),
                foreground_ratio,
                mc_resolution,
            )
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
        applied_settings = set(preprocess_step.get("applied_settings", set()))
        applied_settings.update(generate_step.get("applied_settings", set()))
        cls._require_configured_triposr_settings(
            applied_settings,
            foreground_ratio,
            mc_resolution,
        )
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
        component_values: list[Any] | None = None,
        component_props: list[dict[str, Any] | object] | None = None,
        configured_settings: dict[str, float | int | None] | None = None,
    ) -> dict[str, Any]:
        """Assemble tout ce qu'il faut pour appeler une fonction Gradio : sélecteur, valeurs par défaut,
        réglages appliqués, position de l'image et position de la sortie GLB.
        """
        inputs = cls._defaulted_inputs(
            parameters,
            image_index,
            component_values,
        )
        applied_settings = cls._apply_triposr_settings(
            parameters,
            inputs,
            component_props,
            configured_settings or {},
        )
        return {
            "selector": selector,
            "inputs": inputs,
            "applied_settings": applied_settings,
            "input_index": image_index,
            "model_output_index": model_output_index,
        }

    @classmethod
    def _apply_triposr_settings(
        cls,
        parameters: list[dict[str, Any]],
        inputs: list[Any],
        component_props: list[dict[str, Any] | object] | None,
        configured_settings: dict[str, float | int | None],
    ) -> set[str]:
        """Applique les valeurs .env seulement si view_api publie le contrôle et ses bornes."""
        applied: set[str] = set()
        for setting_name, value in configured_settings.items():
            if value is None:
                continue
            indexes = [
                index
                for index, parameter in enumerate(parameters)
                if cls._parameter_name(parameter) == setting_name
            ]
            if not indexes:
                continue
            if len(indexes) != 1:
                raise ProviderError(
                    f"view_api() publie plusieurs paramètres {setting_name} ; "
                    "aucun réglage n'a été appliqué."
                )

            index = indexes[0]
            parameter = parameters[index]
            parameter_type = parameter.get("type")
            component_type = str(parameter.get("component", "")).casefold()
            type_name = (
                parameter_type.get("type")
                if isinstance(parameter_type, dict)
                else parameter_type
            )
            if type_name not in {"number", "integer", "float"} and component_type != "slider":
                raise ProviderError(
                    f"Le paramètre {setting_name} n'est pas décrit comme une valeur numérique dans view_api()."
                )

            metadata = parameter_type if isinstance(parameter_type, dict) else {}
            props = (
                component_props[index]
                if component_props is not None and index < len(component_props)
                else _MISSING_COMPONENT_VALUE
            )
            props = props if isinstance(props, dict) else {}
            minimum = metadata.get(
                "minimum",
                metadata.get("min", props.get("minimum", props.get("min"))),
            )
            maximum = metadata.get(
                "maximum",
                metadata.get("max", props.get("maximum", props.get("max"))),
            )
            if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
                raise ProviderError(
                    f"view_api() ou Client.config ne publie pas les bornes de {setting_name} ; "
                    "retirez son réglage .env pour utiliser la valeur du serveur."
                )
            if not minimum <= value <= maximum:
                raise ProviderError(
                    f"La valeur configurée de {setting_name} est hors des bornes publiées par l'API."
                )
            inputs[index] = value
            applied.add(setting_name)
        return applied

    @staticmethod
    def _require_configured_triposr_settings(
        applied: set[str],
        foreground_ratio: float | None,
        mc_resolution: int | None,
    ) -> None:
        """Refuse une config qui ne correspond pas aux champs du contrat réellement découvert."""
        if foreground_ratio is not None and "foreground_ratio" not in applied:
            raise ProviderError(
                "view_api() ne publie pas le paramètre foreground_ratio dans la chaîne choisie."
            )
        if mc_resolution is not None and "mc_resolution" not in applied:
            raise ProviderError(
                "view_api() ne publie pas le paramètre mc_resolution dans la chaîne choisie."
            )

    @classmethod
    def _defaulted_inputs(
        cls,
        parameters: list[dict[str, Any]],
        image_index: int,
        component_values: list[Any] | None = None,
    ) -> list[Any]:
        """Prend les défauts de view_api ou les valeurs configurées dans Client.config."""
        values = []
        for index, parameter in enumerate(parameters):
            if index == image_index:
                values.append(_ImageInput())
            elif (
                parameter.get("parameter_has_default")
                and "parameter_default" in parameter
            ):
                values.append(parameter.get("parameter_default"))
            elif (
                component_values is not None
                and index < len(component_values)
                and component_values[index] is not _MISSING_COMPONENT_VALUE
            ):
                values.append(component_values[index])
            else:
                name = cls._parameter_name(parameter) or f"position {index + 1}"
                raise ProviderError(
                    f"Aucune valeur par défaut vérifiable dans view_api() ou Client.config "
                    f"pour le paramètre {name}."
                )
        return values

    @staticmethod
    def _client_component_values(
        client_config: Any,
        selector: dict[str, Any],
        parameter_count: int,
    ) -> list[Any] | None:
        """Associe un endpoint observé aux valeurs de ses composants dans la config Gradio."""
        if not isinstance(client_config, dict):
            return None
        api_name = selector.get("api_name")
        dependencies = client_config.get("dependencies")
        components = client_config.get("components")
        if not isinstance(api_name, str) or not isinstance(dependencies, list):
            return None
        if not isinstance(components, list):
            return None

        matching_dependencies = [
            dependency
            for dependency in dependencies
            if isinstance(dependency, dict)
            and isinstance(dependency.get("api_name"), str)
            and dependency["api_name"].strip("/") == api_name.strip("/")
            and isinstance(dependency.get("inputs"), list)
            and len(dependency["inputs"]) == parameter_count
        ]
        if len(matching_dependencies) != 1:
            return None

        component_by_id = {
            component.get("id"): component
            for component in components
            if isinstance(component, dict) and "id" in component
        }
        values = []
        for component_id in matching_dependencies[0]["inputs"]:
            component = component_by_id.get(component_id)
            props = component.get("props") if isinstance(component, dict) else None
            if isinstance(props, dict) and "value" in props:
                values.append(props["value"])
            else:
                values.append(_MISSING_COMPONENT_VALUE)
        return values

    @staticmethod
    def _client_component_props(
        client_config: Any,
        selector: dict[str, Any],
        parameter_count: int,
    ) -> list[dict[str, Any] | object] | None:
        """Lit les propriétés des contrôles Gradio reliés à un endpoint découvert."""
        if not isinstance(client_config, dict):
            return None
        api_name = selector.get("api_name")
        dependencies = client_config.get("dependencies")
        components = client_config.get("components")
        if not isinstance(api_name, str) or not isinstance(dependencies, list):
            return None
        if not isinstance(components, list):
            return None

        matches = [
            dependency
            for dependency in dependencies
            if isinstance(dependency, dict)
            and isinstance(dependency.get("api_name"), str)
            and dependency["api_name"].strip("/") == api_name.strip("/")
            and isinstance(dependency.get("inputs"), list)
            and len(dependency["inputs"]) == parameter_count
        ]
        if len(matches) != 1:
            return None

        component_by_id = {
            component.get("id"): component
            for component in components
            if isinstance(component, dict) and "id" in component
        }
        properties = []
        for component_id in matches[0]["inputs"]:
            component = component_by_id.get(component_id)
            props = component.get("props") if isinstance(component, dict) else None
            properties.append(props if isinstance(props, dict) else _MISSING_COMPONENT_VALUE)
        return properties

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
        """Renvoie le nom normalisé d'un paramètre décrit par view_api (ou une chaîne vide)."""
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
        """Trouve la position du paramètre « image » dans la liste des paramètres, ou None."""
        for index, parameter in enumerate(parameters):
            name = cls._parameter_name(parameter)
            component = str(parameter.get("component", "")).casefold()
            if name in {"input_image", "image"} or component == "image":
                return index
        return None

    @classmethod
    def _has_background_control(cls, parameters: list[dict[str, Any]]) -> bool:
        """Vrai si la fonction propose une option de suppression du fond."""
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
        """Vrai si la fonction propose un réglage de taille du premier plan (foreground)."""
        return any("foreground" in cls._parameter_name(parameter) for parameter in parameters)

    @classmethod
    def _has_resolution_control(cls, parameters: list[dict[str, Any]]) -> bool:
        """Vrai si la fonction propose un réglage de résolution du maillage."""
        return any(
            "resolution" in cls._parameter_name(parameter)
            or cls._parameter_name(parameter) == "mc_resolution"
            for parameter in parameters
        )

    @classmethod
    def _find_image_output(cls, outputs: list[Any]) -> int | None:
        """Trouve la position de la sortie « image prétraitée », ou None."""
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
        """Trouve la position de la sortie fichier dont le libellé contient « glb », ou None."""
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
        """Vrai si une sortie décrite par view_api est un fichier (chemin local ou composant Model3D)."""
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
        """Extrait le chemin du fichier renvoyé par Gradio à la position demandée.

        Lève ProviderError si la sortie manque, n'est pas un fichier présent, ou n'est pas un .glb quand require_glb est vrai.
        """
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

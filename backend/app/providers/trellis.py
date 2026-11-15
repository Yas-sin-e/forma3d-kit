# Rôle : adapte le Space public TRELLIS au contrat Image3DProvider (détourage puis génération GLB texturé).
# Exécution : choisi au démarrage quand IMAGE3D_PROVIDER=trellis ; GenerationService appelle generate().
"""Fournisseur TRELLIS : enchaînement observé du Space trellis-community/TRELLIS (sous-étape C2).

Enchaînement, identique à l'interface web et vérifié par les essais du 11 novembre 2026 :
1. `view_api()` : on refuse de continuer si une fonction attendue a disparu ;
2. `/start_session` : crée le dossier de session côté Space (sans lui, FileNotFoundError) ;
3. `/preprocess_image` : détourage du fond (sans lui, le sol de la photo est reconstruit) ;
4. `/generate_and_extract_glb` : génération et extraction d'un GLB texturé.

Le jeton HF_TOKEN facultatif n'est envoyé qu'à un identifiant de Space Hugging Face
(« propriétaire/nom », contrôlé dans config.py). Quota, file d'attente ou panne du Space
produisent une ProviderError compréhensible ; aucun contournement n'est tenté.
"""

from __future__ import annotations

# time (standard) : time.monotonic sert à calculer le temps restant avant le délai maximal.
import time
from concurrent.futures import TimeoutError as JobTimeoutError
from pathlib import Path
# tempfile.TemporaryDirectory (standard) : dossier temporaire supprimé à la fin du bloc « with ».
from tempfile import TemporaryDirectory
from typing import Any, Callable
from urllib.parse import quote

# httpx2 : client HTTP (comme RestTemplate/WebClient en Java, ou HttpClient d'Angular côté serveur).
# Ici : une seule requête GET pour connaître l'état du Space (contrôle de santé).
import httpx2
# gradio_client : bibliothèque officielle pour appeler une application Gradio (la page web d'un modèle d'IA)
# depuis un programme. Client = connexion au Space ; handle_file = prépare l'envoi d'un fichier.
from gradio_client import Client, handle_file

from app.config import Settings, get_settings
from app.providers.base import ProviderError
from app.providers.huggingface import HuggingFaceSpaceProvider

REQUIRED_FUNCTIONS = ("/start_session", "/preprocess_image", "/generate_and_extract_glb")
# Valeurs par défaut lues dans le contrat du Space le 11 novembre 2026 (voir docs/QUALITE-3D.md).
GENERATION_SETTINGS = {
    "multiimages": [],
    "seed": 0,
    "ss_guidance_strength": 7.5,
    "ss_sampling_steps": 12,
    "slat_guidance_strength": 3.0,
    "slat_sampling_steps": 12,
    "multiimage_algo": "stochastic",
    "mesh_simplify": 0.95,
    "texture_size": 1024,
}
_HEALTH_TIMEOUT_SECONDS = 5.0
# gradio_client utilise sinon le délai httpx par défaut (5 s par requête) : quand le Space gratuit
# est chargé, la connexion seule a pris 26 s le 15 novembre 2026 et provoquait un ReadTimeout.
# Le délai global de la génération reste hf_timeout_seconds.
_HTTP_REQUEST_TIMEOUT_SECONDS = 120.0


def output_file_path(value: Any) -> Path | None:
    """Chemin local d'une sortie fichier Gradio (chaîne ou dict path/value), sinon None."""
    if isinstance(value, str) and value:
        return Path(value)
    if isinstance(value, dict):
        for key in ("path", "value", "name"):
            if isinstance(value.get(key), str) and value[key]:
                return Path(value[key])
    return None


class TrellisSpaceProvider:
    """Génère un GLB texturé avec le Space TRELLIS, après détourage de la photo."""

    label = "TRELLIS"

    def __init__(
        self,
        settings: Settings | None = None,
        client_factory: Callable[..., Any] = Client,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Reçoit la configuration, la fabrique de client Gradio et l'horloge.

        client_factory et clock sont remplaçables : les tests y mettent un faux client, sans réseau.
        """
        self.settings = settings or get_settings()
        self._client_factory = client_factory
        self._clock = clock

    def generate(self, image_path: Path) -> bytes:
        """Transforme une photo en GLB texturé avec le Space TRELLIS.

        Paramètre : image_path (photo préparée). Retour : octets d'un GLB 2.0 vérifié.
        Étapes : contrat (view_api), /start_session, /preprocess_image (détourage), /generate_and_extract_glb.
        Lève ProviderError avec un message clair (quota, délai dépassé, Space indisponible).
        """
        source = Path(image_path)
        if not source.is_file():
            raise ProviderError("La photo à convertir est introuvable sur le serveur.")
        deadline = self._clock() + self.settings.hf_timeout_seconds
        try:
            with TemporaryDirectory(prefix="forma3d-trellis-") as download_dir:
                # Connexion au Space. download_files : dossier où le client range les fichiers reçus.
                # httpx_kwargs : délai de 120 s par requête HTTP (le délai par défaut de 5 s échouait quand le Space était lent).
                client = self._client_factory(
                    self.settings.trellis_space_id,
                    token=self.settings.hf_token or None,
                    verbose=False,
                    analytics_enabled=False,
                    download_files=download_dir,
                    httpx_kwargs={"timeout": _HTTP_REQUEST_TIMEOUT_SECONDS},
                )
                self._check_contract(client)
                self._call(client, deadline, api_name="/start_session")
                prepared = output_file_path(
                    self._call(client, deadline, image=handle_file(str(source)), api_name="/preprocess_image")
                )
                if prepared is None:
                    raise ProviderError("Le détourage TRELLIS n'a renvoyé aucune image.")
                result = self._call(
                    client, deadline, image=handle_file(str(prepared)),
                    api_name="/generate_and_extract_glb", **GENERATION_SETTINGS,
                )
                glb_path = output_file_path(result[2] if isinstance(result, (list, tuple)) and len(result) > 2 else None)
                if glb_path is None or not glb_path.is_file():
                    raise ProviderError("TRELLIS n'a renvoyé aucun fichier GLB.")
                return HuggingFaceSpaceProvider._read_glb(glb_path)
        except ProviderError:
            raise
        except JobTimeoutError as error:
            raise ProviderError(f"La génération TRELLIS a dépassé {self.settings.hf_timeout_seconds} secondes.") from error
        except Exception as error:
            raise ProviderError(self._explain(error)) from error

    def _check_contract(self, client: Any) -> None:
        """Vérifie que le Space expose encore les trois fonctions attendues, avant d'envoyer la photo.

        view_api() renvoie la description réelle de l'API ; on n'invente jamais un nom de fonction.
        """
        description = client.view_api(print_info=False, return_format="dict")
        endpoints = description.get("named_endpoints", {}) if isinstance(description, dict) else {}
        missing = [name for name in REQUIRED_FUNCTIONS if name not in endpoints]
        if missing:
            raise ProviderError(f"Le contrat du Space TRELLIS a changé : fonctions absentes {missing}.")

    def _call(self, client: Any, deadline: float, **kwargs: Any) -> Any:
        """Soumet un appel et attend son résultat sans dépasser le délai global.

        client.submit lance le travail sans bloquer ; job.result(timeout=...) attend au plus le temps restant.
        Si le délai est dépassé, le travail est annulé côté Space.
        """
        remaining = deadline - self._clock()
        if remaining <= 0:
            raise JobTimeoutError("Délai global atteint.")
        job = client.submit(**kwargs)
        try:
            return job.result(timeout=remaining)
        except JobTimeoutError:
            job.cancel()
            raise

    def _explain(self, error: Exception) -> str:
        """Message clair, sans jamais recopier le jeton."""
        message = str(error)
        if self.settings.hf_token:
            message = message.replace(self.settings.hf_token, "[jeton masqué]")
        if "quota" in message.casefold():
            return (
                "Quota GPU gratuit du Space TRELLIS atteint pour aujourd'hui. "
                "Réessayez plus tard ; ajoutez un jeton gratuit HF_TOKEN dans backend/.env pour un quota plus élevé."
            )
        return f"Le Space TRELLIS {self.settings.trellis_space_id} est indisponible ou a refusé la génération : {message}"

    def health_status(self) -> str:
        """ONLINE si le Space est en cours d'exécution ; aucune adresse n'est renvoyée."""
        url = f"https://huggingface.co/api/spaces/{quote(self.settings.trellis_space_id, safe='/')}/runtime"
        headers = {"Authorization": f"Bearer {self.settings.hf_token}"} if self.settings.hf_token else {}
        try:
            response = httpx2.get(url, headers=headers, timeout=_HEALTH_TIMEOUT_SECONDS)
            response.raise_for_status()
            return "ONLINE" if response.json().get("stage") == "RUNNING" else "OFFLINE"
        except Exception:
            return "OFFLINE"

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

# Les annotations de type restent du texte.
from __future__ import annotations

# time (standard) : time.monotonic sert à calculer le temps restant avant le délai maximal.
import time
# Erreur levée quand on attend un résultat plus longtemps que prévu.
from concurrent.futures import TimeoutError as JobTimeoutError
# Path : type des chemins de fichiers.
from pathlib import Path
# tempfile.TemporaryDirectory (standard) : dossier temporaire supprimé à la fin du bloc « with ».
from tempfile import TemporaryDirectory
# Any : valeur quelconque ; Callable : type d'une fonction passée en paramètre.
from typing import Any, Callable
# quote : encode l'identifiant du Space dans une URL.
from urllib.parse import quote

# httpx2 : client HTTP (comme RestTemplate/WebClient en Java, ou HttpClient d'Angular côté serveur).
# Ici : une seule requête GET pour connaître l'état du Space (contrôle de santé).
import httpx2
# gradio_client : bibliothèque officielle pour appeler une application Gradio (la page web d'un modèle d'IA)
# depuis un programme. Client = connexion au Space ; handle_file = prépare l'envoi d'un fichier.
from gradio_client import Client, handle_file

# Settings : configuration lue dans .env ; get_settings : la charge.
from app.config import Settings, get_settings
# Erreur commune des fournisseurs.
from app.providers.base import ProviderError
# Réutilisé seulement pour la vérification binaire du GLB (_read_glb).
from app.providers.huggingface import HuggingFaceSpaceProvider

# Les trois fonctions du Space dont on a besoin, dans l'ordre d'appel.
REQUIRED_FUNCTIONS = ("/start_session", "/preprocess_image", "/generate_and_extract_glb")
# Valeurs par défaut lues dans le contrat du Space le 11 novembre 2026 (voir docs/QUALITE-3D.md).
# Réglages envoyés à la génération (valeurs par défaut du contrat réel).
GENERATION_SETTINGS = {
    # Pas d'images supplémentaires : une seule photo.
    "multiimages": [],
    # Graine fixe : la même photo donne le même modèle.
    "seed": 0,
    # Étape 1 (structure 3D) : force du guidage par l'image.
    "ss_guidance_strength": 7.5,
    # Étape 1 : nombre d'itérations.
    "ss_sampling_steps": 12,
    # Étape 2 (détails et texture) : force du guidage.
    "slat_guidance_strength": 3.0,
    # Étape 2 : nombre d'itérations.
    "slat_sampling_steps": 12,
    # Méthode de fusion multi-images (sans effet avec une seule photo).
    "multiimage_algo": "stochastic",
    # Simplification du maillage : fichier plus léger.
    "mesh_simplify": 0.95,
    # Taille de la texture en pixels (1024 x 1024).
    "texture_size": 1024,
}
# Délai du contrôle de santé : il doit répondre vite.
_HEALTH_TIMEOUT_SECONDS = 5.0
# gradio_client utilise sinon le délai httpx par défaut (5 s par requête) : quand le Space gratuit
# est chargé, la connexion seule a pris 26 s le 15 novembre 2026 et provoquait un ReadTimeout.
# Le délai global de la génération reste hf_timeout_seconds.
# Délai par requête HTTP vers le Space (120 s).
_HTTP_REQUEST_TIMEOUT_SECONDS = 120.0


# Fonction qui extrait le chemin d'un fichier renvoyé par Gradio.
def output_file_path(value: Any) -> Path | None:
    """Chemin local d'une sortie fichier Gradio (chaîne ou dict path/value), sinon None."""
    # Sortie sous forme de texte non vide...
    if isinstance(value, str) and value:
        # ...c'est directement le chemin.
        return Path(value)
    # Sortie sous forme de dictionnaire...
    if isinstance(value, dict):
        # ...on cherche le chemin sous l'une de ces clés...
        for key in ("path", "value", "name"):
            # ...la première clé qui contient un texte non vide...
            if isinstance(value.get(key), str) and value[key]:
                # ...donne le chemin.
                return Path(value[key])
    # Rien trouvé : None (l'appelant lèvera une erreur claire).
    return None


# Fournisseur TRELLIS : respecte le contrat Image3DProvider.
class TrellisSpaceProvider:
    """Génère un GLB texturé avec le Space TRELLIS, après détourage de la photo."""

    # Nom lisible du fournisseur.
    label = "TRELLIS"

    # Constructeur avec dépendances remplaçables par les tests.
    def __init__(
        # Configuration (lue dans .env si absente).
        self,
        # Fabrique du client Gradio (faux client dans les tests).
        settings: Settings | None = None,
        # Horloge monotone (fausse horloge dans les tests).
        client_factory: Callable[..., Any] = Client,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Reçoit la configuration, la fabrique de client Gradio et l'horloge.

        client_factory et clock sont remplaçables : les tests y mettent un faux client, sans réseau.
        """
        # Mémorise la configuration, ou la charge.
        self.settings = settings or get_settings()
        # Mémorise la fabrique de client.
        self._client_factory = client_factory
        # Mémorise l'horloge.
        self._clock = clock

    # Méthode principale : photo -> octets GLB.
    def generate(self, image_path: Path) -> bytes:
        """Transforme une photo en GLB texturé avec le Space TRELLIS.

        Paramètre : image_path (photo préparée). Retour : octets d'un GLB 2.0 vérifié.
        Étapes : contrat (view_api), /start_session, /preprocess_image (détourage), /generate_and_extract_glb.
        Lève ProviderError avec un message clair (quota, délai dépassé, Space indisponible).
        """
        # Chemin de la photo préparée.
        source = Path(image_path)
        # Photo absente du disque...
        if not source.is_file():
            # ...erreur claire.
            raise ProviderError("La photo à convertir est introuvable sur le serveur.")
        # Échéance globale : maintenant + HF_TIMEOUT_SECONDS.
        deadline = self._clock() + self.settings.hf_timeout_seconds
        # Essaie toute la génération...
        try:
            # ...dans un dossier temporaire effacé à la fin.
            with TemporaryDirectory(prefix="forma3d-trellis-") as download_dir:
                # Connexion au Space. download_files : dossier où le client range les fichiers reçus.
                # httpx_kwargs : délai de 120 s par requête HTTP (le délai par défaut de 5 s échouait quand le Space était lent).
                # Crée le client connecté au Space...
                client = self._client_factory(
                    # ...identifiant « propriétaire/nom » du Space...
                    self.settings.trellis_space_id,
                    # ...jeton gratuit facultatif (None = anonyme)...
                    token=self.settings.hf_token or None,
                    # ...pas de messages dans la console...
                    verbose=False,
                    # ...pas de télémétrie...
                    analytics_enabled=False,
                    # ...dossier où ranger les fichiers reçus...
                    download_files=download_dir,
                    # ...délai de 120 s par requête HTTP.
                    httpx_kwargs={"timeout": _HTTP_REQUEST_TIMEOUT_SECONDS},
                )
                # Étape 1 : vérifie que les trois fonctions existent toujours.
                self._check_contract(client)
                # Étape 2 : ouvre une session côté Space.
                self._call(client, deadline, api_name="/start_session")
                # Étape 3 : envoie la photo au détourage et récupère le chemin de l'image détourée.
                prepared = output_file_path(
                    self._call(client, deadline, image=handle_file(str(source)), api_name="/preprocess_image")
                )
                # Aucune image détourée...
                if prepared is None:
                    # ...erreur claire.
                    raise ProviderError("Le détourage TRELLIS n'a renvoyé aucune image.")
                # Étape 4 : génère le modèle à partir de l'image détourée...
                result = self._call(
                    # ...fichier à envoyer...
                    client, deadline, image=handle_file(str(prepared)),
                    # ...nom de la fonction, puis les réglages dépliés en arguments nommés.
                    api_name="/generate_and_extract_glb", **GENERATION_SETTINGS,
                )
                # Le GLB est la 3e sortie (index 2), si le résultat est une liste assez longue.
                glb_path = output_file_path(result[2] if isinstance(result, (list, tuple)) and len(result) > 2 else None)
                # Pas de chemin ou fichier absent...
                if glb_path is None or not glb_path.is_file():
                    # ...erreur claire.
                    raise ProviderError("TRELLIS n'a renvoyé aucun fichier GLB.")
                # Vérifie que c'est un vrai GLB 2.0 et renvoie ses octets.
                return HuggingFaceSpaceProvider._read_glb(glb_path)
        # Erreur déjà claire...
        except ProviderError:
            # ...on la laisse passer telle quelle.
            raise
        # Délai dépassé...
        except JobTimeoutError as error:
            # ...message qui indique la durée maximale.
            raise ProviderError(f"La génération TRELLIS a dépassé {self.settings.hf_timeout_seconds} secondes.") from error
        # Toute autre erreur...
        except Exception as error:
            # ...traduite en message lisible, sans jeton.
            raise ProviderError(self._explain(error)) from error

    # Vérifie le contrat réel du Space.
    def _check_contract(self, client: Any) -> None:
        """Vérifie que le Space expose encore les trois fonctions attendues, avant d'envoyer la photo.

        view_api() renvoie la description réelle de l'API ; on n'invente jamais un nom de fonction.
        """
        # Demande au Space la description de ses fonctions, sous forme de dictionnaire.
        description = client.view_api(print_info=False, return_format="dict")
        # Garde les fonctions nommées (dictionnaire vide si la réponse est inattendue).
        endpoints = description.get("named_endpoints", {}) if isinstance(description, dict) else {}
        # Liste des fonctions attendues qui sont absentes.
        missing = [name for name in REQUIRED_FUNCTIONS if name not in endpoints]
        # S'il en manque au moins une...
        if missing:
            # ...on s'arrête avant d'envoyer la photo.
            raise ProviderError(f"Le contrat du Space TRELLIS a changé : fonctions absentes {missing}.")

    # Lance un appel et attend son résultat sans dépasser l'échéance.
    def _call(self, client: Any, deadline: float, **kwargs: Any) -> Any:
        """Soumet un appel et attend son résultat sans dépasser le délai global.

        client.submit lance le travail sans bloquer ; job.result(timeout=...) attend au plus le temps restant.
        Si le délai est dépassé, le travail est annulé côté Space.
        """
        # Temps restant avant l'échéance globale.
        remaining = deadline - self._clock()
        # Plus de temps...
        if remaining <= 0:
            # ...on lève l'erreur de délai.
            raise JobTimeoutError("Délai global atteint.")
        # Lance le travail sur le Space sans bloquer.
        job = client.submit(**kwargs)
        # Essaie d'attendre...
        try:
            # ...le résultat, au plus le temps restant.
            return job.result(timeout=remaining)
        # Si le délai est dépassé...
        except JobTimeoutError:
            # ...on annule le travail côté Space (libère la file d'attente)...
            job.cancel()
            # ...et on relance l'erreur.
            raise

    # Construit un message d'erreur clair.
    def _explain(self, error: Exception) -> str:
        """Message clair, sans jamais recopier le jeton."""
        # Texte de l'erreur d'origine.
        message = str(error)
        # Si un jeton est configuré...
        if self.settings.hf_token:
            # ...on le masque dans le message.
            message = message.replace(self.settings.hf_token, "[jeton masqué]")
        # Si le message parle de quota...
        if "quota" in message.casefold():
            # ...message dédié au quota GPU gratuit.
            return (
                "Quota GPU gratuit du Space TRELLIS atteint pour aujourd'hui. "
                "Réessayez plus tard ; ajoutez un jeton gratuit HF_TOKEN dans backend/.env pour un quota plus élevé."
            )
        # Autre cas : message générique avec le texte d'origine.
        return f"Le Space TRELLIS {self.settings.trellis_space_id} est indisponible ou a refusé la génération : {message}"

    # Contrôle de santé du Space.
    def health_status(self) -> str:
        """ONLINE si le Space est en cours d'exécution ; aucune adresse n'est renvoyée."""
        # URL de l'API Hugging Face qui donne l'état du Space.
        url = f"https://huggingface.co/api/spaces/{quote(self.settings.trellis_space_id, safe='/')}/runtime"
        # En-tête d'authentification, seulement si un jeton est configuré.
        headers = {"Authorization": f"Bearer {self.settings.hf_token}"} if self.settings.hf_token else {}
        # Essaie la requête...
        try:
            # ...GET avec un délai de 5 s...
            response = httpx2.get(url, headers=headers, timeout=_HEALTH_TIMEOUT_SECONDS)
            # ...une réponse d'erreur (404, 500...) devient une exception...
            response.raise_for_status()
            # ...ONLINE si l'état est RUNNING, sinon OFFLINE.
            return "ONLINE" if response.json().get("stage") == "RUNNING" else "OFFLINE"
        # Toute panne...
        except Exception:
            # ...donne simplement OFFLINE.
            return "OFFLINE"

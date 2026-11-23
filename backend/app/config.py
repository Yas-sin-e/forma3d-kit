# Rôle : charge et valide les réglages d'un Space Hugging Face ou d'un serveur Gradio.
# Exécution : appelé à la première génération ; jamais besoin d'un secret pour démarrer l'API.
"""Configuration locale du fournisseur image-vers-3D."""

# math, os, re (standard) : nombres, variables d'environnement (os.getenv), expressions régulières.
import math
import os
import re
# dataclasses (standard) : génère automatiquement constructeur et comparaison d'une classe de données.
# Équivalent d'un record Java ou de Lombok @Value.
from dataclasses import dataclass
# Path : chemins de fichiers (dossier racine, fichiers .env).
from pathlib import Path
# urllib.parse (standard) : découpe une URL en schéma, hôte, chemin, paramètres.
from urllib.parse import urlsplit

# python-dotenv : charge les lignes CLE=valeur d'un fichier .env dans les variables d'environnement.
# Ici : lit backend/.env (secrets locaux, ignoré par Git). Équivalent d'application.properties.
from dotenv import load_dotenv

# Racine du dépôt : backend/app/config.py -> on remonte de deux dossiers.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Motif « propriétaire/nom » d'un Space Hugging Face (jamais une URL).
_SPACE_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*")


# frozen=True : l'objet devient non modifiable après sa création (configuration immuable).
# Décorateur : configuration immuable après sa création.
@dataclass(frozen=True)
# Classe qui regroupe tous les réglages lus dans l'environnement.
class Settings:
    """Réglages d'un Space ou serveur Gradio et des limites d'attente."""

    # Identifiant du Space TripoSR ou URL Gradio (vide = non configuré).
    hf_space_id: str = ""
    # Jeton Hugging Face facultatif (None = appel anonyme).
    hf_token: str | None = None
    # Délai maximal d'une génération, en secondes.
    hf_timeout_seconds: int = 300
    # Nombre de tentatives (1 ou 2).
    hf_max_attempts: int = 2
    # Pause entre deux tentatives, en secondes.
    hf_retry_delay_seconds: float = 5.0
    # Réglage TripoSR facultatif (taille du premier plan).
    foreground_ratio: float | None = None
    # Réglage TripoSR facultatif (résolution du maillage).
    mc_resolution: int | None = None
    # Taille maximale d'un GLB importé, en Mo.
    max_glb_upload_mb: int = 30
    # Quota de créations par jour et par clé API.
    api_daily_generation_limit: int = 20
    # Nombre maximal de requêtes par minute et par clé API.
    api_rate_limit_per_minute: int = 10
    # Sites autorisés à lire l'API depuis un navigateur (CORS), vide par défaut.
    api_cors_origins: tuple[str, ...] = ()
    # Sites autorisés à afficher /embed dans une iframe, vide par défaut.
    embed_allowed_origins: tuple[str, ...] = ()
    # Fournisseur 3D actif : « triposr » (par défaut, HF_SPACE_ID) ou « trellis » (Space public TRELLIS).
    image3d_provider: str = "triposr"
    # Identifiant « propriétaire/nom » du Space TRELLIS.
    trellis_space_id: str = "trellis-community/TRELLIS"

    # Méthode appelée automatiquement juste après le constructeur.
    def __post_init__(self) -> None:
        """Valide la configuration juste après la construction de l'objet.

        Lève ValueError (le serveur refuse alors de démarrer) si une valeur est dangereuse ou
        incohérente : URL avec identifiants, délai nul, fournisseur inconnu, origine « * », etc.
        Une erreur de configuration doit se voir au démarrage, pas au milieu d'une démonstration.
        """
        # Cible du fournisseur TripoSR, sans espaces autour.
        target = self.hf_space_id.strip()
        # Si c'est une URL...
        if "://" in target:
            # ...on la découpe en morceaux.
            parsed = urlsplit(target)
            # Refus si l'un de ces cas est vrai :
            if (
                # schéma autre que http ou https ;
                parsed.scheme.casefold() not in {"http", "https"}
                # pas de nom d'hôte ;
                or not parsed.hostname
                # un nom d'utilisateur dans l'URL ;
                or parsed.username
                # un mot de passe dans l'URL ;
                or parsed.password
                # des paramètres après « ? » ;
                or parsed.query
                # un fragment après « # ».
                or parsed.fragment
            ):
                # Erreur : le serveur refuse de démarrer.
                raise ValueError(
                    "HF_SPACE_ID doit être un identifiant de Space ou une URL HTTP(S) "
                    "sans identifiants, paramètres ni fragment."
                )
        # Délai nul ou négatif...
        if self.hf_timeout_seconds <= 0:
            # ...refusé.
            raise ValueError("HF_TIMEOUT_SECONDS doit être positif.")
        # Nombre de tentatives hors de 1 à 2...
        if self.hf_max_attempts < 1 or self.hf_max_attempts > 2:
            # ...refusé.
            raise ValueError("HF_MAX_ATTEMPTS doit être égal à 1 ou 2.")
        # Pause négative...
        if self.hf_retry_delay_seconds < 0:
            # ...refusée.
            raise ValueError("HF_RETRY_DELAY_SECONDS ne peut pas être négatif.")
        # Réglage présent mais infini ou « NaN »...
        if self.foreground_ratio is not None and not math.isfinite(self.foreground_ratio):
            # ...refusé.
            raise ValueError("FOREGROUND_RATIO doit être un nombre fini.")
        # Résolution présente mais nulle ou négative...
        if self.mc_resolution is not None and self.mc_resolution <= 0:
            # ...refusée.
            raise ValueError("MC_RESOLUTION doit être un entier positif.")
        # Fournisseur inconnu...
        if self.image3d_provider not in {"triposr", "trellis"}:
            # ...refusé.
            raise ValueError("IMAGE3D_PROVIDER doit valoir « triposr » ou « trellis ».")
        # Identifiant TRELLIS qui n'a pas la forme « propriétaire/nom »...
        if not _SPACE_ID_PATTERN.fullmatch(self.trellis_space_id):
            # Un identifiant « propriétaire/nom » garantit que HF_TOKEN n'est envoyé qu'à Hugging Face.
            raise ValueError("TRELLIS_SPACE_ID doit être un identifiant de Space « propriétaire/nom », pas une URL.")
        # Taille d'import hors de 1 à 512 Mo...
        if self.max_glb_upload_mb < 1 or self.max_glb_upload_mb > 512:
            # ...refusée.
            raise ValueError("MAX_GLB_UPLOAD_MB doit être compris entre 1 et 512.")
        # Quota journalier inférieur à 1...
        if self.api_daily_generation_limit < 1:
            # ...refusé.
            raise ValueError("API_DAILY_GENERATION_LIMIT doit être au moins égal à 1.")
        # Limite par minute inférieure à 1...
        if self.api_rate_limit_per_minute < 1:
            # ...refusée.
            raise ValueError("API_RATE_LIMIT_PER_MINUTE doit être au moins égal à 1.")
        # Mêmes règles pour les deux listes d'origines : HTTP(S) précis, sans chemin ni identifiants, jamais « * ».
        # Pour chacune des deux listes d'origines (nom de la variable, valeurs)...
        for setting_name, origins in (
            # ...origines CORS...
            ("API_CORS_ORIGINS", self.api_cors_origins),
            # ...origines d'iframe.
            ("EMBED_ALLOWED_ORIGINS", self.embed_allowed_origins),
        ):
            # Pour chaque origine de la liste...
            for origin in origins:
                # ...on la découpe en morceaux.
                parsed_origin = urlsplit(origin)
                # Essaie de lire le port...
                try:
                    # ...lève une erreur si le port n'est pas un nombre valide.
                    parsed_origin.port
                # Port invalide...
                except ValueError as error:
                    # ...erreur claire.
                    raise ValueError(f"{setting_name} contient un port invalide.") from error
                # Refus si l'un de ces cas est vrai :
                if (
                    # origine vide ;
                    not origin
                    # joker « * » (tout le monde) ;
                    or origin == "*"
                    # schéma autre que http ou https ;
                    or parsed_origin.scheme.casefold() not in {"http", "https"}
                    # pas de nom d'hôte ;
                    or not parsed_origin.hostname
                    # un utilisateur dans l'URL ;
                    or parsed_origin.username
                    # un mot de passe dans l'URL ;
                    or parsed_origin.password
                    # un chemin après l'hôte ;
                    or parsed_origin.path not in {"", "/"}
                    # des paramètres ;
                    or parsed_origin.query
                    # un fragment.
                    or parsed_origin.fragment
                ):
                    # Erreur : le serveur refuse de démarrer.
                    raise ValueError(f"{setting_name} doit contenir des origines HTTP(S) précises, jamais *.")


# Transforme « a, b, a » en tuple d'origines uniques.
def parse_api_cors_origins(value: str) -> tuple[str, ...]:
    """Convertit une liste séparée par des virgules en origines explicites."""
    # Découpe aux virgules, retire espaces et « / » final, ignore les vides, supprime les doublons en gardant l'ordre.
    return tuple(dict.fromkeys(item.strip().rstrip("/") for item in value.split(",") if item.strip()))


# Même transformation pour les origines d'iframe.
def parse_embed_allowed_origins(value: str) -> tuple[str, ...]:
    """Convertit la liste des origines autorisées par CSP frame-ancestors."""
    # Réutilise la fonction précédente.
    return parse_api_cors_origins(value)


# Construit l'objet Settings à partir de l'environnement.
def get_settings() -> Settings:
    """Charge backend/.env en priorité, puis .env racine, sans écraser l'environnement.

    override=False : une variable déjà définie dans le terminal garde la priorité.
    Retour : un objet Settings validé. Lève ValueError si une valeur est invalide.
    """
    # Lit backend/.env sans écraser les variables déjà définies.
    load_dotenv(_PROJECT_ROOT / "backend" / ".env", override=False)
    # Lit ensuite le .env racine, toujours sans écraser.
    load_dotenv(_PROJECT_ROOT / ".env", override=False)
    # Jeton : None s'il est vide.
    token = os.getenv("HF_TOKEN", "").strip() or None
    # Texte brut du réglage FOREGROUND_RATIO.
    foreground_ratio = os.getenv("FOREGROUND_RATIO", "").strip()
    # Texte brut du réglage MC_RESOLUTION.
    mc_resolution = os.getenv("MC_RESOLUTION", "").strip()
    # Crée et renvoie la configuration (validée par __post_init__) :
    return Settings(
        # identifiant du Space ou URL ;
        hf_space_id=os.getenv("HF_SPACE_ID", "").strip(),
        # jeton ;
        hf_token=token,
        # délai converti en entier (300 par défaut) ;
        hf_timeout_seconds=int(os.getenv("HF_TIMEOUT_SECONDS", "300")),
        # nombre de tentatives (2 par défaut) ;
        hf_max_attempts=int(os.getenv("HF_MAX_ATTEMPTS", "2")),
        # pause entre tentatives (5 s par défaut) ;
        hf_retry_delay_seconds=float(os.getenv("HF_RETRY_DELAY_SECONDS", "5")),
        # réglage converti en nombre décimal, ou None ;
        foreground_ratio=float(foreground_ratio) if foreground_ratio else None,
        # réglage converti en entier, ou None ;
        mc_resolution=int(mc_resolution) if mc_resolution else None,
        # taille d'import maximale (30 Mo par défaut) ;
        max_glb_upload_mb=int(os.getenv("MAX_GLB_UPLOAD_MB", "30")),
        # quota journalier (20 par défaut) ;
        api_daily_generation_limit=int(os.getenv("API_DAILY_GENERATION_LIMIT", "20")),
        # limite par minute (10 par défaut) ;
        api_rate_limit_per_minute=int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "10")),
        # origines CORS ;
        api_cors_origins=parse_api_cors_origins(os.getenv("API_CORS_ORIGINS", "")),
        # origines d'iframe ;
        embed_allowed_origins=parse_embed_allowed_origins(os.getenv("EMBED_ALLOWED_ORIGINS", "")),
        # fournisseur en minuscules (« triposr » par défaut) ;
        image3d_provider=os.getenv("IMAGE3D_PROVIDER", "triposr").strip().casefold() or "triposr",
        # identifiant du Space TRELLIS (valeur publique par défaut).
        trellis_space_id=os.getenv("TRELLIS_SPACE_ID", "trellis-community/TRELLIS").strip() or "trellis-community/TRELLIS",
    )

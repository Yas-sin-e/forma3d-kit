# Rôle : écrit et lit les photos et les GLB dans backend/storage/.
# Exécution : GenerationService l'utilise après validation et génération.
"""Stockage local atomique des fichiers d'une génération."""

# Les annotations de type restent du texte.
from __future__ import annotations

# os (standard) : appels système ; ici fsync (forcer l'écriture sur disque) et link.
import os
# Path : manipulation des chemins comme des objets.
from pathlib import Path
# uuid (standard) : UUID(...) vérifie qu'un identifiant a bien la forme d'un UUID.
from uuid import UUID, uuid4

# Extensions de photo acceptées (ensemble : test d'appartenance rapide).
_ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


# Implémentation du contrat Storage sur le disque local.
class LocalStorage:
    """Conserve les fichiers sous un dossier dédié au backend."""

    # Constructeur : root permet aux tests d'utiliser un dossier temporaire.
    def __init__(self, root: Path | None = None) -> None:
        """Fixe les dossiers de stockage : backend/storage/images et backend/storage/models par défaut.

        Paramètre : root, remplacé par un dossier temporaire dans les tests.
        """
        # Dossier par défaut : backend/storage (deux dossiers au-dessus de ce fichier, puis « storage »).
        default_root = Path(__file__).resolve().parents[2] / "storage"
        # Dossier choisi, converti en chemin absolu.
        self.root = (root or default_root).resolve()
        # Sous-dossier des photos.
        self.images_dir = self.root / "images"
        # Sous-dossier des modèles GLB.
        self.models_dir = self.root / "models"

    # Enregistre une photo.
    def save_image(self, generation_id: str, extension: str, content: bytes) -> Path:
        """Écrit une image validée avec un nom choisi par le serveur.

        Paramètres : generation_id (UUID), extension (.jpg, .jpeg, .png, .webp), content (octets).
        Retour : chemin du fichier. Lève ValueError si l'identifiant, l'extension ou le contenu est invalide.
        """
        # Refuse un identifiant qui n'est pas un UUID (protection contre « ../ »).
        self._validate_generation_id(generation_id)
        # Extension en minuscules (.JPG -> .jpg).
        normalized_extension = extension.lower()
        # Extension non autorisée...
        if normalized_extension not in _ALLOWED_IMAGE_EXTENSIONS:
            # ...erreur.
            raise ValueError("Extension d'image non autorisée pour le stockage local.")
        # Contenu vide...
        if not content:
            # ...erreur.
            raise ValueError("Impossible d'enregistrer une image vide.")
        # Nom du fichier choisi par le serveur : images/<uuid>.<extension>.
        destination = self.images_dir / f"{generation_id}{normalized_extension}"
        # Écriture « tout ou rien ».
        self._write_atomically(destination, content)
        # Renvoie le chemin écrit.
        return destination

    # Enregistre un modèle GLB.
    def save_model(self, generation_id: str, content: bytes) -> Path:
        """Écrit le GLB déjà contrôlé par Image3DProvider."""
        # Refuse un identifiant qui n'est pas un UUID.
        self._validate_generation_id(generation_id)
        # Contenu vide...
        if not content:
            # ...erreur.
            raise ValueError("Impossible d'enregistrer un modèle vide.")
        # Nom du fichier : models/<uuid>.glb.
        destination = self.models_dir / f"{generation_id}.glb"
        # Un modèle existe déjà avec cet identifiant...
        if destination.exists():
            # ...on refuse : un GLB terminé n'est jamais écrasé.
            raise FileExistsError("Un modèle portant cet identifiant existe déjà.")
        # Écriture « tout ou rien ».
        self._write_atomically(destination, content)
        # Renvoie le chemin écrit.
        return destination

    # Renvoie le chemin d'un GLB existant.
    def get_model_path(self, generation_id: str) -> Path | None:
        """Retourne le chemin d'un GLB présent sans accepter de chemin client."""
        # Refuse un identifiant qui n'est pas un UUID.
        self._validate_generation_id(generation_id)
        # Chemin reconstruit par le serveur.
        path = self.models_dir / f"{generation_id}.glb"
        # Chemin si c'est un fichier présent, sinon None.
        return path if path.is_file() else None

    # Supprime les fichiers d'une génération.
    def delete_files(self, generation_id: str) -> None:
        """Efface le GLB et la photo source ; les noms sont reconstruits par le serveur, jamais reçus du client."""
        # Refuse un identifiant qui n'est pas un UUID.
        self._validate_generation_id(generation_id)
        # Premier candidat : le GLB.
        candidates = [self.models_dir / f"{generation_id}.glb"]
        # Autres candidats : la photo, pour chaque extension possible (triées pour un ordre stable).
        candidates += [self.images_dir / f"{generation_id}{extension}" for extension in sorted(_ALLOWED_IMAGE_EXTENSIONS)]
        # Pour chaque fichier candidat...
        for path in candidates:
            # ...on le supprime, sans erreur s'il n'existe pas.
            path.unlink(missing_ok=True)

    # Méthode sans self : simple vérification.
    @staticmethod
    # Vérifie qu'un identifiant a la forme d'un UUID.
    def _validate_generation_id(generation_id: str) -> None:
        """Refuse toute valeur qui n'est pas un UUID généré par l'application.

        Sécurité : le nom du fichier est construit à partir de cet identifiant ; un UUID ne peut pas
        contenir « ../ » et ne permet donc pas de sortir du dossier de stockage.
        """
        # Essaie de lire le texte comme un UUID...
        try:
            # ...lève une erreur si la forme est incorrecte.
            UUID(generation_id)
        # Forme incorrecte (ValueError) ou valeur qui n'est pas du texte (AttributeError)...
        except (ValueError, AttributeError) as error:
            # ...erreur claire, avec la cause d'origine conservée.
            raise ValueError("Identifiant de génération invalide.") from error

    # Méthode sans self : simple écriture.
    @staticmethod
    # Écrit un fichier de façon atomique.
    def _write_atomically(destination: Path, content: bytes) -> None:
        """Écrit dans un fichier temporaire du même dossier puis le renomme.

        Écriture « atomique » : le fichier final apparaît complet ou pas du tout, jamais à moitié écrit,
        même si le serveur s'arrête pendant l'écriture.
        """
        # Crée le dossier de destination si besoin (sans erreur s'il existe).
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Fichier temporaire caché dans le même dossier, nom unique grâce à uuid4.
        temporary_path = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
        # Essaie l'écriture...
        try:
            # Mode « xb » : création exclusive en binaire (échoue si le fichier existe déjà).
            # ...ouvre le temporaire en création exclusive binaire...
            with temporary_path.open("xb") as temporary_file:
                # ...écrit les octets...
                temporary_file.write(content)
                # ...vide le tampon de Python vers le système...
                temporary_file.flush()
                # ...force l'écriture physique sur le disque.
                os.fsync(temporary_file.fileno())
            # os.link échoue si la destination existe : on n'écrase jamais un fichier déjà présent.
            # Crée le nom final (lien physique) : échoue si la destination existe déjà.
            os.link(temporary_path, destination)
            # Retire le nom temporaire ; les données restent sous le nom final.
            temporary_path.unlink()
        # En cas d'erreur...
        except Exception:
            # ...on supprime le temporaire s'il existe...
            temporary_path.unlink(missing_ok=True)
            # ...et on relance l'erreur d'origine.
            raise

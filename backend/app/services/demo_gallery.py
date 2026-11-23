# Rôle : ne publie qu'une liste fixe de GLB réels générés pendant la faisabilité.
# Exécution : la route /models/gallery liste ces fichiers et les routes de lecture résolvent leur identifiant.
"""Catalogue borné des modèles GLB de démonstration présents sur le poste."""

# Les annotations de type restent du texte.
from __future__ import annotations

# json (standard) : lit le bloc JSON contenu dans un fichier GLB.
import json
# Classe de données immuable pour un exemple.
from dataclasses import dataclass
# Path : chemins des fichiers d'exemple.
from pathlib import Path

# Liste fixe des exemples : (identifiant, nom, catégorie, fichier GLB, photo source).
_DEMO_FILES = (
    # Chaise en bois cintré.
    ("chair-bentwood", "Chaise en bois cintré", "chair", "chair-bentwood.glb", "chair-bentwood.jpg"),
    # Chaise en métal n° 1.
    ("chair-metal-01", "Chaise métal 01", "chair", "chair-met-01.glb", "chair-met-01.jpg"),
    # Chaise en métal n° 2.
    ("chair-metal-02", "Chaise métal 02", "chair", "chair-met-02.glb", "chair-met-02.jpg"),
    # Table d'appoint en métal.
    ("side-table-metal", "Table d’appoint en métal", "side-table", "side-table-met.glb", "side-table-met.jpg"),
    # Tabouret en métal.
    ("stool-metal-01", "Tabouret métal 01", "stool", "stool-met-01.glb", "stool-met-01.jpg"),
)
# Code du type de chunk « JSON » dans un GLB.
_JSON_CHUNK_TYPE = 0x4E4F534A


# Décorateur : objet immuable limité aux attributs déclarés.
@dataclass(frozen=True, slots=True)
# Métadonnées d'un exemple.
class DemoModel:
    """Métadonnées publiques d'un modèle de faisabilité réellement disponible."""

    # Identifiant de l'exemple.
    id: str
    # Nom affiché.
    name: str
    # Nom du fichier GLB.
    filename: str
    # Slug de la catégorie.
    category: str
    # Source : toujours « example ».
    source: str
    # Taille du fichier en octets.
    size_bytes: int
    # URL de téléchargement du GLB.
    model_url: str
    # URL de la photo source, si elle existe.
    source_image_url: str | None


# Galerie des exemples pré-générés.
class DemoGallery:
    """Résout uniquement les cinq noms connus, sans exposer de chemin arbitraire."""

    # Constructeur : dossier des exemples (dossier temporaire dans les tests).
    def __init__(self, root: Path | None = None) -> None:
        """Fixe le dossier des 5 GLB d'exemple (backend/data/feasibility-results par défaut) et celui des photos source.

        Paramètre : root, remplacé par un dossier temporaire dans les tests.
        """
        # Dossier par défaut : backend/data/feasibility-results.
        default_root = Path(__file__).resolve().parents[2] / "data" / "feasibility-results"
        # Dossier choisi, en chemin absolu.
        self.root = (root or default_root).resolve()
        # Dossier voisin des photos source.
        self.source_images_root = self.root.parent / "feasibility-inputs"

    # Liste les exemples réellement présents et valides.
    def list_models(self) -> list[DemoModel]:
        """Retourne les modèles dont le fichier existe et porte une structure GLB 2.0."""
        # Liste résultat.
        models = []
        # Pour chaque exemple connu...
        for model_id, name, category, filename, source_image in _DEMO_FILES:
            # ...chemin de son GLB...
            path = self.root / filename
            # ...fichier absent ou GLB invalide...
            if not path.is_file() or not self._is_valid_glb_2(path):
                # ...on l'ignore.
                continue
            # Sinon on l'ajoute...
            models.append(
                # ...avec ses métadonnées...
                DemoModel(
                    # ...identifiant...
                    id=model_id,
                    # ...nom...
                    name=name,
                    # ...nom de fichier...
                    filename=filename,
                    # ...catégorie...
                    category=category,
                    # ...source « example »...
                    source="example",
                    # ...taille réelle du fichier...
                    size_bytes=path.stat().st_size,
                    # ...URL du GLB...
                    model_url=f"/models/gallery/{model_id}",
                    # ...URL de la photo...
                    source_image_url=(
                        # ...seulement...
                        f"/models/gallery/{model_id}/source-image"
                        # ...si la photo existe...
                        if (self.source_images_root / source_image).is_file()
                        # ...sinon None.
                        else None
                    ),
                )
            )
        # Renvoie la liste.
        return models

    # Chemin du GLB d'un exemple connu.
    def get_model_path(self, model_id: str) -> Path | None:
        """Renvoie le chemin d'un seul identifiant autorisé si son GLB reste valide."""
        # Cherche l'exemple par identifiant (None s'il n'existe pas).
        entry = next((item for item in _DEMO_FILES if item[0] == model_id), None)
        # Identifiant inconnu...
        if entry is None:
            # ...None.
            return None
        # Chemin du GLB (4e élément de la ligne).
        path = self.root / entry[3]
        # Chemin si le fichier existe et est valide, sinon None.
        return path if path.is_file() and self._is_valid_glb_2(path) else None

    # Chemin de la photo source d'un exemple connu.
    def get_source_image_path(self, model_id: str) -> Path | None:
        """Résout la photo source uniquement pour un modèle connu et une photo présente."""
        # Cherche l'exemple par identifiant.
        entry = next((item for item in _DEMO_FILES if item[0] == model_id), None)
        # Identifiant inconnu...
        if entry is None:
            # ...None.
            return None
        # Chemin absolu de la photo (5e élément).
        path = (self.source_images_root / entry[4]).resolve()
        # Vérifie que le chemin reste dans le dossier des photos...
        try:
            # ...lève une erreur sinon.
            path.relative_to(self.source_images_root.resolve())
        # Hors du dossier...
        except ValueError:
            # ...None.
            return None
        # Chemin si c'est une image présente avec une extension autorisée, sinon None.
        return path if path.is_file() and path.suffix.casefold() in {".jpg", ".jpeg", ".png", ".webp"} else None

    # Méthode sans self : simple vérification.
    @staticmethod
    # Vérifie la structure d'un GLB 2.0 en mémoire.
    def is_valid_glb_2(content: bytes) -> bool:
        """Vérifie en mémoire la structure du conteneur GLB et son document glTF 2.0."""
        # Octets à vérifier.
        data = content
        # Un GLB commence par 12 octets : le mot « glTF », la version (2), la longueur totale.
        # int.from_bytes(..., "little") lit un entier écrit octet de poids faible en premier.
        # Trop court ou pas de « glTF » au début...
        if len(data) < 20 or data[:4] != b"glTF":
            # ...invalide.
            return False
        # Version différente de 2...
        if int.from_bytes(data[4:8], "little") != 2:
            # ...invalide.
            return False
        # Longueur déclarée différente de la taille réelle...
        if int.from_bytes(data[8:12], "little") != len(data):
            # ...invalide (fichier tronqué).
            return False

        # Longueur du bloc JSON.
        json_length = int.from_bytes(data[12:16], "little")
        # Position de fin du bloc JSON.
        json_end = 20 + json_length
        # Refus si :
        if (
            # le premier bloc n'est pas de type JSON ;
            int.from_bytes(data[16:20], "little") != _JSON_CHUNK_TYPE
            # il est vide ;
            or json_length == 0
            # sa longueur n'est pas un multiple de 4 ;
            or json_length % 4 != 0
            # il dépasse la fin du fichier.
            or json_end > len(data)
        ):
            # Invalide.
            return False
        # Essaie de lire le JSON...
        try:
            # ...texte UTF-8 sans les octets de remplissage de fin.
            document = json.loads(data[20:json_end].decode("utf-8").rstrip(" \t\r\n\0"))
        # Texte ou JSON illisible...
        except (UnicodeDecodeError, json.JSONDecodeError):
            # ...invalide.
            return False
        # Pas d'objet « asset »...
        if not isinstance(document, dict) or not isinstance(document.get("asset"), dict):
            # ...invalide.
            return False
        # Version glTF différente de 2.0...
        if document["asset"].get("version") != "2.0":
            # ...invalide.
            return False

        # Position du bloc suivant.
        offset = json_end
        # Parcourt tous les blocs restants...
        while offset < len(data):
            # ...en-tête de bloc tronqué...
            if offset + 8 > len(data):
                # ...invalide.
                return False
            # Longueur du bloc.
            chunk_length = int.from_bytes(data[offset : offset + 4], "little")
            # Longueur non alignée ou bloc qui dépasse le fichier...
            if chunk_length % 4 != 0 or offset + 8 + chunk_length > len(data):
                # ...invalide.
                return False
            # Passe au bloc suivant (8 octets d'en-tête + données).
            offset += 8 + chunk_length
        # Valide seulement si les blocs couvrent exactement le fichier.
        return offset == len(data)

    # Méthode sans self.
    @staticmethod
    # Vérifie un GLB à partir de son chemin.
    def _is_valid_glb_2(path: Path) -> bool:
        """Vérifie l'en-tête, le JSON glTF 2.0 et les limites de chaque chunk."""
        # Essaie de lire le fichier...
        try:
            # ...et de vérifier ses octets.
            return DemoGallery.is_valid_glb_2(path.read_bytes())
        # Fichier illisible...
        except OSError:
            # ...invalide.
            return False

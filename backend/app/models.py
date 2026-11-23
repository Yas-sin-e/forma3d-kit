# Rôle : décrit les catégories et les générations conservées par l'application.
# Exécution : le dépôt PostgreSQL reconstruit ces objets pour GenerationService et les routes.
"""Modèles métier des catégories et des générations image-vers-GLB."""

# dataclasses (standard) : classes de données générées (constructeur, égalité). Équivalent d'un record Java.
# Importe le décorateur qui génère automatiquement __init__, __eq__ et __repr__ d'une classe de données.
from dataclasses import dataclass
# datetime : type des dates de création et de mise à jour.
from datetime import datetime
# enum.StrEnum (standard) : énumération dont chaque valeur est aussi une chaîne (pratique pour SQL et JSON).
# StrEnum : énumération dont chaque membre est aussi une chaîne de caractères.
from enum import StrEnum
# Path : type des chemins de fichiers (photo source, GLB).
from pathlib import Path


# frozen=True : objet immuable ; slots=True : seuls les attributs déclarés existent.
# Pour « modifier » un enregistrement, on en crée une copie avec dataclasses.replace().
# Décorateur : objet immuable (frozen) et limité aux attributs déclarés (slots).
@dataclass(frozen=True, slots=True)
# Déclare la classe qui représente une ligne de la table categories.
class CategoryRecord:
    """Catégorie persistée, éventuellement masquée aux nouveaux uploads."""

    # Identifiant numérique attribué par PostgreSQL (auto-incrément).
    id: int
    # Identifiant technique stable, utilisé dans les URL (ex. « side-table »).
    slug: str
    # Libellé affiché à l'écran, modifiable (ex. « Table d'appoint »).
    label: str
    # Faux = la catégorie est masquée du menu d'envoi, mais reste liée aux anciens modèles.
    is_active: bool
    # Date de création de la catégorie (avec fuseau horaire).
    created_at: datetime


# Machine à états d'un modèle : PENDING -> RUNNING -> DONE ou FAILED.
# Déclare l'énumération des quatre états possibles d'une génération.
class GenerationStatus(StrEnum):
    """États publics du parcours asynchrone de génération."""

    # En attente : la photo est reçue, le travail n'a pas encore commencé.
    PENDING = "PENDING"
    # En cours : le fournisseur 3D est en train de produire le modèle.
    RUNNING = "RUNNING"
    # Terminé : le fichier GLB est enregistré.
    DONE = "DONE"
    # Échoué : error_message explique la cause.
    FAILED = "FAILED"


# Déclare l'énumération de la provenance d'un modèle de la bibliothèque.
class ModelOrigin(StrEnum):
    """Origine persistée d'un modèle visible dans la bibliothèque."""

    # Produit en direct par le fournisseur 3D à partir d'une photo.
    GENERATED = "generated"
    # Fichier GLB importé à la main par la propriétaire.
    IMPORTED = "imported"
    # Copie d'un exemple pré-généré (identifié honnêtement, pas une génération en direct).
    EXAMPLE = "example"


# Déclare les trois catégories historiques du Sprint 1 (utilisées pour remplir la base au départ).
class ProductCategory(StrEnum):
    """Catégories de mobilier prises en charge par le Sprint 1."""

    # Chaise.
    CHAIR = "chair"
    # Tabouret.
    STOOL = "stool"
    # Table d'appoint.
    SIDE_TABLE = "side-table"


# Décorateur : enregistrement immuable ; on le « modifie » avec dataclasses.replace().
@dataclass(frozen=True, slots=True)
# Déclare la classe qui représente une ligne de la table generations.
class GenerationRecord:
    """Métadonnées persistées d'une génération et de ses fichiers locaux."""

    # Identifiant interne (UUID) de suivi, utilisé par le Studio.
    id: str
    # État courant de la génération (PENDING, RUNNING, DONE ou FAILED).
    status: GenerationStatus
    # Nom de fichier affiché, nettoyé (sans chemin local).
    filename: str
    # Type MIME de la photo reçue (image/jpeg, image/png, image/webp).
    content_type: str
    # Slug de la catégorie choisie (texte libre, car les catégories vivent dans PostgreSQL).
    category: str
    # Chemin local de la photo source, ou None (par exemple pour un GLB importé).
    image_path: Path | None
    # Date de création de la génération.
    created_at: datetime
    # Date de la dernière modification (changement d'état, renommage...).
    updated_at: datetime
    # Chemin local du GLB, rempli seulement quand la génération est terminée.
    model_path: Path | None = None
    # Message d'erreur lisible, rempli seulement en cas d'échec.
    error_message: str | None = None
    # Durée de la génération en secondes, connue à la fin.
    duration_seconds: float | None = None
    # Avertissement non bloquant de la préparation photo (petite ou floue).
    image_warning: str | None = None
    # Provenance du modèle ; « généré » par défaut.
    origin: ModelOrigin = ModelOrigin.GENERATED
    # UUID public donné aux sites clients (différent de l'identifiant interne).
    public_id: str | None = None
    # Intégration publique désactivée par défaut (fermée tant que la propriétaire ne l'active pas).
    embed_enabled: bool = False


# Décorateur : métadonnées de clé immuables.
@dataclass(frozen=True, slots=True)
# Déclare la classe qui représente une ligne de la table api_keys (sans le secret).
class APIKeyRecord:
    """Métadonnées persistées d'une clé API sans sa valeur secrète."""

    # Identifiant interne de la clé.
    id: str
    # Nom donné par la propriétaire pour reconnaître la clé.
    name: str
    # Début visible de la clé, pour la retrouver sans révéler le secret.
    prefix: str
    # Hash (empreinte) du secret ; le secret en clair n'est jamais conservé.
    fingerprint: str
    # Date de création de la clé.
    created_at: datetime
    # Vrai = clé révoquée (désactivée), refusée par l'API.
    revoked: bool = False

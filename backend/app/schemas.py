# Rôle : définit le contrat JSON renvoyé par les routes du backend.
# Exécution : FastAPI valide et sérialise ce schéma lors de chaque réponse.
"""Schémas des réponses HTTP de Forma3D Studio."""

# datetime : Pydantic convertit ces dates en texte ISO 8601 dans le JSON.
from datetime import datetime
# typing.Literal (standard) : limite un champ à une liste de valeurs exactes.
from typing import Literal

# Pydantic : valide et convertit les données JSON à partir de classes Python.
# Ici : ce sont les DTO (objets de transfert) de l'API ; FastAPI répond 422 si un JSON reçu
# ne respecte pas la classe. Équivalent des DTO + Bean Validation (@Valid) de Spring.
from pydantic import BaseModel, ConfigDict, Field


# Réponse JSON d'une génération, renvoyée au Studio.
class GenerationResponse(BaseModel):
    """État public d'un travail de génération image-vers-GLB."""

    # Identifiant interne de la génération.
    id: str = Field(description="Identifiant de suivi créé par le serveur.")
    # État : seules ces quatre valeurs sont acceptées.
    status: Literal["PENDING", "RUNNING", "DONE", "FAILED"]
    # Nom de fichier affiché.
    filename: str = Field(description="Nom de fichier nettoyé, sans chemin local.")
    # Type MIME de la photo d'origine.
    content_type: str
    # Slug de la catégorie.
    category: str = Field(description="Slug de la catégorie choisie avant l'envoi de la photo.")
    # Date de création.
    created_at: datetime
    # Date de dernière modification.
    updated_at: datetime
    # URL à interroger pour suivre l'avancement.
    status_url: str
    # URL du GLB, absente tant que le modèle n'est pas terminé.
    model_url: str | None = None
    # Message d'erreur, présent seulement en cas d'échec.
    error_message: str | None = None
    # Durée de génération en secondes.
    duration_seconds: float | None = None
    # Avertissement de préparation photo, facultatif...
    image_warning: str | None = Field(
        # ...valeur par défaut : aucun avertissement...
        default=None,
        # ...texte affiché dans la documentation /docs.
        description="Avertissement non bloquant issu de la préparation locale de la photo.",
    )
    # Provenance du modèle, « generated » par défaut.
    origin: Literal["generated", "imported", "example"] = "generated"
    # UUID public, présent une fois le modèle terminé.
    public_id: str | None = None
    # Intégration désactivée par défaut.
    embed_enabled: bool = False


# Réponse JSON d'un modèle de la galerie.
class DemoModelResponse(BaseModel):
    """Modèle de faisabilité consultable dans la galerie du viewer."""

    # from_attributes=True : Pydantic peut lire directement les attributs d'un objet métier (dataclass).
    # Autorise la lecture d'un objet Python (dataclass) en plus d'un dictionnaire.
    model_config = ConfigDict(from_attributes=True)

    # Identifiant du modèle dans la galerie.
    id: str
    # Nom affiché.
    name: str
    # Nom du fichier GLB.
    filename: str
    # Slug de la catégorie.
    category: str
    # Source affichée : généré par l'application, importé ou exemple.
    source: Literal["generated_by_app", "imported", "example"]
    # Provenance enregistrée, « example » par défaut.
    origin: Literal["generated", "imported", "example"] = "example"
    # Date de création, inconnue pour certains exemples.
    created_at: datetime | None = None
    # Taille du fichier GLB en octets.
    size_bytes: int
    # URL de téléchargement du GLB.
    model_url: str
    # URL de la photo source, si elle existe.
    source_image_url: str | None = None
    # UUID public, si attribué.
    public_id: str | None = None
    # État de l'intégration publique.
    embed_enabled: bool = False


# Corps JSON reçu pour activer ou désactiver l'intégration.
class EmbedIntegrationRequest(BaseModel):
    """Demande d'activation ou de désactivation pour une fiche terminée."""

    # Vrai = activer, faux = désactiver.
    enabled: bool


# Corps JSON reçu pour renommer un modèle.
class ModelRenameRequest(BaseModel):
    """Nouveau nom affiché d'un modèle du Studio (l'extension d'origine est conservée)."""

    # Nouveau nom : 1 à 80 caractères, sinon réponse 422 automatique.
    name: str = Field(min_length=1, max_length=80, description="Nouveau nom, 1 à 80 caractères.")


# Corps JSON reçu pour changer la catégorie d'un modèle.
class ModelCategoryRequest(BaseModel):
    """Nouvelle catégorie d'un modèle du Studio, désignée par son slug."""

    # Slug de la nouvelle catégorie : 1 à 80 caractères.
    category: str = Field(min_length=1, max_length=80, description="Slug d'une catégorie active.")


# Réponse publique minimale d'un modèle activé (aucun détail interne).
class PublicModelResponse(BaseModel):
    """Métadonnées minimales exposées lorsque l'intégration est activée."""

    # UUID public du modèle.
    public_id: str
    # Nom affiché.
    name: str
    # Nom du fichier GLB.
    filename: str
    # Slug de la catégorie.
    category: str
    # Provenance du modèle.
    origin: Literal["generated", "imported", "example"]
    # Date de création.
    created_at: datetime
    # URL publique du GLB.
    model_url: str


# Réponse JSON de la galerie complète.
class DemoGalleryResponse(BaseModel):
    """Liste des fichiers GLB réels connus et valides sur ce poste."""

    # Liste des modèles, enveloppée dans « items » pour pouvoir ajouter des champs plus tard.
    items: list[DemoModelResponse]


# Réponse JSON d'une catégorie.
class CategoryResponse(BaseModel):
    """Catégorie partagée exposée au formulaire et à la gestion."""

    # Autorise la lecture directe d'un CategoryRecord.
    model_config = ConfigDict(from_attributes=True)

    # Identifiant numérique.
    id: int
    # Slug technique.
    slug: str
    # Libellé affiché.
    label: str
    # Active ou désactivée.
    is_active: bool
    # Date de création.
    created_at: datetime


# Réponse JSON d'une liste de catégories.
class CategoryListResponse(BaseModel):
    """Liste de catégories retournée par l'API."""

    # Liste enveloppée dans « items ».
    items: list[CategoryResponse]


# Corps JSON reçu pour créer une catégorie.
class CategoryCreateRequest(BaseModel):
    """Valeurs à fournir pour créer une catégorie."""

    # Slug obligatoire (vérifié ensuite par CategoryService).
    slug: str
    # Libellé obligatoire.
    label: str


# Corps JSON reçu pour modifier une catégorie (PATCH : seulement les champs envoyés).
class CategoryUpdateRequest(BaseModel):
    """Champs facultatifs modifiables sur une catégorie existante."""

    # Nouveau slug, ou None pour ne pas le changer.
    slug: str | None = None
    # Nouveau libellé, ou None pour ne pas le changer.
    label: str | None = None
    # Nouvel état, ou None pour ne pas le changer.
    is_active: bool | None = None


# Corps JSON reçu pour créer une clé API.
class APIKeyCreateRequest(BaseModel):
    """Nom donné par la propriétaire à une nouvelle clé API."""

    # Field(...) ajoute des contraintes : ici 1 à 80 caractères, sinon réponse 422 automatique.
    # Nom de la clé : 1 à 80 caractères.
    name: str = Field(min_length=1, max_length=80)


# Réponse JSON d'une clé API, sans secret ni empreinte.
class APIKeyResponse(BaseModel):
    """Métadonnées d’une clé sans sa valeur secrète ni son empreinte."""

    # Identifiant de la clé.
    id: str
    # Nom donné par la propriétaire.
    name: str
    # Début visible de la clé.
    prefix: str
    # Date de création.
    created_at: datetime
    # Vrai si la clé est révoquée.
    revoked: bool


# Hérite de APIKeyResponse et ajoute le secret : utilisé uniquement à la création.
class APIKeyCreatedResponse(APIKeyResponse):
    """Réponse de création contenant le secret, qui n’est renvoyé qu’ici."""

    # Le secret complet, montré une seule fois.
    key: str


# Réponse JSON de la liste des clés.
class APIKeyListResponse(BaseModel):
    """Collection des clés connues pour la page de gestion du Studio."""

    # Liste enveloppée dans « items » (sans secret).
    items: list[APIKeyResponse]


# Réponse JSON d'un modèle pour l'API externe /api/v1.
class APIModelResponse(BaseModel):
    """État d'un modèle visible par une clé API, avec des URL versionnées."""

    # Identifiant du modèle.
    id: str
    # État de la génération.
    status: Literal["PENDING", "RUNNING", "DONE", "FAILED"]
    # Nom de fichier affiché.
    filename: str
    # Slug de la catégorie.
    category: str
    # Date de création.
    created_at: datetime
    # Date de dernière modification.
    updated_at: datetime
    # URL versionnée de suivi (/api/v1/...).
    status_url: str
    # URL versionnée du GLB, quand il est prêt.
    model_url: str | None = None
    # Message d'erreur en cas d'échec.
    error_message: str | None = None
    # Durée de génération.
    duration_seconds: float | None = None
    # UUID public, s'il existe.
    public_id: str | None = None
    # Intégration activée ou non.
    embed_enabled: bool = False


# Réponse JSON du code d'intégration à copier.
class APIIntegrationCodeResponse(BaseModel):
    """Code iframe prêt à copier pour un modèle déjà activé."""

    # UUID public du modèle.
    public_id: str
    # Code <iframe> prêt à coller dans une page.
    iframe_html: str
    # Code du composant Web <forma3d-viewer> prêt à coller.
    widget_html: str

# Rôle : orchestre les états de génération via un dépôt persistant et le stockage de fichiers.
# Exécution : les routes lancent run() comme tâche de fond après un upload validé.
"""Service de génération indépendant du fournisseur et du dépôt de métadonnées."""

# Les annotations de type restent du texte.
from __future__ import annotations

# logging (standard) : journal du serveur. On y écrit le diagnostic d'un échec, jamais un secret.
import logging
# re : expressions régulières pour nettoyer un titre importé.
import re
# tempfile (standard) : dossier temporaire effacé automatiquement (pour la copie préparée de la photo).
import tempfile
# dataclasses.replace : crée une COPIE modifiée d'un objet immuable (frozen).
from dataclasses import replace
# UTC et datetime : dates de création et de mise à jour.
from datetime import UTC, datetime
# Path : chemins des fichiers.
from pathlib import Path
# threading.RLock (standard) : verrou réentrant. Une seule lecture-écriture à la fois entre la requête HTTP
# et la tâche de fond. Équivalent de synchronized en Java.
from threading import RLock
# time.monotonic (standard) : horloge qui ne recule jamais, pour mesurer une durée.
from time import monotonic
# uuid4 : identifiant aléatoire d'une nouvelle génération.
from uuid import uuid4

# Objets métier et énumérations.
from app.models import GenerationRecord, GenerationStatus, ModelOrigin
# Contrat du fournisseur et son erreur commune.
from app.providers.base import Image3DProvider, ProviderError
# Contrat du dépôt.
from app.repositories.base import GenerationRepository
# Résultat de la validation d'une photo.
from app.services.upload_validator import ValidatedUpload
# Préparation locale de la photo et son erreur.
from app.services.image_preparer import ImagePreparer, ImagePreparationError
# Contrat du stockage de fichiers.
from app.storage.base import Storage
# Réutilisée pour vérifier qu'un fichier est un GLB 2.0 valide.
from app.services.demo_gallery import DemoGallery
# Ajoute un matériau mat et des normales à un GLB généré.
from app.services.glb_finisher import finish_glb

# Journal de ce module.
logger = logging.getLogger(__name__)

# Longueur maximale d'un nom de modèle choisi dans le Studio (même borne que ModelRenameRequest).
MAX_MODEL_NAME_LENGTH = 80


# Service qui orchestre toute la vie d'une génération.
class GenerationService:
    """Coordonne le fournisseur, les fichiers locaux et l'historique persistant."""

    # Constructeur : reçoit ses dépendances.
    def __init__(
        # Le service lui-même.
        self,
        # Fournisseur 3D (TripoSR ou TRELLIS).
        provider: Image3DProvider,
        # Stockage des fichiers.
        storage: Storage,
        # Dépôt des métadonnées.
        repository: GenerationRepository,
        # Préparateur de photo (un par défaut).
        image_preparer: ImagePreparer | None = None,
    ) -> None:
        """Reçoit ses dépendances par le constructeur : fournisseur 3D, stockage, dépôt, préparateur d'image.

        Chacune est une interface (Protocol) : on peut changer de fournisseur ou de base sans modifier ce service.
        """
        # Mémorise le fournisseur.
        self._provider = provider
        # Mémorise le stockage.
        self._storage = storage
        # Mémorise le dépôt.
        self._repository = repository
        # Préparateur fourni, ou un nouveau par défaut.
        self._image_preparer = image_preparer or ImagePreparer()
        # Verrou réentrant partagé entre la requête et la tâche de fond.
        self._lock = RLock()

    # Crée une génération PENDING à partir d'une photo validée.
    def create_generation(
        # Le service lui-même.
        self,
        # Métadonnées validées de la photo.
        upload: ValidatedUpload,
        # Octets de la photo.
        content: bytes,
        # Slug de la catégorie choisie.
        category: str,
    ) -> GenerationRecord:
        """Enregistre l'image et sa catégorie, puis initialise PENDING.

        Paramètres : upload (métadonnées validées), content (octets de la photo), category (slug).
        Retour : l'enregistrement PENDING. Lève ValueError si la catégorie est inconnue ou désactivée.
        """
        # Slug en texte (accepte une énumération ou un texte).
        category_slug = str(getattr(category, "value", category))
        # Catégorie inconnue ou désactivée...
        if self._repository.get_category(category_slug) is None:
            # ...erreur (la route répondra 422).
            raise ValueError("Cette catégorie est inconnue ou désactivée.")
        # Nouvel identifiant aléatoire.
        generation_id = str(uuid4())
        # Extension du fichier en minuscules (.jpg, .png...).
        extension = Path(upload.filename).suffix.lower()
        # Enregistre la photo sur le disque.
        image_path = self._storage.save_image(generation_id, extension, content)
        # Instant présent.
        now = datetime.now(UTC)
        # Construit l'enregistrement initial...
        record = GenerationRecord(
            # ...identifiant...
            id=generation_id,
            # ...état PENDING...
            status=GenerationStatus.PENDING,
            # ...nom de fichier nettoyé...
            filename=upload.filename,
            # ...type MIME vérifié...
            content_type=upload.content_type,
            # ...catégorie...
            category=category_slug,
            # ...chemin de la photo...
            image_path=image_path,
            # ...date de création...
            created_at=now,
            # ...date de mise à jour...
            updated_at=now,
            # ...provenance : générée.
            origin=ModelOrigin.GENERATED,
        )
        # Prend le verrou...
        with self._lock:
            # ...enregistre la génération en base.
            self._repository.save_generation(record)
        # Renvoie l'enregistrement PENDING.
        return record

    # Lit une génération.
    def get_generation(self, generation_id: str) -> GenerationRecord | None:
        """Retourne l'état courant d'une génération connue."""
        # Prend le verrou...
        with self._lock:
            # ...lit dans le dépôt.
            return self._repository.get_generation(generation_id)

    # Lit une génération par UUID public.
    def get_generation_by_public_id(self, public_id: str) -> GenerationRecord | None:
        """Retourne un modèle via son identifiant public d'intégration."""
        # Prend le verrou...
        with self._lock:
            # ...lit dans le dépôt.
            return self._repository.get_generation_by_public_id(public_id)

    # Active ou désactive l'intégration publique.
    def set_integration_enabled(
        # Le service lui-même.
        self,
        # Identifiant du modèle.
        generation_id: str,
        # Vrai = activer.
        enabled: bool,
    ) -> GenerationRecord | None:
        """Change l'autorisation publique d'un modèle DONE dont le GLB existe.

        Retour : l'enregistrement mis à jour, ou None si l'identifiant est inconnu.
        Lève ValueError si le modèle n'est pas terminé (on ne publie jamais un modèle incomplet).
        """
        # Prend le verrou...
        with self._lock:
            # ...lit la génération...
            record = self._repository.get_generation(generation_id)
            # ...inconnue...
            if record is None:
                # ...None (404).
                return None
            # Pas terminée ou GLB absent...
            if record.status is not GenerationStatus.DONE or self.get_model_path(generation_id) is None:
                # ...refus.
                raise ValueError("Seuls les modèles terminés avec un GLB disponible peuvent être intégrés.")
            # Délègue au dépôt.
            return self._repository.set_embed_enabled(generation_id, enabled)

    # Renomme un modèle.
    def rename_generation(self, generation_id: str, name: str) -> GenerationRecord | None:
        """Renomme un modèle du Studio : seul le nom affiché change, l'extension d'origine est gardée.

        Retour : l'enregistrement mis à jour, ou None si l'identifiant est inconnu.
        Lève ValueError si le nom est vide, trop long ou contient un séparateur de chemin.
        """
        cleaned = " ".join(name.split())  # espaces multiples, tabulations et retours à la ligne -> un espace
        # Nom saisi...
        if not cleaned:
            # ...vide : erreur.
            raise ValueError("Le nom ne peut pas être vide.")
        # Nom trop long...
        if len(cleaned) > MAX_MODEL_NAME_LENGTH:
            # ...erreur.
            raise ValueError(f"Le nom ne doit pas dépasser {MAX_MODEL_NAME_LENGTH} caractères.")
        # Nom avec « / » ou « \ »...
        if "/" in cleaned or "\\" in cleaned:
            # ...erreur.
            raise ValueError("Le nom ne doit pas contenir de « / » ni de « \\ ».")
        # Prend le verrou...
        with self._lock:
            # ...lit la génération...
            record = self._repository.get_generation(generation_id)
            # ...inconnue...
            if record is None:
                # ...None (404).
                return None
            # La galerie affiche Path(filename).stem : on garde donc l'extension (.png, .glb…) d'origine.
            # Enregistre le nouveau nom suivi de l'extension d'origine.
            return self._repository.rename_generation(generation_id, cleaned + Path(record.filename).suffix)

    # Change la catégorie d'un modèle.
    def change_category(self, generation_id: str, category: str) -> GenerationRecord | None:
        """Déplace un modèle du Studio vers une autre catégorie active.

        Retour : l'enregistrement mis à jour, ou None si l'identifiant est inconnu.
        Lève ValueError si la catégorie est inconnue ou désactivée (même règle qu'à l'envoi).
        """
        # Slug sans espaces autour.
        category_slug = category.strip()
        # Catégorie inconnue ou désactivée...
        if self._repository.get_category(category_slug) is None:
            # ...erreur.
            raise ValueError("Cette catégorie est inconnue ou désactivée.")
        # Prend le verrou...
        with self._lock:
            # ...génération inconnue...
            if self._repository.get_generation(generation_id) is None:
                # ...None (404).
                return None
            # Délègue au dépôt.
            return self._repository.set_generation_category(generation_id, category_slug)

    # Supprime un modèle et ses fichiers.
    def delete_generation(self, generation_id: str) -> bool:
        """Supprime définitivement une génération terminée ou échouée, puis ses fichiers.

        Renvoie False si l'identifiant est inconnu. Une génération PENDING ou RUNNING est refusée :
        la tâche de fond écrirait sinon un GLB pour une ligne disparue.
        """
        # Prend le verrou...
        with self._lock:
            # ...lit la génération...
            record = self._repository.get_generation(generation_id)
            # ...inconnue...
            if record is None:
                # ...faux (404).
                return False
            # Encore en attente ou en cours...
            if record.status in {GenerationStatus.PENDING, GenerationStatus.RUNNING}:
                # ...refus.
                raise ValueError("Ce modèle est encore en cours de création ; attendez la fin avant de le supprimer.")
            # Supprime la ligne en base.
            self._repository.delete_generation(generation_id)
        # La ligne est retirée d'abord : le modèle disparaît du Studio et de /embed même si un fichier résiste.
        # Supprime ensuite les fichiers (photo et GLB).
        self._storage.delete_files(generation_id)
        # Suppression réussie.
        return True

    # Chemin du GLB d'un modèle terminé.
    def get_model_path(self, generation_id: str) -> Path | None:
        """Retourne uniquement un modèle lié à une génération DONE."""
        # Lit la génération.
        record = self.get_generation(generation_id)
        # Refus si :
        if (
            # elle est inconnue ;
            record is None
            # elle n'est pas terminée ;
            or record.status is not GenerationStatus.DONE
            # elle n'a pas de chemin de GLB ;
            or record.model_path is None
            # le fichier n'existe plus.
            or not record.model_path.is_file()
        ):
            # Dans ces cas : None.
            return None
        # Chemin donné par le stockage.
        model_path = self._storage.get_model_path(generation_id)
        # Renvoyé seulement s'il correspond au chemin enregistré et existe.
        return model_path if model_path == record.model_path and model_path.is_file() else None

    # Chemin de la photo source d'un modèle terminé.
    def get_source_image_path(self, generation_id: str) -> Path | None:
        """Retourne la photo source locale d'une génération réellement terminée."""
        # Lit la génération.
        record = self.get_generation(generation_id)
        # Inconnue ou pas terminée...
        if record is None or record.status is not GenerationStatus.DONE:
            # ...None.
            return None
        # Photo si elle existe sur le disque, sinon None.
        return record.image_path if record.image_path is not None and record.image_path.is_file() else None

    # Liste les modèles terminés.
    def list_completed_generations(self) -> list[GenerationRecord]:
        """Liste les générations persistées terminées, de la plus récente à l'ancienne."""
        # Prend le verrou...
        with self._lock:
            # ...lit les modèles terminés.
            records = self._repository.list_completed_generations()
        # Garde seulement...
        return [
            # ...chaque modèle...
            record
            # ...de la liste...
            for record in records
            # ...qui a un chemin de GLB...
            if record.model_path is not None
            # ...dont le fichier existe...
            and record.model_path.is_file()
            # ...et, s'il a été généré depuis une photo...
            and (record.origin is not ModelOrigin.GENERATED or (
                # ...dont la photo source existe aussi.
                record.image_path is not None and record.image_path.is_file()
            ))
        ]

    # Méthode sans self : simple nettoyage de texte.
    @staticmethod
    # Nettoie le titre d'un GLB importé.
    def _clean_model_title(title: str, filename: str) -> str:
        """Nettoie un titre importé sans conserver de chemin ou de caractère de contrôle."""
        # Titre saisi sans espaces autour.
        candidate = title.strip()
        # Pas de titre...
        if not candidate:
            # ...on le fabrique depuis le nom de fichier (points, tirets et soulignés -> espaces).
            candidate = re.sub(r"[._-]+", " ", Path(filename.replace("\\", "/")).stem)
        # Sinon...
        else:
            # ...on retire une éventuelle extension.
            candidate = Path(candidate).stem
        # Remplace les caractères interdits dans un nom de fichier par des espaces.
        candidate = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", " ", candidate)
        # Espaces multiples -> un seul, puis 100 caractères maximum.
        candidate = " ".join(candidate.split())[:100].strip()
        # Titre vide après nettoyage...
        if not candidate:
            # ...erreur.
            raise ValueError("Le titre du modèle ne peut pas être vide.")
        # Renvoie le titre propre.
        return candidate

    # Ajoute un GLB importé ou un exemple copié à la bibliothèque.
    def create_library_model(
        # Le service lui-même.
        self,
        # Tous les arguments suivants doivent être nommés.
        *,
        # Octets du GLB.
        content: bytes,
        # Titre saisi.
        title: str,
        # Nom du fichier envoyé.
        filename: str,
        # Slug de la catégorie.
        category: str,
        # Provenance : importé ou exemple.
        origin: ModelOrigin,
        # Taille maximale autorisée.
        max_upload_bytes: int,
    ) -> GenerationRecord:
        """Valide et persiste un GLB importé ou copié dans la bibliothèque du vendeur."""
        # GLB vide...
        if not content:
            # ...erreur.
            raise ValueError("Le fichier GLB est vide.")
        # Trop gros...
        if len(content) > max_upload_bytes:
            # ...erreur.
            raise ValueError("Le fichier dépasse la taille maximale autorisée.")
        # Pas un GLB 2.0 valide...
        if not DemoGallery.is_valid_glb_2(content):
            # ...erreur.
            raise ValueError("Le fichier n'est pas un modèle GLB 2.0 valide.")
        # Slug de catégorie sans espaces.
        category_slug = str(getattr(category, "value", category)).strip()
        # Catégorie inconnue ou désactivée...
        if self._repository.get_category(category_slug) is None:
            # ...erreur.
            raise ValueError("Cette catégorie est inconnue ou désactivée.")
        # Provenance non autorisée ici...
        if origin not in {ModelOrigin.IMPORTED, ModelOrigin.EXAMPLE}:
            # ...erreur.
            raise ValueError("L'origine du modèle est invalide.")

        # Titre nettoyé.
        clean_title = self._clean_model_title(title, filename)
        # Nouvel identifiant.
        model_id = str(uuid4())
        # Enregistre le GLB sur le disque.
        model_path = self._storage.save_model(model_id, content)
        # Instant présent.
        now = datetime.now(UTC)
        # Construit l'enregistrement...
        record = GenerationRecord(
            # ...identifiant...
            id=model_id,
            # ...directement terminé...
            status=GenerationStatus.DONE,
            # ...nom affiché avec l'extension .glb...
            filename=f"{clean_title}.glb",
            # ...type MIME d'un GLB...
            content_type="model/gltf-binary",
            # ...catégorie...
            category=category_slug,
            # ...pas de photo source...
            image_path=None,
            # ...date de création...
            created_at=now,
            # ...date de mise à jour...
            updated_at=now,
            # ...chemin du GLB...
            model_path=model_path,
            # ...provenance.
            origin=origin,
        )
        # Prend le verrou...
        with self._lock:
            # ...enregistre en base...
            self._repository.save_generation(record)
            # ...puis relit la ligne (avec son UUID public).
            persisted = self._repository.get_generation(model_id)
        # Renvoie la ligne relue, ou l'enregistrement si la relecture échoue.
        return persisted or record

    # Méthode sans self.
    @staticmethod
    # Améliore un GLB généré.
    def _finish_generated_model(model_bytes: bytes) -> bytes:
        """Ajoute matériau mat et normales au GLB généré ; garde l'original si le résultat n'est pas valide."""
        # Renvoie le GLB modifié et un rapport des ajouts.
        finished, report = finish_glb(model_bytes)
        # Si quelque chose a changé et que le résultat reste valide...
        if report.changed and DemoGallery.is_valid_glb_2(finished):
            # ...on journalise les ajouts...
            logger.info(
                "GLB complété : %s normale(s), %s matériau(x) ajoutés.",
                report.normals_added,
                report.materials_added,
            )
            # ...et on garde la version complétée.
            return finished
        # Sinon on garde le GLB d'origine.
        return model_bytes

    # Exécute la génération en tâche de fond.
    def run(self, generation_id: str) -> None:
        """Exécute le fournisseur et publie DONE ou FAILED de façon atomique.

        Appelée en tâche de fond après la réponse 202. Étapes : PENDING -> RUNNING, préparation de la photo,
        appel du fournisseur, finition du GLB, écriture du fichier, puis DONE.
        Toute erreur donne FAILED avec un message sans secret (jeton et adresse masqués).
        """
        # Démarre le chronomètre.
        started_at = monotonic()
        # Prend le verrou...
        with self._lock:
            # ...lit la génération...
            record = self._repository.get_generation(generation_id)
            # ...inconnue ou déjà traitée...
            if record is None or record.status is not GenerationStatus.PENDING:
                # ...on ne fait rien.
                return
            # L'enregistrement est immuable : replace() en crée une copie avec le nouveau statut.
            # Copie avec l'état RUNNING...
            running_record = replace(
                # ...à partir de l'enregistrement actuel...
                record,
                # ...nouvel état...
                status=GenerationStatus.RUNNING,
                # ...nouvelle date.
                updated_at=datetime.now(UTC),
            )
            # Enregistre l'état RUNNING.
            self._repository.save_generation(running_record)

        # Essaie toute la génération...
        try:
            # ...dans un dossier temporaire effacé à la fin.
            with tempfile.TemporaryDirectory(prefix="forma3d-photo-") as temporary_directory:
                # Chemin de la copie préparée.
                prepared_path = Path(temporary_directory) / "prepared.png"
                # Par défaut, on enverra la photo originale.
                provider_image_path = running_record.image_path
                # Essaie de préparer la photo...
                try:
                    # ...avec le préparateur...
                    preparation = self._image_preparer.prepare(
                        # ...photo d'origine...
                        running_record.image_path,
                        # ...destination de la copie.
                        prepared_path,
                    )
                    # Succès : on enverra la copie préparée...
                    provider_image_path = preparation.prepared_path
                    # ...et on garde l'avertissement éventuel.
                    image_warning = preparation.warning
                # Échec de la préparation...
                except ImagePreparationError:
                    # ...avertissement : la photo originale sera envoyée.
                    image_warning = (
                        "La photo n'a pas pu être préparée localement ; la photo originale sera envoyée. "
                        "Vérifiez qu'il s'agit d'une image JPG, PNG ou WebP lisible."
                    )
                # Copie avec l'avertissement...
                running_record = replace(
                    # ...à partir de l'état RUNNING...
                    running_record,
                    # ...avertissement...
                    image_warning=image_warning,
                    # ...nouvelle date.
                    updated_at=datetime.now(UTC),
                )
                # Prend le verrou...
                with self._lock:
                    # ...enregistre l'avertissement.
                    self._repository.save_generation(running_record)
                # Appel du fournisseur (TripoSR ou TRELLIS) : peut durer 1 à 2 minutes. Aucun verrou n'est tenu
                # ici, pour ne pas bloquer les autres requêtes pendant la génération.
                # Appelle le fournisseur, puis complète le GLB.
                model_bytes = self._finish_generated_model(self._provider.generate(provider_image_path))
                # Enregistre le GLB sur le disque.
                model_path = self._storage.save_model(generation_id, model_bytes)
        # Erreur du fournisseur...
        except ProviderError as error:
            # ...lit la configuration du fournisseur si elle existe...
            provider_settings = getattr(self._provider, "settings", None)
            # ...valeurs à ne jamais exposer...
            protected_values = (
                # ...le jeton...
                getattr(provider_settings, "hf_token", None),
                # ...l'adresse du serveur 3D.
                getattr(provider_settings, "hf_space_id", None),
            )

            # Sécurité : le jeton HF et l'adresse du serveur 3D sont remplacés avant d'écrire ou d'afficher une erreur.
            # Fonction locale qui masque ces valeurs dans un texte.
            def redact(text: str) -> str:
                """Masque le jeton et l'adresse configurée avant toute exposition."""
                # Pour chaque valeur protégée...
                for protected_value in protected_values:
                    # ...si elle est renseignée...
                    if isinstance(protected_value, str) and protected_value:
                        # ...on la remplace.
                        text = text.replace(protected_value, "[valeur masquée]")
                # Renvoie le texte masqué.
                return text

            # Fonction locale : représentation technique masquée.
            def safe_repr(value: object) -> str:
                """Masque le jeton et l'adresse temporaire dans les diagnostics locaux."""
                # Masque repr() de la valeur.
                return redact(repr(value))

            # Copie avec l'état FAILED...
            failed_record = replace(
                # ...à partir de l'état RUNNING...
                running_record,
                # ...état échoué...
                status=GenerationStatus.FAILED,
                # ...nouvelle date...
                updated_at=datetime.now(UTC),
                # ...message d'erreur masqué...
                error_message=redact(str(error)),
                # ...durée écoulée (jamais négative).
                duration_seconds=max(0.0, monotonic() - started_at),
            )

            # Cause technique de l'erreur.
            cause = error.__cause__
            # Cause de la cause, si elle existe.
            nested_cause = cause.__cause__ if cause is not None else None
            # Journalise le diagnostic, masqué...
            logger.warning(
                # ...texte du message (anglais, pour le journal)...
                "Generation %s failed in image provider: error_type=%s error_repr=%s "
                "cause_type=%s cause_repr=%s nested_cause_repr=%s",
                # ...identifiant...
                generation_id,
                # ...type de l'erreur...
                type(error).__name__,
                # ...erreur masquée...
                safe_repr(error),
                # ...type de la cause...
                type(cause).__name__ if cause is not None else None,
                # ...cause masquée...
                safe_repr(cause) if cause is not None else None,
                # ...cause imbriquée masquée.
                safe_repr(nested_cause) if nested_cause is not None else None,
            )
        # Toute autre erreur...
        except Exception as error:
            # ...copie avec l'état FAILED...
            failed_record = replace(
                # ...à partir de l'état RUNNING...
                running_record,
                # ...état échoué...
                status=GenerationStatus.FAILED,
                # ...nouvelle date...
                updated_at=datetime.now(UTC),
                # ...message générique (pas de détail interne)...
                error_message="La génération a échoué à cause d'une erreur interne.",
                # ...durée écoulée.
                duration_seconds=max(0.0, monotonic() - started_at),
            )
            # Journalise seulement le type de l'erreur.
            logger.error(
                "Generation %s failed with %s",
                generation_id,
                type(error).__name__,
            )
        # Aucune erreur...
        else:
            # ...copie avec l'état DONE...
            completed_record = replace(
                # ...à partir de l'état RUNNING...
                running_record,
                # ...état terminé...
                status=GenerationStatus.DONE,
                # ...nouvelle date...
                updated_at=datetime.now(UTC),
                # ...chemin du GLB...
                model_path=model_path,
                # ...pas d'erreur...
                error_message=None,
                # ...durée totale.
                duration_seconds=max(0.0, monotonic() - started_at),
            )
            # Prend le verrou...
            with self._lock:
                # ...enregistre l'état DONE.
                self._repository.save_generation(completed_record)
            # Fin : succès.
            return

        # En cas d'échec : prend le verrou...
        with self._lock:
            # ...enregistre l'état FAILED.
            self._repository.save_generation(failed_record)

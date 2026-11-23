# Rôle : persiste les catégories, générations et clés API dans un serveur PostgreSQL.
# Exécution : créé par repositories/factory.py à partir de DATABASE_URL ;
# l'API appelle initialize() au démarrage, puis chaque opération ouvre une connexion courte.
"""Dépôt PostgreSQL : seule implémentation de l'interface GenerationRepository.

Choix techniques, invisibles pour les services :
- types natifs : BOOLEAN, TIMESTAMPTZ (date avec fuseau), BIGINT GENERATED ALWAYS AS IDENTITY ;
- migrations idempotentes avec « ADD COLUMN IF NOT EXISTS » ;
- atomicité des quotas par verrou de ligne « SELECT ... FOR UPDATE » ;
- initialize() protégée par un verrou consultatif (pg_advisory_xact_lock) si deux API démarrent ensemble ;
- chemins de fichiers PORTABLES : sous storage_root, on enregistre « models/x.glb » (relatif) ; la même base
  sert alors au conteneur Linux (/app/backend/storage) et au poste Windows (dossier backend/storage du dépôt).
"""

# Les annotations de type restent du texte (pas d'évaluation au chargement).
from __future__ import annotations

# contextmanager : transforme une fonction avec yield en bloc « with ».
from contextlib import contextmanager
# UTC : fuseau universel ; timedelta : durée (ici 60 secondes pour la limite par minute).
from datetime import UTC, datetime, timedelta
# Path : type des chemins de fichiers.
from pathlib import Path
# Any : valeur de type quelconque ; Iterator : type de retour d'un générateur.
from typing import Any, Iterator
# uuid4 : génère un identifiant aléatoire (UUID public).
from uuid import uuid4

# psycopg 3 : pilote officiel PostgreSQL pour Python (équivalent du driver JDBC PostgreSQL).
# Les requêtes utilisent des paramètres %s : psycopg les envoie séparément du SQL (pas d'injection SQL).
import psycopg
# errors : exceptions précises de PostgreSQL (ex. violation d'unicité).
from psycopg import errors
# dict_row : chaque ligne relue devient un dictionnaire.
from psycopg.rows import dict_row

# Objets métier reconstruits à partir des lignes SQL.
from app.models import APIKeyRecord, CategoryRecord, GenerationRecord, GenerationStatus, ModelOrigin, ProductCategory
# Erreurs métier traduites depuis les erreurs PostgreSQL.
from app.repositories.base import CategoryConflictError, CategoryInUseError, CategoryNotFoundError

# Catégories créées au premier démarrage : (slug, libellé).
_INITIAL_CATEGORIES = (
    # Chaise.
    (ProductCategory.CHAIR.value, "Chaise"),
    # Tabouret.
    (ProductCategory.STOOL.value, "Tabouret"),
    # Table d'appoint.
    (ProductCategory.SIDE_TABLE.value, "Table d’appoint"),
)
# Message écrit sur les générations coupées par un arrêt du serveur.
_INTERRUPTED_MESSAGE = "Génération interrompue au redémarrage du serveur."
# Numéro arbitraire mais fixe du verrou consultatif : toutes les API qui initialisent le schéma
# demandent le même verrou, donc elles passent une par une.
# Numéro du verrou consultatif partagé par toutes les instances de l'API.
_SCHEMA_LOCK_ID = 3_040_301

# Début de requête commun : une génération + le slug de sa catégorie (jointure).
_GENERATION_SELECT = """
    SELECT generations.*, categories.slug AS category_slug
    FROM generations
    JOIN categories ON categories.id = generations.category_id
"""


# Implémentation du contrat GenerationRepository pour PostgreSQL.
class PostgresGenerationRepository:
    """Lit et écrit les données avec une connexion PostgreSQL par opération."""

    # Constructeur : URL de la base, dossier de stockage, délai de connexion (5 s).
    def __init__(self, database_url: str, *, storage_root: Path | None = None, connect_timeout: int = 5) -> None:
        """Mémorise l'URL de connexion et le dossier de stockage ; aucune connexion n'est ouverte ici.

        L'URL contient le mot de passe : elle n'est jamais journalisée (voir factory.mask_database_url).
        storage_root : dossier des photos et GLB ; les chemins situés dessous sont stockés en relatif.
        """
        # Mémorise l'URL (elle contient le mot de passe : jamais journalisée).
        self._database_url = database_url
        # Mémorise le dossier de stockage en chemin absolu, s'il est fourni.
        self._storage_root = storage_root.resolve() if storage_root is not None else None
        # Mémorise le délai maximal de connexion.
        self._connect_timeout = connect_timeout

    # Convertit un chemin en texte pour la base.
    def _path_to_db(self, path: Path | None) -> str | None:
        """Convertit un chemin de fichier en texte à enregistrer (relatif au stockage si possible).

        Exemple : /app/backend/storage/models/a.glb -> « models/a.glb ». Hors du stockage : chemin absolu.
        """
        # Aucun chemin...
        if path is None:
            # ...on enregistre NULL.
            return None
        # Chemin absolu et sans « .. ».
        absolute = path.resolve()
        # Si le fichier est sous le dossier de stockage...
        if self._storage_root is not None and absolute.is_relative_to(self._storage_root):
            # ...on enregistre le chemin relatif avec des « / » (portable Windows / Linux).
            return absolute.relative_to(self._storage_root).as_posix()
        # Sinon on enregistre le chemin absolu.
        return str(absolute)

    # Convertit le texte de la base en chemin réel.
    def _path_from_db(self, value: str | None) -> Path | None:
        """Reconstruit le chemin réel : un chemin relatif est rattaché au dossier de stockage courant."""
        # Valeur vide ou NULL...
        if not value:
            # ...pas de fichier.
            return None
        # Transforme le texte en Path.
        path = Path(value)
        # Chemin relatif et dossier de stockage connu...
        if not path.is_absolute() and self._storage_root is not None:
            # ...on le rattache au dossier de stockage de cette machine.
            return self._storage_root / path
        # Sinon on renvoie le chemin tel quel.
        return path

    # Rend la méthode utilisable avec « with self._connection() as connection ».
    @contextmanager
    # Ouvre une connexion PostgreSQL courte.
    def _connection(self) -> Iterator[psycopg.Connection[dict[str, Any]]]:
        """Ouvre une connexion, valide (commit) si le bloc réussit, annule (rollback) sinon, puis ferme.

        dict_row : chaque ligne est un dictionnaire (row["status"]) plutôt qu'un tuple.
        TimeZone=UTC : toutes les dates relues sont exprimées en UTC, quel que soit le serveur.
        """
        # Ouvre la connexion...
        with psycopg.connect(
            # ...avec l'URL de la base...
            self._database_url,
            # ...lignes sous forme de dictionnaires...
            row_factory=dict_row,
            # ...délai maximal de connexion...
            connect_timeout=self._connect_timeout,
            # ...dates relues en UTC.
            options="-c TimeZone=UTC",
        ) as connection:
            # Le bloc « with » de psycopg fait commit en sortie normale et rollback sur exception.
            # Donne la connexion au bloc « with » de l'appelant.
            yield connection

    # Crée ou met à jour le schéma au démarrage.
    def initialize(self) -> None:
        """Crée le schéma s'il manque, applique les migrations, insère les catégories initiales.

        Idempotente : peut être appelée à chaque démarrage sans perte de données.
        """
        # Instant présent en UTC.
        now = datetime.now(UTC)
        # Ouvre une transaction unique pour toute l'initialisation.
        with self._connection() as connection:
            # Prend le verrou consultatif : une seule API initialise le schéma à la fois.
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (_SCHEMA_LOCK_ID,))
            # Crée la table des catégories si elle n'existe pas.
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    slug TEXT NOT NULL UNIQUE,
                    label TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            # Crée la table des générations si elle n'existe pas (clé étrangère vers categories).
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS generations (
                    id TEXT PRIMARY KEY,
                    category_id BIGINT NOT NULL REFERENCES categories(id),
                    status TEXT NOT NULL CHECK (status IN ('PENDING', 'RUNNING', 'DONE', 'FAILED')),
                    filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    source_photo_path TEXT NOT NULL,
                    glb_path TEXT,
                    duration_seconds DOUBLE PRECISION CHECK (
                        duration_seconds IS NULL OR duration_seconds >= 0
                    ),
                    error_message TEXT,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            # Migrations non destructives : colonnes ajoutées au fil des étapes (avertissement, origine, intégration).
            # Migration : ajoute la colonne de l'avertissement photo.
            connection.execute("ALTER TABLE generations ADD COLUMN IF NOT EXISTS image_warning TEXT")
            # Migration : ajoute la colonne de provenance, « generated » par défaut, valeurs contrôlées.
            connection.execute(
                "ALTER TABLE generations ADD COLUMN IF NOT EXISTS origin TEXT NOT NULL DEFAULT 'generated'"
                " CHECK (origin IN ('generated', 'imported', 'example'))"
            )
            # Migration : ajoute la colonne de l'UUID public.
            connection.execute("ALTER TABLE generations ADD COLUMN IF NOT EXISTS public_id TEXT")
            # Migration : ajoute l'activation de l'intégration, fausse par défaut.
            connection.execute(
                "ALTER TABLE generations ADD COLUMN IF NOT EXISTS embed_enabled BOOLEAN NOT NULL DEFAULT FALSE"
            )
            # Crée la table des clés API (empreinte unique, jamais le secret).
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    prefix TEXT NOT NULL,
                    fingerprint TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMPTZ NOT NULL,
                    revoked BOOLEAN NOT NULL DEFAULT FALSE
                )
                """
            )
            # Index pour retrouver vite une clé active par son préfixe.
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_keys_prefix_active ON api_keys(prefix, revoked)"
            )
            # Crée la table des compteurs journaliers : une ligne par clé et par jour.
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS api_usage_daily (
                    api_key_id TEXT NOT NULL REFERENCES api_keys(id),
                    usage_date DATE NOT NULL,
                    generation_count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (api_key_id, usage_date)
                )
                """
            )
            # Crée la table des événements de requête (limite par minute).
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS api_rate_events (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    api_key_id TEXT NOT NULL REFERENCES api_keys(id),
                    occurred_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            # Index pour compter vite les requêtes récentes d'une clé.
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_rate_events_key_time ON api_rate_events(api_key_id, occurred_at)"
            )
            # Migration de données : un modèle terminé sans identifiant public en reçoit un (UUID4).
            # Cherche les modèles terminés qui n'ont pas encore d'UUID public.
            rows = connection.execute(
                "SELECT id FROM generations WHERE status = 'DONE' AND public_id IS NULL"
            ).fetchall()
            # Pour chacun d'eux...
            for row in rows:
                # ...on lui attribue un UUID aléatoire.
                connection.execute(
                    "UPDATE generations SET public_id = %s WHERE id = %s", (str(uuid4()), row["id"])
                )
            # Index unique : deux modèles ne peuvent pas partager le même UUID public.
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_generations_public_id "
                "ON generations(public_id) WHERE public_id IS NOT NULL"
            )
            # Index pour lister vite les modèles par état et par date.
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_generations_status_created "
                "ON generations(status, created_at DESC)"
            )
            # Pour chaque catégorie initiale...
            for slug, label in _INITIAL_CATEGORIES:
                # ...on l'insère, sauf si son slug existe déjà (ON CONFLICT DO NOTHING).
                connection.execute(
                    """
                    INSERT INTO categories (slug, label, is_active, created_at)
                    VALUES (%s, %s, TRUE, %s)
                    ON CONFLICT (slug) DO NOTHING
                    """,
                    # Valeurs : slug, libellé, date de création.
                    (slug, label, now),
                )
            # Une génération restée PENDING/RUNNING a été coupée par l'arrêt du serveur.
            # Passe en échec les générations restées en cours lors du dernier arrêt.
            connection.execute(
                """
                UPDATE generations
                SET status = 'FAILED', error_message = %s, updated_at = %s, duration_seconds = NULL
                WHERE status IN ('PENDING', 'RUNNING')
                """,
                # Valeurs : message d'interruption, date de mise à jour.
                (_INTERRUPTED_MESSAGE, now),
            )

    # Enregistre une génération : insertion, ou mise à jour si l'identifiant existe (upsert).
    def save_generation(self, record: GenerationRecord) -> None:
        """Insère ou met à jour (upsert) une génération ; l'UUID public et l'activation existants sont conservés."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # Exécute l'upsert ; l'UUID public existant et l'activation ne sont jamais écrasés.
            connection.execute(
                """
                INSERT INTO generations (
                    id, category_id, status, filename, content_type,
                    source_photo_path, glb_path, duration_seconds, error_message, image_warning, origin,
                    public_id, embed_enabled, created_at, updated_at
                )
                VALUES (
                    %s, (SELECT id FROM categories WHERE slug = %s),
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    category_id = excluded.category_id,
                    status = excluded.status,
                    filename = excluded.filename,
                    content_type = excluded.content_type,
                    source_photo_path = excluded.source_photo_path,
                    glb_path = excluded.glb_path,
                    duration_seconds = excluded.duration_seconds,
                    error_message = excluded.error_message,
                    image_warning = excluded.image_warning,
                    origin = excluded.origin,
                    public_id = COALESCE(generations.public_id, excluded.public_id),
                    embed_enabled = generations.embed_enabled,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                # Valeurs envoyées à la place des %s, dans l'ordre des colonnes :
                (
                    # identifiant interne ;
                    record.id,
                    # slug de la catégorie (accepte une énumération ou un texte) ;
                    str(getattr(record.category, "value", record.category)),
                    # état en texte ;
                    record.status.value,
                    # nom de fichier ;
                    record.filename,
                    # type MIME ;
                    record.content_type,
                    # chemin relatif de la photo, ou chaîne vide si aucune photo (colonne NOT NULL) ;
                    self._path_to_db(record.image_path) or "",
                    # chemin relatif du GLB, ou NULL ;
                    self._path_to_db(record.model_path),
                    # durée ;
                    record.duration_seconds,
                    # message d'erreur ;
                    record.error_message,
                    # avertissement photo ;
                    record.image_warning,
                    # provenance en texte ;
                    record.origin.value,
                    # UUID public existant, ou nouveau UUID si le modèle vient de se terminer ;
                    record.public_id or (str(uuid4()) if record.status is GenerationStatus.DONE else None),
                    # activation de l'intégration ;
                    record.embed_enabled,
                    # date de création ;
                    record.created_at,
                    # date de mise à jour.
                    record.updated_at,
                ),
            )

    # Lit une génération par identifiant interne.
    def get_generation(self, generation_id: str) -> GenerationRecord | None:
        """Retourne une génération par identifiant interne, ou None."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # Exécute le SELECT commun filtré par identifiant ; fetchone renvoie une ligne ou None.
            row = connection.execute(
                _GENERATION_SELECT + " WHERE generations.id = %s", (generation_id,)
            ).fetchone()
        # Convertit la ligne en objet métier, ou renvoie None si rien n'est trouvé.
        return self._record_from_row(row) if row is not None else None

    # Lit une génération par UUID public.
    def get_generation_by_public_id(self, public_id: str) -> GenerationRecord | None:
        """Retourne une génération par UUID public, ou None."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # SELECT commun filtré par UUID public.
            row = connection.execute(
                _GENERATION_SELECT + " WHERE generations.public_id = %s", (public_id,)
            ).fetchone()
        # Ligne convertie, ou None.
        return self._record_from_row(row) if row is not None else None

    # Active ou désactive l'intégration d'un modèle.
    def set_embed_enabled(self, generation_id: str, enabled: bool) -> GenerationRecord | None:
        """Active ou désactive l'intégration d'un modèle DONE, sans changer son UUID public."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # Met à jour seulement un modèle terminé qui possède un UUID public.
            cursor = connection.execute(
                """
                UPDATE generations SET embed_enabled = %s, updated_at = %s
                WHERE id = %s AND status = 'DONE' AND public_id IS NOT NULL
                """,
                # Valeurs : activation, date de mise à jour, identifiant.
                (enabled, datetime.now(UTC), generation_id),
            )
            # Aucune ligne modifiée (inconnu ou pas terminé)...
            if cursor.rowcount == 0:
                # ...on renvoie None (la route répondra 404).
                return None
            # Relit la ligne à jour.
            row = connection.execute(
                _GENERATION_SELECT + " WHERE generations.id = %s", (generation_id,)
            ).fetchone()
        # Renvoie l'objet métier à jour.
        return self._record_from_row(row) if row is not None else None

    # Renomme un modèle.
    def rename_generation(self, generation_id: str, filename: str) -> GenerationRecord | None:
        """Change le nom affiché (colonne filename) sans toucher aux fichiers ni à l'UUID public."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # Change le nom affiché et la date de mise à jour.
            cursor = connection.execute(
                "UPDATE generations SET filename = %s, updated_at = %s WHERE id = %s",
                (filename, datetime.now(UTC), generation_id),
            )
            # Aucune ligne modifiée...
            if cursor.rowcount == 0:
                # ...modèle inconnu.
                return None
            # Relit la ligne à jour.
            row = connection.execute(
                _GENERATION_SELECT + " WHERE generations.id = %s", (generation_id,)
            ).fetchone()
        # Renvoie l'objet métier à jour.
        return self._record_from_row(row) if row is not None else None

    # Change la catégorie d'un modèle.
    def set_generation_category(self, generation_id: str, category_slug: str) -> GenerationRecord | None:
        """Change la catégorie (colonne category_id, retrouvée par son slug) d'une génération."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # Remplace category_id par l'identifiant de la catégorie trouvée par son slug.
            cursor = connection.execute(
                """
                UPDATE generations
                SET category_id = (SELECT id FROM categories WHERE slug = %s), updated_at = %s
                WHERE id = %s
                """,
                # Valeurs : slug, date, identifiant du modèle.
                (category_slug, datetime.now(UTC), generation_id),
            )
            # Aucune ligne modifiée...
            if cursor.rowcount == 0:
                # ...modèle inconnu.
                return None
            # Relit la ligne à jour.
            row = connection.execute(
                _GENERATION_SELECT + " WHERE generations.id = %s", (generation_id,)
            ).fetchone()
        # Renvoie l'objet métier à jour.
        return self._record_from_row(row) if row is not None else None

    # Supprime la ligne d'une génération.
    def delete_generation(self, generation_id: str) -> bool:
        """Supprime la ligne d'une génération ; False si elle n'existait pas."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # Supprime la ligne par identifiant.
            cursor = connection.execute("DELETE FROM generations WHERE id = %s", (generation_id,))
            # Vrai si au moins une ligne a été supprimée.
            return cursor.rowcount > 0

    # Liste les modèles terminés.
    def list_completed_generations(self) -> list[GenerationRecord]:
        """Liste les générations DONE, de la plus récente à la plus ancienne."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # SELECT commun filtré sur DONE, du plus récent au plus ancien (puis par identifiant pour un ordre stable).
            rows = connection.execute(
                _GENERATION_SELECT
                + " WHERE generations.status = 'DONE' ORDER BY generations.created_at DESC, generations.id"
            ).fetchall()
        # Convertit chaque ligne en objet métier.
        return [self._record_from_row(row) for row in rows]

    # Lit une catégorie par slug.
    def get_category(self, slug: str, include_inactive: bool = False) -> CategoryRecord | None:
        """Retourne une catégorie par slug ; les inactives seulement si demandé."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # Le filtre (%s OR is_active) montre les inactives seulement si include_inactive est vrai.
            row = connection.execute(
                "SELECT * FROM categories WHERE slug = %s AND (%s OR is_active)",
                (slug, include_inactive),
            ).fetchone()
        # Ligne convertie, ou None.
        return self._category_from_row(row) if row is not None else None

    # Liste les catégories.
    def list_categories(self, include_inactive: bool = False) -> list[CategoryRecord]:
        """Liste les catégories dans l'ordre de création puis du libellé."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # Même astuce de filtre, triée par ordre de création.
            rows = connection.execute(
                "SELECT * FROM categories WHERE (%s OR is_active) ORDER BY id, label",
                (include_inactive,),
            ).fetchall()
        # Convertit chaque ligne en catégorie métier.
        return [self._category_from_row(row) for row in rows]

    # Crée une catégorie.
    def create_category(self, slug: str, label: str) -> CategoryRecord:
        """Crée une catégorie active ; un slug déjà pris devient CategoryConflictError."""
        # Essaie l'insertion...
        try:
            # ...dans une transaction.
            with self._connection() as connection:
                # Insère la catégorie active et renvoie la ligne créée (RETURNING *).
                row = connection.execute(
                    "INSERT INTO categories (slug, label, is_active, created_at)"
                    " VALUES (%s, %s, TRUE, %s) RETURNING *",
                    (slug, label, datetime.now(UTC)),
                ).fetchone()
        # Slug déjà pris (contrainte UNIQUE)...
        except errors.UniqueViolation as error:
            # ...traduit en erreur métier (la route répondra 409).
            raise CategoryConflictError("Ce slug de catégorie existe déjà.") from error
        # Renvoie la catégorie créée.
        return self._category_from_row(row)

    # Modifie une catégorie.
    def update_category(
        self,
        current_slug: str,
        *,
        slug: str | None = None,
        label: str | None = None,
        is_active: bool | None = None,
    ) -> CategoryRecord:
        """Met à jour les champs fournis ; l'identifiant (donc le lien avec les générations) ne change pas."""
        # Morceaux « colonne = %s » à assembler.
        assignments: list[str] = []
        # Valeurs correspondantes, dans le même ordre.
        values: list[object] = []
        # Nouveau slug demandé...
        if slug is not None:
            # ...on ajoute sa colonne...
            assignments.append("slug = %s")
            # ...et sa valeur.
            values.append(slug)
        # Nouveau libellé demandé...
        if label is not None:
            # ...on ajoute sa colonne...
            assignments.append("label = %s")
            # ...et sa valeur.
            values.append(label)
        # Nouvel état demandé...
        if is_active is not None:
            # ...on ajoute sa colonne...
            assignments.append("is_active = %s")
            # ...et sa valeur.
            values.append(is_active)
        # Rien à modifier...
        if not assignments:
            # ...on relit la catégorie actuelle...
            category = self.get_category(current_slug, include_inactive=True)
            # ...introuvable...
            if category is None:
                # ...erreur 404.
                raise CategoryNotFoundError("Catégorie introuvable.")
            # Sinon on la renvoie sans changement.
            return category
        # Essaie la mise à jour...
        try:
            # ...dans une transaction.
            with self._connection() as connection:
                # Les noms de colonnes viennent de la liste fixe ci-dessus, jamais de l'utilisateur.
                # Assemble l'UPDATE (noms de colonnes fixes) et renvoie la ligne modifiée.
                row = connection.execute(
                    f"UPDATE categories SET {', '.join(assignments)} WHERE slug = %s RETURNING *",
                    (*values, current_slug),
                ).fetchone()
        # Nouveau slug déjà pris...
        except errors.UniqueViolation as error:
            # ...erreur métier 409.
            raise CategoryConflictError("Ce slug de catégorie existe déjà.") from error
        # Aucune ligne renvoyée...
        if row is None:
            # ...catégorie introuvable.
            raise CategoryNotFoundError("Catégorie introuvable.")
        # Renvoie la catégorie modifiée.
        return self._category_from_row(row)

    # Supprime une catégorie inutilisée.
    def delete_category(self, slug: str) -> None:
        """Supprime une catégorie seulement si aucune génération ne la référence."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # Lit la catégorie et la verrouille (FOR UPDATE) jusqu'à la fin de la transaction.
            row = connection.execute(
                "SELECT id FROM categories WHERE slug = %s FOR UPDATE", (slug,)
            ).fetchone()
            # Introuvable...
            if row is None:
                # ...erreur 404.
                raise CategoryNotFoundError("Catégorie introuvable.")
            # Compte les générations qui utilisent cette catégorie.
            uses = connection.execute(
                "SELECT COUNT(*) AS uses FROM generations WHERE category_id = %s", (row["id"],)
            ).fetchone()["uses"]
            # Au moins une utilisation...
            if uses:
                # ...suppression refusée (erreur 409).
                raise CategoryInUseError(
                    "Cette catégorie est utilisée par des générations et ne peut pas être supprimée."
                )
            # Supprime la catégorie.
            connection.execute("DELETE FROM categories WHERE id = %s", (row["id"],))

    # Enregistre une clé API.
    def create_api_key(self, record: APIKeyRecord) -> APIKeyRecord:
        """Enregistre les métadonnées et l'empreinte d'une clé, jamais sa valeur secrète."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # Insère les métadonnées et l'empreinte (jamais le secret).
            connection.execute(
                "INSERT INTO api_keys (id, name, prefix, fingerprint, created_at, revoked)"
                " VALUES (%s, %s, %s, %s, %s, %s)",
                # Valeurs dans l'ordre des colonnes.
                (record.id, record.name, record.prefix, record.fingerprint, record.created_at, record.revoked),
            )
        # Renvoie l'enregistrement reçu.
        return record

    # Liste les clés API.
    def list_api_keys(self) -> list[APIKeyRecord]:
        """Liste toutes les clés (y compris révoquées), sans aucun secret."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # Toutes les clés, les plus récentes d'abord.
            rows = connection.execute("SELECT * FROM api_keys ORDER BY created_at DESC, id").fetchall()
        # Convertit chaque ligne en objet métier.
        return [self._api_key_from_row(row) for row in rows]

    # Cherche les clés actives d'un préfixe.
    def find_api_keys_by_prefix(self, prefix: str) -> list[APIKeyRecord]:
        """Retourne les clés actives candidates partageant ce préfixe."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # Clés non révoquées qui ont ce préfixe.
            rows = connection.execute(
                "SELECT * FROM api_keys WHERE prefix = %s AND NOT revoked ORDER BY id", (prefix,)
            ).fetchall()
        # Convertit chaque ligne en objet métier.
        return [self._api_key_from_row(row) for row in rows]

    # Révoque une clé.
    def revoke_api_key(self, key_id: str) -> APIKeyRecord | None:
        """Révoque une clé sans effacer son historique."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # Passe revoked à vrai et renvoie la ligne modifiée.
            row = connection.execute(
                "UPDATE api_keys SET revoked = TRUE WHERE id = %s RETURNING *", (key_id,)
            ).fetchone()
        # Ligne convertie, ou None si la clé est inconnue.
        return self._api_key_from_row(row) if row is not None else None

    # Supprime une clé déjà révoquée.
    def delete_revoked_api_key(self, key_id: str) -> str:
        """Efface une clé révoquée et ses compteurs dans une seule transaction."""
        # Ouvre une transaction.
        with self._connection() as connection:
            # Lit la clé et la verrouille.
            row = connection.execute(
                "SELECT revoked FROM api_keys WHERE id = %s FOR UPDATE", (key_id,)
            ).fetchone()
            # Clé inconnue...
            if row is None:
                # ...on le signale.
                return "not_found"
            # Clé encore active...
            if not row["revoked"]:
                # ...suppression refusée : il faut d'abord la révoquer.
                return "active"
            # Supprime d'abord ses événements de requête (clé étrangère).
            connection.execute("DELETE FROM api_rate_events WHERE api_key_id = %s", (key_id,))
            # Supprime ses compteurs journaliers.
            connection.execute("DELETE FROM api_usage_daily WHERE api_key_id = %s", (key_id,))
            # Supprime enfin la clé.
            connection.execute("DELETE FROM api_keys WHERE id = %s", (key_id,))
        # Suppression réussie.
        return "deleted"

    # Limite par minute, sur une fenêtre glissante de 60 secondes.
    def consume_api_rate_limit(self, key_id: str, rate_limit_per_minute: int, now: datetime) -> str | None:
        """Réserve atomiquement une requête dans une fenêtre glissante de 60 secondes.

        « FOR UPDATE » verrouille la ligne de la clé jusqu'à la fin de la transaction : deux requêtes
        simultanées avec la même clé passent l'une après l'autre et ne peuvent pas dépasser la limite.
        Retour : None si acceptée, "revoked" ou "rate_limit" sinon.
        """
        # Instant présent converti en UTC.
        current = now.astimezone(UTC)
        # Début de la fenêtre : il y a 60 secondes.
        cutoff = current - timedelta(seconds=60)
        # Ouvre une transaction.
        with self._connection() as connection:
            # Verrouille la ligne de la clé, si elle est active.
            active_key = connection.execute(
                "SELECT id FROM api_keys WHERE id = %s AND NOT revoked FOR UPDATE", (key_id,)
            ).fetchone()
            # Clé absente ou révoquée...
            if active_key is None:
                # ...refus « revoked ».
                return "revoked"
            # Compte les requêtes de cette clé dans les 60 dernières secondes.
            rate_count = connection.execute(
                "SELECT COUNT(*) AS n FROM api_rate_events WHERE api_key_id = %s AND occurred_at > %s",
                (key_id, cutoff),
            ).fetchone()["n"]
            # Limite atteinte...
            if rate_count >= rate_limit_per_minute:
                # ...refus « rate_limit » (la route répondra 429).
                return "rate_limit"
            # Purge les événements plus vieux que la fenêtre.
            connection.execute("DELETE FROM api_rate_events WHERE occurred_at <= %s", (cutoff,))
            # Enregistre la requête courante.
            connection.execute(
                "INSERT INTO api_rate_events (api_key_id, occurred_at) VALUES (%s, %s)", (key_id, current)
            )
        # Requête acceptée.
        return None

    # Quota journalier de créations par clé.
    def consume_api_daily_quota(self, key_id: str, daily_limit: int, now: datetime) -> str | None:
        """Consomme atomiquement une création dans la journée UTC.

        Retour : None si acceptée, "revoked" ou "daily_quota" sinon.
        """
        # Jour UTC courant.
        usage_date = now.astimezone(UTC).date()
        # Ouvre une transaction.
        with self._connection() as connection:
            # Verrouille la ligne de la clé, si elle est active.
            active_key = connection.execute(
                "SELECT id FROM api_keys WHERE id = %s AND NOT revoked FOR UPDATE", (key_id,)
            ).fetchone()
            # Clé absente ou révoquée...
            if active_key is None:
                # ...refus « revoked ».
                return "revoked"
            # Lit le compteur du jour pour cette clé.
            usage = connection.execute(
                "SELECT generation_count FROM api_usage_daily WHERE api_key_id = %s AND usage_date = %s",
                (key_id, usage_date),
            ).fetchone()
            # Quota atteint...
            if usage is not None and usage["generation_count"] >= daily_limit:
                # ...refus « daily_quota ».
                return "daily_quota"
            # Crée le compteur à 1, ou l'incrémente s'il existe déjà.
            connection.execute(
                """
                INSERT INTO api_usage_daily (api_key_id, usage_date, generation_count)
                VALUES (%s, %s, 1)
                ON CONFLICT (api_key_id, usage_date) DO UPDATE
                SET generation_count = api_usage_daily.generation_count + 1
                """,
                (key_id, usage_date),
            )
        # Création acceptée.
        return None

    # Méthode sans self : simple conversion.
    @staticmethod
    # Convertit une ligne SQL en catégorie.
    def _category_from_row(row: dict[str, Any]) -> CategoryRecord:
        """Convertit une ligne PostgreSQL en catégorie métier."""
        # Construit l'objet métier...
        return CategoryRecord(
            # ...identifiant...
            id=row["id"],
            # ...slug...
            slug=row["slug"],
            # ...libellé...
            label=row["label"],
            # ...état actif converti en booléen...
            is_active=bool(row["is_active"]),
            # ...date de création.
            created_at=row["created_at"],
        )

    # Méthode sans self : simple conversion.
    @staticmethod
    # Convertit une ligne SQL en clé API.
    def _api_key_from_row(row: dict[str, Any]) -> APIKeyRecord:
        """Convertit une ligne PostgreSQL en métadonnées de clé."""
        # Construit l'objet métier...
        return APIKeyRecord(
            # ...identifiant...
            id=row["id"],
            # ...nom...
            name=row["name"],
            # ...préfixe...
            prefix=row["prefix"],
            # ...empreinte...
            fingerprint=row["fingerprint"],
            # ...date de création...
            created_at=row["created_at"],
            # ...état révoqué.
            revoked=bool(row["revoked"]),
        )

    # Convertit une ligne SQL en génération (a besoin de self pour les chemins).
    def _record_from_row(self, row: dict[str, Any]) -> GenerationRecord:
        """Convertit une ligne PostgreSQL en génération métier typée."""
        # Construit l'objet métier...
        return GenerationRecord(
            # ...identifiant...
            id=row["id"],
            # ...texte de l'état reconverti en énumération...
            status=GenerationStatus(row["status"]),
            # ...nom de fichier...
            filename=row["filename"],
            # ...type MIME...
            content_type=row["content_type"],
            # ...slug lu grâce à la jointure...
            category=row["category_slug"],
            # ...chemin réel de la photo...
            image_path=self._path_from_db(row["source_photo_path"]),
            # ...date de création...
            created_at=row["created_at"],
            # ...date de mise à jour...
            updated_at=row["updated_at"],
            # ...chemin réel du GLB...
            model_path=self._path_from_db(row["glb_path"]),
            # ...message d'erreur...
            error_message=row["error_message"],
            # ...durée...
            duration_seconds=row["duration_seconds"],
            # ...avertissement photo...
            image_warning=row["image_warning"],
            # ...provenance reconvertie en énumération...
            origin=ModelOrigin(row["origin"]),
            # ...UUID public...
            public_id=row["public_id"],
            # ...activation de l'intégration.
            embed_enabled=bool(row["embed_enabled"]),
        )

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

from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

# psycopg 3 : pilote officiel PostgreSQL pour Python (équivalent du driver JDBC PostgreSQL).
# Les requêtes utilisent des paramètres %s : psycopg les envoie séparément du SQL (pas d'injection SQL).
import psycopg
from psycopg import errors
from psycopg.rows import dict_row

from app.models import APIKeyRecord, CategoryRecord, GenerationRecord, GenerationStatus, ModelOrigin, ProductCategory
from app.repositories.base import CategoryConflictError, CategoryInUseError, CategoryNotFoundError

_INITIAL_CATEGORIES = (
    (ProductCategory.CHAIR.value, "Chaise"),
    (ProductCategory.STOOL.value, "Tabouret"),
    (ProductCategory.SIDE_TABLE.value, "Table d’appoint"),
)
_INTERRUPTED_MESSAGE = "Génération interrompue au redémarrage du serveur."
# Numéro arbitraire mais fixe du verrou consultatif : toutes les API qui initialisent le schéma
# demandent le même verrou, donc elles passent une par une.
_SCHEMA_LOCK_ID = 3_040_301

_GENERATION_SELECT = """
    SELECT generations.*, categories.slug AS category_slug
    FROM generations
    JOIN categories ON categories.id = generations.category_id
"""


class PostgresGenerationRepository:
    """Lit et écrit les données avec une connexion PostgreSQL par opération."""

    def __init__(self, database_url: str, *, storage_root: Path | None = None, connect_timeout: int = 5) -> None:
        """Mémorise l'URL de connexion et le dossier de stockage ; aucune connexion n'est ouverte ici.

        L'URL contient le mot de passe : elle n'est jamais journalisée (voir factory.mask_database_url).
        storage_root : dossier des photos et GLB ; les chemins situés dessous sont stockés en relatif.
        """
        self._database_url = database_url
        self._storage_root = storage_root.resolve() if storage_root is not None else None
        self._connect_timeout = connect_timeout

    def _path_to_db(self, path: Path | None) -> str | None:
        """Convertit un chemin de fichier en texte à enregistrer (relatif au stockage si possible).

        Exemple : /app/backend/storage/models/a.glb -> « models/a.glb ». Hors du stockage : chemin absolu.
        """
        if path is None:
            return None
        absolute = path.resolve()
        if self._storage_root is not None and absolute.is_relative_to(self._storage_root):
            return absolute.relative_to(self._storage_root).as_posix()
        return str(absolute)

    def _path_from_db(self, value: str | None) -> Path | None:
        """Reconstruit le chemin réel : un chemin relatif est rattaché au dossier de stockage courant."""
        if not value:
            return None
        path = Path(value)
        if not path.is_absolute() and self._storage_root is not None:
            return self._storage_root / path
        return path

    @contextmanager
    def _connection(self) -> Iterator[psycopg.Connection[dict[str, Any]]]:
        """Ouvre une connexion, valide (commit) si le bloc réussit, annule (rollback) sinon, puis ferme.

        dict_row : chaque ligne est un dictionnaire (row["status"]) plutôt qu'un tuple.
        TimeZone=UTC : toutes les dates relues sont exprimées en UTC, quel que soit le serveur.
        """
        with psycopg.connect(
            self._database_url,
            row_factory=dict_row,
            connect_timeout=self._connect_timeout,
            options="-c TimeZone=UTC",
        ) as connection:
            # Le bloc « with » de psycopg fait commit en sortie normale et rollback sur exception.
            yield connection

    def initialize(self) -> None:
        """Crée le schéma s'il manque, applique les migrations, insère les catégories initiales.

        Idempotente : peut être appelée à chaque démarrage sans perte de données.
        """
        now = datetime.now(UTC)
        with self._connection() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (_SCHEMA_LOCK_ID,))
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
            connection.execute("ALTER TABLE generations ADD COLUMN IF NOT EXISTS image_warning TEXT")
            connection.execute(
                "ALTER TABLE generations ADD COLUMN IF NOT EXISTS origin TEXT NOT NULL DEFAULT 'generated'"
                " CHECK (origin IN ('generated', 'imported', 'example'))"
            )
            connection.execute("ALTER TABLE generations ADD COLUMN IF NOT EXISTS public_id TEXT")
            connection.execute(
                "ALTER TABLE generations ADD COLUMN IF NOT EXISTS embed_enabled BOOLEAN NOT NULL DEFAULT FALSE"
            )
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
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_keys_prefix_active ON api_keys(prefix, revoked)"
            )
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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS api_rate_events (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    api_key_id TEXT NOT NULL REFERENCES api_keys(id),
                    occurred_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_rate_events_key_time ON api_rate_events(api_key_id, occurred_at)"
            )
            # Migration de données : un modèle terminé sans identifiant public en reçoit un (UUID4).
            rows = connection.execute(
                "SELECT id FROM generations WHERE status = 'DONE' AND public_id IS NULL"
            ).fetchall()
            for row in rows:
                connection.execute(
                    "UPDATE generations SET public_id = %s WHERE id = %s", (str(uuid4()), row["id"])
                )
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_generations_public_id "
                "ON generations(public_id) WHERE public_id IS NOT NULL"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_generations_status_created "
                "ON generations(status, created_at DESC)"
            )
            for slug, label in _INITIAL_CATEGORIES:
                connection.execute(
                    """
                    INSERT INTO categories (slug, label, is_active, created_at)
                    VALUES (%s, %s, TRUE, %s)
                    ON CONFLICT (slug) DO NOTHING
                    """,
                    (slug, label, now),
                )
            # Une génération restée PENDING/RUNNING a été coupée par l'arrêt du serveur.
            connection.execute(
                """
                UPDATE generations
                SET status = 'FAILED', error_message = %s, updated_at = %s, duration_seconds = NULL
                WHERE status IN ('PENDING', 'RUNNING')
                """,
                (_INTERRUPTED_MESSAGE, now),
            )

    def save_generation(self, record: GenerationRecord) -> None:
        """Insère ou met à jour (upsert) une génération ; l'UUID public et l'activation existants sont conservés."""
        with self._connection() as connection:
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
                (
                    record.id,
                    str(getattr(record.category, "value", record.category)),
                    record.status.value,
                    record.filename,
                    record.content_type,
                    self._path_to_db(record.image_path) or "",
                    self._path_to_db(record.model_path),
                    record.duration_seconds,
                    record.error_message,
                    record.image_warning,
                    record.origin.value,
                    record.public_id or (str(uuid4()) if record.status is GenerationStatus.DONE else None),
                    record.embed_enabled,
                    record.created_at,
                    record.updated_at,
                ),
            )

    def get_generation(self, generation_id: str) -> GenerationRecord | None:
        """Retourne une génération par identifiant interne, ou None."""
        with self._connection() as connection:
            row = connection.execute(
                _GENERATION_SELECT + " WHERE generations.id = %s", (generation_id,)
            ).fetchone()
        return self._record_from_row(row) if row is not None else None

    def get_generation_by_public_id(self, public_id: str) -> GenerationRecord | None:
        """Retourne une génération par UUID public, ou None."""
        with self._connection() as connection:
            row = connection.execute(
                _GENERATION_SELECT + " WHERE generations.public_id = %s", (public_id,)
            ).fetchone()
        return self._record_from_row(row) if row is not None else None

    def set_embed_enabled(self, generation_id: str, enabled: bool) -> GenerationRecord | None:
        """Active ou désactive l'intégration d'un modèle DONE, sans changer son UUID public."""
        with self._connection() as connection:
            cursor = connection.execute(
                """
                UPDATE generations SET embed_enabled = %s, updated_at = %s
                WHERE id = %s AND status = 'DONE' AND public_id IS NOT NULL
                """,
                (enabled, datetime.now(UTC), generation_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                _GENERATION_SELECT + " WHERE generations.id = %s", (generation_id,)
            ).fetchone()
        return self._record_from_row(row) if row is not None else None

    def rename_generation(self, generation_id: str, filename: str) -> GenerationRecord | None:
        """Change le nom affiché (colonne filename) sans toucher aux fichiers ni à l'UUID public."""
        with self._connection() as connection:
            cursor = connection.execute(
                "UPDATE generations SET filename = %s, updated_at = %s WHERE id = %s",
                (filename, datetime.now(UTC), generation_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                _GENERATION_SELECT + " WHERE generations.id = %s", (generation_id,)
            ).fetchone()
        return self._record_from_row(row) if row is not None else None

    def delete_generation(self, generation_id: str) -> bool:
        """Supprime la ligne d'une génération ; False si elle n'existait pas."""
        with self._connection() as connection:
            cursor = connection.execute("DELETE FROM generations WHERE id = %s", (generation_id,))
            return cursor.rowcount > 0

    def list_completed_generations(self) -> list[GenerationRecord]:
        """Liste les générations DONE, de la plus récente à la plus ancienne."""
        with self._connection() as connection:
            rows = connection.execute(
                _GENERATION_SELECT
                + " WHERE generations.status = 'DONE' ORDER BY generations.created_at DESC, generations.id"
            ).fetchall()
        return [self._record_from_row(row) for row in rows]

    def get_category(self, slug: str, include_inactive: bool = False) -> CategoryRecord | None:
        """Retourne une catégorie par slug ; les inactives seulement si demandé."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM categories WHERE slug = %s AND (%s OR is_active)",
                (slug, include_inactive),
            ).fetchone()
        return self._category_from_row(row) if row is not None else None

    def list_categories(self, include_inactive: bool = False) -> list[CategoryRecord]:
        """Liste les catégories dans l'ordre de création puis du libellé."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM categories WHERE (%s OR is_active) ORDER BY id, label",
                (include_inactive,),
            ).fetchall()
        return [self._category_from_row(row) for row in rows]

    def create_category(self, slug: str, label: str) -> CategoryRecord:
        """Crée une catégorie active ; un slug déjà pris devient CategoryConflictError."""
        try:
            with self._connection() as connection:
                row = connection.execute(
                    "INSERT INTO categories (slug, label, is_active, created_at)"
                    " VALUES (%s, %s, TRUE, %s) RETURNING *",
                    (slug, label, datetime.now(UTC)),
                ).fetchone()
        except errors.UniqueViolation as error:
            raise CategoryConflictError("Ce slug de catégorie existe déjà.") from error
        return self._category_from_row(row)

    def update_category(
        self,
        current_slug: str,
        *,
        slug: str | None = None,
        label: str | None = None,
        is_active: bool | None = None,
    ) -> CategoryRecord:
        """Met à jour les champs fournis ; l'identifiant (donc le lien avec les générations) ne change pas."""
        assignments: list[str] = []
        values: list[object] = []
        if slug is not None:
            assignments.append("slug = %s")
            values.append(slug)
        if label is not None:
            assignments.append("label = %s")
            values.append(label)
        if is_active is not None:
            assignments.append("is_active = %s")
            values.append(is_active)
        if not assignments:
            category = self.get_category(current_slug, include_inactive=True)
            if category is None:
                raise CategoryNotFoundError("Catégorie introuvable.")
            return category
        try:
            with self._connection() as connection:
                # Les noms de colonnes viennent de la liste fixe ci-dessus, jamais de l'utilisateur.
                row = connection.execute(
                    f"UPDATE categories SET {', '.join(assignments)} WHERE slug = %s RETURNING *",
                    (*values, current_slug),
                ).fetchone()
        except errors.UniqueViolation as error:
            raise CategoryConflictError("Ce slug de catégorie existe déjà.") from error
        if row is None:
            raise CategoryNotFoundError("Catégorie introuvable.")
        return self._category_from_row(row)

    def delete_category(self, slug: str) -> None:
        """Supprime une catégorie seulement si aucune génération ne la référence."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT id FROM categories WHERE slug = %s FOR UPDATE", (slug,)
            ).fetchone()
            if row is None:
                raise CategoryNotFoundError("Catégorie introuvable.")
            uses = connection.execute(
                "SELECT COUNT(*) AS uses FROM generations WHERE category_id = %s", (row["id"],)
            ).fetchone()["uses"]
            if uses:
                raise CategoryInUseError(
                    "Cette catégorie est utilisée par des générations et ne peut pas être supprimée."
                )
            connection.execute("DELETE FROM categories WHERE id = %s", (row["id"],))

    def create_api_key(self, record: APIKeyRecord) -> APIKeyRecord:
        """Enregistre les métadonnées et l'empreinte d'une clé, jamais sa valeur secrète."""
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO api_keys (id, name, prefix, fingerprint, created_at, revoked)"
                " VALUES (%s, %s, %s, %s, %s, %s)",
                (record.id, record.name, record.prefix, record.fingerprint, record.created_at, record.revoked),
            )
        return record

    def list_api_keys(self) -> list[APIKeyRecord]:
        """Liste toutes les clés (y compris révoquées), sans aucun secret."""
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM api_keys ORDER BY created_at DESC, id").fetchall()
        return [self._api_key_from_row(row) for row in rows]

    def find_api_keys_by_prefix(self, prefix: str) -> list[APIKeyRecord]:
        """Retourne les clés actives candidates partageant ce préfixe."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM api_keys WHERE prefix = %s AND NOT revoked ORDER BY id", (prefix,)
            ).fetchall()
        return [self._api_key_from_row(row) for row in rows]

    def revoke_api_key(self, key_id: str) -> APIKeyRecord | None:
        """Révoque une clé sans effacer son historique."""
        with self._connection() as connection:
            row = connection.execute(
                "UPDATE api_keys SET revoked = TRUE WHERE id = %s RETURNING *", (key_id,)
            ).fetchone()
        return self._api_key_from_row(row) if row is not None else None

    def delete_revoked_api_key(self, key_id: str) -> str:
        """Efface une clé révoquée et ses compteurs dans une seule transaction."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT revoked FROM api_keys WHERE id = %s FOR UPDATE", (key_id,)
            ).fetchone()
            if row is None:
                return "not_found"
            if not row["revoked"]:
                return "active"
            connection.execute("DELETE FROM api_rate_events WHERE api_key_id = %s", (key_id,))
            connection.execute("DELETE FROM api_usage_daily WHERE api_key_id = %s", (key_id,))
            connection.execute("DELETE FROM api_keys WHERE id = %s", (key_id,))
        return "deleted"

    def consume_api_rate_limit(self, key_id: str, rate_limit_per_minute: int, now: datetime) -> str | None:
        """Réserve atomiquement une requête dans une fenêtre glissante de 60 secondes.

        « FOR UPDATE » verrouille la ligne de la clé jusqu'à la fin de la transaction : deux requêtes
        simultanées avec la même clé passent l'une après l'autre et ne peuvent pas dépasser la limite.
        Retour : None si acceptée, "revoked" ou "rate_limit" sinon.
        """
        current = now.astimezone(UTC)
        cutoff = current - timedelta(seconds=60)
        with self._connection() as connection:
            active_key = connection.execute(
                "SELECT id FROM api_keys WHERE id = %s AND NOT revoked FOR UPDATE", (key_id,)
            ).fetchone()
            if active_key is None:
                return "revoked"
            rate_count = connection.execute(
                "SELECT COUNT(*) AS n FROM api_rate_events WHERE api_key_id = %s AND occurred_at > %s",
                (key_id, cutoff),
            ).fetchone()["n"]
            if rate_count >= rate_limit_per_minute:
                return "rate_limit"
            connection.execute("DELETE FROM api_rate_events WHERE occurred_at <= %s", (cutoff,))
            connection.execute(
                "INSERT INTO api_rate_events (api_key_id, occurred_at) VALUES (%s, %s)", (key_id, current)
            )
        return None

    def consume_api_daily_quota(self, key_id: str, daily_limit: int, now: datetime) -> str | None:
        """Consomme atomiquement une création dans la journée UTC.

        Retour : None si acceptée, "revoked" ou "daily_quota" sinon.
        """
        usage_date = now.astimezone(UTC).date()
        with self._connection() as connection:
            active_key = connection.execute(
                "SELECT id FROM api_keys WHERE id = %s AND NOT revoked FOR UPDATE", (key_id,)
            ).fetchone()
            if active_key is None:
                return "revoked"
            usage = connection.execute(
                "SELECT generation_count FROM api_usage_daily WHERE api_key_id = %s AND usage_date = %s",
                (key_id, usage_date),
            ).fetchone()
            if usage is not None and usage["generation_count"] >= daily_limit:
                return "daily_quota"
            connection.execute(
                """
                INSERT INTO api_usage_daily (api_key_id, usage_date, generation_count)
                VALUES (%s, %s, 1)
                ON CONFLICT (api_key_id, usage_date) DO UPDATE
                SET generation_count = api_usage_daily.generation_count + 1
                """,
                (key_id, usage_date),
            )
        return None

    @staticmethod
    def _category_from_row(row: dict[str, Any]) -> CategoryRecord:
        """Convertit une ligne PostgreSQL en catégorie métier."""
        return CategoryRecord(
            id=row["id"],
            slug=row["slug"],
            label=row["label"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
        )

    @staticmethod
    def _api_key_from_row(row: dict[str, Any]) -> APIKeyRecord:
        """Convertit une ligne PostgreSQL en métadonnées de clé."""
        return APIKeyRecord(
            id=row["id"],
            name=row["name"],
            prefix=row["prefix"],
            fingerprint=row["fingerprint"],
            created_at=row["created_at"],
            revoked=bool(row["revoked"]),
        )

    def _record_from_row(self, row: dict[str, Any]) -> GenerationRecord:
        """Convertit une ligne PostgreSQL en génération métier typée."""
        return GenerationRecord(
            id=row["id"],
            status=GenerationStatus(row["status"]),
            filename=row["filename"],
            content_type=row["content_type"],
            category=row["category_slug"],
            image_path=self._path_from_db(row["source_photo_path"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            model_path=self._path_from_db(row["glb_path"]),
            error_message=row["error_message"],
            duration_seconds=row["duration_seconds"],
            image_warning=row["image_warning"],
            origin=ModelOrigin(row["origin"]),
            public_id=row["public_id"],
            embed_enabled=bool(row["embed_enabled"]),
        )

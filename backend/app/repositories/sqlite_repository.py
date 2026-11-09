# Rôle : persiste les catégories et les générations dans une base SQLite locale.
# Exécution : l'API initialise le dépôt au démarrage ; chaque opération ouvre sa connexion.
"""Dépôt SQLite avec connexions courtes et réouvertes à chaque opération."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from app.models import CategoryRecord, GenerationRecord, GenerationStatus, ModelOrigin, ProductCategory
from app.repositories.base import CategoryConflictError, CategoryInUseError, CategoryNotFoundError

_INITIAL_CATEGORIES = (
    (ProductCategory.CHAIR.value, "Chaise"),
    (ProductCategory.STOOL.value, "Tabouret"),
    (ProductCategory.SIDE_TABLE.value, "Table d’appoint"),
)
_INTERRUPTED_MESSAGE = "Génération interrompue au redémarrage du serveur."


class SQLiteGenerationRepository:
    """Lit et écrit les générations avec une connexion SQLite par opération."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path.resolve()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Fournit une connexion indépendante, avec commit/rollback et fermeture garantis."""
        connection = sqlite3.connect(self.database_path, timeout=5.0)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        """Crée les tables, insère les catégories de départ et échoue les travaux interrompus."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now(UTC).isoformat()
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT NOT NULL UNIQUE,
                    label TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS generations (
                    id TEXT PRIMARY KEY,
                    category_id INTEGER NOT NULL REFERENCES categories(id),
                    status TEXT NOT NULL CHECK (status IN ('PENDING', 'RUNNING', 'DONE', 'FAILED')),
                    filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    source_photo_path TEXT NOT NULL,
                    glb_path TEXT,
                    duration_seconds REAL CHECK (
                        duration_seconds IS NULL OR duration_seconds >= 0
                    ),
                    error_message TEXT,
                    image_warning TEXT,
                    origin TEXT NOT NULL DEFAULT 'generated' CHECK (origin IN ('generated', 'imported', 'example')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            generation_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(generations)").fetchall()
            }
            if "image_warning" not in generation_columns:
                connection.execute("ALTER TABLE generations ADD COLUMN image_warning TEXT")
            if "origin" not in generation_columns:
                connection.execute(
                    "ALTER TABLE generations ADD COLUMN origin TEXT NOT NULL DEFAULT 'generated'"
                )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_generations_status_created "
                "ON generations(status, created_at DESC)"
            )
            connection.executemany(
                """
                INSERT INTO categories (slug, label, is_active, created_at)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(slug) DO NOTHING
                """,
                [(slug, label, now) for slug, label in _INITIAL_CATEGORIES],
            )
            connection.execute(
                """
                UPDATE generations
                SET status = 'FAILED', error_message = ?, updated_at = ?, duration_seconds = NULL
                WHERE status IN ('PENDING', 'RUNNING')
                """,
                (_INTERRUPTED_MESSAGE, now),
            )

    def save_generation(self, record: GenerationRecord) -> None:
        """Insère ou met à jour une génération en reliant sa catégorie par slug."""
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO generations (
                    id, category_id, status, filename, content_type,
                    source_photo_path, glb_path, duration_seconds, error_message, image_warning, origin,
                    created_at, updated_at
                )
                VALUES (
                    ?, (SELECT id FROM categories WHERE slug = ?), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(id) DO UPDATE SET
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
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at
                """,
                (
                    record.id,
                    str(getattr(record.category, "value", record.category)),
                    record.status.value,
                    record.filename,
                    record.content_type,
                    str(record.image_path.resolve()) if record.image_path is not None else "",
                    str(record.model_path.resolve()) if record.model_path is not None else None,
                    record.duration_seconds,
                    record.error_message,
                    record.image_warning,
                    record.origin.value,
                    record.created_at.isoformat(),
                    record.updated_at.isoformat(),
                ),
            )

    def get_generation(self, generation_id: str) -> GenerationRecord | None:
        """Reconstruit le modèle métier à partir d'une ligne persistée."""
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT generations.*, categories.slug AS category_slug
                FROM generations
                JOIN categories ON categories.id = generations.category_id
                WHERE generations.id = ?
                """,
                (generation_id,),
            ).fetchone()
        return self._record_from_row(row) if row is not None else None

    def list_completed_generations(self) -> list[GenerationRecord]:
        """Liste les lignes DONE dans l'ordre chronologique inverse."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT generations.*, categories.slug AS category_slug
                FROM generations
                JOIN categories ON categories.id = generations.category_id
                WHERE generations.status = 'DONE'
                ORDER BY generations.created_at DESC, generations.id
                """
            ).fetchall()
        return [self._record_from_row(row) for row in rows]

    def get_category(self, slug: str, include_inactive: bool = False) -> CategoryRecord | None:
        """Recherche une catégorie, en filtrant les inactives sauf demande explicite."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM categories WHERE slug = ? AND (? OR is_active = 1)",
                (slug, int(include_inactive)),
            ).fetchone()
        return self._category_from_row(row) if row is not None else None

    def list_categories(self, include_inactive: bool = False) -> list[CategoryRecord]:
        """Retourne les catégories dans l'ordre de création puis du libellé."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM categories WHERE (? OR is_active = 1) ORDER BY id, label",
                (int(include_inactive),),
            ).fetchall()
        return [self._category_from_row(row) for row in rows]

    def create_category(self, slug: str, label: str) -> CategoryRecord:
        """Insère une catégorie active et traduit le conflit unique en erreur métier."""
        with self._connection() as connection:
            try:
                cursor = connection.execute(
                    "INSERT INTO categories (slug, label, is_active, created_at) VALUES (?, ?, 1, ?)",
                    (slug, label, datetime.now(UTC).isoformat()),
                )
            except sqlite3.IntegrityError as error:
                raise CategoryConflictError("Ce slug de catégorie existe déjà.") from error
            row = connection.execute(
                "SELECT * FROM categories WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return self._category_from_row(row)

    def update_category(
        self,
        current_slug: str,
        *,
        slug: str | None = None,
        label: str | None = None,
        is_active: bool | None = None,
    ) -> CategoryRecord:
        """Met à jour les champs fournis tout en conservant l'identifiant relationnel."""
        assignments: list[str] = []
        values: list[object] = []
        if slug is not None:
            assignments.append("slug = ?")
            values.append(slug)
        if label is not None:
            assignments.append("label = ?")
            values.append(label)
        if is_active is not None:
            assignments.append("is_active = ?")
            values.append(int(is_active))
        if not assignments:
            category = self.get_category(current_slug, include_inactive=True)
            if category is None:
                raise CategoryNotFoundError("Catégorie introuvable.")
            return category
        with self._connection() as connection:
            try:
                cursor = connection.execute(
                    f"UPDATE categories SET {', '.join(assignments)} WHERE slug = ?",
                    (*values, current_slug),
                )
            except sqlite3.IntegrityError as error:
                raise CategoryConflictError("Ce slug de catégorie existe déjà.") from error
            if cursor.rowcount == 0:
                raise CategoryNotFoundError("Catégorie introuvable.")
            row = connection.execute(
                "SELECT * FROM categories WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            if row is None:
                row = connection.execute(
                    "SELECT * FROM categories WHERE slug = ?", (slug or current_slug,)
                ).fetchone()
        return self._category_from_row(row)

    def delete_category(self, slug: str) -> None:
        """Supprime une catégorie seulement si aucune génération ne la référence."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT id FROM categories WHERE slug = ?", (slug,)
            ).fetchone()
            if row is None:
                raise CategoryNotFoundError("Catégorie introuvable.")
            uses = connection.execute(
                "SELECT COUNT(*) FROM generations WHERE category_id = ?", (row["id"],)
            ).fetchone()[0]
            if uses:
                raise CategoryInUseError(
                    "Cette catégorie est utilisée par des générations et ne peut pas être supprimée."
                )
            connection.execute("DELETE FROM categories WHERE id = ?", (row["id"],))

    @staticmethod
    def _category_from_row(row: sqlite3.Row) -> CategoryRecord:
        """Convertit une ligne SQLite en catégorie métier immuable."""
        return CategoryRecord(
            id=row["id"],
            slug=row["slug"],
            label=row["label"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @staticmethod
    def _record_from_row(row: sqlite3.Row) -> GenerationRecord:
        """Convertit une ligne SQLite en objet métier typé."""
        return GenerationRecord(
            id=row["id"],
            status=GenerationStatus(row["status"]),
            filename=row["filename"],
            content_type=row["content_type"],
            category=row["category_slug"],
            image_path=Path(row["source_photo_path"]) if row["source_photo_path"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            model_path=Path(row["glb_path"]) if row["glb_path"] is not None else None,
            error_message=row["error_message"],
            duration_seconds=row["duration_seconds"],
            image_warning=row["image_warning"],
            origin=ModelOrigin(row["origin"]) if "origin" in row.keys() else ModelOrigin.GENERATED,
        )

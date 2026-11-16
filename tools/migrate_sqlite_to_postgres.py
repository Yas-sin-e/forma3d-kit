# Rôle : outil de migration UNIQUE qui copie l'ancienne base SQLite (backend/data/forma3d.sqlite3)
# vers PostgreSQL : catégories, générations, clés API (empreintes) et quotas journaliers.
# Exécution (depuis la racine du dépôt, PostgreSQL démarré) :
#   python tools/migrate_sqlite_to_postgres.py --dry-run     # simulation : rien n'est écrit
#   python tools/migrate_sqlite_to_postgres.py               # migration réelle
# DATABASE_URL désigne la base cible (par défaut celle de dev.ps1 : 127.0.0.1:5433/forma3d).
"""Migration ponctuelle SQLite -> PostgreSQL, non destructive et rejouable.

Garanties :
- la base SQLite est ouverte en LECTURE SEULE (mode=ro) : elle n'est jamais modifiée ;
- tout est copié dans UNE transaction PostgreSQL : en cas d'erreur, rien n'est écrit (rollback) ;
- rejouable : une ligne déjà présente (même slug, même identifiant) est ignorée, jamais écrasée ;
- chemins portables : « C:\\...\\backend\\storage\\models\\a.glb » devient « models/a.glb » ;
- api_rate_events n'est pas copiée : ce sont des événements de la dernière minute, sans valeur après coup.
SQLite n'est plus utilisé par l'application : ce fichier ne sert qu'à cette reprise de données.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path, PureWindowsPath

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "backend"))

import psycopg  # noqa: E402

from app.repositories.factory import mask_database_url, normalize_database_url  # noqa: E402
from app.repositories.postgres_repository import PostgresGenerationRepository  # noqa: E402

DEFAULT_SQLITE = _ROOT / "backend" / "data" / "forma3d.sqlite3"
DEFAULT_STORAGE = _ROOT / "backend" / "storage"
DEFAULT_DATABASE_URL = "postgresql://forma3d:dev-password@127.0.0.1:5433/forma3d"


def portable_path(value: str | None, old_storage_root: Path) -> str | None:
    """Rend un chemin relatif au dossier de stockage s'il est dessous ; sinon le garde tel quel.

    Accepte les chemins Windows (« C:\\...\\storage\\models\\a.glb ») même si l'outil tourne sous Linux.
    """
    if not value:
        return value
    root_parts = [part.casefold() for part in PureWindowsPath(str(old_storage_root)).parts]
    path_parts = PureWindowsPath(value).parts
    if [part.casefold() for part in path_parts[: len(root_parts)]] == root_parts and len(path_parts) > len(root_parts):
        return "/".join(path_parts[len(root_parts):])
    return value


def migrate(sqlite_path: Path, database_url: str, old_storage_root: Path, *, dry_run: bool = False) -> dict[str, tuple[int, int]]:
    """Copie les données ; renvoie, par table, (lignes insérées, lignes ignorées car déjà présentes)."""
    if not sqlite_path.is_file():
        raise FileNotFoundError(f"Base SQLite introuvable : {sqlite_path}")
    url = normalize_database_url(database_url)
    # Crée le schéma cible s'il n'existe pas encore (idempotent).
    PostgresGenerationRepository(url).initialize()

    source = sqlite3.connect(f"file:{sqlite_path.as_posix()}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    report: dict[str, tuple[int, int]] = {}
    try:
        with psycopg.connect(url, options="-c TimeZone=UTC") as target:
            rows = source.execute("SELECT * FROM categories ORDER BY id").fetchall()
            inserted = 0
            for row in rows:
                inserted += target.execute(
                    "INSERT INTO categories (slug, label, is_active, created_at) VALUES (%s, %s, %s, %s)"
                    " ON CONFLICT (slug) DO NOTHING",
                    (row["slug"], row["label"], bool(row["is_active"]), row["created_at"]),
                ).rowcount
            report["categories"] = (inserted, len(rows) - inserted)

            rows = source.execute(
                "SELECT generations.*, categories.slug AS category_slug FROM generations"
                " JOIN categories ON categories.id = generations.category_id ORDER BY generations.created_at"
            ).fetchall()
            inserted = 0
            for row in rows:
                keys = row.keys()
                inserted += target.execute(
                    """
                    INSERT INTO generations (
                        id, category_id, status, filename, content_type, source_photo_path, glb_path,
                        duration_seconds, error_message, image_warning, origin, public_id, embed_enabled,
                        created_at, updated_at
                    ) VALUES (
                        %s, (SELECT id FROM categories WHERE slug = %s), %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s
                    ) ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        row["id"], row["category_slug"], row["status"], row["filename"], row["content_type"],
                        portable_path(row["source_photo_path"], old_storage_root) or "",
                        portable_path(row["glb_path"], old_storage_root),
                        row["duration_seconds"], row["error_message"],
                        row["image_warning"] if "image_warning" in keys else None,
                        row["origin"] if "origin" in keys else "generated",
                        row["public_id"] if "public_id" in keys else None,
                        bool(row["embed_enabled"]) if "embed_enabled" in keys else False,
                        row["created_at"], row["updated_at"],
                    ),
                ).rowcount
            report["generations"] = (inserted, len(rows) - inserted)

            rows = source.execute("SELECT * FROM api_keys ORDER BY created_at").fetchall()
            inserted = 0
            for row in rows:
                inserted += target.execute(
                    "INSERT INTO api_keys (id, name, prefix, fingerprint, created_at, revoked)"
                    " VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    (row["id"], row["name"], row["prefix"], row["fingerprint"], row["created_at"], bool(row["revoked"])),
                ).rowcount
            report["api_keys"] = (inserted, len(rows) - inserted)

            rows = source.execute("SELECT * FROM api_usage_daily").fetchall()
            inserted = 0
            for row in rows:
                inserted += target.execute(
                    "INSERT INTO api_usage_daily (api_key_id, usage_date, generation_count) VALUES (%s, %s, %s)"
                    " ON CONFLICT DO NOTHING",
                    (row["api_key_id"], row["usage_date"], row["generation_count"]),
                ).rowcount
            report["api_usage_daily"] = (inserted, len(rows) - inserted)

            if dry_run:
                # Simulation : on annule tout ce qui vient d'être écrit dans la transaction.
                target.rollback()
    finally:
        source.close()
    return report


def main(argv: list[str] | None = None) -> int:
    """Point d'entrée en ligne de commande ; code 0 si la migration réussit, 1 sinon."""
    parser = argparse.ArgumentParser(description="Copie l'ancienne base SQLite vers PostgreSQL (une fois).")
    parser.add_argument("--sqlite", type=Path, default=DEFAULT_SQLITE, help="fichier SQLite source")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL)
    parser.add_argument("--storage-root", type=Path, default=DEFAULT_STORAGE,
                        help="ancien dossier de stockage, pour rendre les chemins relatifs")
    parser.add_argument("--dry-run", action="store_true", help="simuler sans rien écrire")
    args = parser.parse_args(argv)

    print(f"Source : {args.sqlite}")
    print(f"Cible  : {mask_database_url(args.database_url)}")
    print("Mode   : SIMULATION (rien n'est écrit)" if args.dry_run else "Mode   : migration réelle")
    try:
        report = migrate(args.sqlite, args.database_url, args.storage_root, dry_run=args.dry_run)
    except Exception as error:  # message lisible puis code 1, sans trace inutile pour l'utilisatrice
        print(f"[ECHEC] {type(error).__name__} : {error}", file=sys.stderr)
        return 1
    for table, (inserted, skipped) in report.items():
        print(f"  {table:16} {inserted:3} insérée(s), {skipped:3} déjà présente(s)")
    print("[SUCCES] simulation terminée." if args.dry_run else "[SUCCES] migration terminée.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

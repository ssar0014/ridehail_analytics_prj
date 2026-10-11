"""
Simple migration runner.

Migrations are plain .sql files in the migrations/ directory, named with a
numeric prefix (e.g. 001_create_schema.sql). They are applied in filename
order and tracked in a schema_migrations table so they only run once.

Usage:
    uv run python db/migrate.py           # apply pending migrations
    uv run python db/migrate.py --reset   # drop everything and re-run all migrations
"""

import sys
from pathlib import Path

import psycopg

from db.connection import get_conn

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"

_CREATE_TRACKING_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
"""


def _applied_versions(conn: psycopg.Connection) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations;")
        return {row[0] for row in cur.fetchall()}


def _apply(conn: psycopg.Connection, path: Path) -> None:
    sql = path.read_text()
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute(
            "INSERT INTO schema_migrations (version) VALUES (%s);",
            (path.name,),
        )
    conn.commit()
    print(f"  applied  {path.name}")


def _reset(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS public CASCADE;")
        cur.execute("CREATE SCHEMA public;")
        cur.execute("GRANT ALL ON SCHEMA public TO PUBLIC;")
        cur.execute("GRANT ALL ON SCHEMA public TO CURRENT_USER;")
        cur.execute("SET search_path TO public;")
    conn.commit()
    print("  schema reset")


def run(reset: bool = False) -> None:
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print("No migration files found.")
        return

    with get_conn() as conn:
        if reset:
            print("Resetting schema ...")
            _reset(conn)

        with conn.cursor() as cur:
            cur.execute(_CREATE_TRACKING_TABLE)
        conn.commit()

        applied = _applied_versions(conn)

        pending = [f for f in migration_files if f.name not in applied]
        if not pending:
            print("All migrations already applied.")
            return

        print(f"Applying {len(pending)} migration(s):")
        for f in pending:
            _apply(conn, f)

    print("Done.")


if __name__ == "__main__":
    run(reset="--reset" in sys.argv)

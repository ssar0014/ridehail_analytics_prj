import os
from contextlib import contextmanager
from typing import Generator

import psycopg

_DSN = os.getenv(
    "DATABASE_URL",
    "postgresql://ridehail:ridehail@localhost:5432/ridehail_db",
)


@contextmanager
def get_conn() -> Generator[psycopg.Connection, None, None]:
    with psycopg.connect(_DSN) as conn:
        yield conn


@contextmanager
def get_cursor(autocommit: bool = False) -> Generator[psycopg.Cursor, None, None]:
    with psycopg.connect(_DSN, autocommit=autocommit) as conn:
        with conn.cursor() as cur:
            yield cur

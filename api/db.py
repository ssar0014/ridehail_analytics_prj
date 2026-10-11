"""
Database handles for the API.

Postgres: an async psycopg connection pool, opened in the app lifespan.
ClickHouse: an async HTTP client, created lazily on first use so the API can
start (and serve Postgres-backed routes) while ClickHouse is still down.
"""

import asyncio
from typing import Annotated, Any, AsyncIterator

import clickhouse_connect
from clickhouse_connect.driver.asyncclient import AsyncClient
from fastapi import Depends, HTTPException, Request, status
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from api.config import Settings


def create_pg_pool(settings: Settings) -> AsyncConnectionPool:
    return AsyncConnectionPool(
        conninfo=settings.database_url,
        min_size=settings.pg_pool_min_size,
        max_size=settings.pg_pool_max_size,
        kwargs={"row_factory": dict_row},
        timeout=5,  # seconds to wait for a free/working connection before erroring
        open=False,
    )


class ClickHouse:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncClient | None = None
        self._lock = asyncio.Lock()

    async def client(self) -> AsyncClient:
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    s = self._settings
                    self._client = await clickhouse_connect.get_async_client(
                        host=s.clickhouse_host,
                        port=s.clickhouse_port,
                        username=s.clickhouse_user,
                        password=s.clickhouse_password,
                        database=s.clickhouse_database,
                    )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None


async def get_pg(request: Request) -> AsyncIterator[AsyncConnection[dict[str, Any]]]:
    pool: AsyncConnectionPool = request.app.state.pg_pool
    async with pool.connection() as conn:
        yield conn


async def get_ch(request: Request) -> AsyncClient:
    try:
        return await request.app.state.clickhouse.client()
    except Exception as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"ClickHouse unavailable: {exc}")


PgConn = Annotated[AsyncConnection[dict[str, Any]], Depends(get_pg)]
ChClient = Annotated[AsyncClient, Depends(get_ch)]

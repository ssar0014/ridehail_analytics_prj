import asyncio

from fastapi import APIRouter, Request

from api.schemas import Health, ServiceHealth

router = APIRouter(tags=["health"])

_TIMEOUT_S = 3


async def _postgres(request: Request) -> ServiceHealth:
    try:
        async with asyncio.timeout(_TIMEOUT_S):
            async with request.app.state.pg_pool.connection(timeout=_TIMEOUT_S) as conn:
                cur = await conn.execute("SHOW server_version")
                row = await cur.fetchone()
        return ServiceHealth(ok=True, detail=f"PostgreSQL {row['server_version']}")
    except Exception as exc:
        return ServiceHealth(ok=False, detail=str(exc) or type(exc).__name__)


async def _clickhouse(request: Request) -> ServiceHealth:
    try:
        async with asyncio.timeout(_TIMEOUT_S):
            client = await request.app.state.clickhouse.client()
            version = await client.command("SELECT version()")
        return ServiceHealth(ok=True, detail=f"ClickHouse {version}")
    except Exception as exc:
        return ServiceHealth(ok=False, detail=str(exc) or type(exc).__name__)


@router.get("/health", response_model=Health)
async def health(request: Request) -> Health:
    pg, ch = await asyncio.gather(_postgres(request), _clickhouse(request))
    return Health(status="ok" if pg.ok and ch.ok else "degraded", postgres=pg, clickhouse=ch)

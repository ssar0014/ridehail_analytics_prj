"""
FastAPI backend for the RideHail web app.

Usage:
    uv run uvicorn api.main:app --reload     # http://localhost:8000/api/docs
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.db import ClickHouse, create_pg_pool
from api.routers import admin, auth, customer, driver, health

log = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.using_dev_jwt_secret:
        log.warning("JWT_SECRET is not set — using the insecure development default")

    app.state.pg_pool = create_pg_pool(settings)
    await app.state.pg_pool.open(wait=False)  # don't block startup if Postgres is down
    app.state.clickhouse = ClickHouse(settings)
    try:
        yield
    finally:
        await app.state.clickhouse.close()
        await app.state.pg_pool.close()


# Docs live under /api too, so they're reachable through the web proxy
app = FastAPI(
    title="RideHail API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (health.router, auth.router, admin.router, driver.router, customer.router):
    app.include_router(r, prefix="/api")

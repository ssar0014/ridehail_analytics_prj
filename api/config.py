from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_JWT_SECRET = "dev-only-insecure-jwt-secret-change-me"


class Settings(BaseSettings):
    """API settings, read from environment variables (or a .env file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres (OLTP) — same variable db/connection.py reads
    database_url: str = "postgresql://ridehail:ridehail@localhost:5432/ridehail_db"
    pg_pool_min_size: int = 1
    pg_pool_max_size: int = 10

    # ClickHouse (OLAP)
    clickhouse_host: str = "localhost"
    clickhouse_port: int = 8123
    clickhouse_user: str = "ridehail"
    clickhouse_password: str = "ridehail"
    clickhouse_database: str = "ridehail"

    # Auth
    jwt_secret: str = Field(_DEV_JWT_SECRET, min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60

    # Frontend dev server origin(s); JSON list when set via env
    cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def using_dev_jwt_secret(self) -> bool:
        return self.jwt_secret == _DEV_JWT_SECRET


@lru_cache
def get_settings() -> Settings:
    return Settings()

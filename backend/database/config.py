"""Database configuration driven by environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

DEFAULT_DATABASE_URL = "postgresql+psycopg2://amruser:amrpass@localhost:5432/amrdb"


@dataclass(frozen=True)
class DatabaseConfig:
    """Holds the connection URL and engine tuning options."""

    url: str = field(
        default_factory=lambda: os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    )
    echo: bool = field(
        default_factory=lambda: os.getenv("DB_ECHO", "false").lower() == "true"
    )
    pool_size: int = field(default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "10")))
    max_overflow: int = field(
        default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "20"))
    )
    pool_pre_ping: bool = field(
        default_factory=lambda: os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
    )


@lru_cache(maxsize=1)
def get_database_config() -> DatabaseConfig:
    """Return a cached :class:`DatabaseConfig` instance."""
    return DatabaseConfig()
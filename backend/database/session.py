"""Engine and session management for the MVP schema."""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from .base import Base
from .config import get_database_config


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create (once) and return the application's SQLAlchemy engine."""
    config = get_database_config()
    return create_engine(
        config.url,
        echo=config.echo,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_pre_ping=config.pool_pre_ping,
        future=True,
    )


@lru_cache(maxsize=1)
def get_sessionmaker() -> sessionmaker[Session]:
    """Return a cached session factory bound to the engine."""
    return sessionmaker(
        bind=get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


class _SessionLocal:
    """Lazy proxy so importing models never instantiates the engine.

    Calling ``SessionLocal()`` builds the engine on first use; importing this
    module (and therefore the models) does not require a live database driver.
    """

    def __call__(self) -> Session:
        return get_sessionmaker()()


SessionLocal = _SessionLocal()


def get_session() -> Iterator[Session]:
    """Yield a database session, closing it when the caller is done."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Create all MVP tables in the configured database.

    Importing the models module registers every table on ``Base.metadata``
    before ``create_all`` runs.
    """
    import backend.models  # noqa: F401  (ensures models are registered)

    Base.metadata.create_all(bind=get_engine())
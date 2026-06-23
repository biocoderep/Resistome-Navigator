"""Database session and connection management."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use Postgres if provided by docker-compose, otherwise fallback to local sqlite MVP
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///amr_mvp.db")

# connect_args={"check_same_thread": False} is needed only for SQLite
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
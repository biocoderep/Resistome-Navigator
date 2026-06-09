"""Base SQLAlchemy definitions and mixins."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Utility to generate UUID4 as a string for SQLite compatibility
# Since SQLite doesn't have a native UUID type, we'll use string representations of UUIDs.
# SQLAlchemy's UUIDType can handle this, but for simplicity in MVP we often use String(36).
# However, SQLAlchemy 2.0 has built-in Uuid type which handles UUID objects correctly across dialects.
from sqlalchemy import Uuid

def generate_uuid():
    return uuid.uuid4()

def utcnow():
    return datetime.now(timezone.utc)

class TimestampMixin:
    """Mixin to add created_at and updated_at columns."""
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class SoftDeleteMixin:
    """Mixin to add soft-delete capability."""
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

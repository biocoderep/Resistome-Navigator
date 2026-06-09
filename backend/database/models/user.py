"""User stub model for FK integrity."""

from sqlalchemy import Column, String, Boolean
from sqlalchemy import Uuid
from .base import Base, TimestampMixin, SoftDeleteMixin, generate_uuid

class User(Base, TimestampMixin, SoftDeleteMixin):
    """Stub representation of users table."""
    __tablename__ = "users"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)

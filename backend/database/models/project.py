"""Project stub model for FK integrity."""

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy import Uuid
from .base import Base, TimestampMixin, SoftDeleteMixin, generate_uuid

class Project(Base, TimestampMixin, SoftDeleteMixin):
    """Stub representation of projects table."""
    __tablename__ = "projects"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    owner_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

"""Reference database stub models for FK integrity."""

from sqlalchemy import Column, String, Boolean, Integer, SmallInteger, ForeignKey
from sqlalchemy import Uuid
from .base import Base, TimestampMixin, generate_uuid

class ReferenceDatabase(Base):
    """Stub representation of reference_databases table."""
    __tablename__ = "reference_databases"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    short_code = Column(String(30), unique=True, nullable=False)
    data_type = Column(String(50), nullable=False)

class DatabaseVersion(Base):
    """Stub representation of database_versions table."""
    __tablename__ = "database_versions"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=generate_uuid)
    db_id = Column(Integer, ForeignKey("reference_databases.id"), nullable=False)
    version = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

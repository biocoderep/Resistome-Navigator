"""Sample and assembly management models."""

from sqlalchemy import Column, String, Integer, BigInteger, Date, Float, ForeignKey, DateTime
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from sqlalchemy import Uuid
from .base import Base, TimestampMixin, SoftDeleteMixin, generate_uuid, utcnow
from sqlalchemy.schema import UniqueConstraint

class Sample(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "samples"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=generate_uuid)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    isolate_name = Column(String(200), nullable=False)
    species = Column(String(200))
    species_taxid = Column(Integer)
    host = Column(String(100))
    collection_date = Column(Date)
    source_type = Column(String(100))
    location = Column(String(200))
    country_code = Column(String(3))
    submitter_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    status = Column(String(30), nullable=False, default="UPLOADED")

    # Relationships
    project = relationship("Project")
    submitter = relationship("User")
    files = relationship("SampleFile", back_populates="sample", cascade="all, delete-orphan")
    metadata_entries = relationship("SampleMetadata", back_populates="sample", cascade="all, delete-orphan")
    assemblies = relationship("Assembly", back_populates="sample", cascade="all, delete-orphan")

class SampleMetadata(Base):
    __tablename__ = "sample_metadata"
    __table_args__ = (UniqueConstraint('sample_id', 'key', name='uq_sample_meta'),)
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=generate_uuid)
    sample_id = Column(Uuid(as_uuid=True), ForeignKey("samples.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(100), nullable=False)
    value = Column(String)
    value_type = Column(String(20), default="string")
    
    sample = relationship("Sample", back_populates="metadata_entries")

class SampleFile(Base):
    __tablename__ = "sample_files"
    __table_args__ = (UniqueConstraint('sample_id', 'file_type', name='uq_sample_file_type'),)
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=generate_uuid)
    sample_id = Column(Uuid(as_uuid=True), ForeignKey("samples.id", ondelete="CASCADE"), nullable=False)
    file_type = Column(String(50), nullable=False)
    storage_path = Column(String(500), nullable=False)
    storage_backend = Column(String(50), default="minio")
    filename = Column(String(255), nullable=False)
    file_size_bytes = Column(BigInteger)
    checksum_sha256 = Column(String(64), nullable=False)
    upload_status = Column(String(30), default="COMPLETE")
    uploaded_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    sample = relationship("Sample", back_populates="files")

class Assembly(Base, TimestampMixin):
    __tablename__ = "assemblies"
    __table_args__ = (UniqueConstraint('sample_id', 'assembly_version', name='uq_assembly_sample'),)
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=generate_uuid)
    sample_id = Column(Uuid(as_uuid=True), ForeignKey("samples.id", ondelete="CASCADE"), nullable=False)
    assembly_version = Column(String(20), default="1.0")
    assembler = Column(String(100))
    assembler_version = Column(String(30))
    input_file_id = Column(Uuid(as_uuid=True), ForeignKey("sample_files.id", ondelete="SET NULL"))
    validated_fasta_path = Column(String(500))
    
    sample = relationship("Sample", back_populates="assemblies")
    metrics = relationship("AssemblyMetrics", back_populates="assembly", uselist=False, cascade="all, delete-orphan")

class AssemblyMetrics(Base):
    __tablename__ = "assembly_metrics"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=generate_uuid)
    assembly_id = Column(Uuid(as_uuid=True), ForeignKey("assemblies.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_length_bp = Column(BigInteger)
    contig_count = Column(Integer)
    n50_bp = Column(Integer)
    n90_bp = Column(Integer)
    gc_percent = Column(Float)
    n_percent = Column(Float)
    longest_contig = Column(Integer)
    shortest_contig = Column(Integer)
    l50 = Column(Integer)
    species_prediction = Column(String(200))
    species_confidence = Column(Float)
    validation_status = Column(String(20), default="PENDING")
    validation_warnings = Column(JSON)
    validation_errors = Column(JSON)
    computed_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    assembly = relationship("Assembly", back_populates="metrics")

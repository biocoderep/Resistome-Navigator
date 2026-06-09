"""AMR Detection models."""

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from sqlalchemy import Uuid
from .base import Base, generate_uuid, utcnow
from sqlalchemy.schema import UniqueConstraint

class AMRGene(Base):
    __tablename__ = "amr_genes"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=generate_uuid)
    sample_id = Column(Uuid(as_uuid=True), ForeignKey("samples.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Uuid(as_uuid=True), ForeignKey("analysis_jobs.id", ondelete="SET NULL"))
    db_version_id = Column(Uuid(as_uuid=True), ForeignKey("database_versions.id", ondelete="RESTRICT"), nullable=False)
    
    gene_name = Column(String(200), nullable=False)
    gene_family = Column(String(200))
    aro_accession = Column(String(50))
    drug_class = Column(String(200))
    resistance_mechanism = Column(String(100))
    antibiotic_class = Column(String(200))
    mechanism_type = Column(String(50))
    confidence_tier = Column(String(20), default="MEDIUM")
    confidence_score = Column(Float)
    
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    sample = relationship("Sample")
    job = relationship("AnalysisJob")
    db_version = relationship("DatabaseVersion")
    hits = relationship("AMRHit", back_populates="amr_gene", cascade="all, delete-orphan")
    annotations = relationship("AMRAnnotation", back_populates="amr_gene", cascade="all, delete-orphan")

class AMRHit(Base):
    __tablename__ = "amr_hits"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=generate_uuid)
    amr_gene_id = Column(Uuid(as_uuid=True), ForeignKey("amr_genes.id", ondelete="CASCADE"), nullable=False)
    detection_tool = Column(String(50), nullable=False)
    hit_category = Column(String(20), nullable=False)
    identity_pct = Column(Float, nullable=False)
    coverage_pct = Column(Float, nullable=False)
    contig_id = Column(String(200))
    contig_start = Column(Integer)
    contig_end = Column(Integer)
    strand = Column(String(1))
    reference_length = Column(Integer)
    query_length = Column(Integer)
    partial_hit = Column(Boolean, nullable=False, default=False)
    raw_result_json = Column(JSON)
    detected_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    amr_gene = relationship("AMRGene", back_populates="hits")

class AMRAnnotation(Base):
    __tablename__ = "amr_annotations"
    __table_args__ = (UniqueConstraint('amr_gene_id', 'annotation_source', 'key', name='uq_amr_annotation'),)
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=generate_uuid)
    amr_gene_id = Column(Uuid(as_uuid=True), ForeignKey("amr_genes.id", ondelete="CASCADE"), nullable=False)
    annotation_source = Column(String(50))
    key = Column(String(100), nullable=False)
    value = Column(String)
    
    amr_gene = relationship("AMRGene", back_populates="annotations")

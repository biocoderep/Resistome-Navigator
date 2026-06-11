from typing import Any, Dict, List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.session import get_session
from backend.models.sample import Sample
from backend.models.amr_gene import AmrGene
from backend.models.amr_hit import AmrHit

router = APIRouter(prefix="/isolates", tags=["isolates"])

@router.get("/cohort-metadata", response_model=List[Dict[str, Any]])
def get_cohort_metadata(
    batch_id: uuid.UUID | None = None,
    db: Session = Depends(get_session)
):
    query = select(Sample)
    if batch_id:
        query = query.where(Sample.batch_id == str(batch_id))
    samples = db.execute(query).scalars().all()
    
    return [{
        "sample_id": str(s.id),
        "isolate_name": s.isolate_name,
        "organism": s.species,
        "collection_date": s.collection_date.isoformat() if s.collection_date else None,
        "region": s.location,
        "project_id": s.project_id
    } for s in samples]

@router.get("/{sample_id}/metadata", response_model=Dict[str, Any])
def get_isolate_metadata(sample_id: uuid.UUID, db: Session = Depends(get_session)):
    s = db.execute(select(Sample).where(Sample.id == sample_id)).scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Sample not found")
    return {
        "sample_id": str(s.id),
        "isolate_name": s.isolate_name,
        "organism": s.species,
        "collection_date": s.collection_date.isoformat() if s.collection_date else None,
        "region": s.location,
        "project_id": s.project_id
    }

@router.get("/{sample_id}/amr-genes", response_model=List[Dict[str, Any]])
def get_isolate_amr_genes(sample_id: uuid.UUID, db: Session = Depends(get_session)):
    genes = db.execute(select(AmrGene).where(AmrGene.sample_id == sample_id)).scalars().all()
    # Assuming hits are mapped for coverage/identity
    return [{
        "sample_id": str(g.sample_id),
        "gene_name": g.gene_name,
        "database_source": "CARD", # Mock mapping
        "identity_pct": 100.0, # Placeholder until hit join
        "coverage_pct": 100.0,
        "contig_id": "contig_1",
        "start": 0,
        "end": 1000,
        "strand": "+",
        "drug_class": g.antibiotic_class or "Unknown",
        "mechanism_type": g.resistance_mechanism or "antibiotic_inactivation",
        "confidence_score": float(g.confidence_score) if g.confidence_score else 100.0
    } for g in genes]

from backend.models.virulence_gene import VirulenceGene
from backend.models.resistance_mutation import ResistanceMutation
from backend.models.phenotype_prediction import PhenotypePrediction
from backend.models.confidence_score import ConfidenceScore

@router.get("/{sample_id}/mutations", response_model=List[Dict[str, Any]])
def get_isolate_mutations(sample_id: uuid.UUID, db: Session = Depends(get_session)):
    muts = db.execute(select(ResistanceMutation).where(ResistanceMutation.sample_id == sample_id)).scalars().all()
    return [{
        "sample_id": str(m.sample_id),
        "gene_name": m.gene_name,
        "mutation": m.mutation,
        "mechanism": m.mechanism,
        "effect": m.effect,
        "identity_pct": float(m.identity_percent) if m.identity_percent else 100.0,
        "coverage_pct": float(m.coverage_percent) if m.coverage_percent else 100.0,
        "database_source": m.database_source or "CARD"
    } for m in muts]

@router.get("/mechanisms", response_model=List[Dict[str, Any]])
def get_mechanisms(db: Session = Depends(get_session)):
    # Global mechanism classifications. Model not yet implemented.
    return []

@router.get("/{sample_id}/phenotypes", response_model=List[Dict[str, Any]])
def get_isolate_phenotypes(sample_id: uuid.UUID, db: Session = Depends(get_session)):
    preds = db.execute(select(PhenotypePrediction).where(PhenotypePrediction.sample_id == sample_id)).scalars().all()
    return [{
        "sample_id": str(p.sample_id),
        "antibiotic": p.drug,
        "antibiotic_class": p.drug_class,
        "predicted_sir": p.predicted_sir,
        "confidence_score": float(p.confidence_score) if p.confidence_score else None,
        "confidence_tier": p.confidence_tier,
        "breakpoint_source": p.breakpoint_source,
        "breakpoint_version": p.breakpoint_version,
        "is_not_testable": p.is_not_testable,
        "has_conflict": p.has_conflict,
        "supporting_genes": p.supporting_genes,
        "supporting_mutations": p.supporting_mutations,
        "explanation": p.explanation
    } for p in preds]

@router.get("/{sample_id}/virulence", response_model=List[Dict[str, Any]])
def get_isolate_virulence(sample_id: uuid.UUID, db: Session = Depends(get_session)):
    virs = db.execute(select(VirulenceGene).where(VirulenceGene.sample_id == sample_id)).scalars().all()
    return [{
        "sample_id": str(v.sample_id),
        "gene_name": v.gene_name,
        "virulence_factor": v.virulence_factor,
        "mechanism": v.mechanism,
        "contig_id": v.contig_id,
        "start_position": v.start_position,
        "end_position": v.end_position,
        "identity_pct": float(v.identity_percent) if v.identity_percent else 100.0,
        "coverage_pct": float(v.coverage_percent) if v.coverage_percent else 100.0,
        "database_source": v.database_source or "VFDB"
    } for v in virs]

@router.get("/{sample_id}/confidence", response_model=List[Dict[str, Any]])
def get_isolate_confidence(sample_id: uuid.UUID, db: Session = Depends(get_session)):
    confs = db.execute(select(ConfidenceScore).where(ConfidenceScore.sample_id == sample_id)).scalars().all()
    return [{
        "sample_id": str(c.sample_id),
        "context": c.context,
        "target_name": c.target_name,
        "overall_score": float(c.overall_score),
        "tier": c.tier,
        "cap_applied": c.cap_applied,
        "components": c.components,
        "weighted": c.weighted
    } for c in confs]

@router.get("/{sample_id}/assembly-metrics", response_model=List[Dict[str, Any]])
def get_isolate_assembly_metrics(sample_id: uuid.UUID, db: Session = Depends(get_session)):
    # Assuming Assembly model has this, returning empty for now to match contract
    return []

# Cohort-level bulk endpoints
@router.get("/cohort-amr-genes", response_model=List[Dict[str, Any]])
def get_cohort_amr_genes(batch_id: uuid.UUID | None = None, db: Session = Depends(get_session)):
    query = select(AmrGene)
    if batch_id:
        query = query.join(Sample, Sample.id == AmrGene.sample_id).where(Sample.batch_id == str(batch_id))
    genes = db.execute(query).scalars().all()
    return [{
        "sample_id": str(g.sample_id),
        "gene_name": g.gene_name,
        "database_source": "CARD",
        "identity_pct": 100.0,
        "coverage_pct": 100.0,
        "contig_id": "contig_1",
        "start": 0,
        "end": 1000,
        "strand": "+",
        "drug_class": g.antibiotic_class or "Unknown",
        "mechanism_type": g.resistance_mechanism or "antibiotic_inactivation",
        "confidence_score": float(g.confidence_score) if g.confidence_score else 100.0
    } for g in genes]

@router.get("/cohort-phenotypes", response_model=List[Dict[str, Any]])
def get_cohort_phenotypes(batch_id: uuid.UUID | None = None, db: Session = Depends(get_session)):
    query = select(PhenotypePrediction)
    if batch_id:
        query = query.join(Sample, Sample.id == PhenotypePrediction.sample_id).where(Sample.batch_id == str(batch_id))
    preds = db.execute(query).scalars().all()
    return [{
        "sample_id": str(p.sample_id),
        "antibiotic": p.drug,
        "antibiotic_class": p.drug_class,
        "predicted_sir": p.predicted_sir,
        "confidence_score": float(p.confidence_score) if p.confidence_score else None,
        "confidence_tier": p.confidence_tier,
        "breakpoint_source": p.breakpoint_source,
        "breakpoint_version": p.breakpoint_version,
        "is_not_testable": p.is_not_testable,
        "has_conflict": p.has_conflict,
        "supporting_genes": p.supporting_genes,
        "supporting_mutations": p.supporting_mutations,
        "explanation": p.explanation
    } for p in preds]

@router.get("/cohort-mutations", response_model=List[Dict[str, Any]])
def get_cohort_mutations(batch_id: uuid.UUID | None = None, db: Session = Depends(get_session)):
    query = select(ResistanceMutation)
    if batch_id:
        query = query.join(Sample, Sample.id == ResistanceMutation.sample_id).where(Sample.batch_id == str(batch_id))
    muts = db.execute(query).scalars().all()
    return [{
        "sample_id": str(m.sample_id),
        "gene_name": m.gene_name,
        "mutation": m.mutation,
        "mechanism": m.mechanism,
        "effect": m.effect,
        "identity_pct": float(m.identity_percent) if m.identity_percent else 100.0,
        "coverage_pct": float(m.coverage_percent) if m.coverage_percent else 100.0,
        "database_source": m.database_source or "CARD"
    } for m in muts]

@router.get("/cohort-virulence", response_model=List[Dict[str, Any]])
def get_cohort_virulence(batch_id: uuid.UUID | None = None, db: Session = Depends(get_session)):
    query = select(VirulenceGene)
    if batch_id:
        query = query.join(Sample, Sample.id == VirulenceGene.sample_id).where(Sample.batch_id == str(batch_id))
    virs = db.execute(query).scalars().all()
    return [{
        "sample_id": str(v.sample_id),
        "gene_name": v.gene_name,
        "virulence_factor": v.virulence_factor,
        "mechanism": v.mechanism,
        "contig_id": v.contig_id,
        "start_position": v.start_position,
        "end_position": v.end_position,
        "identity_pct": float(v.identity_percent) if v.identity_percent else 100.0,
        "coverage_pct": float(v.coverage_percent) if v.coverage_percent else 100.0,
        "database_source": v.database_source or "VFDB"
    } for v in virs]

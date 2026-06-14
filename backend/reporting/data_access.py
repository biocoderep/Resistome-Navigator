"""Assemble report-ready dicts from the database.

These builders reconstruct the report payloads consumed by
``backend.reporting.pdf_report`` from the normalised ORM tables, so the server
can generate a PDF on demand without the original Nextflow ``isolate_report.json``
on disk.

Note: the DB schema is slightly lossy versus the full pipeline report (e.g.
``AmrGene`` does not persist per-gene identity/coverage except via ``AmrHit``,
and mutation classification/SIR are not stored). For maximum-fidelity reports,
render the Nextflow ``isolate_report.json`` directly via the ``amr-pipeline
report`` CLI command.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.models.amr_gene import AmrGene
from backend.models.batch import Batch, CohortResult
from backend.models.confidence_score import ConfidenceScore
from backend.models.phenotype_prediction import PhenotypePrediction
from backend.models.resistance_mutation import ResistanceMutation
from backend.models.sample import Sample
from backend.models.virulence_gene import VirulenceGene


def _f(value: Any) -> Optional[float]:
    return None if value is None else float(value)


def _best_hit(gene: AmrGene):
    hits = list(getattr(gene, "hits", []) or [])
    if not hits:
        return None
    return max(hits, key=lambda h: (h.identity or 0))


def build_isolate_report(db: Session, sample_id: uuid.UUID | str) -> Dict[str, Any]:
    """Reconstruct a single-isolate report dict from the database."""
    sid = sample_id if isinstance(sample_id, uuid.UUID) else uuid.UUID(str(sample_id))
    sample = db.get(Sample, sid)

    genes = db.scalars(
        select(AmrGene)
        .options(selectinload(AmrGene.hits))
        .where(AmrGene.sample_id == sid)
    ).all()
    virs = db.scalars(select(VirulenceGene).where(VirulenceGene.sample_id == sid)).all()
    muts = db.scalars(select(ResistanceMutation).where(ResistanceMutation.sample_id == sid)).all()
    phenos = db.scalars(select(PhenotypePrediction).where(PhenotypePrediction.sample_id == sid)).all()
    confs = db.scalars(select(ConfidenceScore).where(ConfidenceScore.sample_id == sid)).all()

    amr_genes: List[Dict[str, Any]] = []
    for g in genes:
        hit = _best_hit(g)
        amr_genes.append({
            "gene_name": g.gene_name,
            "gene_family": g.gene_family,
            "antibiotic_class": g.antibiotic_class,
            "drug_class": g.antibiotic_class,
            "resistance_mechanism": g.resistance_mechanism,
            "identity_percent": _f(hit.identity) if hit else None,
            "coverage_percent": _f(hit.coverage) if hit else None,
            "tool_name": hit.tool_name if hit else None,
            "confidence_score": _f(g.confidence_score),
        })

    virulence_genes = [{
        "gene_name": v.gene_name,
        "virulence_factor": v.virulence_factor,
        "virulence_category": v.virulence_factor or v.mechanism,
        "mechanism": v.mechanism,
        "identity_percent": _f(v.identity_percent),
        "coverage_percent": _f(v.coverage_percent),
        "contig_id": v.contig_id,
        "start_position": v.start_position,
        "end_position": v.end_position,
        "is_high_risk": False,
        "risk_weight": 0.0,
        "database_source": v.database_source,
    } for v in virs]

    mutations = [{
        "gene_name": m.gene_name,
        "mutation": m.mutation,
        "effect": m.effect,
        "mechanism": m.mechanism,
        "classification": None,
        "drug_class": None,
        "sir_prediction": None,
        "identity_percent": _f(m.identity_percent),
        "coverage_percent": _f(m.coverage_percent),
    } for m in muts]

    phenotypes = [{
        "drug": p.drug,
        "drug_class": p.drug_class,
        "predicted_sir": p.predicted_sir,
        "confidence_score": _f(p.confidence_score),
        "confidence_tier": p.confidence_tier,
        "breakpoint_source": p.breakpoint_source,
        "breakpoint_version": p.breakpoint_version,
        "is_not_testable": p.is_not_testable,
        "has_conflict": p.has_conflict,
        "supporting_genes": p.supporting_genes or [],
        "supporting_mutations": p.supporting_mutations or [],
        "explanation": p.explanation,
    } for p in phenos]

    confidence_scores = [{
        "context": c.context,
        "target_name": c.target_name,
        "overall_score": _f(c.overall_score),
        "tier": c.tier,
        "cap_applied": c.cap_applied,
        "components": c.components or {},
        "weighted": c.weighted or {},
    } for c in confs]

    # Derive mechanisms by grouping genes/mutations on their mechanism label.
    mech_map: Dict[str, Dict[str, Any]] = {}
    for g in genes:
        code = g.resistance_mechanism or "unknown"
        entry = mech_map.setdefault(code, {"genes": [], "mutations": [], "classes": set()})
        entry["genes"].append(g.gene_name)
        if g.antibiotic_class:
            entry["classes"].add(g.antibiotic_class)
    for m in muts:
        code = m.mechanism or "unknown"
        entry = mech_map.setdefault(code, {"genes": [], "mutations": [], "classes": set()})
        entry["mutations"].append(m.mutation)
    mechanisms = [{
        "mechanism_code": code,
        "mechanism_name": code.replace("_", " ").title(),
        "drug_classes": sorted(data["classes"]),
        "supporting_genes": data["genes"],
        "supporting_mutations": data["mutations"],
        "evidence_sources": [],
        "confidence": 0.0,
        "confidence_tier": "-",
    } for code, data in mech_map.items()]

    vf_count = len(virulence_genes)
    risk_score = min(vf_count * 20.0, 100.0)
    risk_class = ("CRITICAL" if risk_score >= 75 else "HIGH" if risk_score >= 50
                  else "MODERATE" if risk_score >= 25 else "LOW")

    resistance_classes = sorted({g["drug_class"] for g in amr_genes if g["drug_class"]})

    return {
        "report_version": "2.0",
        "sample_id": str(sid),
        "species": sample.species if sample else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_stage": "Module 1 - AMR Characterisation",
        "genome_quality": "N/A",
        "validation_status": sample.status if sample else None,
        "amr_genes": amr_genes,
        "virulence_genes": virulence_genes,
        "mutations": mutations,
        "mechanisms": mechanisms,
        "drug_associations": [],
        "phenotypes": phenotypes,
        "confidence_scores": confidence_scores,
        "pathogenicity": {
            "total_vf_genes": vf_count,
            "category_diversity": len({v["virulence_category"] for v in virulence_genes}),
            "high_risk_count": 0,
            "high_risk_genes": [],
            "risk_score": risk_score,
            "risk_class": risk_class,
        },
        "summary": {
            "total_amr_genes": len(amr_genes),
            "total_virulence_genes": vf_count,
            "total_mutations": len(mutations),
            "total_mechanisms": len(mechanisms),
            "total_resistant_phenotypes": sum(1 for p in phenotypes if p["predicted_sir"] == "R"),
            "resistance_classes": resistance_classes,
        },
    }


def build_cohort_report(db: Session, batch_id: str) -> Dict[str, Any]:
    """Assemble a cohort report dict from CohortResult rows + batch metadata."""
    batch = db.get(Batch, str(batch_id))
    rows = db.scalars(
        select(CohortResult).where(CohortResult.batch_id == str(batch_id))
    ).all()
    by_type = {r.analysis_type: r.result_json for r in rows}

    return {
        "batch_id": str(batch_id),
        "batch_name": batch.batch_name if batch else None,
        "total_isolates": (batch.total_isolates if batch else None),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "antibiogram": by_type.get("cohort_antibiogram_summary", []),
        "population_barcode": by_type.get("population_barcode", {}),
        "gene_cooccurrence_network": by_type.get("gene_cooccurrence_network", {}),
        "resistome_umap": by_type.get("resistome_umap", []),
    }


__all__ = ["build_isolate_report", "build_cohort_report"]

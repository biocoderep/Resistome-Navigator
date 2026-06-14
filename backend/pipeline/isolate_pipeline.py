"""Per-isolate analysis orchestrator.

Given an assembly plus the upstream genome-validation and AMR-detection JSON
reports, this runs the mutation, mechanism, virulence, phenotype and confidence
engines in-process and assembles the canonical :class:`IsolateReport`.

Running the dependency-coupled engines (mutation -> mechanism -> phenotype ->
confidence) in a single process avoids fragile serialisation of intermediate
dataclasses across Nextflow process boundaries, while the individual engines
remain independently importable/testable. The same per-isolate code path is used
for one sample and for every sample in a 50-isolate cohort.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.amr_confidence.finding_scorer import score_finding
from backend.mutation_engine.mutation_detection_engine import MutationDetectionEngine
from backend.mutation_engine.mechanism_classification_engine import (
    MechanismClassificationEngine,
    _normalise_drug_class,
)
from backend.virulence_engine.virulence_classifier import VirulenceClassifier
from backend.virulence_engine.adapters.vfdb_adapter import VFDBAdapter
from backend.virulence_engine.pathogenicity_profile import compute_pathogenicity_profile
from backend.virulence_engine.result_models import VirulenceFactor
from backend.phenotype_engine.rule_repository import RuleRepository
from backend.phenotype_engine.inference.phenotype_inference import (
    PhenotypeInferenceEngine,
)
from backend.phenotype_engine.inference.confidence_propagation import ConfidencePropagator
from backend.phenotype_engine.breakpoints.eucast_adapter import EUCASTAdapter
from backend.phenotype_engine.result_models import AMRGeneResult

from .report_schema import (
    IsolateReport,
    AmrGeneRecord,
    VirulenceGeneRecord,
    MutationRecord,
    MechanismRecord,
    DrugAssociationRecord,
    PhenotypeRecord,
    ConfidenceScoreRecord,
    PathogenicitySummary,
    ReportSummary,
    dump_model,
)

logger = logging.getLogger(__name__)

_VIR_ONTOLOGY = (
    Path(__file__).resolve().parents[1]
    / "virulence_engine" / "ontology" / "virulence_ontology.json"
)
_VIR_GENE_MAP = (
    Path(__file__).resolve().parents[1]
    / "virulence_engine" / "ontology" / "gene_category_map.json"
)
_PHENOTYPE_RULES = (
    Path(__file__).resolve().parents[1]
    / "phenotype_engine" / "rules" / "rule_repository.json"
)

# genome_validator quality_class -> confidence cap key (FULL/MEDIUM/LOW are the
# keys shared by both the amr_confidence and phenotype cap tables).
_QUALITY_TO_CAP = {
    "EXCELLENT": "FULL",
    "GOOD": "FULL",
    "ACCEPTABLE": "MEDIUM",
    "POOR": "LOW",
    "LOW": "LOW",
    "FAILED": "LOW",
}


def _enum_value(value: Any) -> Any:
    """Return ``.value`` for enums, else the value unchanged."""
    return getattr(value, "value", value)


def _canon_drug_class(label: Optional[str]) -> str:
    """Normalise a possibly enum-stringified resistance-class label."""
    if not label:
        return "unknown"
    text = str(label)
    if "." in text:  # e.g. "ResistanceClass.FLUOROQUINOLONES"
        text = text.split(".")[-1]
    text = text.strip().lower().replace("_", "-")
    return _normalise_drug_class(text)


def _map_genome_quality(validation_report: Dict[str, Any]) -> str:
    quality_class = (
        validation_report.get("quality_class")
        or validation_report.get("quality_classification")
        or ""
    )
    return _QUALITY_TO_CAP.get(str(quality_class).upper(), "LOW")


# --------------------------------------------------------------------------- #
# Gene findings (from the upstream AMR-detection report)
# --------------------------------------------------------------------------- #


@dataclass
class GeneFinding:
    """Unified AMR gene finding consumed by mechanism + phenotype engines."""

    gene_name: str
    gene_family: str
    identity_pct: float
    coverage_pct: float
    confidence_score: float
    drug_class: str            # canonical (e.g. "fluoroquinolone")
    antibiotic_class: str      # display (e.g. "Fluoroquinolones")
    hit_type: str = "Strict"
    aro_accession: Optional[str] = None
    mechanism_type: Optional[str] = None
    contig_id: Optional[str] = None
    start_position: Optional[int] = None
    end_position: Optional[int] = None
    strand: Optional[str] = None
    tool_name: Optional[str] = None
    tool_names: List[str] = field(default_factory=list)
    evidence_level: int = 3
    gene_length: int = 1000


def _iter_amr_hits(amr_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    for key in ("rgi_results", "amrfinderplus_results"):
        block = amr_report.get(key) or {}
        for hit in block.get("hits", []) or []:
            hits.append(hit)
    # Some reports may carry a flat "hits" list as well.
    for hit in amr_report.get("hits", []) or []:
        hits.append(hit)
    return hits


def _genes_from_amr_report(
    amr_report: Dict[str, Any], genome_quality: str
) -> List[GeneFinding]:
    """Parse + dedupe AMR hits into GeneFinding objects with confidence."""
    merged: Dict[tuple, Dict[str, Any]] = {}

    for hit in _iter_amr_hits(amr_report):
        gene_name = hit.get("gene_name")
        if not gene_name:
            continue
        rc_raw = hit.get("resistance_class") or hit.get("antibiotic_class")
        key = (gene_name, _canon_drug_class(rc_raw))
        identity = float(hit.get("identity_percent", hit.get("identity", 0.0)) or 0.0)

        existing = merged.get(key)
        if existing is None:
            merged[key] = {"hit": hit, "rc_raw": rc_raw, "tools": set(), "best_identity": identity}
            existing = merged[key]
        if hit.get("tool_name"):
            existing["tools"].add(hit["tool_name"])
        if identity > existing["best_identity"]:
            existing["best_identity"] = identity
            existing["hit"] = hit

    findings: List[GeneFinding] = []
    for (gene_name, canon_class), data in merged.items():
        hit = data["hit"]
        tools = sorted(data["tools"]) or ([hit["tool_name"]] if hit.get("tool_name") else [])
        identity = float(hit.get("identity_percent", hit.get("identity", 0.0)) or 0.0)
        coverage = float(hit.get("coverage_percent", hit.get("coverage", 0.0)) or 0.0)
        gene_length = int(hit.get("gene_length", 1000) or 1000)

        conf = score_finding(
            target_name=gene_name,
            context="amr_gene",
            identity_pct=identity,
            coverage_pct=coverage,
            bit_score=float(hit.get("bit_score", 0.0) or 0.0),
            e_value=float(hit.get("e_value", 1e-50) or 1e-50),
            supporting_tools=tools,
            evidence_types=["computational"],
            genome_quality=genome_quality,
            reference_length=gene_length,
        )

        display_class = str(data["rc_raw"] or "").split(".")[-1] or "Unknown"
        findings.append(
            GeneFinding(
                gene_name=gene_name,
                gene_family=hit.get("gene_family") or gene_name,
                identity_pct=identity,
                coverage_pct=coverage,
                confidence_score=conf["overall_score"],
                drug_class=canon_class,
                antibiotic_class=display_class,
                hit_type=hit.get("hit_type", "Strict"),
                aro_accession=hit.get("aro_accession"),
                mechanism_type=hit.get("resistance_mechanism") or hit.get("mechanism"),
                contig_id=hit.get("contig_id"),
                start_position=hit.get("start_position"),
                end_position=hit.get("end_position"),
                strand=hit.get("strand"),
                tool_name=tools[0] if tools else None,
                tool_names=tools,
                evidence_level=int(hit.get("evidence_level", 3) or 3),
                gene_length=gene_length,
            )
        )
    return findings


# --------------------------------------------------------------------------- #
# Virulence
# --------------------------------------------------------------------------- #


def _run_virulence(
    sample_id: str, assembly_path: str, genome_quality: str
):
    """Return (virulence_records, pathogenicity_summary, confidence_records)."""
    records: List[VirulenceGeneRecord] = []
    confidence_records: List[ConfidenceScoreRecord] = []

    if not (_VIR_ONTOLOGY.exists() and _VIR_GENE_MAP.exists()):
        logger.warning("Virulence ontology/gene-map missing; skipping virulence.")
        return records, PathogenicitySummary(), confidence_records

    classifier = VirulenceClassifier(_VIR_ONTOLOGY, _VIR_GENE_MAP)
    adapter = VFDBAdapter(db_version_id="VFDB_2024")
    hits = adapter.run(Path(assembly_path))

    factors: List[VirulenceFactor] = []
    for idx, hit in enumerate(hits):
        cat = classifier.classify(hit)
        conf = score_finding(
            target_name=hit.gene_name,
            context="virulence",
            identity_pct=hit.identity_pct,
            coverage_pct=hit.coverage_pct,
            bit_score=hit.bit_score,
            e_value=hit.e_value,
            supporting_tools=[hit.tool],
            evidence_types=["computational"],
            genome_quality=genome_quality,
        )
        factors.append(
            VirulenceFactor(
                vf_id=f"vf_{sample_id}_{idx}",
                sample_id=sample_id,
                gene_name=hit.gene_name,
                category_code=cat["category_code"],
                category_display=cat["category_display"],
                function_description=hit.vf_function,
                detection_tool=hit.tool,
                db_version_id=hit.db_version_id,
                identity_pct=hit.identity_pct,
                coverage_pct=hit.coverage_pct,
                bit_score=hit.bit_score,
                e_value=hit.e_value,
                contig_id=hit.contig_id,
                start=hit.start,
                end=hit.end,
                strand=hit.strand,
                is_high_risk=cat["is_high_risk"],
                risk_weight=cat["risk_weight"],
                confidence=conf,
            )
        )
        records.append(
            VirulenceGeneRecord(
                gene_name=hit.gene_name,
                virulence_factor=hit.vf_function,
                virulence_category=cat["category_display"],
                mechanism=cat["category_code"],
                identity_percent=hit.identity_pct,
                coverage_percent=hit.coverage_pct,
                contig_id=hit.contig_id,
                start_position=hit.start,
                end_position=hit.end,
                is_high_risk=cat["is_high_risk"],
                risk_weight=cat["risk_weight"],
                database_source=hit.tool,
                confidence_score=conf["overall_score"],
            )
        )
        confidence_records.append(ConfidenceScoreRecord(**conf))

    profile = compute_pathogenicity_profile(sample_id, factors)
    summary = PathogenicitySummary(
        total_vf_genes=profile.total_vf_genes,
        category_diversity=profile.category_diversity,
        high_risk_count=profile.high_risk_count,
        high_risk_genes=profile.high_risk_genes,
        categories_detected=profile.categories_detected,
        category_summary=profile.category_summary,
        risk_score=profile.risk_score,
        risk_class=profile.risk_class,
    )
    return records, summary, confidence_records


# --------------------------------------------------------------------------- #
# Phenotype
# --------------------------------------------------------------------------- #


def _run_phenotype(
    sample_id: str,
    genome_quality: str,
    genes: List[GeneFinding],
    mutation_determinants: List[Any],
    mechanisms: List[Any],
    species: Optional[str],
) -> List[PhenotypeRecord]:
    if not _PHENOTYPE_RULES.exists():
        logger.warning("Phenotype rule repository missing; skipping phenotype.")
        return []

    repo = RuleRepository(_PHENOTYPE_RULES)
    engine = PhenotypeInferenceEngine(
        rule_repo=repo,
        breakpoint_adapter=EUCASTAdapter(),
        confidence_propagator=ConfidencePropagator(),
    )

    gene_inputs = [
        AMRGeneResult(
            gene_name=g.gene_name,
            gene_family=g.gene_family,
            aro_accession=g.aro_accession,
            hit_type=g.hit_type,
            identity_pct=g.identity_pct,
            coverage_pct=g.coverage_pct,
            confidence_score=g.confidence_score,
            mechanism_type=g.mechanism_type,
        )
        for g in genes
    ]

    predictions = engine.predict(
        sample_id=sample_id,
        assembly_quality=genome_quality,
        genes=gene_inputs,
        mutations=mutation_determinants,
        mechanisms=mechanisms,
        species=species,
        breakpoint_source="EUCAST",
    )

    return [
        PhenotypeRecord(
            drug=p.drug,
            drug_class=p.drug_class,
            predicted_sir=p.predicted_sir,
            confidence_score=p.confidence_score,
            confidence_tier=p.confidence_tier,
            breakpoint_source=p.breakpoint_source,
            breakpoint_version=p.breakpoint_version,
            is_not_testable=p.is_not_testable,
            has_conflict=p.has_conflict,
            supporting_genes=p.supporting_genes,
            supporting_mutations=p.supporting_mutations,
            explanation=p.explanation,
        )
        for p in predictions
    ]


# --------------------------------------------------------------------------- #
# Main orchestration
# --------------------------------------------------------------------------- #


def run_isolate_analysis(
    sample_id: str,
    assembly_path: str,
    species: Optional[str],
    validation_report: Dict[str, Any],
    amr_report: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
    job_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Run all post-AMR engines for one isolate and return the report dict."""
    config = config or {}
    job_id = job_id or sample_id
    genome_quality = _map_genome_quality(validation_report)
    errors: List[str] = []
    confidence_records: List[ConfidenceScoreRecord] = []

    # 1. AMR genes (from upstream report)
    genes = _genes_from_amr_report(amr_report, genome_quality)
    amr_records: List[AmrGeneRecord] = []
    for g in genes:
        amr_records.append(
            AmrGeneRecord(
                gene_name=g.gene_name,
                gene_family=g.gene_family,
                antibiotic_class=g.antibiotic_class,
                drug_class=g.drug_class,
                resistance_mechanism=g.mechanism_type,
                identity_percent=g.identity_pct,
                coverage_percent=g.coverage_pct,
                contig_id=g.contig_id,
                start_position=g.start_position,
                end_position=g.end_position,
                strand=g.strand,
                tool_name=g.tool_name,
                evidence_level=g.evidence_level,
                confidence_score=g.confidence_score,
            )
        )
        confidence_records.append(
            ConfidenceScoreRecord(
                **score_finding(
                    target_name=g.gene_name,
                    context="amr_gene",
                    identity_pct=g.identity_pct,
                    coverage_pct=g.coverage_pct,
                    supporting_tools=g.tool_names,
                    evidence_types=["computational"],
                    genome_quality=genome_quality,
                    reference_length=g.gene_length,
                )
            )
        )

    # 2. Mutations
    mutation_records: List[MutationRecord] = []
    mut_result = None
    try:
        mut_engine = MutationDetectionEngine(
            job_id,
            {
                "sample_id": sample_id,
                "reference_fasta": config.get("reference_fasta"),
                "min_identity": config.get("min_identity", 85.0),
                "min_coverage": config.get("min_coverage", 80.0),
            },
        )
        mut_result = mut_engine.run(assembly_path, species or "Unknown")
    except Exception as exc:  # noqa: BLE001 - engine failure should not abort report
        logger.exception("Mutation detection failed: %s", exc)
        errors.append(f"mutation_detection: {exc}")

    if mut_result is not None:
        for av, mapping, conf in zip(
            mut_result.mutations, mut_result.mappings, mut_result.confidences
        ):
            classification = _enum_value(mapping.classification)
            if classification == "SILENT":
                continue
            raw = av.raw_variant
            kb = mapping.kb_entry or {}
            metrics = mut_result.gene_metrics.get(raw.gene_name, {})
            mutation_records.append(
                MutationRecord(
                    gene_name=raw.gene_name,
                    mutation=av.mutation_notation,
                    protein_position=raw.protein_position,
                    ref_amino_acid=raw.ref_amino_acid,
                    alt_amino_acid=raw.alt_amino_acid,
                    effect=_enum_value(av.effect),
                    mechanism=kb.get("mechanism"),
                    classification=classification,
                    drug_class=_canon_drug_class(kb.get("drug_class")),
                    drugs_affected=list(kb.get("drugs_affected", [])),
                    sir_prediction=kb.get("sir_prediction"),
                    identity_percent=metrics.get("identity_pct"),
                    coverage_percent=metrics.get("coverage_pct"),
                    contig_id=av.contig_id or metrics.get("contig_id"),
                    hgvs_protein=av.hgvs_protein,
                    hgvs_cdna=av.hgvs_cdna,
                    domain=av.domain,
                    confidence_score=conf.final_score,
                    confidence_tier=_enum_value(conf.confidence_tier),
                )
            )
            evidence = ["clinical"] if classification == "KNOWN_RESISTANCE" else (
                ["computational"] if classification == "LIKELY_RESISTANCE" else ["inferred"]
            )
            confidence_records.append(
                ConfidenceScoreRecord(
                    **score_finding(
                        target_name=av.mutation_notation or raw.gene_name,
                        context="mutation",
                        identity_pct=metrics.get("identity_pct", 0.0) or 0.0,
                        coverage_pct=metrics.get("coverage_pct", 0.0) or 0.0,
                        supporting_tools=["knowledgebase"],
                        evidence_types=evidence,
                        genome_quality=genome_quality,
                    )
                )
            )

    # 3. Mechanism classification (genes + mutations)
    mechanism_records: List[MechanismRecord] = []
    drug_assoc_records: List[DrugAssociationRecord] = []
    mechanisms: List[Any] = []
    mutation_determinants: List[Any] = []
    try:
        mech_engine = MechanismClassificationEngine(job_id, config)
        mech_out = mech_engine.run(
            genes,
            mut_result.mutations if mut_result else [],
            mut_result.mappings if mut_result else [],
        )
        mechanisms = mech_out["mechanisms"]
        mutation_determinants = [
            d for d in mech_out["determinants"] if d.determinant_type == "mutation"
        ]
        for m in mechanisms:
            mechanism_records.append(
                MechanismRecord(
                    mechanism_code=m.mechanism_code,
                    mechanism_name=m.mechanism_name,
                    drug_classes=m.drug_classes,
                    supporting_genes=m.supporting_genes,
                    supporting_mutations=m.supporting_mutations,
                    evidence_sources=m.evidence_sources,
                    confidence=m.confidence,
                    confidence_tier=_enum_value(m.confidence_tier),
                )
            )
        for a in mech_out["drug_associations"]:
            drug_assoc_records.append(
                DrugAssociationRecord(
                    drug_name=a.drug_name,
                    drug_class=a.drug_class,
                    sir_prediction=_enum_value(a.sir_prediction),
                    evidence_type=a.evidence_type,
                    evidence_name=a.evidence_name,
                    evidence_level=a.evidence_level,
                    confidence=a.confidence,
                    cross_resistance=a.cross_resistance,
                )
            )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Mechanism classification failed: %s", exc)
        errors.append(f"mechanism_classification: {exc}")

    # 4. Virulence
    try:
        virulence_records, pathogenicity, vir_conf = _run_virulence(
            sample_id, assembly_path, genome_quality
        )
        confidence_records.extend(vir_conf)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Virulence profiling failed: %s", exc)
        errors.append(f"virulence: {exc}")
        virulence_records, pathogenicity = [], PathogenicitySummary()

    # 5. Phenotype
    try:
        phenotype_records = _run_phenotype(
            sample_id, genome_quality, genes, mutation_determinants, mechanisms, species
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Phenotype inference failed: %s", exc)
        errors.append(f"phenotype: {exc}")
        phenotype_records = []

    for p in phenotype_records:
        confidence_records.append(
            ConfidenceScoreRecord(
                context="phenotype",
                target_name=p.drug,
                overall_score=p.confidence_score or 0.0,
                tier=p.confidence_tier or "LOW",
                cap_applied=False,
                components={"propagated": p.confidence_score or 0.0},
                weighted={},
            )
        )

    # 6. Summary
    resistance_classes = sorted(
        {r.drug_class for r in amr_records if r.drug_class}
        | {m.drug_class for m in mutation_records if m.drug_class}
    )
    summary = ReportSummary(
        total_amr_genes=len(amr_records),
        total_virulence_genes=len(virulence_records),
        total_mutations=len(mutation_records),
        total_novel_mutations=(mut_result.total_novel if mut_result else 0),
        total_mechanisms=len(mechanism_records),
        total_resistant_phenotypes=sum(
            1 for p in phenotype_records if p.predicted_sir == "R"
        ),
        resistance_classes=resistance_classes,
    )

    report = IsolateReport(
        sample_id=str(sample_id),
        species=species,
        generated_at=datetime.now(timezone.utc).isoformat(),
        genome_quality=genome_quality,
        validation_status=validation_report.get("validation_status"),
        amr_genes=amr_records,
        virulence_genes=virulence_records,
        mutations=mutation_records,
        mechanisms=mechanism_records,
        drug_associations=drug_assoc_records,
        phenotypes=phenotype_records,
        confidence_scores=confidence_records,
        pathogenicity=pathogenicity,
        summary=summary,
        errors=errors,
    )
    return dump_model(report)


def _load_json(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint used by the Nextflow bio-analysis process."""
    parser = argparse.ArgumentParser(description="Run per-isolate AMR analysis")
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--assembly", required=True)
    parser.add_argument("--species", default="Unknown")
    parser.add_argument("--validation", help="genome validation report JSON")
    parser.add_argument("--amr", help="AMR detection report JSON")
    parser.add_argument("--reference-fasta", default=None)
    parser.add_argument("--job-id", default=None)
    parser.add_argument("--output", default="amr_detection_report.json")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO)

    report = run_isolate_analysis(
        sample_id=args.sample_id,
        assembly_path=args.assembly,
        species=args.species,
        validation_report=_load_json(args.validation),
        amr_report=_load_json(args.amr),
        config={"reference_fasta": args.reference_fasta},
        job_id=args.job_id,
    )

    Path(args.output).write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    s = report["summary"]
    print(
        f"[{args.sample_id}] amr_genes={s['total_amr_genes']} "
        f"mutations={s['total_mutations']} mechanisms={s['total_mechanisms']} "
        f"phenotypes(R)={s['total_resistant_phenotypes']} -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Mechanism Classification Engine main entrypoint."""

import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from .mechanism_classifier import MechanismClassifier
from .mechanism_evidence import aggregate_mechanisms
from .drug_association import associate_drugs
from .mutation_prioritizer import rank_mutations
from .knowledgebase import KnowledgebaseLoader
from .result_models import (
    ResistanceDeterminant,
    SIRPrediction,
    MutationClassification,
)

DEFAULT_ONTOLOGY = Path(__file__).parent / "ontology" / "mechanism_ontology.json"

# Normalise heterogeneous drug-class labels (e.g. AMR tool "Fluoroquinolones")
# onto the canonical keys used by the cross-resistance tables.
_DRUG_CLASS_ALIAS = {
    "fluoroquinolones": "fluoroquinolone",
    "beta-lactams": "beta-lactam",
    "betalactam": "beta-lactam",
    "carbapenems": "carbapenem",
    "cephalosporins": "cephalosporin",
    "aminoglycosides": "aminoglycoside",
    "glycopeptides": "glycopeptide",
    "macrolides": "macrolide",
    "tetracyclines": "tetracycline",
    "polymyxins": "polymyxin",
    "rifamycins": "rifamycin",
    "phenicols": "phenicol",
}


def _normalise_drug_class(label: Optional[str]) -> str:
    if not label:
        return "unknown"
    key = str(label).strip().lower()
    return _DRUG_CLASS_ALIAS.get(key, key)


def _safe_sir(value: Optional[str]) -> SIRPrediction:
    if not value:
        return SIRPrediction.UNKNOWN
    try:
        return SIRPrediction(str(value).upper())
    except ValueError:
        return SIRPrediction.UNKNOWN


class MechanismClassificationEngine:
    """Main orchestrator for mechanism classification.

    Produces three linked views over the resistome of a single isolate:
      * ``mechanisms``        - unique resistance mechanisms with evidence
      * ``determinants``      - per gene/mutation resistance elements (ranked)
      * ``drug_associations`` - drug-level predictions with cross-resistance
    """

    def __init__(
        self,
        job_id: str,
        config: Dict[str, Any],
        ontology_path: Optional[Path] = None,
        aro_mapper: Any = None,
        kb: Optional[List[Dict]] = None,
    ):
        self.job_id = job_id
        self.config = config or {}
        ontology_path = Path(ontology_path) if ontology_path else DEFAULT_ONTOLOGY
        if kb is None:
            kb = KnowledgebaseLoader().get_entries()
        self.kb = kb
        self.classifier = MechanismClassifier(ontology_path, aro_mapper, kb)

    def _determinant_from_gene(self, gene: Any) -> ResistanceDeterminant:
        mech = self.classifier.classify_gene(gene)
        drug_class = _normalise_drug_class(
            getattr(gene, "drug_class", None)
            or getattr(gene, "resistance_class", None)
        )
        return ResistanceDeterminant(
            determinant_id=uuid.uuid4(),
            determinant_type="gene",
            gene_name=getattr(gene, "gene_name", "unknown"),
            mechanism_code=mech["code"],
            mechanism_name=mech["name"],
            drug_class=drug_class,
            aro_accession=getattr(gene, "aro_accession", None),
            sir_prediction=SIRPrediction.RESISTANT,
            evidence_level=int(getattr(gene, "evidence_level", 3) or 3),
            confidence_score=float(mech.get("confidence", 0.5)),
            contig_id=getattr(gene, "contig_id", None),
            start=getattr(gene, "start", None) or getattr(gene, "start_position", None),
            end=getattr(gene, "end", None) or getattr(gene, "end_position", None),
            strand=getattr(gene, "strand", None),
        )

    def _determinant_from_mutation(self, mutation: Any, mapping: Any) -> ResistanceDeterminant:
        mech = self.classifier.classify_mutation(mutation, mapping)
        kb_entry = getattr(mapping, "kb_entry", None) or {}
        raw = getattr(mutation, "raw_variant", None)
        return ResistanceDeterminant(
            determinant_id=uuid.uuid4(),
            determinant_type="mutation",
            gene_name=getattr(raw, "gene_name", "unknown"),
            mechanism_code=mech["code"],
            mechanism_name=mech["name"],
            drug_class=_normalise_drug_class(kb_entry.get("drug_class")),
            mutation_notation=getattr(mutation, "mutation_notation", None),
            drugs_affected=list(kb_entry.get("drugs_affected", [])),
            sir_prediction=_safe_sir(kb_entry.get("sir_prediction")),
            evidence_level=int(kb_entry.get("evidence_level", 5)),
            classification=getattr(
                mapping, "classification", MutationClassification.UNKNOWN
            ),
            confidence_score=float(
                kb_entry.get("confidence", getattr(mapping, "confidence", 0.5))
            ),
            contig_id=getattr(mutation, "contig_id", None),
            start=getattr(mutation, "start_pos", None),
        )

    def run(
        self,
        genes: List[Any],
        mutations: List[Any],
        mappings: List[Any],
        progress_cb=None,
    ) -> Dict[str, Any]:
        """Run the mechanism classification pipeline for one isolate."""
        if progress_cb:
            progress_cb(10, "CLASSIFYING_GENES_AND_MUTATIONS")

        mechanisms = aggregate_mechanisms(genes, mutations, mappings, self.classifier)

        if progress_cb:
            progress_cb(40, "BUILDING_DETERMINANTS")
        determinants: List[ResistanceDeterminant] = []
        determinants.extend(self._determinant_from_gene(g) for g in genes)
        determinants.extend(
            self._determinant_from_mutation(m, mp)
            for m, mp in zip(mutations, mappings)
        )

        if progress_cb:
            progress_cb(70, "ASSOCIATING_DRUGS")
        drug_associations = associate_drugs(determinants)

        if progress_cb:
            progress_cb(90, "PRIORITIZING")
        determinants = rank_mutations(determinants)

        if progress_cb:
            progress_cb(100, "COMPLETED")
        return {
            "mechanisms": mechanisms,
            "determinants": determinants,
            "drug_associations": drug_associations,
        }

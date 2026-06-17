"""Mutation Detection Engine main entrypoint."""

import uuid
from typing import Dict, Any

from .gene_localization import localise_genes
from .variant_detection import call_variants, detect_stop_codons
from .variant_annotation import annotate_variant
from .mutation_mapper import map_mutation
from .mutation_confidence import compute_mutation_confidence
from .reference_loader import get_reference_sequences
from .knowledgebase import KnowledgebaseLoader
from .result_models import MutationDetectionResult, MutationClassification

# Mapping classifications considered "novel / requires review".
_NOVEL_CLASSES = {
    MutationClassification.NOVEL,
    MutationClassification.NOVEL_IN_DOMAIN,
    MutationClassification.LIKELY_RESISTANCE,
}


def _as_uuid(value: Any) -> uuid.UUID:
    """Coerce a value to a UUID, generating one when not parseable."""
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return uuid.uuid4()


class MutationDetectionEngine:
    """Main orchestrator for mutation detection."""

    def __init__(self, job_id: str, config: Dict[str, Any]):
        self.job_id = job_id
        self.config = config or {}
        self.kb_loader = KnowledgebaseLoader()

    def run(self, fasta_path: str, species: str, progress_cb=None) -> MutationDetectionResult:
        """Run the mutation detection pipeline against an assembly FASTA."""
        if progress_cb:
            progress_cb(5, "LOADING_REFERENCES")

        kb_entries = self.kb_loader.get_entries()
        references = get_reference_sequences(
            self.config.get("reference_fasta"), kb_entries, species=species
        )

        if progress_cb:
            progress_cb(15, "GENE_LOCALIZATION")
        locations = localise_genes(
            fasta_path,
            references,
            min_identity=float(self.config.get("min_identity", 85.0)),
            min_coverage=float(self.config.get("min_coverage", 80.0)),
        )

        mutations = []
        mappings = []
        confidences = []
        gene_metrics: Dict[str, dict] = {}

        if progress_cb:
            progress_cb(40, "VARIANT_CALLING")

        for loc in locations:
            gene_metrics[loc.gene_name] = {
                "identity_pct": round(loc.identity_pct, 2),
                "coverage_pct": round(loc.coverage_pct, 2),
                "contig_id": loc.contig_id,
                "start": loc.start,
                "end": loc.end,
                "strand": loc.strand,
            }

            ref_seq = references.get(loc.gene_name, "")
            query_seq = loc.extracted_seq
            length = min(len(query_seq), len(ref_seq))

            raw_variants = call_variants(
                query_seq[:length], ref_seq[:length], loc.gene_name
            )
            raw_variants.extend(detect_stop_codons(loc.extracted_seq, loc.gene_name))

            for variant in raw_variants:
                annotated = annotate_variant(
                    variant, contig_id=loc.contig_id, start_pos=loc.start
                )
                mapping = map_mutation(annotated, kb_entries)
                confidence = compute_mutation_confidence(annotated, mapping, loc)

                mutations.append(annotated)
                mappings.append(mapping)
                confidences.append(confidence)

        if progress_cb:
            progress_cb(85, "NOVEL_DETECTION")
        novel_mutations = [
            av
            for av, mapping in zip(mutations, mappings)
            if mapping.classification in _NOVEL_CLASSES
        ]

        confidence_scores = {
            av.mutation_notation: conf.final_score
            for av, conf in zip(mutations, confidences)
            if av.mutation_notation
        }

        if progress_cb:
            progress_cb(100, "COMPLETED")

        return MutationDetectionResult(
            job_id=self.job_id,
            sample_id=_as_uuid(self.config.get("sample_id")),
            assembly_id=_as_uuid(self.config.get("assembly_id")),
            mutations=mutations,
            novel_mutations=novel_mutations,
            mappings=mappings,
            confidences=confidences,
            gene_metrics=gene_metrics,
            confidence_scores=confidence_scores,
            total_mutations=len(mutations),
            total_novel=len(novel_mutations),
        )

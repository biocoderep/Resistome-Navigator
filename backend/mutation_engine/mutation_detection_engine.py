"""Mutation Detection Engine main entrypoint."""

import uuid
from pathlib import Path
from typing import Dict, Any, List

from .gene_localization import localise_genes
from .variant_detection import call_variants, detect_stop_codons
from .variant_annotation import annotate_variant
from .mutation_mapper import map_mutation
from .mutation_confidence import compute_mutation_confidence
from .novel_mutation_detector import extract_novel_mutations
from .knowledgebase import KnowledgebaseLoader
from .result_models import MutationDetectionResult, AnnotatedVariant

class MutationDetectionEngine:
    """Main orchestrator for mutation detection."""
    
    def __init__(self, job_id: str, config: Dict[str, Any]):
        self.job_id = job_id
        self.config = config
        self.kb_loader = KnowledgebaseLoader()
        
    def run(self, fasta_path: str, species: str, progress_cb=None) -> MutationDetectionResult:
        """Run the mutation detection pipeline."""
        if progress_cb: progress_cb(5, "LOADING_GENOME")
        
        # Stub: normally we load references here
        references = {"gyrA": "ATGCGTACGTTAGC", "rpoB": "ATGGCTC"}
        
        if progress_cb: progress_cb(10, "GENE_LOCALIZATION")
        locations = localise_genes(fasta_path, references)
        
        if progress_cb: progress_cb(30, "VARIANT_CALLING")
        raw_variants = []
        for loc in locations:
            # Stub alignments for variant calling
            q_aln, r_aln = loc.extracted_seq, references.get(loc.gene_name, "")
            # Ensure equal lengths for stub alignment logic
            length = min(len(q_aln), len(r_aln))
            q_aln, r_aln = q_aln[:length], r_aln[:length]
            
            variants = call_variants(q_aln, r_aln, loc.gene_name)
            stops = detect_stop_codons(loc.extracted_seq, loc.gene_name)
            raw_variants.extend(variants)
            raw_variants.extend(stops)
            
        if progress_cb: progress_cb(55, "VARIANT_ANNOTATION")
        annotated_variants = [annotate_variant(v) for v in raw_variants]
        
        if progress_cb: progress_cb(65, "KB_MAPPING")
        mappings = [map_mutation(v, self.kb_loader.get_entries()) for v in annotated_variants]
        
        if progress_cb: progress_cb(82, "NOVEL_DETECTION")
        sample_id = self.config.get("sample_id", str(uuid.uuid4()))
        novel_report = extract_novel_mutations(annotated_variants, mappings, sample_id)
        
        if progress_cb: progress_cb(87, "CONFIDENCE_SCORING")
        confidences = []
        for v, mapping in zip(annotated_variants, mappings):
            loc = next((l for l in locations if l.gene_name == v.raw_variant.gene_name), None)
            if loc:
                conf = compute_mutation_confidence(v, mapping, loc)
                confidences.append(conf)
                
        if progress_cb: progress_cb(100, "REPORT_GENERATION")
        
        # Build result
        result = MutationDetectionResult(
            job_id=self.job_id,
            sample_id=uuid.UUID(sample_id) if isinstance(sample_id, str) else sample_id,
            assembly_id=uuid.uuid4(),
            mutations=annotated_variants,
            total_mutations=len(annotated_variants),
            total_novel=novel_report["total_novel"]
        )
        return result

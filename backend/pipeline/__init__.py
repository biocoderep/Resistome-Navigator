"""Per-isolate pipeline orchestration.

Runs the post-AMR-detection biological engines (mutation, virulence, mechanism,
phenotype, confidence) for a single isolate and assembles the canonical
``amr_detection_report.json`` consumed by the Celery ingestion layer and the
Nextflow report assembler.
"""

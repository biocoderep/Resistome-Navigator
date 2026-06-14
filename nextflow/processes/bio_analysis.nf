/*
=============================================================================
    BIOLOGICAL CHARACTERISATION PROCESS
=============================================================================
    Runs the post-AMR-detection engines for a single isolate:
      - Mutation detection      (resistance SNPs / indels / truncations)
      - Mechanism classification (resistance mechanisms + drug associations)
      - Virulence profiling      (virulence factors + pathogenicity score)
      - Phenotype prediction     (rule-based S/I/R)
      - Confidence scoring       (per-finding aggregated confidence)

    Emits the canonical ``isolate_report.json`` consumed by the Celery
    ingestion layer and the cohort/reporting stages. This process runs once per
    sample on the per-sample channel, so a single isolate and a 50-isolate
    cohort use the identical code path.
=============================================================================
*/

process bio_analysis {
    tag "${sample_id}"

    label 'aggregation'

    cpus 2
    memory "4 GB"
    time "2h"

    publishDir "${params.output}/${sample_id}/reports", mode: "copy"

    input:
        tuple val(sample_id), path(assembly_file), val(species), path(validation_report), path(amr_report)

    output:
        tuple val(sample_id), path("isolate_report.json")

    script:
        // Prepend the repo root (parent of the Nextflow project dir) so that
        // `backend.*` is importable regardless of the container PYTHONPATH.
        """
        export PYTHONPATH="${projectDir}/..:\${PYTHONPATH}"
        python -m backend.pipeline.isolate_pipeline \\
            --sample-id "${sample_id}" \\
            --assembly "${assembly_file}" \\
            --species "${species}" \\
            --validation "${validation_report}" \\
            --amr "${amr_report}" \\
            --output "isolate_report.json"
        """
}

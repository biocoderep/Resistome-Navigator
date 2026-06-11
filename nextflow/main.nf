#!/usr/bin/env nextflow

/*
=============================================================================
    AMR DETECTION PIPELINE - NEXTFLOW DSL2
=============================================================================
    Module 1: Genome Validation + Analysis
    
    This workflow orchestrates the complete AMR detection pipeline:
    - Genome Validation Engine (MVP)
    - Sequence Alignment Service
    - AMR Detection Analysis (CARD RGI, AMRFinderPlus)
    - Result Aggregation and Confidence Scoring
    
    Usage:
        nextflow run main.nf \
            --samples samples.csv \
            --output results/ \
            -profile docker
=============================================================================
*/

nextflow.enable.dsl = 2

// =============================================================================
// PARAMETERS
// =============================================================================

// Input
params.samples = null                          // CSV with columns: sample_id,assembly_file,species
params.output = "results"

// Genome Validation Config
params.min_assembly_length_bp = 200_000
params.max_contig_count = 2000
params.n_warn_threshold = 1.0
params.n_fail_threshold = 5.0

// Alignment Config
params.alignment_method = "bowtie2"            // bowtie2, bwa, minimap2
params.alignment_threads = 4
params.alignment_min_identity = 95.0
params.alignment_min_coverage = 80.0

// AMR Detection Config
params.amr_tools = "card_rgi,amrfinderplus"
params.amr_min_identity = 95.0
params.amr_min_coverage = 80.0

// Reference Databases
params.reference_db_dir = "${projectDir}/databases"
params.card_database = "${params.reference_db_dir}/card"
params.amrfinder_database = "${params.reference_db_dir}/amrfinderplus"

// Resource Limits
params.validation_cpus = 4
params.validation_memory = "8 GB"
params.alignment_cpus = 8
params.alignment_memory = "16 GB"
params.amr_cpus = 8
params.amr_memory = "16 GB"    
    // Output Formats
    params.output_formats = "json,tsv,pdf"
    params.publish_dir = "${params.output}"
    
    // Help message
    params.help = false

// =============================================================================
// HELP MESSAGE
// =============================================================================

if (params.help) {
    log.info """
    ╔════════════════════════════════════════════════════════════════════════╗
    ║              AMR DETECTION PIPELINE - NEXTFLOW DSL2                    ║
    ║                          Module 1 MVP                                  ║
    ╚════════════════════════════════════════════════════════════════════════╝
    
    USAGE:
        nextflow run main.nf --samples samples.csv --output results/ -profile docker
    
    MANDATORY ARGUMENTS:
        --samples       CSV file with columns: sample_id,assembly_file,species
        --output        Output directory for results (default: results)
    
    OPTIONAL ARGUMENTS:
        --alignment_method      bowtie2, bwa, or minimap2 (default: bowtie2)
        --amr_tools             comma-separated: card_rgi,amrfinderplus (default: both)
        --reference_db_dir      Path to reference databases (default: ./databases)
        --help                  Show this help message
    
    PROFILES:
        docker          Run with Docker containers
        singularity     Run with Singularity containers
        local           Run locally (requires tools installed)
    
    EXAMPLES:
        # Run full pipeline with Docker
        nextflow run main.nf \\
            --samples samples.csv \\
            --output results/ \\
            -profile docker
        
        # Run with specific tools
        nextflow run main.nf \\
            --samples samples.csv \\
            --amr_tools "card_rgi" \\
            -profile docker
        
        # Run with custom resources
        nextflow run main.nf \\
            --samples samples.csv \\
            --alignment_cpus 16 \\
            --alignment_memory "32 GB" \\
            -profile docker
    
    REFERENCE:
        Documentation: docs/specifications/
        Database setup: docs/DATABASE_SETUP.md
    """.stripIndent()
    exit 0
}

// =============================================================================
// VALIDATE INPUTS
// =============================================================================

if (!params.samples) {
    log.error "ERROR: --samples parameter is required"
    exit 1
}

if (!file(params.samples).exists()) {
    log.error "ERROR: Samples file not found: ${params.samples}"
    exit 1
}

log.info """
╔════════════════════════════════════════════════════════════════════════╗
║              AMR DETECTION PIPELINE - NEXTFLOW DSL2                    ║
║                          Module 1 MVP                                  ║
╚════════════════════════════════════════════════════════════════════════╝

PARAMETERS:
  Samples:                    ${params.samples}
  Output Directory:           ${params.output}
  Alignment Method:           ${params.alignment_method}
  AMR Tools:                  ${params.amr_tools}
  Reference DB Directory:     ${params.reference_db_dir}

RESOURCES:
  Validation Cpus:            ${params.validation_cpus}
  Validation Memory:          ${params.validation_memory}
  Alignment Cpus:             ${params.alignment_cpus}
  Alignment Memory:           ${params.alignment_memory}
  AMR Detection Cpus:         ${params.amr_cpus}
  AMR Detection Memory:       ${params.amr_memory}

""".stripIndent()

// =============================================================================
// INCLUDE PROCESS DEFINITIONS
// =============================================================================

include { genome_validation } from "./processes/genome_validation.nf"
include { sequence_alignment } from "./processes/alignment.nf"
include { amr_detection } from "./processes/amr_detection.nf"
include { aggregate_results } from "./processes/aggregation.nf"
include { generate_report } from "./processes/reporting.nf"

// =============================================================================
// WORKFLOW
// =============================================================================

workflow {
    // Parse sample CSV
    samples_ch = Channel
        .fromPath(params.samples)
        .splitCsv(header: true)
        .map { row -> 
            tuple(
                row.sample_id,
                file(row.assembly_file),
                row.species
            )
        }
    
    // Step 1: Genome Validation Engine (MVP)
    log.info "Step 1/5: Running Genome Validation Engine"
    validation_results = genome_validation(samples_ch)
    
    // Step 2: Sequence Alignment
    log.info "Step 2/5: Running Sequence Alignment"
    alignment_results = sequence_alignment(
        validation_results,
        file(params.card_database)
    )
    
    // Step 3: AMR Detection
    log.info "Step 3/5: Running AMR Detection"
    amr_results = amr_detection(
        validation_results,
        file(params.card_database),
        file(params.amrfinder_database)
    )
    
    // Step 4: Aggregate Results
    log.info "Step 4/5: Aggregating Results"
    aggregated = aggregate_results(
        amr_results.combine(alignment_results, by: 0)
    )
    
    // Step 5: Generate Report
    log.info "Step 5/5: Generating Report"
    reports = generate_report(aggregated)
    
    // Publish outputs
    reports.publishDir(
        path: params.publish_dir,
        mode: "copy",
        pattern: "*"
    )
}

// =============================================================================
// WORKFLOW COMPLETION
// =============================================================================

workflow.onComplete {
    log.info """
    ╔════════════════════════════════════════════════════════════════════════╗
    ║                    PIPELINE EXECUTION COMPLETED                        ║
    ╚════════════════════════════════════════════════════════════════════════╝
    
    Status:         ${workflow.success ? "✓ SUCCESS" : "✗ FAILED"}
    Exit Code:      ${workflow.exitStatus}
    Duration:       ${workflow.duration}
    Output Dir:     ${params.publish_dir}
    
    ${workflow.success ? "Pipeline completed successfully!" : "Pipeline failed. Check logs for details."}
    """.stripIndent()
}

workflow.onError {
    log.error """
    ╔════════════════════════════════════════════════════════════════════════╗
    ║                       PIPELINE ERROR                                   ║
    ╚════════════════════════════════════════════════════════════════════════╝
    
    Error Message:  ${workflow.errorMessage}
    Exit Code:      ${workflow.exitStatus}
    
    For troubleshooting, check:
    1. Log file: ${workflow.workDir}/.nextflow.log
    2. Work directory: ${workflow.workDir}
    """.stripIndent()
}

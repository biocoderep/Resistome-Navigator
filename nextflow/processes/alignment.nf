/*
=============================================================================
    SEQUENCE ALIGNMENT PROCESS
=============================================================================
*/

process sequence_alignment {
    tag "${sample_id}"
    
    label 'alignment'
    
    cpus params.alignment_cpus
    memory params.alignment_memory
    time "4h"
    
    publishDir "${params.output}/${sample_id}/alignment", mode: "copy"
    
    input:
        tuple val(sample_id), path(assembly_file), val(species), path(validation_report)
        path reference_db
    
    output:
        tuple val(sample_id), path("alignment_report.json"), path("alignment.bam")
    
    script:
        """
        python << 'EOF'
        import json
        from pathlib import Path
        from backend.alignment import Bowtie2Aligner, AlignmentConfig
        
        # Check if validation passed
        with open("${validation_report}") as f:
            validation = json.load(f)
        
        if validation.get("validation_status") != "PASS":
            print(f"Warning: Validation status is {validation['validation_status']}")
        
        # Configure alignment
        config = AlignmentConfig(
            method="bowtie2",
            threads=${params.alignment_cpus},
            min_match_identity=${params.alignment_min_identity},
            max_mismatch_percent=5.0
        )
        
        # Run alignment
        aligner = Bowtie2Aligner(config=config)
        result = aligner.align(
            query_file=Path("${assembly_file}"),
            reference_db=Path("${reference_db}"),
            output_file=Path("alignment.bam"),
            sample_id="${sample_id}"
        )
        
        # Save report
        with open("alignment_report.json", "w") as f:
            json.dump(result.dict(), f, indent=2, default=str)
        
        print(f"Aligned: {result.mapped_queries}/{result.total_queries} contigs")
        print(f"Identity: {result.stats.get('mean_identity', 0):.1f}%")
        EOF
        """
}

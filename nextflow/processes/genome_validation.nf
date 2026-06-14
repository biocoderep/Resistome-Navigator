/*
=============================================================================
    GENOME VALIDATION PROCESS
=============================================================================
*/

process genome_validation {
    tag "${sample_id}"
    
    label 'validation'
    
    cpus params.validation_cpus
    memory params.validation_memory
    time "2h"
    
    publishDir "${params.output}/${sample_id}/validation", mode: "copy"
    
    input:
        tuple val(sample_id), path(assembly_file), val(species)
    
    output:
        tuple val(sample_id), path(assembly_file), val(species), path("validation_report.json")
    
    script:
        """
        python << 'EOF'
        import json
        from pathlib import Path
        from backend.genome_validator import GenomeValidationEngine, ValidationConfig
        
        config = ValidationConfig(
            min_length_bp = ${params.min_assembly_length_bp},
            max_contig_count = ${params.max_contig_count},
            n_warn_threshold = ${params.n_warn_threshold},
            n_fail_threshold = ${params.n_fail_threshold},
        )
        
        engine = GenomeValidationEngine(config=config)
        
        report = engine.validate(
            file_path=Path("${assembly_file}"),
            sample_id="${sample_id}",
            species="${species}"
        )
        
        # Save report
        with open("validation_report.json", "w") as f:
            json.dump(report.dict(), f, indent=2, default=str)
        
        print(f"Validation Status: {report.validation_status}")
        print(f"Quality Score: {report.quality_score:.1f}")
        print(f"Proceed to AMR: {report.proceed_to_amr}")
        EOF
        """
}

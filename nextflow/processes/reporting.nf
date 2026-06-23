/*
=============================================================================
    REPORT GENERATION PROCESS
=============================================================================
*/

process generate_report {
    tag "${sample_id}"
    
    label 'reporting'
    
    cpus 2
    memory "4 GB"
    time "1h"
    
    publishDir "${params.output}/${sample_id}/reports", mode: "copy"
    
    input:
        tuple val(sample_id), path(aggregated_results)
    
    output:
        tuple val(sample_id), path("*.html"), path("*.json"), path("*.tsv")
    
    script:
        """
        generate_report.py "${aggregated_results}"
        """
}

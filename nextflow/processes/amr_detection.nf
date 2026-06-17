/*
=============================================================================
    AMR DETECTION PROCESS
=============================================================================
*/

process amr_detection {
    tag "${sample_id}"
    
    label 'amr_detection'
    
    cpus params.amr_cpus
    memory params.amr_memory
    time "6h"
    
    publishDir "${params.output}/${sample_id}/amr_detection", mode: "copy"
    
    input:
        tuple val(sample_id), path(assembly_file), val(species), path(validation_report)
        path card_db
        path amrfinder_db
    
    output:
        tuple val(sample_id), path("amr_detection_report.json"), path("rgi*.json", optional: true), path("amrfinderplus*.tsv", optional: true)
    
    script:
        """
        python << 'EOF'
        import json
        from pathlib import Path
        from backend.amr_detection import CARDRGIDetector, AMRFinderPlusDetector, AMRConfig
        
        # Load validation report
        with open("${validation_report}") as f:
            validation = json.load(f)
        
        if not validation.get("proceed_to_amr", False):
            print("ERROR: Assembly did not pass validation. Cannot proceed to AMR analysis.")
            exit(1)
        
        output_dir = Path(".")
        
        # Configure AMR detection
        config = AMRConfig(
            tools=["card_rgi", "amrfinderplus"],
            min_identity_percent=${params.amr_min_identity},
            min_coverage_percent=${params.amr_min_coverage},
            threads=${params.amr_cpus},
            enable_consensus=True
        )
        
        # Run CARD RGI
        print("Starting CARD RGI analysis...")
        rgi_detector = CARDRGIDetector(config=config)
        rgi_result = rgi_detector.detect(
            assembly_file=Path("${assembly_file}"),
            output_dir=output_dir,
            sample_id="${sample_id}"
        )
        
        # Run AMRFinderPlus
        print("Starting AMRFinderPlus analysis...")
        amrfinder_detector = AMRFinderPlusDetector(config=config)
        amrfinder_result = amrfinder_detector.detect(
            assembly_file=Path("${assembly_file}"),
            output_dir=output_dir,
            sample_id="${sample_id}"
        )
        
        # Aggregate results
        all_hits = rgi_result.hits + amrfinder_result.hits
        unique_genes = len(set((h.gene_name, h.resistance_class) for h in all_hits))
        
        # Belt-and-suspenders: Nextflow requires the files to exist even with optional: true
        if not list(Path(".").glob("rgi*.json")):
            with open("rgi_empty.json", "w") as f: json.dump({}, f)
        if not list(Path(".").glob("amrfinderplus*.tsv")):
            Path("amrfinderplus_empty.tsv").touch()
        
        # Create master report
        master_report = {
            "sample_id": "${sample_id}",
            "species": "${species}",
            "validation_status": validation.get("validation_status"),
            "quality_score": validation.get("quality_score"),
            "total_amr_genes_detected": len(all_hits),
            "unique_gene_families": unique_genes,
            "rgi_results": rgi_result.model_dump(),
            "amrfinderplus_results": amrfinder_result.model_dump(),
            "errors": rgi_result.errors + amrfinder_result.errors
        }
        
        with open("amr_detection_report.json", "w") as f:
            json.dump(master_report, f, indent=2, default=str)
        
        print(f"Total AMR genes detected: {len(all_hits)}")
        print(f"Unique gene families: {unique_genes}")
        EOF
        """
}

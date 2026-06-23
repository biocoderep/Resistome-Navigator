/*
=============================================================================
    RESULT AGGREGATION PROCESS
=============================================================================
*/

process aggregate_results {
    tag "${sample_id}"
    
    label 'aggregation'
    
    cpus 2
    memory "4 GB"
    time "1h"
    
    publishDir "${params.output}/${sample_id}/aggregation", mode: "copy"
    
    input:
        tuple val(sample_id), path(amr_report), val(rgi_output), val(amrfinder_output), path(alignment_report), path(alignment_bam)
    
    output:
        tuple val(sample_id), path("aggregated_results.json")
    
    script:
        """
        python << 'EOF'
        import json
        from pathlib import Path
        from collections import defaultdict
        
        # Load individual reports
        with open("${amr_report}") as f:
            amr_data = json.load(f)
        
        with open("${alignment_report}") as f:
            alignment_data = json.load(f)
        
        # Build consensus: hits present in multiple tools get higher confidence
        tool_hits = defaultdict(list)
        
        # Extract hits from each tool
        for hit in amr_data.get("rgi_results", {}).get("hits", []):
            key = (hit["gene_name"], hit["gene_family"])
            tool_hits[key].append(hit)
        
        for hit in amr_data.get("amrfinderplus_results", {}).get("hits", []):
            key = (hit["gene_name"], hit["gene_family"])
            tool_hits[key].append(hit)
        
        # Determine consensus confidence
        consensus_hits = []
        for (gene_name, gene_family), hits in tool_hits.items():
            if len(hits) >= 2:
                # Consensus hit: confirmed by multiple tools
                avg_identity = sum(h.get("identity_percent", 0) for h in hits) / len(hits)
                consensus_hits.append({
                    "gene_name": gene_name,
                    "gene_family": gene_family,
                    "tool_count": len(hits),
                    "avg_identity": avg_identity,
                    "tools": [h.get("tool_name") for h in hits]
                })
        
        # Aggregate report
        aggregated = {
            "sample_id": "${sample_id}",
            "validation_status": amr_data.get("validation_status"),
            "quality_score": amr_data.get("quality_score"),
            "assembly_alignment": {
                "total_queries": alignment_data.get("total_queries"),
                "mapped_queries": alignment_data.get("mapped_queries"),
                "mapped_percent": alignment_data.get("mapped_percent")
            },
            "amr_detection": {
                "total_genes_detected": amr_data.get("total_amr_genes_detected"),
                "unique_gene_families": amr_data.get("unique_gene_families"),
                "resistance_classes": amr_data.get("rgi_results", {}).get("resistance_classes", [])
            },
            "consensus_hits": consensus_hits,
            "consensus_count": len(consensus_hits),
            "tool_concordance": f"{len(consensus_hits)}/{amr_data.get('total_amr_genes_detected', 1)}" if amr_data.get("total_amr_genes_detected", 0) > 0 else "0/0"
        }
        
        with open("aggregated_results.json", "w") as f:
            json.dump(aggregated, f, indent=2)
        
        print(f"Aggregation complete: {len(consensus_hits)} consensus hits")
        EOF
        """
}

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
        python << 'EOF'
        import json
        from pathlib import Path
        from datetime import datetime
        
        # Load aggregated results
        with open("${aggregated_results}") as f:
            results = json.load(f)
        
        # Generate JSON report (structured output)
        json_report = {
            "report_version": "1.0",
            "generation_date": datetime.now().isoformat(),
            "sample_id": results["sample_id"],
            "pipeline_stage": "Module 1 - Genome Validation & AMR Detection",
            "results": results
        }
        
        with open("report.json", "w") as f:
            json.dump(json_report, f, indent=2)
        
        # Generate TSV report (human-readable tabular format)
        with open("report.tsv", "w") as f:
            f.write("Field\\tValue\\n")
            f.write(f"Sample ID\\t{results['sample_id']}\\n")
            f.write(f"Validation Status\\t{results['validation_status']}\\n")
            f.write(f"Quality Score\\t{results['quality_score']}\\n")
            f.write(f"Mapped Reads\\t{results['assembly_alignment']['mapped_percent']:.1f}%\\n")
            f.write(f"Total AMR Genes\\t{results['amr_detection']['total_genes_detected']}\\n")
            f.write(f"Consensus Hits (≥2 tools)\\t{results['consensus_count']}\\n")
            f.write(f"Tool Concordance\\t{results['tool_concordance']}\\n")
            f.write(f"\\nResistance Classes:\\n")
            for rc in results['amr_detection']['resistance_classes']:
                f.write(f"  - {rc}\\n")
        
        # Generate HTML report
        html_report = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AMR Detection Report - {results['sample_id']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #2c3e50; color: white; padding: 15px; }}
                .section {{ margin-top: 20px; padding: 15px; border: 1px solid #ddd; }}
                .stat {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #27ae60; }}
                .stat-label {{ color: #555; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .consensus {{ background-color: #d5f4e6; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>AMR Detection Report</h1>
                <p>Sample: {results['sample_id']}</p>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="section">
                <h2>Quality Metrics</h2>
                <div class="stat">
                    <div class="stat-label">Validation Status</div>
                    <div class="stat-value">{results['validation_status']}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Quality Score</div>
                    <div class="stat-value">{results['quality_score']:.1f}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Alignment Rate</div>
                    <div class="stat-value">{results['assembly_alignment']['mapped_percent']:.1f}%</div>
                </div>
            </div>
            
            <div class="section">
                <h2>AMR Detection Results</h2>
                <div class="stat">
                    <div class="stat-label">Total AMR Genes</div>
                    <div class="stat-value">{results['amr_detection']['total_genes_detected']}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Consensus Hits (≥2 tools)</div>
                    <div class="stat-value consensus">{results['consensus_count']}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Tool Concordance</div>
                    <div class="stat-value">{results['tool_concordance']}</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Resistance Classes Detected</h2>
                <ul>
        """
        
        for rc in results['amr_detection']['resistance_classes']:
            html_report += f"<li>{rc}</li>"
        
        html_report += """
                </ul>
            </div>
            
            <div class="section">
                <h2>Consensus Hits (High Confidence)</h2>
                <table>
                    <tr>
                        <th>Gene Name</th>
                        <th>Gene Family</th>
                        <th>Tool Count</th>
                        <th>Avg Identity</th>
                        <th>Tools</th>
                    </tr>
        """
        
        for hit in results.get('consensus_hits', []):
            html_report += f"""
                    <tr>
                        <td>{hit['gene_name']}</td>
                        <td>{hit['gene_family']}</td>
                        <td>{hit['tool_count']}</td>
                        <td>{hit['avg_identity']:.1f}%</td>
                        <td>{', '.join(hit['tools'])}</td>
                    </tr>
            """
        
        html_report += """
                </table>
            </div>
        </body>
        </html>
        """
        
        with open("report.html", "w") as f:
            f.write(html_report)
        
        print(f"Reports generated: JSON, TSV, HTML")
        EOF
        """
}

export { generate_report }

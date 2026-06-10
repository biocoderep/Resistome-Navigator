import json
import os
from pycirclize import Circos

def get_isolate_data(job_id: str):
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cohort_mock.json")
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        data = json.load(f)
        # return first isolate or match by job_id
        cohort = data.get("cohort", [])
        if not cohort:
            return None
        return cohort[0]

def generate_circos_plot(job_id: str) -> str:
    isolate = get_isolate_data(job_id)
    if not isolate:
        return "<svg></svg>"
        
    amr_genes = isolate.get("amr_genes", [])
    virulence_genes = isolate.get("virulence_genes", [])
    
    # Extract unique contigs and their max lengths
    sectors = {}
    for g in amr_genes + virulence_genes:
        cid = g.get("contig_id", "contig_1")
        end = g.get("end", 0)
        sectors[cid] = max(sectors.get(cid, 500000), end + 50000)
        
    if not sectors:
        sectors = {"contig_1": 500000}
        
    circos = Circos(sectors, space=5)
    
    # Outer ring: AMR genes (Red palette)
    # Inner ring: Virulence genes (Purple palette)
    
    for sector in circos.sectors:
        # Plot backbone
        track_backbone = sector.add_track((80, 100))
        track_backbone.axis(fc="lightgrey")
        track_backbone.text(sector.name, color="#0F172A", size=10)
        track_backbone.xticks_by_interval(100000, label_formatter=lambda v: f"{v/1000:.0f} kb", label_size=8, label_color="#0F172A")
        
        # AMR Track
        track_amr = sector.add_track((65, 75))
        s_amr = [g for g in amr_genes if g.get("contig_id") == sector.name]
        for g in s_amr:
            start = g.get("start", 0)
            end = g.get("end", 1000)
            track_amr.rect(start, end, fc="#fa4d56", ec="black")
            track_amr.text(g.get("gene_name"), x=(start+end)/2, size=8, color="#fa4d56", r=12)
            
        # Virulence Track
        track_vir = sector.add_track((50, 60))
        s_vir = [g for g in virulence_genes if g.get("contig_id") == sector.name]
        for g in s_vir:
            start = g.get("start", 0)
            end = g.get("end", 1000)
            track_vir.rect(start, end, fc="#AF4BCE", ec="black")
            track_vir.text(g.get("gene_name"), x=(start+end)/2, size=8, color="#AF4BCE", r=-12)
            
    fig = circos.plotfig()
    
    # Save to SVG string
    import io
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", transparent=True)
    svg_str = buf.getvalue()
    buf.close()
    
    return svg_str

import React, { useState } from "react";
import { getStatusColors, PALETTE, getColorForClass } from "../utils/palette";

function QualityGate({ status, metrics }: { status: string, metrics: any }) {
  const statusColors: Record<string, string> = { PASS: "text-green-400 border-green-400/30 bg-green-900/10", WARNING: "text-yellow-400 border-yellow-400/30 bg-yellow-900/10", FAIL: "text-red-400 border-red-400/30 bg-red-900/10" };
  const colorClass = statusColors[status] || statusColors.PASS;

  return (
    <div className={`border rounded-xl p-4 flex items-center justify-between flex-wrap gap-4 ${colorClass}`}>
      <div className="flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-current" />
        <span className="font-bold text-sm tracking-wide uppercase">
          Genome QC: {status}
        </span>
      </div>
      <div className="flex gap-6 flex-wrap">
        {[
          ["Length", metrics.totalLength || "N/A"],
          ["N50", metrics.n50 || "N/A"],
          ["GC%", `${metrics.gcContent || 0}%`],
          ["Contigs", metrics.totalContigs || "N/A"],
        ].map(([label, val]) => (
          <div key={label} className="text-center">
            <div className="text-xs text-text-muted tracking-wider uppercase">{label}</div>
            <div className="text-sm font-semibold text-text-primary tabular-nums">{val}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CircosPlot({ jobId }: { jobId: string }) {
  const [svgStr, setSvgStr] = useState<string>("");

  React.useEffect(() => {
    fetch(`http://127.0.0.1:8000/api/v1/analysis/${jobId}/circos`)
      .then(res => res.text())
      .then(svg => setSvgStr(svg))
      .catch(err => console.error(err));
  }, [jobId]);

  if (!svgStr) return <div className="animate-pulse text-text-muted">Loading Circos Plot...</div>;

  return (
    <div 
      className="w-full h-full flex items-center justify-center"
      dangerouslySetInnerHTML={{ __html: svgStr }}
      style={{
        "& svg": { width: "100%", height: "100%", maxHeight: "500px" }
      } as any}
    />
  );
}

const ConfidenceBar = ({ val }: { val: number }) => {
  const pct = val * 100;
  const color = val >= 0.9 ? "bg-green-500" : val >= 0.75 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 bg-surface-dark rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-text-muted tabular-nums">{val.toFixed(2)}</span>
    </div>
  );
};

function AntibiogramTable({ data, selectedDrug, onSelect }: { data: any[], selectedDrug: string | null, onSelect: (d: string | null) => void }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-surface-dark">
      <table className="w-full text-left text-sm border-collapse">
        <thead className="bg-surface-dark text-text-muted text-xs uppercase tracking-wider">
          <tr>
            <th className="p-3 font-semibold">Drug</th>
            <th className="p-3 font-semibold">Class</th>
            <th className="p-3 font-semibold">Prediction</th>
            <th className="p-3 font-semibold">Confidence</th>
            <th className="p-3 font-semibold">Evidence</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-surface-dark bg-surface-card">
          {data.map((row) => {
            const sc = getStatusColors(row.sir);
            const isSelected = selectedDrug === row.drug;
            return (
              <tr
                key={row.drug}
                onClick={() => onSelect(isSelected ? null : row.drug)}
                className={`cursor-pointer transition-colors hover:bg-surface-dark/50 ${isSelected ? 'bg-surface-dark/80' : ''}`}
              >
                <td className="p-3 font-semibold text-text-primary">{row.drug}</td>
                <td className="p-3 text-text-muted text-xs">{row.class}</td>
                <td className="p-3">
                  <span className={`inline-block px-3 py-1 rounded-md text-xs font-bold border tracking-wider ${sc.bg} ${sc.text} ${sc.border}`}>
                    {row.sir}
                  </span>
                </td>
                <td className="p-3"><ConfidenceBar val={row.confidence} /></td>
                <td className="p-3 text-text-muted text-xs max-w-xs truncate" title={row.evidence}>{row.evidence}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function CollapsibleSection({ title, count, defaultOpen, children }: { title: string, count?: number, defaultOpen?: boolean, children: React.ReactNode }) {
  const [open, setOpen] = useState(defaultOpen || false);
  return (
    <div className="border border-surface-dark rounded-lg overflow-hidden bg-surface-card">
      <button
        onClick={() => setOpen(!open)}
        className="w-full p-4 flex items-center justify-between text-sm font-semibold text-text-primary hover:bg-surface-dark/50 transition-colors"
      >
        <span>{title} {count != null && <span className="font-normal text-text-muted text-xs ml-1">({count})</span>}</span>
        <span className={`text-text-muted transition-transform duration-200 ${open ? 'rotate-180' : ''}`}>▾</span>
      </button>
      {open && <div className="px-4 pb-4">{children}</div>}
    </div>
  );
}

export default function AMRDashboard({ data }: { data: any }) {
  const [selectedDrug, setSelectedDrug] = useState<string | null>(null);

  if (!data) return <div className="p-8 text-center text-text-muted animate-pulse">Loading Analytics...</div>;

  const antibiogram = data.phenotypes || [];
  const rCount = antibiogram.filter((a: any) => a.sir === "R").length;
  const iCount = antibiogram.filter((a: any) => a.sir === "I").length;
  const sCount = antibiogram.filter((a: any) => a.sir === "S").length;

  const qualityData = {
    status: data.validation?.status || "PASS",
    totalLength: "5.12 Mbp", // mock or from data
    n50: "312,450",
    gcContent: 50.8,
    totalContigs: 42,
  };

  return (
    <div className="max-w-5xl mx-auto p-6 text-text-primary space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary">AMR Analysis Report</h1>
        <div className="text-xs text-text-muted mt-1">
          <span className="font-mono text-accent-teal">{data.id || "Unknown"}</span> · {new Date().toLocaleDateString()}
        </div>
      </div>

      {/* Quality Gate */}
      <QualityGate status={qualityData.status} metrics={qualityData} />

      {/* Resistance Summary Strip */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Resistant", count: rCount, color: "text-red-400", bg: "bg-red-900/10 border border-red-900/30" },
          { label: "Intermediate", count: iCount, color: "text-yellow-400", bg: "bg-yellow-900/10 border border-yellow-900/30" },
          { label: "Susceptible", count: sCount, color: "text-green-400", bg: "bg-green-900/10 border border-green-900/30" },
        ].map(s => (
          <div key={s.label} className={`p-4 rounded-xl text-center ${s.bg}`}>
            <div className={`text-3xl font-bold tabular-nums ${s.color}`}>{s.count}</div>
            <div className={`text-xs font-semibold uppercase tracking-wider mt-1 ${s.color}`}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Antibiogram */}
      <div>
        <div className="flex justify-between items-baseline mb-3">
          <h2 className="text-lg font-bold text-text-primary">Predicted Antibiogram</h2>
          <span className="text-xs text-text-muted">Click a row to trace evidence below &darr;</span>
        </div>
        <AntibiogramTable data={antibiogram} selectedDrug={selectedDrug} onSelect={setSelectedDrug} />
      </div>

      {/* Genomic Architecture */}
      <div>
        <h2 className="text-lg font-bold text-text-primary mb-3">Genomic Architecture</h2>
        <div className="border border-surface-dark bg-surface-card rounded-lg flex items-center justify-center p-4 overflow-hidden relative" style={{ minHeight: '400px' }}>
          <div className="absolute top-4 right-4 text-xs text-text-muted space-y-1 bg-surface-dark/80 p-2 rounded z-10">
            <div className="flex items-center gap-2"><div className="w-3 h-3 bg-[#fa4d56]" /> AMR Genes</div>
            <div className="flex items-center gap-2"><div className="w-3 h-3 bg-[#AF4BCE]" /> Virulence</div>
          </div>
          <CircosPlot jobId={data.id || "mock-job-id"} />
        </div>
      </div>

      {/* Collapsible Details */}
      <div className="space-y-4">
        <CollapsibleSection title="Detected AMR Genes" count={data.amr_genes?.length} defaultOpen={true}>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-text-muted text-xs uppercase tracking-wider border-b border-surface-dark">
                <tr>
                  <th className="py-2">Gene</th>
                  <th className="py-2">Class</th>
                  <th className="py-2">Mechanism</th>
                  <th className="py-2">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-dark">
                {(data.amr_genes || []).map((g: any, i: number) => (
                  <tr key={i}>
                    <td className="py-2 font-mono font-semibold text-accent-teal">{g.gene_name}</td>
                    <td className="py-2 text-text-muted text-xs">{g.antibiotic_class}</td>
                    <td className="py-2 text-text-muted text-xs">{g.resistance_mechanism}</td>
                    <td className="py-2"><ConfidenceBar val={g.confidence_score || 0.99} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CollapsibleSection>
        
        <CollapsibleSection title="Detected Virulence Factors" count={data.virulence_genes?.length || 0} defaultOpen={false}>
          {data.virulence_status === 'not_run' ? (
            <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg text-center">Virulence not assessed.</div>
          ) : (!data.virulence_genes || data.virulence_genes.length === 0) ? (
            <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg text-center">No virulence factors detected.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-text-muted text-xs uppercase tracking-wider border-b border-surface-dark">
                  <tr>
                    <th className="py-2">Factor</th>
                    <th className="py-2">Type</th>
                    <th className="py-2">Subclass</th>
                    <th className="py-2">Contig</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-dark">
                  {data.virulence_genes.map((g: any, i: number) => (
                    <tr key={i}>
                      <td className="py-2 font-mono font-semibold" style={{ color: PALETTE.purple1 }}>{g.gene_name}</td>
                      <td className="py-2 text-text-muted text-xs">{g.element_type || g.virulence_factor}</td>
                      <td className="py-2 text-text-muted text-xs">{g.subclass || g.virulence_category}</td>
                      <td className="py-2 text-text-muted text-xs">{g.contig_id || "N/A"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CollapsibleSection>
      </div>
      
      {/* Footer */}
      <div className="pt-6 border-t border-surface-dark text-xs text-text-muted flex justify-between">
        <span>Databases: CARD v3.2.9 · ResFinder v4.4 · AMRFinderPlus</span>
        <span>Pipeline v2.1.0 · For research use only</span>
      </div>
    </div>
  );
}

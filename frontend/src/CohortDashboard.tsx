import React, { useEffect, useState } from 'react';
import { ExportCard } from './components/ExportCard';
import { SirBadge } from './components/SirBadge';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, ZAxis, Cell, Sankey } from 'recharts';
import DimReductionPlot from './components/charts/DimReductionPlot';
import CoOccurrenceNetwork from './components/charts/CoOccurrenceNetwork';
import MinimumSpanningTree from './components/charts/MinimumSpanningTree';
import AntibiogramHeatmap, { type AntibiogramIsolate } from './cohort/AntibiogramHeatmap';
import ResistanceClassFrequency, { type ClassFrequencyRow } from './cohort/ResistanceClassFrequency';

const CARBON_COLORS = [
  '#6929c4', '#1192e8', '#005d5d', '#9f1853', '#fa4d56',
  '#570408', '#198038', '#002d9c', '#ee5396', '#b28600',
  '#009d9a', '#012749', '#8a3800', '#a56eff'
];

export const CohortDashboard = () => {
  const [cohort, setCohort] = useState<any[]>([]);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/v1/analysis/cohort')
      .then(res => res.json())
      .then(json => setCohort(json.cohort))
      .catch(err => console.error(err));
  }, []);

  if (!cohort || cohort.length === 0) return <div className="p-10 text-text-primary text-center">Loading Large Cohort Data...</div>;

  // 1. Prepare Scatter Plot Data (Identity vs Coverage)
  const scatterData: any[] = [];
  cohort.forEach(isolate => {
    isolate.amr_genes.forEach((g: any) => {
      g.hits.forEach((h: any) => {
        scatterData.push({
          gene: g.gene_name,
          class: g.antibiotic_class,
          identity: h.identity,
          coverage: h.coverage,
          id: isolate.isolate_id
        });
      });
    });
  });

  // Assign a carbon color to each unique class
  const uniqueClasses = Array.from(new Set(scatterData.map(d => d.class)));

  // 2. Prepare Top Co-occurring Combinations (UpSet alternative)
  const comboCounts: Record<string, number> = {};
  cohort.forEach(isolate => {
    const genes = isolate.amr_genes.map((g: any) => g.gene_name).sort();
    const key = genes.join(' + ');
    comboCounts[key] = (comboCounts[key] || 0) + 1;
  });
  const topCombos = Object.entries(comboCounts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10); // Top 10 combos

  // 3. Prepare Resistance Barcode (Stack of isolates x drugs)
  // Get all unique drugs
  const allDrugs = Array.from(new Set(cohort[0].phenotype_predictions.map((p:any) => p.drug)));
  
  // 4. Sankey Diagram Data (Gene -> Mechanism -> Class -> S/I/R)
  // Simplified for performance: just Mechanism -> Class
  const sankeyNodes: any[] = [];
  const sankeyLinks: any[] = [];
  const nodeIndex: Record<string, number> = {};
  
  const addNode = (name: string) => {
    if (nodeIndex[name] === undefined) {
      nodeIndex[name] = sankeyNodes.length;
      sankeyNodes.push({ name });
    }
    return nodeIndex[name];
  };

  const linkCounts: Record<string, number> = {};
  cohort.forEach(isolate => {
    isolate.amr_genes.forEach((g: any) => {
      const mech = g.resistance_mechanism;
      const cls = g.antibiotic_class;
      const key = `${mech}|${cls}`;
      linkCounts[key] = (linkCounts[key] || 0) + 1;
    });
  });

  Object.entries(linkCounts).forEach(([key, value]) => {
    const [source, target] = key.split('|');
    const sId = addNode(source);
    const tId = addNode(target);
    sankeyLinks.push({ source: sId, target: tId, value });
  });

  const sankeyData = { nodes: sankeyNodes, links: sankeyLinks };

  // --- Clinical antibiogram heatmap (isolates x antibiotics) ---
  const antibioticsSet = new Set<string>();
  cohort.forEach((iso) =>
    (iso.phenotype_predictions || []).forEach((p: any) => antibioticsSet.add(p.drug)),
  );
  const antibiotics = Array.from(antibioticsSet);
  const heatmapIsolates: AntibiogramIsolate[] = cohort.map((iso) => ({
    id: iso.isolate_id || iso.id,
    label: iso.isolate_id || iso.filename || iso.id,
    profile: Object.fromEntries(
      (iso.phenotype_predictions || []).map((p: any) => [p.drug, p.sir]),
    ),
  }));

  // --- Resistance class frequency (stacked S/I/R per class) ---
  const classAgg: Record<string, ClassFrequencyRow> = {};
  cohort.forEach((iso) =>
    (iso.phenotype_predictions || []).forEach((p: any) => {
      const cat = p.drug_class || p.antibiotic_class || p.drug;
      const row = classAgg[cat] || { category: cat, R: 0, I: 0, S: 0 };
      if (p.sir === 'R') row.R += 1;
      else if (p.sir === 'I') row.I += 1;
      else if (p.sir === 'S') row.S += 1;
      classAgg[cat] = row;
    }),
  );
  const classFrequency = Object.values(classAgg).sort((a, b) => b.R - a.R);

  return (
    <div className="flex-1 p-10 overflow-y-auto w-full">
      <div className="max-w-7xl mx-auto">
        <header className="mb-10 pb-6 border-b border-surface-card flex justify-between items-end">
          <div>
            <h2 className="text-3xl font-sans font-bold text-text-primary">Cohort Epidemiology Dashboard</h2>
            <p className="text-text-muted mt-2 font-mono text-sm">Total Isolates: {cohort.length} • Stress Test: Large Data</p>
          </div>
        </header>

        {/* Clinical Antibiogram Heatmap (isolates x antibiotics) */}
        <div className="grid grid-cols-1 gap-8 mb-8">
          <ExportCard title="Clinical Antibiogram Heatmap" filename="antibiogram_heatmap"
                      subtitle="Predicted susceptibility — isolates (rows) × antibiotics (columns)">
            <AntibiogramHeatmap isolates={heatmapIsolates} antibiotics={antibiotics} />
          </ExportCard>
        </div>

        {/* Resistance Class Frequency */}
        <div className="grid grid-cols-1 gap-8 mb-8">
          <ExportCard title="Resistance Class Frequency" filename="resistance_class_frequency"
                      subtitle="Stacked S/I/R counts across the cohort">
            <ResistanceClassFrequency data={classFrequency} />
          </ExportCard>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <ExportCard title="Resistome Dimensionality Reduction (UMAP)" filename="UMAP.png">
            <DimReductionPlot />
          </ExportCard>
          <ExportCard title="Gene Co-occurrence Network" filename="Network.png">
            <CoOccurrenceNetwork />
          </ExportCard>
        </div>
        
        <div className="grid grid-cols-1 gap-8 mb-8">
          <ExportCard title="Minimum Spanning Tree (Resistome Clades)" filename="MST.png">
            <MinimumSpanningTree />
          </ExportCard>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          
          {/* Scatter Plot: Identity vs Coverage */}
          <ExportCard title="Hit Quality (Identity vs Coverage)" filename="Cohort_Scatter.png">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis type="number" dataKey="identity" name="Identity" unit="%" domain={[80, 100]} stroke="#64748B" />
                  <YAxis type="number" dataKey="coverage" name="Coverage" unit="%" domain={[80, 100]} stroke="#64748B" />
                  <ZAxis type="category" dataKey="gene" name="Gene" />
                  <Tooltip 
                    cursor={{ strokeDasharray: '3 3' }}
                    contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', color: '#0F172A', fontSize: '12px', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Scatter name="AMR Hits" data={scatterData} fill="#00AD9F">
                    {scatterData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CARBON_COLORS[uniqueClasses.indexOf(entry.class) % CARBON_COLORS.length]} />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <div className="flex flex-wrap gap-2 mt-4 text-xs text-text-muted justify-center">
              {uniqueClasses.slice(0, 8).map((cls, i) => (
                <div key={cls} className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: CARBON_COLORS[i % CARBON_COLORS.length] }}></div>
                  {cls as string}
                </div>
              ))}
            </div>
          </ExportCard>

          {/* UpSet Plot alternative: Top Co-occurring Combinations */}
          <ExportCard title="Top Gene Co-occurrences" filename="Cohort_Combos.png">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topCombos} layout="vertical" margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
                  <XAxis type="number" stroke="#64748B" fontSize={12} />
                  <YAxis dataKey="name" type="category" width={180} stroke="#64748B" fontSize={10} tick={{ fill: '#0F172A' }} />
                  <Tooltip 
                    cursor={{fill: '#F8FAFC'}} 
                    contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', color: '#0F172A', fontSize: '12px', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} 
                  />
                  <Bar dataKey="count" fill={CARBON_COLORS[0]} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ExportCard>

        </div>

        <div className="grid grid-cols-1 gap-8 mb-8">
          {/* Sankey Flow Diagram */}
          <ExportCard title="Resistance Mechanism Flow" filename="Cohort_Sankey.png">
            <div className="h-96 w-full flex items-center justify-center">
              <div className="w-full h-full p-4">
                <ResponsiveContainer width="100%" height="100%">
                  <Sankey
                    data={sankeyData}
                    node={{ fill: CARBON_COLORS[2] }}
                    nodePadding={50}
                    margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
                    link={{ stroke: CARBON_COLORS[1], strokeOpacity: 0.3 }}
                  >
                    <Tooltip contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', color: '#0F172A', fontSize: '12px', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                  </Sankey>
                </ResponsiveContainer>
              </div>
            </div>
          </ExportCard>
        </div>

        <div className="grid grid-cols-1 gap-8">
          {/* Resistance Barcode Strip */}
          <ExportCard title="Population Resistance Barcode" filename="Cohort_Barcode.png">
            <div className="overflow-x-auto p-4 bg-surface rounded-lg border border-surface-dark">
              <div className="min-w-max">
                {/* Header (Drugs) */}
                <div className="flex mb-2 pl-24">
                  {allDrugs.map((d: any) => (
                    <div key={d} className="w-6 rotate-45 origin-bottom-left text-[10px] text-text-muted truncate mb-2">
                      {d}
                    </div>
                  ))}
                </div>
                
                {/* Isolates */}
                {cohort.map((isolate, i) => (
                  <div key={i} className="flex items-center mb-1 hover:bg-surface-dark transition-colors">
                    <div className="w-24 text-[10px] font-mono text-text-primary truncate pr-2">
                      {isolate.isolate_id}
                    </div>
                    {allDrugs.map((drugName: any, j: number) => {
                      const p = isolate.phenotype_predictions.find((p: any) => p.drug === drugName);
                      let cellColor = 'bg-status-none';
                      if (p?.sir === 'R') cellColor = 'bg-status-r';
                      if (p?.sir === 'I') cellColor = 'bg-status-i';
                      if (p?.sir === 'S') cellColor = 'bg-status-s';
                      return (
                        <div key={j} className={`w-6 h-4 border border-surface-card ${cellColor}`} title={`${drugName}: ${p?.sir}`}></div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </ExportCard>
        </div>

      </div>
    </div>
  );
};

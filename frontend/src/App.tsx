import React, { useEffect, useState } from 'react';
import { ExportCard } from './components/ExportCard';
import { SirBadge } from './components/SirBadge';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid } from 'recharts';

function App() {
  const [data, setData] = useState<any>(null);
  const [validation, setValidation] = useState<any>(null);

  useEffect(() => {
    Promise.all([
      fetch('http://127.0.0.1:8000/api/v1/analysis/test-job-123').then(res => res.json()),
      fetch('http://127.0.0.1:8000/api/v1/samples/test-job-123/validation').then(res => res.json())
    ])
    .then(([analysisData, valData]) => {
      setData(analysisData);
      setValidation(valData);
    })
    .catch(err => console.error(err));
  }, []);

  if (!data || !validation) return <div className="min-h-screen bg-surface flex items-center justify-center text-text-primary text-xl">Loading platform...</div>;

  // Process data for charts
  const mechCounts = data.amr_genes.reduce((acc: any, gene: any) => {
    acc[gene.resistance_mechanism] = (acc[gene.resistance_mechanism] || 0) + 1;
    return acc;
  }, {});
  const mechData = Object.keys(mechCounts).map(key => ({ name: key, value: mechCounts[key] }));

  const classCounts = data.amr_genes.reduce((acc: any, gene: any) => {
    acc[gene.antibiotic_class] = (acc[gene.antibiotic_class] || 0) + 1;
    return acc;
  }, {});
  const classData = Object.keys(classCounts).map(key => ({ name: key, count: classCounts[key] }));

  // Confidence distribution (histogram bins)
  const confBins = { 'Low (<75%)': 0, 'Medium (75-90%)': 0, 'High (>90%)': 0 };
  data.amr_genes.forEach((g: any) => {
    if (g.confidence_score < 0.75) confBins['Low (<75%)']++;
    else if (g.confidence_score < 0.90) confBins['Medium (75-90%)']++;
    else confBins['High (>90%)']++;
  });
  const confData = Object.keys(confBins).map(key => ({ name: key, count: confBins[key] }));

  const COLORS = ['#00AD9F', '#2DD4BF', '#8FA3AD', '#F5A623', '#F4503B'];

  return (
    <div className="min-h-screen flex bg-surface">
      {/* Sidebar */}
      <div className="w-64 bg-surface-dark border-r border-surface-card p-6 flex flex-col shadow-2xl z-10">
        <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-accent-teal to-blue-400 mb-8">
          AMR Platform
        </h1>
        <div className="text-text-muted text-xs font-bold mb-4 tracking-widest uppercase">My Samples</div>
        <div className="bg-surface-card p-4 rounded-xl border-l-4 border-accent-teal shadow-md cursor-pointer mb-3">
          <div className="text-text-primary font-bold text-sm">E.coli_ICU01</div>
          <div className="text-xs text-text-muted mt-1 flex justify-between items-center">
            <span>test-job-123</span>
            <span className="w-2 h-2 rounded-full bg-status-s"></span>
          </div>
        </div>
        <div className="p-4 rounded-xl border border-surface-card hover:bg-surface-card/50 transition-colors cursor-pointer opacity-60">
          <div className="text-text-primary font-bold text-sm">K.pneumoniae_W02</div>
          <div className="text-xs text-text-muted mt-1 flex justify-between items-center">
            <span>test-job-124</span>
            <span className="w-2 h-2 rounded-full bg-status-i animate-pulse"></span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-10 overflow-y-auto">
        <div className="max-w-6xl mx-auto">
          <header className="mb-10 pb-6 border-b border-surface-card flex flex-col md:flex-row md:justify-between md:items-end gap-4">
            <div>
              <h2 className="text-3xl font-sans font-bold text-text-primary">Analysis Dashboard</h2>
              <p className="text-text-muted mt-2 font-mono text-sm">Job ID: test-job-123 • Pipeline: MODULE_1_AMR</p>
            </div>
            
            {/* Validation Banner */}
            <div className="bg-surface-card border border-status-s rounded-xl p-4 flex items-center gap-6">
              <div>
                <div className="text-xs text-text-muted uppercase tracking-wider font-bold mb-1">Assembly Quality</div>
                <div className="text-status-s font-bold text-lg">{validation.status}</div>
              </div>
              <div className="flex gap-4 border-l border-surface-dark pl-6">
                <div>
                  <div className="text-xs text-text-muted">N50</div>
                  <div className="font-mono text-text-primary">{(validation.validation.assembly_metrics.n50 / 1000).toFixed(1)}k</div>
                </div>
                <div>
                  <div className="text-xs text-text-muted">Contigs</div>
                  <div className="font-mono text-text-primary">{validation.validation.assembly_metrics.contigs}</div>
                </div>
                <div>
                  <div className="text-xs text-text-muted">Length</div>
                  <div className="font-mono text-text-primary">{(validation.validation.assembly_metrics.total_length / 1000000).toFixed(2)}Mbp</div>
                </div>
              </div>
            </div>
          </header>

          {/* Grid Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            
            {/* Heatmap Grid implementation for Phenotypes */}
            <ExportCard title="Resistance Heatmap" filename="Ecoli_ICU01_heatmap.png">
              <div className="p-4 bg-surface-dark/50 rounded-lg border border-surface-dark overflow-x-auto">
                <div className="flex gap-2 min-w-max">
                  {/* Row Label */}
                  <div className="w-32 flex items-center font-bold text-text-primary text-sm">
                    E.coli_ICU01
                  </div>
                  {/* Grid Cells */}
                  {data.phenotype_predictions.map((p: any, i: number) => {
                    let cellColor = 'bg-status-none';
                    if (p.sir === 'R') cellColor = 'bg-status-r';
                    if (p.sir === 'I') cellColor = 'bg-status-i';
                    if (p.sir === 'S') cellColor = 'bg-status-s';
                    
                    return (
                      <div key={i} className="flex flex-col items-center group relative cursor-pointer">
                        <div className={`w-10 h-10 rounded shadow-md ${cellColor} border border-surface-card hover:brightness-110 transition-all`}></div>
                        <div className="text-[10px] text-text-muted mt-2 rotate-45 origin-top-left w-20 truncate">
                          {p.drug}
                        </div>
                        {/* Tooltip */}
                        <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 hidden group-hover:block bg-surface-card border border-surface-dark text-text-primary text-xs p-2 rounded z-50 w-48 shadow-xl">
                          <div className="font-bold mb-1">{p.drug} ({p.sir})</div>
                          <div className="text-accent-teal font-mono mb-1">{p.evidence_name}</div>
                          <div className="text-text-muted">{p.explanation}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="h-16"></div> {/* Spacer for rotated text */}
              </div>
            </ExportCard>

            <ExportCard title="Detected AMR Genes" filename="Ecoli_ICU01_genes.png">
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-surface-dark text-text-muted text-sm">
                      <th className="pb-3 px-2 font-semibold">Gene</th>
                      <th className="pb-3 px-2 font-semibold">Class</th>
                      <th className="pb-3 px-2 font-semibold text-right">Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.amr_genes.map((g: any, i: number) => (
                      <tr key={i} className="border-b border-surface-dark/50 hover:bg-surface-dark/30 transition-colors">
                        <td className="py-3 px-2 text-accent-cyan font-mono font-bold">{g.gene_name}</td>
                        <td className="py-3 px-2 text-text-primary text-sm">{g.antibiotic_class}</td>
                        <td className="py-3 px-2 text-right">
                          <span className="px-2 py-1 bg-surface-dark rounded text-text-primary font-mono text-xs border border-surface">
                            {(g.confidence_score * 100).toFixed(0)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </ExportCard>

            <ExportCard title="Resistance Mechanisms" filename="Ecoli_ICU01_mechanisms.png">
              <div className="h-64 flex flex-col">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={mechData} innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value" stroke="none">
                      {mechData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#12232B', borderColor: '#162A33', color: '#E6EDF0', borderRadius: '8px' }} 
                      itemStyle={{ color: '#E6EDF0' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex justify-center gap-4 text-xs text-text-muted mt-2">
                  {mechData.map((entry, index) => (
                    <div key={index} className="flex items-center gap-1">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></div>
                      {entry.name}
                    </div>
                  ))}
                </div>
              </div>
            </ExportCard>

            <ExportCard title="Antibiotic Classes" filename="Ecoli_ICU01_classes.png">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={classData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                    <XAxis type="number" stroke="#8FA3AD" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis dataKey="name" type="category" stroke="#8FA3AD" width={100} tick={{ fill: '#E6EDF0', fontSize: 12 }} tickLine={false} axisLine={false} />
                    <Tooltip 
                      cursor={{fill: '#12232B'}} 
                      contentStyle={{ backgroundColor: '#162A33', borderColor: '#0E1E25', color: '#E6EDF0', borderRadius: '8px' }} 
                    />
                    <Bar dataKey="count" fill="#00AD9F" radius={[0, 4, 4, 0]} barSize={24} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ExportCard>

            <ExportCard title="Confidence Distribution" filename="Ecoli_ICU01_confidence.png">
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={confData} margin={{ top: 15, right: 30, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#162A33" vertical={false} />
                    <XAxis dataKey="name" stroke="#8FA3AD" fontSize={12} tickLine={false} axisLine={false} />
                    <YAxis stroke="#8FA3AD" tick={{ fill: '#E6EDF0', fontSize: 12 }} tickLine={false} axisLine={false} allowDecimals={false} />
                    <Tooltip 
                      cursor={{fill: '#12232B'}} 
                      contentStyle={{ backgroundColor: '#162A33', borderColor: '#0E1E25', color: '#E6EDF0', borderRadius: '8px' }} 
                    />
                    <Bar dataKey="count" fill="#2DD4BF" radius={[4, 4, 0, 0]} barSize={40} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </ExportCard>

            <ExportCard title="Virulence Panel" filename="Ecoli_ICU01_virulence.png">
              <div className="flex flex-wrap gap-3">
                {data.virulence_genes.map((v: any, i: number) => (
                  <div key={i} className="bg-surface-dark border border-accent-teal/30 rounded-lg p-3 flex flex-col min-w-[140px]">
                    <div className="text-accent-teal font-mono font-bold">{v.gene_name}</div>
                    <div className="text-text-primary text-xs mt-1">{v.element_type}</div>
                    <div className="text-text-muted text-[10px] mt-2 flex justify-between">
                      <span>ID: {v.identity_pct}%</span>
                      <span>COV: {v.coverage_pct}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </ExportCard>

          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

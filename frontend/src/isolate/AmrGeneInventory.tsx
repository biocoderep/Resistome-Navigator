import React from 'react';
import { 
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Cell, ReferenceArea, ZAxis, BarChart, Bar 
} from 'recharts';
import { useAmrGenes } from '../../hooks/useAmrData';
import { theme } from '../../theme/tokens';

/**
 * AmrGeneInventory
 * Source: AmrGene table
 * Shows a horizontal bar chart of identity_pct per gene and 
 * an identity vs coverage scatterplot.
 */
interface Props {
  sampleId: string;
}

export default function AmrGeneInventory({ sampleId }: Props) {
  const { data: genes, loading } = useAmrGenes(sampleId);

  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!genes || genes.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No AMR genes detected.</div>;

  // Prepare data for horizontal bar
  const barData = [...genes].sort((a, b) => b.identity_pct - a.identity_pct);

  // Helper to color by drug class using IBM categorical
  const getDrugColor = (drugClass: string) => {
    // simple hash to pick a stable color
    let hash = 0;
    for (let i = 0; i < drugClass.length; i++) hash = drugClass.charCodeAt(i) + ((hash << 5) - hash);
    return theme.colors.categorical[Math.abs(hash) % theme.colors.categorical.length];
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Resistome Inventory</h3>
        <p className="text-xs text-gray-500">Detected AMR genes and their match quality.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-64">
        
        {/* Horizontal Bar - Identity Pct */}
        <div className="flex flex-col h-full">
          <div className="text-xs font-bold text-gray-400 uppercase mb-2">Sequence Identity</div>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 40 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke={theme.colors.surface.border} />
              <XAxis type="number" domain={[0, 100]} hide />
              <YAxis dataKey="gene_name" type="category" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: theme.colors.text.secondary }} />
              <Tooltip 
                cursor={{ fill: theme.colors.surface.base }} 
                contentStyle={{ borderRadius: 4, fontSize: 12, border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}
              />
              <Bar dataKey="identity_pct" radius={[0, 4, 4, 0]} barSize={12}>
                {barData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getDrugColor(entry.drug_class)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Scatter - Identity vs Coverage */}
        <div className="flex flex-col h-full">
          <div className="text-xs font-bold text-gray-400 uppercase mb-2">Hit Quality (Coverage vs Identity)</div>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 10, right: 10, bottom: 20, left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.surface.border} />
              <XAxis 
                dataKey="coverage_pct" type="number" domain={[0, 100]} name="Coverage" 
                tick={{ fontSize: 10, fill: theme.colors.text.secondary }}
                label={{ value: 'Coverage %', position: 'bottom', offset: 0, style: { fontSize: 10, fill: theme.colors.text.secondary } }} 
              />
              <YAxis 
                dataKey="identity_pct" type="number" domain={[50, 100]} name="Identity" 
                tick={{ fontSize: 10, fill: theme.colors.text.secondary }}
                label={{ value: 'Identity %', angle: -90, position: 'insideLeft', style: { fontSize: 10, fill: theme.colors.text.secondary } }} 
              />
              <ZAxis dataKey="confidence_score" range={[20, 150]} />
              
              <ReferenceArea x1={0} x2={60} y1={50} y2={100} fill={theme.colors.phenotype.R} fillOpacity={0.1} />
              <ReferenceArea x1={0} x2={100} y1={50} y2={80} fill={theme.colors.phenotype.R} fillOpacity={0.1} />

              <Tooltip 
                cursor={{ strokeDasharray: '3 3' }} 
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const d = payload[0].payload;
                    return (
                      <div className="bg-gray-900 text-white p-2 rounded text-xs shadow-xl">
                        <div className="font-bold text-blue-300 mb-1">{d.gene_name}</div>
                        <div>Cov: {d.coverage_pct.toFixed(1)}%</div>
                        <div>Id: {d.identity_pct.toFixed(1)}%</div>
                        <div className="text-gray-400 mt-1">{d.drug_class}</div>
                      </div>
                    );
                  }
                  return null;
                }} 
              />
              <Scatter name="Genes" data={genes}>
                {genes.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getDrugColor(entry.drug_class)} opacity={0.8} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

      </div>
    </div>
  );
}

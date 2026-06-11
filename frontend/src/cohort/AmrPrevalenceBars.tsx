import React, { useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Cell 
} from 'recharts';
import { useAmrGenes } from '../hooks/useAmrData';
import { useDashboardFilters } from './FilterContext';
import { theme } from '../theme/tokens';

export default function AmrPrevalenceBars() {
  // Pass filters down when backend is live
  const { data: genes, loading } = useAmrGenes();

  const chartData = useMemo(() => {
    if (!genes || genes.length === 0) return [];

    // Count unique isolates per gene
    const geneToSamples: Record<string, Set<string>> = {};
    const totalSamples = new Set<string>();

    genes.forEach(g => {
      if (!geneToSamples[g.gene_name]) geneToSamples[g.gene_name] = new Set();
      geneToSamples[g.gene_name].add(g.sample_id);
      totalSamples.add(g.sample_id);
    });

    const N = totalSamples.size;

    return Object.entries(geneToSamples)
      .map(([gene, samples]) => ({
        gene,
        prevalence: (samples.size / N) * 100,
        count: samples.size
      }))
      .sort((a, b) => b.prevalence - a.prevalence)
      .slice(0, 15); // Top 15
  }, [genes]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!chartData || chartData.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No prevalence data.</div>;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Top Resistance Determinants</h3>
        <p className="text-xs text-gray-500">Prevalence percentage across cohort.</p>
      </div>

      <div className="flex-1 min-h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 40 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke={theme.colors.surface.border} />
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} />
            <YAxis 
              dataKey="gene" 
              type="category" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fontSize: 10, fill: theme.colors.text.primary, fontWeight: 'bold' }} 
            />
            <Tooltip 
              cursor={{ fill: theme.colors.surface.base }}
              contentStyle={{ borderRadius: 4, fontSize: 12, border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}
              formatter={(value: number) => [`${value.toFixed(1)}%`, 'Prevalence']}
            />
            <Bar dataKey="prevalence" radius={[0, 4, 4, 0]} barSize={16}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={theme.colors.categorical[2]} /> // Teal
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

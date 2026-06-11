import React, { useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, ReferenceLine 
} from 'recharts';
import { usePhenotypePredictions } from '../hooks/useAmrData';
import { theme } from '../theme/tokens';

export default function ResistanceBurdenHistogram() {
  const { data: phenotypes, loading } = usePhenotypePredictions();

  const chartData = useMemo(() => {
    if (!phenotypes || phenotypes.length === 0) return [];

    // 1. Group by sample
    const sampleClasses: Record<string, Set<string>> = {};
    phenotypes.forEach(p => {
      if (!sampleClasses[p.sample_id]) sampleClasses[p.sample_id] = new Set();
      // Only count if resistant
      if (p.predicted_phenotype === 'R') {
        sampleClasses[p.sample_id].add(p.antibiotic_class);
      }
    });

    // 2. Count frequency of class burdens
    const burdenCounts: Record<number, number> = {};
    Object.values(sampleClasses).forEach(classes => {
      const b = classes.size;
      burdenCounts[b] = (burdenCounts[b] || 0) + 1;
    });

    // 3. Format for Recharts (bins 0 to max)
    const maxBurden = Math.max(...Object.keys(burdenCounts).map(Number), 8);
    const bins = [];
    for (let i = 0; i <= maxBurden; i++) {
      bins.push({
        burden: i,
        count: burdenCounts[i] || 0
      });
    }

    return bins;
  }, [phenotypes]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!chartData || chartData.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No burden data.</div>;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Resistance Burden</h3>
        <p className="text-xs text-gray-500">Number of resistant drug classes per isolate.</p>
      </div>

      <div className="flex-1 min-h-[250px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, bottom: 20, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme.colors.surface.border} />
            <XAxis 
              dataKey="burden" 
              tick={{ fontSize: 10 }}
              label={{ value: 'Number of Resistant Classes', position: 'bottom', style: { fontSize: 10 } }} 
            />
            <YAxis 
              tick={{ fontSize: 10 }} 
              label={{ value: 'Number of Isolates', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }} 
            />
            <Tooltip 
              cursor={{ fill: theme.colors.surface.base }}
              contentStyle={{ borderRadius: 4, fontSize: 12, border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}
            />
            
            <ReferenceLine x={2.5} stroke={theme.colors.phenotype.I} strokeDasharray="3 3" label={{ position: 'top', value: 'MDR (≥3)', fill: theme.colors.text.secondary, fontSize: 10 }} />
            <ReferenceLine x={5.5} stroke={theme.colors.phenotype.R} strokeDasharray="3 3" label={{ position: 'top', value: 'XDR (≥6)', fill: theme.colors.text.secondary, fontSize: 10 }} />

            <Bar dataKey="count" fill={theme.colors.categorical[0]} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

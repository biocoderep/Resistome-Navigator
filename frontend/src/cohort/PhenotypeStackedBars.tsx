import React, { useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { usePhenotypePredictions } from '../hooks/useAmrData';
import { theme } from '../theme/tokens';

export default function PhenotypeStackedBars() {
  const { data: phenotypes, loading } = usePhenotypePredictions();

  const chartData = useMemo(() => {
    if (!phenotypes || phenotypes.length === 0) return [];

    // Group by antibiotic
    const drugStats: Record<string, { S: number, I: number, R: number, total: number }> = {};
    
    phenotypes.forEach(p => {
      if (!drugStats[p.antibiotic]) drugStats[p.antibiotic] = { S: 0, I: 0, R: 0, total: 0 };
      drugStats[p.antibiotic][p.predicted_phenotype]++;
      drugStats[p.antibiotic].total++;
    });

    return Object.entries(drugStats)
      .map(([antibiotic, stats]) => ({
        antibiotic,
        S_pct: (stats.S / stats.total) * 100,
        I_pct: (stats.I / stats.total) * 100,
        R_pct: (stats.R / stats.total) * 100,
        total: stats.total
      }))
      .sort((a, b) => b.R_pct - a.R_pct); // sort by highest resistance
  }, [phenotypes]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!chartData || chartData.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No phenotype data.</div>;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Predicted Phenotypes</h3>
        <p className="text-xs text-gray-500">Proportion of S/I/R per antibiotic.</p>
      </div>

      <div className="flex-1 min-h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, bottom: 40, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme.colors.surface.border} />
            <XAxis 
              dataKey="antibiotic" 
              tick={{ fontSize: 10 }} 
              angle={-45} 
              textAnchor="end" 
              interval={0}
            />
            <YAxis 
              domain={[0, 100]} 
              tick={{ fontSize: 10 }} 
              label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }} 
            />
            <Tooltip 
              cursor={{ fill: theme.colors.surface.base }}
              contentStyle={{ borderRadius: 4, fontSize: 12, border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}
              formatter={(val: number) => `${val.toFixed(1)}%`}
            />
            <Legend wrapperStyle={{ fontSize: 10, paddingTop: 20 }} />
            <Bar dataKey="R_pct" name="Resistant (R)" stackId="a" fill={theme.colors.phenotype.R} />
            <Bar dataKey="I_pct" name="Intermediate (I)" stackId="a" fill={theme.colors.phenotype.I} />
            <Bar dataKey="S_pct" name="Susceptible (S)" stackId="a" fill={theme.colors.phenotype.S} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

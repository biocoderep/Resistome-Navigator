import React from 'react';
import { 
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer 
} from 'recharts';
import { useCohortRarefaction } from '../hooks/useAmrData';
import { useDashboardFilters } from './FilterContext';
import { theme } from '../theme/tokens';

export default function ResistomeRarefaction() {
  const { filters } = useDashboardFilters();
  const { data: rarefaction, loading } = useCohortRarefaction(filters);

  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!rarefaction || rarefaction.points.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No rarefaction data.</div>;

  // Recharts needs a combined array for Area (CI band) and Line (Mean).
  // The Area can use an array [low, high] for the y-value to plot a band.
  const chartData = rarefaction.points.map(p => ({
    n: p.n_isolates,
    mean: p.unique_genes_mean,
    ci: [p.ci_low, p.ci_high]
  }));

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Resistome Rarefaction</h3>
        <p className="text-xs text-gray-500">Accumulation of unique resistance determinants as cohort size increases.</p>
      </div>

      <div className="flex-1 min-h-[250px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, bottom: 20, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.surface.border} />
            <XAxis 
              dataKey="n" 
              type="number" 
              domain={['dataMin', 'dataMax']} 
              tick={{ fontSize: 10, fill: theme.colors.text.secondary }}
              label={{ value: 'Number of Isolates Sampled', position: 'bottom', style: { fontSize: 10, fill: theme.colors.text.secondary } }} 
            />
            <YAxis 
              tick={{ fontSize: 10, fill: theme.colors.text.secondary }}
              label={{ value: 'Unique Genes', angle: -90, position: 'insideLeft', style: { fontSize: 10, fill: theme.colors.text.secondary } }} 
            />
            <Tooltip 
              contentStyle={{ borderRadius: 4, fontSize: 12, border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}
              formatter={(value: any, name: string) => {
                if (name === 'ci') return [`${value[0].toFixed(1)} - ${value[1].toFixed(1)}`, '95% CI'];
                return [Number(value).toFixed(1), 'Mean Unique Genes'];
              }}
            />
            {/* Confidence Interval Band */}
            <Area 
              type="monotone" 
              dataKey="ci" 
              stroke="none" 
              fill={theme.colors.confidence.MEDIUM} 
              fillOpacity={0.2} 
            />
            {/* Mean Line */}
            <Line 
              type="monotone" 
              dataKey="mean" 
              stroke={theme.colors.confidence.HIGH} 
              strokeWidth={2} 
              dot={false} 
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

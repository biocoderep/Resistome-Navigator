import React, { useMemo } from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend 
} from 'recharts';
import { usePhenotypePredictions, useCohortMetadata } from '../hooks/useAmrData';
import { useDashboardFilters } from './FilterContext';
import { theme } from '../theme/tokens';

export default function ResistanceTrend() {
  const { filters } = useDashboardFilters();
  const { data: metadata, loading: mLoad } = useCohortMetadata(filters);
  const { data: phenotypes, loading: pLoad } = usePhenotypePredictions();

  const { chartData, hasDates } = useMemo(() => {
    if (!metadata || !phenotypes) return { chartData: [], hasDates: false };

    // Check if we have at least one valid date
    const validDates = metadata.filter(m => m.collection_date);
    if (validDates.length === 0) return { chartData: [], hasDates: false };

    // Map sample to its collection month (YYYY-MM)
    const sampleToMonth: Record<string, string> = {};
    metadata.forEach(m => {
      if (m.collection_date) {
        // Assume ISO YYYY-MM-DD
        sampleToMonth[m.sample_id] = m.collection_date.substring(0, 7);
      }
    });

    // Count resistance burden per sample
    const sampleBurden: Record<string, Set<string>> = {};
    phenotypes.forEach(p => {
      if (!sampleBurden[p.sample_id]) sampleBurden[p.sample_id] = new Set();
      if (p.predicted_phenotype === 'R') {
        sampleBurden[p.sample_id].add(p.antibiotic_class);
      }
    });

    // Group by month
    const monthlyStats: Record<string, { MDR: number, XDR: number, Susceptible: number }> = {};
    
    Object.entries(sampleBurden).forEach(([sampleId, classes]) => {
      const month = sampleToMonth[sampleId];
      if (!month) return; // Skip if no date
      
      if (!monthlyStats[month]) monthlyStats[month] = { MDR: 0, XDR: 0, Susceptible: 0 };
      
      const b = classes.size;
      if (b >= 6) monthlyStats[month].XDR++;
      else if (b >= 3) monthlyStats[month].MDR++;
      else monthlyStats[month].Susceptible++;
    });

    const formattedData = Object.entries(monthlyStats)
      .map(([month, stats]) => ({ month, ...stats }))
      .sort((a, b) => a.month.localeCompare(b.month));

    return { chartData: formattedData, hasDates: true };
  }, [metadata, phenotypes]);

  if (mLoad || pLoad) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!hasDates) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No collection dates available for temporal analysis.</div>;
  if (chartData.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No temporal data available.</div>;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Longitudinal Resistance Trends</h3>
        <p className="text-xs text-gray-500">MDR/XDR prevalence over time.</p>
      </div>

      <div className="flex-1 min-h-[250px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, bottom: 20, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme.colors.surface.border} />
            <XAxis dataKey="month" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip 
              contentStyle={{ borderRadius: 4, fontSize: 12, border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}
            />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            <Area type="monotone" dataKey="XDR" stackId="1" stroke="#8a3800" fill="#8a3800" />
            <Area type="monotone" dataKey="MDR" stackId="1" stroke={theme.colors.phenotype.R} fill={theme.colors.phenotype.R} />
            <Area type="monotone" dataKey="Susceptible" stackId="1" stroke={theme.colors.phenotype.S} fill={theme.colors.phenotype.S} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

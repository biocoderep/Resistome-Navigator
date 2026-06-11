import React, { useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { useVirulenceGenes } from '../../hooks/useAmrData';
import { theme } from '../../theme/tokens';

export default function VirulenceProfile({ sampleId }: { sampleId: string }) {
  const { data: genes, loading } = useVirulenceGenes(sampleId);

  const chartData = useMemo(() => {
    if (!genes || genes.length === 0) return [];
    
    const counts = genes.reduce((acc, curr) => {
      acc[curr.function_category] = (acc[curr.function_category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(counts)
      .map(([category, count]) => ({ category, count }))
      .sort((a, b) => b.count - a.count);
  }, [genes]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!genes || genes.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No virulence factors detected.</div>;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Virulence Factors</h3>
        <p className="text-xs text-gray-500">Distribution of detected pathogenic elements.</p>
      </div>

      <div className="flex-1 min-h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={theme.colors.surface.border} />
            <XAxis 
              dataKey="category" 
              tick={{ fontSize: 10, fill: theme.colors.text.secondary }} 
              axisLine={false} 
              tickLine={false}
              angle={-45}
              textAnchor="end"
            />
            <YAxis 
              tick={{ fontSize: 10, fill: theme.colors.text.secondary }} 
              axisLine={false} 
              tickLine={false}
              allowDecimals={false}
            />
            <Tooltip 
              cursor={{ fill: theme.colors.surface.base }}
              contentStyle={{ borderRadius: 4, fontSize: 12, border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}
            />
            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={theme.colors.categorical[index % theme.colors.categorical.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

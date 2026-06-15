import React, { useMemo } from 'react';
import { 
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Cell 
} from 'recharts';
import { useAmrGenes, useVirulenceGenes } from '../hooks/useAmrData';
import { theme } from '../theme/tokens';

export default function VirulenceVsResistanceScatter() {
  const { data: amrGenes, loading: aLoad } = useAmrGenes();
  const { data: virGenes, loading: vLoad } = useVirulenceGenes();

  const chartData = useMemo(() => {
    if (!amrGenes || !virGenes) return [];

    const amrCounts: Record<string, number> = {};
    const virCounts: Record<string, number> = {};

    amrGenes.forEach(g => amrCounts[g.sample_id] = (amrCounts[g.sample_id] || 0) + 1);
    (virGenes?.genes || []).forEach(g => virCounts[g.sample_id] = (virCounts[g.sample_id] || 0) + 1);

    const samples = Array.from(new Set([...Object.keys(amrCounts), ...Object.keys(virCounts)]));

    return samples.map(id => ({
      sample_id: id,
      amr: amrCounts[id] || 0,
      vir: virCounts[id] || 0
    }));
  }, [amrGenes, virGenes]);

  if (aLoad || vLoad) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!chartData || chartData.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No scatter data.</div>;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Pathogenicity Matrix</h3>
        <p className="text-xs text-gray-500">Virulence vs Resistance determinant count per isolate.</p>
      </div>

      <div className="flex-1 min-h-[250px]">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={theme.colors.surface.border} />
            <XAxis 
              dataKey="amr" type="number" name="AMR Genes" 
              tick={{ fontSize: 10 }}
              label={{ value: 'AMR Determinants', position: 'bottom', style: { fontSize: 10 } }} 
            />
            <YAxis 
              dataKey="vir" type="number" name="Virulence Genes" 
              tick={{ fontSize: 10 }}
              label={{ value: 'Virulence Factors', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }} 
            />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3' }}
              contentStyle={{ borderRadius: 4, fontSize: 12, border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}
              formatter={(val: number, name: string) => [val, name]}
            />
            <Scatter name="Isolates" data={chartData}>
              {chartData.map((entry, index) => {
                // High risk if both are high
                const isHighRisk = entry.amr > 10 && entry.vir > 5;
                return <Cell key={`cell-${index}`} fill={isHighRisk ? theme.colors.phenotype.R : theme.colors.categorical[0]} />;
              })}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

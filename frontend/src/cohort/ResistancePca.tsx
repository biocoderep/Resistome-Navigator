import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { useCohortPca } from '../hooks/useAmrData';
import { useDashboardFilters } from './FilterContext';
import { theme } from '../theme/tokens';

export default function ResistancePca() {
  const { filters } = useDashboardFilters();
  const { data: pcaData, loading } = useCohortPca(filters);

  const traces = useMemo(() => {
    if (!pcaData) return [];

    // Group points by organism to create distinct traces for legend
    const byOrg = pcaData.points.reduce((acc, curr) => {
      if (!acc[curr.organism]) acc[curr.organism] = [];
      acc[curr.organism].push(curr);
      return acc;
    }, {} as Record<string, typeof pcaData.points>);

    const organisms = Object.keys(byOrg).sort();

    return organisms.map((org, i) => ({
      x: byOrg[org].map(p => p.pc1),
      y: byOrg[org].map(p => p.pc2),
      text: byOrg[org].map(p => p.sample_id),
      mode: 'markers',
      type: 'scatter',
      name: org,
      marker: {
        size: 8,
        color: theme.colors.categorical[i % theme.colors.categorical.length],
        line: { width: 1, color: 'white' }
      }
    }));
  }, [pcaData]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!pcaData || pcaData.points.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No PCA data.</div>;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Resistome PCA</h3>
        <p className="text-xs text-gray-500">2D projection of AMR profiles. Colored by organism.</p>
      </div>

      <div className="flex-1 min-h-[300px]">
        <Plot
          data={traces as any}
          layout={{
            margin: { t: 10, r: 10, l: 40, b: 40 },
            xaxis: { title: `PC1 (${pcaData.explainedVariance[0].toFixed(1)}%)`, titlefont: { size: 10 }, tickfont: { size: 10 } },
            yaxis: { title: `PC2 (${pcaData.explainedVariance[1].toFixed(1)}%)`, titlefont: { size: 10 }, tickfont: { size: 10 } },
            legend: { orientation: 'h', y: -0.2, font: { size: 10 } },
            hovermode: 'closest'
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
        />
      </div>
    </div>
  );
}

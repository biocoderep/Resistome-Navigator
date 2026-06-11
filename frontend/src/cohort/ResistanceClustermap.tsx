import React from 'react';
import Plot from 'react-plotly.js';
import { useCohortClustermap } from '../hooks/useAmrData';
import { useDashboardFilters } from './FilterContext';

export default function ResistanceClustermap() {
  const { filters } = useDashboardFilters();
  const { data: clustermap, loading } = useCohortClustermap(filters);

  if (loading) return <div className="animate-pulse h-96 bg-gray-100 rounded-lg w-full"></div>;
  if (!clustermap || clustermap.matrix.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No clustermap data.</div>;

  // Render a basic heatmap. 
  // True dendrogram integration in Plotly requires separate subplot traces for the dendrogram lines (often pre-computed as coordinates).
  // Given we just have linkage matrix in the contract, a production app would run a small JS layout function to draw the dendrogram on a secondary axis.
  // For this mock, we render the clustered heatmap array directly.
  
  const trace = {
    z: clustermap.matrix,
    x: clustermap.colLabels,
    y: clustermap.rowLabels,
    type: 'heatmap',
    colorscale: [
      [0, '#F3F4F6'], // Absent
      [1, '#C62828']  // Present / R
    ],
    showscale: false
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Resistance Clustermap</h3>
        <p className="text-xs text-gray-500">Hierarchical clustering of isolates vs antibiotic classes.</p>
      </div>

      <div className="flex-1 min-h-[300px]">
        <Plot
          data={[trace as any]}
          layout={{
            margin: { t: 10, r: 10, l: 80, b: 80 },
            xaxis: { tickangle: -45, tickfont: { size: 10 } },
            yaxis: { tickfont: { size: 10 } }
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
        />
      </div>
    </div>
  );
}

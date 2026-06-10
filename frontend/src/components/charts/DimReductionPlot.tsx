import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';

const CARBON_COLORS = [
  '#6929c4', '#1192e8', '#005d5d', '#9f1853', '#fa4d56',
  '#570408', '#198038', '#002d9c', '#ee5396', '#b28600',
  '#009d9a', '#012749', '#8a3800', '#a56eff'
];

export default function DimReductionPlot() {
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/v1/analytics/dim-reduction?method=umap')
      .then(res => res.json())
      .then(json => setData(json))
      .catch(err => console.error(err));
  }, []);

  if (!data || !Array.isArray(data) || data.length === 0) return <div className="p-10 text-text-muted text-center">No dimension reduction data available.</div>;

  // Group data by dominant class for Plotly traces
  const groupedData: Record<string, {x: number[], y: number[], z: number[], text: string[]}> = {};
  data.forEach(pt => {
    const cls = pt.dominant_resistance;
    if (!groupedData[cls]) groupedData[cls] = {x: [], y: [], z: [], text: []};
    groupedData[cls].x.push(pt.x);
    groupedData[cls].y.push(pt.y);
    groupedData[cls].z.push(pt.z || 0);
    groupedData[cls].text.push(pt.id);
  });

  const uniqueClasses = Object.keys(groupedData);
  
  const plotData: any[] = uniqueClasses.map((cls, index) => ({
    x: groupedData[cls].x,
    y: groupedData[cls].y,
    z: groupedData[cls].z,
    text: groupedData[cls].text,
    mode: 'markers',
    type: 'scatter3d',
    name: cls,
    marker: {
      size: 6,
      color: CARBON_COLORS[index % CARBON_COLORS.length],
      line: { color: 'white', width: 0.5 },
      opacity: 0.8
    },
    hoverinfo: 'text+name'
  }));

  return (
    <div className="h-[500px] w-full border border-surface-dark rounded-xl overflow-hidden bg-surface-card flex items-center justify-center relative">
      <Plot
        data={plotData}
        layout={{
          autosize: true,
          margin: { l: 0, r: 0, b: 0, t: 0 },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          showlegend: true,
          legend: { x: 0, y: 1, font: { color: '#0F172A', size: 10 } },
          scene: {
            xaxis: { title: 'UMAP 1', showgrid: true, gridcolor: '#E2E8F0', zerolinecolor: '#E2E8F0', tickfont: {color: '#64748B'}, titlefont: {color: '#0F172A'} },
            yaxis: { title: 'UMAP 2', showgrid: true, gridcolor: '#E2E8F0', zerolinecolor: '#E2E8F0', tickfont: {color: '#64748B'}, titlefont: {color: '#0F172A'} },
            zaxis: { title: 'UMAP 3', showgrid: true, gridcolor: '#E2E8F0', zerolinecolor: '#E2E8F0', tickfont: {color: '#64748B'}, titlefont: {color: '#0F172A'} },
            camera: { eye: { x: 1.5, y: 1.5, z: 1.5 } }
          }
        }}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
        config={{ displayModeBar: false }}
      />
    </div>
  );
}

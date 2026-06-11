import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import Graph from 'react-graph-vis';
import "vis-network/styles/vis-network.css";

export default function CohortViews({ batchId }: { batchId?: string }) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!batchId) return;
    
    // In a real app we'd fetch from http://127.0.0.1:8000/api/v1/batches/${batchId}/cohort
    // For demo purposes, we'll try to fetch it, but if it fails we mock the data to show the components
    fetch(`http://127.0.0.1:8000/api/v1/batches/${batchId}/cohort`)
      .then(res => res.json())
      .then(json => {
        if (json.analyses) {
          setData(json.analyses);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [batchId]);

  if (!batchId) {
    return <div className="p-6 text-center text-gray-500">Cohort analytics require a valid Batch ID.</div>;
  }

  if (loading) {
    return <div className="p-6 text-center text-gray-500 animate-pulse">Loading native interactive visualizations...</div>;
  }

  if (!data) {
    return <div className="p-6 text-center text-red-500">Failed to load analytics data.</div>;
  }

  // 1. UMAP Setup
  const umapData = data.resistome_umap || [];
  const trace1 = {
    x: umapData.map((d: any) => d.x),
    y: umapData.map((d: any) => d.y),
    z: umapData.map((d: any) => d.z),
    mode: 'markers',
    marker: {
      size: 5,
      color: umapData.map((d: any) => d.dominant_resistance === 'MDR' ? 'red' : 'green'),
    },
    text: umapData.map((d: any) => `${d.id} - ${d.dominant_resistance}`),
    type: 'scatter3d'
  };

  // 2. Network Setup
  const networkGraph = data.gene_cooccurrence_network || { nodes: [], links: [] };
  const visNetworkData = {
    nodes: networkGraph.nodes.map((n: any) => ({ id: n.id, label: n.name, value: n.val, group: n.group })),
    edges: networkGraph.links.map((l: any) => ({ from: l.source, to: l.target, value: l.value }))
  };
  const visOptions = {
    physics: { stabilization: false, solver: 'forceAtlas2Based' },
    edges: { color: "#64748b" },
    nodes: { shape: "dot" }
  };

  // 3. Barcode Setup
  const barcode = data.population_barcode || { antibiotics: [], isolates: [] };
  const yLabels = barcode.isolates.map((iso: any) => iso.filename);
  const xLabels = barcode.antibiotics;
  
  const heatmapZ = barcode.isolates.map((iso: any) => {
    return barcode.antibiotics.map((ab: string) => {
      const p = iso.profile[ab];
      return p === 'R' ? 1 : p === 'I' ? 0.5 : 0;
    });
  });

  const traceBarcode = {
    z: heatmapZ,
    x: xLabels,
    y: yLabels,
    type: 'heatmap',
    colorscale: [
      [0, '#198038'], // S
      [0.5, '#b28600'], // I
      [1, '#da1e28'] // R
    ]
  };

  return (
    <div className="w-full flex flex-col gap-6 p-6">
      
      {/* 3D UMAP */}
      <div className="bg-white rounded-xl overflow-hidden border border-gray-200 shadow-sm">
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <h3 className="font-bold text-gray-800">Live 3D Resistome UMAP</h3>
        </div>
        <div className="w-full h-[500px]">
          <Plot
            data={[trace1 as any]}
            layout={{ title: '', margin: { l: 0, r: 0, b: 0, t: 0 } }}
            style={{ width: "100%", height: "100%" }}
            useResizeHandler={true}
          />
        </div>
      </div>

      {/* VisNetwork */}
      <div className="bg-white rounded-xl overflow-hidden border border-gray-200 shadow-sm">
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <h3 className="font-bold text-gray-800">Gene Co-occurrence Network</h3>
        </div>
        <div className="w-full h-[500px]">
          <Graph
            graph={visNetworkData}
            options={visOptions}
            events={{}}
            style={{ width: "100%", height: "100%" }}
          />
        </div>
      </div>

      {/* Barcode */}
      <div className="bg-white rounded-xl overflow-hidden border border-gray-200 shadow-sm">
        <div className="p-4 bg-gray-50 border-b border-gray-200">
          <h3 className="font-bold text-gray-800">Population Resistance Barcode</h3>
        </div>
        <div className="w-full h-[600px]">
          <Plot
            data={[traceBarcode as any]}
            layout={{ title: '', margin: { l: 150, r: 50, b: 100, t: 50 } }}
            style={{ width: "100%", height: "100%" }}
            useResizeHandler={true}
          />
        </div>
      </div>

    </div>
  );
}

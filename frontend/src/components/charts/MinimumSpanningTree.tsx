import React, { useEffect, useState, useRef, useCallback } from 'react';
import ForceGraph3D from 'react-force-graph-3d';

const CARBON_COLORS = [
  '#6929c4', '#1192e8', '#005d5d', '#9f1853', '#fa4d56',
  '#570408', '#198038', '#002d9c', '#ee5396', '#b28600',
  '#009d9a', '#012749', '#8a3800', '#a56eff'
];

export default function MinimumSpanningTree() {
  const [data, setData] = useState<any>({ nodes: [], links: [] });
  const fgRef = useRef<any>();

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/v1/analysis/cohort/mst')
      .then(res => res.json())
      .then(json => setData(json))
      .catch(err => console.error(err));
  }, []);

  // Inject strong repulsion physics to de-cluster the network
  useEffect(() => {
    if (fgRef.current) {
      fgRef.current.d3Force('charge').strength(-200);
      fgRef.current.d3Force('link').distance(100);
    }
  }, [data]);

  const uniqueGroups = Array.from(new Set(data.nodes.map((n:any) => n.group)));
  const getColorForClass = (cls: string) => {
    const idx = uniqueGroups.indexOf(cls);
    return CARBON_COLORS[idx % CARBON_COLORS.length];
  };

  const handleNodeClick = useCallback((node: any) => {
    // Zoom in on the clicked node
    const distance = 40;
    const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
    if (fgRef.current) {
      fgRef.current.cameraPosition(
        { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }, // new position
        node, // lookAt
        3000  // ms transition
      );
    }
  }, [fgRef]);

  if (!data.nodes.length) return <div className="p-10 text-text-muted text-center">No network data available.</div>;

  return (
    <div className="h-[500px] w-full border border-surface-dark rounded-xl overflow-hidden bg-surface-card relative flex items-center justify-center">
      <ForceGraph3D
        ref={fgRef}
        graphData={data}
        nodeLabel="id"
        nodeColor={(node: any) => getColorForClass(node.group)}
        nodeRelSize={4}
        nodeVal={(node: any) => node.val}
        linkColor={() => 'rgba(100, 116, 139, 0.4)'}
        linkWidth={(link: any) => Math.max(1, link.value * 3)}
        onNodeClick={handleNodeClick}
        backgroundColor="#FFFFFF"
        showNavInfo={false}
      />
      <div className="absolute top-4 left-4 bg-surface-card/90 p-3 rounded-lg border border-surface-dark shadow-sm text-xs backdrop-blur-sm pointer-events-none">
        <div className="font-bold text-text-primary mb-2">MST Nodes (Resistome)</div>
        {uniqueGroups.map((g: any) => (
          <div key={g} className="flex items-center gap-2 mt-1">
            <div className="w-3 h-3 rounded-full" style={{ background: getColorForClass(g) }} />
            <span className="text-text-muted">{g}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

import React, { useMemo, useEffect, useRef, useState } from 'react';
import { forceSimulation, forceLink, forceManyBody, forceCenter } from 'd3-force';
import { useAmrGenes } from '../hooks/useAmrData';
import { theme } from '../theme/tokens';

export default function GeneCoOccurrence({ width = 400, height = 300 }: { width?: number, height?: number }) {
  const { data: genes, loading } = useAmrGenes();
  const [nodes, setNodes] = useState<any[]>([]);
  const [links, setLinks] = useState<any[]>([]);

  // 1. Build graph structure from data
  useMemo(() => {
    if (!genes || genes.length === 0) return;

    const sampleToGenes: Record<string, string[]> = {};
    genes.forEach(g => {
      if (!sampleToGenes[g.sample_id]) sampleToGenes[g.sample_id] = [];
      sampleToGenes[g.sample_id].push(g.gene_name);
    });

    const edgeWeights: Record<string, number> = {};
    const nodeCounts: Record<string, number> = {};

    Object.values(sampleToGenes).forEach(list => {
      const unique = Array.from(new Set(list)).sort();
      unique.forEach(u => nodeCounts[u] = (nodeCounts[u] || 0) + 1);

      for (let i = 0; i < unique.length; i++) {
        for (let j = i + 1; j < unique.length; j++) {
          const key = `${unique[i]}::${unique[j]}`;
          edgeWeights[key] = (edgeWeights[key] || 0) + 1;
        }
      }
    });

    const newNodes = Object.keys(nodeCounts).map(id => ({ 
      id, 
      radius: Math.max(5, Math.min(15, nodeCounts[id] * 2)) 
    }));
    
    const newLinks = Object.entries(edgeWeights)
      .filter(([_, weight]) => weight > 1) // only significant co-occurrence
      .map(([key, weight]) => {
        const [source, target] = key.split('::');
        return { source, target, value: weight };
      });

    setNodes(newNodes);
    setLinks(newLinks);
  }, [genes]);

  // 2. Run physics simulation
  useEffect(() => {
    if (nodes.length === 0) return;

    const simulation = forceSimulation(nodes)
      .force("link", forceLink(links).id((d: any) => d.id).distance(50))
      .force("charge", forceManyBody().strength(-100))
      .force("center", forceCenter(width / 2, height / 2))
      .on("tick", () => {
        // Trigger re-render to update positions
        setNodes([...simulation.nodes()]);
        setLinks([...links]); // links have their source/target updated to node refs
      });

    return () => {
      simulation.stop();
    };
  }, [nodes.length, width, height]); // Only re-run when graph topology changes

  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!nodes || nodes.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No co-occurrence data.</div>;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Gene Co-Occurrence</h3>
        <p className="text-xs text-gray-500">Force-directed network of genes appearing in the same isolate.</p>
      </div>

      <div className="flex-1 overflow-hidden" style={{ minHeight: height }}>
        <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
          <g>
            {/* Draw Links */}
            {links.map((link, i) => {
              if (typeof link.source !== 'object' || typeof link.target !== 'object') return null;
              return (
                <line
                  key={i}
                  x1={link.source.x}
                  y1={link.source.y}
                  x2={link.target.x}
                  y2={link.target.y}
                  stroke={theme.colors.surface.border}
                  strokeWidth={Math.min(4, link.value)}
                  strokeOpacity={0.6}
                />
              );
            })}
            
            {/* Draw Nodes */}
            {nodes.map(node => (
              <g key={node.id} className="group cursor-pointer">
                <circle
                  cx={node.x || 0}
                  cy={node.y || 0}
                  r={node.radius}
                  fill={theme.colors.categorical[3]}
                  stroke="white"
                  strokeWidth={1.5}
                />
                {/* Node Label (always visible if large, or on hover) */}
                <text
                  x={(node.x || 0) + node.radius + 2}
                  y={(node.y || 0) + 3}
                  className={`text-[9px] font-mono fill-gray-700 ${node.radius < 10 ? 'opacity-0 group-hover:opacity-100' : ''} transition-opacity`}
                >
                  {node.id}
                </text>
              </g>
            ))}
          </g>
        </svg>
      </div>
    </div>
  );
}

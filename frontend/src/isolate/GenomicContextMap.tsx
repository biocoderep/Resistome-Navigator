import React, { useMemo } from 'react';
import { scaleLinear } from '@visx/scale';
import { Group } from '@visx/group';
import { useAmrGenes, useVirulenceGenes } from '../../hooks/useAmrData';
import { theme } from '../../theme/tokens';

export default function GenomicContextMap({ sampleId, width = 800, height = 300 }: { sampleId: string, width?: number, height?: number }) {
  const { data: amrGenes, loading: amrLoad } = useAmrGenes(sampleId);
  const { data: virGenes, loading: virLoad } = useVirulenceGenes(sampleId);

  const { contigs, maxLen } = useMemo(() => {
    if (!amrGenes && !virGenes) return { contigs: {}, maxLen: 0 };
    
    const cmap: Record<string, { amr: typeof amrGenes, vir: typeof virGenes, length: number }> = {};
    let mLen = 0;

    const process = (gene: any, type: 'amr' | 'vir') => {
      if (!cmap[gene.contig_id]) cmap[gene.contig_id] = { amr: [], vir: [], length: 0 };
      cmap[gene.contig_id][type].push(gene as never);
      if (gene.end > cmap[gene.contig_id].length) cmap[gene.contig_id].length = gene.end + 5000; // Add padding
      if (cmap[gene.contig_id].length > mLen) mLen = cmap[gene.contig_id].length;
    };

    (amrGenes || []).forEach(g => process(g, 'amr'));
    (virGenes || []).forEach(g => process(g, 'vir'));

    return { contigs: cmap, maxLen: mLen };
  }, [amrGenes, virGenes]);

  if (amrLoad || virLoad) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (Object.keys(contigs).length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No genomic mapping data.</div>;

  const margin = { top: 20, right: 20, bottom: 20, left: 80 };
  const innerWidth = width - margin.left - margin.right;
  
  const xScale = scaleLinear<number>({
    range: [0, innerWidth],
    domain: [0, maxLen],
  });

  const TRACK_HEIGHT = 40;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 overflow-x-auto h-full flex flex-col">
      <div className="mb-4 shrink-0">
        <h3 className="font-bold text-gray-900 text-sm">Genomic Context Map</h3>
        <p className="text-xs text-gray-500">Linear physical mapping of AMR (Red) and Virulence (Blue) genes across contigs.</p>
      </div>

      <div className="flex-1 overflow-y-auto" style={{ minWidth: width }}>
        <svg width={width} height={Math.max(height - 80, Object.keys(contigs).length * TRACK_HEIGHT + margin.top)}>
          <Group top={margin.top} left={margin.left}>
            {Object.entries(contigs).map(([contigId, data], i) => {
              const y = i * TRACK_HEIGHT;
              
              return (
                <g key={contigId}>
                  <text x={-10} y={y + 10} textAnchor="end" className="text-xs font-mono fill-gray-500">
                    {contigId}
                  </text>
                  
                  {/* Contig Backbone */}
                  <rect 
                    x={0} y={y + 8} 
                    width={xScale(data.length)} height={4} 
                    fill="#E5E7EB" rx={2} 
                  />

                  {/* AMR Genes */}
                  {data.amr.map((g, j) => {
                    const xStart = xScale(g.start);
                    const xW = Math.max(xScale(g.end) - xStart, 4); // min width 4px for visibility
                    return (
                      <g key={`amr-${j}`} className="group">
                        <rect x={xStart} y={y + 4} width={xW} height={12} fill={theme.colors.phenotype.R} />
                        <text x={xStart + xW/2} y={y - 2} textAnchor="middle" className="text-[9px] font-mono fill-red-800 opacity-0 group-hover:opacity-100">{g.gene_name}</text>
                      </g>
                    );
                  })}

                  {/* Virulence Genes */}
                  {data.vir.map((g, j) => {
                    const xStart = xScale(g.start);
                    const xW = Math.max(xScale(g.end) - xStart, 4);
                    return (
                      <g key={`vir-${j}`} className="group">
                        <rect x={xStart} y={y + 4} width={xW} height={12} fill={theme.colors.confidence.MEDIUM} />
                        <text x={xStart + xW/2} y={y + 26} textAnchor="middle" className="text-[9px] font-mono fill-blue-800 opacity-0 group-hover:opacity-100">{g.gene_name}</text>
                      </g>
                    );
                  })}
                </g>
              );
            })}
          </Group>
        </svg>
      </div>
    </div>
  );
}

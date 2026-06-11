import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useAmrGenes } from '../hooks/useAmrData';
import { theme } from '../theme/tokens';

export default function ResistanceGeneUpset() {
  const { data: genes, loading } = useAmrGenes();

  const { intersections, topGenes } = useMemo(() => {
    if (!genes || genes.length === 0) return { intersections: [], topGenes: [] };

    // 1. Get genes per sample
    const sampleGenes: Record<string, string[]> = {};
    const geneCounts: Record<string, number> = {};
    
    genes.forEach(g => {
      if (!sampleGenes[g.sample_id]) sampleGenes[g.sample_id] = [];
      sampleGenes[g.sample_id].push(g.gene_name);
      geneCounts[g.gene_name] = (geneCounts[g.gene_name] || 0) + 1;
    });

    // Pick top 5 genes for the UpSet sets to keep it readable
    const topG = Object.entries(geneCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(e => e[0]);

    // 2. Compute intersections of these top 5 genes
    const intersectionCounts: Record<string, number> = {};
    Object.values(sampleGenes).forEach(list => {
      // Create a signature of which of the top 5 genes are present
      const sig = topG.map(g => list.includes(g) ? '1' : '0').join('');
      if (sig.includes('1')) { // ignore empty sets
        intersectionCounts[sig] = (intersectionCounts[sig] || 0) + 1;
      }
    });

    // 3. Format for charting
    const interArray = Object.entries(intersectionCounts)
      .map(([sig, count]) => ({ sig, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10); // top 10 intersections

    return { intersections: interArray, topGenes: topG };
  }, [genes]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!intersections || intersections.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No upset data.</div>;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4 shrink-0">
        <h3 className="font-bold text-gray-900 text-sm">Resistome UpSet Plot</h3>
        <p className="text-xs text-gray-500">Intersection sizes of the top 5 most prevalent genes.</p>
      </div>

      <div className="flex-1 flex flex-col h-full min-h-[300px]">
        {/* Top Bar Chart (Intersection Sizes) */}
        <div className="h-32 w-full pl-[100px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={intersections}>
              <XAxis dataKey="sig" hide />
              <YAxis tick={{ fontSize: 10 }} width={30} />
              <Tooltip 
                cursor={{ fill: theme.colors.surface.base }}
                contentStyle={{ borderRadius: 4, fontSize: 12, border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}
                formatter={(val: number) => [val, 'Isolates']}
                labelFormatter={() => ''}
              />
              <Bar dataKey="count" fill={theme.colors.categorical[1]} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Matrix */}
        <div className="flex w-full mt-2">
          {/* Gene Labels */}
          <div className="w-[100px] flex flex-col justify-between pt-2 pb-2">
            {topGenes.map(g => (
              <div key={g} className="text-xs font-mono font-bold text-gray-700 text-right pr-2 h-6 flex items-center justify-end">{g}</div>
            ))}
          </div>
          
          {/* Intersection Dots */}
          <div className="flex-1 flex justify-around">
            {intersections.map(inter => (
              <div key={inter.sig} className="flex flex-col justify-between pt-2 pb-2 w-8 items-center relative">
                {/* Draw connection line if multiple dots */}
                {(() => {
                  const firstIdx = inter.sig.indexOf('1');
                  const lastIdx = inter.sig.lastIndexOf('1');
                  if (firstIdx !== -1 && lastIdx !== -1 && firstIdx !== lastIdx) {
                    return (
                      <div 
                        className="absolute w-1 bg-gray-400 z-0" 
                        style={{ top: `${(firstIdx/topGenes.length)*100 + 10}%`, bottom: `${100 - (lastIdx/topGenes.length)*100 - 10}%` }}
                      ></div>
                    );
                  }
                  return null;
                })()}

                {topGenes.map((_, i) => (
                  <div key={i} className="h-6 flex items-center justify-center z-10">
                    <div className={`w-3 h-3 rounded-full ${inter.sig[i] === '1' ? 'bg-gray-800' : 'bg-gray-200'}`}></div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}

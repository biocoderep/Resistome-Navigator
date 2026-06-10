import React, { useMemo } from 'react';

const GENOME_LENGTH = 5400000; // 5.4 Mbp

// RNG for mock data
const rng = ((s) => { let x = s; return () => { x = (x * 16807) % 2147483647; return (x - 1) / 2147483646; }; })(42);

export default function GenomicSummary() {

  // Generate spatial data mapped to 0-360 degrees
  const spatialData = useMemo(() => {
    
    // AMR Genes (Red)
    const amr = Array.from({length: 15}, () => ({
      pos: rng() * GENOME_LENGTH,
      label: 'AMR'
    }));
    
    // Virulence Factors (Purple)
    const virulence = Array.from({length: 25}, () => ({
      pos: rng() * GENOME_LENGTH,
      label: 'VF'
    }));
    
    // Mutations (Orange)
    const mutations = Array.from({length: 10}, () => ({
      pos: rng() * GENOME_LENGTH,
      label: 'MUT'
    }));

    // GC Skew (Blue wave)
    const gc = Array.from({length: 360}, (_, i) => {
      // Create a wavy pattern
      const val = Math.sin(i * Math.PI / 180 * 10) * 15 + Math.sin(i * Math.PI / 180 * 2) * 5;
      return { degree: i, val }; 
    });

    return { amr, virulence, mutations, gc };
  }, []);

  const getCoordinates = (pos: number, radius: number) => {
    const angle = (pos / GENOME_LENGTH) * 360;
    const rad = (angle - 90) * (Math.PI / 180); // Start at top
    const x = Math.cos(rad) * radius;
    const y = Math.sin(rad) * radius;
    return { x, y, angle };
  };

  const getPathForGC = (data: any[], baseRadius: number) => {
    let path = '';
    data.forEach((d, i) => {
      const rad = (d.degree - 90) * (Math.PI / 180);
      const r = baseRadius + d.val;
      const x = Math.cos(rad) * r;
      const y = Math.sin(rad) * r;
      if (i === 0) path += `M ${x} ${y} `;
      else path += `L ${x} ${y} `;
    });
    path += 'Z';
    return path;
  };

  return (
    <div className="p-6 h-full flex flex-col gap-6 items-center">
      
      <div className="text-center max-w-2xl">
        <h3 className="text-xl font-bold text-gray-900 mb-2">Genomic Summary (Circos Map)</h3>
        <p className="text-sm text-gray-500">
          Spatial mapping of all detected determinants against the 5.4 Mbp reference genome.
        </p>
      </div>

      <div className="flex-1 w-full max-w-[600px] aspect-square relative bg-white border border-gray-200 rounded-xl shadow-sm flex items-center justify-center p-8">
        
        <svg viewBox="-250 -250 500 500" className="w-full h-full overflow-visible">
          
          {/* Base Genome Ring */}
          <circle cx="0" cy="0" r="200" fill="none" stroke="#E5E7EB" strokeWidth="20" />
          
          {/* Ticks and Labels for Genome Coordinates */}
          {[0, 1, 2, 3, 4, 5].map(mb => {
            const pos = mb * 1000000;
            const {x, y, angle} = getCoordinates(pos, 220);
            const {x: tx, y: ty} = getCoordinates(pos, 205);
            const {x: bx, y: by} = getCoordinates(pos, 195);
            return (
              <g key={`tick-${mb}`}>
                <line x1={tx} y1={ty} x2={bx} y2={by} stroke="#9CA3AF" strokeWidth="2" />
                <text x={x} y={y} fontSize="10" fill="#6B7280" textAnchor="middle" alignmentBaseline="middle" transform={`rotate(${angle < 180 ? angle : angle + 180}, ${x}, ${y})`}>
                  {mb} Mbp
                </text>
              </g>
            );
          })}

          {/* Ring 1: GC Content (Inner wavy line) */}
          <path d={getPathForGC(spatialData.gc, 160)} fill="none" stroke="#1192e8" strokeWidth="1.5" opacity="0.6" />
          <circle cx="0" cy="0" r="160" fill="none" stroke="#E5E7EB" strokeWidth="1" strokeDasharray="4 4" />

          {/* Ring 2: AMR Genes (Red markers) */}
          {spatialData.amr.map((d, i) => {
            const {x, y} = getCoordinates(d.pos, 180);
            const {x: ix, y: iy} = getCoordinates(d.pos, 175);
            return <line key={`amr-${i}`} x1={x} y1={y} x2={ix} y2={iy} stroke="#da1e28" strokeWidth="3" />;
          })}

          {/* Ring 3: Virulence Factors (Purple markers) */}
          {spatialData.virulence.map((d, i) => {
            const {x, y} = getCoordinates(d.pos, 140);
            const {x: ix, y: iy} = getCoordinates(d.pos, 135);
            return <line key={`vf-${i}`} x1={x} y1={y} x2={ix} y2={iy} stroke="#6929c4" strokeWidth="2" />;
          })}

          {/* Ring 4: Mutations (Orange scatter dots) */}
          {spatialData.mutations.map((d, i) => {
            const {x, y} = getCoordinates(d.pos, 120);
            return <circle key={`mut-${i}`} cx={x} cy={y} r="3" fill="#f1c21b" stroke="#b28600" strokeWidth="1" />;
          })}

        </svg>

        {/* Legend Panel */}
        <div className="absolute bottom-4 right-4 bg-white/90 p-4 rounded-lg shadow-sm border border-gray-200 text-xs backdrop-blur-sm">
          <div className="font-bold text-gray-900 mb-2">Track Legend</div>
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2"><div className="w-4 h-1 bg-[#da1e28]"></div> AMR Genes (Ring 1)</div>
            <div className="flex items-center gap-2"><div className="w-4 h-1 bg-[#6929c4]"></div> Virulence Factors (Ring 3)</div>
            <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-[#f1c21b] border border-[#b28600]"></div> Point Mutations (Ring 4)</div>
            <div className="flex items-center gap-2"><svg className="w-4 h-2"><path d="M0,1 Q2,0 4,1 T8,1" fill="none" stroke="#1192e8"/></svg> GC Skew (Ring 2)</div>
          </div>
        </div>
      </div>

    </div>
  );
}

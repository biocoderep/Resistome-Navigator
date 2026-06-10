import React, { useMemo } from 'react';

const GENES = [
  { name: 'gyrA', length: 875, color: '#457B9D' },
  { name: 'parC', length: 752, color: '#2A9D8F' },
  { name: 'rpoB', length: 1342, color: '#E63946' }
];

export default function Service4Mutation() {

  const mutations = useMemo(() => {
    return [
      { gene: 'gyrA', pos: 83, ref: 'S', alt: 'I', sig: 'HIGH', mech: 'Target alteration', id: 'S83I' },
      { gene: 'gyrA', pos: 87, ref: 'D', alt: 'N', sig: 'HIGH', mech: 'Target alteration', id: 'D87N' },
      { gene: 'parC', pos: 80, ref: 'S', alt: 'I', sig: 'MEDIUM', mech: 'Target alteration', id: 'S80I' },
      { gene: 'parC', pos: 84, ref: 'E', alt: 'K', sig: 'LOW', mech: 'Target alteration', id: 'E84K' },
      { gene: 'rpoB', pos: 526, ref: 'H', alt: 'Y', sig: 'HIGH', mech: 'Target alteration', id: 'H526Y' },
      { gene: 'rpoB', pos: 531, ref: 'S', alt: 'L', sig: 'HIGH', mech: 'Target alteration', id: 'S531L' },
    ];
  }, []);

  const getSigColor = (sig: string) => {
    if (sig === 'HIGH') return '#da1e28';
    if (sig === 'MEDIUM') return '#b28600';
    return '#8a3800';
  };

  return (
    <div className="p-6 h-full flex flex-col gap-6">
      
      {/* Lollipop Plot */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm overflow-x-auto">
        <h3 className="text-sm font-bold text-gray-900 mb-2">Mutation Profiles (Lollipop Map)</h3>
        <p className="text-xs text-gray-500 mb-6">Point mutations mapped to reference gene coordinates. Red indicates HIGH clinical significance.</p>
        
        <div className="flex flex-col gap-8 min-w-[600px] py-4">
          {GENES.map(gene => {
            const geneMuts = mutations.filter(m => m.gene === gene.name);
            return (
              <div key={gene.name} className="relative h-20 w-full flex items-center">
                <div className="w-16 font-mono font-bold text-gray-700 text-sm flex-shrink-0">{gene.name}</div>
                <div className="flex-1 relative h-full flex items-center">
                  
                  {/* Gene Body (Track) */}
                  <div className="absolute w-full h-3 rounded-full bg-gray-100 border border-gray-200"></div>
                  
                  {/* Mutations (Lollipops) */}
                  {geneMuts.map(mut => {
                    const pct = (mut.pos / gene.length) * 100;
                    return (
                      <div key={mut.id} className="absolute h-full flex flex-col items-center justify-end group" style={{left: `${pct}%`, transform: 'translateX(-50%)'}}>
                        {/* Hover Tooltip */}
                        <div className="absolute -top-6 bg-gray-900 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 pointer-events-none">
                          {mut.gene} {mut.ref}{mut.pos}{mut.alt} ({mut.sig})
                        </div>
                        {/* Label */}
                        <div className="text-[10px] font-mono font-bold text-gray-600 mb-1">{mut.ref}{mut.pos}{mut.alt}</div>
                        {/* Stick */}
                        <div className="w-px h-6 bg-gray-400"></div>
                        {/* Head */}
                        <div 
                          className="w-4 h-4 rounded-full border-2 border-white shadow-sm z-10 absolute bottom-[calc(50%-8px)]"
                          style={{backgroundColor: getSigColor(mut.sig)}}
                        ></div>
                      </div>
                    );
                  })}
                  
                  {/* End coordinate */}
                  <div className="absolute right-0 bottom-2 text-[9px] text-gray-400 font-mono">{gene.length}aa</div>
                </div>
              </div>
            );
          })}
        </div>
        
        {/* Legend */}
        <div className="flex gap-4 mt-4 justify-center text-xs text-gray-500 border-t border-gray-100 pt-4">
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-[#da1e28]"></div> HIGH Significance</div>
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-[#b28600]"></div> MEDIUM Significance</div>
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-[#8a3800]"></div> LOW Significance</div>
        </div>
      </div>

      {/* Evidence Table */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex-1 flex flex-col">
        <h3 className="text-sm font-bold text-gray-900 mb-4">Mutation Evidence Log</h3>
        <div className="overflow-auto flex-1">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 text-gray-500 uppercase text-xs font-bold sticky top-0">
              <tr>
                <th className="px-4 py-3 rounded-tl-lg">Gene</th>
                <th className="px-4 py-3">Mutation</th>
                <th className="px-4 py-3">Mechanism</th>
                <th className="px-4 py-3">Clinical Significance</th>
                <th className="px-4 py-3 rounded-tr-lg">Evidence DB</th>
              </tr>
            </thead>
            <tbody>
              {mutations.map((m, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono font-bold text-gray-800">{m.gene}</td>
                  <td className="px-4 py-3 font-mono text-gray-600 bg-gray-100 rounded px-2">{m.ref}{m.pos}{m.alt}</td>
                  <td className="px-4 py-3 text-gray-600">{m.mech}</td>
                  <td className="px-4 py-3">
                    <span 
                      className="px-2 py-1 rounded text-xs font-bold"
                      style={{
                        backgroundColor: m.sig === 'HIGH' ? '#ffe5e5' : m.sig === 'MEDIUM' ? '#fff2cc' : '#f4f4f4',
                        color: m.sig === 'HIGH' ? '#da1e28' : m.sig === 'MEDIUM' ? '#b28600' : '#8a3800'
                      }}
                    >
                      {m.sig}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">POINTFINDER</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}

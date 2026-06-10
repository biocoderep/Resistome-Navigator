import React, { useMemo } from 'react';
import DimReductionPlot from '../charts/DimReductionPlot';
import CoOccurrenceNetwork from '../charts/CoOccurrenceNetwork';
import MinimumSpanningTree from '../charts/MinimumSpanningTree';

const rng = ((s) => { let x = s; return () => { x = (x * 16807) % 2147483647; return (x - 1) / 2147483646; }; })(42);

const ANTIBIOTICS = ['AMP', 'AMC', 'TZP', 'CXM', 'CTX', 'CAZ', 'MEM', 'ETP', 'GEN', 'AMK', 'CIP', 'LVX', 'TGC', 'CST'];
const SIR_COLORS: any = { 'S': '#198038', 'I': '#b28600', 'R': '#da1e28' };

export default function CohortViews() {

  // Barcode data
  const barcodeData = useMemo(() => {
    return Array.from({length: 40}, (_, i) => {
      const row: any = { isolate: `Iso-${i}` };
      // Assign a random phenotype cluster (mostly S, mostly R, or mixed)
      const cluster = rng();
      ANTIBIOTICS.forEach(ab => {
        let probR = 0.2;
        if(cluster > 0.7) probR = 0.8;
        else if(cluster > 0.4) probR = 0.5;
        
        const roll = rng();
        if(roll < probR) row[ab] = 'R';
        else if(roll < probR + 0.1) row[ab] = 'I';
        else row[ab] = 'S';
      });
      return row;
    });
  }, []);

  return (
    <div className="p-6 flex flex-col gap-8">
      
      {/* Resistance Barcode */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm overflow-x-auto">
        <h3 className="text-sm font-bold text-gray-900 mb-2">Population Resistance Barcode</h3>
        <p className="text-xs text-gray-500 mb-4">Rows: Isolates (n={barcodeData.length}). Columns: Antibiotics. Colors: S/I/R prediction.</p>
        
        <div className="min-w-[800px]">
          <div className="flex mb-1">
            <div className="w-16 flex-shrink-0"></div>
            {ANTIBIOTICS.map(ab => (
              <div key={ab} className="flex-1 text-center text-[10px] font-bold text-gray-500 rotate-[-45deg] origin-bottom-left whitespace-nowrap h-8">
                {ab}
              </div>
            ))}
          </div>
          
          <div className="flex flex-col gap-0.5">
            {barcodeData.map(row => (
              <div key={row.isolate} className="flex items-center h-4 hover:opacity-80 cursor-pointer group relative">
                <div className="w-16 flex-shrink-0 text-[10px] font-mono text-gray-500 group-hover:text-gray-900 group-hover:font-bold truncate pr-2">
                  {row.isolate}
                </div>
                {ANTIBIOTICS.map(ab => (
                  <div 
                    key={ab} 
                    className="flex-1 h-full mx-[1px] rounded-sm"
                    style={{backgroundColor: SIR_COLORS[row[ab]]}}
                    title={`${row.isolate} - ${ab}: ${row[ab]}`}
                  ></div>
                ))}
              </div>
            ))}
          </div>
        </div>
        
        {/* Legend */}
        <div className="flex gap-4 mt-6 justify-center text-xs text-gray-500 border-t border-gray-100 pt-4">
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-sm bg-[#198038]"></div> Susceptible (S)</div>
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-sm bg-[#b28600]"></div> Intermediate (I)</div>
          <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-sm bg-[#da1e28]"></div> Resistant (R)</div>
        </div>
      </div>

      {/* 3D Integrations */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-bold text-gray-900 mb-2">Live 3D UMAP</h3>
          <p className="text-xs text-gray-500 mb-4">Non-linear dimensionality reduction of the resistome.</p>
          <DimReductionPlot />
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-bold text-gray-900 mb-2">Gene Co-occurrence Network</h3>
          <p className="text-xs text-gray-500 mb-4">ForceGraph3D interactive physics simulation.</p>
          <CoOccurrenceNetwork />
        </div>
      </div>

    </div>
  );
}

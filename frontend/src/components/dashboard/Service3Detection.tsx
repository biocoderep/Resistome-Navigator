import React, { useState, useMemo } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell, ZAxis, Legend } from 'recharts';

const rng = ((s) => { let x = s; return () => { x = (x * 16807) % 2147483647; return (x - 1) / 2147483646; }; })(42);

const DRUG_COLORS: any = {
  "Beta-lactam": "#E63946", "Aminoglycoside": "#457B9D", "Tetracycline": "#8338EC",
  "Macrolide": "#F4845F", "Fluoroquinolone": "#2A9D8F", "Colistin": "#E9C46A"
};

const DATABASES = ["CARD", "ResFinder", "AMRFinder+", "Abricate"];
const GENES = ["blaNDM-1", "mcr-1", "aac(6')-Ib", "tet(A)", "qnrS1", "sul1", "blaOXA-48", "armA", "blaCTX-M-15", "dfrA12", "catA1", "aph(3')-Ia"];

export default function Service3Detection() {

  // 1. Concordance Heatmap Data
  const heatmapData = useMemo(() => {
    return GENES.map(gene => {
      const row: any = { gene };
      let presentCount = 0;
      DATABASES.forEach(db => {
        // Mock identity score
        const isPresent = rng() > 0.3;
        row[db] = isPresent ? +(85 + rng()*15).toFixed(1) : 0;
        if(isPresent) presentCount++;
      });
      // Force at least one DB to have it so it's a real hit
      if(presentCount === 0) row[DATABASES[Math.floor(rng()*4)]] = 99.9;
      return row;
    });
  }, []);

  const heatColor = (val: number) => {
    if(val === 0) return '#F3F4F6';
    if(val < 90) return '#FEF08A'; // yellow
    if(val < 98) return '#FDBA74'; // orange
    return '#16A34A'; // green
  };

  // 2. Hit Quality Scatter (Identity vs Coverage)
  const scatterData = useMemo(() => {
    const classes = Object.keys(DRUG_COLORS);
    return Array.from({length: 40}, (_, i) => {
      const cls = classes[Math.floor(rng() * classes.length)];
      return {
        id: `Hit-${i}`,
        gene: GENES[i % GENES.length],
        identity: +(80 + rng() * 20).toFixed(1),
        coverage: +(70 + rng() * 30).toFixed(1),
        confidence: +(rng() * 100).toFixed(0),
        drugClass: cls
      };
    });
  }, []);

  return (
    <div className="p-6 h-full flex flex-col gap-6">
      
      {/* Top row: Heatmap + Scatter */}
      <div className="grid grid-cols-2 gap-6 h-96">
        
        {/* Database Concordance Heatmap */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm overflow-hidden flex flex-col">
          <h3 className="text-sm font-bold text-gray-900 mb-2">Database Concordance</h3>
          <p className="text-xs text-gray-500 mb-4">Percent identity across 4 reference databases</p>
          <div className="flex-1 overflow-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr>
                  <th className="pb-2 font-mono text-gray-400">Gene</th>
                  {DATABASES.map(db => <th key={db} className="pb-2 px-1 text-center font-bold text-gray-700">{db}</th>)}
                </tr>
              </thead>
              <tbody>
                {heatmapData.map(row => (
                  <tr key={row.gene} className="border-t border-gray-100">
                    <td className="py-1.5 font-mono font-bold text-gray-800 pr-2">{row.gene}</td>
                    {DATABASES.map(db => (
                      <td key={db} className="p-0.5">
                        <div 
                          className="w-full h-6 rounded flex items-center justify-center text-[10px] font-bold text-gray-800"
                          style={{backgroundColor: heatColor(row[db]), opacity: row[db]===0 ? 0.3 : 1}}
                        >
                          {row[db] > 0 ? `${row[db]}%` : '-'}
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Hit Quality Scatter */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex flex-col">
          <h3 className="text-sm font-bold text-gray-900 mb-2">Hit Quality (QC Scatter)</h3>
          <p className="text-xs text-gray-500 mb-4">Identity vs Coverage. Bubble size = Confidence.</p>
          <div className="flex-1 relative">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="coverage" type="number" domain={[60, 100]} name="Coverage %" stroke="#9CA3AF" tick={{fontSize: 10}} label={{ value: 'Coverage (%)', position: 'bottom', offset: 0, style: {fontSize: 12, fill: '#6B7280'} }} />
                <YAxis dataKey="identity" type="number" domain={[70, 100]} name="Identity %" stroke="#9CA3AF" tick={{fontSize: 10}} label={{ value: 'Identity (%)', angle: -90, position: 'insideLeft', style: {fontSize: 12, fill: '#6B7280'} }} />
                <ZAxis dataKey="confidence" type="number" range={[20, 200]} />
                <RechartsTooltip cursor={{strokeDasharray: '3 3'}} content={({active, payload}) => {
                  if(active && payload && payload.length) {
                    const d = payload[0].payload;
                    return (
                      <div className="bg-gray-900 text-white p-3 rounded-lg text-xs shadow-xl">
                        <div className="font-bold font-mono text-blue-300">{d.gene}</div>
                        <div>Identity: {d.identity}%</div>
                        <div>Coverage: {d.coverage}%</div>
                        <div>Confidence: {d.confidence}%</div>
                        <div className="mt-1 flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full" style={{background: DRUG_COLORS[d.drugClass]}}></span>
                          {d.drugClass}
                        </div>
                      </div>
                    )
                  }
                  return null;
                }} />
                {Object.keys(DRUG_COLORS).map(cls => (
                  <Scatter key={cls} name={cls} data={scatterData.filter(d => d.drugClass === cls)} fill={DRUG_COLORS[cls]}>
                    {scatterData.filter(d => d.drugClass === cls).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={DRUG_COLORS[cls]} fillOpacity={0.7} stroke={DRUG_COLORS[cls]} strokeWidth={1} />
                    ))}
                  </Scatter>
                ))}
              </ScatterChart>
            </ResponsiveContainer>
            {/* Danger Zone Overlay */}
            <div className="absolute left-[30px] bottom-[30px] w-[120px] h-[80px] border-2 border-dashed border-red-400 bg-red-400/10 pointer-events-none rounded flex items-end p-2">
              <span className="text-red-600 text-[10px] font-bold">Low Confidence Zone</span>
            </div>
          </div>
        </div>

      </div>

      {/* Bottom row: Table */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex-1 flex flex-col min-h-[300px]">
        <h3 className="text-sm font-bold text-gray-900 mb-4">AMR Gene Inventory</h3>
        <div className="overflow-auto flex-1">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 text-gray-500 uppercase text-xs font-bold sticky top-0">
              <tr>
                <th className="px-4 py-3 rounded-tl-lg">Gene</th>
                <th className="px-4 py-3">Drug Class</th>
                <th className="px-4 py-3">Mechanism</th>
                <th className="px-4 py-3">Best DB Source</th>
                <th className="px-4 py-3 rounded-tr-lg">Detection Confidence</th>
              </tr>
            </thead>
            <tbody>
              {scatterData.slice(0, 8).map((hit, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono font-bold text-gray-800">{hit.gene}</td>
                  <td className="px-4 py-3 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full" style={{background: DRUG_COLORS[hit.drugClass]}}></span>
                    {hit.drugClass}
                  </td>
                  <td className="px-4 py-3 text-gray-600">Antibiotic inactivation</td>
                  <td className="px-4 py-3">
                    <span className="px-2 py-1 bg-blue-50 text-blue-600 rounded text-xs font-bold">{DATABASES[i % 4]}</span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-yellow-400 to-green-500" style={{width: `${hit.confidence}%`}}></div>
                    </div>
                    <div className="text-xs text-right mt-1 text-gray-500">{hit.confidence}%</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}

import React, { useMemo } from 'react';
import { ResponsiveContainer, Sankey, Tooltip as RechartsTooltip } from 'recharts';

export default function Service6Phenotype() {

  // Phenotype Data
  const antibiogram = [
    { drug: 'Ampicillin', cls: 'Beta-lactam', sir: 'R', conf: 99.8, ev: ['blaNDM-1'] },
    { drug: 'Meropenem', cls: 'Carbapenem', sir: 'R', conf: 98.5, ev: ['blaNDM-1'] },
    { drug: 'Ciprofloxacin', cls: 'Fluoroquinolone', sir: 'R', conf: 95.2, ev: ['gyrA (S83I)'] },
    { drug: 'Tetracycline', cls: 'Tetracycline', sir: 'R', conf: 92.1, ev: ['tet(A)'] },
    { drug: 'Colistin', cls: 'Polymyxin', sir: 'R', conf: 88.0, ev: ['mcr-1'] },
    { drug: 'Gentamicin', cls: 'Aminoglycoside', sir: 'S', conf: 94.0, ev: [] },
    { drug: 'Amikacin', cls: 'Aminoglycoside', sir: 'I', conf: 76.5, ev: ['aac(6\')-Ib (Partial)'] },
  ];

  const counts = {
    R: antibiogram.filter(d => d.sir === 'R').length,
    I: antibiogram.filter(d => d.sir === 'I').length,
    S: antibiogram.filter(d => d.sir === 'S').length,
    Total: antibiogram.length
  };

  const getColorSIR = (sir: string) => {
    if (sir === 'R') return '#da1e28'; // Red
    if (sir === 'I') return '#b28600'; // Yellow
    return '#198038'; // Green
  };

  // Sankey Data: Gene -> Drug -> S/I/R
  const sankeyData = useMemo(() => {
    return {
      nodes: [
        // Determinants
        { name: "blaNDM-1" }, { name: "gyrA (S83I)" }, { name: "tet(A)" }, { name: "mcr-1" },
        // Drugs
        { name: "Ampicillin" }, { name: "Meropenem" }, { name: "Ciprofloxacin" }, { name: "Tetracycline" }, { name: "Colistin" },
        // Outcomes
        { name: "Resistant (R)" }
      ],
      links: [
        { source: 0, target: 4, value: 5 },
        { source: 0, target: 5, value: 5 },
        { source: 1, target: 6, value: 5 },
        { source: 2, target: 7, value: 5 },
        { source: 3, target: 8, value: 5 },
        
        { source: 4, target: 9, value: 5 },
        { source: 5, target: 9, value: 5 },
        { source: 6, target: 9, value: 5 },
        { source: 7, target: 9, value: 5 },
        { source: 8, target: 9, value: 5 },
      ]
    };
  }, []);

  return (
    <div className="p-6 h-full flex flex-col gap-6">
      
      {/* Resistance Summary Strip */}
      <div className="grid grid-cols-4 gap-6">
        <div className="bg-white border-b-4 border-[#da1e28] rounded-xl p-5 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Resistant (R)</div>
            <div className="text-3xl font-bold text-gray-900">{counts.R}</div>
          </div>
          <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center text-red-600 font-bold">R</div>
        </div>
        <div className="bg-white border-b-4 border-[#b28600] rounded-xl p-5 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Intermediate (I)</div>
            <div className="text-3xl font-bold text-gray-900">{counts.I}</div>
          </div>
          <div className="w-12 h-12 rounded-full bg-yellow-50 flex items-center justify-center text-yellow-600 font-bold">I</div>
        </div>
        <div className="bg-white border-b-4 border-[#198038] rounded-xl p-5 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Susceptible (S)</div>
            <div className="text-3xl font-bold text-gray-900">{counts.S}</div>
          </div>
          <div className="w-12 h-12 rounded-full bg-green-50 flex items-center justify-center text-green-600 font-bold">S</div>
        </div>
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-5 shadow-sm flex items-center justify-between text-white">
          <div>
            <div className="text-xs text-gray-400 font-bold uppercase tracking-wider mb-1">Drugs Tested</div>
            <div className="text-3xl font-bold">{counts.Total}</div>
          </div>
          <div className="w-12 h-12 rounded-full bg-gray-700 flex items-center justify-center font-bold">∑</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6 flex-1 min-h-[400px]">
        
        {/* Antibiogram Table */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex flex-col">
          <h3 className="text-sm font-bold text-gray-900 mb-4">Predicted Antibiogram</h3>
          <div className="overflow-auto flex-1">
            <table className="w-full text-sm text-left">
              <thead className="bg-gray-50 text-gray-500 uppercase text-xs font-bold sticky top-0 z-10">
                <tr>
                  <th className="px-4 py-3 rounded-tl-lg">Antibiotic</th>
                  <th className="px-4 py-3 text-center">Prediction</th>
                  <th className="px-4 py-3">Confidence</th>
                  <th className="px-4 py-3 rounded-tr-lg">Primary Evidence</th>
                </tr>
              </thead>
              <tbody>
                {antibiogram.map((row, i) => (
                  <tr key={i} className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer">
                    <td className="px-4 py-3">
                      <div className="font-bold text-gray-800">{row.drug}</div>
                      <div className="text-[10px] text-gray-500 font-mono">{row.cls}</div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span 
                        className="inline-flex w-6 h-6 items-center justify-center rounded-sm font-bold text-white shadow-sm"
                        style={{backgroundColor: getColorSIR(row.sir)}}
                      >
                        {row.sir}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full" style={{width: `${row.conf}%`, backgroundColor: getColorSIR(row.sir)}}></div>
                      </div>
                      <div className="text-xs text-right mt-1 text-gray-500">{row.conf.toFixed(1)}%</div>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-600">
                      {row.ev.length > 0 ? row.ev.join(', ') : 'None detected'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Evidence Flow Sankey */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex flex-col">
          <h3 className="text-sm font-bold text-gray-900 mb-2">Evidence Flow Graph</h3>
          <p className="text-xs text-gray-500 mb-4">Tracing causality from genetic determinant to final phenotype.</p>
          <div className="flex-1 -mx-4">
            <ResponsiveContainer width="100%" height="100%">
              <Sankey
                data={sankeyData}
                nodePadding={20}
                nodeWidth={10}
                link={{ stroke: '#da1e28', strokeOpacity: 0.2 }}
                margin={{ top: 20, right: 80, bottom: 20, left: 40 }}
              >
                <RechartsTooltip />
              </Sankey>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}

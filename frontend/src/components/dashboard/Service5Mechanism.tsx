import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, Tooltip as RechartsTooltip, ResponsiveContainer, Legend, Sankey } from 'recharts';

const MECH_COLORS: any = {
  "Antibiotic inactivation": "#E63946", 
  "Efflux pump": "#457B9D", 
  "Target alteration": "#8338EC",
  "Target protection": "#F4845F", 
  "Reduced permeability": "#E9C46A"
};

export default function Service5Mechanism() {

  // Donut Chart Data
  const donutData = useMemo(() => {
    return Object.keys(MECH_COLORS).map(mech => ({
      name: mech,
      value: Math.floor(Math.random() * 20) + 5
    }));
  }, []);

  // Sankey Data: Gene -> Mechanism -> Drug Class
  // Recharts Sankey requires nodes and links arrays
  const sankeyData = useMemo(() => {
    return {
      nodes: [
        // Genes (0-3)
        { name: "blaNDM-1" }, { name: "tet(A)" }, { name: "gyrA (S83I)" }, { name: "mcr-1" },
        // Mechanisms (4-6)
        { name: "Antibiotic inactivation" }, { name: "Efflux pump" }, { name: "Target alteration" },
        // Drugs (7-9)
        { name: "Beta-lactam" }, { name: "Tetracycline" }, { name: "Fluoroquinolone" }
      ],
      links: [
        { source: 0, target: 4, value: 10 },
        { source: 1, target: 5, value: 5 },
        { source: 2, target: 6, value: 8 },
        { source: 3, target: 6, value: 4 },
        
        { source: 4, target: 7, value: 10 },
        { source: 5, target: 8, value: 5 },
        { source: 6, target: 9, value: 8 },
        { source: 6, target: 7, value: 4 }, // mcr-1 is colistin but just mapping to demo
      ]
    };
  }, []);

  return (
    <div className="p-6 h-full flex flex-col gap-6">
      
      <div className="grid grid-cols-3 gap-6 h-96">
        
        {/* Donut Chart */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm col-span-1 flex flex-col">
          <h3 className="text-sm font-bold text-gray-900 mb-2">Mechanism Composition</h3>
          <p className="text-xs text-gray-500 mb-4">Proportional breakdown of resistance mechanisms</p>
          <div className="flex-1 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie 
                  data={donutData} 
                  innerRadius={60} 
                  outerRadius={90} 
                  dataKey="value" 
                  paddingAngle={2}
                >
                  {donutData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={MECH_COLORS[entry.name]} />
                  ))}
                </Pie>
                <RechartsTooltip contentStyle={{borderRadius: 8, fontSize: 12, border: 'none', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)'}} />
                <Legend layout="horizontal" verticalAlign="bottom" align="center" wrapperStyle={{fontSize: 10}} />
              </PieChart>
            </ResponsiveContainer>
            {/* Center Text */}
            <div className="absolute inset-0 flex flex-col items-center justify-center -mt-8 pointer-events-none">
              <span className="text-2xl font-bold text-gray-900">
                {donutData.reduce((acc, curr) => acc + curr.value, 0)}
              </span>
              <span className="text-[10px] text-gray-500">Determinants</span>
            </div>
          </div>
        </div>

        {/* Sankey Flow */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm col-span-2 flex flex-col">
          <h3 className="text-sm font-bold text-gray-900 mb-2">Explainability Flow (Sankey)</h3>
          <p className="text-xs text-gray-500 mb-4">Tracing the path from determinant (gene/mutation) to mechanism to drug class.</p>
          <div className="flex-1 -mx-4">
            <ResponsiveContainer width="100%" height="100%">
              <Sankey
                data={sankeyData}
                nodePadding={30}
                nodeWidth={10}
                link={{ stroke: '#CBD5E1' }}
                margin={{ top: 20, right: 40, bottom: 20, left: 40 }}
              >
                <RechartsTooltip />
              </Sankey>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* Mechanism Rules Engine Table */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex-1 flex flex-col min-h-[300px]">
        <h3 className="text-sm font-bold text-gray-900 mb-4">Mechanism Ontology Log</h3>
        <div className="overflow-auto flex-1">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 text-gray-500 uppercase text-xs font-bold sticky top-0">
              <tr>
                <th className="px-4 py-3 rounded-tl-lg">Determinant</th>
                <th className="px-4 py-3">Mechanism Type</th>
                <th className="px-4 py-3">Sub-mechanism (Ontology)</th>
                <th className="px-4 py-3 rounded-tr-lg">Affected Classes</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-100 hover:bg-gray-50">
                <td className="px-4 py-3 font-mono font-bold text-gray-800">blaNDM-1</td>
                <td className="px-4 py-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{background: MECH_COLORS['Antibiotic inactivation']}}></span>
                  Antibiotic inactivation
                </td>
                <td className="px-4 py-3 text-gray-600">Metallo-beta-lactamase (MBL)</td>
                <td className="px-4 py-3 font-mono text-xs">Beta-lactam, Carbapenem</td>
              </tr>
              <tr className="border-b border-gray-100 hover:bg-gray-50">
                <td className="px-4 py-3 font-mono font-bold text-gray-800">gyrA (S83I)</td>
                <td className="px-4 py-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{background: MECH_COLORS['Target alteration']}}></span>
                  Target alteration
                </td>
                <td className="px-4 py-3 text-gray-600">DNA gyrase subunit A mutation</td>
                <td className="px-4 py-3 font-mono text-xs">Fluoroquinolone</td>
              </tr>
              <tr className="border-b border-gray-100 hover:bg-gray-50">
                <td className="px-4 py-3 font-mono font-bold text-gray-800">tet(A)</td>
                <td className="px-4 py-3 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{background: MECH_COLORS['Efflux pump']}}></span>
                  Efflux pump
                </td>
                <td className="px-4 py-3 text-gray-600">Major facilitator superfamily (MFS)</td>
                <td className="px-4 py-3 font-mono text-xs">Tetracycline</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}

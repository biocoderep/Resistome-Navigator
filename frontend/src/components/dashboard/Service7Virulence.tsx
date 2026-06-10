import React, { useMemo } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell, ZAxis, BarChart, Bar, Legend } from 'recharts';

const rng = ((s) => { let x = s; return () => { x = (x * 16807) % 2147483647; return (x - 1) / 2147483646; }; })(77);

const VIRULENCE_CATEGORIES: any = {
  "Toxin": "#da1e28",
  "Adhesin": "#005d5d",
  "Invasion": "#8a3800",
  "Immune evasion": "#1192e8",
  "Siderophore": "#6929c4",
  "Secretion system": "#b28600",
  "Capsule": "#ee5396",
  "Biofilm": "#198038"
};

const VF_NAMES = ["ybtA", "iroN", "rmpA", "magA", "fimH", "mrkD", "entB", "iutA", "kfuA", "clbA"];

export default function Service7Virulence() {

  const data = useMemo(() => {
    const cats = Object.keys(VIRULENCE_CATEGORIES);
    return Array.from({length: 30}, (_, i) => {
      const cat = cats[Math.floor(rng() * cats.length)];
      return {
        id: `VF-${i}`,
        gene: VF_NAMES[i % VF_NAMES.length],
        category: cat,
        identity: +(80 + rng() * 20).toFixed(1),
        coverage: +(60 + rng() * 40).toFixed(1),
        confidence: +(rng() * 100).toFixed(0)
      };
    });
  }, []);

  const barData = useMemo(() => {
    const counts: any = {};
    Object.keys(VIRULENCE_CATEGORIES).forEach(c => counts[c] = 0);
    data.forEach(d => counts[d.category]++);
    return Object.keys(counts).map(c => ({ category: c, count: counts[c] })).sort((a,b) => b.count - a.count);
  }, [data]);

  return (
    <div className="p-6 h-full flex flex-col gap-6">
      
      <div className="grid grid-cols-3 gap-6 h-[450px]">
        
        {/* Virulence Bubble Plot */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm col-span-2 flex flex-col">
          <h3 className="text-sm font-bold text-gray-900 mb-2">Virulence Factor Detection</h3>
          <p className="text-xs text-gray-500 mb-4">Identity vs Coverage. Bubble size = Detection Confidence.</p>
          <div className="flex-1 relative">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="coverage" type="number" domain={[50, 100]} name="Coverage %" stroke="#9CA3AF" tick={{fontSize: 10}} label={{ value: 'Coverage (%)', position: 'bottom', offset: 0, style: {fontSize: 12, fill: '#6B7280'} }} />
                <YAxis dataKey="identity" type="number" domain={[70, 100]} name="Identity %" stroke="#9CA3AF" tick={{fontSize: 10}} label={{ value: 'Identity (%)', angle: -90, position: 'insideLeft', style: {fontSize: 12, fill: '#6B7280'} }} />
                <ZAxis dataKey="confidence" type="number" range={[50, 400]} />
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
                          <span className="w-2 h-2 rounded-full" style={{background: VIRULENCE_CATEGORIES[d.category]}}></span>
                          {d.category}
                        </div>
                      </div>
                    )
                  }
                  return null;
                }} />
                {Object.keys(VIRULENCE_CATEGORIES).map(cat => (
                  <Scatter key={cat} name={cat} data={data.filter(d => d.category === cat)} fill={VIRULENCE_CATEGORIES[cat]}>
                    {data.filter(d => d.category === cat).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={VIRULENCE_CATEGORIES[cat]} fillOpacity={0.7} stroke={VIRULENCE_CATEGORIES[cat]} strokeWidth={1} />
                    ))}
                  </Scatter>
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Bar Chart */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm col-span-1 flex flex-col">
          <h3 className="text-sm font-bold text-gray-900 mb-2">Category Breakdown</h3>
          <p className="text-xs text-gray-500 mb-4">Total VFs detected per functional class</p>
          <div className="flex-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 40 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E5E7EB" />
                <XAxis type="number" tick={{fontSize: 10}} stroke="#9CA3AF" />
                <YAxis dataKey="category" type="category" tick={{fontSize: 10, fill: '#4B5563'}} width={80} />
                <RechartsTooltip cursor={{fill: '#F3F4F6'}} contentStyle={{borderRadius: 8, fontSize: 12}} />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {barData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={VIRULENCE_CATEGORIES[entry.category]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* VF Table */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex-1 flex flex-col min-h-[250px]">
        <h3 className="text-sm font-bold text-gray-900 mb-4">Pathogenicity Profile</h3>
        <div className="overflow-auto flex-1">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 text-gray-500 uppercase text-xs font-bold sticky top-0">
              <tr>
                <th className="px-4 py-3 rounded-tl-lg">Gene</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Identity %</th>
                <th className="px-4 py-3">Coverage %</th>
                <th className="px-4 py-3 rounded-tr-lg">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {data.slice(0, 6).map((vf, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono font-bold text-gray-800">{vf.gene}</td>
                  <td className="px-4 py-3 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full" style={{background: VIRULENCE_CATEGORIES[vf.category]}}></span>
                    {vf.category}
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-600">{vf.identity}%</td>
                  <td className="px-4 py-3 font-mono text-gray-600">{vf.coverage}%</td>
                  <td className="px-4 py-3">
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500" style={{width: `${vf.confidence}%`}}></div>
                    </div>
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

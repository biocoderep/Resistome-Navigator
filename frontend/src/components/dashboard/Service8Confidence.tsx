import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Legend } from 'recharts';

export default function Service8Confidence() {

  // Waterfall/Stacked Bar Data
  const waterfallData = useMemo(() => {
    return [
      { id: 'blaNDM-1', alignment: 20, concordance: 20, clinical: 25, mutation: 0, rule: 30, total: 95 },
      { id: 'tet(A)', alignment: 18, concordance: 15, clinical: 20, mutation: 0, rule: 25, total: 78 },
      { id: 'gyrA (S83I)', alignment: 20, concordance: 20, clinical: 25, mutation: 25, rule: 0, total: 90 },
      { id: 'mcr-1', alignment: 15, concordance: 10, clinical: 15, mutation: 0, rule: 20, total: 60 },
      { id: 'qnrS1', alignment: 8, concordance: 5, clinical: 10, mutation: 0, rule: 10, total: 33 },
    ];
  }, []);

  const getTierColor = (score: number) => {
    if (score >= 80) return '#198038'; // HIGH
    if (score >= 60) return '#b28600'; // MEDIUM
    if (score >= 40) return '#f1c21b'; // LOW
    return '#da1e28'; // INSUFFICIENT
  };

  const getTierName = (score: number) => {
    if (score >= 80) return 'HIGH';
    if (score >= 60) return 'MEDIUM';
    if (score >= 40) return 'LOW';
    return 'INSUFFICIENT';
  };

  return (
    <div className="p-6 h-full flex flex-col gap-6">
      
      {/* 5-Dimension Scoring Breakdown */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm min-h-[400px] flex flex-col">
        <h3 className="text-sm font-bold text-gray-900 mb-2">Confidence Dimensional Analysis</h3>
        <p className="text-xs text-gray-500 mb-4">Contribution of the 5 heuristic dimensions to the composite confidence score.</p>
        
        <div className="flex-1 min-h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={waterfallData} layout="vertical" margin={{ top: 20, right: 30, left: 40, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E5E7EB" />
              <XAxis type="number" domain={[0, 100]} tick={{fontSize: 10}} stroke="#9CA3AF" />
              <YAxis dataKey="id" type="category" tick={{fontSize: 12, fontFamily: 'monospace', fontWeight: 'bold', fill: '#374151'}} width={100} />
              <RechartsTooltip contentStyle={{borderRadius: 8, fontSize: 12}} />
              <Legend wrapperStyle={{fontSize: 11, paddingTop: 10}} />
              
              <Bar dataKey="alignment" name="Alignment Quality" stackId="a" fill="#005d5d" />
              <Bar dataKey="concordance" name="DB Concordance" stackId="a" fill="#1192e8" />
              <Bar dataKey="clinical" name="Clinical Evidence" stackId="a" fill="#6929c4" />
              <Bar dataKey="mutation" name="Mutation Confidence" stackId="a" fill="#ee5396" />
              <Bar dataKey="rule" name="Phenotype Rule Strength" stackId="a" fill="#b28600" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Tiers Distribution Table */}
      <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex-1 flex flex-col">
        <h3 className="text-sm font-bold text-gray-900 mb-4">Finding Confidence Tiers</h3>
        <div className="overflow-auto flex-1">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 text-gray-500 uppercase text-xs font-bold sticky top-0">
              <tr>
                <th className="px-4 py-3 rounded-tl-lg">Determinant</th>
                <th className="px-4 py-3">Total Score</th>
                <th className="px-4 py-3">Confidence Tier</th>
                <th className="px-4 py-3 rounded-tr-lg">Action</th>
              </tr>
            </thead>
            <tbody>
              {waterfallData.map((d, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono font-bold text-gray-800">{d.id}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full" style={{width: `${d.total}%`, backgroundColor: getTierColor(d.total)}}></div>
                      </div>
                      <span className="font-mono text-gray-600">{d.total}/100</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span 
                      className="px-2 py-1 rounded text-xs font-bold text-white"
                      style={{backgroundColor: getTierColor(d.total)}}
                    >
                      {getTierName(d.total)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {d.total < 40 ? 'Requires manual review' : 'Auto-approved for report'}
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

import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter, Cell, PieChart, Pie, Legend } from 'recharts';

// Seeded RNG for consistent mock data
const rng = ((s) => { let x = s; return () => { x = (x * 16807) % 2147483647; return (x - 1) / 2147483646; }; })(123);

export default function Service1Validation() {
  
  // 1. Contig Length Distribution Data (Histogram)
  const contigData = useMemo(() => {
    const bins = Array.from({length: 20}, (_, i) => ({
      range: `${i*10}-${(i+1)*10}kbp`,
      count: Math.floor(Math.exp(-(i-5)*(i-5)/20) * 100 + rng()*10)
    }));
    return bins;
  }, []);

  // 2. GC Content Data (Donut)
  const gcData = [
    { name: 'Observed GC', value: 57.2, fill: '#005d5d' },
    { name: 'Expected Range', value: 42.8, fill: '#E2E8F0' }
  ];

  // 3. N50 Scatterplot Data
  const scatterData = useMemo(() => {
    return Array.from({length: 40}, (_, i) => {
      const len = 4.5 + rng() * 1.5; // Total length in Mbp
      const n50 = len * 20000 + rng() * 50000; // N50 roughly correlated
      const status = n50 < 80000 ? 'fail' : n50 < 150000 ? 'warn' : 'pass';
      return { id: `Iso-${i}`, length: +len.toFixed(2), n50: +n50.toFixed(0), status };
    });
  }, []);

  const getStatusColor = (status: string) => {
    if(status === 'pass') return '#198038'; // Green
    if(status === 'warn') return '#b28600'; // Yellow
    return '#da1e28'; // Red
  };

  return (
    <div className="p-6 h-full flex flex-col gap-6">
      
      {/* QC Gate Banner */}
      <div className="bg-white border-l-4 border-[#198038] rounded-xl p-5 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-[#198038] animate-pulse"></div>
            QC Gate Passed
          </h2>
          <p className="text-sm text-gray-500 mt-1">Isolate KP-001 meets all quality thresholds for downstream AMR detection.</p>
        </div>
        <div className="flex gap-4">
          <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 text-center min-w-[100px]">
            <div className="text-xs text-gray-500 font-bold uppercase tracking-wider">Total Length</div>
            <div className="text-lg font-bold text-gray-900">5.4 Mbp</div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 text-center min-w-[100px]">
            <div className="text-xs text-gray-500 font-bold uppercase tracking-wider">Contigs</div>
            <div className="text-lg font-bold text-gray-900">84</div>
          </div>
          <div className="bg-gray-50 p-3 rounded-lg border border-gray-100 text-center min-w-[100px]">
            <div className="text-xs text-gray-500 font-bold uppercase tracking-wider">N50</div>
            <div className="text-lg font-bold text-gray-900">214.5 kbp</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6 flex-1">
        
        {/* Contig Histogram */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h3 className="text-sm font-bold text-gray-900 mb-4">Contig Length Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={contigData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                <XAxis dataKey="range" tick={{fontSize: 10}} interval={2} stroke="#9CA3AF" />
                <YAxis tick={{fontSize: 10}} stroke="#9CA3AF" />
                <Tooltip cursor={{fill: '#F3F4F6'}} contentStyle={{borderRadius: 8, border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'}} />
                <Bar dataKey="count" fill="#1192e8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* GC Gauge */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm relative">
          <h3 className="text-sm font-bold text-gray-900 mb-4">GC Content Match</h3>
          <div className="h-64 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={gcData} innerRadius={80} outerRadius={110} dataKey="value" startAngle={180} endAngle={0} stroke="none">
                  {gcData.map((entry, index) => <Cell key={`cell-${index}`} fill={entry.fill} />)}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pt-16 pointer-events-none">
              <span className="text-4xl font-bold text-gray-900">57.2%</span>
              <span className="text-xs text-gray-500">Expected: 56.5 - 58.0%</span>
            </div>
          </div>
        </div>

        {/* N50 Scatter */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm col-span-2">
          <h3 className="text-sm font-bold text-gray-900 mb-4">Batch Assembly Quality (N50 vs Length)</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="length" type="number" domain={[4, 6]} name="Total Length (Mbp)" stroke="#9CA3AF" tick={{fontSize: 10}} label={{ value: 'Total Assembly Length (Mbp)', position: 'bottom', offset: 0, style: {fontSize: 12, fill: '#6B7280'} }} />
                <YAxis dataKey="n50" type="number" name="N50 (bp)" stroke="#9CA3AF" tick={{fontSize: 10}} label={{ value: 'N50 (bp)', angle: -90, position: 'insideLeft', style: {fontSize: 12, fill: '#6B7280'} }} />
                <Tooltip cursor={{strokeDasharray: '3 3'}} contentStyle={{borderRadius: 8, border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'}} />
                <Scatter name="Assemblies" data={scatterData}>
                  {scatterData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getStatusColor(entry.status)} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          {/* Threshold Legend */}
          <div className="flex gap-4 mt-2 justify-center text-xs text-gray-500">
            <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-[#198038]"></div> Pass (N50 {'>'} 150k)</div>
            <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-[#b28600]"></div> Warn (N50 80k-150k)</div>
            <div className="flex items-center gap-1"><div className="w-3 h-3 rounded-full bg-[#da1e28]"></div> Fail (N50 {'<'} 80k)</div>
          </div>
        </div>

      </div>
    </div>
  );
}

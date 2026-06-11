import React, { useMemo } from 'react';
import { 
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend
} from 'recharts';
import { useMechanismClassifications } from '../../hooks/useAmrData';
import { theme } from '../../theme/tokens';

export default function MechanismBreakdown() {
  const { data: mechanisms, loading } = useMechanismClassifications();

  const chartData = useMemo(() => {
    if (!mechanisms) return [];
    
    const counts = mechanisms.reduce((acc, curr) => {
      acc[curr.mechanism_type] = (acc[curr.mechanism_type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return Object.entries(counts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);
  }, [mechanisms]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!mechanisms || mechanisms.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No mechanism data available.</div>;

  const COLORS = theme.colors.categorical;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Mechanism Breakdown</h3>
        <p className="text-xs text-gray-500">Distribution of predicted resistance mechanisms.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-64">
        
        {/* Donut Chart */}
        <div className="relative h-full flex flex-col items-center">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                innerRadius="60%"
                outerRadius="90%"
                paddingAngle={2}
                dataKey="value"
                stroke="none"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ borderRadius: 4, fontSize: 12, border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none mt-4">
            <span className="text-2xl font-bold text-gray-900">{mechanisms.length}</span>
            <span className="text-[10px] text-gray-500 uppercase tracking-widest">Total</span>
          </div>
        </div>

        {/* Bar Chart */}
        <div className="h-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ top: 10, right: 20, bottom: 0, left: 100 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke={theme.colors.surface.border} />
              <XAxis type="number" hide />
              <YAxis 
                dataKey="name" 
                type="category" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 10, fill: theme.colors.text.secondary }} 
                width={90}
              />
              <Tooltip 
                cursor={{ fill: theme.colors.surface.base }}
                contentStyle={{ borderRadius: 4, fontSize: 12, border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

      </div>
    </div>
  );
}

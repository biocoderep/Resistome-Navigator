import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useAmrGenes, useIsolateMetadata } from '../hooks/useAmrData';
import { theme } from '../theme/tokens';

export default function OrganismStratifiedPanels() {
  const { data: genes, loading: gl } = useAmrGenes();
  // We need metadata to know which sample belongs to which organism
  const { data: metaData } = { data: [] }; // In a real app we'd fetch all metadata here or pass it down

  // For this mock, the genes don't carry organism info, so we use a pre-calculated mock payload or join them
  // To keep it simple, I'll mock the aggregation since the useAmrData hook doesn't currently join metadata
  const chartData = useMemo(() => {
    const orgs = ['E. coli', 'K. pneumoniae', 'P. aeruginosa', 'A. baumannii'];
    const mechs = ['antibiotic_inactivation', 'target_alteration', 'efflux_pump'];
    
    return orgs.map(org => {
      const data = mechs.map(mech => ({
        mech: mech.replace('_', ' '),
        count: Math.floor(Math.random() * 50) + 10
      }));
      return { org, data };
    });
  }, []);

  if (gl) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Organism Stratification</h3>
        <p className="text-xs text-gray-500">Mechanism prevalence across major pathogens.</p>
      </div>

      <div className="flex-1 grid grid-cols-2 gap-4">
        {chartData.map((panel, i) => (
          <div key={panel.org} className="border border-gray-100 rounded p-2">
            <div className="text-xs font-bold text-gray-700 mb-2">{panel.org}</div>
            <div className="h-24">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={panel.data} layout="vertical" margin={{ top: 0, right: 10, bottom: 0, left: 0 }}>
                  <XAxis type="number" hide />
                  <YAxis dataKey="mech" type="category" hide />
                  <Tooltip 
                    cursor={{ fill: theme.colors.surface.base }}
                    contentStyle={{ borderRadius: 4, fontSize: 10, border: 'none', padding: 4 }}
                    formatter={(val: number) => [val, 'Count']}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                    {panel.data.map((_, j) => (
                      <Cell key={`cell-${j}`} fill={theme.colors.categorical[i % theme.colors.categorical.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            {/* Custom Y-axis labels over the bars to save space */}
            <div className="flex flex-col justify-around h-24 -mt-24 pointer-events-none">
              {panel.data.map(d => (
                <div key={d.mech} className="text-[9px] text-gray-900 ml-1 drop-shadow-md font-medium truncate w-full">{d.mech}</div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

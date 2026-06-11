import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { useCohortMetadata, usePhenotypePredictions } from '../hooks/useAmrData';
import { useDashboardFilters } from './FilterContext';
import { theme } from '../theme/tokens';

// Simplistic map mapping region names to generic ISO-3 codes for Plotly
const REGION_MAP: Record<string, string> = {
  'North America': 'USA',
  'Europe': 'FRA',
  'Asia': 'CHN',
  'South America': 'BRA'
};

export default function PrevalenceChoropleth() {
  const { filters } = useDashboardFilters();
  const { data: metadata, loading: mLoad } = useCohortMetadata(filters);
  const { data: phenotypes, loading: pLoad } = usePhenotypePredictions();

  const { chartData, hasRegions } = useMemo(() => {
    if (!metadata || !phenotypes) return { chartData: [], hasRegions: false };

    // Check if we have at least one valid region
    const validRegions = metadata.filter(m => m.region);
    if (validRegions.length === 0) return { chartData: [], hasRegions: false };

    // Map sample to region
    const sampleToRegion: Record<string, string> = {};
    metadata.forEach(m => {
      if (m.region) {
        sampleToRegion[m.sample_id] = m.region;
      }
    });

    // Count resistance burden per sample
    const sampleBurden: Record<string, Set<string>> = {};
    phenotypes.forEach(p => {
      if (!sampleBurden[p.sample_id]) sampleBurden[p.sample_id] = new Set();
      if (p.predicted_phenotype === 'R') {
        sampleBurden[p.sample_id].add(p.antibiotic_class);
      }
    });

    // Group by region
    const regionStats: Record<string, { total: number, mdr: number }> = {};
    
    Object.entries(sampleBurden).forEach(([sampleId, classes]) => {
      const region = sampleToRegion[sampleId];
      if (!region) return; // Skip if no region
      
      if (!regionStats[region]) regionStats[region] = { total: 0, mdr: 0 };
      
      regionStats[region].total++;
      if (classes.size >= 3) {
        regionStats[region].mdr++;
      }
    });

    const formattedData = Object.entries(regionStats)
      .map(([region, stats]) => ({ 
        loc: REGION_MAP[region] || region, // fallback to raw
        regionName: region,
        val: (stats.mdr / stats.total) * 100 
      }));

    return { chartData: formattedData, hasRegions: true };
  }, [metadata, phenotypes]);

  if (mLoad || pLoad) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!hasRegions) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No geographic metadata available.</div>;
  if (chartData.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No prevalence data for mapped regions.</div>;

  const trace = {
    type: 'choropleth',
    locations: chartData.map(d => d.loc),
    z: chartData.map(d => d.val),
    text: chartData.map(d => `${d.regionName}: ${d.val.toFixed(1)}% MDR`),
    colorscale: [
      [0, '#F3F4F6'],
      [1, theme.colors.phenotype.R]
    ],
    showscale: true,
    marker: { line: { color: 'white', width: 0.5 } },
    colorbar: { title: 'MDR %', tickfont: { size: 10 }, titlefont: { size: 10 } }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Global Prevalence</h3>
        <p className="text-xs text-gray-500">MDR isolation rates by region.</p>
      </div>

      <div className="flex-1 min-h-[300px]">
        <Plot
          data={[trace as any]}
          layout={{
            margin: { t: 0, r: 0, l: 0, b: 0 },
            geo: {
              showframe: false,
              showcoastlines: true,
              coastlinecolor: theme.colors.surface.border,
              projection: { type: 'natural earth' }
            }
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
        />
      </div>
    </div>
  );
}

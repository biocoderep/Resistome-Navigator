import React from 'react';
import { useAssemblyMetrics } from '../../hooks/useAmrData';
import { theme } from '../../theme/tokens';

export default function AssemblyQcPanel({ sampleId }: { sampleId: string }) {
  const { data: metricsArray, loading } = useAssemblyMetrics(sampleId);

  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!metricsArray || metricsArray.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No assembly metrics available.</div>;

  const metrics = metricsArray[0];

  const getStatusColor = (val: number, good: number, warn: number, type: 'higherIsBetter' | 'lowerIsBetter') => {
    if (type === 'higherIsBetter') {
      if (val >= good) return theme.colors.phenotype.S; // Green
      if (val >= warn) return theme.colors.phenotype.I; // Yellow
      return theme.colors.phenotype.R; // Red
    } else {
      if (val <= good) return theme.colors.phenotype.S; // Green
      if (val <= warn) return theme.colors.phenotype.I; // Yellow
      return theme.colors.phenotype.R; // Red
    }
  };

  const n50Color = getStatusColor(metrics.n50, 100000, 50000, 'higherIsBetter');
  const contigColor = getStatusColor(metrics.contig_count, 100, 300, 'lowerIsBetter');
  
  // Formatters
  const formatLength = (bp: number) => (bp / 1000000).toFixed(2) + ' Mbp';
  const formatN50 = (bp: number) => (bp / 1000).toFixed(1) + ' kbp';

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Assembly Quality Metrics</h3>
        <p className="text-xs text-gray-500">Predicted Species: <span className="font-bold text-gray-700">{metrics.species_prediction}</span></p>
      </div>

      <div className="grid grid-cols-2 gap-4 flex-1">
        
        {/* N50 Metric */}
        <div className="p-3 bg-gray-50 rounded-lg border border-gray-100 flex flex-col justify-center items-center text-center">
          <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">N50 Length</div>
          <div className="text-2xl font-bold" style={{ color: n50Color }}>{formatN50(metrics.n50)}</div>
          <div className="text-[10px] text-gray-400 mt-1">Expected > 100kbp</div>
        </div>

        {/* Contig Count Metric */}
        <div className="p-3 bg-gray-50 rounded-lg border border-gray-100 flex flex-col justify-center items-center text-center">
          <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Contig Count</div>
          <div className="text-2xl font-bold" style={{ color: contigColor }}>{metrics.contig_count}</div>
          <div className="text-[10px] text-gray-400 mt-1">Expected {'<'} 100</div>
        </div>

        {/* Total Length Metric */}
        <div className="p-3 bg-gray-50 rounded-lg border border-gray-100 flex flex-col justify-center items-center text-center">
          <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">Total Size</div>
          <div className="text-2xl font-bold text-gray-800">{formatLength(metrics.total_length)}</div>
          <div className="text-[10px] text-gray-400 mt-1">Expected 4.5 - 6.0 Mbp</div>
        </div>

        {/* GC % Metric */}
        <div className="p-3 bg-gray-50 rounded-lg border border-gray-100 flex flex-col justify-center items-center text-center">
          <div className="text-xs text-gray-500 font-bold uppercase tracking-wider mb-1">GC Content</div>
          <div className="text-2xl font-bold text-gray-800">{metrics.gc_pct.toFixed(1)}%</div>
          <div className="text-[10px] text-gray-400 mt-1">Expected ~50%</div>
        </div>

      </div>
    </div>
  );
}

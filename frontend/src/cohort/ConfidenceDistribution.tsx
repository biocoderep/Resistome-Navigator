import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { useConfidenceScores } from '../hooks/useAmrData';
import { theme } from '../theme/tokens';

export default function ConfidenceDistribution() {
  const { data: scores, loading } = useConfidenceScores();

  const traces = useMemo(() => {
    if (!scores || scores.length === 0) return [];

    // We'll plot the overall_confidence distribution
    return [{
      type: 'violin',
      y: scores.map(s => s.overall_confidence),
      box: { visible: true },
      line: { color: theme.colors.categorical[5] },
      meanline: { visible: true },
      x0: 'Overall Confidence'
    }];
  }, [scores]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!scores || scores.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No confidence data.</div>;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-4">
        <h3 className="font-bold text-gray-900 text-sm">Prediction Confidence</h3>
        <p className="text-xs text-gray-500">Distribution of confidence scores across the cohort.</p>
      </div>

      <div className="flex-1 min-h-[250px]">
        <Plot
          data={traces as any}
          layout={{
            margin: { t: 10, r: 10, l: 40, b: 20 },
            yaxis: { title: 'Confidence Score', tickfont: { size: 10 }, titlefont: { size: 10 }, range: [0, 100] }
          }}
          useResizeHandler={true}
          style={{ width: "100%", height: "100%" }}
        />
      </div>
    </div>
  );
}

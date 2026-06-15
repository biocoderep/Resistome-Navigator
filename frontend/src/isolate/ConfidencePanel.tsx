import React, { useMemo } from 'react';
import { 
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, 
  ResponsiveContainer, Tooltip 
} from 'recharts';
import { useConfidenceScores } from '../hooks/useAmrData';
import { theme } from '../theme/tokens';

export default function ConfidencePanel({ sampleId }: { sampleId: string }) {
  const { data: scores, loading } = useConfidenceScores(sampleId);

  // We'll aggregate the dimension scores across all findings for a summary radar
  const radarData = useMemo(() => {
    if (!scores || scores.length === 0) return [];
    
    // Average each dimension
    const sums = {
      alignment: 0,
      concordance: 0,
      clinical: 0,
      mutation: 0,
      phenotype: 0
    };

    scores.forEach(s => {
      sums.alignment += s.dimension_scores.alignment_quality;
      sums.concordance += s.dimension_scores.database_concordance;
      sums.clinical += s.dimension_scores.clinical_evidence_weight;
      sums.mutation += s.dimension_scores.mutation_catalogue_confidence;
      sums.phenotype += s.dimension_scores.phenotype_rule_strength;
    });

    const n = scores.length;
    return [
      { subject: 'Alignment Quality', A: sums.alignment / n, fullMark: 100 },
      { subject: 'DB Concordance', A: sums.concordance / n, fullMark: 100 },
      { subject: 'Clinical Evidence', A: sums.clinical / n, fullMark: 100 },
      { subject: 'Mutation Confidence', A: sums.mutation / n, fullMark: 100 },
      { subject: 'Phenotype Rules', A: sums.phenotype / n, fullMark: 100 },
    ];
  }, [scores]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg w-full"></div>;
  if (!scores || scores.length === 0) return <div className="text-gray-400 text-sm p-4 border border-dashed rounded-lg">No confidence data.</div>;

  const avgOverall = scores.reduce((sum, s) => sum + s.overall_confidence, 0) / scores.length;
  
  let overallTierColor = theme.colors.confidence.INSUFFICIENT;
  if (avgOverall >= 90) overallTierColor = theme.colors.confidence.HIGH;
  else if (avgOverall >= 70) overallTierColor = theme.colors.confidence.MEDIUM;
  else if (avgOverall >= 40) overallTierColor = theme.colors.confidence.LOW;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-full flex flex-col">
      <div className="mb-2">
        <h3 className="font-bold text-gray-900 text-sm">Prediction Confidence</h3>
        <p className="text-xs text-gray-500">Multidimensional evidence scoring.</p>
      </div>

      <div className="flex-1 flex items-center justify-center relative min-h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
            <PolarGrid stroke={theme.colors.surface.border} />
            <PolarAngleAxis dataKey="subject" tick={{ fill: theme.colors.text.secondary, fontSize: 10 }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 8 }} />
            <Radar
              name="Avg Confidence"
              dataKey="A"
              stroke={overallTierColor}
              fill={overallTierColor}
              fillOpacity={0.4}
            />
            <Tooltip contentStyle={{ borderRadius: 4, fontSize: 12, border: 'none', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }} />
          </RadarChart>
        </ResponsiveContainer>
        
        {/* Center Score */}
        <div className="absolute top-2 right-2 text-right">
          <div className="text-2xl font-bold" style={{ color: overallTierColor }}>
            {Math.round(avgOverall)}%
          </div>
          <div className="text-[10px] text-gray-500 font-bold uppercase">Overall</div>
        </div>
      </div>
    </div>
  );
}

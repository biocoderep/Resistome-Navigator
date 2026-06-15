import React from 'react';
import type {} from '../types/amr';
import { usePhenotypePredictions } from '../hooks/useAmrData';
import { theme } from '../theme/tokens';

/**
 * AntibiogramStrip
 * Source: PhenotypePrediction table
 * Renders a grid of S/I/R phenotypes for a single isolate, grouped by antibiotic class.
 */
interface Props {
  sampleId: string;
}

export default function AntibiogramStrip({ sampleId }: Props) {
  const { data: phenotypes, loading } = usePhenotypePredictions(sampleId);

  if (loading) return <div className="animate-pulse h-24 bg-gray-100 rounded-lg w-full"></div>;
  if (!phenotypes || phenotypes.length === 0) return <div className="text-gray-400 text-sm p-4 text-center border border-dashed rounded-lg">No phenotype data available for this isolate.</div>;

  // Group by class
  const byClass = phenotypes.reduce((acc, curr) => {
    if (!acc[curr.antibiotic_class]) acc[curr.antibiotic_class] = [];
    acc[curr.antibiotic_class].push(curr);
    return acc;
  }, {} as Record<string, PhenotypePrediction[]>);

  const getPhenotypeColor = (phenotype: string) => {
    if (phenotype === 'S') return theme.colors.phenotype.S;
    if (phenotype === 'I') return theme.colors.phenotype.I;
    if (phenotype === 'R') return theme.colors.phenotype.R;
    return '#E5E7EB';
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="font-bold text-gray-900 text-sm">Clinical Antibiogram</h3>
          <p className="text-xs text-gray-500">Predicted phenotype profile</p>
        </div>
        {phenotypes.length > 0 && (
          <span className="bg-blue-50 text-blue-700 text-[10px] font-bold px-2 py-1 rounded">
            {phenotypes[0].breakpoint_source}
          </span>
        )}
      </div>

      <div className="flex flex-col gap-4">
        {Object.entries(byClass).map(([className, drugs]) => (
          <div key={className}>
            <div className="text-xs font-bold text-gray-400 uppercase mb-2">{className}</div>
            <div className="flex flex-wrap gap-2">
              {drugs.map(drug => (
                <div 
                  key={drug.antibiotic} 
                  className="relative group border border-gray-200 rounded flex items-stretch min-w-[120px] overflow-hidden cursor-default"
                >
                  <div 
                    className="w-8 flex items-center justify-center font-bold text-white text-xs"
                    style={{ backgroundColor: getPhenotypeColor(drug.predicted_phenotype) }}
                  >
                    {drug.predicted_phenotype}
                  </div>
                  <div className="px-3 py-1.5 flex-1 bg-gray-50 text-xs font-medium text-gray-700 flex items-center">
                    {drug.antibiotic}
                  </div>
                  
                  {/* Tooltip */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 bg-gray-900 text-white text-xs p-2 rounded opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10 shadow-xl pointer-events-none">
                    <div className="font-bold border-b border-gray-700 pb-1 mb-1">{drug.antibiotic}</div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-gray-400">Phenotype:</span>
                      <span className="font-bold" style={{ color: getPhenotypeColor(drug.predicted_phenotype) }}>{drug.predicted_phenotype}</span>
                    </div>
                    {drug.supporting_genes.length > 0 && (
                      <div className="mb-1 text-gray-300">
                        <span className="text-gray-400">Drivers:</span> {drug.supporting_genes.join(', ')}
                      </div>
                    )}
                    <div className="text-[10px] text-gray-500 italic mt-1">{drug.interpretation_notes}</div>
                    
                    {/* Arrow */}
                    <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

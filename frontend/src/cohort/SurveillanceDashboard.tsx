import React from 'react';
import { FilterProvider, useDashboardFilters } from './FilterContext';
import ResistanceClustermap from './ResistanceClustermap';
import AmrPrevalenceBars from './AmrPrevalenceBars';
import PhenotypeStackedBars from './PhenotypeStackedBars';
import ResistanceBurdenHistogram from './ResistanceBurdenHistogram';
import GeneCoOccurrence from './GeneCoOccurrence';
import ResistanceGeneUpset from './ResistanceGeneUpset';
import OrganismStratifiedPanels from './OrganismStratifiedPanels';
import ResistanceTrend from './ResistanceTrend';
import PrevalenceChoropleth from './PrevalenceChoropleth';
import ResistancePca from './ResistancePca';
import VirulenceVsResistanceScatter from './VirulenceVsResistanceScatter';
import ConfidenceDistribution from './ConfidenceDistribution';
import ResistomeRarefaction from './ResistomeRarefaction';

function DashboardGrid() {
  const { filters } = useDashboardFilters(); // Just reading them to trigger re-renders if needed

  return (
    <div className="bg-gray-50 min-h-screen p-6 font-sans">
      <div className="max-w-[1600px] mx-auto flex flex-col gap-6">
        
        {/* Header */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AMR Surveillance Cohort</h1>
            <p className="text-sm text-gray-500 mt-1">Multi-isolate analytics and population tracking</p>
          </div>
          <div className="bg-indigo-50 text-indigo-700 px-4 py-2 rounded-lg font-bold text-sm border border-indigo-100">
            50 Isolates Selected
          </div>
        </div>

        {/* Row 1: Flagship Clustering & Prevalance */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ResistanceClustermap />
          </div>
          <div className="lg:col-span-1">
            <AmrPrevalenceBars />
          </div>
        </div>

        {/* Row 2: Phenotypes & Burden */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PhenotypeStackedBars />
          <ResistanceBurdenHistogram />
        </div>

        {/* Row 3: Gene Networks & Upset */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ResistanceGeneUpset />
          <GeneCoOccurrence width={600} height={400} />
        </div>

        {/* Row 4: Stratification & Trends */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <OrganismStratifiedPanels />
          <ResistanceTrend />
        </div>

        {/* Row 5: Geography & PCA */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PrevalenceChoropleth />
          <ResistancePca />
        </div>

        {/* Row 6: Scatter, Confidence & Rarefaction */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <VirulenceVsResistanceScatter />
          <ConfidenceDistribution />
          <ResistomeRarefaction />
        </div>

      </div>
    </div>
  );
}

export default function SurveillanceDashboard() {
  return (
    <FilterProvider>
      <DashboardGrid />
    </FilterProvider>
  );
}

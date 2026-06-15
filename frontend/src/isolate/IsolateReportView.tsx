import React from 'react';
import AntibiogramStrip from './AntibiogramStrip';
import AmrGeneInventory from './AmrGeneInventory';
import MechanismBreakdown from './MechanismBreakdown';
import GenomicContextMap from './GenomicContextMap';
import MutationLollipop from './MutationLollipop';
import ConfidencePanel from './ConfidencePanel';
import VirulenceProfile from './VirulenceProfile';
import AssemblyQcPanel from './AssemblyQcPanel';
import DrugClassCoverageMatrix from './DrugClassCoverageMatrix';
import { useIsolateMetadata } from '../hooks/useAmrData';

export default function IsolateReportView({ sampleId }: { sampleId: string }) {
  const { data: meta, loading } = useIsolateMetadata(sampleId);

  if (loading) return <div className="p-8 text-center animate-pulse text-gray-500">Loading isolate profile...</div>;
  if (!meta) return <div className="p-8 text-center text-red-500">Isolate not found.</div>;

  return (
    <div className="bg-gray-50 min-h-screen p-6 font-sans">
      <div className="max-w-[1400px] mx-auto flex flex-col gap-6">
        
        {/* Header */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{meta.isolate_name}</h1>
            <div className="text-sm text-gray-500 mt-1 flex gap-4">
              <span>Organism: <span className="font-bold text-gray-700">{meta.organism || 'Unknown'}</span></span>
              <span>Sample ID: <span className="font-mono">{meta.sample_id}</span></span>
              <span>Date: {meta.collection_date || 'N/A'}</span>
            </div>
          </div>
          <div className="bg-blue-50 text-blue-700 px-4 py-2 rounded-lg font-bold text-sm border border-blue-100">
            Clinical Isolate Report
          </div>
        </div>

        {/* Row 1: Phenotypes & Assembly QC */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <AntibiogramStrip sampleId={sampleId} />
          </div>
          <div className="lg:col-span-1">
            <AssemblyQcPanel sampleId={sampleId} />
          </div>
        </div>

        {/* Row 2: Resistome Inventory & Confidence */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <AmrGeneInventory sampleId={sampleId} />
          </div>
          <div className="lg:col-span-1">
            <ConfidencePanel sampleId={sampleId} />
          </div>
        </div>

        {/* Row 3: Mechanism Breakdown & Virulence */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <MechanismBreakdown />
          <VirulenceProfile sampleId={sampleId} />
        </div>

        {/* Row 4: Genomic Context */}
        <div className="w-full">
          <GenomicContextMap sampleId={sampleId} width={1200} height={250} />
        </div>

        {/* Row 5: Mutation Profiling */}
        <div className="w-full">
          <MutationLollipop sampleId={sampleId} width={1200} height={300} />
        </div>

        {/* Row 6: Cross-mapping */}
        <div className="w-full">
          <DrugClassCoverageMatrix sampleId={sampleId} />
        </div>

      </div>
    </div>
  );
}

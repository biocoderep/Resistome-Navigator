import React from 'react';

import { useIsolateMetadata } from './hooks/useAmrData';
import { ExportCard } from './components/ExportCard';

import AntibiogramStrip from './isolate/AntibiogramStrip';
import AssemblyQcPanel from './isolate/AssemblyQcPanel';
import AmrGeneInventory from './isolate/AmrGeneInventory';
import ConfidencePanel from './isolate/ConfidencePanel';
import MechanismBreakdown from './isolate/MechanismBreakdown';
import VirulenceProfile from './isolate/VirulenceProfile';
import MutationLollipop from './isolate/MutationLollipop';
import DrugClassCoverageMatrix from './isolate/DrugClassCoverageMatrix';
import IdentityCoverageScatter from './isolate/IdentityCoverageScatter';
import CircularGenomeViewer from './isolate/CircularGenomeViewer';

/**
 * Single-isolate deep-dive dashboard. Clean, light, clinical/research theme.
 * Every chart/table is wrapped in ExportCard for SVG / PNG@300dpi / PDF export.
 */
export default function TBioDashboard({ sampleId }: { sampleId: string }) {
  const { data: meta, loading } = useIsolateMetadata(sampleId);

  if (loading) {
    return <div className="p-10 text-center text-text-muted animate-pulse">Loading isolate profile…</div>;
  }

  return (
    <div className="bg-surface min-h-screen p-6 font-sans">
      <div className="max-w-[1400px] mx-auto flex flex-col gap-6">
        {/* Header */}
        <div className="bg-surface-card rounded-2xl shadow-sm border border-surface-dark p-6 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">{meta?.isolate_name || 'Isolate'}</h1>
            <div className="text-sm text-text-muted mt-1 flex flex-wrap gap-4">
              <span>Organism: <span className="font-semibold text-text-primary">{meta?.organism || 'Unknown'}</span></span>
              <span>Sample ID: <span className="font-mono">{meta?.sample_id || sampleId}</span></span>
              <span>Date: {meta?.collection_date || 'N/A'}</span>
            </div>
          </div>
          <div className="bg-accent-teal/10 text-accent-teal px-4 py-2 rounded-lg font-bold text-sm border border-accent-teal/20">
            Single Isolate Report
          </div>
        </div>

        {/* Phenotypes + Assembly QC */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ExportCard title="Predicted Antibiogram" filename="antibiogram" variant="overlay">
              <AntibiogramStrip sampleId={sampleId} />
            </ExportCard>
          </div>
          <div className="lg:col-span-1">
            <ExportCard title="Assembly QC" filename="assembly_qc" variant="overlay">
              <AssemblyQcPanel sampleId={sampleId} />
            </ExportCard>
          </div>
        </div>

        {/* Required single-isolate visualizations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ExportCard title="Gene Confidence — Identity vs Coverage" filename="identity_coverage"
                      subtitle="Point size ∝ confidence; guides at 95% identity / 80% coverage">
            <IdentityCoverageScatter sampleId={sampleId} />
          </ExportCard>
          <ExportCard title="Circular Genome Map" filename="circular_genome"
                      subtitle="Contigs, AMR genes (outer) and virulence genes (inner)">
            <CircularGenomeViewer sampleId={sampleId} />
          </ExportCard>
        </div>

        {/* Resistome inventory + confidence */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ExportCard title="AMR Gene Inventory" filename="amr_genes" variant="overlay">
              <AmrGeneInventory sampleId={sampleId} />
            </ExportCard>
          </div>
          <div className="lg:col-span-1">
            <ExportCard title="Confidence" filename="confidence" variant="overlay">
              <ConfidencePanel sampleId={sampleId} />
            </ExportCard>
          </div>
        </div>

        {/* Mechanism + virulence */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ExportCard title="Mechanism Breakdown" filename="mechanisms" variant="overlay">
            <MechanismBreakdown />
          </ExportCard>
          <ExportCard title="Virulence Profile" filename="virulence" variant="overlay">
            <VirulenceProfile sampleId={sampleId} />
          </ExportCard>
        </div>

        {/* Mutations */}
        <ExportCard title="Resistance Mutations" filename="mutations" variant="overlay">
          <MutationLollipop sampleId={sampleId} width={1200} height={300} />
        </ExportCard>

        {/* Drug-class cross mapping */}
        <ExportCard title="Drug-Class Coverage" filename="drug_class_matrix" variant="overlay">
          <DrugClassCoverageMatrix sampleId={sampleId} />
        </ExportCard>
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { 
  SampleMetadata, AmrGene, ResistanceMutation, MechanismClassification,
  PhenotypePrediction, VirulenceGene, ConfidenceScore, AssemblyMetrics,
  ClustermapPayload, PcaPayload, RarefactionPayload
} from '../types/amr';

import {
  mockSampleMetadata, mockAmrGenes, mockMutations, mockMechanismClassifications,
  mockPhenotypes, mockVirulenceGenes, mockConfidenceScores, mockAssemblyMetrics,
  mockClustermapPayload, mockPcaPayload, mockRarefactionPayload
} from '../mockData';

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

// Helper for fetching
async function fetchData<T>(url: string, mockFallback: T): Promise<T> {
  if (USE_MOCK) return mockFallback;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return await res.json();
}

// Custom hook generator to handle loading/error/data boilerplate safely
function useAmrFetch<T>(url: string | null, mockFallback: T, deps: any[] = []) {
  const [data, setData] = useState<T>(mockFallback); // initialize with mock structurally, but override
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!url) {
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    fetchData<T>(url, mockFallback)
      .then(res => {
        setData(res);
        setLoading(false);
      })
      .catch(err => {
        console.error(`Fetch failed for ${url}:`, err);
        setError(err); // Explicit error state. DO NOT silently substitute mock data.
        setLoading(false);
      });
  }, deps);

  return { data, loading, error };
}

// -------------------------------------------------------------------------
// Single Isolate Hooks
// -------------------------------------------------------------------------

export function useIsolateMetadata(sampleId: string) {
  const mock = mockSampleMetadata.find(m => m.sample_id === sampleId) || mockSampleMetadata[0];
  return useAmrFetch(`/api/v1/isolates/${sampleId}/metadata`, mock, [sampleId]);
}

export function useCohortMetadata(filters?: any) {
  const qs = filters?.project ? `?batch_id=${filters.project}` : '';
  return useAmrFetch(`/api/v1/isolates/cohort-metadata${qs}`, mockSampleMetadata, [filters]);
}

export function useAmrGenes(sampleId?: string) {
  if (sampleId) {
    const mock = mockAmrGenes.filter(g => g.sample_id === sampleId);
    return useAmrFetch(`/api/v1/isolates/${sampleId}/amr-genes`, mock, [sampleId]);
  }
  return useAmrFetch(`/api/v1/isolates/cohort-amr-genes`, mockAmrGenes, [sampleId]);
}

export function useResistanceMutations(sampleId?: string) {
  if (sampleId) {
    const mock = mockMutations.filter(m => m.sample_id === sampleId);
    return useAmrFetch(`/api/v1/isolates/${sampleId}/mutations`, mock, [sampleId]);
  }
  return useAmrFetch(`/api/v1/isolates/cohort-mutations`, mockMutations, [sampleId]);
}

export function useMechanismClassifications() {
  return useAmrFetch(`/api/v1/isolates/mechanisms`, mockMechanismClassifications, []);
}

export function usePhenotypePredictions(sampleId?: string) {
  if (sampleId) {
    const mock = mockPhenotypes.filter(p => p.sample_id === sampleId);
    return useAmrFetch(`/api/v1/isolates/${sampleId}/phenotypes`, mock, [sampleId]);
  }
  return useAmrFetch(`/api/v1/isolates/cohort-phenotypes`, mockPhenotypes, [sampleId]);
}

export function useVirulenceGenes(sampleId?: string) {
  if (sampleId) {
    const mockGenes = mockVirulenceGenes.filter(v => v.sample_id === sampleId);
    const mockResp = { status: "not_run", genes: mockGenes };
    return useAmrFetch(`/api/v1/isolates/${sampleId}/virulence`, mockResp, [sampleId]);
  }
  const mockResp = { status: "not_run", genes: mockVirulenceGenes };
  return useAmrFetch(`/api/v1/isolates/cohort-virulence`, mockResp, [sampleId]);
}

export function useConfidenceScores(sampleId?: string) {
  if (sampleId) {
    return useAmrFetch(`/api/v1/isolates/${sampleId}/confidence`, mockConfidenceScores, [sampleId]);
  }
  return useAmrFetch(`/api/v1/isolates/cohort-confidence`, mockConfidenceScores, [sampleId]);
}

export function useAssemblyMetrics(sampleId?: string) {
  if (sampleId) {
    const mock = mockAssemblyMetrics.filter(m => m.sample_id === sampleId);
    return useAmrFetch(`/api/v1/isolates/${sampleId}/assembly-metrics`, mock, [sampleId]);
  }
  return useAmrFetch(`/api/v1/isolates/cohort-assembly-metrics`, mockAssemblyMetrics, [sampleId]);
}

// -------------------------------------------------------------------------
// Cohort / Precomputed Payload Hooks
// -------------------------------------------------------------------------

export function useCohortClustermap(filters?: any) {
  const qs = filters?.project ? `?batch_id=${filters.project}` : '';
  return useAmrFetch(`/api/v1/surveillance/clustermap${qs}`, mockClustermapPayload, [filters]);
}

export function useCohortPca(filters?: any) {
  const qs = filters?.project ? `?batch_id=${filters.project}` : '';
  return useAmrFetch(`/api/v1/surveillance/pca${qs}`, mockPcaPayload, [filters]);
}

export function useCohortRarefaction(filters?: any) {
  const qs = filters?.project ? `?batch_id=${filters.project}` : '';
  return useAmrFetch(`/api/v1/surveillance/rarefaction${qs}`, mockRarefactionPayload, [filters]);
}

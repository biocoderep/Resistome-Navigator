import { 
  AmrGene, ResistanceMutation, MechanismClassification, 
  PhenotypePrediction, VirulenceGene, ConfidenceScore, 
  AssemblyMetrics, SampleMetadata, ClustermapPayload, 
  PcaPayload, RarefactionPayload 
} from './types/amr';

// A simple seeded random generator for consistent mocks
const rng = ((s) => { let x = s; return () => { x = (x * 16807) % 2147483647; return (x - 1) / 2147483646; }; })(42);

const ORGANISMS = ['E. coli', 'K. pneumoniae', 'P. aeruginosa', 'A. baumannii'];
const DRUG_CLASSES = ['Beta-lactam', 'Aminoglycoside', 'Tetracycline', 'Macrolide', 'Fluoroquinolone', 'Colistin'];
const REGIONS = ['North America', 'Europe', 'Asia', 'South America'];

// Generate 50 sample IDs
export const mockSampleIds = Array.from({length: 50}, (_, i) => `SAMP-${String(i+1).padStart(3, '0')}`);

export const mockSampleMetadata: SampleMetadata[] = mockSampleIds.map((id, i) => ({
  sample_id: id,
  isolate_name: `Isolate_${i+1}`,
  organism: ORGANISMS[Math.floor(rng() * ORGANISMS.length)],
  collection_date: `2025-0${Math.floor(rng()*9)+1}-15`,
  region: REGIONS[Math.floor(rng() * REGIONS.length)],
  project_id: 'PRJ-2026'
}));

export const mockAssemblyMetrics: AssemblyMetrics[] = mockSampleIds.map((id, i) => ({
  sample_id: id,
  total_length: 5000000 + (rng() * 1000000),
  contig_count: Math.floor(40 + rng() * 150),
  n50: 100000 + (rng() * 200000),
  gc_pct: 50 + (rng() * 15),
  species_prediction: mockSampleMetadata[i].organism || 'Unknown'
}));

export const mockAmrGenes: AmrGene[] = [];
mockSampleIds.forEach(id => {
  const numGenes = Math.floor(3 + rng() * 8);
  for(let i=0; i<numGenes; i++) {
    mockAmrGenes.push({
      sample_id: id,
      gene_name: ['blaNDM-1', 'mcr-1', 'tet(A)', 'sul1', 'aac(6\')-Ib'][Math.floor(rng()*5)],
      database_source: ['CARD', 'ResFinder'][Math.floor(rng()*2)],
      identity_pct: 85 + (rng() * 15),
      coverage_pct: 70 + (rng() * 30),
      contig_id: `contig_${Math.floor(rng()*10)}`,
      start: Math.floor(rng() * 10000),
      end: Math.floor(rng() * 10000) + 1000,
      strand: rng() > 0.5 ? '+' : '-',
      drug_class: DRUG_CLASSES[Math.floor(rng()*DRUG_CLASSES.length)],
      mechanism_type: 'antibiotic_inactivation',
      confidence_score: rng() * 100
    });
  }
});

export const mockMutations: ResistanceMutation[] = mockSampleIds.flatMap(id => {
  return [
    {
      sample_id: id,
      gene: 'gyrA',
      position: 83,
      ref_aa: 'S',
      alt_aa: 'I',
      codon_change: 'AGC>ATC',
      clinical_significance: 'HIGH',
      evidence_level: 'Confirmed',
      mechanism_type: 'target_alteration'
    }
  ];
});

export const mockMechanismClassifications: MechanismClassification[] = [
  {
    gene_or_mutation_id: 'blaNDM-1',
    mechanism_type: 'antibiotic_inactivation',
    mechanism_subtype: 'beta-lactamase',
    aro_accession: 'ARO:3000589',
    drug_classes_affected: ['Beta-lactam']
  }
];

export const mockPhenotypes: PhenotypePrediction[] = mockSampleIds.flatMap(id => {
  return ['Meropenem', 'Ciprofloxacin', 'Colistin'].map(drug => ({
    sample_id: id,
    antibiotic: drug,
    antibiotic_class: 'Various',
    predicted_phenotype: (rng() > 0.6 ? 'R' : rng() > 0.3 ? 'I' : 'S') as 'R'|'I'|'S',
    supporting_genes: ['blaNDM-1'],
    confidence: 80 + rng()*20,
    breakpoint_source: 'EUCAST',
    interpretation_notes: 'Predicted via resistome'
  }));
});

export const mockVirulenceGenes: VirulenceGene[] = mockSampleIds.flatMap(id => {
  return [
    {
      sample_id: id,
      gene_name: 'fimH',
      database: 'VFDB',
      function_category: 'adhesin',
      identity_pct: 99,
      coverage_pct: 100,
      contig_id: 'contig_1',
      start: 100,
      end: 1000
    }
  ];
});

export const mockConfidenceScores: ConfidenceScore[] = [
  {
    finding_id: 'blaNDM-1',
    gene_or_mutation: 'blaNDM-1',
    overall_confidence: 95,
    dimension_scores: {
      alignment_quality: 98,
      database_concordance: 100,
      clinical_evidence_weight: 90,
      mutation_catalogue_confidence: 0,
      phenotype_rule_strength: 95
    },
    interpretation_tier: 'HIGH'
  }
];

// Heavy payloads
export const mockClustermapPayload: ClustermapPayload = {
  rowLabels: mockSampleIds.slice(0,10),
  colLabels: DRUG_CLASSES,
  matrix: Array.from({length: 10}, () => Array.from({length: 6}, () => Math.round(rng()))),
  rowLinkage: [[1, 2, 0.5, 2]],
  colLinkage: [[1, 2, 0.5, 2]]
};

export const mockPcaPayload: PcaPayload = {
  points: mockSampleMetadata.map(meta => ({
    sample_id: meta.sample_id,
    pc1: (rng() - 0.5) * 10,
    pc2: (rng() - 0.5) * 10,
    organism: meta.organism || 'Unknown'
  })),
  explainedVariance: [45.2, 21.8]
};

export const mockRarefactionPayload: RarefactionPayload = {
  points: Array.from({length: 50}, (_, i) => ({
    n_isolates: i + 1,
    unique_genes_mean: Math.log(i + 2) * 10,
    ci_low: Math.log(i + 2) * 8,
    ci_high: Math.log(i + 2) * 12
  }))
};

/**
 * AMR Visualisation Data Contract
 * Single source of truth for the JSON payloads expected from the backend.
 */

export type MechanismType = 
  | 'antibiotic_inactivation'
  | 'target_alteration'
  | 'target_protection'
  | 'efflux_pump'
  | 'reduced_permeability'
  | 'target_replacement';

export type Phenotype = 'S' | 'I' | 'R';
export type BreakpointSource = 'EUCAST' | 'CLSI';

export type VirulenceFunctionCategory = 
  | 'toxin'
  | 'adhesin'
  | 'invasion'
  | 'immune_evasion'
  | 'siderophore'
  | 'secretion_system'
  | 'capsule'
  | 'biofilm';

export type InterpretationTier = 'HIGH' | 'MEDIUM' | 'LOW' | 'INSUFFICIENT';

export interface AmrGene {
  sample_id: string;
  gene_name: string;
  database_source: string;
  identity_pct: number;
  coverage_pct: number;
  contig_id: string;
  start: number;
  end: number;
  strand: '+' | '-';
  drug_class: string;
  mechanism_type: MechanismType;
  confidence_score: number;
}

export interface ResistanceMutation {
  sample_id: string;
  gene: string;
  position: number;
  ref_aa: string;
  alt_aa: string;
  codon_change: string;
  clinical_significance: 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';
  evidence_level: string;
  mechanism_type: MechanismType;
}

export interface MechanismClassification {
  gene_or_mutation_id: string;
  mechanism_type: MechanismType;
  mechanism_subtype: string;
  aro_accession: string;
  drug_classes_affected: string[];
}

export interface PhenotypePrediction {
  sample_id: string;
  antibiotic: string;
  antibiotic_class: string;
  predicted_phenotype: Phenotype;
  supporting_genes: string[];
  confidence: number;
  breakpoint_source: BreakpointSource;
  interpretation_notes: string;
}

export interface VirulenceGene {
  sample_id: string;
  gene_name: string;
  database: string;
  function_category: VirulenceFunctionCategory;
  identity_pct: number;
  coverage_pct: number;
  contig_id: string;
  start: number;
  end: number;
}

export interface DimensionScores {
  alignment_quality: number;
  database_concordance: number;
  clinical_evidence_weight: number;
  mutation_catalogue_confidence: number;
  phenotype_rule_strength: number;
}

export interface ConfidenceScore {
  finding_id: string; // e.g., an AmrGene.gene_name or ResistanceMutation.gene_or_mutation_id
  gene_or_mutation: string;
  overall_confidence: number;
  dimension_scores: DimensionScores;
  interpretation_tier: InterpretationTier;
}

export interface AssemblyMetrics {
  sample_id: string;
  total_length: number;
  contig_count: number;
  n50: number;
  gc_pct: number;
  species_prediction: string;
}

export interface SampleMetadata {
  sample_id: string;
  isolate_name: string;
  organism: string | null;
  collection_date: string | null; // ISO 8601 YYYY-MM-DD
  region: string | null;
  project_id: string | null;
}

// -----------------------------------------------------------------------------
// Precomputed (server-side) payloads for heavy plots
// -----------------------------------------------------------------------------

export interface ClustermapPayload {
  rowLabels: string[];
  colLabels: string[];
  matrix: number[][]; // e.g. 0/1 presence or quantitative identity
  rowLinkage: number[][]; // scipy linkage matrix format
  colLinkage: number[][];
}

export interface PcaPoint {
  sample_id: string;
  pc1: number;
  pc2: number;
  organism: string;
}

export interface PcaPayload {
  points: PcaPoint[];
  explainedVariance: [number, number]; // [pc1_var, pc2_var]
}

export interface RarefactionPoint {
  n_isolates: number;
  unique_genes_mean: number;
  ci_low: number;
  ci_high: number;
}

export interface RarefactionPayload {
  points: RarefactionPoint[];
}

# 07 — Resistance Mutation Detection and Mechanism Classification Engine

> **⚠️ Implementation Phase: Phase 2**
>
> Do not implement in the 2-week MVP. Build this after core AMR detection (Doc 06) is working.
>
> **Prerequisite:** `06_AMR_Detection_Engine.md` fully operational.

---

**RESISTANCE MUTATION DETECTION**

**AND MECHANISM CLASSIFICATION ENGINE**

**TECHNICAL DESIGN SPECIFICATION**

**MODULE 1D --- AMR CHARACTERISATION ENGINE**

*Mutations · Mechanisms · Ontology · Phenotypic Evidence*

Python · FastAPI · PostgreSQL · Celery · Nextflow DSL2

Version 1.0 --- CONFIDENTIAL --- Direct Implementation Ready

> **SECTION 1 --- PURPOSE AND SCOPE**

**1.1 Purpose**

The Resistance Mutation and Mechanism Engine (RMME) detects chromosomal resistance mutations and classifies the mechanisms by which all detected AMR determinants (acquired genes + mutations) confer resistance. Its outputs are the primary inputs for the Phenotype Prediction Engine and the Module 2 Genotype--Phenotype Concordance Analysis.

**1.2 Two-Component Design**

  --------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------- ----------------------------------------------------
  **Component**                     **Scope**                                                                                                                                           **Output**

  Mutation Detection Engine         Locates target resistance genes in assembled genome; calls point mutations, indels, frameshifts, and premature stop codons; maps to knowledgebase   resistance_mutations.tsv, mutation_annotations.tsv

  Mechanism Classification Engine   Assigns every AMR gene (from Module 1C) and every mutation to a resistance mechanism class using ARO ontology + rule engine                         mechanism_summary.json, mechanism_per_gene.tsv
  --------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------- ----------------------------------------------------

> **Pipeline Position:** Mutation Detection runs in parallel with AMR Gene Detection (Module 1C). Mechanism Classification runs after both complete and receives the merged gene + mutation inventory as input.
>
> **SECTION 2 --- BIOLOGICAL OBJECTIVES**

**2.1 Mutation Types Detected**

  --------------------------------- ---------------------------------------- ------------------------------------- ----------------------------------------------------------------
  **Mutation Type**                 **Detection Method**                     **Example**                           **Clinical Significance**

  Point mutation (SNP)              Pairwise alignment + codon translation   gyrA S83L (c.248C\>T)                 Primary fluoroquinolone resistance mechanism in Gram-negatives

  Insertion                         Gap analysis in pairwise alignment       IS-element insertion in mgrB          Disrupts mgrB → colistin resistance in K. pneumoniae

  Deletion                          Gap analysis in pairwise alignment       ΔoprD (P. aeruginosa)                 Porin loss → carbapenem resistance via reduced permeability

  Frameshift                        Reading frame analysis after indel       mgrB +1 frameshift → premature stop   Loss of function → resistance

  Premature stop codon              Codon translation check                  mgrB Q71\* (CAG→TAG)                  Protein truncation → loss of function

  Promoter mutation                 Upstream region alignment (−35/−10)      mexR upstream −58 C→T                 Overexpression of efflux pump MexAB-OprM

  Target site alteration (direct)   Alignment + codon change                 rpoB S531L                            Rifampicin resistance by altered binding pocket

  Gene amplification / CNV          Coverage depth analysis (future)         dhfr amplification                    Trimethoprim resistance by gene copy number increase
  --------------------------------- ---------------------------------------- ------------------------------------- ----------------------------------------------------------------

> **SECTION 3 --- TARGET RESISTANCE GENE LOCI**

  ----------------------------- -------------------------------------------- ----------------------------------------------------- -----------------------------------------------------------------
  **Resistance Class**          **Target Genes / Loci**                      **Mutation Type**                                     **Key Example Mutations**

  Fluoroquinolones              gyrA, gyrB, parC, parE                       Point mutations in QRDR                               gyrA S83L/D87N; parC S80I/E84K (E. coli numbering)

  Fluoroquinolones (plasmid)    qnrA/B/S (acquired; also in Module 1C)       Point mutations                                       Reduced susceptibility only; no full resistance alone

  Rifamycins                    rpoB                                         Point mutations in RRDR                               rpoB S450L (D516V, H526Y, H526D) --- WHO high-confidence TBDRaM

  Macrolides / MLSB             23S rRNA (positions 2058/2059 E. coli)       Point mutations                                       A2058G, A2059G (azithromycin resistance in N. gonorrhoeae)

  Aminoglycosides (ribosomes)   16S rRNA, rpsL, rrl                          Point mutations                                       rpsL K43R (streptomycin); 16S rRNA A1408G (amikacin)

  Beta-lactams (PBP)            pbp1a, pbp1b, pbp2, pbp2b, pbp3, pbp4        Point mutations in transpeptidase domain              PBP2b T446A (penicillin resistance in S. pneumoniae)

  Polymyxins (regulatory)       mgrB, pmrA, pmrB, phoP, phoQ                 Point mutations, IS insertions, truncations           mgrB IS element insertion; pmrA T157P

  Glycopeptides                 vanH, vanA (ligase domain)                   Point mutations in van cluster (see also Module 1C)   vanA D312E affects D-Ala-D-Lac activity

  Fluoroquinolones (aac)        aac(6\')-Ib-cr variant                       Point mutation creating new function                  W102R + D179Y creates dual aminoglycoside/FQ acetyltransferase

  Extensible                    Configured via mutation_knowledgebase.json   Any type                                              New loci added without code changes
  ----------------------------- -------------------------------------------- ----------------------------------------------------- -----------------------------------------------------------------

> **SECTION 4 --- REFERENCE KNOWLEDGEBASE DESIGN**

**4.1 Knowledgebase Schema (mutation_knowledgebase.json)**

> {
>
> \"schema_version\": \"1.0.0\",
>
> \"generated_at\": \"2025-06-01T00:00:00Z\",
>
> \"sources\": \[\"CARD\", \"WHO_TBDRAM\", \"EUCAST_ECOFFinder\", \"literature\"\],
>
> \"entries\": \[
>
> {
>
> \"entry_id\": \"MUT_GYRA_S83L_ECO\",
>
> \"gene\": \"gyrA\",
>
> \"organism_group\": \"Enterobacterales\",
>
> \"reference_accession\": \"NP_416734.1\",
>
> \"protein_position\": 83,
>
> \"codon_position\": 249, // 1-based CDS position of first codon base
>
> \"ref_amino_acid\": \"Ser\",
>
> \"alt_amino_acid\": \"Leu\",
>
> \"ref_codon\": \"TCG\",
>
> \"alt_codon\": \"TTG\",
>
> \"mutation_notation\":\"gyrA S83L\",
>
> \"nucleotide_change\":\"c.248C\>T\",
>
> \"drug_class\": \"fluoroquinolone\",
>
> \"drugs_affected\": \[\"ciprofloxacin\",\"levofloxacin\",\"moxifloxacin\"\],
>
> \"mechanism\": \"target_alteration\",
>
> \"effect_on_mic\": \"increase\",
>
> \"mic_fold_change\": \"\>32\",
>
> \"sir_prediction\": \"R\",
>
> \"evidence_level\": 1, // 1=highest; 5=lowest (1=clinical isolates+MIC data)
>
> \"resistance_type\": \"acquired\",
>
> \"pmids\": \[\"10234567\",\"15234890\"\],
>
> \"card_aro\": \"ARO:3003923\",
>
> \"confidence\": 0.99,
>
> \"notes\": \"Most common FQ resistance mutation in E. coli; QRDR position 83\"
>
> },
>
> \...
>
> \]
>
> }

**4.2 Evidence Level Scale**

  ------------------- ------------------------------------------------------------------------- ---------------------------------------------------------------------------
  **Level**           **Description**                                                           **Examples**

  1 --- Definitive    Clinical isolates with MIC data + functional validation                   gyrA S83L in FQ-resistant E. coli; rpoB S531L in rifampicin-resistant MTB

  2 --- Strong        Multiple independent clinical observations; no functional data required   Most CARD/WHO high-confidence mutations

  3 --- Moderate      In vitro selection data; fewer clinical isolates                          Some PMrB mutations for colistin

  4 --- Preliminary   Computational prediction; single report                                   Novel mutations in known QRDR positions

  5 --- Putative      Structural modelling only; no experimental validation                     Predicted effect of amino acid change at binding site
  ------------------- ------------------------------------------------------------------------- ---------------------------------------------------------------------------

> **SECTION 5 --- MUTATION DETECTION WORKFLOW**

**5.1 Workflow Diagram**

> INPUT: validated_genome.fasta + species_id + assembly_metrics.json
>
> │
>
> ▼
>
> ┌───────────────────────────────────────────────────────────┐
>
> │ GENE LOCALIZATION ENGINE │
>
> │ Locate gyrA, gyrB, parC, rpoB, pbp2, mgrB, etc. │
>
> │ → gene_locations.json {contig, start, end, strand} │
>
> └───────────────────────────────┬───────────────────────────┘
>
> │ extracted gene sequences
>
> ▼
>
> ┌───────────────────────────────────────────────────────────┐
>
> │ REFERENCE EXTRACTION │
>
> │ Pull species-matched reference from knowledgebase │
>
> │ → reference_sequences.fasta │
>
> └───────────────────────────────┬───────────────────────────┘
>
> │
>
> ▼
>
> ┌───────────────────────────────────────────────────────────┐
>
> │ ALIGNMENT ENGINE │
>
> │ Needleman-Wunsch (full gene) + Smith-Waterman (local) │
>
> │ → alignment.sam / pairwise_alignments.json │
>
> └───────────────────────────────┬───────────────────────────┘
>
> │
>
> ▼
>
> ┌───────────────────────────────────────────────────────────┐
>
> │ VARIANT DETECTION ENGINE │
>
> │ SNPs, indels, frameshifts, stop codons │
>
> │ → raw_variants.vcf / raw_variants.json │
>
> └──────────────┬──────────────────┬────────────────────────-┘
>
> │ │
>
> ▼ ▼
>
> ┌──────────────────┐ ┌──────────────────────────┐
>
> │ VARIANT │ │ RESISTANCE MUTATION │
>
> │ ANNOTATION │ │ MAPPING (knowledgebase) │
>
> │ Gene, codon, │ │ Known \| Likely \| Novel │
>
> │ protein notation │ │ Unknown │
>
> └────────┬─────────┘ └──────────┬───────────────┘
>
> └─────────────────────────┘
>
> │
>
> ▼
>
> ┌───────────────────────────────────────┐
>
> │ MUTATION CONFIDENCE ENGINE │
>
> │ weighted score → HIGH/MEDIUM/LOW │
>
> └───────────────────────────────────────┘
>
> OUTPUT: resistance_mutations.tsv + mutation_annotations.tsv
>
> **SECTION 6 --- GENE LOCALIZATION ENGINE**

**6.1 Implementation: gene_localization.py**

> \"\"\"Gene localization engine --- Module 1D v1.0.0\"\"\"
>
> from Bio import SeqIO
>
> from ..algorithms.alignment.smith_waterman import smith_waterman
>
> from ..algorithms.search.fmindex_engine import FMIndex
>
> import subprocess, json
>
> from dataclasses import dataclass
>
> \@dataclass
>
> class GeneLocation:
>
> gene_name: str
>
> contig_id: str
>
> start: int \# 1-based inclusive
>
> end: int \# 1-based inclusive
>
> strand: str \# \"+\" or \"-\"
>
> identity_pct: float
>
> coverage_pct: float
>
> extracted_seq:str \# coding sequence from assembly (same strand as reference)
>
> def localise_genes(fasta_path, references: dict\[str, str\],
>
> min_identity=85.0, min_coverage=80.0) -\> list\[GeneLocation\]:
>
> \"\"\"
>
> Locate target resistance genes using BLAST for speed, with SW fallback.
>
> references: {gene_name: reference_cds_sequence}
>
> \"\"\"
>
> results = \[\]
>
> \# Step 1: BLAST pre-screening (fast; low threshold)
>
> blast_hits = \_blast_localise(fasta_path, references, min_identity=70.0)
>
> \# Step 2: Refine candidate regions with NW alignment
>
> for hit in blast_hits:
>
> nw_result = needleman_wunsch(hit.query_seq, references\[hit.gene_name\])
>
> if nw_result.metrics\[\"identity_pct\"\] \>= min_identity:
>
> results.append(\_build_location(hit, nw_result))
>
> return results

**6.2 Reference CDS Extraction**

For each target gene, one species-matched reference CDS is selected from the knowledgebase reference FASTA. Selection priority: (1) same species, (2) same genus, (3) curated representative from CARD/NCBI. All references are pre-indexed using FM-Index at platform startup and stored in indexed_references/ volume.

> **SECTION 7 --- VARIANT DETECTION ENGINE**

**7.1 Implementation: variant_detection.py**

> \"\"\"Variant detection from pairwise alignment --- Module 1D v1.0.0\"\"\"
>
> from dataclasses import dataclass
>
> \@dataclass
>
> class RawVariant:
>
> gene_name: str
>
> cds_position: int \# 1-based position in CDS
>
> protein_position: int \# 1-based amino acid position
>
> ref_nucleotide: str \# reference allele (single or multiple bases)
>
> alt_nucleotide: str \# observed allele
>
> ref_amino_acid: str \| None \# reference amino acid (3-letter code)
>
> alt_amino_acid: str \| None \# observed amino acid (or \"Stop\", \"FS\" for frameshift)
>
> variant_type: str \# SNP \| INS \| DEL \| FRAMESHIFT \| STOP \| PROMOTER
>
> codon_ref: str \| None
>
> codon_alt: str \| None
>
> alignment_quality: float \# fraction of aligned bases around this position
>
> def call_variants(query_aln: str, ref_aln: str, gene_name: str) -\> list\[RawVariant\]:
>
> \"\"\"Call variants from a pairwise alignment (query vs reference).\"\"\"
>
> variants = \[\]
>
> cds_pos, prot_pos = 0, 0
>
> codon_buffer_q, codon_buffer_r = \[\], \[\]
>
> for q_char, r_char in zip(query_aln, ref_aln):
>
> if r_char != \"-\": cds_pos += 1
>
> if q_char == r_char: pass \# match
>
> elif q_char == \"-\": \# deletion in query
>
> variants.append(RawVariant(gene_name=gene_name,
>
> cds_position=cds_pos, protein_position=(cds_pos-1)//3+1,
>
> ref_nucleotide=r_char, alt_nucleotide=\"-\",
>
> variant_type=\"DEL\", \...))
>
> elif r_char == \"-\": \# insertion in query
>
> variants.append(RawVariant(\..., variant_type=\"INS\", \...))
>
> else: \# substitution (SNP)
>
> variants.append(\_call_snp(q_char, r_char, cds_pos, gene_name, \...))
>
> \# Post-process: detect frameshifts from indel patterns
>
> return \_annotate_frameshifts(variants)

**7.2 Stop Codon and Frameshift Detection**

> STOP_CODONS = {\"TAA\", \"TAG\", \"TGA\"}
>
> def detect_stop_codons(coding_seq: str, gene_name: str) -\> list\[RawVariant\]:
>
> \"\"\"Scan translated CDS for premature stop codons.\"\"\"
>
> variants = \[\]
>
> for i in range(0, len(coding_seq) - 2, 3):
>
> codon = coding_seq\[i:i+3\].upper()
>
> aa_pos = i // 3 + 1
>
> if i \< len(coding_seq) - 5 and codon in STOP_CODONS:
>
> variants.append(RawVariant(
>
> gene_name=gene_name, cds_position=i+1,
>
> protein_position=aa_pos, ref_nucleotide=\"\",
>
> alt_nucleotide=\"\*\", ref_amino_acid=None,
>
> alt_amino_acid=\"Stop\", variant_type=\"STOP\",
>
> codon_alt=codon, \...))
>
> return variants
>
> **SECTION 8 --- VARIANT ANNOTATION ENGINE**

**8.1 Implementation: variant_annotation.py**

> \"\"\"Variant annotation with HGVS-style notation --- Module 1D v1.0.0\"\"\"
>
> from Bio.Data import CodonTable
>
> STANDARD_TABLE = CodonTable.unambiguous_dna_by_name\[\"Standard\"\]
>
> AA_3TO1 = {v: k for k, v in CodonTable.standard_dna_table.protein_letters_3to1.items()}
>
> \@dataclass
>
> class AnnotatedVariant:
>
> raw_variant: RawVariant
>
> mutation_notation:str \# e.g. \"gyrA S83L\"
>
> hgvs_protein: str \# e.g. \"p.Ser83Leu\"
>
> hgvs_cdna: str \# e.g. \"c.248C\>T\"
>
> effect: str \# missense \| nonsense \| silent \| frameshift \| inframe_indel
>
> domain: str \| None \# e.g. \"QRDR\" (quinolone resistance-determining region)
>
> def annotate_variant(v: RawVariant) -\> AnnotatedVariant:
>
> if v.variant_type == \"SNP\" and v.ref_amino_acid != v.alt_amino_acid:
>
> notation = f\"{v.gene_name} {v.ref_amino_acid}{v.protein_position}{v.alt_amino_acid}\"
>
> hgvs_p = f\"p.{v.ref_amino_acid}{v.protein_position}{v.alt_amino_acid}\"
>
> hgvs_c = f\"c.{v.cds_position}{v.ref_nucleotide}\>{v.alt_nucleotide}\"
>
> effect = \"missense\"
>
> elif v.variant_type == \"STOP\":
>
> notation = f\"{v.gene_name} {v.ref_amino_acid}{v.protein_position}\*\"
>
> effect = \"nonsense\"
>
> elif v.variant_type in (\"FRAMESHIFT\",):
>
> notation = f\"{v.gene_name} frameshift at {v.protein_position}\"
>
> effect = \"frameshift\"
>
> \...

**8.2 Known Resistance Domain Annotations**

  ----------------------- ---------- --------------------------------------- ---------------------------------------------------------------
  **Domain**              **Gene**   **Positions (protein)**                 **Clinical Significance**

  QRDR (Gyrase A)         gyrA       67--106 (E. coli numbering)             Mutations at 83, 87 confer FQ resistance

  QRDR (Gyrase B)         gyrB       426--447                                D426N, K447E confer moderate FQ resistance

  QRDR (Topo IV A)        parC       78--102                                 S80I, E84K primary contributors with gyrA mutations

  RRDR (RpoB)             rpoB       507--534 (E. coli) / 426--452 (MTB)     Cluster I/II; S531L (H526Y MTB) confers RIF resistance

  Transpeptidase (PBP2)   pbp2       420--475                                Active site mutations in MRSA borderline PBPs

  Sensor domain (MgrB)    mgrB       Entire protein (63 aa); IS insertions   Any disruption → colistin resistance via PmrAB overactivation
  ----------------------- ---------- --------------------------------------- ---------------------------------------------------------------

> **SECTION 9 --- RESISTANCE MUTATION MAPPING ENGINE**

**9.1 Implementation: mutation_mapper.py**

> \"\"\"Knowledgebase mutation mapper --- Module 1D v1.0.0\"\"\"
>
> class MutationClassification:
>
> KNOWN = \"KNOWN_RESISTANCE\" \# exact match in knowledgebase
>
> LIKELY = \"LIKELY_RESISTANCE\" \# same position, different alt AA; same domain
>
> NOVEL = \"NOVEL\" \# new position in known gene; functional impact unknown
>
> SILENT = \"SILENT\" \# synonymous change; no expected effect
>
> UNKNOWN = \"UNKNOWN\" \# gene not in knowledgebase
>
> def map_mutation(variant: AnnotatedVariant,
>
> kb: list\[dict\]) -\> dict:
>
> \"\"\"Match annotated variant against knowledgebase entries.\"\"\"
>
> gene, pos = variant.raw_variant.gene_name, variant.raw_variant.protein_position
>
> alt_aa = variant.raw_variant.alt_amino_acid
>
> \# 1. Exact match: gene + position + alt AA
>
> exact = \[e for e in kb if e\[\"gene\"\]==gene and e\[\"protein_position\"\]==pos
>
> and e\[\"alt_amino_acid\"\]==alt_aa\]
>
> if exact: return {\*\*exact\[0\], \"classification\": MutationClassification.KNOWN}
>
> \# 2. Position match: same gene + same position, different alt AA
>
> same_pos = \[e for e in kb if e\[\"gene\"\]==gene and e\[\"protein_position\"\]==pos\]
>
> if same_pos:
>
> return {\*\*same_pos\[0\], \"classification\": MutationClassification.LIKELY,
>
> \"note\": f\"Different amino acid change at known resistance position {pos}\"}
>
> \# 3. Gene in KB but position not recorded
>
> if any(e\[\"gene\"\]==gene for e in kb):
>
> return {\"gene\":gene,\"classification\":MutationClassification.NOVEL,\"position\":pos}
>
> return {\"gene\":gene,\"classification\":MutationClassification.UNKNOWN}
>
> **SECTION 10 --- MUTATION CONFIDENCE ENGINE**

**10.1 Confidence Formula**

Mutation confidence C = w₁×alignment_quality + w₂×kb_evidence + w₃×gene_coverage + w₄×classification_score

  ------------------------ ------------ -----------------------------------------------------------------------------------------------------------
  **Component**            **Weight**   **Calculation**

  Alignment quality        0.30         Fraction of bases aligned without gaps in ±10 bp window around mutation

  Knowledgebase evidence   0.35         1.0 if KNOWN (ev_level 1-2); 0.80 if KNOWN (ev_level 3-4); 0.60 if LIKELY; 0.25 if NOVEL; 0.10 if UNKNOWN

  Gene coverage            0.20         coverage_pct / 100 from gene localisation (full-length gene hit preferred)

  Classification score     0.15         1.0 if KNOWN; 0.70 if LIKELY; 0.40 if NOVEL; 0.10 if UNKNOWN
  ------------------------ ------------ -----------------------------------------------------------------------------------------------------------

**10.2 Implementation: mutation_confidence.py**

> CLASSIFICATION_WEIGHT = {
>
> \"KNOWN_RESISTANCE\": 1.0,
>
> \"LIKELY_RESISTANCE\": 0.70,
>
> \"NOVEL\": 0.40,
>
> \"UNKNOWN\": 0.10,
>
> }
>
> def kb_evidence_score(kb_entry: dict \| None) -\> float:
>
> if kb_entry is None: return 0.10
>
> level = kb_entry.get(\"evidence_level\", 5)
>
> return max(0.0, 1.0 - (level - 1) \* 0.15)
>
> def compute_mutation_confidence(variant: AnnotatedVariant,
>
> mapping: dict,
>
> gene_loc: GeneLocation) -\> dict:
>
> aln_q = variant.raw_variant.alignment_quality
>
> kb_ev = kb_evidence_score(mapping.get(\"kb_entry\"))
>
> cov_s = min(gene_loc.coverage_pct / 100, 1.0)
>
> cls_s = CLASSIFICATION_WEIGHT.get(mapping\[\"classification\"\], 0.10)
>
> score = 0.30\*aln_q + 0.35\*kb_ev + 0.20\*cov_s + 0.15\*cls_s
>
> tier = \"HIGH\" if score\>=0.80 else \"MEDIUM\" if score\>=0.55 else \"LOW\"
>
> return {\"confidence_score\": round(score, 4), \"confidence_tier\": tier}
>
> **SECTION 11 --- RESISTANCE MECHANISM ONTOLOGY**

**11.1 mechanism_ontology.json**

> {
>
> \"schema_version\": \"1.0.0\",
>
> \"mechanism_classes\": \[
>
> {
>
> \"code\": \"antibiotic_inactivation\",
>
> \"display_name\":\"Antibiotic Inactivation (Beta-Lactamase / Enzyme)\",
>
> \"aro_term\": \"antibiotic inactivation enzyme\",
>
> \"subclasses\": \[\"beta-lactamase_serine\",\"beta-lactamase_metallo\",
>
> \"acetyltransferase\",\"phosphotransferase\",\"adenylyltransferase\"\],
>
> \"drug_classes\":\[\"beta-lactam\",\"aminoglycoside\",\"chloramphenicol\"\]
>
> },
>
> { \"code\":\"efflux_pump\", \"display_name\":\"Efflux Pump Overexpression\",
>
> \"subclasses\":\[\"RND\",\"MFS\",\"ABC\",\"MATE\",\"SMR\"\],
>
> \"drug_classes\":\[\"fluoroquinolone\",\"tetracycline\",\"macrolide\",\"beta-lactam\"\] },
>
> { \"code\":\"target_alteration\", \"display_name\":\"Target Site Alteration\",
>
> \"subclasses\":\[\"QRDR_mutation\",\"RRDR_mutation\",\"PBP_alteration\",\"ribosomal_mutation\",\"23S_mutation\"\],
>
> \"drug_classes\":\[\"fluoroquinolone\",\"rifamycin\",\"beta-lactam\",\"aminoglycoside\",\"macrolide\"\] },
>
> { \"code\":\"target_protection\", \"display_name\":\"Target Protection\",
>
> \"subclasses\":\[\"Qnr_protein\",\"Tet_ribosomal_protection\"\],
>
> \"drug_classes\":\[\"fluoroquinolone\",\"tetracycline\"\] },
>
> { \"code\":\"target_replacement\", \"display_name\":\"Target Replacement (Alternative Target)\",
>
> \"subclasses\":\[\"altered_PBP\",\"D-Ala-D-Lac_ligase\"\],
>
> \"drug_classes\":\[\"beta-lactam\",\"glycopeptide\"\] },
>
> { \"code\":\"reduced_permeability\", \"display_name\":\"Reduced Membrane Permeability\",
>
> \"subclasses\":\[\"porin_loss\",\"OMP_downregulation\"\],
>
> \"drug_classes\":\[\"carbapenem\",\"aminoglycoside\"\] },
>
> { \"code\":\"membrane_remodeling\", \"display_name\":\"Membrane Lipid Remodeling\",
>
> \"subclasses\":\[\"LPS_modification\",\"lipid_A_modification\"\],
>
> \"drug_classes\":\[\"polymyxin\"\] },
>
> { \"code\":\"enzymatic_modification\",\"display_name\":\"Enzymatic Drug Modification\",
>
> \"subclasses\":\[\"methyltransferase\",\"kinase\"\],
>
> \"drug_classes\":\[\"macrolide\",\"aminoglycoside\"\] },
>
> { \"code\":\"regulatory_mutation\", \"display_name\":\"Regulatory/Promoter Mutation\",
>
> \"subclasses\":\[\"promoter_mutation\",\"regulatory_gene_mutation\"\],
>
> \"drug_classes\":\[\"fluoroquinolone\",\"tetracycline\",\"macrolide\"\] },
>
> { \"code\":\"unknown\", \"display_name\":\"Unknown Mechanism\",
>
> \"subclasses\":\[\],
>
> \"drug_classes\":\[\] }
>
> \]
>
> }
>
> **SECTION 12 --- MECHANISM CLASSIFICATION ENGINE**

**12.1 Classification Logic**

The Mechanism Classification Engine receives the merged gene + mutation inventory (acquired genes from Module 1C + chromosomal mutations from Module 1D) and assigns each determinant to a mechanism class using a three-tier priority system.

  ----------------------------- --------------------------------------------------------- -------------- ---------------------------------------------------------
  **Tier**                      **Source**                                                **Priority**   **Example**

  1 --- ARO Ontology            CARD ARO mechanism annotation on amr_gene.aro_accession   Highest        ARO:3000016 (blaCTX-M-15) → \"antibiotic_inactivation\"

  2 --- Knowledgebase           mutation_knowledgebase.json mechanism field               High           gyrA S83L → \"target_alteration\"

  3 --- Gene prefix heuristic   Gene name prefix lookup table (from Module 1C)            Fallback       tetA → \"efflux_pump\"; vanA → \"target_alteration\"
  ----------------------------- --------------------------------------------------------- -------------- ---------------------------------------------------------

**12.2 Implementation: mechanism_classifier.py**

> \"\"\"Mechanism classification engine --- Module 1D v1.0.0\"\"\"
>
> import json
>
> from pathlib import Path
>
> class MechanismClassifier:
>
> def \_\_init\_\_(self, ontology_path: Path, aro_mapper, kb: list):
>
> self.ontology = json.loads(ontology_path.read_text())
>
> self.aro_mapper = aro_mapper
>
> self.kb = {e\[\"entry_id\"\]: e for e in kb}
>
> self.\_build_class_index()
>
> def classify_gene(self, gene: \"AMRGeneResult\") -\> dict:
>
> \# Tier 1: ARO ontology
>
> if gene.aro_accession:
>
> aro_mech = self.aro_mapper.lookup(gene.aro_accession)
>
> if aro_mech.get(\"resistance_mechanism\"):
>
> return self.\_build_result(aro_mech\[\"resistance_mechanism\"\],
>
> source=\"ARO\", confidence=0.95)
>
> \# Tier 2: pre-annotated mechanism from Module 1C
>
> if gene.mechanism_type and gene.mechanism_type != \"unknown\":
>
> return self.\_build_result(gene.mechanism_type,
>
> source=\"AMR_DETECTION\", confidence=0.85)
>
> \# Tier 3: gene-name prefix heuristic
>
> return self.\_heuristic_classify(gene.gene_name)
>
> def classify_mutation(self, mutation: \"AnnotatedVariant\", mapping: dict) -\> dict:
>
> if mapping.get(\"mechanism\"):
>
> return self.\_build_result(mapping\[\"mechanism\"\],
>
> source=\"KNOWLEDGEBASE\", confidence=mapping.get(\"confidence\",0.8))
>
> return self.\_build_result(\"target_alteration\", source=\"HEURISTIC\", confidence=0.60)

**12.3 Classification Examples**

  ------------------------------------- ------------------------------ --------------------- ------------------------------ ----------------
  **Determinant**                       **ARO Lookup**                 **KB Lookup**         **Final Mechanism**            **Confidence**

  blaCTX-M-15                           antibiotic inactivation        ---                   antibiotic_inactivation        0.95

  tetA                                  antibiotic efflux              ---                   efflux_pump                    0.95

  gyrA S83L                             ---                            target_alteration     target_alteration              0.92

  mgrB IS insertion (truncation)        ---                            membrane_remodeling   membrane_remodeling            0.90

  vanA                                  antibiotic target alteration   ---                   target_alteration              0.95

  qnrB2                                 antibiotic target protection   ---                   target_protection              0.95

  MexAB-OprM (mexR promoter mutation)   ---                            regulatory_mutation   regulatory_mutation            0.85

  novel gyrA mutation                   ---                            NOVEL in QRDR         target_alteration (inferred)   0.60
  ------------------------------------- ------------------------------ --------------------- ------------------------------ ----------------

> **SECTION 13 --- MECHANISM EVIDENCE AGGREGATION**

**13.1 Implementation: mechanism_evidence.py**

> \@dataclass
>
> class MechanismObject:
>
> mechanism_code: str \# from ontology
>
> mechanism_name: str \# display name
>
> mechanism_subclass: str \| None
>
> drug_classes: list\[str\] \# drugs affected by this mechanism
>
> supporting_genes: list\[str\] \# gene names
>
> supporting_mutations: list\[str\] \# mutation notations
>
> evidence_sources: list\[str\] \# ARO \| KNOWLEDGEBASE \| HEURISTIC
>
> confidence: float
>
> confidence_tier: str
>
> def aggregate_mechanisms(genes: list, mutations: list,
>
> classifier: MechanismClassifier) -\> list\[MechanismObject\]:
>
> mech_map = defaultdict(lambda: {\"genes\":\[\],\"mutations\":\[\],\"confidences\":\[\],\"sources\":\[\]})
>
> for gene in genes:
>
> mech = classifier.classify_gene(gene)
>
> mech_map\[mech\[\"code\"\]\]\[\"genes\"\].append(gene.gene_name)
>
> mech_map\[mech\[\"code\"\]\]\[\"confidences\"\].append(mech\[\"confidence\"\])
>
> mech_map\[mech\[\"code\"\]\]\[\"sources\"\].append(mech\[\"source\"\])
>
> for mutation in mutations:
>
> mech = classifier.classify_mutation(mutation, mutation.mapping)
>
> mech_map\[mech\[\"code\"\]\]\[\"mutations\"\].append(mutation.mutation_notation)
>
> mech_map\[mech\[\"code\"\]\]\[\"confidences\"\].append(mech\[\"confidence\"\])
>
> return \[\_build_mech_object(code, data) for code, data in mech_map.items()\]
>
> **SECTION 14 --- DRUG RESISTANCE ASSOCIATION ENGINE**

**14.1 Implementation: drug_association.py**

> \@dataclass
>
> class DrugAssociation:
>
> drug_name: str
>
> drug_class: str
>
> sir_prediction: str \# S \| I \| R \| U
>
> evidence_type: str \# gene \| mutation \| mechanism
>
> evidence_name: str
>
> evidence_level: int \# 1--5
>
> confidence: float
>
> cross_resistance: list\[str\] \# other drugs in same class also predicted R
>
> \# Cross-resistance rules
>
> CROSS_RESISTANCE = {
>
> \"fluoroquinolone\": \[\"ciprofloxacin\",\"levofloxacin\",\"moxifloxacin\",\"norfloxacin\"\],
>
> \"beta-lactam\": \[\"ampicillin\",\"piperacillin\",\"cefazolin\",\"ceftriaxone\"\],
>
> \"carbapenem\": \[\"meropenem\",\"imipenem\",\"ertapenem\",\"doripenem\"\],
>
> \"aminoglycoside\": \[\"gentamicin\",\"tobramycin\",\"amikacin\",\"kanamycin\"\],
>
> }

**14.2 Drug Association Matrix**

  ----------------------- ------------------------------ ----------------------------- -------------------- --------------------
  **Gene/Mutation**       **Primary Drug**               **Cross-Resistance**          **SIR Prediction**   **Evidence Level**

  blaCTX-M-15             Ceftriaxone                    All 3GC, aztreonam            R                    1

  blaKPC-2                Meropenem                      All carbapenems + 3GC         R                    1

  gyrA S83L (alone)       Ciprofloxacin                  Most fluoroquinolones         R                    1

  gyrA S83L + parC S80I   Ciprofloxacin + Levofloxacin   All FQ (high-level)           R (high-level)       1

  rpoB S531L              Rifampicin                     All rifamycins                R                    1

  mgrB truncation         Colistin                       Polymyxin B                   R                    2

  vanA                    Vancomycin                     Teicoplanin                   R                    1

  gyrA D87N (alone)       Ciprofloxacin                  Reduced susceptibility only   I                    1
  ----------------------- ------------------------------ ----------------------------- -------------------- --------------------

> **SECTION 15 --- NOVEL MUTATION DETECTION ENGINE**

**15.1 Novel Mutation Classification Criteria**

  -------------------- -------------------------------------------------------------- ------------------------------------------------------------------ -------------------
  **Classification**   **Criteria**                                                   **Action**                                                         **Report Flag**

  KNOWN_RESISTANCE     Exact match in knowledgebase                                   Include in standard report; use KB SIR prediction                  None

  LIKELY_RESISTANCE    Same position as known mutation; different alt amino acid      Include with LIKELY flag; use inferred SIR from domain knowledge   LIKELY_RESISTANCE

  NOVEL_IN_DOMAIN      New position within known resistance domain (QRDR/RRDR/etc)    Include with NOVEL_DOMAIN flag; SIR = INDETERMINATE                NOVEL_DOMAIN

  NOVEL_IN_GENE        New position in known resistance gene; outside known domains   Include with NOVEL flag; SIR = UNKNOWN                             NOVEL

  SILENT               Synonymous change; no amino acid change                        Log; exclude from resistance report                                SILENT (excluded)

  UNKNOWN_GENE         Gene not in knowledgebase                                      Exclude from mutation report; may appear via Module 1C             UNKNOWN_GENE
  -------------------- -------------------------------------------------------------- ------------------------------------------------------------------ -------------------

**15.2 novel_mutation_report.json Schema**

> {
>
> \"sample_id\": \"uuid\",
>
> \"novel_mutations\": \[
>
> {
>
> \"gene\": \"gyrA\",
>
> \"mutation\": \"gyrA T66A\",
>
> \"position\": 66,
>
> \"domain\": \"QRDR\",
>
> \"classification\":\"NOVEL_IN_DOMAIN\",
>
> \"sir_prediction\":\"INDETERMINATE\",
>
> \"notes\": \"Position 66 is within QRDR (67-106); not in knowledgebase; requires wet-lab confirmation\"
>
> }
>
> \],
>
> \"total_novel\": 1
>
> **SECTION 16 --- MUTATION PRIORITISATION ENGINE**

**16.1 Prioritisation Scoring**

Priority score P = w₁×clinical_relevance + w₂×drug_importance + w₃×confidence + w₄×evidence_strength

  -------------------- ------------ ------------------------------------------------------------------------------
  **Component**        **Weight**   **Scoring**

  Clinical relevance   0.35         1.0 if WHO Critical/Priority drug; 0.70 if High Priority; 0.40 if other

  Drug importance      0.25         1.0 for carbapenems/glycopeptides/polymyxins; 0.80 for FQ/BL; 0.60 for other

  Confidence score     0.25         Direct from mutation_confidence.py (0.0--1.0)

  Evidence strength    0.15         1.0 if evidence_level ≤ 2; 0.70 if level 3; 0.40 if level 4-5
  -------------------- ------------ ------------------------------------------------------------------------------

**16.2 prioritized_mutations.tsv Columns**

> priority_rank \| gene \| mutation_notation \| drug_class \| drugs_affected \|
>
> sir_prediction \| confidence_tier \| confidence_score \| evidence_level \|
>
> classification \| novel_flag \| priority_score
>
> **SECTION 17 --- RESISTANCE KNOWLEDGE MODEL**

**17.1 ResistanceDeterminant --- Unified Data Model**

The ResistanceDeterminant is the canonical output object that flows from Module 1D into the Phenotype Prediction Engine (Module 1E) and the Module 2 concordance analysis.

> \@dataclass
>
> class ResistanceDeterminant:
>
> \"\"\"Unified model linking a resistance element to its mechanism and drug effects.\"\"\"
>
> determinant_id: str \# UUID
>
> determinant_type: str \# \"gene\" \| \"mutation\" \| \"gene_mutation\"
>
> \# Identity
>
> gene_name: str
>
> mutation_notation: str \| None \# e.g. \"gyrA S83L\" (None for gene-only)
>
> aro_accession: str \| None
>
> \# Mechanism
>
> mechanism_code: str
>
> mechanism_name: str
>
> mechanism_subclass:str \| None
>
> \# Drug associations
>
> drug_class: str
>
> drugs_affected: list\[str\]
>
> sir_prediction: str \# S \| I \| R \| U \| INDETERMINATE
>
> \# Evidence
>
> evidence_level: int
>
> supporting_dbs: list\[str\]
>
> classification: str \# KNOWN_RESISTANCE \| LIKELY \| NOVEL \| UNKNOWN
>
> \# Scores
>
> confidence_score: float
>
> confidence_tier: str
>
> priority_score: float
>
> \# Genomic location
>
> contig_id: str \| None
>
> start: int \| None
>
> end: int \| None
>
> strand: str \| None
>
> **SECTION 18 --- DATABASE DESIGN**

**18.1 Table Design**

  -------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ --------------------------------------------------------------------------------
  **Table**                        **Key Columns**                                                                                                                                                                                                                **Notes**

  mutations                        id, sample_id, job_id, db_version_id, gene_name, gene_id (FK amr_genes), cds_position, protein_position, ref_aa, alt_aa, codon_change, mutation_type, variant_type, clinical_significance, associated_drug, confidence_score   Core table; one row per detected mutation per sample; replaces stub from DDS

  mutation_annotations             id, mutation_id (FK), annotation_source, key, value                                                                                                                                                                            HGVS notations, domain annotations, mutation_notation string, cross-references

  mutation_evidence                id, mutation_id (FK), evidence_type, evidence_level, pmid, description                                                                                                                                                         Literature and database evidence for each mutation

  mechanisms                       id, class_id (FK mechanism_classes), name, aro_accession, description, drug_classes TEXT\[\]                                                                                                                                   Canonical mechanism entries from ontology

  mechanism_classes                id, code, display_name, aro_term                                                                                                                                                                                               Reference table; 10 entries seeded from mechanism_ontology.json

  gene_mechanisms (junction)       amr_gene_id, mechanism_id, confidence, source, assigned_at                                                                                                                                                                     Links amr_genes → mechanisms; many-to-many

  mutation_mechanisms (junction)   mutation_id, mechanism_id, confidence, source                                                                                                                                                                                  Links mutations → mechanisms

  drug_associations                id, sample_id, determinant_type, determinant_id, drug_name, drug_class, sir_prediction, confidence, evidence_level                                                                                                             Drug-specific resistance calls per sample; feeds phenotype predictor

  knowledgebase_versions           id, version, source, entry_count, deployed_at, checksum                                                                                                                                                                        Tracks mutation_knowledgebase.json versions for reproducibility
  -------------------------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ --------------------------------------------------------------------------------

**18.2 Key SQL --- mutation_mechanisms**

> CREATE TABLE mutation_mechanisms (
>
> mutation_id UUID NOT NULL REFERENCES mutations(id) ON DELETE CASCADE,
>
> mechanism_id UUID NOT NULL REFERENCES mechanisms(id) ON DELETE RESTRICT,
>
> confidence NUMERIC(5,4),
>
> source VARCHAR(50), \-- ARO \| KNOWLEDGEBASE \| HEURISTIC
>
> assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> PRIMARY KEY (mutation_id, mechanism_id)
>
> );
>
> CREATE INDEX idx_mut_mech ON mutation_mechanisms (mutation_id);
>
> **SECTION 19 --- FASTAPI SERVICE DESIGN**

  ------------ --------------------------------------------- --------------------------------------------- --------------------------------------------------------------------------
  **Method**   **Path**                                      **Response**                                  **Description**

  POST         /api/v1/module1/mutations                     202 {job_id}                                  Submit mutation detection job; async

  GET          /api/v1/module1/mutations/{job_id}            200 {status, progress_pct}                    Poll job status

  GET          /api/v1/module1/mutations/{job_id}/results    200 {mutations\[\], novel\[\]}                Full mutation inventory

  GET          /api/v1/samples/{id}/mutations                200 {mutations\[\], pagination}               All mutations for a sample

  POST         /api/v1/module1/mechanisms                    202 {job_id}                                  Submit mechanism classification; typically auto-triggered

  GET          /api/v1/module1/mechanisms/{job_id}           200 {status, progress_pct}                    Poll classification job

  GET          /api/v1/module1/mechanisms/{job_id}/results   200 {mechanisms\[\], drug_associations\[\]}   Full classification results

  GET          /api/v1/samples/{id}/determinants             200 {determinants\[\]}                        All ResistanceDeterminant objects for sample; fed to phenotype predictor
  ------------ --------------------------------------------- --------------------------------------------- --------------------------------------------------------------------------

**19.1 Mutation Detection Request Schema**

> class MutationDetectionRequest(BaseModel):
>
> model_config = ConfigDict(strict=True)
>
> sample_id: UUID
>
> assembly_id: UUID
>
> species: str \| None = None
>
> kb_version_id: str \| None = None \# pin knowledgebase version; default = active
>
> target_genes: list\[str\] \| None = None \# restrict to subset; default = all configured
>
> min_gene_identity: float = Field(default=85.0, ge=70.0, le=100.0)

**19.2 Mutation Result Response Schema**

> {
>
> \"mutation_id\": \"uuid\",
>
> \"gene_name\": \"gyrA\",
>
> \"mutation_notation\": \"gyrA S83L\",
>
> \"hgvs_protein\": \"p.Ser83Leu\",
>
> \"hgvs_cdna\": \"c.248C\>T\",
>
> \"variant_type\": \"SNP\",
>
> \"effect\": \"missense\",
>
> \"domain\": \"QRDR\",
>
> \"drug_class\": \"fluoroquinolone\",
>
> \"drugs_affected\": \[\"ciprofloxacin\",\"levofloxacin\",\"moxifloxacin\"\],
>
> \"sir_prediction\": \"R\",
>
> \"classification\": \"KNOWN_RESISTANCE\",
>
> \"evidence_level\": 1,
>
> \"confidence_score\": 0.9420,
>
> \"confidence_tier\": \"HIGH\"
>
> **SECTION 20 --- CELERY TASK DESIGN**

**20.1 Mutation Detection Task**

> \@celery.task(bind=True, name=\"module1.mutation_detection\",
>
> max_retries=3, soft_time_limit=3600, time_limit=4200)
>
> def mutation_detection_task(self, job_id: str, config: dict) -\> dict:
>
> engine = MutationDetectionEngine(job_id, config)
>
> result = engine.run(progress_cb=lambda p,s: self.update_state(
>
> state=\"RUNNING\", meta={\"progress\":p,\"step\":s}))
>
> return {\"status\":\"COMPLETED\",\"mutation_count\": result.total_mutations}

**20.2 Progress Steps**

  ------------------------- ---------------- -----------------------------------------------------------
  **Step**                  **Progress %**   **Description**

  LOADING_GENOME            0--5             Parse validated FASTA; build contig registry

  GENE_LOCALIZATION         5--30            BLAST + NW alignment for all target gene loci

  VARIANT_CALLING           30--55           SNP/indel/stop codon detection from alignments

  VARIANT_ANNOTATION        55--65           HGVS notation; domain classification; codon translation

  KB_MAPPING                65--75           Knowledgebase lookup for all variants

  DRUG_ASSOCIATION          75--82           Drug class and SIR prediction from KB entries

  NOVEL_DETECTION           82--87           Novel mutation identification and flagging

  CONFIDENCE_SCORING        87--92           Weighted confidence score per variant

  PRIORITIZATION            92--96           Priority ranking and prioritized_mutations.tsv generation

  MECHANISM_PREANNOTATION   96--98           Mechanism pre-annotation for mutation-only findings

  REPORT_GENERATION         98--100          JSON/TSV/PDF; DB write; mechanism classification trigger
  ------------------------- ---------------- -----------------------------------------------------------

> **SECTION 21 --- NEXTFLOW DSL2 PROCESS DESIGN**

**21.1 DSL2 Processes**

> process MUTATION_DETECTION {
>
> tag \"\${meta.sample_id}\"
>
> label \"process_medium\"
>
> cpus 4; memory \"8 GB\"; time \"45.min\"
>
> container \"amr-platform/mutation-detector:1.0.0\"
>
> input:
>
> tuple val(meta), path(fasta)
>
> path kb_json // mutation_knowledgebase.json
>
> path ref_sequences // reference CDS FASTA per gene
>
> output:
>
> tuple val(meta), path(\"resistance_mutations.tsv\"), emit: mutations_tsv
>
> tuple val(meta), path(\"mutation_annotations.tsv\"), emit: annotations_tsv
>
> tuple val(meta), path(\"novel_mutation_report.json\"), emit: novel_json
>
> tuple val(meta), path(\"prioritized_mutations.tsv\"), emit: prioritized_tsv
>
> script:
>
> \"\"\"
>
> mutation-detect \\
>
> \--input \${fasta} \\
>
> \--knowledgebase \${kb_json} \\
>
> \--references \${ref_sequences} \\
>
> \--species \"\${meta.species ?: \"\"}\" \\
>
> \--threads \${task.cpus} \\
>
> \--output-dir .
>
> \"\"\"
>
> }
>
> process MECHANISM_CLASSIFICATION {
>
> tag \"\${meta.sample_id}\"
>
> label \"process_low\"
>
> cpus 2; memory \"4 GB\"; time \"15.min\"
>
> container \"amr-platform/mechanism-classifier:1.0.0\"
>
> input:
>
> tuple val(meta), path(amr_genes_json) // from Module 1C
>
> tuple val(meta), path(mutations_tsv) // from MUTATION_DETECTION
>
> path ontology_json // mechanism_ontology.json
>
> path aro_json // CARD aro.json
>
> output:
>
> tuple val(meta), path(\"mechanism_summary.json\"), emit: mech_summary
>
> tuple val(meta), path(\"mechanism_per_gene.tsv\"), emit: mech_per_gene
>
> tuple val(meta), path(\"drug_associations.tsv\"), emit: drug_assoc
>
> tuple val(meta), path(\"determinants.json\"), emit: determinants // ResistanceDeterminant objects
>
> script:
>
> \"\"\"
>
> mechanism-classify \\
>
> \--amr-genes \${amr_genes_json} \\
>
> \--mutations \${mutations_tsv} \\
>
> \--ontology \${ontology_json} \\
>
> \--aro \${aro_json} \\
>
> \--output-dir .
>
> \"\"\"
>
> }
>
> workflow MUTATION_MECHANISM_SUBWORKFLOW {
>
> take:
>
> ch_validated_fasta
>
> ch_amr_genes_json // from AMR_DETECTION_SUBWORKFLOW
>
> main:
>
> MUTATION_DETECTION(ch_validated_fasta, kb_json, ref_sequences)
>
> MECHANISM_CLASSIFICATION(
>
> ch_amr_genes_json,
>
> MUTATION_DETECTION.out.mutations_tsv,
>
> ontology_json, aro_json
>
> )
>
> emit:
>
> determinants = MECHANISM_CLASSIFICATION.out.determinants
>
> mutations = MUTATION_DETECTION.out.mutations_tsv
>
> **SECTION 22 --- TESTING STRATEGY**

  --------------------------- -------------------------- -------------------------------------------------------------------------- ---------------------------------------------------------------------------------------------
  **Test Type**               **Framework**              **Scope**                                                                  **Key Assertions**

  Unit Tests                  pytest                     call_variants(), annotate_variant(), map_mutation(), classify_gene()       ≥ 95% coverage; known-answer tests for gyrA/rpoB/mgrB mutations

  Mutation Validation Tests   pytest + FASTA fixtures    Synthetic FASTAs with engineered mutations                                 gyrA S83L engineered → detected as KNOWN_RESISTANCE; mgrB stop → STOP + membrane_remodeling

  Reference Dataset Tests     pytest + NCBI accessions   NCBI isolates with confirmed resistance profiles                           FQ-resistant E. coli → gyrA S83L detected; MDR K. pneumoniae → blaKPC + colistin mutations

  Ontology Tests              pytest                     All mechanism classification rules and ARO mappings                        All 100 KB entries mapped to correct mechanism; ontology completeness check

  Novel Mutation Tests        pytest                     Engineered novel positions in QRDR/RRDR                                    Novel QRDR mutation → NOVEL_IN_DOMAIN flag; correct SIR=INDETERMINATE

  Integration Tests           pytest + testcontainers    POST mutations → COMPLETED → results; mechanism classification triggered   DB tables populated correctly; determinants.json valid schema

  Performance Tests           pytest-benchmark           5 Mb genome; all default target genes                                      Mutation detection \< 8 min; mechanism classification \< 2 min
  --------------------------- -------------------------- -------------------------------------------------------------------------- ---------------------------------------------------------------------------------------------

**22.1 Known-Answer Test Cases**

  -------------------------------- ---------------------------------- -------------------------- --------------------
  **Test Sequence**                **Engineered Change**              **Expected Notation**      **Expected SIR**

  E. coli K-12 gyrA (wild-type)    c.248C\>T (p.Ser83Leu)             gyrA S83L                  R (FQ)

  E. coli K-12 gyrA (wild-type)    c.259G\>A (p.Asp87Asn)             gyrA D87N                  I/R (FQ)

  E. coli K-12 parC (wild-type)    c.239G\>T (p.Ser80Ile)             parC S80I                  R when + gyrA S83L

  MTB rpoB (wild-type)             c.1592C\>T (p.Ser531Leu)           rpoB S531L                 R (RIF)

  K. pneumoniae mgrB (wild-type)   IS1 insertion at position 45       mgrB IS-insertion (STOP)   R (COL)

  E. coli gyrA (WT)                c.197G\>A (p.Gly66Asp) --- NOVEL   gyrA G66D                  INDETERMINATE
  -------------------------------- ---------------------------------- -------------------------- --------------------

> **SECTION 23 --- REPORT GENERATION**

  ---------------------------- ------------ ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **File**                     **Format**   **Key Contents**

  resistance_mutations.tsv     TSV          mutation_id, gene, mutation_notation, hgvs_p, hgvs_c, variant_type, drug_class, sir_prediction, classification, evidence_level, confidence_tier, contig_id, protein_position

  mutation_annotations.tsv     TSV          mutation_id, annotation_source, key, value --- includes HGVS, domain, cross-references

  mutation_evidence.tsv        TSV          mutation_id, evidence_type, evidence_level, pmid, description

  mechanism_summary.json       JSON         Per-sample list of MechanismObject with supporting genes, mutations, confidence

  mechanism_per_gene.tsv       TSV          gene_or_mutation, mechanism_code, mechanism_name, drug_class, confidence_tier, source

  drug_associations.tsv        TSV          determinant, drug_name, drug_class, sir_prediction, confidence, cross_resistance

  novel_mutation_report.json   JSON         All NOVEL and LIKELY mutations with domains and notes

  prioritized_mutations.tsv    TSV          Priority-ranked mutations; priority_score, all key fields

  mutation_report.pdf          PDF          Clinical report: per-drug-class mutation table, mechanism summary, novel mutation alert panel, evidence quality bar chart
  ---------------------------- ------------ ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

> **SECTION 24 --- IMPLEMENTATION PLAN AND PACKAGE STRUCTURE**

**24.1 Python Package Structure**

> mutation_engine/
>
> ├── \_\_init\_\_.py \# MutationDetectionEngine + MechanismClassificationEngine
>
> ├── cli.py \# mutation-detect CLI entrypoint
>
> ├── result_models.py \# RawVariant, AnnotatedVariant, ResistanceDeterminant
>
> ├── knowledgebase/
>
> │ ├── loader.py \# Load + cache mutation_knowledgebase.json
>
> │ └── mutation_knowledgebase.json \# Curated knowledgebase (seeded at install)
>
> ├── ontology/
>
> │ ├── mechanism_ontology.json
>
> │ └── ontology_loader.py
>
> ├── gene_localization.py \# BLAST + NW gene localisation
>
> ├── variant_detection.py \# call_variants(), detect_stop_codons()
>
> ├── variant_annotation.py \# annotate_variant(), domain annotation
>
> ├── mutation_mapper.py \# KB lookup + KNOWN/LIKELY/NOVEL classification
>
> ├── mutation_confidence.py \# Weighted confidence scoring
>
> ├── novel_mutation_detector.py \# Novel mutation flagging + report
>
> ├── mutation_prioritizer.py \# Priority scoring + TSV generation
>
> ├── mechanism_classifier.py \# Gene + mutation → mechanism classification
>
> ├── mechanism_evidence.py \# MechanismObject aggregation
>
> ├── drug_association.py \# Drug-specific SIR associations
>
> ├── report_generator.py \# JSON/TSV/PDF outputs
>
> ├── db_writer.py \# SQLAlchemy persistence
>
> ├── celery_tasks.py
>
> └── tests/
>
> ├── fixtures/
>
> │ ├── synthetic_gyra_s83l.fasta
>
> │ ├── synthetic_rpob_s531l.fasta
>
> │ └── synthetic_mgrb_insertion.fasta
>
> ├── test_variant_detection.py
>
> ├── test_mutation_mapper.py
>
> ├── test_mechanism_classifier.py
>
> ├── test_confidence.py
>
> └── test_integration.py

**24.2 Implementation Checklist**

  -------------------------- ----------------------------------------------------------------------------- -------------- ---------------------------------------------------------------------------
  **Phase**                  **Deliverables**                                                              **Duration**   **Acceptance Criteria**

  1 --- Gene localisation    gene_localization.py; BLAST + NW pipeline                                     3 days         All 12 target genes located in reference genomes; identity ≥ 98%

  2 --- Variant calling      variant_detection.py; stop codon detection; frameshift detection              3 days         Known-answer tests pass for all 6 engineered mutations

  3 --- Annotation           variant_annotation.py; HGVS notation; domain classification                   2 days         gyrA S83L → p.Ser83Leu, c.248C\>T; QRDR domain flagged

  4 --- KB mapping           mutation_mapper.py; knowledgebase loader                                      2 days         Exact match recall = 100% on 50 known KB entries; NOVEL correctly flagged

  5 --- Novel + confidence   novel_mutation_detector.py, mutation_confidence.py, mutation_prioritizer.py   2 days         KNOWN_RESISTANCE scores ≥ 0.85; UNKNOWN scores ≤ 0.20

  6 --- Mechanism engine     mechanism_classifier.py, mechanism_evidence.py, drug_association.py           3 days         All 8 classification examples from Section 12.3 produce correct mechanism

  7 --- API + Celery         FastAPI routes, celery_tasks.py, progress tracking                            2 days         POST mutations → COMPLETED; POST mechanisms → determinants.json produced

  8 --- Nextflow + tests     DSL2 processes; full test suite; benchmarks                                   3 days         ≥ 95% unit coverage; 5 Mb genome \< 10 min total; PDF report renders
  -------------------------- ----------------------------------------------------------------------------- -------------- ---------------------------------------------------------------------------
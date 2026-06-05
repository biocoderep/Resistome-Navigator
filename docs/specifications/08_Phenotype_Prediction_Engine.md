# 08 — Phenotype Prediction Rule Engine

> **⚠️ Implementation Phase: Phase 3**
>
> Do not implement until mutation detection (Doc 07) is complete.
>
> **Prerequisites:** Docs 06 and 07 fully operational.

---

**PHENOTYPE PREDICTION**

**RULE ENGINE SPECIFICATION**

**PPRE --- Version 1.0**

**MODULE 1E --- AMR CHARACTERISATION ENGINE**

*S · I · R Prediction · EUCAST · CLSI · ECOFF · Module 2 Export*

Python · FastAPI · PostgreSQL · Celery · Nextflow DSL2

Version 1.0 --- CONFIDENTIAL --- Direct Implementation Ready

> **SECTION 1 --- PURPOSE AND SCOPE**

**1.1 Purpose**

The Phenotype Prediction Rule Engine (PPRE) is the biological inference layer of Module 1. It integrates all AMR evidence produced by the detection pipeline (acquired genes from Module 1C, chromosomal mutations and mechanism classifications from Module 1D) and applies a rule-based inference system to produce structured S/I/R predictions per antibiotic agent. Every prediction is accompanied by a traceable evidence chain, a human-readable explanation, and a confidence score.

**1.2 Core Principle**

> **No Unsupported Prediction:** Every S/I/R prediction must be backed by at least one tracked evidence record linking the prediction to a specific gene, mutation, or mechanism via an explicit rule. Predictions without evidence must be reported as NOT_TESTABLE or INSUFFICIENT_EVIDENCE --- never as Susceptible by default without explicit wild-type confirmation.

**1.3 Pipeline Position**

  --------------------------------- --------------------------------------------------------------------------------------------------------- ------------------------------------------------------
  **Input Source**                  **Data Provided**                                                                                         **Consumed By PPRE**

  Module 1C --- AMR Detection       AMRGeneResult objects with aro_accession, drug_class, mechanism_type, confidence                          Gene-based rule evaluation

  Module 1D --- Mutation Engine     AnnotatedVariant + ResistanceDeterminant objects with mutation_notation, sir_prediction, evidence_level   Mutation-based rule evaluation

  Module 1D --- Mechanism Engine    MechanismObject list with mechanism_code, supporting_genes, confidence                                    Mechanism-based rule evaluation

  Module 1A --- Genome Validation   confidence_cap (FULL / MEDIUM / LOW) from quality score                                                   Global confidence ceiling applied to all predictions
  --------------------------------- --------------------------------------------------------------------------------------------------------- ------------------------------------------------------

> **SECTION 2 --- BIOLOGICAL OBJECTIVES**

  ------------------------------- ------------------------------------------------ ------------------------------------------------------ -----------------------
  **Drug Class**                  **Representative Drugs**                         **Key Determinants**                                   **Clinical Priority**

  Beta-lactams (penicillins)      Ampicillin, Amoxicillin, Piperacillin            blaTEM, blaSHV, blaOXA; PBP mutations                  HIGH

  Beta-lactams (cephalosporins)   Cefazolin, Ceftriaxone, Cefepime                 blaCTX-M, blaSHV-12; AmpC derepression                 CRITICAL

  Beta-lactams (carbapenems)      Meropenem, Imipenem, Ertapenem                   blaKPC, blaNDM, blaOXA-48, blaVIM, blaIMP; OprD loss   CRITICAL

  Fluoroquinolones                Ciprofloxacin, Levofloxacin, Moxifloxacin        gyrA/B + parC/E mutations; qnr; aac(6\')-Ib-cr         CRITICAL

  Aminoglycosides                 Gentamicin, Tobramycin, Amikacin                 aac(3), aac(6\'), aph(3\'), ant(2\'\')                 HIGH

  Macrolides / MLSB               Azithromycin, Erythromycin, Clindamycin          ermA/B/C, mefA/E, 23S A2058G                           HIGH

  Tetracyclines                   Tetracycline, Doxycycline, Tigecycline           tetA/B/C/M/O; tet(X) for tigecycline                   MEDIUM

  Sulfonamides / Trimethoprim     Sulfamethoxazole, Trimethoprim, Co-trimoxazole   sul1/2/3, dfrA genes                                   MEDIUM

  Glycopeptides                   Vancomycin, Teicoplanin                          vanA/B/C/D/E                                           CRITICAL

  Polymyxins                      Colistin, Polymyxin B                            mcr-1--9, mgrB/pmrAB mutations                         CRITICAL

  Oxazolidinones                  Linezolid                                        23S rRNA G2576T, optrA, cfr                            HIGH

  Lipopeptides                    Daptomycin                                       mprF, dltA/B/C/D mutations (Gram-positive)             HIGH

  Folate inhibitors               Trimethoprim + SXT                               dfrA; thyA mutations (MTB context)                     MEDIUM

  Rifamycins                      Rifampicin                                       rpoB mutations                                         HIGH

  Other / Extensible              Future drugs via configuration                   rule_repository.json additions                         Varies
  ------------------------------- ------------------------------------------------ ------------------------------------------------------ -----------------------

> **SECTION 3 --- INPUT DATA MODEL AND KNOWLEDGE GRAPH**

**3.1 Knowledge Graph Architecture**

> ┌──────────────────────────────────────────────────────────────────┐
>
> │ RESISTANCE KNOWLEDGE GRAPH │
>
> │ │
>
> │ ┌──────────┐ confers_resistance_via ┌─────────────────────┐ │
>
> │ │ AMRGene │─────────────────────────►│ Mechanism │ │
>
> │ └────┬─────┘ └──────────┬──────────┘ │
>
> │ │ directly_affects │ │
>
> │ ▼ │ class_of │
>
> │ ┌──────────┐ ▼ │
>
> │ │ Drug │◄──────────────────────────────┌──────────────┐ │
>
> │ └────┬─────┘ confers_resistance_to │ MechClass │ │
>
> │ │ └──────────────┘ │
>
> │ ┌────▼─────┐ │
>
> │ │DrugClass │◄── blaCTX-M → beta-lactam → cephalosporin │
>
> │ └────┬─────┘ │
>
> │ │ has_predicted │
>
> │ ▼ │
>
> │ ┌──────────┐ supported_by ┌──────────────────────────────┐ │
>
> │ │ Phenotype│◄────────────────►│ Evidence (gene+mutation+mech)│ │
>
> │ └──────────┘ └──────────────────────────────┘ │
>
> │ │
>
> │ ┌──────────────┐ also feeds │
>
> │ │ Mutation │─────────────────────────────────────────────► │
>
> │ │ (RawVariant) │ → Mechanism → Drug → Phenotype │
>
> └───────────────────────────────────────────────────────────────────┘

**3.2 Input Consumption**

> \@dataclass
>
> class PredictionInput:
>
> sample_id: str
>
> species: str \| None
>
> assembly_quality: str \# EXCELLENT \| GOOD \| ACCEPTABLE \| POOR
>
> confidence_cap: str \# FULL \| MEDIUM \| LOW
>
> amr_genes: list\[\"AMRGeneResult\"\]
>
> mutations: list\[\"ResistanceDeterminant\"\]
>
> mechanisms: list\[\"MechanismObject\"\]
>
> breakpoint_source: str \# EUCAST \| CLSI; from project settings
>
> **SECTION 4 --- RULE ENGINE ARCHITECTURE**

**4.1 Architecture Diagram**

> ┌──────────────────────────────────────────────────────────────────┐
>
> │ RULE ENGINE ARCHITECTURE │
>
> │ │
>
> │ ┌──────────────────────────────────────────────────────────┐ │
>
> │ │ RULE REPOSITORY │ │
>
> │ │ rule_repository.json (versioned, hot-reloadable) │ │
>
> │ │ Gene Rules \| Mutation Rules \| Mechanism Rules \| Combo │ │
>
> │ └──────────────────────┬───────────────────────────────────┘ │
>
> │ │
>
> │ ┌──────────────────────▼───────────────────────────────────┐ │
>
> │ │ RULE EVALUATOR │ │
>
> │ │ gene_rule_engine.py │ mutation_rule_engine.py │ │
>
> │ │ mechanism_rule_engine.py │ combinatorial_rules.py │ │
>
> │ └──────────────────────┬───────────────────────────────────┘ │
>
> │ │ raw candidate predictions
>
> │ ┌──────────────────────▼───────────────────────────────────┐ │
>
> │ │ INFERENCE ENGINE │ │
>
> │ │ phenotype_inference.py │ inheritance_engine.py │ │
>
> │ └──────────────────────┬───────────────────────────────────┘ │
>
> │ │ conflicting candidates
>
> │ ┌──────────────────────▼───────────────────────────────────┐ │
>
> │ │ CONFLICT RESOLVER │ │
>
> │ │ conflict_resolution.py (R \> I \> S priority) │ │
>
> │ └──────────────────────┬───────────────────────────────────┘ │
>
> │ │ resolved SIR + evidence chain
>
> │ ┌──────────────────────▼───────────────────────────────────┐ │
>
> │ │ CONFIDENCE PROPAGATION ENGINE │ │
>
> │ │ confidence_propagation.py │ ecoff_engine.py │ │
>
> │ └──────────────────────┬───────────────────────────────────┘ │
>
> │ │ scored predictions
>
> │ ┌──────────────────────▼───────────────────────────────────┐ │
>
> │ │ EXPLANATION ENGINE │ │
>
> │ │ explanation_engine.py → human-readable justification │ │
>
> **SECTION 5 --- RULE DATABASE DESIGN**

**5.1 Rule Schema (rule_repository.json)**

> {
>
> \"schema_version\": \"1.0.0\",
>
> \"rules\": \[
>
> {
>
> \"rule_id\": \"RULE_GENE_BLACTXM_CEFTRIAXONE_001\",
>
> \"rule_name\": \"blaCTX-M family → Ceftriaxone Resistant\",
>
> \"rule_version\": \"1.0\",
>
> \"rule_type\": \"gene\", // gene \| mutation \| mechanism \| combinatorial
>
> \"drug\": \"ceftriaxone\",
>
> \"drug_class\": \"cephalosporin\",
>
> \"antibiotic_class\":\"beta-lactam\",
>
> \"condition\": {
>
> \"type\": \"gene_family_match\",
>
> \"gene_family\": \"CTX-M beta-lactamase\",
>
> \"hit_types\": \[\"Perfect\",\"Strict\"\],
>
> \"min_identity\": 90.0,
>
> \"min_coverage\": 80.0
>
> },
>
> \"action\": \"R\", // S \| I \| R \| NOT_TESTABLE
>
> \"evidence_level\": 1,
>
> \"confidence_weight\": 0.97,
>
> \"breakpoint_sources\": \[\"EUCAST\",\"CLSI\"\],
>
> \"organism_scope\": \"Enterobacterales\", // null = all organisms
>
> \"source\": \"CARD_ARO + EUCAST_v13\",
>
> \"pmids\": \[\"10234567\"\],
>
> \"status\": \"active\",
>
> \"created_at\": \"2025-01-01\",
>
> \"updated_at\": \"2025-06-01\"
>
> },
>
> {
>
> \"rule_id\": \"RULE_MUT_GYRA_S83L_CIPROFLOXACIN_001\",
>
> \"rule_type\": \"mutation\",
>
> \"drug\": \"ciprofloxacin\",
>
> \"drug_class\": \"fluoroquinolone\",
>
> \"condition\": {
>
> \"type\": \"mutation_exact\",
>
> \"gene\": \"gyrA\",
>
> \"protein_position\": 83,
>
> \"alt_amino_acid\": \"Leu\"
>
> },
>
> \"action\": \"I\", // single QRDR mutation → intermediate
>
> \"evidence_level\": 1,
>
> \"confidence_weight\": 0.90
>
> },
>
> {
>
> \"rule_id\": \"RULE_COMBO_GYRA_PARC_FQ_HIGH_001\",
>
> \"rule_type\": \"combinatorial\",
>
> \"drug_class\": \"fluoroquinolone\",
>
> \"condition\": {
>
> \"type\": \"all_of\",
>
> \"conditions\": \[
>
> {\"type\":\"mutation_exact\",\"gene\":\"gyrA\",\"protein_position\":83,\"alt_amino_acid\":\"Leu\"},
>
> {\"type\":\"mutation_domain\",\"gene\":\"parC\",\"domain\":\"QRDR\"}
>
> \]
>
> },
>
> \"action\": \"R\", // combination → high-level resistance
>
> \"evidence_level\": 1,
>
> \"confidence_weight\": 0.97
>
> }
>
> \]
>
> }

**5.2 Rule Type Taxonomy**

  ----------------------- -------------------------------------------------------- ------------------------------------------------------
  **Rule Type**           **Trigger Condition**                                    **Example**

  gene                    Specific gene name or gene family present at threshold   blaNDM-1 → carbapenem R

  gene_family             ARO gene family match (any member)                       CTX-M beta-lactamase family → 3GC R

  mutation_exact          Gene + protein position + specific alt amino acid        gyrA S83L → FQ I

  mutation_domain         Any mutation in named resistance domain                  Any QRDR gyrA mutation → FQ warning

  mutation_stop           Premature stop codon or frameshift in gene               mgrB stop → polymyxin R

  mechanism               Detected mechanism class (not gene-specific)             efflux_pump → multi-drug reduced susceptibility

  combinatorial all_of    ALL listed conditions must be true                       gyrA S83L AND parC QRDR mut → FQ high-level R

  combinatorial any_of    ANY listed condition triggers rule                       blaKPC OR blaNDM OR blaOXA-48 → carbapenem R

  combinatorial none_of   Rule fires only if conditions are absent                 FQ I only if no additional QRDR mutations

  organism_specific       Rule applies only to named organism group                mgrB disruption → colistin R (Enterobacterales only)
  ----------------------- -------------------------------------------------------- ------------------------------------------------------

> **SECTION 6 --- GENE-BASED RULE ENGINE**

**6.1 Implementation: gene_rule_engine.py**

> \"\"\"Gene-based phenotype rule evaluator --- Module 1E v1.0.0\"\"\"
>
> from dataclasses import dataclass
>
> from typing import Literal
>
> \@dataclass
>
> class CandidatePrediction:
>
> drug: str
>
> drug_class: str
>
> sir: Literal\[\"S\",\"I\",\"R\",\"NOT_TESTABLE\",\"INDETERMINATE\"\]
>
> rule_id: str
>
> evidence_type: str \# \"gene\" \| \"mutation\" \| \"mechanism\" \| \"combo\"
>
> evidence_name: str \# e.g. \"blaCTX-M-15\"
>
> confidence: float
>
> evidence_level: int
>
> class GeneRuleEngine:
>
> def \_\_init\_\_(self, rules: list\[dict\]):
>
> self.gene_rules = \[r for r in rules if r\[\"rule_type\"\] in (\"gene\",\"gene_family\")\]
>
> def evaluate(self, genes: list\[\"AMRGeneResult\"\]) -\> list\[CandidatePrediction\]:
>
> candidates = \[\]
>
> for gene in genes:
>
> for rule in self.gene_rules:
>
> if not self.\_organism_match(rule, gene): continue
>
> if self.\_condition_met(rule\[\"condition\"\], gene):
>
> candidates.append(CandidatePrediction(
>
> drug = rule\[\"drug\"\],
>
> drug_class = rule\[\"drug_class\"\],
>
> sir = rule\[\"action\"\],
>
> rule_id = rule\[\"rule_id\"\],
>
> evidence_type = \"gene\",
>
> evidence_name = gene.gene_name,
>
> confidence = rule\[\"confidence_weight\"\] \* gene.confidence_score,
>
> evidence_level= rule\[\"evidence_level\"\]))
>
> return candidates
>
> def \_condition_met(self, cond: dict, gene) -\> bool:
>
> if cond\[\"type\"\] == \"gene_family_match\":
>
> return (gene.gene_family == cond\[\"gene_family\"\]
>
> and gene.hit_type in cond.get(\"hit_types\", \[\"Perfect\",\"Strict\",\"Loose\"\])
>
> and gene.identity_pct \>= cond.get(\"min_identity\", 80.0)
>
> and gene.coverage_pct \>= cond.get(\"min_coverage\", 60.0))
>
> if cond\[\"type\"\] == \"gene_exact\":
>
> return gene.gene_name == cond\[\"gene_name\"\]

**6.2 Gene Rule Catalogue (excerpt)**

  ------------------------------------ ----------------------------- ---------------------------- --------- --------------
  **Rule ID**                          **Gene/Family**               **Drug(s)**                  **SIR**   **Evidence**

  RULE_GENE_BLANDM_CARBAPENEMS_001     blaNDM (any variant)          All carbapenems              R         1

  RULE_GENE_BLAKPC_CARBAPENEMS_001     blaKPC (any variant)          All carbapenems              R         1

  RULE_GENE_BLAOXA48_CARBAPENEMS_001   blaOXA-48 family              Meropenem, Ertapenem         R         1

  RULE_GENE_BLACTXM_CEFTRIAXONE_001    CTX-M beta-lactamase family   Ceftriaxone, Cefotaxime      R         1

  RULE_GENE_MCR1_COLISTIN_001          mcr-1                         Colistin, Polymyxin B        R         1

  RULE_GENE_VANA_VANCOMYCIN_001        vanA                          Vancomycin, Teicoplanin      R         1

  RULE_GENE_TETAB_TETRACYCLINE_001     tetA or tetB                  Tetracycline, Doxycycline    R         1

  RULE_GENE_SUL1_SULFONAMIDE_001       sul1, sul2, sul3              Sulfamethoxazole             R         1

  RULE_GENE_ERMABC_MACROLIDE_001       ermA, ermB, ermC              Erythromycin, Azithromycin   R         1

  RULE_GENE_TETM_TETRACYCLINE_001      tetM (ribosomal protection)   Tetracycline, Minocycline    R         1
  ------------------------------------ ----------------------------- ---------------------------- --------- --------------

> **SECTION 7 --- MUTATION-BASED RULE ENGINE**

**7.1 Implementation: mutation_rule_engine.py**

> class MutationRuleEngine:
>
> def \_\_init\_\_(self, rules: list\[dict\]):
>
> self.mut_rules = \[r for r in rules if r\[\"rule_type\"\].startswith(\"mutation\")\]
>
> def evaluate(self, mutations: list\[\"ResistanceDeterminant\"\]) -\> list\[CandidatePrediction\]:
>
> candidates = \[\]
>
> for mut in mutations:
>
> for rule in self.mut_rules:
>
> if self.\_mutation_matches(rule\[\"condition\"\], mut):
>
> \# Apply classification modifier: LIKELY → confidence × 0.85
>
> conf_mod = 1.0 if mut.classification == \"KNOWN_RESISTANCE\" else 0.85
>
> candidates.append(CandidatePrediction(
>
> drug=rule\[\"drug\"\], drug_class=rule\[\"drug_class\"\],
>
> sir=rule\[\"action\"\], rule_id=rule\[\"rule_id\"\],
>
> evidence_type=\"mutation\",
>
> evidence_name=mut.mutation_notation or mut.gene_name,
>
> confidence=rule\[\"confidence_weight\"\] \* mut.confidence_score \* conf_mod,
>
> evidence_level=rule\[\"evidence_level\"\]))
>
> return candidates

**7.2 Mutation Rule Catalogue (excerpt)**

  ----------------------------------- --------------------- ---------------------------- --------- ------------------------------------------------------------
  **Rule ID**                         **Mutation**          **Drug(s)**                  **SIR**   **Notes**

  RULE_MUT_GYRA_S83L_CIPRO_001        gyrA S83L             Ciprofloxacin                I         Single QRDR mutation → intermediate; needs parC for full R

  RULE_MUT_GYRA_D87N_CIPRO_001        gyrA D87N             Ciprofloxacin                I         Lower impact than S83L alone

  RULE_MUT_RPOB_S531L_RIFAMP_001      rpoB S531L            Rifampicin                   R         High-level resistance; most common RRDR mutation

  RULE_MUT_RPOB_H526Y_RIFAMP_001      rpoB H526Y            Rifampicin                   R         MTB RRDR mutation (D516V in some conventions)

  RULE_MUT_23SRNA_A2058G_AZITH_001    23S rRNA A2058G       Azithromycin, Erythromycin   R         Full macrolide resistance; N. gonorrhoeae context

  RULE_MUT_MGRB_STOP_COLISTIN_001     mgrB premature stop   Colistin                     R         Any LOF mutation in mgrB → polymyxin R

  RULE_MUT_MGRB_INSERT_COLISTIN_001   mgrB IS-insertion     Colistin                     R         IS-element insertion = functional loss

  RULE_MUT_RPSL_K43R_STREP_001        rpsL K43R             Streptomycin                 R         Ribosomal mutation → aminoglycoside R
  ----------------------------------- --------------------- ---------------------------- --------- ------------------------------------------------------------

> **SECTION 8 --- MECHANISM-BASED RULE ENGINE**

**8.1 Implementation: mechanism_rule_engine.py**

> class MechanismRuleEngine:
>
> def \_\_init\_\_(self, rules: list\[dict\]):
>
> self.mech_rules = \[r for r in rules if r\[\"rule_type\"\] == \"mechanism\"\]
>
> def evaluate(self, mechanisms: list\[\"MechanismObject\"\]) -\> list\[CandidatePrediction\]:
>
> candidates = \[\]
>
> for mech in mechanisms:
>
> for rule in self.mech_rules:
>
> if rule\[\"condition\"\]\[\"mechanism_code\"\] == mech.mechanism_code:
>
> for drug_class in mech.drug_classes:
>
> if rule.get(\"drug_class\") in (None, drug_class):
>
> candidates.append(CandidatePrediction(
>
> drug=rule.get(\"drug\",\"class-level\"),
>
> drug_class=drug_class, sir=rule\[\"action\"\],
>
> rule_id=rule\[\"rule_id\"\],
>
> evidence_type=\"mechanism\",
>
> evidence_name=mech.mechanism_name,
>
> confidence=rule\[\"confidence_weight\"\] \* mech.confidence,
>
> evidence_level=rule\[\"evidence_level\"\]))
>
> return candidates

**8.2 Mechanism Rule Catalogue**

  -------------------------------------------- ----------------- ------------------------------------------ ----------------------- ---------------------------------------------------------
  **Mechanism**                                **Rule Action**   **Drug Class**                             **Confidence Weight**   **Notes**

  antibiotic_inactivation (beta-lactamase)     R                 beta-lactam                                0.92                    Specific drug depends on beta-lactamase class (A/B/C/D)

  efflux_pump (RND family)                     I                 fluoroquinolone, tetracycline, macrolide   0.75                    Efflux alone rarely confers full R; raises MIC

  target_alteration (QRDR)                     I→R               fluoroquinolone                            0.85                    Degree depends on number of QRDR mutations

  target_protection (Qnr)                      I                 fluoroquinolone                            0.80                    Protection reduces activity; rarely standalone R

  target_replacement (vanHAX)                  R                 glycopeptide                               0.95                    D-Ala-D-Lac ligase fully replaces target

  membrane_remodeling (LPS mod)                R                 polymyxin                                  0.90                    LPS modification reduces colistin binding

  reduced_permeability (porin loss)            I                 carbapenem                                 0.70                    Synergistic with beta-lactamase; alone raises MIC

  enzymatic_modification (methyltransferase)   R                 macrolide, aminoglycoside                  0.88                    Methylation prevents drug binding to ribosome
  -------------------------------------------- ----------------- ------------------------------------------ ----------------------- ---------------------------------------------------------

> **SECTION 9 --- COMBINATORIAL RULE ENGINE**

**9.1 Implementation: combinatorial_rules.py**

> class CombinatorialRuleEngine:
>
> def \_\_init\_\_(self, rules: list\[dict\], gene_engine, mut_engine, mech_engine):
>
> self.combo_rules = \[r for r in rules if r\[\"rule_type\"\] == \"combinatorial\"\]
>
> self.gene_engine = gene_engine
>
> self.mut_engine = mut_engine
>
> self.mech_engine = mech_engine
>
> def evaluate(self, genes, mutations, mechanisms) -\> list\[CandidatePrediction\]:
>
> candidates = \[\]
>
> for rule in self.combo_rules:
>
> cond = rule\[\"condition\"\]
>
> if cond\[\"type\"\] == \"all_of\":
>
> if all(self.\_check(c, genes, mutations, mechanisms) for c in cond\[\"conditions\"\]):
>
> candidates.append(self.\_make_candidate(rule, genes, mutations))
>
> elif cond\[\"type\"\] == \"any_of\":
>
> if any(self.\_check(c, genes, mutations, mechanisms) for c in cond\[\"conditions\"\]):
>
> candidates.append(self.\_make_candidate(rule, genes, mutations))
>
> return candidates

**9.2 Key Combinatorial Rules**

  ---------------------------------- ---------------------------------------------------------- --------------------------------------- --------- -----------------------------------------------------
  **Rule ID**                        **Condition**                                              **Drug / Class**                        **SIR**   **Clinical Basis**

  RULE_COMBO_GYRA_PARC_FQ_001        gyrA QRDR mutation AND parC QRDR mutation                  All fluoroquinolones                    R         Double-step resistance; MIC \> 4 mg/L ciprofloxacin

  RULE_COMBO_CTX_OXA_BL_001          CTX-M family AND OXA-1                                     Ceftriaxone + piperacillin/tazobactam   R         OXA-1 inhibits tazobactam; combined with ESBL

  RULE_COMBO_NDM_OXA_CARB_001        blaNDM OR blaOXA-48 OR blaVIM OR blaKPC (any_of)           All carbapenems                         R         Any class B or A carbapenemase → carbapenem R

  RULE_COMBO_EFFLUX_PORIN_CARB_001   efflux_pump mechanism AND reduced_permeability mechanism   Carbapenems                             I→R       Dual mechanism → synergistic MIC elevation

  RULE_COMBO_VANA_VANB_GLYCO_001     vanA OR vanB (any_of)                                      Vancomycin                              R         Either VanA or VanB cluster sufficient for Van R

  RULE_COMBO_TETM_TETX_TIG_001       tetM AND tet(X)                                            Tigecycline                             R         tet(X) enzymatic inactivation overrides protection
  ---------------------------------- ---------------------------------------------------------- --------------------------------------- --------- -----------------------------------------------------

> **SECTION 10 --- HIERARCHICAL RULE INHERITANCE**

**10.1 Inheritance Hierarchy**

> Drug Class Rule (most general)
>
> └── Drug Rule (specific antibiotic)
>
> └── Species Rule (organism-specific)
>
> └── Isolate Rule (override for specific isolate)

**10.2 Implementation: inheritance_engine.py**

> class InheritanceEngine:
>
> \"\"\"Resolves rule inheritance; child rules override parent class rules.\"\"\"
>
> def resolve(self, candidates: list\[CandidatePrediction\],
>
> drug: str, drug_class: str,
>
> organism: str \| None) -\> list\[CandidatePrediction\]:
>
> \"\"\"
>
> Priority order (highest first):
>
> 1\. Organism-specific drug rule
>
> 2\. Drug-specific rule (no organism restriction)
>
> 3\. Drug class rule
>
> 4\. Mechanism class rule (most general)
>
> \"\"\"
>
> drug_specific = \[c for c in candidates if c.drug == drug
>
> and (not hasattr(c,\"organism\") or c.organism == organism)\]
>
> class_level = \[c for c in candidates if c.drug != drug
>
> and c.drug_class == drug_class\]
>
> return drug_specific or class_level
>
> **SECTION 11 --- CONFLICT RESOLUTION ENGINE**

**11.1 Conflict Resolution Rules**

When multiple rules produce different SIR predictions for the same drug, the Conflict Resolution Engine applies the following priority order:

  -------------- -------------------------------------------------------------------- ----------------------------------------------------------------------------------------
  **Priority**   **Rule**                                                             **Rationale**

  1st            Resistant (R) wins over Intermediate (I) or Susceptible (S)          Clinical safety: never under-call resistance; false negatives are clinically dangerous

  2nd            Intermediate (I) wins over Susceptible (S)                           Intermediate has clinical significance; S may require higher dose confirmation

  3rd            Higher evidence_level rule wins among same SIR                       Evidence level 1 (definitive) overrides level 4 (preliminary)

  4th            Higher confidence_score wins among same SIR and evidence level       Quantitative tiebreaker

  5th            Combinatorial rule wins over single-determinant rule for same drug   Combinatorial rules are more specific and higher priority by design
  -------------- -------------------------------------------------------------------- ----------------------------------------------------------------------------------------

**11.2 Implementation: conflict_resolution.py**

> from functools import reduce
>
> SIR_PRIORITY = {\"R\": 3, \"I\": 2, \"S\": 1, \"INDETERMINATE\": 0, \"NOT_TESTABLE\": -1}
>
> def resolve_conflicts(candidates: list\[CandidatePrediction\],
>
> drug: str) -\> \"ResolvedPrediction\":
>
> \"\"\"Select winning SIR and track all evidence.\"\"\"
>
> drug_candidates = \[c for c in candidates if c.drug == drug or c.drug == \"class-level\"\]
>
> if not drug_candidates:
>
> return ResolvedPrediction(drug=drug, sir=\"NOT_TESTABLE\", candidates=\[\])
>
> \# Sort by SIR priority desc, then evidence_level asc, then confidence desc
>
> ranked = sorted(drug_candidates,
>
> key=lambda c: (-SIR_PRIORITY\[c.sir\], c.evidence_level, -c.confidence))
>
> winner = ranked\[0\]
>
> all_evidence = ranked \# all candidates kept for explanation
>
> conflict_flag = len({c.sir for c in ranked}) \> 1
>
> return ResolvedPrediction(
>
> drug=drug, sir=winner.sir,
>
> confidence=winner.confidence,
>
> winning_rule=winner.rule_id,
>
> all_evidence=all_evidence, has_conflict=conflict_flag)
>
> **SECTION 12 --- CONFIDENCE PROPAGATION ENGINE**

**12.1 Composite Confidence Formula**

Final prediction confidence C_pred = min(C_evidence × C_rule × C_genome, C_cap)

  ------------------------- -------------------- --------------------------------------------------------------------------------------- --------------
  **Factor**                **Symbol**           **Source**                                                                              **Range**

  Evidence confidence       C_evidence           Max confidence score among winning evidence records                                     0.0--1.0

  Rule confidence weight    C_rule               rule\[\"confidence_weight\"\] from rule repository                                      0.0--1.0

  Genome quality cap        C_cap                confidence_cap from Module 1A (FULL=1.0; MEDIUM=0.75; LOW=0.50)                         0.5--1.0

  Evidence level modifier   Embedded in C_rule   rule\[\"evidence_level\"\] → weight decay: L1=1.0, L2=0.90, L3=0.75, L4=0.55, L5=0.35   0.35--1.0
  ------------------------- -------------------- --------------------------------------------------------------------------------------- --------------

**12.2 Implementation: confidence_propagation.py**

> EVIDENCE_LEVEL_MODIFIER = {1: 1.00, 2: 0.90, 3: 0.75, 4: 0.55, 5: 0.35}
>
> GENOME_CAP = {\"FULL\": 1.0, \"MEDIUM\": 0.75, \"LOW\": 0.50}
>
> def propagate_confidence(resolved: \"ResolvedPrediction\",
>
> genome_quality: str,
>
> breakpoint_source: str) -\> dict:
>
> c_evidence = resolved.confidence
>
> ev_mod = EVIDENCE_LEVEL_MODIFIER.get(resolved.winning_rule_evidence_level, 0.5)
>
> c_rule = resolved.winning_rule_weight \* ev_mod
>
> c_cap = GENOME_CAP.get(genome_quality, 0.50)
>
> c_final = min(c_evidence \* c_rule, c_cap)
>
> tier = \"HIGH\" if c_final\>=0.80 else \"MEDIUM\" if c_final\>=0.55 else \"LOW\"
>
> return {\"confidence\": round(c_final, 4), \"tier\": tier, \"cap_applied\": c_final \< c_evidence \* c_rule}
>
> **SECTION 13 --- PHENOTYPE INFERENCE ENGINE**

**13.1 Implementation: phenotype_inference.py**

> \"\"\"Phenotype prediction orchestrator --- Module 1E v1.0.0\"\"\"
>
> class PhenotypeInferenceEngine:
>
> def \_\_init\_\_(self, rule_repo: RuleRepository,
>
> breakpoint_adapter,
>
> confidence_propagator):
>
> self.gene_engine = GeneRuleEngine(rule_repo.gene_rules)
>
> self.mut_engine = MutationRuleEngine(rule_repo.mutation_rules)
>
> self.mech_engine = MechanismRuleEngine(rule_repo.mechanism_rules)
>
> self.combo_engine = CombinatorialRuleEngine(rule_repo.combo_rules, \...)
>
> self.resolver = ConflictResolutionEngine()
>
> self.bp_adapter = breakpoint_adapter
>
> self.conf_prop = confidence_propagator
>
> def predict(self, inp: PredictionInput) -\> list\[\"PhenotypePrediction\"\]:
>
> \# 1. Evaluate all rule types
>
> candidates = (
>
> self.gene_engine.evaluate(inp.amr_genes) +
>
> self.mut_engine.evaluate(inp.mutations) +
>
> self.mech_engine.evaluate(inp.mechanisms) +
>
> self.combo_engine.evaluate(inp.amr_genes, inp.mutations, inp.mechanisms)
>
> )
>
> \# 2. Get all drugs with at least one candidate
>
> drugs = {c.drug for c in candidates}
>
> \# 3. Resolve conflicts per drug
>
> predictions = \[\]
>
> for drug in drugs:
>
> resolved = self.resolver.resolve(candidates, drug)
>
> conf = self.conf_prop.propagate(resolved, inp.assembly_quality, inp.breakpoint_source)
>
> bp_info = self.bp_adapter.get_breakpoint(drug, inp.species, inp.breakpoint_source)
>
> pred = PhenotypePrediction(
>
> sample_id=inp.sample_id, drug=drug,
>
> drug_class=resolved.drug_class, predicted_sir=resolved.sir,
>
> confidence_score=conf\[\"confidence\"\], confidence_tier=conf\[\"tier\"\],
>
> breakpoint_source=inp.breakpoint_source, breakpoint_version=bp_info.version,
>
> \...)
>
> predictions.append(pred)
>
> return predictions
>
> **SECTION 14 --- EUCAST AND CLSI INTEGRATION**

**14.1 EUCAST Adapter: eucast_adapter.py**

> \@dataclass
>
> class BreakpointRecord:
>
> drug: str
>
> species_group: str
>
> s_threshold: float \| None \# MIC ≤ S threshold → Susceptible
>
> r_threshold: float \| None \# MIC \> R threshold → Resistant
>
> i_range: str \| None \# \"S \< MIC ≤ R\" description
>
> version: str \# e.g. \"EUCAST v13.0\"
>
> source: str \# EUCAST \| CLSI
>
> notes: str \| None \# expert rule references
>
> class EUCASTAdapter:
>
> def \_\_init\_\_(self, bp_table_path: Path, version: str):
>
> self.version = version
>
> self.table = self.\_load(bp_table_path)
>
> def get_breakpoint(self, drug: str, species: str \| None,
>
> organism_group: str \| None = None) -\> BreakpointRecord \| None:
>
> \# Try species-specific first, then organism group, then general
>
> for scope in \[species, organism_group, \"All streptococci\", \"Enterobacterales\", None\]:
>
> bp = self.table.get((drug.lower(), scope))
>
> if bp: return bp
>
> return None

**14.2 EUCAST Expert Rules Integration**

EUCAST Expert Rules provide organism-specific conditional interpretive rules that override standard breakpoints. These are stored as additional rule entries in rule_repository.json with rule_type=\"eucast_expert\" and linked to the relevant breakpoint version.

  ---------------------------------------------- -------------------------------------- -----------------------------------------------
  **EUCAST Expert Rule**                         **Condition**                          **Override Action**

  Salmonella + fluoroquinolone (EUCAST ER 3.3)   gyrA mutation detected in Salmonella   Ciprofloxacin = R regardless of MIC

  K. pneumoniae + carbapenem (EUCAST ER 1.1)     blaKPC or blaNDM detected              All carbapenems = R; report for expert review

  Enterococcus + glycopeptide (EUCAST ER 7.1)    vanA or vanB detected                  Vancomycin = R (vanA); R/I (vanB)

  MRSA + beta-lactams (EUCAST ER 6.1)            mecA or mecC detected                  All beta-lactams except ceftaroline = R
  ---------------------------------------------- -------------------------------------- -----------------------------------------------

> **SECTION 15 --- ECOFF ENGINE**

**15.1 Mathematical Foundation**

> **ECOFF = μ + 3σ where μ = mean(log₂ MIC) and σ = SD(log₂ MIC)**

The Epidemiological Cut-off Value (ECOFF) separates wild-type (WT) populations from non-wild-type isolates. Isolates with MIC above ECOFF have acquired mechanisms reducing susceptibility, even if they fall below clinical breakpoints.

**15.2 Implementation: ecoff_engine.py**

> \"\"\"ECOFF wild-type threshold engine --- Module 1E v1.0.0\"\"\"
>
> import numpy as np
>
> from scipy import stats
>
> def compute_ecoff(log2_mic_values: list\[float\],
>
> method: str = \"normal\") -\> dict:
>
> \"\"\"
>
> Compute ECOFF from log2 MIC distribution.
>
> Reference: EUCAST Technical Note on ECOFF (2012)
>
> \"\"\"
>
> a = np.array(log2_mic_values)
>
> mu = float(np.mean(a))
>
> sigma = float(np.std(a, ddof=1))
>
> ecoff_log2 = mu + 3 \* sigma
>
> ecoff_mic = 2 \*\* ecoff_log2
>
> return {
>
> \"ecoff_log2\": round(ecoff_log2, 3),
>
> \"ecoff_mic\": round(ecoff_mic, 3),
>
> \"mu_log2\": round(mu, 3),
>
> \"sigma_log2\": round(sigma, 3),
>
> \"n\": len(a),
>
> \"method\": method}
>
> def classify_vs_ecoff(observed_log2_mic: float, ecoff_log2: float) -\> str:
>
> return \"non_wild_type\" if observed_log2_mic \> ecoff_log2 else \"wild_type\"
>
> **SECTION 16 --- HILL EQUATION ENGINE**

**16.1 Mathematical Foundation**

> **E = E₀ + (Emax × C\^H) / (EC₅₀\^H + C\^H)**

Where E = observed effect; E₀ = baseline effect (no drug); Emax = maximum drug effect; C = drug concentration; EC₅₀ = concentration at half-maximum effect; H = Hill coefficient (steepness of dose-response curve). Used for MIC-to-response modelling and PK/PD integration.

**16.2 Implementation: hill_equation_engine.py**

> \"\"\"Hill equation dose-response model --- Module 1E v1.0.0\"\"\"
>
> import numpy as np
>
> from scipy.optimize import curve_fit
>
> def hill_response(c: float, e0: float, emax: float,
>
> ec50: float, h: float) -\> float:
>
> \"\"\"Compute drug effect at concentration c using Hill equation.\"\"\"
>
> return e0 + (emax \* c\*\*h) / (ec50\*\*h + c\*\*h)
>
> def fit_hill_curve(concentrations: list\[float\],
>
> effects: list\[float\]) -\> dict:
>
> \"\"\"Fit Hill equation parameters to observed concentration-effect data.\"\"\"
>
> popt, pcov = curve_fit(
>
> lambda c, emax, ec50, h: hill_response(c, 0, emax, ec50, h),
>
> concentrations, effects,
>
> p0=\[max(effects), np.median(concentrations), 1.0\],
>
> bounds=(\[0, 1e-6, 0.1\], \[np.inf, np.inf, 10.0\])
>
> )
>
> emax, ec50, h = popt
>
> return {
>
> \"emax\": round(float(emax), 4),
>
> \"ec50\": round(float(ec50), 4),
>
> \"hill_coefficient\": round(float(h), 4),
>
> \"r_squared\": \_r_squared(concentrations, effects, popt)
>
> }
>
> **SECTION 17 --- EXPLANATION ENGINE**

**17.1 Implementation: explanation_engine.py**

> \"\"\"Human-readable prediction explanation --- Module 1E v1.0.0\"\"\"
>
> def generate_explanation(prediction: \"PhenotypePrediction\") -\> str:
>
> lines = \[\]
>
> lines.append(f\"Predicted: {prediction.predicted_sir} ({\_sir_label(prediction.predicted_sir)})\")
>
> lines.append(f\"Drug: {prediction.drug} ({prediction.drug_class})\")
>
> lines.append(f\"Confidence: {prediction.confidence_tier} ({prediction.confidence_score:.3f})\")
>
> lines.append(\"\")
>
> lines.append(\"Supporting Evidence:\")
>
> for ev in prediction.supporting_evidence:
>
> if ev.evidence_type == \"gene\":
>
> lines.append(f\" ▸ Gene: {ev.evidence_name} \| Identity: {ev.identity_pct:.1f}% \| Coverage: {ev.coverage_pct:.1f}% \| Hit: {ev.hit_type}\")
>
> elif ev.evidence_type == \"mutation\":
>
> lines.append(f\" ▸ Mutation: {ev.evidence_name} \| Classification: {ev.classification} \| Evidence level: {ev.evidence_level}\")
>
> elif ev.evidence_type == \"mechanism\":
>
> lines.append(f\" ▸ Mechanism: {ev.evidence_name} (confidence: {ev.confidence:.3f})\")
>
> if prediction.has_conflict:
>
> lines.append(\"\")
>
> lines.append(\"Note: Conflicting evidence was detected. Resistance call takes priority (R \> I \> S).\")
>
> return \"\\n\".join(lines)

**17.2 Explanation Example Output**

> **Example:** Predicted: R (Resistant) \| Drug: Ceftriaxone (cephalosporin) \| Confidence: HIGH (0.942) \| Supporting Evidence: Gene: blaCTX-M-15 \| Identity: 100.0% \| Coverage: 100.0% \| Hit: Perfect \| Mechanism: Antibiotic Inactivation (confidence: 0.971) \| Breakpoint: EUCAST v13.0; S ≤ 1 mg/L, R \> 2 mg/L
>
> **SECTION 18 --- PREDICTION OBJECT MODEL**

**18.1 PhenotypePrediction Dataclass**

> \@dataclass
>
> class PhenotypePrediction:
>
> prediction_id: str \# UUID
>
> sample_id: str
>
> drug: str \# e.g. \"ceftriaxone\"
>
> drug_class: str \# e.g. \"cephalosporin\"
>
> antibiotic_class: str \# e.g. \"beta-lactam\"
>
> predicted_sir: str \# S \| I \| R \| NOT_TESTABLE \| INDETERMINATE
>
> confidence_score: float
>
> confidence_tier: str \# HIGH \| MEDIUM \| LOW
>
> breakpoint_source: str \# EUCAST \| CLSI
>
> breakpoint_version: str
>
> is_not_testable: bool
>
> has_conflict: bool
>
> \# Evidence
>
> supporting_genes: list\[str\]
>
> supporting_mutations:list\[str\]
>
> supporting_mechanisms:list\[str\]
>
> supporting_rules: list\[str\] \# rule_ids that fired
>
> all_candidates: list\[CandidatePrediction\] \# full evidence chain
>
> \# Explanation
>
> explanation: str \# human-readable; from explanation_engine
>
> **SECTION 19 --- MODULE 2 EXPORT ENGINE**

**19.1 module2_input.csv Schema**

> \# Header row:
>
> sample_id, isolate_name, species, antibiotic, antibiotic_class, drug_class,
>
> predicted_sir, confidence_score, confidence_tier,
>
> amr_gene, gene_aro_accession, gene_identity_pct, gene_coverage_pct, gene_hit_type,
>
> mutation_notation, mutation_classification, mutation_evidence_level,
>
> mechanism_code, mechanism_name,
>
> supporting_rules, breakpoint_source, breakpoint_version,
>
> explanation, assembly_quality, schema_version

**19.2 Implementation: module2_export.py**

> import csv
>
> from pathlib import Path
>
> SCHEMA_VERSION = \"1.0.0\"
>
> def export_module2_csv(predictions: list\[\"PhenotypePrediction\"\],
>
> sample_meta: dict, out_path: Path) -\> int:
>
> \"\"\"Export predictions to module2_input.csv. Returns row count.\"\"\"
>
> rows = \[\]
>
> for pred in predictions:
>
> \# One row per gene+mutation combo per prediction
>
> gene_entries = pred.supporting_genes or \[\"\"\]
>
> mut_entries = pred.supporting_mutations or \[\"\"\]
>
> for gene in gene_entries:
>
> for mutation in mut_entries:
>
> rows.append({
>
> \"sample_id\": sample_meta\[\"sample_id\"\],
>
> \"isolate_name\": sample_meta\[\"isolate_name\"\],
>
> \"species\": sample_meta\[\"species\"\] or \"\",
>
> \"antibiotic\": pred.drug,
>
> \"antibiotic_class\":pred.antibiotic_class,
>
> \"drug_class\": pred.drug_class,
>
> \"predicted_sir\": pred.predicted_sir,
>
> \"confidence_score\":pred.confidence_score,
>
> \"confidence_tier\": pred.confidence_tier,
>
> \"amr_gene\": gene,
>
> \"mutation_notation\":mutation,
>
> \"mechanism_code\": \";\".join(pred.supporting_mechanisms),
>
> \"supporting_rules\":\";\".join(pred.supporting_rules),
>
> \"breakpoint_source\":pred.breakpoint_source,
>
> \"explanation\": pred.explanation\[:500\],
>
> \"schema_version\": SCHEMA_VERSION
>
> })
>
> with open(out_path, \"w\", newline=\"\") as f:
>
> writer = csv.DictWriter(f, fieldnames=rows\[0\].keys())
>
> writer.writeheader(); writer.writerows(rows)
>
> return len(rows)
>
> **SECTION 20 --- DATABASE DESIGN**

  -------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------- -----------------------------------------------------------------
  **Table**                        **Key Columns**                                                                                                                                                   **Notes**

  phenotype_predictions            id, sample_id, job_id, drug, drug_class, predicted_sir, confidence_score, confidence_tier, breakpoint_source, breakpoint_version, is_not_testable, has_conflict   Core prediction table; one row per drug per sample per job

  prediction_rules (reference)     id, rule_id, rule_name, rule_version, drug, drug_class, rule_type, condition_json, action, evidence_level, confidence_weight, status                              Versioned rule repository in DB; sync from rule_repository.json

  prediction_evidence (junction)   id, prediction_id (FK), evidence_type, evidence_id (UUID to gene/mutation/mechanism), evidence_name, rule_id (FK), contribution_weight                            Full evidence chain per prediction

  prediction_explanations          id, prediction_id (FK), explanation_text, explanation_version                                                                                                     Human-readable explanations; separate table for size

  module2_exports                  id, sample_id, job_id, schema_version, storage_path, row_count, exported_at                                                                                       Tracks every module2_input.csv export for reproducibility
  -------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------- -----------------------------------------------------------------

**20.1 prediction_evidence SQL**

> CREATE TABLE prediction_evidence (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> prediction_id UUID NOT NULL REFERENCES phenotype_predictions(id) ON DELETE CASCADE,
>
> evidence_type VARCHAR(30) NOT NULL, \-- gene \| mutation \| mechanism \| combo
>
> evidence_id UUID NOT NULL, \-- FK to amr_genes, mutations, or mechanisms
>
> evidence_name VARCHAR(200),
>
> rule_id VARCHAR(100),
>
> contribution_weight NUMERIC(5,4),
>
> is_winning_evidence BOOLEAN DEFAULT FALSE,
>
> notes TEXT
>
> );
>
> **SECTION 21 --- FASTAPI SERVICE DESIGN**

  ------------ -------------------------------------------------- ------------------------------------------ ------------------------------------------
  **Method**   **Path**                                           **Response**                               **Description**

  POST         /api/v1/module1/predict                            202 {job_id}                               Submit phenotype prediction job; async

  GET          /api/v1/module1/predict/{job_id}                   200 {status, progress_pct, current_step}   Poll job status

  GET          /api/v1/module1/predict/{job_id}/results           200 {predictions\[\]}                      Full S/I/R predictions with evidence

  GET          /api/v1/module1/predict/{job_id}/results/summary   200 {by_drug_class{}}                      Resistance profile grouped by drug class

  GET          /api/v1/module1/predict/{job_id}/explanations      200 {explanations\[\]}                     Human-readable explanations per drug

  GET          /api/v1/module1/predict/{job_id}/module2-export    302 redirect                               Download module2_input.csv

  GET          /api/v1/samples/{id}/predictions                   200 {predictions\[\], pagination}          Latest predictions for a sample
  ------------ -------------------------------------------------- ------------------------------------------ ------------------------------------------

**21.1 Prediction Request Schema**

> class PhenotypePredictionRequest(BaseModel):
>
> model_config = ConfigDict(strict=True)
>
> sample_id: UUID
>
> job_ids: dict\[str, UUID\] = {}
>
> \# Optional: pin job IDs from Module 1C/1D for reproducibility
>
> \# {amr_detection: UUID, mutation_detection: UUID, mechanism_classification: UUID}
>
> breakpoint_source: Literal\[\"EUCAST\",\"CLSI\"\] = \"EUCAST\"
>
> breakpoint_version: str \| None = None \# defaults to active version
>
> generate_module2_export: bool = True
>
> **SECTION 22 --- CELERY TASK DESIGN**

**22.1 Phenotype Prediction Task**

> \@celery.task(bind=True, name=\"module1.phenotype_predict\",
>
> max_retries=3, soft_time_limit=1800, time_limit=2100)
>
> def phenotype_prediction_task(self, job_id: str, config: dict) -\> dict:
>
> engine = PhenotypeInferenceEngine(\...)
>
> result = engine.predict(inp, progress_cb=lambda p,s: \...)

**22.2 Progress Steps**

  ------------------------ ---------------- -------------------------------------------------------------------
  **Step**                 **Progress %**   **Description**

  LOADING_EVIDENCE         0--10            Retrieve AMR genes, mutations, mechanisms from DB for this sample

  GENE_RULE_EVAL           10--30           Evaluate all gene-based rules

  MUTATION_RULE_EVAL       30--50           Evaluate all mutation-based rules

  MECHANISM_RULE_EVAL      50--60           Evaluate mechanism-based rules

  COMBINATORIAL_EVAL       60--70           Evaluate all combinatorial rules

  INHERITANCE_RESOLUTION   70--74           Apply hierarchical inheritance

  CONFLICT_RESOLUTION      74--80           Resolve conflicting SIR candidates per drug

  CONFIDENCE_PROPAGATION   80--86           Apply confidence formula + genome cap

  BREAKPOINT_LOOKUP        86--90           EUCAST/CLSI breakpoint enrichment

  EXPLANATION_GENERATION   90--95           Generate human-readable explanations

  MODULE2_EXPORT           95--98           Write module2_input.csv; store in object storage

  REPORT_GENERATION        98--100          JSON/TSV/PDF outputs; DB persistence
  ------------------------ ---------------- -------------------------------------------------------------------

> **SECTION 23 --- NEXTFLOW DSL2 PROCESS DESIGN**
>
> process PHENOTYPE_PREDICTION {
>
> tag \"\${meta.sample_id}\"
>
> label \"process_low\"
>
> cpus 2; memory \"4 GB\"; time \"20.min\"
>
> container \"amr-platform/phenotype-predictor:1.0.0\"
>
> input:
>
> tuple val(meta), path(amr_genes_json) // from Module 1C
>
> tuple val(meta), path(determinants_json) // ResistanceDeterminants from Module 1D
>
> path rule_repository_json
>
> path eucast_breakpoints_tsv
>
> path clsi_breakpoints_tsv
>
> output:
>
> tuple val(meta), path(\"phenotype_prediction.json\"), emit: prediction_json
>
> tuple val(meta), path(\"phenotype_predictions.tsv\"), emit: prediction_tsv
>
> tuple val(meta), path(\"prediction_explanations.tsv\"), emit: explanations
>
> tuple val(meta), path(\"confidence_scores.json\"), emit: conf_scores
>
> tuple val(meta), path(\"module2_input.csv\"), emit: module2_export
>
> tuple val(meta), path(\"phenotype_prediction_report.pdf\"), emit: pdf_report
>
> script:
>
> \"\"\"
>
> phenotype-predict \\
>
> \--amr-genes \${amr_genes_json} \\
>
> \--determinants \${determinants_json} \\
>
> \--rules \${rule_repository_json} \\
>
> \--eucast \${eucast_breakpoints_tsv} \\
>
> \--clsi \${clsi_breakpoints_tsv} \\
>
> \--breakpoint-source \${meta.breakpoint_source ?: \"EUCAST\"} \\
>
> \--output-dir .
>
> \"\"\"
>
> }
>
> **SECTION 24 --- TESTING STRATEGY**

  ------------------------------ ------------------------ ----------------------------------------------------------------------------------------- ----------------------------------------------------------------------------------
  **Test Type**                  **Framework**            **Scope**                                                                                 **Key Assertions**

  Unit Tests                     pytest                   Individual rule evaluators, conflict resolver, confidence formula, ECOFF, Hill equation   ≥ 95% coverage; known-answer tests for all 5 rule types

  Rule Engine Tests              pytest + fixtures        All rules in rule_repository.json against engineered inputs                               100% rule coverage; every rule fires correctly on designed input; no false fires

  Conflict Resolution Tests      pytest                   Conflicting candidate sets: R vs I; R vs S; multiple rules same drug                      R always wins; correct winning rule selected; all evidence preserved

  Confidence Tests               pytest                   Confidence formula with various evidence and genome quality inputs                        FULL cap ≥ MEDIUM cap; HIGH tier only when score ≥ 0.80

  EUCAST/CLSI Tests              pytest                   Breakpoint lookup for all supported species/drug combinations                             Correct breakpoint returned; version tracked; NOT_TESTABLE when no breakpoint

  Reference Dataset Validation   pytest + NCBI fixtures   MDR K. pneumoniae, MRSA, FQ-resistant E. coli, VRE                                        Sensitivity ≥ 0.90; specificity ≥ 0.90 against clinically confirmed phenotypes

  Regression Tests               pytest snapshots         10 reference genomes; predictions must be identical across versions ± 0.001 confidence    Zero prediction changes without explicit rule/version update

  Performance Tests              pytest-benchmark         Single isolate full pipeline                                                              Prediction engine \< 30 seconds per isolate; module2 export \< 5 seconds
  ------------------------------ ------------------------ ----------------------------------------------------------------------------------------- ----------------------------------------------------------------------------------

**24.1 Reference Phenotype Validation Isolates**

  ----------------------- ---------------------- ---------------------------------- ------------------------------------------------------------------
  **Accession**           **Species**            **Phenotype Profile**              **Expected Key Predictions**

  GCF_001457655.1         K. pneumoniae KPNIH1   KPC-2, TEM-1, SHV-18, AAC(3)-IV    Carbapenem R; Ceftriaxone R; Gentamicin R; Ciprofloxacin unknown

  Synthetic MRSA genome   S. aureus              mecA, vanA                         Oxacillin R; Vancomycin R (if vanA); all BL except ceftaroline R

  FQ-resistant E. coli    E. coli                gyrA S83L + parC S80I + blaTEM-1   Ciprofloxacin R; Ceftriaxone I; Ampicillin R

  VRE isolate             E. faecium             vanA + ampicillin-resistant pbp5   Vancomycin R; Teicoplanin R; Ampicillin R

  Colistin-resistant KP   K. pneumoniae          mgrB truncation + blaKPC           Colistin R; all carbapenems R
  ----------------------- ---------------------- ---------------------------------- ------------------------------------------------------------------

> **SECTION 25 --- IMPLEMENTATION PLAN**

**25.1 Python Package Structure**

> phenotype_engine/
>
> ├── \_\_init\_\_.py \# PhenotypeInferenceEngine orchestrator
>
> ├── cli.py \# phenotype-predict CLI entrypoint
>
> ├── result_models.py \# CandidatePrediction, ResolvedPrediction, PhenotypePrediction
>
> ├── rule_repository.py \# Load, validate, hot-reload rule_repository.json
>
> ├── rules/
>
> │ ├── rule_repository.json \# Versioned rule definitions
>
> │ ├── gene_rule_engine.py
>
> │ ├── mutation_rule_engine.py
>
> │ ├── mechanism_rule_engine.py
>
> │ └── combinatorial_rules.py
>
> ├── inference/
>
> │ ├── phenotype_inference.py \# Orchestrator: all rules → per-drug prediction
>
> │ ├── inheritance_engine.py
>
> │ ├── conflict_resolution.py
>
> │ └── confidence_propagation.py
>
> ├── breakpoints/
>
> │ ├── eucast_adapter.py
>
> │ ├── clsi_adapter.py
>
> │ └── breakpoint_tables/ \# EUCAST v13.0, CLSI M100-S33 CSV files
>
> ├── mathematical/
>
> │ ├── ecoff_engine.py
>
> │ └── hill_equation_engine.py
>
> ├── explanation_engine.py
>
> ├── module2_export.py
>
> ├── report_generator.py
>
> ├── db_writer.py
>
> ├── celery_tasks.py
>
> └── tests/
>
> ├── fixtures/ \# Reference genome FASTAs + expected phenotype tables
>
> ├── test_gene_rules.py
>
> ├── test_mutation_rules.py
>
> ├── test_combinatorial.py
>
> ├── test_conflict_resolution.py
>
> ├── test_confidence.py
>
> ├── test_eucast_adapter.py
>
> └── test_integration.py

**25.2 Implementation Checklist**

  --------------------------------- ------------------------------------------------------------------------------ -------------- -----------------------------------------------------------------------------
  **Phase**                         **Deliverables**                                                               **Duration**   **Acceptance Criteria**

  1 --- Rule repository             rule_repository.json (100+ rules); rule_repository.py loader                   3 days         All rules load and validate; schema validation passes; hot-reload tested

  2 --- Rule evaluators             gene_rule_engine.py, mutation_rule_engine.py, mechanism_rule_engine.py         3 days         Each engine produces correct candidates for 20 test inputs per type

  3 --- Combinatorial + inference   combinatorial_rules.py, phenotype_inference.py, inheritance_engine.py          2 days         gyrA S83L + parC S80I → R; NDM OR KPC → carbapenem R

  4 --- Conflict + confidence       conflict_resolution.py, confidence_propagation.py                              2 days         R always wins; FULL cap \> MEDIUM cap; genome quality applied correctly

  5 --- Breakpoints + ECOFF         eucast_adapter.py, clsi_adapter.py, ecoff_engine.py, hill_equation_engine.py   2 days         Breakpoint lookup returns correct S/R thresholds for 50 drug/species combos

  6 --- Explanation + export        explanation_engine.py, module2_export.py                                       2 days         Explanation readable; module2_input.csv passes schema validation

  7 --- API + Celery + Nextflow     FastAPI routes, celery_tasks.py, DSL2 processes                                2 days         POST predict → COMPLETED; GET module2-export returns valid CSV

  8 --- Testing + validation        Full test suite; reference phenotype validation; benchmarks                    3 days         ≥ 95% coverage; sensitivity ≥ 0.90 on reference dataset; \< 30s per isolate
  --------------------------------- ------------------------------------------------------------------------------ -------------- -----------------------------------------------------------------------------
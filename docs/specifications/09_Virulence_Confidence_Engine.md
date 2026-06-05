# 09 — Virulence Profiling and Confidence Scoring Engine

> **⚠️ Implementation Phase: Phase 4**
>
> Do not implement until phenotype prediction (Doc 08) is complete.
>
> **Prerequisites:** Docs 06, 07, and 08 fully operational.

---

**VIRULENCE PROFILING AND**

**CONFIDENCE SCORING ENGINE**

**SPECIFICATION \| VPCE v1.0**

**MODULE 1F --- AMR CHARACTERISATION ENGINE**

*VFDB · VirulenceFinder · Pathogenicity Scoring · Global Confidence Framework*

Python · FastAPI · PostgreSQL · Celery · Nextflow DSL2

Version 1.0 --- CONFIDENTIAL --- Direct Implementation Ready

> **SECTION 1 --- PURPOSE AND SCOPE**

**1.1 Dual Purpose**

Module 1F delivers two integrated subsystems: (1) the Virulence Profiling Engine, which screens assembled bacterial genomes against VFDB and VirulenceFinder to produce a pathogenicity-annotated virulence factor inventory; and (2) the Global Confidence Scoring Framework, which provides a reusable, standardised confidence scoring architecture for all findings across all Module 1 subsystems and future modules.

**1.2 Reusability Principle**

> **Design Goal:** The confidence scoring framework is designed as a standalone, independently importable Python package. It is consumed by Module 1C (AMR Detection), 1D (Mutation & Mechanism), 1E (Phenotype Prediction), and 1F (Virulence Profiling). All future modules (2, 3) import the same framework to ensure consistent confidence interpretation across the platform.

**1.3 Outputs Feed**

  ------------------------------------------------------ -----------------------------------------------------------------------------------------------------------------
  **Output**                                             **Consumed By**

  Virulence factor inventory (VirulenceFactor objects)   Module 1E Phenotype Prediction (pathogenicity risk context); Reporting layer; Module 2 export

  Pathogenicity profile + risk scores                    Clinical PDF report; surveillance dashboards; future epidemiology module

  Global confidence scores for all Module 1 findings     Module 1E prediction confidence; Module 2 genotype-phenotype concordance weighting; all report confidence tiers
  ------------------------------------------------------ -----------------------------------------------------------------------------------------------------------------

> **SECTION 2 --- BIOLOGICAL OBJECTIVES AND VIRULENCE CATEGORIES**

  ------------------------- -------------------------------------------------------------- ---------------------------------------------------------------------------- --------------------------------------------------------------------
  **Category**              **Definition**                                                 **Example Genes**                                                            **Clinical Significance**

  Adhesins                  Proteins mediating attachment to host cells or surfaces        fimH (type 1 fimbriae), papG (P fimbriae), sfa (S fimbriae), afa             Critical for UTI, sepsis initiation; host tropism determinants

  Toxins                    Secreted or cell-associated factors causing host cell damage   stx1/2 (Shiga toxin), hlyA (alpha-haemolysin), cdtB (CDT), ltA/stA (LT/ST)   Direct pathology; diarrhoea, HUS, cell lysis

  Invasins                  Proteins enabling intracellular penetration                    invA (Salmonella SPI-1), ipaB/C (Shigella), ial, ibeA                        Intracellular lifestyle; evade host immunity

  Biofilm                   Genes enabling surface colonisation and biofilm matrix         csgA/B (curli), pgaA-D, fliC, luxS, bssS                                     Persistent infections; device colonisation; antibiotic tolerance

  Iron acquisition          Siderophore biosynthesis and receptor genes                    fyuA (yersiniabactin receptor), iucA-D (aerobactin), iroN, entB/F            Iron limitation overcome; competitive advantage in host

  Capsule biosynthesis      Polysaccharide capsule assembly genes                          kpsMT (K-antigen), neuA-D, wcaA-Z                                            Immune evasion; complement resistance; invasive disease

  Secretion systems         Protein secretion machinery (T3SS, T4SS, T6SS)                 spiB (T3SS), trbB/C (T4SS), hcp (T6SS), esxA/B (T7SS)                        Effector delivery into host cells; immune modulation

  Immune evasion            Factors suppressing host immune responses                      iss (serum resistance), traT, ompT, kpsMT (capsule)                          Bacteraemia; evasion of complement and opsonisation

  Stress response           Tolerance to hostile host environments                         rpoS, dnaK, sodA/B, katG, recA, lexA                                         Persistence; tolerance to oxidative stress, acid, heat

  Host colonisation         Generalised colonisation factors not in above classes          luxS (quorum sensing), fis, H-NS (regulatory)                                Fitness advantage during infection

  Antimicrobial tolerance   Non-resistance tolerance mechanisms                            tisB, hipA, mazF (toxin-antitoxin), persister inducers                       Phenotypic tolerance; treatment failure without genetic resistance

  Unknown                   Genes with VF database annotation but unclear function         Novel VFDB entries                                                           Flagged for review; not scored in pathogenicity model
  ------------------------- -------------------------------------------------------------- ---------------------------------------------------------------------------- --------------------------------------------------------------------

> **SECTION 3 --- SUPPORTED DATABASES AND WORKFLOW**

**3.1 Database Support**

  --------------------------- --------------------------- -------------------------------------------------------------------------------------- --------------- ---------------
  **Database**                **Version Tracked**         **Scope**                                                                              **Seq Type**    **License**

  VFDB (Full dataset)         ≥ 2024 quarterly release    Comprehensive VF genes across all bacterial species; function + category annotations   DNA + protein   Free academic

  VirulenceFinder             ≥ 2.0.x (database ≥ 2023)   Clinical pathogen VF genes; species-specific panels                                    DNA             Apache 2.0

  VFDB (Core dataset)         Same as full                Experimentally validated VF genes only                                                 DNA + protein   Free academic

  PATRIC Virulence (future)   On integration              PATRIC VF annotations from genome feature tables                                       Protein         Public domain

  Victors Database (future)   On integration              Manually curated VF proteins                                                           Protein         Academic
  --------------------------- --------------------------- -------------------------------------------------------------------------------------- --------------- ---------------

**3.2 Detection Workflow**

> INPUT: validated_genome.fasta
>
> │
>
> ▼
>
> ┌────────────────────────────────────────────────────────┐
>
> │ DATABASE SEARCH (BLAST against VFDB + VirulenceFinder) │
>
> │ min_identity=75% \| min_coverage=60% \| E \< 1e-5 │
>
> └────────────────┬───────────────────────────────────────┘
>
> │ raw_hits\[\]
>
> ┌────────────────▼───────────────────────────────────────┐
>
> │ HIT VALIDATION ENGINE │
>
> │ identity, coverage, bit_score, e_value metrics │
>
> └────────────────┬───────────────────────────────────────┘
>
> │ validated_hits\[\]
>
> ┌────────────────▼───────────────────────────────────────┐
>
> │ ONTOLOGY MAPPING + CATEGORY ASSIGNMENT │
>
> │ gene → category → function (from virulence_ontology.json)│
>
> └────────────────┬───────────────────────────────────────┘
>
> │ classified_hits\[\]
>
> ┌────────────────▼───────────────────────────────────────┐
>
> │ CONFIDENCE SCORING (Global Framework) │
>
> │ identity × coverage × db_agreement × evidence_strength │
>
> └────────────────┬───────────────────────────────────────┘
>
> │ scored_factors\[\]
>
> ┌────────────────▼───────────────────────────────────────┐
>
> │ PATHOGENICITY PROFILE + RISK SCORING │
>
> └────────────────────────────────────────────────────────────┘
>
> **SECTION 4 --- VFDB INTEGRATION**

**4.1 Implementation: vfdb_adapter.py**

> \"\"\"VFDB virulence factor adapter --- Module 1F v1.0.0\"\"\"
>
> import subprocess, re
>
> from pathlib import Path
>
> from .result_models import VirulenceRawHit
>
> class VFDBAdapter:
>
> def \_\_init\_\_(self, vfdb_fasta: Path, blast_db_path: Path, db_version_id: str):
>
> self.blast_db = blast_db_path
>
> self.db_version_id = db_version_id
>
> def run(self, fasta: Path, min_identity=75.0,
>
> min_coverage=60.0, threads=4) -\> list\[VirulenceRawHit\]:
>
> cmd = \[\"blastn\", \"-query\", str(fasta),
>
> \"-db\", str(self.blast_db),
>
> \"-out\", \"/dev/stdout\",
>
> \"-outfmt\", \"6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore slen\",
>
> \"-perc_identity\", str(min_identity),
>
> \"-num_threads\", str(threads),
>
> \"-evalue\", \"1e-5\"\]
>
> result = subprocess.run(cmd, check=True, capture_output=True, text=True)
>
> return self.\_parse_blast6(result.stdout, min_coverage)
>
> def \_parse_blast6(self, blast_out: str, min_cov: float) -\> list\[VirulenceRawHit\]:
>
> hits = \[\]
>
> for line in blast_out.strip().split(\"\\n\"):
>
> if not line: continue
>
> cols = line.split(\"\\t\")
>
> qid, sid, pident, alen, \_, \_, qs, qe, ss, se, evalue, bs, slen = cols
>
> cov = int(alen) / int(slen) \* 100
>
> if cov \< min_cov: continue
>
> gene_name, category, function = self.\_parse_vfdb_header(sid)
>
> hits.append(VirulenceRawHit(
>
> tool=\"VFDB\", gene_name=gene_name, vf_category=category,
>
> vf_function=function, identity_pct=float(pident),
>
> coverage_pct=cov, contig_id=qid, start=int(qs), end=int(qe),
>
> bit_score=float(bs), e_value=float(evalue),
>
> db_version_id=self.db_version_id))
>
> return hits

**4.2 VFDB Header Parsing**

> \# VFDB sequence header format: \>VF####(GB\|VF_XXXXXX) \[gene_name\] \[function\] \[organism\]
>
> VFDB_HEADER_RE = re.compile(
>
> r\"VF(?P\<vf_id\>\\d+).\*?\\\[(?P\<gene\>\[\^\\\]\]+)\\\]\\s\*\\\[(?P\<function\>\[\^\\\]\]+)\\\]\"
>
> )
>
> **SECTION 5 --- VIRULENCEFINDER INTEGRATION**

**5.1 Implementation: virulencefinder_adapter.py**

> class VirulenceFinderAdapter:
>
> def \_\_init\_\_(self, db_path: Path, db_version_id: str):
>
> self.db_path = db_path
>
> self.db_version_id = db_version_id
>
> def run(self, fasta: Path, species: str \| None = None,
>
> min_identity=90.0, min_coverage=60.0) -\> list\[VirulenceRawHit\]:
>
> cmd = \[\"python\", \"-m\", \"virulencefinder\",
>
> \"-i\", str(fasta), \"-o\", \"/tmp/vf_out\",
>
> \"-d\", str(self.db_path),
>
> \"-l\", str(min_coverage / 100),
>
> \"-t\", str(min_identity / 100)\]
>
> if species: cmd += \[\"-s\", species\]
>
> subprocess.run(cmd, check=True, capture_output=True)
>
> return self.\_parse_results(Path(\"/tmp/vf_out/data.json\"))
>
> def \_parse_results(self, json_path: Path) -\> list\[VirulenceRawHit\]:
>
> import json
>
> data = json.loads(json_path.read_text())
>
> hits = \[\]
>
> for db_name, results in data.get(\"virulencefinder\", {}).items():
>
> for gene, entry in results.items():
>
> if entry.get(\"identity\", 0) == \"No hit\": continue
>
> hits.append(VirulenceRawHit(
>
> tool=\"VirulenceFinder\", gene_name=gene,
>
> identity_pct=float(entry.get(\"identity\",\"0\").rstrip(\"%\")),
>
> coverage_pct=float(entry.get(\"coverage\",\"0\").rstrip(\"%\")),
>
> db_version_id=self.db_version_id, \...))
>
> return hits
>
> **SECTION 6 --- VIRULENCE ONTOLOGY**

**6.1 virulence_ontology.json**

> {
>
> \"schema_version\": \"1.0.0\",
>
> \"categories\": \[
>
> {\"code\":\"adhesin\", \"display\":\"Adhesion Factor\", \"risk_weight\":0.70,
>
> \"description\":\"Enables attachment to host epithelium or matrix\"},
>
> {\"code\":\"toxin\", \"display\":\"Toxin\", \"risk_weight\":1.00,
>
> \"description\":\"Directly damages host cells or tissues\"},
>
> {\"code\":\"invasin\", \"display\":\"Invasion Factor\", \"risk_weight\":0.90,
>
> \"description\":\"Mediates intracellular penetration\"},
>
> {\"code\":\"biofilm\", \"display\":\"Biofilm Factor\", \"risk_weight\":0.50,
>
> \"description\":\"Promotes surface colonisation and persistence\"},
>
> {\"code\":\"iron_acquisition\", \"display\":\"Iron Acquisition System\", \"risk_weight\":0.75,
>
> \"description\":\"Overcomes iron limitation in host environment\"},
>
> {\"code\":\"capsule\", \"display\":\"Capsule Biosynthesis\", \"risk_weight\":0.85,
>
> \"description\":\"Polysaccharide capsule evades innate immunity\"},
>
> {\"code\":\"secretion_system\", \"display\":\"Secretion System\", \"risk_weight\":0.85,
>
> \"description\":\"T3SS/T4SS/T6SS delivers effectors into host\"},
>
> {\"code\":\"immune_evasion\", \"display\":\"Immune Evasion Factor\", \"risk_weight\":0.80,
>
> \"description\":\"Suppresses complement, opsonisation, or phagocytosis\"},
>
> {\"code\":\"stress_response\", \"display\":\"Stress Response Factor\", \"risk_weight\":0.40,
>
> \"description\":\"Tolerance to host-imposed stresses\"},
>
> {\"code\":\"colonisation\", \"display\":\"Host Colonisation Factor\", \"risk_weight\":0.45,
>
> \"description\":\"General fitness advantage during infection\"},
>
> {\"code\":\"amr_tolerance\", \"display\":\"Antimicrobial Tolerance\", \"risk_weight\":0.60,
>
> \"description\":\"Phenotypic tolerance without genetic resistance\"},
>
> {\"code\":\"unknown\", \"display\":\"Unknown Function\", \"risk_weight\":0.10,
>
> \"description\":\"Annotated in VF database; function unclear\"}
>
> \],
>
> \"high_risk_categories\": \[\"toxin\",\"invasin\",\"capsule\",\"secretion_system\",\"immune_evasion\"\],
>
> \"high_risk_genes\": \[\"stx1\",\"stx2\",\"hlyA\",\"cdtB\",\"cna\",\"lukSF\",\"tcdA\",\"tcdB\"\]
>
> **SECTION 7 --- CATEGORY ASSIGNMENT AND VIRULENCE CLASSIFIER**

**7.1 Implementation: virulence_classifier.py**

> \"\"\"Virulence category assignment --- Module 1F v1.0.0\"\"\"
>
> import json
>
> from functools import lru_cache
>
> from pathlib import Path
>
> class VirulenceClassifier:
>
> def \_\_init\_\_(self, ontology_path: Path, gene_map_path: Path):
>
> self.ontology = json.loads(ontology_path.read_text())
>
> self.gene_map = json.loads(gene_map_path.read_text()) \# {gene_name: category_code}
>
> self.\_cat_index = {c\[\"code\"\]: c for c in self.ontology\[\"categories\"\]}
>
> def classify(self, hit: \"VirulenceRawHit\") -\> dict:
>
> cat_code = self.\_lookup_category(hit.gene_name)
>
> cat = self.\_cat_index.get(cat_code, self.\_cat_index\[\"unknown\"\])
>
> is_hr = (cat_code in self.ontology\[\"high_risk_categories\"\]
>
> or hit.gene_name.lower() in \[g.lower() for g in self.ontology\[\"high_risk_genes\"\]\])
>
> return {
>
> \"category_code\": cat_code,
>
> \"category_display\": cat\[\"display\"\],
>
> \"risk_weight\": cat\[\"risk_weight\"\],
>
> \"is_high_risk\": is_hr,
>
> }
>
> \@lru_cache(maxsize=4096)
>
> def \_lookup_category(self, gene_name: str) -\> str:
>
> name = gene_name.lower()
>
> \# Direct map lookup
>
> if name in self.gene_map: return self.gene_map\[name\]
>
> \# Prefix heuristic
>
> PREFIXES = {\"fim\":\"adhesin\",\"pap\":\"adhesin\",\"stx\":\"toxin\",\"hly\":\"toxin\",
>
> \"inv\":\"invasin\",\"iuc\":\"iron_acquisition\",\"kps\":\"capsule\",
>
> \"spi\":\"secretion_system\",\"csg\":\"biofilm\",\"iro\":\"iron_acquisition\"}
>
> return next((v for k,v in PREFIXES.items() if name.startswith(k)), \"unknown\")

**7.2 Gene Category Map (excerpt)**

  ---------- ------------------ ---------------------------------------------------------------------------- ---------------
  **Gene**   **Category**       **Function**                                                                 **High Risk**

  fimH       adhesin            Type 1 fimbrial adhesin; binds uroplakin Ia on bladder epithelium            No

  stx1       toxin              Shiga toxin 1; AB5 toxin inhibiting ribosomal protein synthesis              YES

  stx2       toxin              Shiga toxin 2; associated with HUS; more potent than Stx1                    YES

  hlyA       toxin              Alpha-haemolysin; pore-forming RTX toxin; lysed RBCs and cells               YES

  iucA       iron_acquisition   Aerobactin synthetase; enables aerobactin siderophore production             No

  fyuA       iron_acquisition   Yersiniabactin receptor; iron acquisition in bloodstream                     No

  kpsMT      capsule            K-antigen capsule transport; complement evasion                              YES

  invA       invasin            SPI-1 T3SS inner membrane component; required for host cell invasion         YES

  csgA       biofilm            Major curli subunit; biofilm matrix formation                                No

  hcp        secretion_system   T6SS hemolysin-coregulated protein; secreted effector carrier                YES

  iss        immune_evasion     Increased serum survival; complement resistance outer membrane lipoprotein   YES

  rpoS       stress_response    Stationary-phase sigma factor; general stress response regulator             No

  hipA       amr_tolerance      Toxin component of HipAB TA system; persister cell induction                 No
  ---------- ------------------ ---------------------------------------------------------------------------- ---------------

> **SECTION 8 --- PATHOGENICITY PROFILE AND RISK SCORING**

**8.1 Pathogenicity Profile Engine**

> \@dataclass
>
> class PathogenicityProfile:
>
> sample_id: str
>
> total_vf_genes: int
>
> categories_detected: list\[str\]
>
> category_diversity: int \# number of distinct categories
>
> high_risk_count: int
>
> high_risk_genes: list\[str\]
>
> unique_determinants: list\[str\] \# genes not common in species
>
> risk_score: float \# 0--100
>
> risk_class: str \# LOW \| MODERATE \| HIGH \| CRITICAL
>
> category_summary: dict \# {category: gene_count}
>
> confidence: float

**8.2 Virulence Risk Score Formula**

> **Risk = min( w_burden × burden_score + w_diversity × diversity_score + w_highRisk × high_risk_score, 100 )**

  ----------------- ------------ -----------------------------------------------------------------
  **Component**     **Weight**   **Calculation**

  Burden score      0.35         100 × min(total_vf_genes / 20, 1.0) --- 20 genes = max burden

  Diversity score   0.30         100 × (category_diversity / 12) --- 12 = total categories

  High-risk score   0.35         100 × min(high_risk_count / 5, 1.0) --- 5 high-risk genes = max
  ----------------- ------------ -----------------------------------------------------------------

**8.3 Risk Classification**

  ----------- ----------- ------------------------------------------------------------------------------------ -------------------------------------------------------------------
  **Score**   **Class**   **Interpretation**                                                                   **Clinical Action**

  0--24       LOW         Few or low-impact VF genes; typical commensal or low-virulence isolate               Standard interpretation; no special alert

  25--49      MODERATE    Multiple VF categories present; potential opportunistic pathogen                     Note in report; include with clinical context

  50--74      HIGH        High burden with diverse categories including immune evasion or secretion systems    Highlight in report; epidemiological review recommended

  75--100     CRITICAL    Multiple high-risk determinants including toxins or invasins; likely hypervirulent   Urgent clinical flag; alert infection control; epidemic potential
  ----------- ----------- ------------------------------------------------------------------------------------ -------------------------------------------------------------------

**8.4 Implementation: pathogenicity_profile.py**

> def compute_risk_score(factors: list\[\"VirulenceFactor\"\],
>
> ontology: dict) -\> dict:
>
> categories = {f.category_code for f in factors}
>
> hr_genes = \[f for f in factors if f.is_high_risk\]
>
> burden_s = min(len(factors) / 20, 1.0) \* 100
>
> diversity_s= (len(categories) / 12) \* 100
>
> hr_s = min(len(hr_genes) / 5, 1.0) \* 100
>
> score = 0.35 \* burden_s + 0.30 \* diversity_s + 0.35 \* hr_s
>
> cls = \"CRITICAL\" if score\>=75 else \"HIGH\" if score\>=50 else \"MODERATE\" if score\>=25 else \"LOW\"
>
> return {\"risk_score\": round(score, 2), \"risk_class\": cls, \"high_risk_genes\": \[f.gene_name for f in hr_genes\]}
>
> **SECTION 9 --- GLOBAL CONFIDENCE FRAMEWORK**

**9.1 Framework Architecture**

> ┌───────────────────────────────────────────────────────────────────┐
>
> │ GLOBAL CONFIDENCE SCORING FRAMEWORK (amr_confidence/) │
>
> │ │
>
> │ ┌─────────────────────────────────────────────────────────────┐ │
>
> │ │ COMPONENT SCORERS │ │
>
> │ │ identity_score.py coverage_score.py bitscore_score.py │ │
>
> │ │ evalue_score.py agreement_score.py evidence_strength.py│ │
>
> │ └─────────────────────────────────────────────────────────────┘ │
>
> │ │ │
>
> │ ┌─────────────────────────────────────────────────────────────┐ │
>
> │ │ CONFIDENCE AGGREGATION ENGINE │ │
>
> │ │ confidence_aggregation.py │ │
>
> │ │ Weighted combination of component scores │ │
>
> │ └─────────────────────────────────────────────────────────────┘ │
>
> │ │
>
> │ ┌─────────────────────────────────────────────────────────────┐ │
>
> │ │ CONTEXT MODIFIERS │ │
>
> │ │ genome_quality_modifier.py (from Module 1A) │ │
>
> │ │ prediction_context_modifier.py (rule strength, KB level) │ │
>
> │ └─────────────────────────────────────────────────────────────┘ │
>
> │ │
>
> │ ┌─────────────────────────────────────────────────────────────┐ │
>
> │ │ CLASSIFIER + EXPLAINER │ │
>
> │ │ confidence_classifier.py confidence_explanation.py │ │
>
> │ └─────────────────────────────────────────────────────────────┘ │
>
> │ │
>
> │ CONSUMERS: │
>
> │ Module 1C AMR Detection │ Module 1D Mutation │ Module 1D Mech │
>
> │ Module 1E Phenotype │ Module 1F Virulence │ Module 2 (future)│

**9.2 Framework Package Structure**

> amr_confidence/
>
> ├── \_\_init\_\_.py \# ConfidenceEngine facade class
>
> ├── components/
>
> │ ├── identity_score.py
>
> │ ├── coverage_score.py
>
> │ ├── bitscore_score.py
>
> │ ├── evalue_score.py
>
> │ ├── agreement_score.py
>
> │ └── evidence_strength.py
>
> ├── confidence_aggregation.py
>
> ├── confidence_classifier.py
>
> ├── confidence_explanation.py
>
> ├── modifiers/
>
> │ ├── genome_quality_modifier.py
>
> │ └── prediction_context_modifier.py
>
> └── tests/
>
> └── test_confidence_framework.py
>
> **SECTION 10 --- CONFIDENCE COMPONENT IMPLEMENTATIONS**

**10.1 Identity Score: identity_score.py**

> \"\"\"Identity-based confidence component --- amr_confidence v1.0.0\"\"\"
>
> \# Piecewise scoring: rewards high identity non-linearly
>
> IDENTITY_THRESHOLDS = \[
>
> (100.0, 1.000), \# Perfect match
>
> (99.0, 0.980),
>
> (95.0, 0.940),
>
> (90.0, 0.860),
>
> (85.0, 0.760),
>
> (80.0, 0.640),
>
> (75.0, 0.500),
>
> (0.0, 0.200), \# Below reporting threshold; should not normally be seen
>
> \]
>
> def identity_score(identity_pct: float) -\> float:
>
> for threshold, score in IDENTITY_THRESHOLDS:
>
> if identity_pct \>= threshold: return score
>
> return 0.10

**10.2 Coverage Score: coverage_score.py**

> COVERAGE_THRESHOLDS = \[
>
> (100.0, 1.000), \# Full reference coverage
>
> (95.0, 0.960),
>
> (90.0, 0.900),
>
> (80.0, 0.800),
>
> (70.0, 0.680),
>
> (60.0, 0.550),
>
> (50.0, 0.400), \# Minimum reportable threshold
>
> \]
>
> def coverage_score(coverage_pct: float, is_partial_expected: bool = False) -\> float:
>
> \"\"\"partial_expected: True for fragmented genes where partial hits are biologically valid.\"\"\"
>
> base = next((s for t, s in COVERAGE_THRESHOLDS if coverage_pct \>= t), 0.30)
>
> return min(base \* 1.15, 1.0) if is_partial_expected else base

**10.3 Bit Score Normalisation: bitscore_score.py**

> def bitscore_score(bit_score: float,
>
> reference_length: int,
>
> max_expected_bitscore: float \| None = None) -\> float:
>
> \"\"\"Normalise bit score relative to expected maximum for this gene length.\"\"\"
>
> if max_expected_bitscore is None:
>
> \# Theoretical max: \~2 bits per aligned base pair
>
> max_expected_bitscore = reference_length \* 2.0
>
> return min(bit_score / max_expected_bitscore, 1.0)

**10.4 E-value Score: evalue_score.py**

> **E-value score = 1 − log₁₀(E) / log₁₀(threshold_E) \[clamped to 0--1\]**
>
> import math
>
> def evalue_score(e_value: float, threshold: float = 1e-5) -\> float:
>
> \"\"\"Convert e-value to confidence score. E ≤ threshold → maximum contribution.\"\"\"
>
> if e_value \<= 0: return 1.0
>
> log_ev = math.log10(e_value)
>
> log_th = math.log10(threshold)
>
> return max(0.0, min(1.0, 1 - log_ev / log_th))
>
> **SECTION 11 --- DATABASE AGREEMENT AND EVIDENCE STRENGTH**

**11.1 Database Agreement Score: agreement_score.py**

> \# Agreement level definitions
>
> AGREEMENT_SCORES = {
>
> 4: 1.00, \# All 4 tools agree (CARD + AMRFinder + ResFinder + Abricate/VFDB)
>
> 3: 0.90, \# 3 tools agree
>
> 2: 0.75, \# 2 tools agree
>
> 1: 0.55, \# Single tool only
>
> }
>
> def agreement_score(supporting_tools: list\[str\],
>
> max_tools: int = 4) -\> float:
>
> n = min(len(supporting_tools), max_tools)
>
> return AGREEMENT_SCORES.get(n, 0.40)
>
> def agreement_flag(supporting_tools: list\[str\], conflicting_tools: list\[str\]) -\> str:
>
> if conflicting_tools: return \"CONFLICT\"
>
> n = len(supporting_tools)
>
> if n == 0: return \"NO_SUPPORT\"
>
> if n == 1: return \"SINGLE_SOURCE\"
>
> if n \>= 2 and n \< 4: return \"PARTIAL_AGREEMENT\"
>
> return \"COMPLETE_AGREEMENT\"

**11.2 Evidence Strength: evidence_strength.py**

> EVIDENCE_WEIGHTS = {
>
> \"experimental\": 1.00, \# Direct experimental validation (e.g. virulence assay)
>
> \"clinical\": 0.95, \# From clinical isolates with documented pathogenicity
>
> \"computational\": 0.70, \# Bioinformatic prediction
>
> \"inferred\": 0.50, \# Inferred from gene family or structural similarity
>
> \"unknown\": 0.30, \# No evidence type recorded
>
> }
>
> def evidence_strength_score(evidence_types: list\[str\]) -\> float:
>
> if not evidence_types: return EVIDENCE_WEIGHTS\[\"unknown\"\]
>
> return max(EVIDENCE_WEIGHTS.get(e, 0.30) for e in evidence_types)
>
> **SECTION 12 --- CONFIDENCE AGGREGATION AND CLASSIFICATION**

**12.1 Aggregation Formula**

> **C = w_id × identity_score + w_cov × coverage_score + w_bs × bitscore_score + w_ev × evalue_score + w_ag × agreement_score + w_es × evidence_strength**

Default weights are context-dependent:

  ---------------------- ---------- ----------- ---------- ---------- ---------- ----------
  **Context**            **w_id**   **w_cov**   **w_bs**   **w_ev**   **w_ag**   **w_es**

  AMR gene detection     0.30       0.25        0.05       0.05       0.25       0.10

  Virulence detection    0.30       0.25        0.05       0.05       0.20       0.15

  Mutation calling       0.35       0.20        0.05       0.05       0.20       0.15

  Phenotype prediction   0.15       0.15        0.05       0.05       0.20       0.40
  ---------------------- ---------- ----------- ---------- ---------- ---------- ----------

**12.2 Implementation: confidence_aggregation.py**

> \"\"\"Global confidence aggregation engine --- amr_confidence v1.0.0\"\"\"
>
> from dataclasses import dataclass
>
> CONTEXT_WEIGHTS = {
>
> \"amr_gene\": {\"identity\":0.30,\"coverage\":0.25,\"bitscore\":0.05,\"evalue\":0.05,\"agreement\":0.25,\"evidence\":0.10},
>
> \"virulence\": {\"identity\":0.30,\"coverage\":0.25,\"bitscore\":0.05,\"evalue\":0.05,\"agreement\":0.20,\"evidence\":0.15},
>
> \"mutation\": {\"identity\":0.35,\"coverage\":0.20,\"bitscore\":0.05,\"evalue\":0.05,\"agreement\":0.20,\"evidence\":0.15},
>
> \"phenotype\": {\"identity\":0.15,\"coverage\":0.15,\"bitscore\":0.05,\"evalue\":0.05,\"agreement\":0.20,\"evidence\":0.40},
>
> }
>
> \@dataclass
>
> class ConfidenceResult:
>
> overall_score: float
>
> tier: str \# HIGH \| MEDIUM \| LOW
>
> components: dict \# raw component scores
>
> weighted: dict \# weighted contributions
>
> cap_applied: bool
>
> context: str
>
> def aggregate(identity_pct: float, coverage_pct: float,
>
> bit_score: float, e_value: float,
>
> supporting_tools: list\[str\], evidence_types: list\[str\],
>
> context: str = \"amr_gene\",
>
> genome_quality: str = \"FULL\") -\> ConfidenceResult:
>
> from .components.identity_score import identity_score
>
> from .components.coverage_score import coverage_score
>
> from .components.bitscore_score import bitscore_score
>
> from .components.evalue_score import evalue_score
>
> from .components.agreement_score import agreement_score
>
> from .components.evidence_strength import evidence_strength_score
>
> from .modifiers.genome_quality_modifier import GENOME_CAP
>
> w = CONTEXT_WEIGHTS.get(context, CONTEXT_WEIGHTS\[\"amr_gene\"\])
>
> comps = {
>
> \"identity\": identity_score(identity_pct),
>
> \"coverage\": coverage_score(coverage_pct),
>
> \"bitscore\": bitscore_score(bit_score, reference_length=1000),
>
> \"evalue\": evalue_score(e_value),
>
> \"agreement\": agreement_score(supporting_tools),
>
> \"evidence\": evidence_strength_score(evidence_types),
>
> }
>
> weighted = {k: w\[k\] \* v for k, v in comps.items()}
>
> raw = sum(weighted.values())
>
> cap = GENOME_CAP.get(genome_quality, 0.50)
>
> final = min(raw, cap)
>
> tier = \"HIGH\" if final\>=0.85 else \"MEDIUM\" if final\>=0.60 else \"LOW\"
>
> return ConfidenceResult(final, tier, comps, weighted, final \< raw, context)

**12.3 Confidence Classification Thresholds**

  ---------- ----------------- ----------------- ------------------------------------------------------------------ ----------------------------------------------------------
  **Tier**   **Score Range**   **Colour Code**   **Interpretation**                                                 **Report Treatment**

  HIGH       ≥ 0.85            Green (#2D6A4F)   Strong multi-source evidence; suitable for direct clinical use     Report without qualification

  MEDIUM     0.60--0.84        Amber (#E67E22)   Reasonable evidence with minor gaps; requires clinical context     Report with confidence note

  LOW        \< 0.60           Red (#922B21)     Weak or incomplete evidence; single source or borderline metrics   Report with CAUTION flag; recommend wet-lab confirmation
  ---------- ----------------- ----------------- ------------------------------------------------------------------ ----------------------------------------------------------

> **SECTION 13 --- EXPLANATION ENGINE**

**13.1 Implementation: confidence_explanation.py**

> def explain_confidence(result: ConfidenceResult, entity_name: str) -\> str:
>
> lines = \[f\"Confidence: {result.tier} ({result.overall_score:.3f})\"\]
>
> lines.append(f\"Entity: {entity_name} \| Context: {result.context}\")
>
> lines.append(\"Component Contributions:\")
>
> for comp, weighted_val in sorted(result.weighted.items(), key=lambda x: -x\[1\]):
>
> raw = result.components\[comp\]
>
> lines.append(f\" {comp:\<12} raw={raw:.3f} weighted={weighted_val:.3f}\")
>
> if result.cap_applied:
>
> lines.append(\"Note: Score capped by genome quality (assembly QC result).\")
>
> return \"\\n\".join(lines)

**13.2 Example Explanation Outputs**

> **Example --- HIGH confidence AMR gene:** Entity: blaCTX-M-15 \| Confidence: HIGH (0.921) \| Identity: 100% (1.000) \| Coverage: 100% (1.000) \| Agreement: CARD+AMRFinder+Abricate (0.900) \| Evidence: experimental (1.000) \| Bitscore: normalised 0.85 \| E-value: 0.0 (1.000)
>
> **Example --- LOW confidence virulence:** Entity: fimD \| Confidence: LOW (0.543) \| Identity: 78.4% (0.640) \| Coverage: 61.2% (0.550) \| Agreement: VFDB only (0.550) \| Evidence: computational (0.700) \| Note: Single-database low-identity hit; recommend wet-lab confirmation
>
> **SECTION 14 --- VIRULENCE FACTOR RESULT MODEL**

**14.1 VirulenceFactor Dataclass**

> \@dataclass
>
> class VirulenceFactor:
>
> vf_id: str \# UUID
>
> sample_id: str
>
> gene_name: str
>
> vfdb_id: str \| None \# e.g. \"VF0001\"
>
> category_code: str
>
> category_display: str
>
> function_description: str
>
> detection_tool: str
>
> db_version_id: str
>
> identity_pct: float
>
> coverage_pct: float
>
> bit_score: float
>
> e_value: float
>
> contig_id: str
>
> start: int
>
> end: int
>
> strand: str
>
> is_high_risk: bool
>
> risk_weight: float
>
> confidence: ConfidenceResult
>
> **SECTION 15 --- DATABASE DESIGN**

  -------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------------------------------------------------------------
  **Table**                        **Key Columns**                                                                                                                                                                                                                     **Notes**

  virulence_factors                id, sample_id, job_id, db_version_id, gene_name, vfdb_id, category_code, function_description, detection_tool, identity_pct, coverage_pct, bit_score, e_value, contig_id, start, end, is_high_risk, risk_weight, confidence_score   Core table; one row per detected gene per sample

  virulence_annotations            id, vf_id (FK), annotation_source, key, value                                                                                                                                                                                       Flexible KV store for VFDB function tags, cross-references, PubMed IDs

  virulence_profiles               id, sample_id, job_id, total_vf_genes, categories TEXT\[\], category_diversity, high_risk_count, risk_score, risk_class, computed_at                                                                                                Per-sample aggregated pathogenicity profile

  virulence_scores (detail)        id, sample_id, vf_id (FK), category_summary JSONB, component_scores JSONB                                                                                                                                                           Detailed per-gene score breakdown for audit

  confidence_scores                id, sample_id, entity_type, entity_id, overall_score, tier, components JSONB, weighted JSONB, cap_applied, context, computed_at                                                                                                     Global confidence store; entity_type = amr_gene \| mutation \| phenotype \| virulence

  confidence_components (detail)   id, confidence_id (FK), component_name, raw_value, weight, weighted_score                                                                                                                                                           Per-component rows for detailed confidence audit queries
  -------------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- ---------------------------------------------------------------------------------------

**15.1 confidence_components SQL**

> CREATE TABLE confidence_components (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> confidence_id UUID NOT NULL REFERENCES confidence_scores(id) ON DELETE CASCADE,
>
> component_name VARCHAR(50) NOT NULL,
>
> \-- identity \| coverage \| bitscore \| evalue \| agreement \| evidence
>
> raw_value NUMERIC(8,5),
>
> weight NUMERIC(5,4),
>
> weighted_score NUMERIC(8,5),
>
> notes TEXT
>
> );
>
> CREATE INDEX idx_conf_comp ON confidence_components (confidence_id);
>
> **SECTION 16 --- FASTAPI SERVICE DESIGN**

  ------------ -------------------------------------------- ----------------------------------------- ------------------------------------------------------------------
  **Method**   **Path**                                     **Response**                              **Description**

  POST         /api/v1/module1/virulence                    202 {job_id}                              Submit virulence profiling job; async

  GET          /api/v1/module1/virulence/{job_id}           200 {status, progress_pct}                Poll job status

  GET          /api/v1/module1/virulence/{job_id}/results   200 {virulence_factors\[\]}               Full virulence factor inventory

  GET          /api/v1/module1/virulence/{job_id}/profile   200 {pathogenicity_profile, risk_score}   Pathogenicity summary and risk score

  GET          /api/v1/samples/{id}/virulence               200 {factors\[\], profile}                Latest virulence data for sample

  GET          /api/v1/module1/confidence/{job_id}          200 {confidence_scores\[\]}               All confidence scores for a completed job (any Module 1 job)

  GET          /api/v1/samples/{id}/confidence              200 {by_entity_type{}}                    Aggregated confidence scores grouped by entity type for a sample
  ------------ -------------------------------------------- ----------------------------------------- ------------------------------------------------------------------

**16.1 Virulence Request Schema**

> class VirulenceRequest(BaseModel):
>
> model_config = ConfigDict(strict=True)
>
> sample_id: UUID
>
> assembly_id: UUID
>
> species: str \| None = None
>
> tools: list\[Literal\[\"VFDB\",\"VirulenceFinder\"\]\] = \[\"VFDB\",\"VirulenceFinder\"\]
>
> min_identity: float = Field(default=80.0, ge=75.0, le=100.0)
>
> min_coverage: float = Field(default=60.0, ge=40.0, le=100.0)
>
> include_stress_response: bool = True
>
> db_version_ids: dict\[str, str\] = {}
>
> **SECTION 17 --- CELERY AND NEXTFLOW DESIGN**

**17.1 Celery Progress Steps**

  ------------------------ ---------------- -------------------------------------------------------------------------------------------------------------
  **Step**                 **Progress %**   **Description**

  VFDB_SEARCH              0--35            BLASTn against VFDB full dataset

  VIRULENCEFINDER          35--60           VirulenceFinder execution

  HIT_VALIDATION           60--65           Filter by identity/coverage thresholds

  ONTOLOGY_MAPPING         65--72           Category assignment via virulence_ontology.json

  CONFIDENCE_SCORING       72--82           Global confidence framework applied to all hits

  DEDUPLICATION            82--87           Merge duplicate hits across tools

  PATHOGENICITY_PROFILE    87--93           Risk score computation; profile assembly

  CONFIDENCE_ALL_MODULE1   93--96           Re-compute confidence for all Module 1 entities (genes, mutations, phenotypes) using final assembly quality

  REPORT_GENERATION        96--100          JSON/TSV/PDF; DB write
  ------------------------ ---------------- -------------------------------------------------------------------------------------------------------------

**17.2 Nextflow DSL2 Processes**

> process VIRULENCE_DETECTION {
>
> tag \"\${meta.sample_id}\"
>
> label \"process_medium\"
>
> cpus 4; memory \"8 GB\"; time \"30.min\"
>
> container \"amr-platform/virulence-profiler:1.0.0\"
>
> input:
>
> tuple val(meta), path(fasta)
>
> path vfdb_blast_db
>
> path virulencefinder_db
>
> output:
>
> tuple val(meta), path(\"virulence_factors.tsv\"), emit: vf_tsv
>
> tuple val(meta), path(\"virulence_summary.json\"), emit: vf_summary
>
> tuple val(meta), path(\"pathogenicity_profile.json\"),emit: path_profile
>
> tuple val(meta), path(\"virulence_risk_score.json\"),emit: risk_score
>
> tuple val(meta), path(\"virulence_report.pdf\"), emit: pdf_report
>
> script:
>
> \"\"\"
>
> virulence-profile \\
>
> \--input \${fasta} \\
>
> \--vfdb \${vfdb_blast_db} \\
>
> \--virulencefinder \${virulencefinder_db} \\
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
> process CONFIDENCE_SCORING_ALL {
>
> tag \"\${meta.sample_id}\"
>
> label \"process_low\"
>
> cpus 1; memory \"2 GB\"; time \"10.min\"
>
> container \"amr-platform/confidence-scorer:1.0.0\"
>
> input:
>
> tuple val(meta), path(amr_genes_json)
>
> tuple val(meta), path(mutations_tsv)
>
> tuple val(meta), path(mechanisms_json)
>
> tuple val(meta), path(predictions_json)
>
> tuple val(meta), path(virulence_summary_json)
>
> tuple val(meta), path(assembly_metrics_json)
>
> output:
>
> tuple val(meta), path(\"confidence_scores.json\"), emit: conf_json
>
> tuple val(meta), path(\"confidence_components.tsv\"), emit: conf_tsv
>
> tuple val(meta), path(\"confidence_explanations.tsv\"),emit: conf_explain
>
> script:
>
> \"\"\"
>
> confidence-score-all \\
>
> \--amr-genes \${amr_genes_json} \\
>
> \--mutations \${mutations_tsv} \\
>
> \--mechanisms \${mechanisms_json} \\
>
> \--predictions \${predictions_json} \\
>
> \--virulence \${virulence_summary_json} \\
>
> \--assembly \${assembly_metrics_json} \\
>
> \--output-dir .
>
> \"\"\"
>
> }
>
> **SECTION 18 --- TESTING STRATEGY**

  ------------------------------ -------------------------- ---------------------------------------------------------------------------------------------- ------------------------------------------------------------------------------------
  **Test Type**                  **Framework**              **Scope**                                                                                      **Key Assertions**

  Unit Tests                     pytest                     All component scorers, aggregation formula, classifier, VFDB parser, VF classifier             ≥ 95% coverage; known-answer tests for all IDENTITY_THRESHOLDS breakpoints

  Ontology Tests                 pytest                     All gene→category mappings in virulence_ontology.json + gene_map                               fimH → adhesin; stx1 → toxin (high_risk=true); rpoS → stress_response

  Confidence Framework Tests     pytest                     All 4 context weight profiles; genome quality cap; conflict/agreement scenarios                FULL cap \> MEDIUM cap; HIGH tier only ≥ 0.85; COMPLETE_AGREEMENT = 1.0

  Virulence Validation Tests     pytest + FASTA fixtures    E. coli O157:H7 (stx1, stx2, hlyA), UPEC (fimH, papG, hlyA), K. pneumoniae hvKP (iroN, fyuA)   Expected high-risk genes detected; risk class = HIGH or CRITICAL for hypervirulent

  Reference Dataset Validation   pytest + NCBI accessions   5 reference genomes with known virulence profiles                                              Recall ≥ 0.90 vs published VFDB hit lists

  Regression Tests               pytest snapshots           5 reference genomes; identical virulence gene lists and confidence scores                      Zero changes without version increment

  Performance Tests              pytest-benchmark           5 Mb genome; both tools                                                                        VFDB + VirulenceFinder + confidence scoring \< 10 min; confidence_all \< 30 s
  ------------------------------ -------------------------- ---------------------------------------------------------------------------------------------- ------------------------------------------------------------------------------------

> **SECTION 19 --- FINAL OUTPUT FILES**

  ----------------------------- ------------ -----------------------------------------------------------------------------------------------------------------------------------------------------------
  **File**                      **Format**   **Key Contents**

  virulence_factors.tsv         TSV          gene_name, vfdb_id, category_code, function_description, detection_tool, identity_pct, coverage_pct, contig_id, start, end, is_high_risk, confidence_tier

  virulence_annotations.tsv     TSV          vf_id, annotation_source, key, value --- includes function details, PMIDs, VFDB links

  virulence_summary.json        JSON         Complete list of VirulenceFactor objects with all metrics and nested ConfidenceResult

  pathogenicity_profile.json    JSON         PathogenicityProfile dataclass: total VF count, category breakdown, high-risk genes, risk_score, risk_class

  virulence_risk_score.json     JSON         Risk score components (burden, diversity, high-risk), final score, risk_class, high-risk gene list

  confidence_scores.json        JSON         All ConfidenceResult objects for all Module 1 entities (AMR genes, mutations, phenotypes, VF genes)

  confidence_components.tsv     TSV          entity_id, entity_type, component_name, raw_value, weight, weighted_score --- full audit breakdown

  confidence_explanations.tsv   TSV          entity_id, entity_name, explanation_text --- one row per entity

  virulence_report.pdf          PDF          Clinical report: virulence gene table by category, risk score gauge, high-risk alert panel, confidence tier legend
  ----------------------------- ------------ -----------------------------------------------------------------------------------------------------------------------------------------------------------

> **SECTION 20 --- IMPLEMENTATION PLAN AND PACKAGE STRUCTURE**

**20.1 Python Package Structure**

> virulence_engine/ \# Virulence Profiling Package
>
> ├── \_\_init\_\_.py
>
> ├── cli.py \# virulence-profile CLI
>
> ├── result_models.py \# VirulenceRawHit, VirulenceFactor, PathogenicityProfile
>
> ├── adapters/
>
> │ ├── vfdb_adapter.py
>
> │ └── virulencefinder_adapter.py
>
> ├── ontology/
>
> │ ├── virulence_ontology.json
>
> │ ├── gene_category_map.json \# {gene_name: category_code} for 2000+ known genes
>
> │ └── ontology_loader.py
>
> ├── virulence_classifier.py
>
> ├── pathogenicity_profile.py
>
> ├── report_generator.py
>
> ├── db_writer.py
>
> ├── celery_tasks.py
>
> └── tests/
>
> amr_confidence/ \# Global Confidence Framework Package (standalone)
>
> ├── \_\_init\_\_.py \# ConfidenceEngine facade
>
> ├── components/
>
> │ ├── identity_score.py
>
> │ ├── coverage_score.py
>
> │ ├── bitscore_score.py
>
> │ ├── evalue_score.py
>
> │ ├── agreement_score.py
>
> │ └── evidence_strength.py
>
> ├── confidence_aggregation.py
>
> ├── confidence_classifier.py
>
> ├── confidence_explanation.py
>
> ├── modifiers/
>
> │ ├── genome_quality_modifier.py
>
> │ └── prediction_context_modifier.py
>
> └── tests/
>
> └── test_confidence_framework.py

**20.2 Implementation Checklist**

  -------------------------------- ------------------------------------------------------------------------------------------ -------------- -----------------------------------------------------------------------------------------------------------------
  **Phase**                        **Deliverables**                                                                           **Duration**   **Acceptance Criteria**

  1 --- DB adapters                vfdb_adapter.py, virulencefinder_adapter.py                                                3 days         Both adapters produce VirulenceRawHit lists from real tool output; VFDB BLAST parse tested on real output

  2 --- Ontology + classifier      virulence_ontology.json, gene_category_map.json (2000+ entries), virulence_classifier.py   3 days         fimH→adhesin; stx1→toxin(high_risk); all 13 categories present; prefix heuristic handles unknown genes

  3 --- Risk scoring               pathogenicity_profile.py, risk score formula                                               2 days         E. coli O157:H7 fixture produces CRITICAL or HIGH risk class; AMR-only genome produces LOW

  4 --- Confidence components      All 6 component scorer modules in amr_confidence/components/                               2 days         Identity 100% → 1.000; Coverage 60% → 0.550; E-value 1e-20 → 1.000; agreement 4 tools → 1.000

  5 --- Aggregation + classifier   confidence_aggregation.py, confidence_classifier.py, explanation engine                    2 days         Known-answer test: identity=100, coverage=100, 3 tools agree → HIGH; single tool 80% identity → LOW or MEDIUM

  6 --- API + Celery + Nextflow    FastAPI routes, celery_tasks.py, DSL2 processes for virulence + confidence_all             2 days         POST virulence → COMPLETED; GET profile returns risk_score; confidence_all produces scores for all entity types

  7 --- Testing + docs             Full test suite; reference genome validation; benchmark suite                              3 days         ≥ 95% unit coverage; recall ≥ 0.90 on 5 reference genomes; all benchmarks within targets
  -------------------------------- ------------------------------------------------------------------------------------------ -------------- -----------------------------------------------------------------------------------------------------------------
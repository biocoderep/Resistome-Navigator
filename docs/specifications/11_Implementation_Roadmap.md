# 11 — Implementation Roadmap

> **Platform:** AMR Characterisation Engine — Module 1
> **Total sprints:** 12 · **Estimated duration:** 20–24 weeks
> **Reference documents:** Docs 1–10 (SAS/TDD · DDS · ACS · 1A–1G)

---

## Sprint Overview

| Sprint | Name | Weeks | Based On | Key Output |
|--------|------|-------|----------|------------|
| 1 | Foundation Setup | 1 | — | Repository, Codespace, folder structure |
| 2 | Database Layer | 2 | Doc 2 DDS | SQLAlchemy models, Alembic migrations |
| 3 | API Foundation | 2 | Doc 3 ACS | FastAPI app, auth, routers, Swagger UI |
| 4 | Genome Validation Engine | 2 | Doc 4 GVE | `validation_report.json` |
| 5 | Algorithm Library | 1.5 | Doc 5 CAES | `backend/algorithms/` package |
| 6 | AMR Detection Engine | 3 | Doc 6 ADE | `amr_genes.tsv` |
| 7 | Mutation Engine | 2 | Doc 7 RMME | `resistance_mutations.tsv` |
| 8 | Phenotype Prediction Engine | 2 | Doc 8 PPRE | `phenotype_prediction.json`, `module2_input.csv` |
| 9 | Virulence Engine | 2 | Doc 9 VPCE | `virulence_summary.json` |
| 10 | Workflow Integration | 2 | Doc 10 WIDS | Nextflow + Celery + Docker pipeline |
| 11 | End-to-End Testing | 1.5 | All | All output files from single `sample.fasta` |
| 12 | Production Deployment | 1 | Doc 10 WIDS | Live production environment |

---

## Sprint 1 — Foundation Setup

**Goal:** Establish a working, version-controlled development environment that every subsequent sprint builds on.

### Tasks

```
Create GitHub repository (AMR_Platform)
Create GitHub Codespace or configure local dev environment
Configure Python 3.12 virtual environment
Configure ruff (linting) and mypy (type checking)
Configure pytest with coverage reporting
Create folder structure (see Deliverables)
Create .env.example with all required environment variables
Write initial README.md
Set up GitHub Actions: lint + unit test workflow (empty tests pass)
```

### Deliverables

```
AMR_Platform/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── workers/
│   ├── tests/
│   └── requirements.txt
├── algorithms/
├── engines/
├── nextflow/
│   ├── modules/
│   └── subworkflows/
├── containers/
├── deploy/
├── docs/
├── .github/workflows/ci.yml
├── .env.example
└── README.md
```

### Acceptance Criteria

```
✓ Repository created and accessible
✓ Codespace / local environment starts without errors
✓ `ruff check .` passes with zero errors
✓ `pytest backend/tests/` passes (empty suite)
✓ GitHub Actions CI workflow runs green on push
✓ All required directories exist
```

---

## Sprint 2 — Database Layer

**Based on:** `02_Database_Design.md`

**Goal:** Build the complete PostgreSQL schema, all 49 SQLAlchemy models, Alembic migration infrastructure, and seed data.

### Tasks

```
Install SQLAlchemy 2.x async, asyncpg, Alembic
Configure Alembic with async engine (alembic/env.py)
Implement Base, TimestampMixin, SoftDeleteMixin, AuditMixin
Build models for User Domain (users, roles, permissions, user_roles, sessions, api_tokens)
Build models for Project Domain (projects, project_members, project_settings)
Build models for Sample Domain (samples, sample_metadata, sample_files, assemblies, assembly_metrics, validation_reports)
Build models for Reference Domain (reference_databases, database_versions, database_checksums)
Build models for Workflow Domain (analysis_jobs, workflow_runs, workflow_steps, task_logs)
Build models for Analysis Domain (amr_genes, amr_hits, amr_annotations, alignment_results, blast_statistics, mutations, mutation_annotations, mutation_evidence, mechanism_classes, mechanisms, gene_mechanisms, mutation_mechanisms, gene_evidence, phenotype_predictions, prediction_evidence, prediction_rules, virulence_factors, virulence_annotations, drug_associations)
Build models for Reporting Domain (reports, report_files, module2_exports)
Build models for Audit Domain (audit_logs, change_history, data_lineage)
Build models for Module 2/3 reserved tables (gp_concordance_studies, gp_concordance_results, mge_elements)
Build models for Confidence Domain (confidence_scores, confidence_components, similarity_metrics)
Create Alembic migration: 0001_create_all_tables
Create seed script: scripts/db_seed.py (mechanism_classes, reference_databases, roles)
Write unit tests for all models (field types, constraints, relationships)
Start Docker Compose with postgres service only; run migration
```

### Deliverables

```
backend/app/models/
├── base.py               (Base, TimestampMixin, SoftDeleteMixin, AuditMixin)
├── user.py
├── project.py
├── sample.py
├── reference.py
├── workflow.py
├── amr.py
├── mutation.py
├── mechanism.py
├── phenotype.py
├── virulence.py
├── confidence.py
├── reporting.py
├── audit.py
└── future_modules.py

alembic/
├── env.py
├── versions/
│   └── 0001_create_all_tables.py
└── script.py.mako

scripts/db_seed.py
```

### Acceptance Criteria

```
✓ `alembic upgrade head` runs without errors on fresh PostgreSQL instance
✓ All 49 tables created with correct columns, types, and constraints
✓ `alembic downgrade -1` runs without errors
✓ db_seed.py populates mechanism_classes (10 rows) and roles (5 rows)
✓ Model unit tests pass (relationships, cascade rules)
✓ `pytest backend/tests/unit/test_models.py` green
```

---

## Sprint 3 — API Foundation

**Based on:** `03_API_Specification.md`

**Goal:** Build a working FastAPI application with JWT authentication, RBAC, all router stubs, request/response schemas, and Swagger UI accessible.

### Tasks

```
Install FastAPI, uvicorn, python-jose, passlib, pydantic v2
Configure application factory (app/main.py)
Configure async database session (app/core/database.py)
Configure Redis connection (app/core/redis.py)
Implement JWT RS256 key generation and validation (app/core/security.py)
Implement CorrelationIDMiddleware and RequestLoggingMiddleware
Build auth router: POST /auth/register, /auth/login, /auth/logout, /auth/refresh, GET /auth/me
Build users router: GET/PUT/DELETE /users/{id}, PATCH /users/{id}/status
Build projects router: full CRUD + members + settings endpoints
Build samples router: CRUD + bulk-upload stub
Build files router: upload, chunked upload init/chunk/complete, download, delete
Build module1 router stubs: /validate, /amr-detection, /mutations, /mechanisms, /predict, /virulence, /workflow, /reports
Implement Pydantic schemas for all request/response models
Implement pagination (PaginationParams), filtering base
Implement rate limiting via Redis sliding window
Write integration tests for auth flow (register → login → refresh → logout)
Write integration tests for project/sample CRUD
Configure Swagger UI and ReDoc
```

### Deliverables

```
backend/app/
├── api/v1/
│   ├── auth.py
│   ├── users.py
│   ├── projects.py
│   ├── samples.py
│   ├── files.py
│   └── module1/ (stubs returning 501 Not Implemented)
├── core/
│   ├── config.py
│   ├── database.py
│   ├── redis.py
│   ├── security.py
│   └── middleware.py
└── schemas/
    ├── auth.py
    ├── user.py
    ├── project.py
    ├── sample.py
    ├── file.py
    └── common.py (PaginationParams, APIResponse, ErrorResponse)
```

### Acceptance Criteria

```
✓ GET /api/v1/health returns 200
✓ Swagger UI available at /api/v1/docs
✓ Full JWT auth flow works end-to-end: register → login → use token → refresh → logout
✓ POST /projects creates project; GET /projects returns it
✓ RBAC: VIEWER cannot POST /samples → 403 Forbidden
✓ Rate limit: 1001st request in 1 hour returns 429
✓ Integration tests pass: pytest backend/tests/integration/test_auth.py
```

---

## Sprint 4 — Genome Validation Engine

**Based on:** `04_Genome_Validation_Engine.md`

**Goal:** Build the complete Module 1A genome validation engine, connect it to the API and Celery, and produce `validation_report.json`.

### Tasks

```
Install biopython, datasketch, numpy, scipy, matplotlib, weasyprint
Build genome_validator/ package (19 modules per GVE spec)
Implement integrity.py: MD5, SHA256, gzip detection, record count
Implement input_validator.py: FASTA structure, IUPAC characters, duplicate headers
Implement statistics.py: total length, contig count, N50/N90/L50, mean/median/max contig
Implement gc_analysis.py: whole-genome GC, per-contig GC, outlier detection
Implement ambiguity.py: N%, N-run detection, per-contig analysis
Implement contig_analysis.py: fragmentation classification, length distribution
Implement duplicate_detector.py: hash + MinHash (datasketch)
Implement complexity.py: Shannon entropy, homopolymer detection
Implement kmer_analysis.py: k=21/31/51 spectra, contamination signals
Implement genome_size.py: size range validation
Implement taxonomy.py: Mash species prediction stub (CLI wrapper)
Implement contamination.py: risk aggregation from all signals
Implement quality_scorer.py: composite 7-component score formula
Implement decision_engine.py: PASS/WARNING/FAIL + confidence_cap
Implement report_generator.py: 14 output JSON/TSV files + PDF
Implement db_writer.py: persist metrics to assembly_metrics, validation_reports
Create Celery task: validate_genome_task (16-step progress)
Wire POST /module1/validate → Celery task dispatch
Wire GET /module1/validate/{job_id} → job status poll
Wire GET /module1/validate/{job_id}/results → results from DB
Write unit tests with 6 reference FASTA fixtures (valid, invalid, N-rich, contaminated, small, duplicates)
```

### Deliverables

```
engines/genome_validator/
├── __init__.py
├── cli.py
├── engine.py
├── models.py
├── integrity.py
├── input_validator.py
├── statistics.py
├── gc_analysis.py
├── ambiguity.py
├── contig_analysis.py
├── duplicate_detector.py
├── complexity.py
├── kmer_analysis.py
├── genome_size.py
├── taxonomy.py
├── contamination.py
├── quality_scorer.py
├── decision_engine.py
├── report_generator.py
└── db_writer.py

containers/genome_validator/Dockerfile

Output files (per sample):
validation_report.json, assembly_metrics.json, gc_analysis.json,
ambiguity_report.json, contig_report.json, duplicate_contig_report.json,
complexity_report.json, kmer_report.json, genome_size_report.json,
taxonomy_consistency_report.json, contamination_report.json,
quality_score.json, validation_status.json, final_validation_report.pdf
```

### Acceptance Criteria

```
✓ E. coli K-12 reference FASTA produces: status=PASS, quality_class=EXCELLENT
✓ Synthetic N-rich FASTA (8% N) produces: status=FAIL, error code N_PERCENT_EXCEEDED
✓ 5 Mb FASTA completes in < 120 seconds end-to-end
✓ All 14 output files generated and non-empty
✓ PDF report renders correctly
✓ Unit test suite: ≥ 95% coverage on genome_validator/ package
✓ API: POST /validate → 202 job_id; GET status → COMPLETED
```

---

## Sprint 5 — Algorithm Library

**Based on:** `05_Algorithm_Engine.md`

**Goal:** Build the reusable `amr_confidence/` global confidence framework and all algorithm modules. These are consumed by every subsequent engine.

### Tasks

```
Create algorithms/ package structure
Implement alignment/smith_waterman.py: DP matrix, traceback, vectorised NumPy version
Implement alignment/needleman_wunsch.py: global alignment, affine gap penalties
Implement alignment/alignment_metrics.py: identity%, coverage%, gap%, mismatch%
Implement alignment/substitution_matrices.py: BLOSUM62/80/45, PAM30/70/250, NUC4.4 JSON loader with @lru_cache
Implement search/bwt_engine.py: BWT construction, inverse BWT
Implement search/fmindex_engine.py: FMIndex class, count(), locate()
Implement search/bwa_mem_engine.py: BWAMemEngine, find_mems(), align()
Implement statistics/blast_statistics.py: bit_score(), e_value(), score_hit()
Implement statistics/statistics_engine.py: describe(), z_scores(), confidence_interval(), normalise_score()
Implement similarity/kmer_engine.py: build_kmer_profile(), kmer_statistics(), compare_kmer_profiles()
Implement similarity/minhash_engine.py: build_minhash(), jaccard_similarity(), build_lsh_index(), genome_similarity()
Implement similarity/similarity_engine.py: jaccard(), cosine(), mash_distance(), edit_distance()
Implement utilities/result_models.py: AlgorithmResult dataclass
Implement utilities/sequence_utils.py: complement(), reverse_complement(), normalise()

Build amr_confidence/ package (standalone):
Implement components/identity_score.py (piecewise thresholds)
Implement components/coverage_score.py (piecewise + partial_expected flag)
Implement components/bitscore_score.py (normalised to ref_length × 2)
Implement components/evalue_score.py (log-ratio formula)
Implement components/agreement_score.py ({4:1.0, 3:0.9, 2:0.75, 1:0.55})
Implement components/evidence_strength.py (5-level weight map)
Implement confidence_aggregation.py: aggregate() with 4-context weight profiles
Implement confidence_classifier.py: HIGH/MEDIUM/LOW thresholds
Implement confidence_explanation.py: explain_confidence()
Implement modifiers/genome_quality_modifier.py: GENOME_CAP dict
Write known-answer unit tests for every algorithm (SW, NW, bit score, E-value, MinHash, FMIndex)
Write performance benchmarks (pytest-benchmark)
```

### Deliverables

```
algorithms/
├── alignment/
├── search/
├── statistics/
├── similarity/
└── utilities/

amr_confidence/
├── __init__.py
├── components/ (6 scorers)
├── confidence_aggregation.py
├── confidence_classifier.py
├── confidence_explanation.py
└── modifiers/
```

### Acceptance Criteria

```
✓ SW known-answer: ACACACTA vs AGCACACA (match=1,mismatch=-1,gap=-1) → score=4.0
✓ NW known-answer: GCATGCU vs GATTACA → score=0.0
✓ Bit score known-answer: raw=100, λ=1.28, K=0.46 → 185.17 ± 0.01
✓ FMIndex count("ACGT") on sequence containing "ACGT" twice → 2
✓ MinHash: identical sequences → Jaccard = 1.0
✓ amr_confidence: identity=100%, coverage=100%, 4 tools agree, experimental evidence → HIGH (≥ 0.85)
✓ All benchmark targets met (SW for 500bp pair < 5ms)
✓ ≥ 95% unit test coverage on all algorithm modules
```

---

## Sprint 6 — AMR Detection Engine

**Based on:** `06_AMR_Detection_Engine.md`

**Goal:** Build the complete Module 1C AMR detection engine integrating CARD RGI, AMRFinderPlus, ResFinder, and Abricate, with evidence aggregation, deduplication, ontology mapping, and confidence scoring.

### Tasks

```
Build engines/amr_detection/ package
Implement database_manager.py: DatabaseManager with download(), verify(), activate(), rollback()
Implement genome_parser.py: ContigRecord dataclass, parse_genome()
Implement result_models.py: RawHit, AggregatedGene, AMRGeneResult dataclasses
Implement adapters/card_adapter.py: CARDAdapter, RGI subprocess wrapper + parser
Implement adapters/amrfinder_adapter.py: AMRFinderAdapter, TSV parser
Implement adapters/resfinder_adapter.py: RESFinderAdapter, result parser
Implement adapters/abricate_adapter.py: AbricateAdapter, multi-db runner
Implement hit_metrics.py: identity_pct(), coverage_pct(), classify_hit() (Perfect/Strict/Loose/Nudged)
Implement ontology_mapper.py: OntologyMapper with @lru_cache, ARO JSON loader
Implement evidence_aggregation.py: aggregate_hits(), AggregatedGene builder
Implement deduplication_engine.py: find_overlapping_hits(), merge logic
Implement drug_classification.py: DRUG_CLASS_MAP normalisation dict
Implement mechanism_preannotation.py: MECHANISM_MAP + GENE_PREFIX_MECHANISM heuristic
Implement confidence_engine.py: 5-component weighted formula
Implement report_generator.py: amr_genes.tsv, amr_genes.json, amr_hits.tsv, gene_evidence.tsv, drug_classification.tsv, confidence_scores.json, amr_detection_report.pdf
Implement db_writer.py: persist to amr_genes, amr_hits, amr_annotations, gene_evidence
Create Celery task: amr_detection_task (13-step progress)
Wire /module1/amr-detection endpoints
Create containers/amr_detection/Dockerfile
Write unit tests with mocked subprocess calls per adapter
Write reference genome integration tests (5 NCBI genomes)
```

### Deliverables

```
engines/amr_detection/
├── __init__.py (AMRDetectionEngine)
├── database_manager.py
├── genome_parser.py
├── result_models.py
├── adapters/
│   ├── card_adapter.py
│   ├── amrfinder_adapter.py
│   ├── resfinder_adapter.py
│   └── abricate_adapter.py
├── hit_metrics.py
├── ontology_mapper.py
├── evidence_aggregation.py
├── deduplication_engine.py
├── drug_classification.py
├── mechanism_preannotation.py
├── confidence_engine.py
├── report_generator.py
├── db_writer.py
└── celery_tasks.py

Output files (per sample):
amr_genes.tsv, amr_genes.json, amr_hits.tsv,
gene_evidence.tsv, drug_classification.tsv,
confidence_scores.json, amr_detection_report.pdf
```

### Acceptance Criteria

```
✓ E. coli UTI89 → blaTEM-1, aac(3)-IV, sul1 detected (recall ≥ 0.95)
✓ E. coli K-12 (AMR-negative) → zero AMR genes (precision = 100%)
✓ K. pneumoniae KPNIH1 → blaKPC-2 detected as Perfect hit, confidence = HIGH
✓ blaCTX-M-15 hit → mechanism_type = antibiotic_inactivation; drug_class = cephalosporin
✓ 4 tools agree on blaCTX-M-15 → agreement_score = 1.0
✓ 5 Mb E. coli genome completes in < 15 minutes
✓ Unit tests ≥ 95% coverage; all adapter parsers tested with real tool output fixtures
```

---

## Sprint 7 — Mutation Engine

**Based on:** `07_Mutation_Mechanism_Engine.md`

**Goal:** Build the complete Module 1D resistance mutation detection and mechanism classification engine, including the mutation knowledgebase and drug association engine.

### Tasks

```
Build engines/mutation_engine/ package
Create mutation_knowledgebase.json (seed with ≥ 50 entries: gyrA, gyrB, parC, parE, rpoB, mgrB, 23S rRNA, pbp2, rpsL)
Create mechanism_ontology.json (10 mechanism classes with risk weights)
Implement knowledgebase/loader.py: load + validate knowledgebase, LRU cache
Implement ontology/ontology_loader.py
Implement gene_localization.py: BLAST pre-screen + NW refinement, GeneLocation dataclass
Implement variant_detection.py: call_variants(), detect_stop_codons(), _annotate_frameshifts()
Implement variant_annotation.py: annotate_variant(), HGVS notation, domain lookup
Implement mutation_mapper.py: map_mutation(), KNOWN/LIKELY/NOVEL/SILENT/UNKNOWN classification
Implement mutation_confidence.py: 4-component weighted formula, kb_evidence_score()
Implement novel_mutation_detector.py: NOVEL_IN_DOMAIN, NOVEL_IN_GENE, LIKELY_RESISTANCE flags
Implement mutation_prioritizer.py: 4-component priority score formula, prioritized_mutations.tsv
Implement mechanism_classifier.py: MechanismClassifier (3-tier ARO/KB/heuristic)
Implement mechanism_evidence.py: MechanismObject aggregation, aggregate_mechanisms()
Implement drug_association.py: DrugAssociation dataclass, CROSS_RESISTANCE dict
Implement report_generator.py: 8 output files + PDF
Implement db_writer.py: persist to mutations, mutation_annotations, mutation_mechanisms, drug_associations
Create Celery tasks: mutation_detection_task + mechanism_classification_task
Wire /module1/mutations and /module1/mechanisms endpoints
Create containers/mutation_engine/Dockerfile
Write unit tests with 6 synthetic mutation FASTA fixtures
```

### Deliverables

```
engines/mutation_engine/
├── knowledgebase/mutation_knowledgebase.json
├── ontology/mechanism_ontology.json
├── gene_localization.py
├── variant_detection.py
├── variant_annotation.py
├── mutation_mapper.py
├── mutation_confidence.py
├── novel_mutation_detector.py
├── mutation_prioritizer.py
├── mechanism_classifier.py
├── mechanism_evidence.py
├── drug_association.py
├── report_generator.py
├── db_writer.py
└── celery_tasks.py

Output files (per sample):
resistance_mutations.tsv, mutation_annotations.tsv,
mutation_evidence.tsv, mechanism_summary.json,
mechanism_per_gene.tsv, drug_associations.tsv,
novel_mutation_report.json, prioritized_mutations.tsv,
mutation_report.pdf
```

### Acceptance Criteria

```
✓ gyrA S83L engineered FASTA → KNOWN_RESISTANCE, classification=missense, drug_class=fluoroquinolone, SIR=I
✓ mgrB IS-insertion FASTA → variant_type=STOP/INS, mechanism=membrane_remodeling, SIR=R (colistin)
✓ rpoB S531L FASTA → KNOWN_RESISTANCE, SIR=R (rifampicin), evidence_level=1
✓ Novel QRDR position → NOVEL_IN_DOMAIN flag, SIR=INDETERMINATE
✓ mechanism_classifier: blaCTX-M-15 → antibiotic_inactivation (Tier 1 ARO); gyrA S83L → target_alteration (Tier 2 KB)
✓ Unit tests: ≥ 95% coverage; all 6 synthetic mutation fixtures produce expected outputs
```

---

## Sprint 8 — Phenotype Prediction Engine

**Based on:** `08_Phenotype_Prediction_Engine.md`

**Goal:** Build the complete Module 1E phenotype prediction rule engine with gene/mutation/mechanism/combinatorial rules, EUCAST/CLSI integration, conflict resolution, and Module 2 export.

### Tasks

```
Build engines/phenotype_engine/ package
Create rule_repository.json (seed with ≥ 100 rules covering all major drug classes)
Build breakpoints/eucast_adapter.py: BreakpointRecord, EUCASTAdapter.get_breakpoint()
Build breakpoints/clsi_adapter.py
Add EUCAST v13.0 breakpoint TSV data files
Build rules/gene_rule_engine.py: GeneRuleEngine.evaluate(), _condition_met()
Build rules/mutation_rule_engine.py: MutationRuleEngine.evaluate()
Build rules/mechanism_rule_engine.py: MechanismRuleEngine.evaluate()
Build rules/combinatorial_rules.py: CombinatorialRuleEngine (all_of/any_of)
Build inference/inheritance_engine.py: InheritanceEngine.resolve()
Build inference/conflict_resolution.py: resolve_conflicts(), SIR_PRIORITY dict
Build inference/confidence_propagation.py: propagate_confidence(), GENOME_CAP dict
Build inference/phenotype_inference.py: PhenotypeInferenceEngine.predict()
Build mathematical/ecoff_engine.py: compute_ecoff(), classify_vs_ecoff()
Build mathematical/hill_equation_engine.py: hill_response(), fit_hill_curve()
Build explanation_engine.py: generate_explanation()
Build module2_export.py: export_module2_csv(), SCHEMA_VERSION = "1.0.0"
Build report_generator.py: 7 output files + PDF
Build db_writer.py: persist to phenotype_predictions, prediction_evidence, prediction_explanations, module2_exports
Create Celery task: phenotype_prediction_task (12-step progress)
Wire /module1/predict endpoints
Write unit tests: all 5 rule types; conflict resolution; confidence propagation; EUCAST lookup
Write reference phenotype validation tests (5 isolates with known phenotypes)
```

### Deliverables

```
engines/phenotype_engine/
├── rules/rule_repository.json (≥ 100 rules)
├── breakpoints/eucast_adapter.py + clsi_adapter.py + data files
├── rules/ (4 rule engines)
├── inference/ (4 modules)
├── mathematical/ (ecoff + hill)
├── explanation_engine.py
├── module2_export.py
├── report_generator.py
└── celery_tasks.py

Output files (per sample):
phenotype_prediction.json, phenotype_predictions.tsv,
prediction_evidence.tsv, prediction_explanations.tsv,
confidence_scores.json, module2_input.csv,
phenotype_prediction_report.pdf
```

### Acceptance Criteria

```
✓ blaCTX-M-15 (Perfect hit) → ceftriaxone = R, confidence = HIGH (≥ 0.90)
✓ gyrA S83L alone → ciprofloxacin = I (not full R)
✓ gyrA S83L + parC S80I → ciprofloxacin = R (combinatorial rule fires)
✓ Conflict resolution: R always wins over I; I always wins over S
✓ Genome quality MEDIUM cap: no prediction exceeds confidence = 0.75
✓ module2_input.csv: schema_version=1.0.0; passes CSV schema validation
✓ Reference isolate validation: sensitivity ≥ 0.90; specificity ≥ 0.90
✓ Unit tests ≥ 95% coverage
```

---

## Sprint 9 — Virulence Engine

**Based on:** `09_Virulence_Confidence_Engine.md`

**Goal:** Build Module 1F virulence profiling engine (VFDB + VirulenceFinder) and run the global confidence scoring framework across all Module 1 outputs.

### Tasks

```
Build engines/virulence_engine/ package
Build virulence_ontology.json (12 categories with risk_weight values)
Build gene_category_map.json (≥ 500 gene → category mappings)
Build adapters/vfdb_adapter.py: VFDBAdapter, BLASTn execution, BLAST-6 parser
Build adapters/virulencefinder_adapter.py: VirulenceFinderAdapter, JSON result parser
Build virulence_classifier.py: VirulenceClassifier, _lookup_category() with prefix heuristic
Build pathogenicity_profile.py: compute_risk_score(), PathogenicityProfile, risk classification
Build report_generator.py: 9 output files + PDF
Build db_writer.py: persist to virulence_factors, virulence_annotations, virulence_profiles
Create Celery task: virulence_profiling_task + confidence_scoring_task (9-step progress)
Build confidence scoring all-module task: reads all Module 1 outputs, applies amr_confidence framework to every entity, writes confidence_scores, confidence_components tables
Wire /module1/virulence endpoints
Wire GET /module1/confidence/{job_id}
Create containers/virulence_profiler/Dockerfile and containers/confidence_scorer/Dockerfile
Write unit tests: VFDB parser, classifier, risk score formula
Write reference genome validation tests (E. coli O157:H7 → stx1, stx2, hlyA detected; CRITICAL risk class)
```

### Deliverables

```
engines/virulence_engine/
├── ontology/virulence_ontology.json
├── ontology/gene_category_map.json
├── adapters/vfdb_adapter.py
├── adapters/virulencefinder_adapter.py
├── virulence_classifier.py
├── pathogenicity_profile.py
├── report_generator.py
└── celery_tasks.py

Output files (per sample):
virulence_factors.tsv, virulence_annotations.tsv,
virulence_summary.json, pathogenicity_profile.json,
virulence_risk_score.json, confidence_scores.json,
confidence_components.tsv, confidence_explanations.tsv,
virulence_report.pdf
```

### Acceptance Criteria

```
✓ E. coli O157:H7 → stx1, stx2, hlyA detected; risk_class = CRITICAL or HIGH
✓ AMR-only E. coli K-12 → 0 virulence genes; risk_class = LOW
✓ Identity 100%, coverage 100%, VFDB + VirulenceFinder agree → confidence tier = HIGH
✓ Single VFDB hit, identity 78% → confidence tier = LOW
✓ confidence_scoring_all task: all amr_genes, mutations, phenotype_predictions, virulence_factors have confidence_score populated
✓ 5 Mb genome: VFDB + VirulenceFinder + confidence_all < 10 minutes
✓ Unit tests ≥ 95% coverage
```

---

## Sprint 10 — Workflow Integration

**Based on:** `10_Workflow_Deployment.md`

**Goal:** Wire all engines into a complete Nextflow DSL2 pipeline orchestrated by Celery, served behind Docker Compose with Nginx.

### Tasks

```
Build nextflow/main.nf: 4-stage MODULE1_AMR_PIPELINE workflow
Build nextflow/nextflow.config: resource labels, Docker executor, params
Build nextflow/modules/ (14 .nf process files)
Build nextflow/subworkflows/ (6 subworkflow files)
Build containers/api/Dockerfile (multi-stage)
Build containers/amr_detection/Dockerfile (CARD + AMRFinder + ResFinder + Abricate)
Build containers/mutation_engine/Dockerfile
Build containers/phenotype_engine/Dockerfile
Build containers/virulence_profiler/Dockerfile
Build containers/confidence_scorer/Dockerfile
Build containers/nextflow/Dockerfile (Java 17 + Nextflow)
Build deploy/docker-compose.yml (all 11 services)
Build deploy/nginx/nginx.conf (reverse proxy, TLS, rate limiting)
Configure Celery pipeline chain: validate → amr+mutation parallel → mechanisms → phenotype+virulence parallel → confidence → module2 → reports
Configure WebSocket progress streaming from Celery task updates to Redis pub/sub to client
Configure MinIO bucket lifecycle policies
Set up Flower dashboard
Run full pipeline on 1 test genome: submit via API → track via WebSocket → download PDF
Write nf-test workflow tests for all 14 Nextflow processes
```

### Deliverables

```
nextflow/
├── main.nf
├── nextflow.config
├── modules/ (14 .nf files)
└── subworkflows/ (6 .nf files)

deploy/
├── docker-compose.yml
├── docker-compose.dev.yml
└── nginx/nginx.conf

containers/ (7 Dockerfiles)
```

### Acceptance Criteria

```
✓ docker compose up --build starts all 11 containers without errors
✓ All containers pass their health checks within 60 seconds
✓ Single genome submitted via POST /module1/predict → job completes end-to-end → PDF accessible via presigned URL
✓ WebSocket /ws/jobs/{job_id} receives all progress events from 0% to 100%
✓ Nextflow -resume: re-running completed pipeline skips completed processes
✓ nf-test: all 14 process tests pass
✓ Flower dashboard accessible at :5555 showing completed tasks
```

---

## Sprint 11 — End-to-End Testing

**Goal:** Validate the complete platform against a reference test genome, ensure all output files are correct, achieve coverage targets, and pass security scan.

### Tasks

```
Run full pipeline on 5 reference genomes; verify all outputs match expected profiles
Run regression test baseline: snapshot all output files for future regression detection
Execute load test: k6 script simulating 100 concurrent users, 500 sample submissions/hour
Execute ZAP DAST scan against staging deployment; remediate any High/Critical findings
Execute contract test suite (schemathesis) against all 56 API endpoints
Execute nf-test full workflow suite
Verify module2_input.csv: schema validation, row counts, all required fields populated
Verify PDF reports render correctly on all 5 reference genomes
Write / complete end-to-end Playwright tests (register → upload → run → download)
Achieve ≥ 90% overall unit test coverage
Fix any failures; document known limitations
```

### Input

```
sample.fasta (one of 5 reference genomes, e.g. E. coli UTI89)
```

### Expected Outputs (all must be present and valid)

```
validation_report.json        (status = PASS or PASS_WITH_WARNINGS)
assembly_metrics.json         (all numeric fields populated)
amr_genes.tsv                 (≥ 1 gene detected for AMR-positive genomes)
amr_genes.json                (matches TSV content; confidence_tier present)
resistance_mutations.tsv      (KNOWN mutations present for appropriate genomes)
mechanism_summary.json        (mechanism_code for each gene/mutation)
phenotype_prediction.json     (S/I/R for all configured antibiotics)
module2_input.csv             (schema_version=1.0.0; all columns present)
virulence_summary.json        (virulence_factors array; risk_score populated)
confidence_scores.json        (every entity has overall_score and tier)
amr_detection_report.pdf      (renders; file size > 10 KB)
phenotype_prediction_report.pdf
virulence_report.pdf
```

### Acceptance Criteria

```
✓ All 13 expected output files present and valid for all 5 reference genomes
✓ AMR recall ≥ 0.95 on benchmark; precision ≥ 0.90; zero false positives on negative control
✓ Mutation detection: all 6 known mutations detected in synthetic mutation fixtures
✓ Phenotype prediction: sensitivity ≥ 0.90 on reference phenotype validation set
✓ Load test: zero 5xx errors; p99 < 5s for job submission; 500 samples/hour sustained
✓ ZAP DAST: zero Critical or High security findings
✓ Overall unit test coverage ≥ 90%
✓ All API contract (schemathesis) tests pass
```

---

## Sprint 12 — Production Deployment

**Goal:** Deploy the AMR Platform to a production environment with monitoring, alerting, backup, and operational runbooks.

### Tasks

```
Provision production server / cloud instance (≥ 32 CPU, 128 GB RAM, 2 TB SSD)
Generate production secrets: JWT RS256 keypair, DB password, Redis password, MinIO keys
Deploy using docker-compose.prod.yml with production config
Run alembic upgrade head on production database
Run db_seed.py to populate reference data
Configure SSL certificate (Let's Encrypt via certbot or acme.sh)
Configure MinIO bucket policies and lifecycle rules
Import reference databases (CARD, AMRFinderPlus, ResFinder, VFDB)
Import breakpoint tables (EUCAST v13.0, CLSI M100)
Import mutation knowledgebase and rule repository
Set up Prometheus scraping all services
Import Grafana dashboards (5 dashboards per monitoring spec)
Configure alerting rules in Grafana (8 alerts per alerting spec)
Configure SMTP for alert notifications
Test pg_basebackup + WAL archiving to MinIO; verify restore
Test MinIO mirror to off-site storage
Write and test DR runbook (restore from backup to staging)
Submit 3 real test genomes; verify end-to-end on production
Write operator training notes
```

### Deliverables

```
Production environment:
  - All 11 containers running and healthy
  - Monitoring stack live with 5 dashboards
  - 8 Grafana alerts configured
  - Backup scripts scheduled (cron)
  - SSL certificate active
  - Reference databases loaded

Documentation:
  - ops/runbooks/backup_restore.md
  - ops/runbooks/reference_db_update.md
  - ops/runbooks/incident_response.md
  - ops/runbooks/new_user_onboarding.md
```

### Acceptance Criteria

```
✓ All containers pass health checks in production
✓ HTTPS accessible; TLS grade A (SSL Labs test)
✓ 3 real genomes processed end-to-end; PDFs downloadable
✓ Monitoring: all metrics visible in Grafana Platform Overview dashboard
✓ Alert test: trigger test alert → notification received via email
✓ Backup restore test: restore staging DB from production backup → data matches
✓ Uptime monitoring: platform accessible 99.5%+ over first 7 days
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| CARD RGI version incompatibility | MEDIUM | HIGH | Pin container image tag; test on new releases before upgrade |
| AMRFinderPlus organism-mode missing species | MEDIUM | MEDIUM | Default to no-organism mode; log warning; do not fail pipeline |
| Reference database size changes break disk capacity | LOW | HIGH | Monitor disk; lifecycle policies; alert at 75% capacity |
| Nextflow Docker executor permission issues | MEDIUM | HIGH | Test on target OS early; use UID 1000 consistently |
| EUCAST breakpoint updates change predictions | LOW | HIGH | New EUCAST version = new breakpoint_version field; old results unaffected |
| Module 2 schema incompatibility | LOW | CRITICAL | Semantic versioning on module2_input.csv; v1.0.0 contract locked |

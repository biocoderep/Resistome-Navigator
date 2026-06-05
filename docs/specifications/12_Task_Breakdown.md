# 12 — Task Breakdown

> **Format:** Day-by-day task assignments across all 12 sprints.
> Each day = one focused unit of work (roughly 6–8 hours of implementation).
> Days assume a 5-day work week. Adjust dates to your calendar start.

---

## Sprint 1 — Foundation Setup (Days 1–5)

### Day 1 — Repository and Environment

```
Create GitHub repository: AMR_Platform
Add .gitignore (Python, Node, .env, *.pyc, __pycache__, .nextflow/)
Create README.md with project overview and quick-start
Set up GitHub Codespace devcontainer.json OR local venv with Python 3.12
Install development tools: ruff, mypy, pytest, pytest-cov, pre-commit
Configure pre-commit hooks: ruff, trailing whitespace, end-of-file newline
Test: `ruff check .` passes; `python --version` = 3.12.x
```

### Day 2 — Folder Structure

```
Create complete directory tree (all folders from 11_Implementation_Roadmap.md Sprint 1)
Create __init__.py files for all Python packages
Create .env.example with all required keys (DATABASE_URL, REDIS_URL, S3_ENDPOINT, JWT_PRIVATE_KEY_PATH, etc.)
Create .env (not committed) with development values
Create requirements.txt with all top-level dependencies
Create requirements-dev.txt (pytest, ruff, mypy, pytest-cov, schemathesis)
Test: import all packages from requirements.txt without error
```

### Day 3 — GitHub Actions CI

```
Create .github/workflows/ci.yml
Implement: lint job (ruff check)
Implement: unit_tests job (pytest backend/tests/unit/ with empty suite)
Implement: security job (pip-audit with zero-warning exit)
Configure GitHub secrets: CODECOV_TOKEN (if using codecov)
Push to GitHub; verify CI passes green
```

### Day 4 — Docker Foundation

```
Create deploy/docker-compose.yml with postgres and redis services only
Create deploy/.env (docker compose env vars)
Verify: `docker compose up postgres redis` starts both containers healthy
Create scripts/ directory; create scripts/db_seed.py stub (prints "seed placeholder")
Create docs/architecture/ directory; copy Doc 1–10 references
```

### Day 5 — Sprint 1 Review

```
Verify all acceptance criteria from Sprint 1 checklist
Create SPRINT_1_COMPLETE.md with checklist output
Push final commit; verify CI green
Create Sprint 2 GitHub milestone and issue labels
```

---

## Sprint 2 — Database Layer (Days 6–15)

### Day 6 — SQLAlchemy Core Setup

```
pip install sqlalchemy[asyncio] asyncpg alembic psycopg2-binary
Create backend/app/core/config.py: Settings class with pydantic-settings
Create backend/app/core/database.py: async engine, session factory, get_db dependency
Create backend/app/models/base.py: Base, TimestampMixin, SoftDeleteMixin, AuditMixin
Test: connect to PostgreSQL from Python; create engine; echo CREATE TABLE
```

### Day 7 — User Domain Models

```
Create backend/app/models/user.py: User, Role, Permission, UserRole, Session, APIToken
Define all columns, relationships, cascade rules per DDS Section 4
Write unit tests: backend/tests/unit/test_models_user.py
Test: instantiate models; verify relationships
```

### Day 8 — Project and Sample Domain Models

```
Create backend/app/models/project.py: Project, ProjectMember, ProjectSettings
Create backend/app/models/sample.py: Sample, SampleMetadata, SampleFile, Assembly, AssemblyMetrics, ValidationReport
Write unit tests: test_models_project.py, test_models_sample.py
```

### Day 9 — Reference and Workflow Domain Models

```
Create backend/app/models/reference.py: ReferenceDatabase, DatabaseVersion, DatabaseChecksum
Create backend/app/models/workflow.py: AnalysisJob, WorkflowRun, WorkflowStep, TaskLog
Write unit tests: test_models_reference.py, test_models_workflow.py
```

### Day 10 — Analysis Domain Models (Part 1)

```
Create backend/app/models/amr.py: AMRGene, AMRHit, AMRAnnotation, AlignmentResult, BlastStatistic, GeneEvidence
Create backend/app/models/mechanism.py: MechanismClass, Mechanism, GeneMechanism, MutationMechanism
Write unit tests
```

### Day 11 — Analysis Domain Models (Part 2)

```
Create backend/app/models/mutation.py: Mutation, MutationAnnotation, MutationEvidence, DrugAssociation
Create backend/app/models/phenotype.py: PhenotypePrediction, PredictionEvidence, PredictionRule, PredictionExplanation, Module2Export
Write unit tests
```

### Day 12 — Remaining Domain Models

```
Create backend/app/models/virulence.py: VirulenceFactor, VirulenceAnnotation, VirulenceProfile
Create backend/app/models/confidence.py: ConfidenceScore, ConfidenceComponent, SimilarityMetric
Create backend/app/models/reporting.py: Report, ReportFile
Create backend/app/models/audit.py: AuditLog, ChangeHistory, DataLineage
Create backend/app/models/future_modules.py: GPConcordanceStudy, GPConcordanceResult, MGEElement
Write all remaining model unit tests
```

### Day 13 — Alembic Configuration

```
alembic init alembic
Configure alembic/env.py for async SQLAlchemy; import all models
Run: alembic revision --autogenerate -m "create_all_tables"
Review generated migration; verify all 49 tables present
Run: alembic upgrade head on local PostgreSQL; verify with \dt
Run: alembic downgrade -1; verify tables dropped; run upgrade head again
```

### Day 14 — Seed Script and Docker Compose Update

```
Implement scripts/db_seed.py:
  - Insert MechanismClass records (10 rows from mechanism_ontology.json)
  - Insert ReferenceDatabase records (CARD, AMRFinderPlus, ResFinder, VFDB, VirulenceFinder)
  - Insert Role records (SUPERADMIN, ADMIN, PROJECT_OWNER, ANALYST, VIEWER)
  - Insert default EUCAST and CLSI breakpoint records
Run db_seed.py against local DB; verify rows inserted
Update docker-compose.yml to run migrations + seed on startup (init container pattern)
```

### Day 15 — Sprint 2 Review

```
Run full test suite: pytest backend/tests/unit/ --cov=app/models --cov-report=term
Verify ≥ 85% model coverage (target 90%+ by end of sprint 3)
Verify all Sprint 2 acceptance criteria
Push; CI green
```

---

## Sprint 3 — API Foundation (Days 16–25)

### Day 16 — FastAPI App Setup

```
pip install fastapi uvicorn[standard] python-jose[cryptography] passlib[bcrypt] pydantic-settings
Create backend/app/main.py: application factory, all middleware
Create backend/app/core/security.py: JWT RS256 key load, create_access_token(), verify_token()
Create backend/app/core/redis.py: Redis connection pool
Generate RSA keypair: openssl genrsa 2048 > secrets/jwt_private_key.pem
Test: uvicorn runs; GET /api/v1/health returns 200
```

### Day 17 — Auth Router

```
Create backend/app/schemas/auth.py: RegisterRequest, LoginRequest, TokenResponse, UserResponse
Create backend/app/services/auth_service.py: register_user(), authenticate_user(), create_tokens()
Create backend/app/api/v1/auth.py: all 5 auth endpoints
Write integration tests: test_auth.py (register, login, token validation, refresh, logout)
Test: POST /auth/login returns JWT; verify with /auth/me
```

### Day 18 — Common Schemas and Middleware

```
Create backend/app/schemas/common.py: APIResponse, ErrorResponse, PaginationParams, PaginationMeta
Create backend/app/core/middleware.py: CorrelationIDMiddleware, RequestLoggingMiddleware
Implement structlog JSON logging
Implement rate limiting: Redis sliding window counter in dependency
Test: all requests include x-request-id header; logs are JSON; 1001st request → 429
```

### Day 19 — Users, Projects, Samples Routers

```
Create backend/app/schemas/{user,project,sample}.py
Create backend/app/services/{user,project,sample}_service.py
Create backend/app/api/v1/{users,projects,samples}.py
Implement RBAC dependencies: require_role(), require_project_member()
Write integration tests: CRUD operations; permission checks
```

### Day 20 — File Upload Router

```
Create backend/app/schemas/file.py
Create backend/app/services/file_service.py: upload to MinIO, checksum verify, chunked upload logic
Create backend/app/api/v1/files.py: upload, chunked init/chunk/complete, download (presigned URL), delete
Add minio service to docker-compose.yml; create buckets on startup
Write integration tests: upload 1 MB FASTA; download; verify checksum matches
```

### Day 21 — Module 1 Router Stubs

```
Create backend/app/api/v1/module1/ directory
Create stub routers for: validate, amr_detection, mutations, mechanisms, predict, virulence, workflow, reports
Each stub returns 501 Not Implemented with proper APIResponse format
Wire all routers in main.py
Test: Swagger UI shows all 56 endpoints; each returns 501
```

### Day 22 — WebSocket and Job Management

```
Create backend/app/api/v1/websocket.py: WebSocket endpoint /ws/jobs/{job_id}
Implement auth handshake (first frame = token)
Implement ping/pong keepalive (30s server-side ping)
Create backend/app/workers/celery_app.py: Celery app config (3 queues, routing, settings)
Create backend/app/workers/base_task.py: base task with progress update helper
Test: WebSocket connects; receives auth_ok; ping/pong works
```

### Day 23 — Integration Test Infrastructure

```
Set up pytest fixtures: async DB session, test client, test user, test project
Configure testcontainers for PostgreSQL and Redis in integration tests
Write integration tests covering all CRUD operations for users, projects, samples, files
Write auth flow test: full register → login → token → refresh → logout → verify revoked
```

### Day 24 — Error Handling and Validation

```
Implement global exception handler: SQLAlchemy errors → 500; Pydantic errors → 400
Implement all error codes from ACS Section 19.2 (19 error codes)
Implement custom Pydantic validators: FASTA file extension check; country code format; UUID format
Write unit tests for all custom validators and error handlers
```

### Day 25 — Sprint 3 Review

```
Verify Swagger UI available and all endpoints documented
Run full integration test suite; verify all pass
Verify RBAC: VIEWER cannot mutate; PROJECT_OWNER can manage members
Push; CI green; Swagger screenshot for documentation
```

---

## Sprint 4 — Genome Validation Engine (Days 26–35)

### Day 26 — Engine Package Setup and Integrity

```
Create engines/genome_validator/ package with all 19 module stubs
pip install biopython datasketch numpy scipy
Implement integrity.py: compute_integrity() with MD5, SHA256, gzip detection, record count
Write unit test: test_integrity.py (known file → known checksums)
```

### Day 27 — Input Validation

```
Implement input_validator.py: validate_fasta() with all 10 checks (file not empty, FASTA format, header uniqueness, IUPAC chars, no binary, encoding, no truncation, min contig length)
Create 6 test FASTA fixtures: valid, empty, binary, duplicate headers, invalid chars, truncated
Write test_input_validator.py: all 6 fixtures produce expected errors/pass
```

### Day 28 — Assembly Statistics and GC Analysis

```
Implement statistics.py: total_length, contig_count, mean/median/max/min contig, N50, N90, L50 (n_stat() function)
Implement gc_analysis.py: whole-genome GC, per-contig GC, 3-SD outlier detection
Write tests: known FASTA with pre-computed N50; GC outlier detection with spike contig
```

### Day 29 — Ambiguity, Contig, Duplicate Analysis

```
Implement ambiguity.py: N%, N-run detection, per-contig N table
Implement contig_analysis.py: fragmentation classification (genome-size adjusted), length distribution bins
Implement duplicate_detector.py: SHA256 exact + MinHash near-duplicate (datasketch)
Write tests: N-rich fixture → WARNING; duplicate contig pair detected
```

### Day 30 — Complexity, k-mer, Genome Size, Taxonomy

```
Implement complexity.py: Shannon entropy per contig, sliding window, homopolymer detection (regex)
Implement kmer_analysis.py: k=21/31/51 spectra, singleton%, coverage estimate
Implement genome_size.py: species-specific size ranges; PASS/WARNING/FAIL
Implement taxonomy.py: Mash sketch wrapper (subprocess to mash binary) OR stub with mock
Write tests for all 4 modules
```

### Day 31 — Contamination and Quality Scorer

```
Implement contamination.py: 7-signal weight matrix; LOW/MODERATE/HIGH_RISK aggregation
Implement quality_scorer.py: 7-component composite score formula; EXCELLENT/GOOD/ACCEPTABLE/POOR/FAILED classification
Write tests: E. coli K-12 → EXCELLENT; synthetic contaminated genome → MODERATE risk; N-rich → FAIL
```

### Day 32 — Decision Engine and Report Generator

```
Implement decision_engine.py: PASS/WARNING/FAIL rules; override logic; confidence_cap assignment
Implement report_generator.py: generate all 13 JSON/TSV files + PDF (WeasyPrint)
pip install weasyprint matplotlib
Write tests: decision engine produces correct PASS/WARNING/FAIL for each scenario; PDF renders
```

### Day 33 — DB Writer and Celery Task

```
Implement db_writer.py: write assembly_metrics, validation_reports tables
Create backend/app/workers/genome_validation_task.py: 16-step Celery task with progress updates
Wire POST /module1/validate router to dispatch Celery task
Wire GET /module1/validate/{job_id} to read job status from DB + Celery
Wire GET /module1/validate/{job_id}/results to DB query
```

### Day 34 — Container and Integration Test

```
Create containers/genome_validator/Dockerfile (python:3.12-slim + mash + weasyprint deps)
Build and test container: docker build -t amr-platform/genome-validator:1.0 .
Run integration test: POST /module1/validate with E. coli K-12 FASTA → COMPLETED → all 14 output files present
```

### Day 35 — Sprint 4 Review

```
Run all acceptance criteria checks
Measure runtime: 5 Mb E. coli < 120s
Verify PDF renders correctly
pytest engines/genome_validator/tests/ --cov=engines/genome_validator --cov-report=term ≥ 95%
Push; CI green
```

---

## Sprint 5 — Algorithm Library (Days 36–43)

### Day 36 — Smith-Waterman and Needleman-Wunsch

```
Create algorithms/ package structure
Implement alignment/smith_waterman.py: DP matrix, _traceback(), _sw_vectorised() NumPy version
Implement alignment/needleman_wunsch.py: global alignment with gap penalties
Write known-answer tests: SW (ACACACTA vs AGCACACA) → 4.0; NW (GCATGCU vs GATTACA) → 0.0
```

### Day 37 — Alignment Metrics, Substitution Matrices, BLAST Stats

```
Implement alignment/alignment_metrics.py: compute_metrics(), passes_thresholds()
Implement alignment/substitution_matrices.py: JSON matrix loader with @lru_cache
Create algorithms/alignment/data/matrices/ directory; create BLOSUM62.json and NUC4.4.json
Implement statistics/blast_statistics.py: bit_score(), e_value(), score_hit()
Write known-answer tests: bit score 100 → 185.17; E-value formula verification
```

### Day 38 — BWT, FM-Index, BWA-MEM

```
Implement search/bwt_engine.py: build_bwt(), inverse_bwt()
Implement search/fmindex_engine.py: FMIndex class with _build_occ(), _build_c(), count(), locate()
Implement search/bwa_mem_engine.py: BWAMemEngine with find_mems(), align()
Write tests: FMIndex.count() matches brute force on 20 test patterns
```

### Day 39 — k-mer, MinHash, Similarity

```
Implement similarity/kmer_engine.py: build_kmer_profile(), kmer_statistics(), compare_kmer_profiles()
Implement similarity/minhash_engine.py: build_minhash(), jaccard_similarity(), build_lsh_index()
Implement similarity/similarity_engine.py: jaccard(), cosine(), mash_distance(), edit_distance()
Write tests: MinHash(identical) = 1.0; MinHash(different) ∈ [0,1]; Jaccard({1,2},{2,3}) = 0.333
```

### Day 40 — Statistics Engine

```
Implement statistics/statistics_engine.py: describe(), z_scores(), confidence_interval(), normalise_score()
Write tests: describe([1,2,3,4,5]) → mean=3.0, median=3.0; z_scores known array
```

### Day 41 — amr_confidence Framework

```
Create amr_confidence/ package
Implement all 6 component scorers (identity, coverage, bitscore, evalue, agreement, evidence_strength)
Implement confidence_aggregation.py: aggregate() with 4-context weight profiles
Implement confidence_classifier.py and confidence_explanation.py
Implement modifiers/genome_quality_modifier.py
Write known-answer tests: identity=100, coverage=100, 4 tools, experimental → HIGH
```

### Day 42 — Performance Benchmarks and FastAPI Endpoint

```
pip install pytest-benchmark
Create algorithms/tests/benchmarks/: benchmark tests for SW, NW, MinHash, FMIndex
Run benchmarks; verify all within targets (SW < 5ms for 500bp, MinHash < 3s for 5Mb)
Create backend/app/api/v1/algorithms.py: POST /algorithms/alignment, /blast, /minhash, /kmer
Wire algorithm endpoints
```

### Day 43 — Sprint 5 Review

```
pytest algorithms/ amr_confidence/ --cov ≥ 95%
All benchmark targets met
All known-answer tests pass
Push; CI green
```

---

## Sprint 6 — AMR Detection Engine (Days 44–56)

### Day 44 — Package Setup and RawHit Model

```
Create engines/amr_detection/ package structure
Implement result_models.py: RawHit, AggregatedGene, AMRGeneResult dataclasses
Implement genome_parser.py: ContigRecord, parse_genome()
```

### Day 45 — Database Manager

```
Implement database_manager.py: DatabaseManager with _checksum_directory(), _register()
Implement downloader stubs for CARD, AMRFinder, ResFinder, Abricate
Write unit test: checksum calculation on known file
```

### Day 46 — CARD Adapter

```
Implement adapters/card_adapter.py: CARDAdapter.run() subprocess + _parse_output()
Create test fixtures: sample RGI output .txt files from real CARD tool run
Write test_card_adapter.py: parse fixture → correct RawHit fields
```

### Day 47 — AMRFinder, ResFinder, Abricate Adapters

```
Implement adapters/amrfinder_adapter.py: TSV parser with csv.DictReader
Implement adapters/resfinder_adapter.py: results_tab.txt parser
Implement adapters/abricate_adapter.py: multi-db runner + parser
Create fixture files for each tool; write unit tests for all parsers
```

### Day 48 — Hit Metrics and Classification

```
Implement hit_metrics.py: identity_pct(), coverage_pct(), classify_hit()
Implement ontology_mapper.py: OntologyMapper with ARO JSON loader + @lru_cache
Obtain card.json from CARD database; add to reference data
Write tests: blaCTX-M-15 ARO lookup → correct gene_family, drug_class, mechanism
```

### Day 49 — Evidence Aggregation and Deduplication

```
Implement evidence_aggregation.py: aggregate_hits(), AggregatedGene builder, agreement score
Implement deduplication_engine.py: find_overlapping_hits(), 5-scenario merge logic
Write tests: 4-tool agreement → agreement_score=1.0; overlapping hits merged correctly
```

### Day 50 — Drug Classification and Mechanism Pre-annotation

```
Implement drug_classification.py: DRUG_CLASS_MAP (20+ entries)
Implement mechanism_preannotation.py: MECHANISM_MAP + GENE_PREFIX_MECHANISM
Write tests: "penicillin" → "beta-lactam"; "blaKPC" prefix → "antibiotic_inactivation"
```

### Day 51 — Confidence Engine

```
Implement confidence_engine.py: 5-component weighted formula using amr_confidence package
Write tests: Perfect hit, 4 tools, CARD evidence level 1 → HIGH confidence ≥ 0.90
```

### Day 52 — Report Generator and DB Writer

```
Implement report_generator.py: all 7 output files (TSV, JSON, PDF)
Implement db_writer.py: amr_genes, amr_hits, amr_annotations, gene_evidence tables
Test: E. coli K-12 → zero AMR genes; fixture with known AMR → genes in DB
```

### Day 53 — Celery Task and Wired Endpoints

```
Create backend/app/workers/amr_detection_task.py: 13-step progress
Wire all /module1/amr-detection endpoints
```

### Day 54 — Container and Integration Tests

```
Build containers/amr_detection/Dockerfile (install CARD RGI + AMRFinder + Abricate)
Build container; test inside: rgi --version; amrfinder --version
Run integration test: E. coli UTI89 → blaTEM-1 detected
```

### Day 55 — Reference Genome Tests

```
Download 5 NCBI reference genomes to tests/fixtures/reference_genomes/
Run full AMR detection on all 5; verify against expected gene lists
Calculate recall and precision; must meet ≥ 0.95 / ≥ 0.90 thresholds
```

### Day 56 — Sprint 6 Review

```
All acceptance criteria met
pytest engines/amr_detection/ --cov ≥ 95%
Reference genome recall ≥ 0.95
Push; CI green
```

---

## Sprint 7 — Mutation Engine (Days 57–66)

### Day 57 — Knowledgebase and Package Setup

```
Create engines/mutation_engine/ package
Create mutation_knowledgebase.json: seed 50+ entries (gyrA S83L/D87N, parC S80I, rpoB S531L, mgrB entries, 23S A2058G, etc.)
Create mechanism_ontology.json (copy from Doc 7 spec)
Implement knowledgebase/loader.py: load, validate, LRU cache
```

### Day 58 — Gene Localization

```
Implement gene_localization.py: GeneLocation dataclass; BLAST pre-screen + NW refinement
Create reference CDS FASTA files for all target genes (gyrA, gyrB, parC, parE, rpoB, mgrB, etc.)
Write test: locate gyrA in E. coli K-12 → correct contig, coordinates
```

### Day 59 — Variant Detection

```
Implement variant_detection.py: call_variants(), detect_stop_codons(), _annotate_frameshifts()
Create synthetic FASTA fixture: E. coli gyrA with c.248C>T (S83L)
Write test: fixture → RawVariant with cds_position=248, ref_nucleotide=C, alt_nucleotide=T
```

### Day 60 — Variant Annotation

```
Implement variant_annotation.py: annotate_variant(), HGVS p. and c. notation, domain_annotation
Implement resistance domain table (QRDR, RRDR, etc.) per Section 8.2 of Doc 7
Write test: gyrA c.248C>T → p.Ser83Leu; domain=QRDR; effect=missense
```

### Day 61 — Mutation Mapper and Confidence

```
Implement mutation_mapper.py: map_mutation(), 3-tier lookup (exact/position/gene)
Implement mutation_confidence.py: 4-component formula, kb_evidence_score()
Write tests: gyrA S83L → KNOWN_RESISTANCE; novel QRDR position → NOVEL_IN_DOMAIN
```

### Day 62 — Novel Detection and Prioritizer

```
Implement novel_mutation_detector.py: classification pipeline, novel_mutation_report.json
Implement mutation_prioritizer.py: 4-component priority score; prioritized_mutations.tsv
Write tests: KNOWN mutation gets higher priority than NOVEL; CRITICAL drug gets highest weight
```

### Day 63 — Mechanism Classifier and Evidence

```
Implement mechanism_classifier.py: 3-tier classification (ARO → KB → heuristic)
Implement mechanism_evidence.py: aggregate_mechanisms(), MechanismObject builder
Write tests from Section 12.3 of Doc 7: all 8 examples produce correct mechanism
```

### Day 64 — Drug Association and Reports

```
Implement drug_association.py: DrugAssociation dataclass, CROSS_RESISTANCE dict
Implement report_generator.py: 8 output files + PDF
Implement db_writer.py: mutations, mutation_annotations, mutation_mechanisms, drug_associations
```

### Day 65 — Celery Tasks and Endpoints

```
Create celery_tasks.py: mutation_detection_task + mechanism_classification_task (11-step progress each)
Wire /module1/mutations and /module1/mechanisms endpoints
Build containers/mutation_engine/Dockerfile
Test: submit mutation detection job → COMPLETED → resistance_mutations.tsv present
```

### Day 66 — Sprint 7 Review

```
All 6 known-answer tests pass (gyrA S83L, D87N, parC S80I, rpoB S531L, mgrB insertion, novel QRDR)
pytest engines/mutation_engine/ --cov ≥ 95%
Push; CI green
```

---

## Sprint 8 — Phenotype Prediction Engine (Days 67–76)

### Day 67 — Rule Repository

```
Create engines/phenotype_engine/ package
Create rule_repository.json: seed ≥ 100 rules (all drug classes; gene/mutation/mechanism/combinatorial)
Implement rule_repository.py: RuleRepository loader with validation and hot-reload
Write tests: all 100 rules validate against schema; hot-reload test
```

### Day 68 — Gene and Mutation Rule Engines

```
Implement rules/gene_rule_engine.py: GeneRuleEngine.evaluate(), all condition types
Implement rules/mutation_rule_engine.py: MutationRuleEngine.evaluate() with LIKELY modifier
Write tests for every rule type; known-input → expected SIR
```

### Day 69 — Mechanism and Combinatorial Rule Engines

```
Implement rules/mechanism_rule_engine.py: MechanismRuleEngine.evaluate()
Implement rules/combinatorial_rules.py: all_of, any_of evaluation
Write tests: gyrA S83L alone → I; gyrA S83L + parC S80I → R (combinatorial)
```

### Day 70 — Inheritance and Conflict Resolution

```
Implement inference/inheritance_engine.py: 4-level priority resolution
Implement inference/conflict_resolution.py: SIR_PRIORITY dict, resolve_conflicts()
Write tests: R always wins; evidence level 1 beats level 4; combinatorial beats single-determinant
```

### Day 71 — Confidence Propagation and EUCAST

```
Implement inference/confidence_propagation.py: propagate_confidence(), GENOME_CAP dict
Implement breakpoints/eucast_adapter.py: BreakpointRecord, EUCASTAdapter
Add EUCAST v13.0 breakpoint data files (TSV format)
Implement breakpoints/clsi_adapter.py
Write tests: MEDIUM quality cap ≤ 0.75; EUCAST breakpoint lookup correct for 10 drug/species combos
```

### Day 72 — Phenotype Inference Engine

```
Implement inference/phenotype_inference.py: PhenotypeInferenceEngine.predict() orchestrator
Implement mathematical/ecoff_engine.py: compute_ecoff(), classify_vs_ecoff()
Implement mathematical/hill_equation_engine.py: hill_response(), fit_hill_curve()
Write full integration test: PredictionInput with blaCTX-M-15 → ceftriaxone = R, HIGH confidence
```

### Day 73 — Explanation and Module 2 Export

```
Implement explanation_engine.py: generate_explanation() with full evidence chain
Implement module2_export.py: export_module2_csv(), schema validation
Test: export_module2_csv() produces valid CSV; schema_version=1.0.0; all 23 columns present
```

### Day 74 — Reports, DB Writer, Celery Task

```
Implement report_generator.py: 7 output files + PDF
Implement db_writer.py: phenotype_predictions, prediction_evidence, prediction_explanations, module2_exports
Create celery_tasks.py: phenotype_prediction_task (12-step progress)
Wire /module1/predict endpoints
```

### Day 75 — Reference Phenotype Validation

```
Run prediction engine on 5 reference isolates (KPC KP, MRSA, FQ-resistant E. coli, VRE, colistin-resistant KP)
Verify sensitivity ≥ 0.90 and specificity ≥ 0.90 against known phenotype profiles
```

### Day 76 — Sprint 8 Review

```
All acceptance criteria met
pytest engines/phenotype_engine/ --cov ≥ 95%
module2_input.csv schema validation passes
Push; CI green
```

---

## Sprint 9 — Virulence Engine (Days 77–86)

### Day 77 — Package Setup and Ontology

```
Create engines/virulence_engine/ package
Create ontology/virulence_ontology.json (12 categories with risk_weights)
Create ontology/gene_category_map.json (seed 500+ gene mappings)
Implement ontology/ontology_loader.py
```

### Day 78 — VFDB Adapter

```
Implement adapters/vfdb_adapter.py: VFDBAdapter, BLASTn subprocess, BLAST-6 parser, VFDB header regex
Create VFDB BLAST database from VFDB_setA_nt.fas (download from VFDB)
Test: BLASTn against VFDB database produces valid RawHit list
```

### Day 79 — VirulenceFinder Adapter

```
Implement adapters/virulencefinder_adapter.py: subprocess + JSON result parser
Download VirulenceFinder database
Test: VirulenceFinder on E. coli O157 fixture → fimH, stx1, stx2 detected
```

### Day 80 — Virulence Classifier

```
Implement virulence_classifier.py: VirulenceClassifier, _lookup_category(), prefix heuristic
Write tests: fimH→adhesin; stx1→toxin(is_high_risk=True); rpoS→stress_response; unknown→unknown
```

### Day 81 — Pathogenicity Profile and Risk Scoring

```
Implement pathogenicity_profile.py: compute_risk_score(), PathogenicityProfile builder
Write tests: E. coli O157 (stx1, stx2, hlyA) → CRITICAL; K-12 → LOW
```

### Day 82 — Global Confidence Scoring All

```
Implement confidence_scoring_all: reads all Module 1 output files for a sample
Applies amr_confidence.aggregate() to every AMRGeneResult, Mutation, PhenotypePrediction, VirulenceFactor
Writes confidence_scores and confidence_components tables
Write integration test: after running all engines, all entities have confidence_score populated
```

### Day 83 — Reports and DB Writer

```
Implement report_generator.py: 9 output files + PDF
Implement db_writer.py: virulence_factors, virulence_annotations, virulence_profiles
Create celery_tasks.py: virulence_profiling_task + confidence_scoring_task
Wire /module1/virulence and /module1/confidence endpoints
```

### Day 84 — Containers

```
Build containers/virulence_profiler/Dockerfile (python:3.12-slim + blast+ + VirulenceFinder)
Build containers/confidence_scorer/Dockerfile (python:3.12-slim + amr_confidence)
Test both containers build and run correctly
```

### Day 85 — Reference Genome Validation

```
Run virulence engine on 5 reference genomes
E. coli O157:H7 → stx1, stx2, hlyA detected; CRITICAL or HIGH risk class
E. coli K-12 → 0 virulence genes; LOW risk
Verify recall ≥ 0.90 on published VFDB hit lists
```

### Day 86 — Sprint 9 Review

```
All acceptance criteria met
pytest engines/virulence_engine/ --cov ≥ 95%
Push; CI green
```

---

## Sprint 10 — Workflow Integration (Days 87–96)

### Day 87 — Nextflow Modules (Part 1)

```
Write nextflow/modules/genome_validation.nf: GENOME_VALIDATION + VALIDATION_GATE processes
Write nextflow/modules/amr_detection.nf: AMR_DETECT_CARD, AMR_DETECT_AMRFINDER, AMR_DETECT_RESFINDER, AMR_DETECT_ABRICATE, AMR_AGGREGATE processes
Test GENOME_VALIDATION process: `nextflow run -entry GENOME_VALIDATION -profile docker`
```

### Day 88 — Nextflow Modules (Part 2)

```
Write nextflow/modules/mutation_detection.nf: MUTATION_DETECTION process
Write nextflow/modules/mechanism_classification.nf: MECHANISM_CLASSIFICATION process
Write nextflow/modules/phenotype_prediction.nf: PHENOTYPE_PREDICTION process
Write nextflow/modules/virulence_profiling.nf: VIRULENCE_DETECTION + CONFIDENCE_SCORING_ALL processes
Write nextflow/modules/module2_export.nf: MODULE2_EXPORT + GENERATE_REPORTS processes
```

### Day 89 — Nextflow Subworkflows

```
Write nextflow/subworkflows/validation.nf: VALIDATION_SUBWORKFLOW
Write nextflow/subworkflows/amr_detection.nf: AMR_DETECTION_SUBWORKFLOW
Write nextflow/subworkflows/mutation_mechanism.nf: MUTATION_MECHANISM_SUBWORKFLOW
Write nextflow/subworkflows/phenotype.nf: PHENOTYPE_SUBWORKFLOW
Write nextflow/subworkflows/virulence_confidence.nf: VIRULENCE_CONFIDENCE_SUBWORKFLOW
Write nextflow/subworkflows/reporting.nf: REPORTING_SUBWORKFLOW
```

### Day 90 — main.nf and nextflow.config

```
Write nextflow/main.nf: MODULE1_AMR_PIPELINE workflow (4 stages, all channels, all emits)
Write nextflow/nextflow.config: params, process resource labels, Docker executor, retry strategy
Test: `nextflow run main.nf -profile docker` with test FASTA → runs without error
```

### Day 91 — Celery Pipeline Chain

```
Create backend/app/workers/pipeline_task.py: MODULE1_PIPELINE Celery chord
  - validate → (amr + mutations parallel chord) → mechanisms → (phenotype + virulence parallel chord) → confidence → module2 → reports
Implement pipeline submission service: creates AnalysisJob, dispatches chord, stores Nextflow session ID
Wire POST /workflow/run endpoint
Wire POST /workflow/cancel and POST /workflow/retry
```

### Day 92 — WebSocket Progress Streaming

```
Implement Celery task progress → Redis pub/sub channel (ws:channel:{job_id})
Implement WebSocket handler: subscribe to Redis channel; forward events to connected clients
Implement reconnect handling: buffer last 5 minutes of events per job
Test: submit job → WebSocket client receives all progress events 0% → 100%
```

### Day 93 — Docker Compose Complete Stack

```
Add all services to deploy/docker-compose.yml (11 services total)
Add all volumes, secrets, health checks, depends_on per Section 11
Create deploy/nginx/nginx.conf: reverse proxy, TLS stub, gzip, upstream
Add MinIO lifecycle policy script to startup
Test: `docker compose up --build` → all 11 containers healthy within 60s
```

### Day 94 — First Full End-to-End Run

```
Submit E. coli K-12 via POST /module1/predict
Track via WebSocket; observe all 12 progress steps
Verify all output files written to MinIO
Verify all DB tables populated (amr_genes, mutations, phenotype_predictions, virulence_factors, confidence_scores)
Download PDF report; verify renders correctly
```

### Day 95 — nf-test Workflow Tests

```
Install nf-test: pip install nf-test OR via nextflow plugin
Write tests/test_genome_validation.nf.test: input reference FASTA → assert validation_status.json exists and contains status
Write tests for AMR detection, mutation, phenotype, virulence processes
Run: `nf-test test` → all tests pass
```

### Day 96 — Sprint 10 Review

```
All containers healthy; full pipeline runs end-to-end
WebSocket delivers all progress events
Nextflow -resume skips completed processes on re-run
nf-test: all 14 process tests pass
Flower dashboard shows completed tasks
Push; CI green
```

---

## Sprint 11 — End-to-End Testing (Days 97–104)

### Day 97 — Reference Genome Full Pipeline Runs

```
Run full pipeline (all engines) on all 5 reference genomes
Verify all 13 output files present and valid for each genome
Record actual vs expected gene/mutation/phenotype profiles
Calculate recall, precision, sensitivity, specificity
```

### Day 98 — Regression Baseline and Contract Tests

```
Run schemathesis against all 56 API endpoints on local running server
Fix any schema violations; ensure 100% pass
Create regression baseline: snapshot output JSONs for 5 reference genomes
Commit snapshots as fixtures for future regression detection
```

### Day 99 — Load Testing

```
Write k6 load test script: 100 VUs; mix of GET (status poll, results) and POST (job submit)
Run 30-minute sustained load test: 500 samples/hour equivalent
Record p50, p95, p99 latencies; error rate; throughput
Fix any bottlenecks: add indexes if needed; tune connection pool; adjust Celery concurrency
```

### Day 100 — Security Testing

```
Deploy to staging environment
Run OWASP ZAP DAST baseline scan: `zap-baseline.py -t https://staging.amrplatform.io`
Run ZAP full scan on authenticated session
Document any findings; remediate High and Critical
Re-scan to verify fixes
```

### Day 101 — End-to-End Playwright Tests

```
Install Playwright: pip install playwright; playwright install
Write e2e/test_full_journey.py:
  - Register new user
  - Create project
  - Upload FASTA file
  - Submit workflow
  - Poll until COMPLETED
  - Download PDF report
  - Verify report downloaded successfully
Run against local docker-compose stack
```

### Day 102 — Coverage and Quality Gates

```
Run full pytest suite with coverage: pytest --cov=backend --cov=engines --cov=algorithms --cov=amr_confidence
Verify overall coverage ≥ 90%
Identify under-covered modules; write additional tests
Run mypy type checking; fix any errors
Run ruff with all rules; fix any violations
```

### Day 103 — module2_input.csv Validation

```
Verify module2_input.csv output for all 5 reference genomes:
  - schema_version = 1.0.0
  - All 23 columns present
  - No empty required fields
  - Row counts match expected (one row per gene × antibiotic)
  - Confidence tiers present for all rows
Write automated CSV schema validation test
```

### Day 104 — Sprint 11 Review

```
All 13 output files present for all 5 reference genomes
AMR recall ≥ 0.95; precision ≥ 0.90; zero false positives on negative control
Overall coverage ≥ 90%
ZAP: zero Critical/High findings
Load test: zero 5xx; p99 < 5s
Push; CI green; all gates pass
```

---

## Sprint 12 — Production Deployment (Days 105–109)

### Day 105 — Server Provisioning and Secrets

```
Provision production server (≥ 32 CPU, 128 GB RAM, 2 TB SSD)
Install Docker and Docker Compose on production server
Generate production secrets: openssl genrsa 4096 > jwt_private_key.pem; strong passwords
Create production .env file (server-side only; not committed)
Verify: docker ps runs; docker compose version
```

### Day 106 — Reference Data and Database Setup

```
Download all reference databases: CARD, AMRFinderPlus, ResFinder, VFDB, VirulenceFinder
Verify checksums; register in database_versions table
Import EUCAST v13.0 breakpoint data
Import CLSI M100 breakpoint data
Import mutation_knowledgebase.json (final production version)
Import rule_repository.json (final production version ≥ 100 rules)
Run: alembic upgrade head; python db_seed.py
Verify: \dt shows all 49 tables; SELECT count(*) FROM mechanism_classes → 10
```

### Day 107 — Production Deployment and SSL

```
Deploy docker-compose.prod.yml with all 11 services
Configure certbot or acme.sh for Let's Encrypt SSL
Verify HTTPS: curl -I https://api.amrplatform.io returns 200
Test SSL: SSL Labs grade A
Submit 3 real test genomes; verify end-to-end on production
Verify PDFs downloadable via presigned URLs
```

### Day 108 — Monitoring, Alerting, Backup

```
Import 5 Grafana dashboards from monitoring/grafana/dashboards/
Verify all Prometheus metrics scraping (prometheus targets page: all UP)
Configure 8 Grafana alert rules per Section 15 of WIDS
Configure SMTP for alert email notifications
Test alert: manually trigger disk usage alert; verify email received
Set up backup cron jobs:
  - Daily: pg_dump at 03:00 UTC
  - Weekly: pg_basebackup at 02:00 UTC Sunday
  - Continuous: WAL archiving to MinIO
Test backup restore: pg_restore to staging; verify data matches
```

### Day 109 — Runbooks and Go-Live

```
Write ops/runbooks/backup_restore.md
Write ops/runbooks/reference_db_update.md
Write ops/runbooks/incident_response.md
Write ops/runbooks/new_user_onboarding.md
Final check: all containers healthy; monitoring live; alerts configured; backups tested
Create first production admin user via API
Document go-live in CHANGELOG.md
Push final tag: git tag v1.0.0-production
```

---

## Summary: Task Count by Sprint

| Sprint | Days | ~Tasks |
|--------|------|--------|
| 1 — Foundation | 5 | 25 |
| 2 — Database | 10 | 50 |
| 3 — API | 10 | 50 |
| 4 — Genome Validation | 10 | 50 |
| 5 — Algorithms | 8 | 40 |
| 6 — AMR Detection | 13 | 65 |
| 7 — Mutation Engine | 10 | 50 |
| 8 — Phenotype Engine | 10 | 50 |
| 9 — Virulence Engine | 10 | 50 |
| 10 — Workflow | 10 | 50 |
| 11 — E2E Testing | 8 | 40 |
| 12 — Production | 5 | 25 |
| **Total** | **109** | **~545** |

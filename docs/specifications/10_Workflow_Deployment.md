# 10 — Workflow Orchestration, Infrastructure, Deployment and DevOps

> **MVP Implementation Note:** The full infrastructure described here is the production target.
> For the 2-week MVP, use the simplified stack below.

### MVP Stack vs Full Stack

| Component | MVP (Now) | Full (Phase 5) |
|-----------|-----------|----------------|
| Task execution | FastAPI `BackgroundTasks` | 🔵 Celery + Redis |
| Pipeline orchestration | Python subprocess calls | 🔵 Nextflow DSL2 |
| File storage | Local disk `data/` | 🔵 MinIO object storage |
| Database | SQLite | 🔵 PostgreSQL |
| Deployment | Single `docker-compose.yml` (3 services) | 🔵 Full 11-service stack |
| Monitoring | None | ⬜ Prometheus + Grafana |
| Alerting | None | ⬜ Grafana alerts |
| CI/CD | Basic GitHub Actions lint | ⬜ Full pipeline |
| Kubernetes | Not needed | ⬜ Future enterprise |

| Section | Feature | Phase |
|---------|---------|-------|
| 4 — FastAPI Architecture | Application layers | 🟢 MVP (simplified) |
| 5 — Celery Architecture | Async task queue | 🔵 Phase 5 |
| 6 — Redis Architecture | Cache and queue broker | 🔵 Phase 5 |
| 7 — Nextflow DSL2 | Pipeline orchestration | 🔵 Phase 5 |
| 9 — Docker Compose | Container stack | 🟢 MVP (3 services) |
| 10 — Dockerfiles | Container builds | 🟢 MVP |
| 11 — Full Docker Compose | 11-service production stack | 🔵 Phase 5 |
| 14 — Monitoring | Prometheus + Grafana | ⬜ Future enterprise |
| 15 — Alerting | Grafana alerts | ⬜ Future enterprise |
| 17 — CI/CD | GitHub Actions pipeline | ⬜ Future enterprise |
| 20 — Kubernetes | K8s manifests + HPA | ⬜ Future enterprise |

> **🟢 MVP Deployment:** `docker-compose.yml` with 3 services: `api`, `postgres` (or skip — use SQLite), `nginx`. One command: `docker compose up`.

---

**WORKFLOW ORCHESTRATION**

**INFRASTRUCTURE, DEPLOYMENT AND DEVOPS**

**SPECIFICATION \| WIDS v1.0**

**MODULE 1G --- AMR CHARACTERISATION ENGINE**

*FastAPI · Celery · Redis · Nextflow DSL2 · Docker · Kubernetes · GitHub Actions*

Integrates Documents 1--9 · Production-Grade · Cloud-Ready

Version 1.0 --- CONFIDENTIAL --- Direct Implementation Ready

> **SECTION 1 --- PLATFORM OBJECTIVES AND INTEGRATION SCOPE**

**1.1 Integration of Documents 1--9**

  -------------- ---------------- -----------------------------------------------------------------------------
  **Document**   **Module**       **Component Integrated**

  Doc 1          SAS/TDD          Overall architecture vision; layer definitions; non-functional requirements

  Doc 2          DDS              PostgreSQL schema; 49 tables; Alembic migrations; indexing strategy

  Doc 3          ACS              56 REST endpoints; WebSocket; Pydantic schemas; JWT auth architecture

  Doc 4          Module 1A GVE    Genome Validation Engine; 14 output files; 16-step Celery task

  Doc 5          Module 1B CAES   Algorithm library (SW, NW, BWT, FM-Index, MinHash, k-mer, stats)

  Doc 6          Module 1C ADE    AMR Detection Engine; CARD/AMRFinder/ResFinder/Abricate adapters

  Doc 7          Module 1D RMME   Mutation Detection + Mechanism Classification Engine; knowledgebase

  Doc 8          Module 1E PPRE   Phenotype Prediction Rule Engine; EUCAST/CLSI; Module 2 export

  Doc 9          Module 1F VPCE   Virulence Profiling + Global Confidence Scoring Framework
  -------------- ---------------- -----------------------------------------------------------------------------

**1.2 Non-Functional Requirements**

  ------------------------ ---------------------------------------------- --------------------------------------------------------------
  **Requirement**          **Target**                                     **Measurement**

  Single genome pipeline   \< 60 minutes end-to-end                       Time from job submission to PDF report available

  Batch throughput         100 genomes / 24 hours (single server)         Celery worker concurrency × process time

  API response time        \< 200 ms p95 for GET endpoints                Prometheus histogram percentile

  Availability             99.5% uptime (production)                      Uptime monitoring; \<4.4 hours/month downtime

  Data durability          Zero data loss on single node failure          PostgreSQL WAL + MinIO replication

  Reproducibility          100% identical results from identical inputs   Pinned DB versions + container image tags + Nextflow -resume

  Audit trail              Every action logged with user/timestamp        audit_logs table; immutable log stream

  Security                 OWASP Top 10 mitigated; no Critical CVEs       Trivy container scan + ZAP DAST in CI
  ------------------------ ---------------------------------------------- --------------------------------------------------------------

> **SECTION 2 --- OVERALL SYSTEM ARCHITECTURE**

**2.1 Architecture Diagram**

> ┌─────────────────────────────────────────────────────────────────────┐
>
> │ USER INTERFACE LAYER │
>
> │ Web UI (React) │ CLI Client │ LIS Integration │ Module 2/3 │
>
> └───────────────────────────┬─────────────────────────────────────────┘
>
> │ HTTPS / WSS
>
> ┌───────────────────────────▼─────────────────────────────────────────┐
>
> │ NGINX REVERSE PROXY / TLS │
>
> │ Rate limiting │ Static assets │ SSL termination │
>
> └───────────────────────────┬─────────────────────────────────────────┘
>
> │
>
> ┌───────────────────────────▼─────────────────────────────────────────┐
>
> │ FASTAPI GATEWAY (api/) │
>
> │ Auth Middleware → RBAC → Validation → Routers → Service Layer │
>
> │ /auth /users /projects /samples /files /module1/\* /reports │
>
> └────────┬──────────────────────────────────────┬──────────────────────┘
>
> │ SQLAlchemy async │ Celery task dispatch
>
> ┌────────▼──────────┐ ┌────────────▼──────────────────────┐
>
> │ POSTGRESQL 15 │ │ CELERY 5 + REDIS 7 │
>
> │ Primary DB │ │ Queues: high / default / low │
>
> │ 49 tables │ │ Workers: 4--20 auto-scale │
>
> │ WAL replication │ │ Flower monitoring dashboard │
>
> └────────┬──────────┘ └─────────────┬──────────────────────┘
>
> │ │ subprocess / NF API
>
> │ ┌──────────────▼──────────────────────┐
>
> │ │ NEXTFLOW DSL2 RUNNER │
>
> │ │ main.nf │ nextflow.config │
>
> │ │ Docker executor (local/k8s/slurm) │
>
> │ └──────────────┬──────────────────────┘
>
> │ │
>
> │ ┌──────────────────────────┼─────────────────────┐
>
> │ ▼ ▼ ▼
>
> │ ┌────────────────────┐ ┌───────────────────┐ ┌──────────────────┐
>
> │ │ GENOME VALIDATOR │ │ AMR DETECTION │ │ MUTATION ENGINE │
>
> │ │ (Module 1A) │ │ (Module 1C) │ │ (Module 1D) │
>
> │ └────────────────────┘ └───────────────────┘ └──────────────────┘
>
> │ │ │ │
>
> │ ┌──────────▼──────────┐ ┌───────────▼────────┐ │
>
> │ │ PHENOTYPE PREDICTOR │ │ VIRULENCE PROFILER │ │
>
> │ │ (Module 1E) │ │ (Module 1F) │ │
>
> │ └─────────────────────┘ └────────────────────┘ │
>
> │ │
>
> │ ┌────────▼────────────────────────────────┐
>
> │ │ REPORTING LAYER │
>
> │ │ JSON │ TSV │ PDF │ module2_input.csv │
>
> │ └────────┬────────────────────────────────┘
>
> │ │ file results
>
> │ ┌───────────▼─────────────────┐
>
> └──────────────► MINIO OBJECT STORAGE │
>
> │ uploads/ results/ archive/ │
>
> **SECTION 3 --- PROJECT REPOSITORY STRUCTURE**

**3.1 Top-Level Structure**

> AMR_Platform/
>
> ├── docs/ \# Architecture docs, ADRs, API docs
>
> │ ├── architecture/ \# SAS, DDS, ACS documents
>
> │ ├── adr/ \# Architecture Decision Records
>
> │ └── runbooks/ \# Operational runbooks
>
> ├── backend/ \# Python FastAPI application
>
> │ ├── app/
>
> │ │ ├── api/ \# FastAPI router definitions (v1/)
>
> │ │ ├── core/ \# Config, security, database, redis
>
> │ │ ├── models/ \# SQLAlchemy ORM models (49 tables)
>
> │ │ ├── schemas/ \# Pydantic v2 request/response schemas
>
> │ │ ├── services/ \# Business logic layer
>
> │ │ ├── workers/ \# Celery tasks
>
> │ │ └── reports/ \# PDF/JSON/TSV report generators
>
> │ ├── alembic/ \# Database migration files
>
> │ ├── tests/ \# pytest test suite
>
> │ └── requirements.txt
>
> ├── algorithms/ \# amr_confidence/ + algorithm packages (Doc 5)
>
> │ ├── amr_confidence/ \# Global confidence scoring framework
>
> │ ├── alignment/ \# Smith-Waterman, Needleman-Wunsch
>
> │ ├── search/ \# BWT, FM-Index, BWA-MEM
>
> │ └── similarity/ \# MinHash, k-mer, Jaccard
>
> ├── engines/ \# Bioinformatics analysis engines
>
> │ ├── genome_validator/ \# Module 1A (Doc 4)
>
> │ ├── amr_detection/ \# Module 1C (Doc 6)
>
> │ ├── mutation_engine/ \# Module 1D (Doc 7)
>
> │ ├── phenotype_engine/ \# Module 1E (Doc 8)
>
> │ └── virulence_engine/ \# Module 1F (Doc 9)
>
> ├── nextflow/ \# Nextflow DSL2 pipeline
>
> │ ├── main.nf \# Main workflow entry point
>
> │ ├── nextflow.config \# Executor, resource, container config
>
> │ ├── modules/ \# Individual process definitions
>
> │ │ ├── genome_validation.nf
>
> │ │ ├── amr_detection.nf
>
> │ │ ├── mutation_detection.nf
>
> │ │ ├── mechanism_classification.nf
>
> │ │ ├── phenotype_prediction.nf
>
> │ │ ├── virulence_profiling.nf
>
> │ │ ├── confidence_scoring.nf
>
> │ │ └── module2_export.nf
>
> │ ├── subworkflows/ \# Composite subworkflow definitions
>
> │ └── tests/ \# nf-test workflow tests
>
> ├── containers/ \# Dockerfiles per service
>
> │ ├── api/Dockerfile
>
> │ ├── celery/Dockerfile
>
> │ ├── genome_validator/Dockerfile
>
> │ ├── amr_detection/Dockerfile
>
> │ ├── mutation_engine/Dockerfile
>
> │ └── confidence_scorer/Dockerfile
>
> ├── deploy/ \# Deployment configurations
>
> │ ├── docker-compose.yml
>
> │ ├── docker-compose.dev.yml
>
> │ ├── docker-compose.prod.yml
>
> │ └── kubernetes/ \# K8s manifests (Section 20)
>
> ├── monitoring/ \# Prometheus + Grafana configs
>
> │ ├── prometheus.yml
>
> │ └── grafana/dashboards/
>
> ├── scripts/ \# Utility scripts
>
> │ ├── db_seed.py \# Seed mechanism classes, breakpoints
>
> │ ├── db_update.sh \# Reference DB download + update
>
> │ └── backup.sh
>
> └── .github/
>
> └── workflows/ \# GitHub Actions CI/CD pipelines
>
> **SECTION 4 --- FASTAPI ARCHITECTURE**

**4.1 Application Layers**

  ------------------- ------------------------------------------ ------------------------------------------------------------------------------------------------
  **Layer**           **Location**                               **Responsibility**

  Router Layer        backend/app/api/v1/                        HTTP endpoint definitions; route matching; request deserialization; delegates to Service Layer

  Validation Layer    backend/app/schemas/                       Pydantic v2 strict models; field validators; custom business rule validators; file type checks

  Auth Layer          backend/app/core/security.py               JWT RS256 verification; API token lookup; RBAC permission checks via FastAPI Depends()

  Service Layer       backend/app/services/                      Business logic; orchestrates DB queries and Celery dispatches; project isolation enforcement

  Workflow Layer      backend/app/services/workflow_service.py   Job submission to Celery; job status tracking; Nextflow session ID management

  Persistence Layer   backend/app/models/ + database/            SQLAlchemy 2.x async ORM; session lifecycle; query execution; transaction management

  Reporting Layer     backend/app/reports/                       JSON/TSV/PDF generation; presigned URL generation; report metadata storage
  ------------------- ------------------------------------------ ------------------------------------------------------------------------------------------------

**4.2 Application Factory**

> \# backend/app/main.py
>
> from fastapi import FastAPI
>
> from fastapi.middleware.cors import CORSMiddleware
>
> from fastapi.middleware.gzip import GZipMiddleware
>
> from app.core.config import settings
>
> from app.api.v1 import auth, users, projects, samples, files
>
> from app.api.v1 import module1_validate, module1_amr, module1_mutations
>
> from app.api.v1 import module1_mechanisms, module1_predict, module1_virulence
>
> from app.api.v1 import workflow, reports, admin
>
> from app.core.middleware import RequestLoggingMiddleware, CorrelationIDMiddleware
>
> def create_app() -\> FastAPI:
>
> app = FastAPI(
>
> title=\"AMR Platform API\",
>
> version=\"1.0.0\",
>
> docs_url=\"/api/v1/docs\",
>
> redoc_url=\"/api/v1/redoc\"
>
> )
>
> app.add_middleware(GZipMiddleware, minimum_size=1000)
>
> app.add_middleware(CorrelationIDMiddleware)
>
> app.add_middleware(RequestLoggingMiddleware)
>
> for router in \[auth, users, projects, samples, files,
>
> module1_validate, module1_amr, module1_mutations,
>
> module1_mechanisms, module1_predict, module1_virulence,
>
> workflow, reports, admin\]:
>
> app.include_router(router.router, prefix=\"/api/v1\")
>
> return app
>
> **SECTION 5 --- CELERY ARCHITECTURE**

**5.1 Task Hierarchy and Dependencies**

> MODULE1_PIPELINE (parent task chain)
>
> ├── validate_genome_task (Module 1A) → PASS/FAIL gate
>
> ├── amr_detection_task (Module 1C) → parallel with mutations
>
> ├── mutation_detection_task (Module 1D) → parallel with AMR detection
>
> ├── mechanism_classification_task(Module 1D) → waits for AMR + mutations
>
> ├── phenotype_prediction_task (Module 1E) → waits for mechanisms
>
> ├── virulence_profiling_task (Module 1F) → parallel with phenotype
>
> ├── confidence_scoring_task (Module 1F) → waits for all above
>
> ├── module2_export_task (Module 1E) → waits for confidence
>
> └── report_generation_task (Reports) → waits for all

**5.2 Celery Application Configuration**

> \# backend/app/core/celery_app.py
>
> from celery import Celery
>
> from kombu import Queue
>
> celery = Celery(\"amr_platform\")
>
> celery.conf.update(
>
> broker_url = settings.REDIS_URL,
>
> result_backend = settings.REDIS_URL,
>
> task_serializer = \"json\",
>
> result_serializer = \"json\",
>
> accept_content = \[\"json\"\],
>
> task_track_started = True,
>
> task_acks_late = True, \# ack only after task completes
>
> worker_prefetch_multiplier = 1, \# one task per worker at a time
>
> task_reject_on_worker_lost = True,
>
> result_expires = 86400, \# 24 hours
>
> task_queues = (
>
> Queue(\"high_priority\", routing_key=\"high\"),
>
> Queue(\"default\", routing_key=\"default\"),
>
> Queue(\"low_priority\", routing_key=\"low\"),
>
> ),
>
> task_routes = {
>
> \"module1.validate_genome\": {\"queue\": \"high_priority\"},
>
> \"module1.amr_detection\": {\"queue\": \"default\"},
>
> \"module1.mutation_detection\": {\"queue\": \"default\"},
>
> \"module1.phenotype_predict\": {\"queue\": \"default\"},
>
> \"module1.virulence_profiling\": {\"queue\": \"default\"},
>
> \"module1.confidence_scoring\": {\"queue\": \"low_priority\"},
>
> \"module1.report_generation\": {\"queue\": \"low_priority\"},
>
> },
>
> )

**5.3 Retry Policies**

  -------------------------- ----------------- ----------------- ---------------------------------------------------
  **Task**                   **Max Retries**   **Back-off**      **Non-Retriable Conditions**

  validate_genome            2                 60s, 300s         FASTA parse error; file too small

  amr_detection              3                 30s, 120s, 480s   Tool binary missing (container error)

  mutation_detection         3                 30s, 120s, 480s   Gene not in species catalogue (WARNING, no retry)

  mechanism_classification   2                 60s, 300s         ARO ontology load failure after retry

  phenotype_prediction       2                 60s, 300s         No rules loaded; rule_repository.json missing

  virulence_profiling        3                 30s, 120s, 480s   VFDB BLAST index missing

  confidence_scoring         2                 30s, 120s         Missing input data from prior tasks

  report_generation          2                 30s, 120s         Storage write failure after 2 retries → FAILED
  -------------------------- ----------------- ----------------- ---------------------------------------------------

> **SECTION 6 --- REDIS ARCHITECTURE**

**6.1 Redis Data Structures and Namespacing**

  ------------------------------ --------------------------- ------------------ ------------------------------------------------
  **Namespace**                  **Data Structure**          **TTL**            **Purpose**

  celery:\*                      Celery-managed keys         24h                Task results and metadata (managed by Celery)

  job:progress:{job_id}          Hash {step, pct, message}   2h                 Real-time job progress for WebSocket streaming

  session:blocklist:{jti}        String (1)                  Access token TTL   Revoked JWT JTI blocklist

  ratelimit:{user_id}:{window}   String (counter)            1h sliding         Rate limiting counter per user per time window

  cache:breakpoints:{source}     String (JSON)               24h                EUCAST/CLSI breakpoint table cache

  cache:aro:{accession}          String (JSON)               1h                 ARO ontology lookup cache

  ws:channel:{job_id}            Pub/Sub channel             N/A                WebSocket event broadcast channel per job

  db_version:active:{db_name}    String (UUID)               5m                 Active reference database version cache
  ------------------------------ --------------------------- ------------------ ------------------------------------------------

**6.2 Redis Configuration**

> \# redis.conf (production settings)
>
> maxmemory 2gb
>
> maxmemory-policy allkeys-lru \# evict LRU keys when at max memory
>
> appendonly yes \# AOF persistence for durability
>
> appendfsync everysec \# fsync every second (balance durability/perf)
>
> save 900 1 \# RDB snapshot: 1 change in 15 min
>
> save 300 10 \# 10 changes in 5 min
>
> hz 20 \# 20 background tasks/sec for key expiry
>
> **SECTION 7 --- NEXTFLOW DSL2 ARCHITECTURE**

**7.1 main.nf --- Master Workflow**

> #!/usr/bin/env nextflow
>
> nextflow.enable.dsl = 2
>
> include { VALIDATION_SUBWORKFLOW } from \"./subworkflows/validation\"
>
> include { AMR_DETECTION_SUBWORKFLOW } from \"./subworkflows/amr_detection\"
>
> include { MUTATION_MECHANISM_SUBWORKFLOW } from \"./subworkflows/mutation_mechanism\"
>
> include { PHENOTYPE_SUBWORKFLOW } from \"./subworkflows/phenotype\"
>
> include { VIRULENCE_CONFIDENCE_SUBWORKFLOW} from \"./subworkflows/virulence_confidence\"
>
> include { REPORTING_SUBWORKFLOW } from \"./subworkflows/reporting\"
>
> workflow MODULE1_AMR_PIPELINE {
>
> take:
>
> ch_input // Channel: tuple(meta, fasta_path)
>
> // meta: {sample_id, job_id, species, breakpoint_source, project_id, config_json}
>
> main:
>
> // Stage 1: Genome Validation (GATE)
>
> VALIDATION_SUBWORKFLOW(ch_input)
>
> ch_validated = VALIDATION_SUBWORKFLOW.out.validated // Only PASS/WARNING pass through
>
> // Stage 2: Parallel --- AMR Detection + Mutation Detection
>
> AMR_DETECTION_SUBWORKFLOW(ch_validated)
>
> MUTATION_MECHANISM_SUBWORKFLOW(ch_validated)
>
> // Stage 3: Parallel --- Phenotype Prediction + Virulence (after AMR + Mutation)
>
> ch_amr_done = AMR_DETECTION_SUBWORKFLOW.out.amr_genes_json
>
> ch_det_done = MUTATION_MECHANISM_SUBWORKFLOW.out.determinants
>
> PHENOTYPE_SUBWORKFLOW(ch_amr_done.join(ch_det_done))
>
> VIRULENCE_CONFIDENCE_SUBWORKFLOW(
>
> ch_validated,
>
> ch_amr_done,
>
> ch_det_done,
>
> PHENOTYPE_SUBWORKFLOW.out.predictions_json
>
> )
>
> // Stage 4: Reporting (after all analysis complete)
>
> REPORTING_SUBWORKFLOW(
>
> VALIDATION_SUBWORKFLOW.out.assembly_metrics,
>
> ch_amr_done,
>
> ch_det_done,
>
> PHENOTYPE_SUBWORKFLOW.out.predictions_json,
>
> VIRULENCE_CONFIDENCE_SUBWORKFLOW.out.vf_summary,
>
> VIRULENCE_CONFIDENCE_SUBWORKFLOW.out.confidence_scores
>
> )
>
> emit:
>
> validation_report = VALIDATION_SUBWORKFLOW.out.validation_report
>
> amr_genes_json = ch_amr_done
>
> mutations_tsv = MUTATION_MECHANISM_SUBWORKFLOW.out.mutations_tsv
>
> mechanism_summary = MUTATION_MECHANISM_SUBWORKFLOW.out.mech_summary
>
> predictions_json = PHENOTYPE_SUBWORKFLOW.out.predictions_json
>
> module2_export = PHENOTYPE_SUBWORKFLOW.out.module2_csv
>
> virulence_summary = VIRULENCE_CONFIDENCE_SUBWORKFLOW.out.vf_summary
>
> confidence_scores = VIRULENCE_CONFIDENCE_SUBWORKFLOW.out.confidence_scores
>
> pdf_reports = REPORTING_SUBWORKFLOW.out.all_pdfs

**7.2 nextflow.config**

> // nextflow/nextflow.config
>
> params {
>
> input = null
>
> outdir = \"\${launchDir}/results\"
>
> card_db = \"/data/databases/card/latest\"
>
> amrfinder_db = \"/data/databases/amrfinderplus/latest\"
>
> resfinder_db = \"/data/databases/resfinder/latest\"
>
> vfdb_blast_db = \"/data/databases/vfdb/latest/VFDB_setA_nt\"
>
> virulencefinder_db=\"/data/databases/virulencefinder/latest\"
>
> kb_json = \"/data/knowledgebases/mutation_knowledgebase.json\"
>
> rule_repository = \"/data/knowledgebases/rule_repository.json\"
>
> breakpoint_source= \"EUCAST\"
>
> }
>
> process {
>
> errorStrategy = { task.attempt \<= 3 ? \"retry\" : \"finish\" }
>
> maxRetries = 3
>
> withLabel: \"process_high\" { cpus = 8; memory = \"16 GB\"; time = \"2.h\" }
>
> withLabel: \"process_medium\"{ cpus = 4; memory = \"8 GB\"; time = \"1.h\" }
>
> withLabel: \"process_low\" { cpus = 2; memory = \"4 GB\"; time = \"30.m\" }
>
> }
>
> docker {
>
> enabled = true
>
> runOptions = \"-u \$(id -u):\$(id -g)\"
>
> }
>
> executor {
>
> \$local { cpus = 32; memory = \"128 GB\" }
>
> }
>
> **SECTION 8 --- NEXTFLOW PROCESS SPECIFICATIONS**

  -------------------------- ---------- --------- ---------- --------------------------------------- ---------------------------------------------------------------- ---------------------------------------------------------------------------
  **Process**                **CPUs**   **Mem**   **Time**   **Container**                           **Key Inputs**                                                   **Key Outputs**

  GENOME_VALIDATION          2          4 GB      30m        amr-platform/genome-validator:1.0       fasta, metadata_json                                             validation_report.json, assembly_metrics.json, validated_fasta (if PASS)

  VALIDATION_GATE            1          1 GB      2m         python:3.12-slim                        validation_status.json                                           Passes or terminates channel; emits meta with quality_cap

  AMR_DETECT_CARD            8          16 GB     60m        finlaymaguire/card-rgi:6.0              fasta, card_db                                                   card_rgi_results.txt, card_rgi_results.json

  AMR_DETECT_AMRFINDER       4          8 GB      30m        ncbi/amrfinderplus:3.11                 fasta, amrfinder_db                                              amrfinder_results.tsv

  AMR_DETECT_RESFINDER       4          8 GB      30m        amr-platform/resfinder:4.1              fasta, resfinder_db                                              resfinder_results.tsv

  AMR_DETECT_ABRICATE        4          8 GB      20m        staphb/abricate:1.0                     fasta                                                            abricate_results.tsv

  AMR_AGGREGATE              2          4 GB      10m        amr-platform/amr-aggregator:1.0         card_json, amrfinder_tsv, resfinder_tsv, abricate_tsv            amr_genes.json, amr_genes.tsv

  MUTATION_DETECTION         4          8 GB      45m        amr-platform/mutation-detector:1.0      fasta, kb_json, ref_seqs                                         resistance_mutations.tsv, novel_mutation_report.json

  MECHANISM_CLASSIFICATION   2          4 GB      15m        amr-platform/mechanism-classifier:1.0   amr_genes_json, mutations_tsv, ontology_json, aro_json           mechanism_summary.json, determinants.json

  PHENOTYPE_PREDICTION       2          4 GB      20m        amr-platform/phenotype-predictor:1.0    amr_genes_json, determinants_json, rule_repository, eucast_tsv   phenotype_prediction.json, module2_input.csv

  VIRULENCE_DETECTION        4          8 GB      30m        amr-platform/virulence-profiler:1.0     fasta, vfdb_blast_db, virulencefinder_db                         virulence_factors.tsv, virulence_summary.json, pathogenicity_profile.json

  CONFIDENCE_SCORING_ALL     1          2 GB      10m        amr-platform/confidence-scorer:1.0      All prior output JSONs, assembly_metrics.json                    confidence_scores.json, confidence_components.tsv

  MODULE2_EXPORT             1          2 GB      5m         amr-platform/module2-exporter:1.0       phenotype_prediction.json, confidence_scores.json, sample_meta   module2_input.csv (final, verified)

  GENERATE_REPORTS           2          4 GB      15m        amr-platform/report-generator:1.0       All output files                                                 amr_report.pdf, mutation_report.pdf, virulence_report.pdf
  -------------------------- ---------- --------- ---------- --------------------------------------- ---------------------------------------------------------------- ---------------------------------------------------------------------------

> **SECTION 9 --- CONTAINERISATION STRATEGY**

  ----------------- --------------------------- -------------------------------------------------------------- ---------- --------------------------
  **Container**     **Base Image**              **Key Contents**                                               **Port**   **Health Check**

  api               python:3.12-slim            FastAPI app, uvicorn, SQLAlchemy, Pydantic, python-jose        8000       GET /api/v1/health → 200

  postgres          postgres:15-alpine          PostgreSQL 15; pgaudit extension                               5432       pg_isready -U amr_user

  redis             redis:7-alpine              Redis 7; AOF + RDB persistence enabled                         6379       redis-cli ping

  celery_worker     amr-platform/api:1.0        Same as API image; celery worker entrypoint                    N/A        celery inspect ping

  celery_beat       amr-platform/api:1.0        Celery beat scheduler for periodic tasks                       N/A        Process alive check

  nextflow_runner   amr-platform/nextflow:1.0   Nextflow + Java 17 + Docker-in-Docker OR Docker socket mount   N/A        nextflow -version

  nginx             nginx:1.25-alpine           Reverse proxy; TLS termination; gzip; rate limiting            80, 443    nginx -t

  prometheus        prom/prometheus:v2.51       Metrics scraper; 15-day retention                              9090       HTTP /health

  grafana           grafana/grafana:10.4        Dashboards; alerting; SMTP notifications                       3000       HTTP /api/health

  flower            mher/flower:2.0             Celery task monitoring UI                                      5555       HTTP /healthcheck

  minio             minio/minio:latest          S3-compatible object storage; genomes, results, reports        9000       mc ready local
  ----------------- --------------------------- -------------------------------------------------------------- ---------- --------------------------

> **SECTION 10 --- DOCKERFILE DESIGNS**

**10.1 FastAPI / Celery Dockerfile**

> \# containers/api/Dockerfile
>
> FROM python:3.12-slim AS builder
>
> WORKDIR /build
>
> COPY requirements.txt .
>
> RUN pip install \--no-cache-dir \--user -r requirements.txt
>
> FROM python:3.12-slim
>
> RUN apt-get update && apt-get install -y \--no-install-recommends \\
>
> libgomp1 curl && rm -rf /var/lib/apt/lists/\*
>
> WORKDIR /app
>
> COPY \--from=builder /root/.local /root/.local
>
> COPY . .
>
> ENV PATH=/root/.local/bin:\$PATH
>
> USER 1000:1000
>
> EXPOSE 8000
>
> CMD \[\"uvicorn\", \"app.main:app\", \"\--host\", \"0.0.0.0\", \"\--port\", \"8000\", \"\--workers\", \"4\"\]

**10.2 AMR Detection Container (CARD + AMRFinder + ResFinder + Abricate)**

> \# containers/amr_detection/Dockerfile
>
> FROM ubuntu:22.04
>
> ENV DEBIAN_FRONTEND=noninteractive
>
> RUN apt-get update && apt-get install -y \--no-install-recommends \\
>
> python3 python3-pip openjdk-17-jre-headless blast+ prodigal \\
>
> && rm -rf /var/lib/apt/lists/\*
>
> \# Install CARD RGI
>
> RUN pip3 install \--no-cache-dir rgi==6.0.3
>
> \# Install AMRFinderPlus
>
> RUN curl -Lo amrfinder.tar.gz \\
>
> https://github.com/ncbi/amr/releases/download/v3.11.26/amrfinder_binaries_v3.11.26.tar.gz \\
>
> && tar -xzf amrfinder.tar.gz -C /usr/local/bin/ && rm amrfinder.tar.gz
>
> \# Install Abricate
>
> RUN apt-get install -y bioperl && cpanm Bio::SearchIO
>
> \# Install platform engines
>
> COPY engines/amr_detection/ /app/amr_detection/
>
> RUN pip3 install \--no-cache-dir -e /app/amr_detection/
>
> USER 1000:1000
>
> ENTRYPOINT \[\"python3\", \"-m\", \"amr_detection.cli\"\]

**10.3 Nextflow Runner Container**

> \# containers/nextflow/Dockerfile
>
> FROM eclipse-temurin:17-jre-jammy
>
> RUN apt-get update && apt-get install -y \--no-install-recommends \\
>
> curl wget git docker.io && rm -rf /var/lib/apt/lists/\*
>
> \# Install Nextflow
>
> RUN curl -s https://get.nextflow.io \| bash && mv nextflow /usr/local/bin/
>
> \# Docker socket access (for Docker executor)
>
> RUN groupadd -g 999 docker_group && usermod -aG docker_group nextflow_user \|\| true
>
> USER 1000:1000
>
> ENTRYPOINT \[\"nextflow\"\]
>
> **SECTION 11 --- DOCKER COMPOSE DESIGN**

**11.1 docker-compose.yml (core services)**

> version: \"3.9\"
>
> x-common-env: &common-env
>
> DATABASE_URL: \"postgresql+asyncpg://amr_user:\${DB_PASSWORD}@postgres:5432/amr_platform\"
>
> REDIS_URL: \"redis://:\${REDIS_PASSWORD}@redis:6379/0\"
>
> S3_ENDPOINT: \"http://minio:9000\"
>
> S3_ACCESS_KEY: \"\${MINIO_ACCESS_KEY}\"
>
> S3_SECRET_KEY: \"\${MINIO_SECRET_KEY}\"
>
> JWT_PRIVATE_KEY_PATH: \"/run/secrets/jwt_private_key\"
>
> NEXTFLOW_WORK_DIR: \"/data/nextflow/work\"
>
> services:
>
> postgres:
>
> image: postgres:15-alpine
>
> restart: unless-stopped
>
> environment:
>
> POSTGRES_DB: amr_platform
>
> POSTGRES_USER: amr_user
>
> POSTGRES_PASSWORD_FILE: /run/secrets/db_password
>
> secrets: \[db_password\]
>
> volumes:
>
> \- postgres_data:/var/lib/postgresql/data
>
> \- ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
>
> healthcheck:
>
> test: \[\"CMD-SHELL\", \"pg_isready -U amr_user -d amr_platform\"\]
>
> interval: 10s; timeout: 5s; retries: 5; start_period: 30s
>
> redis:
>
> image: redis:7-alpine
>
> restart: unless-stopped
>
> command: redis-server \--requirepass \"\${REDIS_PASSWORD}\" \--appendonly yes
>
> volumes: \[redis_data:/data\]
>
> healthcheck: { test: \[\"CMD\", \"redis-cli\", \"ping\"\], interval: 10s }
>
> minio:
>
> image: minio/minio:latest
>
> restart: unless-stopped
>
> command: server /data \--console-address \":9001\"
>
> environment:
>
> MINIO_ROOT_USER: \"\${MINIO_ACCESS_KEY}\"
>
> MINIO_ROOT_PASSWORD: \"\${MINIO_SECRET_KEY}\"
>
> volumes: \[minio_data:/data\]
>
> healthcheck: { test: \[\"CMD\", \"mc\", \"ready\", \"local\"\], interval: 30s }
>
> api:
>
> build: { context: ., dockerfile: containers/api/Dockerfile }
>
> image: amr-platform/api:\${VERSION:-latest}
>
> restart: unless-stopped
>
> environment: { \<\<: \*common-env }
>
> secrets: \[db_password, jwt_private_key\]
>
> depends_on: { postgres: { condition: service_healthy }, redis: { condition: service_healthy } }
>
> ports: \[\"8000:8000\"\]
>
> volumes:
>
> \- nextflow_work:/data/nextflow/work
>
> \- reference_dbs:/data/databases:ro
>
> healthcheck: { test: \[\"CMD\", \"curl\", \"-f\", \"http://localhost:8000/api/v1/health\"\], interval: 30s }
>
> celery_worker:
>
> image: amr-platform/api:\${VERSION:-latest}
>
> restart: unless-stopped
>
> command: celery -A app.core.celery_app worker -Q high_priority,default,low_priority -c 4 -l info
>
> environment: { \<\<: \*common-env }
>
> secrets: \[db_password, jwt_private_key\]
>
> depends_on: \[postgres, redis, minio\]
>
> volumes:
>
> \- nextflow_work:/data/nextflow/work
>
> \- reference_dbs:/data/databases:ro
>
> \- /var/run/docker.sock:/var/run/docker.sock
>
> celery_beat:
>
> image: amr-platform/api:\${VERSION:-latest}
>
> restart: unless-stopped
>
> command: celery -A app.core.celery_app beat -l info
>
> environment: { \<\<: \*common-env }
>
> depends_on: \[redis\]
>
> nginx:
>
> image: nginx:1.25-alpine
>
> restart: unless-stopped
>
> ports: \[\"80:80\", \"443:443\"\]
>
> volumes:
>
> \- ./deploy/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
>
> \- ./deploy/nginx/ssl:/etc/nginx/ssl:ro
>
> depends_on: \[api\]
>
> flower:
>
> image: mher/flower:2.0
>
> command: celery \--broker=redis://:\${REDIS_PASSWORD}@redis:6379/0 flower \--port=5555
>
> ports: \[\"5555:5555\"\]
>
> depends_on: \[redis\]
>
> prometheus:
>
> image: prom/prometheus:v2.51.0
>
> volumes: \[./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro\]
>
> ports: \[\"9090:9090\"\]
>
> grafana:
>
> image: grafana/grafana:10.4.0
>
> volumes:
>
> \- grafana_data:/var/lib/grafana
>
> \- ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
>
> ports: \[\"3000:3000\"\]
>
> environment:
>
> GF_SECURITY_ADMIN_PASSWORD: \"\${GRAFANA_PASSWORD}\"
>
> secrets:
>
> db_password: { file: ./secrets/db_password.txt }
>
> jwt_private_key: { file: ./secrets/jwt_private_key.pem }
>
> volumes:
>
> postgres_data:
>
> redis_data:
>
> minio_data:
>
> grafana_data:
>
> nextflow_work:
>
> reference_dbs: { driver_opts: { type: none, device: /data/databases, o: bind } }
>
> **SECTION 12 --- FILE STORAGE ARCHITECTURE**

  ------------ -------------------------- -------------------------- ------------------------------------------------------- ----------------------------------- ----------------------------
  **Tier**     **Storage**                **Path Prefix**            **Contents**                                            **Retention**                       **Access**

  Hot          MinIO local                uploads/                   Uploaded genome FASTAs pending analysis                 30 days                             Direct presigned URL

  Hot          MinIO local                results/{sample_id}/       JSON/TSV/PDF outputs; module2_input.csv                 12 months                           Presigned URL (1h TTL)

  Hot (temp)   NFS volume                 nextflow/work/{session}/   Nextflow intermediate files during pipeline run         7 days; auto-purged                 Container direct mount

  Warm         MinIO lifecycle tier       archive/results/{year}/    Results older than 12 months                            7 years                             Restore-on-request via API

  Cold         MinIO Glacier-equivalent   archive/raw/{year}/        Original FASTA files after analysis                     7 years (clinical traceability)     Manual restore only

  DB           PostgreSQL                 N/A                        All structured analysis results, metadata, audit logs   Per domain retention policy (DDS)   SQLAlchemy ORM
  ------------ -------------------------- -------------------------- ------------------------------------------------------- ----------------------------------- ----------------------------

**12.1 MinIO Lifecycle Policies**

> \# MinIO lifecycle rule (applied via mc CLI at startup)
>
> mc ilm add local/uploads \--expiry-days 30
>
> mc ilm add local/results \--transition-days 365 \--storage-class GLACIER
>
> mc ilm add local/nextflow-work \--expiry-days 7
>
> **SECTION 13 --- LOGGING ARCHITECTURE**

**13.1 Structured Log Format**

> \# Every log line is JSON with these base fields:
>
> {
>
> \"timestamp\": \"2025-06-01T10:05:23.412Z\", // ISO 8601 UTC
>
> \"level\": \"INFO\",
>
> \"event\": \"api_request\",
>
> \"service\": \"api\", // api \| celery \| nextflow \| db
>
> \"request_id\": \"uuid\", // injected per HTTP request
>
> \"trace_id\": \"uuid\", // propagated to all downstream calls
>
> \"user_id\": \"uuid \| null\",
>
> \"project_id\": \"uuid \| null\",
>
> // \... event-specific fields

**13.2 Log Aggregation Stack**

  ---------------- ------------------------------------- ------------------------------------------------------ --------------------------------------
  **Component**    **Tool**                              **Config**                                             **Retention**

  Log collection   Promtail (Loki) or Filebeat (ELK)     Mount /var/log/amr_platform/; parse JSON lines         30 days hot; 12 months archive

  Log storage      Loki (lightweight) or Elasticsearch   Index per service; time-based rolling index            30 days searchable; archive to MinIO

  Log query        Grafana (Loki) or Kibana (ELK)        Dashboard with request_id and trace_id search          N/A (query tier)

  Audit logs       PostgreSQL audit_logs table           Immutable; row-level before/after; forwarded to SIEM   10 years minimum
  ---------------- ------------------------------------- ------------------------------------------------------ --------------------------------------

> **SECTION 14 --- MONITORING AND ALERTING ARCHITECTURE**

**14.1 Prometheus Metrics Collected**

  -------------- ----------------------------------- ----------- -------------------------------------------------
  **Category**   **Metric Name**                     **Type**    **Description**

  API            amr_http_requests_total             Counter     HTTP requests by method, path, status_code

  API            amr_http_request_duration_seconds   Histogram   Request latency with p50/p95/p99 buckets

  Celery         amr_celery_task_total               Counter     Tasks by name and state (success/failure/retry)

  Celery         amr_celery_task_duration_seconds    Histogram   Task execution time by task name

  Celery         amr_celery_queue_length             Gauge       Current queue depth per queue name

  DB             amr_pg_connection_pool_size         Gauge       Active PostgreSQL connections

  DB             amr_pg_query_duration_seconds       Histogram   Query latency from pg_stat_statements

  Workflow       amr_nextflow_processes_total        Counter     Nextflow processes by name and status

  Workflow       amr_workflow_duration_seconds       Histogram   End-to-end workflow time per sample

  Storage        amr_minio_bucket_size_bytes         Gauge       Storage usage per bucket

  System         node_cpu_seconds_total              Counter     CPU utilisation from node_exporter

  System         node_memory_MemAvailable_bytes      Gauge       Available memory from node_exporter
  -------------- ----------------------------------- ----------- -------------------------------------------------

**14.2 Grafana Dashboard Specification**

  ----------------------- ------------------------------------------------------------------------------ -----------------------------------------
  **Dashboard**           **Panels**                                                                     **Key Alerting Metrics**

  Platform Overview       Active jobs gauge, API RPS, p95 latency, queue depth, error rate               Error rate \> 5%; p95 \> 2s

  Workflow Performance    Jobs per hour, per-stage duration heatmap, FAILED job count, completion rate   FAILED jobs \> 5 per hour

  Infrastructure Health   CPU/memory per container, disk usage, DB connections, Redis memory             Disk \> 80%; memory \> 90%

  AMR Biology Summary     Samples analysed per day, gene detection rate, phenotype distribution charts   Informational; no auto-alerts

  Security Events         Failed login attempts, RBAC violations, token revocations, rate limit hits     Failed logins \> 20 per min from one IP
  ----------------------- ------------------------------------------------------------------------------ -----------------------------------------

**14.3 Alert Severity and Response**

  ------------------------- -------------- ------------------------------------- -----------------------------------------------------
  **Alert**                 **Severity**   **Trigger**                           **Response**

  Workflow FAILED rate      WARNING        \> 5 failed jobs in 1 hour            Notify on-call; check Celery worker logs

  API error rate            CRITICAL       5xx rate \> 5% over 5 min             Page on-call; check API container and DB

  Disk usage                WARNING        \> 75% on any volume                  Notify admin; review cleanup policy

  Disk usage                CRITICAL       \> 90%                                Page on-call; trigger emergency archive purge

  DB connection exhausted   CRITICAL       PgBouncer pool \> 95%                 Page on-call; scale workers; check slow queries

  Container crash loop      CRITICAL       Container restarts \> 3 in 10 min     Page on-call; preserve logs; redeploy if needed

  Security: brute force     HIGH           \> 20 auth failures/min from one IP   Auto-block IP via nginx; security team notification

  Redis memory              WARNING        \> 80% maxmemory                      Notify admin; review TTL policies; scale Redis
  ------------------------- -------------- ------------------------------------- -----------------------------------------------------

> **SECTION 15 --- SECURITY ARCHITECTURE**

  --------------------- -------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------
  **Domain**            **Control**                                                                                  **Implementation**

  Authentication        JWT RS256; 15 min access token; 7 day refresh; MFA optional for ADMIN                        python-jose; token rotation on refresh; JTI blocklist in Redis

  Authorisation         RBAC: SUPERADMIN / ADMIN / PROJECT_OWNER / ANALYST / VIEWER; project-scoped data isolation   FastAPI Depends(); all DB queries include project_id filter; PostgreSQL RLS policies

  API Security          Rate limiting; input sanitisation; no SQL injection; no path traversal                       Redis sliding window counter; Pydantic strict validation; parameterised SQLAlchemy queries only

  Secrets Management    No secrets in code, environment files, or images                                             Docker secrets for DB password and JWT key; Vault for production; .env only for development

  Container Security    Non-root UID 1000; read-only root FS; no privileged mode; minimal base images                Dockerfile USER 1000; securityContext in Kubernetes; Trivy scan in CI (block on HIGH+)

  Database Security     TLS connections; per-service DB roles; pgaudit; no direct internet access                    sslmode=require; amr_api_user / amr_celery_user with minimal grants; firewall rules

  Encryption at rest    MinIO SSE-S3 for all stored files; PostgreSQL data volume encryption                         MinIO auto-encryption enabled; dm-crypt on volume in production

  Audit trail           Every mutating API call logged to audit_logs; immutable; tamper-evident                      audit_logs table (Section 18 DDS); row hashing; forwarded to SIEM

  Dependency scanning   Python packages and container layers scanned for CVEs in CI                                  pip-audit + Trivy in GitHub Actions; block deploy on Critical CVEs

  OWASP mitigations     A01-A10 addressed: injection, broken auth, IDOR, XSS, SSRF, etc.                             ZAP DAST in staging pipeline; annual penetration test recommendation
  --------------------- -------------------------------------------------------------------------------------------- -------------------------------------------------------------------------------------------------

> **SECTION 16 --- CI/CD ARCHITECTURE**

**16.1 GitHub Actions Pipeline**

> \# .github/workflows/ci.yml
>
> name: AMR Platform CI/CD
>
> on:
>
> push: { branches: \[main, develop\] }
>
> pull_request: { branches: \[main\] }
>
> jobs:
>
> lint:
>
> runs-on: ubuntu-latest
>
> steps:
>
> \- uses: actions/checkout@v4
>
> \- uses: actions/setup-python@v5
>
> with: { python-version: \"3.12\" }
>
> \- run: pip install ruff mypy && ruff check . && mypy backend/
>
> unit_tests:
>
> runs-on: ubuntu-latest
>
> services:
>
> postgres: { image: postgres:15-alpine, env: { POSTGRES_PASSWORD: test } }
>
> redis: { image: redis:7-alpine }
>
> steps:
>
> \- uses: actions/checkout@v4
>
> \- run: pip install -r requirements.txt
>
> \- run: pytest backend/tests/unit/ -v \--cov=app \--cov-report=xml
>
> \- uses: codecov/codecov-action@v4
>
> integration_tests:
>
> needs: unit_tests
>
> runs-on: ubuntu-latest
>
> steps:
>
> \- uses: actions/checkout@v4
>
> \- run: docker compose -f deploy/docker-compose.test.yml up -d
>
> \- run: sleep 20 && pytest backend/tests/integration/ -v
>
> \- run: docker compose -f deploy/docker-compose.test.yml down
>
> security_scan:
>
> needs: unit_tests
>
> runs-on: ubuntu-latest
>
> steps:
>
> \- uses: actions/checkout@v4
>
> \- uses: aquasecurity/trivy-action@master
>
> with: { scan-type: \"fs\", exit-code: \"1\", severity: \"CRITICAL,HIGH\" }
>
> \- run: pip install pip-audit && pip-audit -r requirements.txt
>
> build_push:
>
> needs: \[integration_tests, security_scan\]
>
> if: github.ref == \"refs/heads/main\"
>
> runs-on: ubuntu-latest
>
> steps:
>
> \- uses: actions/checkout@v4
>
> \- uses: docker/setup-buildx-action@v3
>
> \- uses: docker/login-action@v3
>
> with: { registry: ghcr.io, username: \${{ github.actor }}, password: \${{ secrets.GITHUB_TOKEN }} }
>
> \- uses: docker/build-push-action@v5
>
> with: { push: true, tags: ghcr.io/amr-platform/api:\${{ github.sha }} }
>
> deploy_staging:
>
> needs: build_push
>
> environment: staging
>
> runs-on: ubuntu-latest
>
> steps:
>
> \- run: \|
>
> ssh deploy@staging.amrplatform.io \\
>
> \"cd /opt/amr_platform && VERSION=\${{ github.sha }} docker compose pull && docker compose up -d\"
>
> deploy_production:
>
> needs: deploy_staging
>
> environment: production
>
> runs-on: ubuntu-latest
>
> steps:
>
> \- run: \# Same as staging but on production host; manual approval required via GitHub Environment
>
> **SECTION 17 --- TESTING ARCHITECTURE**

  -------------------- -------------------------------- -------------------------------- ------------------------------------------------------------------------------- ------------------------------------
  **Test Type**        **Framework**                    **Location**                     **Scope**                                                                       **Coverage Target**

  Unit Tests           pytest                           backend/tests/unit/              Individual functions; service methods; algorithm modules                        ≥ 90% line coverage overall

  Integration Tests    pytest + testcontainers          backend/tests/integration/       API endpoint → DB round-trips; Celery task execution; file upload flow          100% critical path endpoints

  Workflow Tests       nf-test                          nextflow/tests/                  Nextflow process and subworkflow execution with real tool containers            All 14 processes tested

  API Contract Tests   schemathesis (OpenAPI fuzzing)   backend/tests/contract/          Auto-generate test cases from OpenAPI spec; verify response schema compliance   100% endpoint schema compliance

  Load Tests           k6                               backend/tests/load/              100 concurrent users; 500 samples/hour; sustained 1 hour                        Zero 5xx; p99 \< 5s for submission

  Security Tests       OWASP ZAP (DAST)                 .github/workflows/security.yml   DAST scan against staging deployment; OWASP Top 10 scenarios                    Zero High/Critical findings

  Regression Tests     pytest fixtures with snapshots   backend/tests/regression/        10 reference genomes; identical outputs across versions                         Zero unintended prediction changes

  End-to-End Tests     Playwright (browser) + pytest    backend/tests/e2e/               Full user journey: register → upload → run → download PDF report                Happy path + 3 failure scenarios
  -------------------- -------------------------------- -------------------------------- ------------------------------------------------------------------------------- ------------------------------------

**17.1 Reference Test Datasets**

  --------------------- ------------------------------------------------------------------------------------------- ---------------------------------------------- --------------------------------------------------
  **Dataset**           **Genomes**                                                                                 **Purpose**                                    **Location**

  AMR benchmark         5 NCBI reference genomes (E. coli, K. pneumoniae, S. aureus, P. aeruginosa, A. baumannii)   Known AMR profiles; regression test baseline   tests/fixtures/reference_genomes/

  Negative control      E. coli K-12 MG1655 (AMR-negative)                                                          Verify no false positives on wild-type         tests/fixtures/amr_negative/

  Synthetic mutations   6 E. coli genomes with engineered mutations (gyrA S83L, rpoB S531L, etc.)                   Mutation detection regression                  tests/fixtures/synthetic_mutations/

  Large batch           50-genome E. coli collection                                                                Batch throughput and performance testing       tests/fixtures/batch_test/ (generated by script)
  --------------------- ------------------------------------------------------------------------------------------- ---------------------------------------------- --------------------------------------------------

> **SECTION 18 --- SCALABILITY DESIGN**

  -------------------------- ----------------- --------------------- ----------------- ----------------- ------------------- ----------------------
  **Scale Tier**             **Genomes/Day**   **Celery Workers**    **CPU (total)**   **RAM (total)**   **Storage/Month**   **DB Connections**

  Small (single server)      10--100           4--8                  16--32 CPU        64--128 GB        \~50 GB             20--50

  Medium (HA + workers)      100--1000         8--20                 64--128 CPU       256--512 GB       \~500 GB            50--150

  Large (cloud horizontal)   1000--10000       20--100 (autoscale)   128--512 CPU      512 GB -- 2 TB    5--50 TB            150--500 (PgBouncer)
  -------------------------- ----------------- --------------------- ----------------- ----------------- ------------------- ----------------------

**18.1 Horizontal Scaling Strategy**

-   Celery workers scale horizontally: add worker containers; no code changes required. Queue depth triggers autoscaling (k8s HPA on custom metric amr_celery_queue_length).

-   FastAPI scales horizontally: stateless; add API replicas behind nginx upstream; session state in Redis.

-   PostgreSQL: read replicas for reporting and GET queries; primary for writes. PgBouncer pool for connection management at scale.

-   Nextflow: scales to available CPUs on local executor; migrates to Kubernetes executor at large scale (Section 20).

-   MinIO: starts as single-node; migrates to distributed mode (4+ nodes) for production.

> **SECTION 19 --- KUBERNETES READINESS**

**19.1 Key K8s Manifest Outlines**

> \# deploy/kubernetes/api-deployment.yaml (outline)
>
> apiVersion: apps/v1
>
> kind: Deployment
>
> metadata: { name: amr-api, namespace: amr-platform }
>
> spec:
>
> replicas: 3
>
> selector: { matchLabels: { app: amr-api } }
>
> template:
>
> spec:
>
> containers:
>
> \- name: api
>
> image: ghcr.io/amr-platform/api:TAG
>
> ports: \[{containerPort: 8000}\]
>
> envFrom: \[{configMapRef: {name: amr-config}}\]
>
> env:
>
> \- name: DB_PASSWORD
>
> valueFrom: { secretKeyRef: { name: amr-secrets, key: db-password } }
>
> resources:
>
> requests: { cpu: \"500m\", memory: \"512Mi\" }
>
> limits: { cpu: \"2000m\", memory: \"2Gi\" }
>
> livenessProbe:
>
> httpGet: { path: /api/v1/health, port: 8000 }
>
> initialDelaySeconds: 30; periodSeconds: 15

**19.2 HorizontalPodAutoscaler**

> apiVersion: autoscaling/v2
>
> kind: HorizontalPodAutoscaler
>
> metadata: { name: celery-worker-hpa, namespace: amr-platform }
>
> spec:
>
> scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: celery-worker }
>
> minReplicas: 2
>
> maxReplicas: 20
>
> metrics:
>
> \- type: External
>
> external:
>
> metric: { name: amr_celery_queue_length }
>
> target: { type: AverageValue, averageValue: \"5\" } \# scale up when \> 5 tasks queued per replica

**19.3 Migration Strategy (Docker Compose → Kubernetes)**

  ---------- ------------------------------------------------------------------------------------------------------------ -------------------------------------------------------------------
  **Step**   **Action**                                                                                                   **Risk**

  1          Deploy stateless services first (API, Celery workers) as Deployments; connect to existing PostgreSQL/Redis   Low --- services are already stateless

  2          Migrate PostgreSQL to StatefulSet with persistent volumes; use pg_dump migration                             MEDIUM --- requires downtime window or dual-write strategy

  3          Migrate MinIO to distributed mode StatefulSet or external S3 (AWS/GCS)                                       Low --- files migrated via sync; application config only

  4          Configure Ingress (nginx-ingress or Traefik) with TLS via cert-manager                                       Low --- DNS/cert change

  5          Enable HPA on API and Celery worker Deployments; verify autoscaling                                          Low --- incremental enablement

  6          Migrate Nextflow executor from local Docker to Kubernetes executor (k8s plugin)                              MEDIUM --- Nextflow config change; test pipeline execution in k8s
  ---------- ------------------------------------------------------------------------------------------------------------ -------------------------------------------------------------------

> **SECTION 20 --- BACKUP AND DISASTER RECOVERY**

  ------------------------------ ------------------------------------------------------------------ ------------------------------------ ------------------------------ ----------------------------- -------------------------
  **Component**                  **Backup Method**                                                  **Frequency**                        **Retention**                  **RTO**                       **RPO**

  PostgreSQL                     pg_basebackup (full) + WAL streaming archive to MinIO              Full: weekly; WAL: continuous        4 weeks full; 14 days WAL      \< 4 hours                    \< 5 minutes

  PostgreSQL                     pg_dump logical (per-database)                                     Daily 03:00 UTC                      30 days                        \< 2 hours (faster restore)   \< 24 hours

  MinIO (genomes + results)      mc mirror to off-site bucket (or replication to secondary MinIO)   Continuous object replication        Per storage retention policy   \< 2 hours                    Near-zero (replication)

  Redis                          AOF + RDB snapshot to MinIO                                        RDB: every 15 min; AOF: realtime     7 days                         \< 15 min (RDB restore)       \< 1 min (AOF replay)

  Application config / secrets   Git-versioned (config); Vault snapshots (secrets)                  Every commit; daily Vault snapshot   Indefinite                     \< 30 min                     \< 24 hours

  Reference databases            Version-controlled + MinIO cold archive per version                On each DB update                    Indefinite (reproducibility)   \< 1 hour (redeploy)          N/A (versioned)
  ------------------------------ ------------------------------------------------------------------ ------------------------------------ ------------------------------ ----------------------------- -------------------------

> **SECTION 21 --- PERFORMANCE OPTIMISATION**

  ---------------------- -------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------
  **Area**               **Optimisation**                                                                                                                       **Expected Gain**

  Database queries       Composite B-tree indexes on (sample_id, status); partial indexes on active jobs; GIN on JSONB where queried by key                     10--100× query speedup for common access patterns

  API caching            Redis cache for breakpoint tables (24h TTL); ARO ontology (1h TTL); reference DB version (5m TTL)                                      \< 1ms cache hit vs 50--200ms DB query

  Nextflow parallelism   AMR detection runs 4 tools in parallel; mutation detection runs in parallel with AMR; max process forks = available CPUs / tool_cpus   4 parallel tools ≈ 4× throughput vs serial

  Connection pooling     SQLAlchemy async pool: min=5, max=20; PgBouncer transaction mode for 100+ concurrent workers                                           Prevents DB connection exhaustion at scale

  Container resources    CARD RGI gets 8 CPUs (most CPU-intensive tool); other tools 4 CPUs; confidence scorer 1 CPU (I/O-bound)                                Prevents CPU contention; optimal bin-packing

  File handling          Stream large FASTA uploads to MinIO (no full file in memory); stream PDF responses; gzip API responses \> 1 KB                         Handles files up to 2 GB without OOM

  Batch processing       Celery chord: validate all samples first, then fan out to AMR detection in parallel                                                    Batch of 100 genomes processes as fast as single when workers available
  ---------------------- -------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------

> **SECTION 22 --- DEPLOYMENT ENVIRONMENTS**

  ----------------- -------------------------------------------------- ----------------------------------------- ------------------------- -------------------------------------------
  **Environment**   **Infrastructure**                                 **Config Source**                         **DB Reset**              **Auto-Deploy**

  Development       Docker Compose (local laptop)                      docker-compose.dev.yml; .env.dev          Allowed (db_seed.py)      No; manual docker compose up

  Testing           Docker Compose (CI runner)                         docker-compose.test.yml; GitHub secrets   Yes (ephemeral per run)   Yes --- on every PR push

  Staging           Docker Compose (staging server) or K8s namespace   Vault secrets; environment ConfigMap      No; migration only        Yes --- on merge to main after tests pass

  Production        Docker Compose (HA) or Kubernetes cluster          Vault production secrets                  Never; migration only     Manual approval gate in GitHub Actions
  ----------------- -------------------------------------------------- ----------------------------------------- ------------------------- -------------------------------------------

**22.1 Release and Rollback Strategy**

-   Release: All releases are container image tags (git SHA). deploy/docker-compose.prod.yml pins VERSION=\$SHA.

-   Blue-green (optional): Spin up new containers alongside existing; switch nginx upstream; tear down old after validation.

-   Rollback: docker compose up -d \--force-recreate with previous SHA tag. DB migrations include downgrade() for one version back. Two-version downgrade requires manual DBA intervention.

-   DB migration safety: Alembic upgrade head runs before API starts (init container pattern). Staging migration always runs 24h before production.

> **SECTION 23 --- MAINTENANCE STRATEGY**

  ------------------------------------------------------ ------------------------------------------------------------------- ----------------------------------------------------------------------------------------------------------- ------------------------------------------------
  **Maintenance Task**                                   **Frequency**                                                       **Method**                                                                                                  **Downtime**

  Reference DB updates (CARD, AMRFinder)                 Monthly or on new release                                           db_update.sh; download → verify checksum → register in database_versions → activate; old version retained   None --- new version activated without restart

  Python dependency updates                              Monthly                                                             Dependabot PRs → CI → review → merge                                                                        None --- rolling restart after deploy

  Container base image patches                           Monthly (security patches: immediate)                               Rebuild images with updated base; push; deploy via CI                                                       Brief container restart (\< 30s)

  PostgreSQL minor updates                               Quarterly                                                           pg_upgrade or dump/restore on major; pg_ctl reload on minor                                                 Brief for minor; maintenance window for major

  Alembic schema migrations                              With each feature release                                           Automatic on container startup; staging tested 24h prior                                                    None for additive; brief for index builds

  Knowledgebase updates (mutation KB, rule repository)   On new clinical evidence                                            JSON file update → version bump → deploy; existing analyses not retroactively changed                       None

  SSL certificate renewal                                Auto via Let\'s Encrypt (cert-manager in K8s; acme.sh in compose)   Automated 30 days before expiry                                                                             None

  Security patches (OS-level)                            Immediately on Critical CVE                                         Rebuild affected containers → CI → deploy                                                                   Brief container restart
  ------------------------------------------------------ ------------------------------------------------------------------- ----------------------------------------------------------------------------------------------------------- ------------------------------------------------

> **SECTION 24 --- IMPLEMENTATION ROADMAP**

  ----------- --------------------------- -------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------------------
  **Phase**   **Name**                    **Duration**   **Deliverables**                                                                                                                                                                                                          **Acceptance Criteria**

  Phase 1     Infrastructure Foundation   2 weeks        Docker Compose stack (all services healthy); PostgreSQL schema v1; Redis operational; MinIO buckets created; GitHub Actions lint + unit test pipeline; .env template; secrets management                                  All containers pass health checks; pytest unit tests pass in CI; alembic upgrade head runs cleanly

  Phase 2     Backend Services            3 weeks        FastAPI app with auth/users/projects/samples/files endpoints; JWT auth flow; RBAC; file upload to MinIO; Celery worker operational; job submission and status polling; WebSocket progress                                 End-to-end: register → login → create project → upload FASTA → job QUEUED → status poll works; WebSocket receives events

  Phase 3     Workflow Integration        2 weeks        Nextflow main.nf with all 8 processes wired; validation gate working; parallel AMR + mutation stages; subworkflows complete; nf-test tests pass; Celery → Nextflow subprocess handoff                                     Reference genome runs end-to-end in Nextflow: COMPLETED status; all output files written to MinIO

  Phase 4     Biological Engines          4 weeks        All 6 analysis engines (1A--1F) integrated; CARD/AMRFinder/ResFinder/Abricate running in Docker; mutation detection with knowledgebase; phenotype prediction with EUCAST rules; virulence profiling; confidence scoring   5 reference genomes produce expected gene/mutation/phenotype calls; recall ≥ 0.90 on benchmark

  Phase 5     Reporting                   2 weeks        JSON/TSV/PDF reports for all engines; module2_input.csv export; presigned URL download; report API endpoints; PDF rendering with WeasyPrint                                                                               PDF reports render correctly; module2_input.csv passes schema validation; all 7 output file types generated

  Phase 6     Testing                     2 weeks        Full pytest suite (unit + integration + contract + load); nf-test workflow suite; ZAP DAST scan on staging; regression test baseline established; performance benchmarks within targets                                   ≥ 90% unit coverage; zero Critical security findings; all benchmark targets met; regression tests pass

  Phase 7     Production Deployment       1 week         Production environment deployed; monitoring stack live; alerting configured; backup scripts tested; DR runbook written; operator training; go-live                                                                        Production health checks pass; monitoring dashboards populated; backup restore tested; first real genome successfully analysed
  ----------- --------------------------- -------------- ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- --------------------------------------------------------------------------------------------------------------------------------
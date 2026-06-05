# 02 — Database Design Specification

> **MVP Implementation Note:** Start with SQLite and implement only the sections marked 🟢 MVP. Migrate to PostgreSQL and add remaining tables in later phases.

| Section | Tables | Phase |
|---------|--------|-------|
| 4 — User Management | users, roles, sessions | 🟡 Phase 2 |
| 5 — Project Management | projects, project_members | 🟡 Phase 2 |
| 6 — Sample Management | samples, sample_files | 🟢 MVP |
| 8 — Workflow Execution | analysis_jobs | 🟢 MVP (simplified) |
| 10 — AMR Detection | amr_genes, amr_hits | 🟢 MVP |
| 12 — Mutations | mutations, mutation_annotations | 🟡 Phase 2 |
| 13 — Mechanisms | mechanisms, gene_mechanisms | 🟡 Phase 2 |
| 14 — Phenotype | phenotype_predictions | 🟠 Phase 3 |
| 15 — Virulence | virulence_factors | 🔵 Phase 4 |
| 16 — Confidence | confidence_scores | 🔵 Phase 4 |

---

**DATABASE DESIGN SPECIFICATION**

**DDS --- Version 1.0**

**ANTIMICROBIAL RESISTANCE ANALYSIS PLATFORM**

*Modules 1 · 2 · 3 --- Enterprise PostgreSQL Schema*

PostgreSQL 15 · SQLAlchemy 2 · Alembic · FastAPI · Celery

CONFIDENTIAL --- Internal Engineering Document

> **SECTION 1 --- DATABASE OBJECTIVES**

**1.1 Purpose**

The AMR Platform database is the authoritative, durable data store for all genomic analysis artefacts, scientific findings, and operational metadata produced by the antimicrobial resistance characterisation platform. It serves as the single source of truth across Module 1 (AMR Characterisation), Module 2 (Genotype--Phenotype Concordance), and Module 3 (Mobile Genetic Element Origin Analysis).

**1.2 Scope**

  -------------------------------- ----------------- -----------------------------------------------------
  **Domain**                       **Included**      **Notes**

  Identity & Access                Yes               Users, roles, projects, API tokens

  Sample Management                Yes               Genome files, metadata, assembly metrics

  Workflow Execution               Yes               Celery jobs, Nextflow runs, task logs

  AMR Results (Module 1)           Yes               Genes, mutations, mechanisms, phenotypes, virulence

  Genotype--Phenotype (Module 2)   Schema reserved   Tables defined; populated by future module

  MGE Origin (Module 3)            Schema reserved   Tables defined; populated by future module

  Reference Databases              Yes               CARD, AMRFinderPlus, ResFinder, VFDB versions

  Reporting                        Yes               Report metadata and file pointers

  Audit & Provenance               Yes               Full immutable audit trail
  -------------------------------- ----------------- -----------------------------------------------------

**1.3 Data Lifecycle**

-   Upload: Sample FASTA uploaded → sample record created → storage path recorded → checksum stored.

-   Analysis: Job created → workflow executed → results written incrementally as services complete.

-   Retention: Active results retained 12 months; archived after; audit logs retained 10 years.

-   Purge: FASTA files purged on schedule; results archived to cold storage; soft-delete for logical removal.

**1.4 Data Ownership, Retention, Auditability, Reproducibility, and Traceability**

  ---------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Principle**                **Implementation**

  Data Ownership               Data owned by the creating project; scoped via project_id FK on all result tables; user cannot access other projects without explicit membership

  Data Retention               Active results: 12 months. Clinical reports: 7 years. Audit logs: 10 years minimum. Reference DB versions: indefinite (scientific reproducibility)

  Auditability                 Every INSERT/UPDATE/DELETE on core tables writes a row to audit_logs. Before/after JSON snapshots stored. User, timestamp, action, and table recorded

  Reproducibility              Every analysis result linked to db_version_id (reference database version at time of run) and workflow_run_id (Nextflow run ID, container versions, tool parameters)

  Traceability                 Complete data lineage from sample upload through every pipeline stage to final report, navigable via foreign keys on all result tables

  Multi-user / Multi-project   Row-level data isolation enforced at ORM and API layers; PostgreSQL RLS policies applied as additional safety net
  ---------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------

> **SECTION 2 --- DATABASE ARCHITECTURE**

**2.1 Logical Domain Architecture**

> ┌───────────────────────────────────────────────────────────────┐
>
> │ AMR PLATFORM DATABASE │
>
> │ │
>
> │ ┌─────────────────┐ ┌─────────────────────────────────┐ │
>
> │ │ USER DOMAIN │ │ PROJECT DOMAIN │ │
>
> │ │ users │ │ projects project_members │ │
>
> │ │ roles │◄───│ project_settings │ │
>
> │ │ permissions │ │ project_permissions │ │
>
> │ │ sessions │ └────────────────┬────────────────┘ │
>
> │ │ api_tokens │ │ │
>
> │ └─────────────────┘ ▼ │
>
> │ ┌─────────────────────────────┐ │
>
> │ │ SAMPLE DOMAIN │ │
>
> │ │ samples sample_metadata │ │
>
> │ │ sample_files assemblies │ │
>
> │ │ assembly_metrics │ │
>
> │ └──────────────┬──────────────┘ │
>
> │ │ │
>
> │ ┌───────────────────┐ ▼ │
>
> │ │ REFERENCE DOMAIN │ ┌─────────────────────────────┐ │
>
> │ │ reference_dbs │ │ WORKFLOW DOMAIN │ │
>
> │ │ db_versions │◄───│ analysis_jobs job_tasks │ │
>
> │ │ db_checksums │ │ workflow_runs task_logs │ │
>
> │ └───────────────────┘ └──────────────┬──────────────┘ │
>
> │ │ │
>
> │ ▼ │
>
> │ ┌────────────────────────────────────────┐ │
>
> │ │ ANALYSIS DOMAIN │ │
>
> │ │ amr_genes amr_hits mutations │ │
>
> │ │ mechanisms phenotype_predictions │ │
>
> │ │ virulence_factors confidence_scores │ │
>
> │ │ alignment_results blast_statistics │ │
>
> │ └────────────────────┬───────────────────┘ │
>
> │ │ │
>
> │ ┌────────────────┐ ▼ │
>
> │ │ AUDIT DOMAIN │ ┌─────────────────────────────────┐ │
>
> │ │ audit_logs │ │ REPORTING DOMAIN │ │
>
> │ │ data_lineage │ │ reports report_files │ │
>
> │ │ change_history│ │ module2_exports │ │
>
> │ └────────────────┘ └─────────────────────────────────┘ │
>
> └───────────────────────────────────────────────────────────────┘

**2.2 Domain Responsibilities**

  ------------------ --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------
  **Domain**         **Tables**                                                                                                                                                                                                                  **Responsibility**

  User Domain        users, roles, permissions, user_roles, sessions, api_tokens                                                                                                                                                                 Authentication, identity, RBAC, session management

  Project Domain     projects, project_members, project_permissions, project_settings                                                                                                                                                            Multi-tenancy, collaboration, access scope

  Sample Domain      samples, sample_metadata, sample_files, sample_versions, assemblies, assembly_metrics, validation_reports                                                                                                                   Genome input lifecycle, file management, QC metrics

  Reference Domain   reference_databases, database_versions, database_downloads, database_checksums                                                                                                                                              Scientific reproducibility --- tracks every DB version used in analysis

  Workflow Domain    analysis_jobs, job_tasks, workflow_runs, workflow_steps, task_logs                                                                                                                                                          Celery job lifecycle, Nextflow execution tracking, resource telemetry

  Analysis Domain    amr_genes, amr_hits, amr_annotations, mutations, mutation_annotations, mechanisms, gene_mechanisms, phenotype_predictions, prediction_evidence, virulence_factors, confidence_scores, alignment_results, blast_statistics   All scientific findings from Module 1 pipeline

  Reporting Domain   reports, report_files, report_metadata, module2_exports                                                                                                                                                                     Output artefact metadata, file pointers, export tracking

  Audit Domain       audit_logs, change_history, data_lineage                                                                                                                                                                                    Immutable audit trail, provenance, compliance
  ------------------ --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------------------------------------

> **SECTION 3 --- ENTITY RELATIONSHIP DESIGN**

**3.1 ERD Overview**

> users ──\< user_roles \>── roles ──\< permissions
>
> │
>
> └──\< project_members \>── projects
>
> │
>
> └──\< samples
>
> │
>
> ┌───────┤
>
> │ │
>
> assemblies analysis_jobs
>
> │ │
>
> assembly_metrics workflow_runs
>
> │ │
>
> └─────┬─────┘
>
> │ (sample_id, job_id)
>
> ┌────────────────┼────────────────┐
>
> ▼ ▼ ▼
>
> amr_genes mutations virulence_factors
>
> │ │
>
> amr_hits mutation_annotations
>
> │
>
> alignment_results
>
> amr_genes ──\< gene_mechanisms \>── mechanisms
>
> │
>
> phenotype_predictions
>
> │
>
> confidence_scores
>
> │
>
> reports / module2_exports

**3.2 Relationship Definitions**

  --------------------------------------------- ------------------------------------ ---------------- ---------------------------------------------------
  **Relationship**                              **Type**                             **Cascade**      **Delete Rule**

  users → user_roles                            One-to-Many                          CASCADE INSERT   CASCADE DELETE

  roles → user_roles                            One-to-Many                          CASCADE INSERT   RESTRICT (role must be unused)

  users → projects (via project_members)        Many-to-Many                         \-               RESTRICT (cannot delete user with owned projects)

  projects → samples                            One-to-Many                          CASCADE INSERT   RESTRICT (cannot delete project with samples)

  samples → assemblies                          One-to-One                           CASCADE          CASCADE DELETE

  samples → analysis_jobs                       One-to-Many                          \-               SET NULL on sample delete

  analysis_jobs → workflow_runs                 One-to-Many                          CASCADE          CASCADE DELETE

  samples → amr_genes                           One-to-Many                          CASCADE          CASCADE DELETE

  amr_genes → amr_hits                          One-to-Many                          CASCADE          CASCADE DELETE

  amr_hits → alignment_results                  One-to-One                           CASCADE          CASCADE DELETE

  amr_genes → gene_mechanisms                   Many-to-Many (via gene_mechanisms)   \-               CASCADE DELETE

  mechanisms → gene_mechanisms                  One-to-Many                          \-               RESTRICT

  samples → phenotype_predictions               One-to-Many                          CASCADE          CASCADE DELETE

  phenotype_predictions → prediction_evidence   One-to-Many                          CASCADE          CASCADE DELETE

  samples → mutations                           One-to-Many                          CASCADE          CASCADE DELETE

  samples → virulence_factors                   One-to-Many                          CASCADE          CASCADE DELETE

  samples → confidence_scores                   One-to-Many                          CASCADE          CASCADE DELETE

  samples → reports                             One-to-Many                          \-               RESTRICT (cannot delete sample with reports)

  analysis_jobs → reports                       One-to-Many                          \-               SET NULL

  db_versions → amr_genes (db_version_id)       One-to-Many                          \-               RESTRICT (audit integrity)
  --------------------------------------------- ------------------------------------ ---------------- ---------------------------------------------------

> **SECTION 4 --- USER MANAGEMENT TABLES**

**4.1 Table: users**

> CREATE TABLE users (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> email VARCHAR(255) NOT NULL,
>
> username VARCHAR(100) NOT NULL,
>
> password_hash VARCHAR(255) NOT NULL,
>
> full_name VARCHAR(255),
>
> is_active BOOLEAN NOT NULL DEFAULT TRUE,
>
> is_superadmin BOOLEAN NOT NULL DEFAULT FALSE,
>
> mfa_secret VARCHAR(64), \-- TOTP secret, NULL if MFA disabled
>
> mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
>
> last_login_at TIMESTAMPTZ,
>
> created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> deleted_at TIMESTAMPTZ, \-- soft delete
>
> CONSTRAINT uq_users_email UNIQUE (email),
>
> CONSTRAINT uq_users_username UNIQUE (username)
>
> );
>
> CREATE INDEX idx_users_email ON users (email) WHERE deleted_at IS NULL;
>
> CREATE INDEX idx_users_active ON users (is_active) WHERE deleted_at IS NULL;

**4.2 Table: roles**

> CREATE TABLE roles (
>
> id SMALLSERIAL PRIMARY KEY,
>
> name VARCHAR(50) NOT NULL,
>
> description TEXT,
>
> is_system BOOLEAN NOT NULL DEFAULT FALSE,
>
> created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> CONSTRAINT uq_roles_name UNIQUE (name)
>
> );
>
> \-- Seed: SUPERADMIN, ADMIN, PROJECT_OWNER, ANALYST, VIEWER

**4.3 Table: permissions**

> CREATE TABLE permissions (
>
> id SMALLSERIAL PRIMARY KEY,
>
> resource VARCHAR(100) NOT NULL, \-- e.g. \"samples\", \"reports\"
>
> action VARCHAR(50) NOT NULL, \-- e.g. \"create\", \"read\", \"delete\"
>
> description TEXT,
>
> CONSTRAINT uq_perm UNIQUE (resource, action)
>
> );

**4.4 Table: user_roles**

> CREATE TABLE user_roles (
>
> user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
>
> role_id SMALLINT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
>
> project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
>
> granted_by UUID REFERENCES users(id) ON DELETE SET NULL,
>
> granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> PRIMARY KEY (user_id, role_id, COALESCE(project_id, uuid_nil()))
>
> );

**4.5 Table: sessions**

> CREATE TABLE sessions (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
>
> refresh_token VARCHAR(512) NOT NULL,
>
> ip_address INET,
>
> user_agent TEXT,
>
> expires_at TIMESTAMPTZ NOT NULL,
>
> revoked_at TIMESTAMPTZ,
>
> created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> CONSTRAINT uq_sessions_token UNIQUE (refresh_token)
>
> );
>
> CREATE INDEX idx_sessions_user ON sessions (user_id) WHERE revoked_at IS NULL;

**4.6 Table: api_tokens**

> CREATE TABLE api_tokens (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
>
> name VARCHAR(100) NOT NULL,
>
> token_hash VARCHAR(255) NOT NULL,
>
> scopes TEXT\[\] NOT NULL DEFAULT ARRAY\[\]::TEXT\[\],
>
> last_used TIMESTAMPTZ,
>
> expires_at TIMESTAMPTZ,
>
> revoked_at TIMESTAMPTZ,
>
> created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> CONSTRAINT uq_api_tokens_hash UNIQUE (token_hash)
>
> );
>
> CREATE INDEX idx_api_tokens_user ON api_tokens (user_id) WHERE revoked_at IS NULL;

**4.7 SQLAlchemy Models --- User Domain**

> from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, ARRAY
>
> from sqlalchemy.dialects.postgresql import UUID, INET
>
> from sqlalchemy.orm import relationship
>
> from .base import Base, TimestampMixin, SoftDeleteMixin
>
> class User(Base, TimestampMixin, SoftDeleteMixin):
>
> \_\_tablename\_\_ = \"users\"
>
> id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
>
> email = Column(String(255), unique=True, nullable=False)
>
> username = Column(String(100), unique=True, nullable=False)
>
> password_hash = Column(String(255), nullable=False)
>
> full_name = Column(String(255))
>
> is_active = Column(Boolean, default=True, nullable=False)
>
> is_superadmin = Column(Boolean, default=False, nullable=False)
>
> mfa_enabled = Column(Boolean, default=False, nullable=False)
>
> mfa_secret = Column(String(64))
>
> last_login_at = Column(DateTime(timezone=True))
>
> roles = relationship(\"UserRole\", back_populates=\"user\", cascade=\"all, delete-orphan\")
>
> sessions = relationship(\"Session\", back_populates=\"user\", cascade=\"all, delete-orphan\")
>
> **SECTION 5 --- PROJECT MANAGEMENT TABLES**

**5.1 Table: projects**

> CREATE TABLE projects (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> name VARCHAR(200) NOT NULL,
>
> slug VARCHAR(100) NOT NULL,
>
> description TEXT,
>
> owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
>
> project_type VARCHAR(50) NOT NULL DEFAULT \'research\',
>
> \-- research \| clinical \| surveillance \| batch
>
> is_active BOOLEAN NOT NULL DEFAULT TRUE,
>
> created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> deleted_at TIMESTAMPTZ,
>
> CONSTRAINT uq_project_slug UNIQUE (slug)
>
> );
>
> CREATE INDEX idx_project_owner ON projects (owner_id) WHERE deleted_at IS NULL;

**5.2 Table: project_members**

> CREATE TABLE project_members (
>
> project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
>
> user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
>
> role_id SMALLINT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
>
> added_by UUID REFERENCES users(id) ON DELETE SET NULL,
>
> added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> PRIMARY KEY (project_id, user_id)
>
> );

**5.3 Table: project_settings**

> CREATE TABLE project_settings (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
>
> default_identity_threshold NUMERIC(5,2) DEFAULT 80.0,
>
> default_coverage_threshold NUMERIC(5,2) DEFAULT 80.0,
>
> breakpoint_source VARCHAR(20) DEFAULT \'EUCAST\',
>
> enabled_tools TEXT\[\] DEFAULT ARRAY\[\'CARD\',\'AMRFinder\',\'ResFinder\',\'Abricate\'\],
>
> notification_email VARCHAR(255),
>
> auto_export_module2 BOOLEAN DEFAULT FALSE,
>
> retention_months SMALLINT DEFAULT 12,
>
> updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> CONSTRAINT uq_proj_settings UNIQUE (project_id)
>
> );
>
> **SECTION 6 --- SAMPLE MANAGEMENT TABLES**

**6.1 Table: samples**

> CREATE TABLE samples (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> project_id UUID NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
>
> isolate_name VARCHAR(200) NOT NULL,
>
> species VARCHAR(200),
>
> species_taxid INTEGER,
>
> host VARCHAR(100),
>
> collection_date DATE,
>
> source_type VARCHAR(100), \-- clinical \| environmental \| surveillance
>
> location VARCHAR(200),
>
> country_code CHAR(3),
>
> submitter_id UUID REFERENCES users(id) ON DELETE SET NULL,
>
> status VARCHAR(30) NOT NULL DEFAULT \'UPLOADED\',
>
> \-- UPLOADED \| VALIDATING \| VALID \| INVALID \| QUEUED \| RUNNING \| COMPLETED \| FAILED
>
> created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> deleted_at TIMESTAMPTZ
>
> );
>
> CREATE INDEX idx_samples_project ON samples (project_id) WHERE deleted_at IS NULL;
>
> CREATE INDEX idx_samples_species ON samples (species);
>
> CREATE INDEX idx_samples_status ON samples (status);

**6.2 Table: sample_metadata**

> CREATE TABLE sample_metadata (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> sample_id UUID NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
>
> key VARCHAR(100) NOT NULL,
>
> value TEXT,
>
> value_type VARCHAR(20) DEFAULT \'string\', \-- string \| integer \| float \| date \| json
>
> CONSTRAINT uq_sample_meta UNIQUE (sample_id, key)
>
> );

**6.3 Table: sample_files**

> CREATE TABLE sample_files (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> sample_id UUID NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
>
> file_type VARCHAR(50) NOT NULL, \-- genome_fasta \| assembly_fasta \| consensus_fasta
>
> storage_path VARCHAR(500) NOT NULL,
>
> storage_backend VARCHAR(50) DEFAULT \'minio\',
>
> filename VARCHAR(255) NOT NULL,
>
> file_size_bytes BIGINT,
>
> checksum_sha256 CHAR(64) NOT NULL,
>
> upload_status VARCHAR(30) DEFAULT \'COMPLETE\',
>
> uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> CONSTRAINT uq_sample_file_type UNIQUE (sample_id, file_type)
>
> );

**6.4 Table: assemblies**

> CREATE TABLE assemblies (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> sample_id UUID NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
>
> assembly_version VARCHAR(20) DEFAULT \'1.0\',
>
> assembler VARCHAR(100), \-- SPAdes \| Unicycler \| Flye
>
> assembler_version VARCHAR(30),
>
> input_file_id UUID REFERENCES sample_files(id) ON DELETE SET NULL,
>
> validated_fasta_path VARCHAR(500),
>
> created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> CONSTRAINT uq_assembly_sample UNIQUE (sample_id, assembly_version)
>
> );

**6.5 Table: assembly_metrics**

> CREATE TABLE assembly_metrics (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> assembly_id UUID NOT NULL REFERENCES assemblies(id) ON DELETE CASCADE,
>
> total_length_bp BIGINT,
>
> contig_count INTEGER,
>
> n50_bp INTEGER,
>
> n90_bp INTEGER,
>
> gc_percent NUMERIC(5,2),
>
> n_percent NUMERIC(5,2),
>
> longest_contig INTEGER,
>
> shortest_contig INTEGER,
>
> l50 INTEGER,
>
> species_prediction VARCHAR(200),
>
> species_confidence NUMERIC(5,4),
>
> validation_status VARCHAR(20) DEFAULT \'PENDING\',
>
> validation_warnings JSONB,
>
> validation_errors JSONB,
>
> computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> CONSTRAINT uq_metrics_assembly UNIQUE (assembly_id)
>
> );
>
> **SECTION 7 --- REFERENCE DATABASE TABLES**

**7.1 Table: reference_databases**

> CREATE TABLE reference_databases (
>
> id SMALLSERIAL PRIMARY KEY,
>
> name VARCHAR(100) NOT NULL, \-- CARD \| AMRFinderPlus \| ResFinder \| VFDB \| VirulenceFinder
>
> short_code VARCHAR(30) NOT NULL,
>
> description TEXT,
>
> source_url VARCHAR(500),
>
> data_type VARCHAR(50) NOT NULL, \-- AMR \| virulence \| both
>
> CONSTRAINT uq_refdb_code UNIQUE (short_code)
>
> );

**7.2 Table: database_versions**

> CREATE TABLE database_versions (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> db_id SMALLINT NOT NULL REFERENCES reference_databases(id),
>
> version VARCHAR(50) NOT NULL,
>
> release_date DATE,
>
> download_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> downloaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
>
> is_active BOOLEAN NOT NULL DEFAULT TRUE,
>
> index_path VARCHAR(500),
>
> sequence_path VARCHAR(500),
>
> notes TEXT,
>
> CONSTRAINT uq_dbversion UNIQUE (db_id, version)
>
> );
>
> CREATE INDEX idx_dbver_active ON database_versions (db_id, is_active);

**7.3 Table: database_checksums**

> CREATE TABLE database_checksums (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> db_version_id UUID NOT NULL REFERENCES database_versions(id) ON DELETE CASCADE,
>
> file_name VARCHAR(255) NOT NULL,
>
> checksum_sha256 CHAR(64) NOT NULL,
>
> file_size_bytes BIGINT,
>
> verified_at TIMESTAMPTZ,
>
> CONSTRAINT uq_db_checksum UNIQUE (db_version_id, file_name)
>
> );
>
> **Purpose:** Every amr_genes, mutations, and virulence_factors row carries a db_version_id FK ensuring any result can be reproduced by pinning to the exact database version used.
>
> **SECTION 8 --- WORKFLOW EXECUTION TABLES**

**8.1 Table: analysis_jobs**

> CREATE TABLE analysis_jobs (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> sample_id UUID NOT NULL REFERENCES samples(id) ON DELETE SET NULL,
>
> project_id UUID NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
>
> submitted_by UUID REFERENCES users(id) ON DELETE SET NULL,
>
> celery_task_id VARCHAR(255),
>
> status VARCHAR(30) NOT NULL DEFAULT \'QUEUED\',
>
> \-- QUEUED \| RUNNING \| COMPLETED \| FAILED \| CANCELLED \| RETRYING
>
> priority SMALLINT NOT NULL DEFAULT 5, \-- 1=high, 10=low
>
> queue_name VARCHAR(50) DEFAULT \'default\',
>
> retry_count SMALLINT DEFAULT 0,
>
> max_retries SMALLINT DEFAULT 3,
>
> error_code VARCHAR(100),
>
> error_message TEXT,
>
> submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> started_at TIMESTAMPTZ,
>
> completed_at TIMESTAMPTZ,
>
> analysis_config JSONB, \-- snapshot of settings at time of submission
>
> );
>
> CREATE INDEX idx_job_sample ON analysis_jobs (sample_id);
>
> CREATE INDEX idx_job_status ON analysis_jobs (status) WHERE status IN (\'QUEUED\',\'RUNNING\');
>
> CREATE INDEX idx_job_project ON analysis_jobs (project_id);

**8.2 Table: workflow_runs**

> CREATE TABLE workflow_runs (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> job_id UUID NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
>
> nextflow_run_id VARCHAR(100), \-- Nextflow session ID
>
> nextflow_version VARCHAR(20),
>
> work_dir VARCHAR(500), \-- Nextflow work directory
>
> command_line TEXT, \-- Full nextflow command
>
> status VARCHAR(30) NOT NULL DEFAULT \'RUNNING\',
>
> started_at TIMESTAMPTZ,
>
> completed_at TIMESTAMPTZ,
>
> duration_seconds INTEGER,
>
> cpu_hours NUMERIC(10,4),
>
> peak_memory_gb NUMERIC(8,3),
>
> container_versions JSONB, \-- {tool: image:tag} snapshot
>
> pipeline_version VARCHAR(30),
>
> git_commit CHAR(40)
>
> );

**8.3 Table: workflow_steps**

> CREATE TABLE workflow_steps (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> workflow_run_id UUID NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
>
> step_name VARCHAR(100) NOT NULL,
>
> process_name VARCHAR(100) NOT NULL,
>
> status VARCHAR(30) NOT NULL DEFAULT \'PENDING\',
>
> attempt SMALLINT DEFAULT 1,
>
> started_at TIMESTAMPTZ,
>
> completed_at TIMESTAMPTZ,
>
> cpus_requested SMALLINT,
>
> memory_gb NUMERIC(6,2),
>
> realtime_ms BIGINT,
>
> container VARCHAR(200),
>
> exit_code SMALLINT,
>
> work_dir_hash VARCHAR(50)
>
> );

**8.4 Table: task_logs**

> CREATE TABLE task_logs (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> step_id UUID NOT NULL REFERENCES workflow_steps(id) ON DELETE CASCADE,
>
> log_level VARCHAR(10) NOT NULL DEFAULT \'INFO\',
>
> message TEXT NOT NULL,
>
> logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );
>
> CREATE INDEX idx_task_log_step ON task_logs (step_id, logged_at);
>
> **SECTION 9 --- GENOME VALIDATION TABLES**

**9.1 Table: validation_reports**

> CREATE TABLE validation_reports (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> assembly_id UUID NOT NULL REFERENCES assemblies(id) ON DELETE CASCADE,
>
> job_id UUID REFERENCES analysis_jobs(id) ON DELETE SET NULL,
>
> validation_status VARCHAR(20) NOT NULL,
>
> \-- PASSED \| FAILED \| PASSED_WITH_WARNINGS
>
> total_checks SMALLINT DEFAULT 0,
>
> checks_passed SMALLINT DEFAULT 0,
>
> checks_failed SMALLINT DEFAULT 0,
>
> warnings JSONB, \-- \[{code, message, threshold, observed}\]
>
> errors JSONB, \-- \[{code, message, threshold, observed}\]
>
> validated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> CONSTRAINT uq_validation UNIQUE (assembly_id, job_id)
>
> );
>
> **SECTION 10 --- AMR DETECTION TABLES**

**10.1 Table: amr_genes**

> CREATE TABLE amr_genes (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> sample_id UUID NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
>
> job_id UUID REFERENCES analysis_jobs(id) ON DELETE SET NULL,
>
> db_version_id UUID NOT NULL REFERENCES database_versions(id) ON DELETE RESTRICT,
>
> gene_name VARCHAR(200) NOT NULL,
>
> gene_family VARCHAR(200),
>
> aro_accession VARCHAR(50), \-- CARD ARO ID e.g. ARO:3000001
>
> drug_class VARCHAR(200),
>
> resistance_mechanism VARCHAR(100),
>
> antibiotic_class VARCHAR(200),
>
> mechanism_type VARCHAR(50),
>
> confidence_tier VARCHAR(20) DEFAULT \'MEDIUM\', \-- HIGH \| MEDIUM \| LOW \| INSUFFICIENT
>
> confidence_score NUMERIC(5,4),
>
> created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );
>
> CREATE INDEX idx_amr_genes_sample ON amr_genes (sample_id);
>
> CREATE INDEX idx_amr_genes_aro ON amr_genes (aro_accession);

**10.2 Table: amr_hits**

> CREATE TABLE amr_hits (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> amr_gene_id UUID NOT NULL REFERENCES amr_genes(id) ON DELETE CASCADE,
>
> detection_tool VARCHAR(50) NOT NULL, \-- CARD \| AMRFinderPlus \| ResFinder \| Abricate
>
> hit_category VARCHAR(20) NOT NULL, \-- Perfect \| Strict \| Loose \| Nudged
>
> identity_pct NUMERIC(6,3) NOT NULL,
>
> coverage_pct NUMERIC(6,3) NOT NULL,
>
> contig_id VARCHAR(200),
>
> contig_start INTEGER,
>
> contig_end INTEGER,
>
> strand CHAR(1), \-- + \| -
>
> reference_length INTEGER,
>
> query_length INTEGER,
>
> partial_hit BOOLEAN NOT NULL DEFAULT FALSE,
>
> raw_result_json JSONB, \-- full tool output for audit
>
> detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );
>
> CREATE INDEX idx_amr_hits_gene ON amr_hits (amr_gene_id);

**10.3 Table: amr_annotations**

> CREATE TABLE amr_annotations (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> amr_gene_id UUID NOT NULL REFERENCES amr_genes(id) ON DELETE CASCADE,
>
> annotation_source VARCHAR(50),
>
> key VARCHAR(100) NOT NULL,
>
> value TEXT,
>
> CONSTRAINT uq_amr_annotation UNIQUE (amr_gene_id, annotation_source, key)
>
> );
>
> **SECTION 11 --- ALIGNMENT AND SEARCH TABLES**

**11.1 Table: alignment_results**

> CREATE TABLE alignment_results (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> amr_hit_id UUID REFERENCES amr_hits(id) ON DELETE CASCADE,
>
> sample_id UUID NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
>
> search_method VARCHAR(30) NOT NULL,
>
> \-- SmithWaterman \| NeedlemanWunsch \| BWA_MEM \| BWT_FM \| BLAST
>
> query_sequence TEXT,
>
> reference_name VARCHAR(200),
>
> alignment_score NUMERIC(12,2),
>
> identity_pct NUMERIC(6,3),
>
> coverage_pct NUMERIC(6,3),
>
> query_start INTEGER,
>
> query_end INTEGER,
>
> ref_start INTEGER,
>
> ref_end INTEGER,
>
> cigar_string TEXT,
>
> created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );

**11.2 Table: blast_statistics**

> CREATE TABLE blast_statistics (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> alignment_id UUID NOT NULL REFERENCES alignment_results(id) ON DELETE CASCADE,
>
> bit_score NUMERIC(12,3),
>
> e_value DOUBLE PRECISION,
>
> raw_score INTEGER,
>
> gap_opens INTEGER,
>
> gap_extensions INTEGER,
>
> mismatch_count INTEGER,
>
> match_count INTEGER,
>
> query_length INTEGER,
>
> db_size_bases BIGINT,
>
> db_num_seqs INTEGER
>
> );
>
> **SECTION 12 --- MUTATION TABLES**

**12.1 Table: mutations**

> CREATE TABLE mutations (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> sample_id UUID NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
>
> job_id UUID REFERENCES analysis_jobs(id) ON DELETE SET NULL,
>
> db_version_id UUID NOT NULL REFERENCES database_versions(id) ON DELETE RESTRICT,
>
> gene_name VARCHAR(200) NOT NULL,
>
> gene_id UUID REFERENCES amr_genes(id) ON DELETE SET NULL,
>
> position INTEGER NOT NULL,
>
> ref_nucleotide VARCHAR(10),
>
> alt_nucleotide VARCHAR(10),
>
> ref_amino_acid VARCHAR(10),
>
> alt_amino_acid VARCHAR(10),
>
> codon_change VARCHAR(20),
>
> mutation_type VARCHAR(50), \-- SNP \| insertion \| deletion \| inversion
>
> clinical_significance VARCHAR(50), \-- resistance \| compensatory \| neutral \| unknown
>
> associated_drug VARCHAR(200),
>
> confidence_score NUMERIC(5,4),
>
> detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );
>
> CREATE INDEX idx_mutations_sample ON mutations (sample_id);

**12.2 Table: mutation_annotations & mutation_evidence**

> CREATE TABLE mutation_annotations (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> mutation_id UUID NOT NULL REFERENCES mutations(id) ON DELETE CASCADE,
>
> source VARCHAR(100), \-- CARD \| ClinVar \| literature_pmid
>
> key VARCHAR(100),
>
> value TEXT
>
> );
>
> CREATE TABLE mutation_evidence (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> mutation_id UUID NOT NULL REFERENCES mutations(id) ON DELETE CASCADE,
>
> evidence_type VARCHAR(50), \-- in_vitro \| clinical \| animal_model \| computational
>
> evidence_level SMALLINT, \-- 1=highest 5=lowest
>
> pmid VARCHAR(20),
>
> description TEXT,
>
> added_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );
>
> **SECTION 13 --- MECHANISM CLASSIFICATION TABLES**

**13.1 Table: mechanism_classes**

> CREATE TABLE mechanism_classes (
>
> id SMALLSERIAL PRIMARY KEY,
>
> name VARCHAR(100) NOT NULL,
>
> code VARCHAR(50) NOT NULL,
>
> description TEXT,
>
> CONSTRAINT uq_mech_code UNIQUE (code)
>
> );
>
> \-- Seed data:
>
> \-- antibiotic_inactivation, target_alteration, target_protection,
>
> \-- efflux_pump, reduced_permeability, target_replacement, enzymatic_modification

**13.2 Table: mechanisms**

> CREATE TABLE mechanisms (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> class_id SMALLINT NOT NULL REFERENCES mechanism_classes(id),
>
> name VARCHAR(200) NOT NULL,
>
> aro_accession VARCHAR(50),
>
> description TEXT,
>
> drug_classes TEXT\[\], \-- antibiotic classes affected
>
> CONSTRAINT uq_mechanism_aro UNIQUE (aro_accession)
>
> );

**13.3 Table: gene_mechanisms (junction)**

> CREATE TABLE gene_mechanisms (
>
> amr_gene_id UUID NOT NULL REFERENCES amr_genes(id) ON DELETE CASCADE,
>
> mechanism_id UUID NOT NULL REFERENCES mechanisms(id) ON DELETE RESTRICT,
>
> confidence NUMERIC(5,4),
>
> source VARCHAR(50), \-- ARO \| manual \| rule_engine
>
> assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> PRIMARY KEY (amr_gene_id, mechanism_id)
>
> );
>
> **SECTION 14 --- PHENOTYPE PREDICTION TABLES**

**14.1 Table: phenotype_predictions**

> CREATE TABLE phenotype_predictions (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> sample_id UUID NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
>
> job_id UUID REFERENCES analysis_jobs(id) ON DELETE SET NULL,
>
> antibiotic VARCHAR(200) NOT NULL,
>
> antibiotic_class VARCHAR(200),
>
> predicted_sir CHAR(1) NOT NULL, \-- S \| I \| R \| U (undetermined)
>
> confidence_score NUMERIC(5,4),
>
> confidence_tier VARCHAR(20) DEFAULT \'MEDIUM\',
>
> breakpoint_source VARCHAR(20) DEFAULT \'EUCAST\', \-- EUCAST \| CLSI
>
> breakpoint_version VARCHAR(20),
>
> interpretation_notes TEXT,
>
> is_not_testable BOOLEAN DEFAULT FALSE,
>
> created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> CONSTRAINT uq_phenotype UNIQUE (sample_id, antibiotic, breakpoint_source)
>
> );
>
> CREATE INDEX idx_pheno_sample ON phenotype_predictions (sample_id);
>
> CREATE INDEX idx_pheno_antibiotic ON phenotype_predictions (antibiotic);

**14.2 Table: prediction_evidence**

> CREATE TABLE prediction_evidence (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> prediction_id UUID NOT NULL REFERENCES phenotype_predictions(id) ON DELETE CASCADE,
>
> evidence_type VARCHAR(30) NOT NULL, \-- gene \| mutation \| mechanism
>
> evidence_id UUID NOT NULL, \-- FK to amr_genes, mutations, or mechanisms
>
> evidence_name VARCHAR(200),
>
> contribution_weight NUMERIC(5,4),
>
> notes TEXT
>
> );

**14.3 Table: prediction_rules**

> CREATE TABLE prediction_rules (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> rule_name VARCHAR(200) NOT NULL,
>
> rule_version VARCHAR(20) NOT NULL,
>
> antibiotic VARCHAR(200),
>
> antibiotic_class VARCHAR(200),
>
> organism_group VARCHAR(200),
>
> condition_json JSONB NOT NULL, \-- rule logic as JSON predicate
>
> predicted_sir CHAR(1),
>
> evidence_level SMALLINT,
>
> breakpoint_source VARCHAR(20),
>
> is_active BOOLEAN NOT NULL DEFAULT TRUE,
>
> created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );
>
> **SECTION 15 --- VIRULENCE TABLES**

**15.1 Table: virulence_factors**

> CREATE TABLE virulence_factors (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> sample_id UUID NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
>
> job_id UUID REFERENCES analysis_jobs(id) ON DELETE SET NULL,
>
> db_version_id UUID NOT NULL REFERENCES database_versions(id) ON DELETE RESTRICT,
>
> gene_name VARCHAR(200) NOT NULL,
>
> vf_id VARCHAR(50), \-- VFDB gene ID
>
> function_category VARCHAR(100),
>
> \-- toxin \| adhesin \| invasion \| immune_evasion \| siderophore \|
>
> \-- secretion_system \| capsule \| biofilm
>
> function_description TEXT,
>
> detection_tool VARCHAR(50) NOT NULL,
>
> identity_pct NUMERIC(6,3),
>
> coverage_pct NUMERIC(6,3),
>
> contig_id VARCHAR(200),
>
> contig_start INTEGER,
>
> contig_end INTEGER,
>
> confidence_score NUMERIC(5,4),
>
> detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );
>
> CREATE INDEX idx_vf_sample ON virulence_factors (sample_id);

**15.2 Table: virulence_annotations**

> CREATE TABLE virulence_annotations (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> vf_id UUID NOT NULL REFERENCES virulence_factors(id) ON DELETE CASCADE,
>
> source VARCHAR(50),
>
> key VARCHAR(100),
>
> value TEXT
>
> );
>
> **SECTION 16 --- CONFIDENCE SCORING TABLES**

**16.1 Table: confidence_scores**

> CREATE TABLE confidence_scores (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> sample_id UUID NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
>
> job_id UUID REFERENCES analysis_jobs(id) ON DELETE SET NULL,
>
> entity_type VARCHAR(50) NOT NULL, \-- amr_gene \| mutation \| phenotype \| virulence
>
> entity_id UUID NOT NULL,
>
> overall_score NUMERIC(5,4) NOT NULL,
>
> tier VARCHAR(20) NOT NULL, \-- HIGH \| MEDIUM \| LOW \| INSUFFICIENT
>
> computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );
>
> CREATE INDEX idx_conf_sample ON confidence_scores (sample_id, entity_type);

**16.2 Table: confidence_components**

> CREATE TABLE confidence_components (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> confidence_id UUID NOT NULL REFERENCES confidence_scores(id) ON DELETE CASCADE,
>
> component_name VARCHAR(100) NOT NULL,
>
> \-- identity_score \| coverage_score \| bit_score_norm \|
>
> \-- db_concordance \| mutation_evidence \| rule_strength
>
> raw_value NUMERIC(10,5),
>
> weight NUMERIC(5,4),
>
> weighted_score NUMERIC(5,4),
>
> notes TEXT
>
> );
>
> **SECTION 17 --- REPORTING TABLES**

**17.1 Table: reports**

> CREATE TABLE reports (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> sample_id UUID NOT NULL REFERENCES samples(id) ON DELETE RESTRICT,
>
> job_id UUID REFERENCES analysis_jobs(id) ON DELETE SET NULL,
>
> project_id UUID NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
>
> report_type VARCHAR(50) NOT NULL,
>
> \-- amr_summary \| phenotype_report \| virulence_report \| full_report \| module2_export
>
> report_format VARCHAR(20) NOT NULL, \-- JSON \| TSV \| PDF \| CSV
>
> schema_version VARCHAR(20) NOT NULL DEFAULT \'v1.0\',
>
> pipeline_version VARCHAR(30),
>
> status VARCHAR(20) NOT NULL DEFAULT \'GENERATING\',
>
> generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> expires_at TIMESTAMPTZ
>
> );

**17.2 Table: report_files**

> CREATE TABLE report_files (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
>
> storage_path VARCHAR(500) NOT NULL,
>
> file_size_bytes BIGINT,
>
> checksum_sha256 CHAR(64),
>
> created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );
>
> CREATE INDEX idx_report_files ON report_files (report_id);

**17.3 Table: module2_exports**

> CREATE TABLE module2_exports (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> sample_id UUID NOT NULL REFERENCES samples(id) ON DELETE RESTRICT,
>
> job_id UUID REFERENCES analysis_jobs(id) ON DELETE SET NULL,
>
> schema_version VARCHAR(20) NOT NULL DEFAULT \'v1.0\',
>
> storage_path VARCHAR(500) NOT NULL,
>
> row_count INTEGER,
>
> is_partial BOOLEAN NOT NULL DEFAULT FALSE,
>
> missing_fields JSONB,
>
> exported_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );
>
> **SECTION 18 --- AUDIT AND PROVENANCE TABLES**

**18.1 Table: audit_logs**

> CREATE TABLE audit_logs (
>
> id BIGSERIAL PRIMARY KEY,
>
> user_id UUID,
>
> project_id UUID,
>
> action VARCHAR(30) NOT NULL, \-- INSERT \| UPDATE \| DELETE \| LOGIN \| EXPORT
>
> table_name VARCHAR(100),
>
> record_id UUID,
>
> before_state JSONB,
>
> after_state JSONB,
>
> ip_address INET,
>
> user_agent TEXT,
>
> request_id UUID,
>
> occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> ) PARTITION BY RANGE (occurred_at);
>
> CREATE INDEX idx_audit_user ON audit_logs (user_id, occurred_at);
>
> CREATE INDEX idx_audit_record ON audit_logs (table_name, record_id);

**18.2 Table: data_lineage**

> CREATE TABLE data_lineage (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> entity_type VARCHAR(50) NOT NULL,
>
> entity_id UUID NOT NULL,
>
> parent_type VARCHAR(50),
>
> parent_id UUID,
>
> workflow_run_id UUID REFERENCES workflow_runs(id) ON DELETE SET NULL,
>
> db_version_id UUID REFERENCES database_versions(id) ON DELETE SET NULL,
>
> pipeline_version VARCHAR(30),
>
> step_name VARCHAR(100),
>
> recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );
>
> CREATE INDEX idx_lineage_entity ON data_lineage (entity_type, entity_id);

**18.3 Table: change_history**

> CREATE TABLE change_history (
>
> id BIGSERIAL PRIMARY KEY,
>
> table_name VARCHAR(100) NOT NULL,
>
> record_id UUID NOT NULL,
>
> field_name VARCHAR(100) NOT NULL,
>
> old_value TEXT,
>
> new_value TEXT,
>
> changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
>
> changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> ) PARTITION BY RANGE (changed_at);
>
> CREATE INDEX idx_chg_record ON change_history (table_name, record_id);
>
> **SECTION 19 --- INDEXING STRATEGY**

**19.1 Index Design Matrix**

  ----------------------- ---------------------------- ------------------ ------------------------------------------------------------------------------- ---------------------------------------------------
  **Table**               **Index Name**               **Type**           **Columns**                                                                     **Rationale**

  samples                 idx_samples_project_status   B-tree (partial)   (project_id, status) WHERE deleted_at IS NULL                                   Project dashboard queries; job queue filtering

  samples                 idx_samples_species          B-tree             (species)                                                                       Species-based filtering in surveillance queries

  amr_genes               idx_amr_genes_sample_gene    B-tree             (sample_id, gene_name)                                                          Per-sample gene lookup; most common query pattern

  amr_genes               idx_amr_genes_aro            B-tree             (aro_accession)                                                                 ARO-based cross-sample surveillance queries

  amr_hits                idx_amr_hits_tool_cat        B-tree             (detection_tool, hit_category)                                                  Filtering by tool and hit stringency

  mutations               idx_mutations_gene_pos       B-tree             (gene_name, position)                                                           Mutation catalogue lookups by gene+position

  phenotype_predictions   idx_pheno_sir                B-tree             (sample_id, predicted_sir)                                                      Resistance phenotype summaries

  analysis_jobs           idx_jobs_queue               B-tree (partial)   (status, priority, submitted_at) WHERE status IN (\'QUEUED\',\'RUNNING\')       Celery worker queue polling --- must be fast

  audit_logs              idx_audit_user_time          B-tree             (user_id, occurred_at DESC)                                                     User activity auditing

  samples                 idx_samples_fts              GIN                to_tsvector(\'english\', isolate_name \|\| \' \' \|\| COALESCE(species,\'\'))   Full-text search across sample names

  amr_genes               idx_amr_genes_meta           GIN                (drug_class gin_trgm_ops)                                                       Trigram search on drug class strings

  workflow_steps          idx_wf_steps_run             B-tree             (workflow_run_id, status)                                                       Workflow progress monitoring

  confidence_scores       idx_conf_entity              B-tree             (entity_type, entity_id)                                                        Entity-level confidence lookup
  ----------------------- ---------------------------- ------------------ ------------------------------------------------------------------------------- ---------------------------------------------------

> **GIN Index:** GIN indexes on JSONB columns (validation_warnings, analysis_config, raw_result_json) are added only for columns with frequent key-based queries, not all JSONB columns. Blanket GIN indexing on all JSONB degrades write performance.
>
> **SECTION 20 --- PARTITIONING STRATEGY**

**20.1 Partition Design**

  -------------------------------- -------------- ------------------------ ----------------------- ------------------------------------
  **Table**                        **Strategy**   **Key**                  **Partition Size**      **Trigger**

  audit_logs                       RANGE          occurred_at              Monthly                 Day 1 of each month via pg_partman

  change_history                   RANGE          changed_at               Monthly                 pg_partman automated

  task_logs                        RANGE          logged_at                Monthly                 pg_partman automated

  samples (future)                 HASH           project_id               16 buckets              Trigger: \> 5M rows

  amr_genes (future)               HASH           sample_id                16 buckets              Trigger: \> 50M rows

  phenotype_predictions (future)   RANGE + HASH   created_at + sample_id   Quarterly / 8 buckets   Trigger: \> 20M rows
  -------------------------------- -------------- ------------------------ ----------------------- ------------------------------------

**20.2 Archiving Strategy**

> \-- Partition detach and archive (example for audit_logs):
>
> ALTER TABLE audit_logs DETACH PARTITION audit_logs_2024_01;
>
> \-- Partition exported to cold storage (pg_dump) then dropped:
>
> pg_dump -t audit_logs_2024_01 amr_platform \> audit_2024_01_archive.dump
>
> DROP TABLE audit_logs_2024_01;

-   pg_partman extension manages automated partition creation and detachment.

-   Active partitions retained per domain retention policy (Section 21).

-   Detached partitions archived to MinIO Glacier tier before DROP.

> **SECTION 21 --- DATA RETENTION STRATEGY**

  ------------------------------- ---------------------- ------------------------------------ ----------------------------------------- -------------------------------------------------------------
  **Data Type**                   **Active Retention**   **Archive Retention**                **Purge Policy**                          **Notes**

  Genome FASTA files              12 months              Cold storage 7 years                 Purged after cold archive verified        S3 lifecycle rules; not DB-managed

  Intermediate workflow files     7 days                 Not archived                         Auto-purged by cleanup cron               Nextflow work dir only

  AMR gene / mutation results     12 months active       7 years archive (JSONB snapshot)     Soft-delete then archive export           Clinical traceability requirement

  Phenotype prediction results    12 months active       7 years archive                      Same as AMR results                       Tied to clinical reports

  PDF / clinical reports          Indefinite             N/A                                  Manual deletion with audit trail          NEVER auto-purged; regulatory requirement

  Audit logs                      Indefinite             Partition to cold store \> 2 years   NEVER deleted                             10 year minimum regulatory requirement

  Reference DB versions           Indefinite             N/A                                  Deprecated but never deleted              Scientific reproducibility --- results point to version IDs

  Sessions / JWT refresh tokens   7 days                 Not retained                         Auto-expired by TTL + nightly purge job   Security; not clinical data

  Task / workflow logs            30 days                Partition archived 12 months         Purged after archive                      Operational telemetry only
  ------------------------------- ---------------------- ------------------------------------ ----------------------------------------- -------------------------------------------------------------

> **SECTION 22 --- BACKUP AND RECOVERY**

**22.1 Backup Strategy**

  ------------------------------ ------------------------------------ ---------------------------------- --------------- ---------------------
  **Backup Type**                **Frequency**                        **Tool**                           **Retention**   **Storage**

  Full base backup               Weekly (Sunday 02:00 UTC)            pg_basebackup                      4 weeks         MinIO / off-site S3

  Incremental WAL archive        Continuous (streaming)               PostgreSQL WAL archiving to S3     14 days         MinIO + off-site

  Logical dump (schema + data)   Daily (03:00 UTC)                    pg_dump \--format=custom           30 days         MinIO

  Hot standby replication        Continuous (streaming replication)   PostgreSQL streaming replication   Live            Secondary DB server
  ------------------------------ ------------------------------------ ---------------------------------- --------------- ---------------------

**22.2 Point-in-Time Recovery (PITR)**

> \-- Restore to specific time using base backup + WAL replay:
>
> recovery_target_time = \'2025-06-01 14:30:00+00\'
>
> restore_command = \'aws s3 cp s3://amr-wal-archive/%f %p\'
>
> recovery_target_action = \'promote\'

-   RTO (Recovery Time Objective): \< 4 hours for full instance recovery.

-   RPO (Recovery Point Objective): \< 5 minutes (continuous WAL archiving).

-   Quarterly DR drills: restore to staging from backup and validate data integrity.

**22.3 Failover Strategy**

-   Patroni cluster manager with ZooKeeper/etcd for automatic leader election.

-   HAProxy load balancer routes read traffic to replicas; write traffic to primary only.

-   Automatic failover: if primary unavailable \> 30 seconds, Patroni promotes replica; DNS updated.

-   Manual failover for planned maintenance: pg_ctl promote on standby + update connection strings.

> **SECTION 23 --- SQLALCHEMY DESIGN**

**23.1 Base and Mixins**

> \# base.py
>
> from sqlalchemy.orm import DeclarativeBase, declared_attr
>
> from sqlalchemy import Column, DateTime, Boolean, text
>
> from sqlalchemy.dialects.postgresql import UUID
>
> from datetime import datetime, timezone
>
> from uuid import uuid4
>
> class Base(DeclarativeBase):
>
> pass
>
> class TimestampMixin:
>
> created_at = Column(DateTime(timezone=True),
>
> nullable=False, default=lambda: datetime.now(timezone.utc))
>
> updated_at = Column(DateTime(timezone=True),
>
> nullable=False, default=lambda: datetime.now(timezone.utc),
>
> onupdate=lambda: datetime.now(timezone.utc))
>
> class SoftDeleteMixin:
>
> deleted_at = Column(DateTime(timezone=True), nullable=True, default=None)
>
> \@property
>
> def is_deleted(self) -\> bool:
>
> return self.deleted_at is not None
>
> def soft_delete(self):
>
> self.deleted_at = datetime.now(timezone.utc)
>
> class AuditMixin:
>
> \"\"\"Attach to models that need automatic audit log entries.\"\"\"
>
> \@declared_attr
>
> def \_\_mapper_args\_\_(cls):
>
> return {}
>
> \# Implement via SQLAlchemy event listeners in audit.py:
>
> \# \@event.listens_for(Session, \"after_flush\")
>
> \# def receive_after_flush(session, flush_context): \...

**23.2 Sample Model Example**

> from sqlalchemy import Column, String, Date, ForeignKey, Enum
>
> from sqlalchemy.dialects.postgresql import UUID
>
> from sqlalchemy.orm import relationship
>
> from .base import Base, TimestampMixin, SoftDeleteMixin, AuditMixin
>
> class Sample(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
>
> \_\_tablename\_\_ = \"samples\"
>
> id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
>
> project_id = Column(UUID(as_uuid=True), ForeignKey(\"projects.id\"), nullable=False)
>
> isolate_name = Column(String(200), nullable=False)
>
> species = Column(String(200))
>
> species_taxid = Column(Integer)
>
> host = Column(String(100))
>
> collection_date = Column(Date)
>
> source_type = Column(String(100))
>
> location = Column(String(200))
>
> country_code = Column(String(3))
>
> submitter_id = Column(UUID(as_uuid=True), ForeignKey(\"users.id\"))
>
> status = Column(String(30), nullable=False, default=\"UPLOADED\")
>
> project = relationship(\"Project\", back_populates=\"samples\")
>
> submitter = relationship(\"User\", foreign_keys=\[submitter_id\])
>
> assembly = relationship(\"Assembly\", uselist=False, back_populates=\"sample\",
>
> cascade=\"all, delete-orphan\")
>
> analysis_jobs = relationship(\"AnalysisJob\", back_populates=\"sample\")
>
> amr_genes = relationship(\"AMRGene\", back_populates=\"sample\",
>
> cascade=\"all, delete-orphan\")
>
> mutations = relationship(\"Mutation\", back_populates=\"sample\",
>
> cascade=\"all, delete-orphan\")
>
> predictions = relationship(\"PhenotypePrediction\", back_populates=\"sample\",
>
> cascade=\"all, delete-orphan\")
>
> virulence_factors = relationship(\"VirulenceFactor\", back_populates=\"sample\",
>
> cascade=\"all, delete-orphan\")
>
> **SECTION 24 --- ALEMBIC DESIGN**

**24.1 Migration Strategy**

  ---------------------- ----------------------------------------------------------------------------------------------
  **Rule**               **Detail**

  Naming convention      YYYY_MM_DD_HHMM_short_description.py --- e.g. 2025_06_01_0900_create_users_table.py

  Revision chaining      Every migration specifies down_revision; no orphaned heads; checked in CI

  Rollback requirement   Every upgrade() has a complete downgrade() --- tested in CI against staging DB

  Data migrations        Separate from schema migrations; data scripts in alembic/data/ run as one-off tasks

  Zero-downtime          Additive changes first (add nullable column); backfill data; add NOT NULL in third migration

  Test before deploy     Migrations run against a copy of production schema in CI; diff validated before merge

  Version tagging        git tag alembic/{revision_id} at every release; maps revision to application version
  ---------------------- ----------------------------------------------------------------------------------------------

**24.2 Migration File Structure**

> alembic/
>
> ├── env.py \# SQLAlchemy engine setup, include_object filter
>
> ├── script.py.mako \# Migration template
>
> ├── versions/
>
> │ ├── 2025_06_01_0900_create_core_tables.py
>
> │ ├── 2025_06_10_1400_add_amr_result_tables.py
>
> │ ├── 2025_06_20_0900_add_phenotype_tables.py
>
> │ └── 2025_07_01_1000_add_module2_reserved_tables.py
>
> └── data/

**24.3 Deployment Workflow**

> \# 1. Generate migration after model changes:
>
> alembic revision \--autogenerate -m \"add_virulence_function_category\"
>
> \# 2. Review generated script; ensure downgrade() is complete
>
> \# 3. Test against staging:
>
> alembic -x db=staging upgrade head
>
> alembic -x db=staging downgrade -1
>
> alembic -x db=staging upgrade head
>
> \# 4. Production deploy (run before app startup):
>
> alembic upgrade head
>
> \# 5. Rollback if needed: alembic downgrade {previous_revision}
>
> **SECTION 25 --- FINAL DELIVERABLES AND RECOMMENDATIONS**

**25.1 Module 2 and Module 3 Reserved Tables**

**Module 2 --- Genotype--Phenotype Concordance (Schema Reserved)**

> CREATE TABLE gp_concordance_studies (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> project_id UUID NOT NULL REFERENCES projects(id) ON DELETE RESTRICT,
>
> name VARCHAR(200),
>
> created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );
>
> CREATE TABLE gp_concordance_results (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> study_id UUID NOT NULL REFERENCES gp_concordance_studies(id) ON DELETE CASCADE,
>
> sample_id UUID NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
>
> module1_export_id UUID REFERENCES module2_exports(id) ON DELETE SET NULL,
>
> antibiotic VARCHAR(200),
>
> genotypic_sir CHAR(1), \-- from Module 1
>
> phenotypic_mic NUMERIC(8,4),
>
> phenotypic_sir CHAR(1), \-- from wet-lab
>
> concordant BOOLEAN,
>
> discordance_type VARCHAR(50), \-- VME \| ME \| acceptable
>
> created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );

**Module 3 --- Mobile Genetic Element Origin (Schema Reserved)**

> CREATE TABLE mge_elements (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> sample_id UUID NOT NULL REFERENCES samples(id) ON DELETE CASCADE,
>
> amr_gene_id UUID REFERENCES amr_genes(id) ON DELETE SET NULL,
>
> mge_type VARCHAR(50), \-- plasmid \| transposon \| integron \| phage \| ICE
>
> replicon_type VARCHAR(100),
>
> mob_type VARCHAR(100),
>
> contig_id VARCHAR(200),
>
> contig_start INTEGER,
>
> contig_end INTEGER,
>
> db_version_id UUID REFERENCES database_versions(id) ON DELETE RESTRICT,
>
> confidence_score NUMERIC(5,4),
>
> detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
>
> );

**25.2 Scalability Recommendations**

  ---------------------- ---------------------------------------------------------------------------------------- -------------------------------------------------
  **Scale Point**        **Recommendation**                                                                       **Trigger**

  Read scaling           Add PostgreSQL read replicas; route all SELECT queries from reporting layer to replica   \> 10,000 samples or dashboard latency \> 500ms

  Write scaling          PgBouncer connection pooling (transaction mode); pool size per service tier              \> 100 concurrent analyses

  Table growth           Activate hash partitioning on samples and amr_genes                                      \> 5M sample rows

  Search performance     Deploy Elasticsearch index for cross-project AMR gene surveillance searches              \> 1M amr_gene rows with FTS requirements

  TimeSeries analytics   Add TimescaleDB extension for time-based surveillance rollup queries                     Surveillance module activation

  Cross-region DR        Logical replication to geographically separate PostgreSQL instance                       Clinical deployment with SLA requirements
  ---------------------- ---------------------------------------------------------------------------------------- -------------------------------------------------

**25.3 Security Recommendations**

  --------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Control**           **Implementation**

  PostgreSQL RLS        Enable Row Level Security on samples, amr_genes, reports: CREATE POLICY p_project_iso ON samples USING (project_id = current_setting(\'app.project_id\')::uuid)

  Service DB users      Separate PostgreSQL role per service (api_user, celery_user, readonly_user); minimum required privileges only

  Encrypted columns     pgcrypto for mfa_secret and api token hashes; sensitive PII fields encrypted at application layer with per-project keys

  Connection security   sslmode=require for all connections; certificate verification in production; no plaintext DB connections allowed

  Query audit           pgaudit extension logs all DDL and privileged DML; logs shipped to SIEM

  Backup encryption     pg_dump output encrypted with GPG before S3 upload; keys managed in Vault
  --------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------

**25.4 Performance Recommendations**

-   Set work_mem = 64MB for analysis queries; local_preload_libraries = pg_stat_statements for query performance tracking.

-   VACUUM and ANALYZE scheduled nightly; autovacuum tuned for high-write analysis_jobs and amr_hits tables.

-   Use EXPLAIN ANALYZE on all new queries in development; target query plans with index scans, not sequential scans, for tables \> 10,000 rows.

-   JSONB columns: use jsonb_path_ops GIN operator class for containment queries (@\>); avoid jsonb_ops unless key-existence queries needed.

-   Materialised views for surveillance rollups: refresh nightly; partial refresh using REFRESH MATERIALIZED VIEW CONCURRENTLY.

-   Prepared statements via SQLAlchemy compiled cache; parameterised queries enforced --- no string interpolation in SQL.

**25.5 Complete Table Inventory**

  -------- ----------------------------- --------------------- -------------
  **\#**   **Table**                     **Domain**            **Module**

  1        users                         User                  1/2/3

  2        roles                         User                  1/2/3

  3        permissions                   User                  1/2/3

  4        user_roles                    User                  1/2/3

  5        sessions                      User                  1/2/3

  6        api_tokens                    User                  1/2/3

  7        projects                      Project               1/2/3

  8        project_members               Project               1/2/3

  9        project_settings              Project               1/2/3

  10       samples                       Sample                1/2/3

  11       sample_metadata               Sample                1/2/3

  12       sample_files                  Sample                1/2/3

  13       assemblies                    Sample                1

  14       assembly_metrics              Sample                1

  15       validation_reports            Sample                1

  16       reference_databases           Reference             1/2/3

  17       database_versions             Reference             1/2/3

  18       database_checksums            Reference             1/2/3

  19       analysis_jobs                 Workflow              1/2/3

  20       workflow_runs                 Workflow              1/2/3

  21       workflow_steps                Workflow              1/2/3

  22       task_logs                     Workflow              1/2/3

  23       amr_genes                     Analysis              1

  24       amr_hits                      Analysis              1

  25       amr_annotations               Analysis              1

  26       alignment_results             Analysis              1

  27       blast_statistics              Analysis              1

  28       mutations                     Analysis              1

  29       mutation_annotations          Analysis              1

  30       mutation_evidence             Analysis              1

  31       mechanism_classes             Analysis              1

  32       mechanisms                    Analysis              1

  33       gene_mechanisms               Analysis              1

  34       phenotype_predictions         Analysis              1

  35       prediction_evidence           Analysis              1

  36       prediction_rules              Analysis              1

  37       virulence_factors             Analysis              1

  38       virulence_annotations         Analysis              1

  39       confidence_scores             Analysis              1

  40       confidence_components         Analysis              1

  41       reports                       Reporting             1/2/3

  42       report_files                  Reporting             1/2/3

  43       module2_exports               Reporting             1

  44       audit_logs                    Audit                 1/2/3

  45       change_history                Audit                 1/2/3

  46       data_lineage                  Audit                 1/2/3

  47       gp_concordance_studies        Module 2 Reserved     2

  48       gp_concordance_results        Module 2 Reserved     2

  49       mge_elements                  Module 3 Reserved     3
  -------- ----------------------------- --------------------- -------------
# 01 — System Architecture and Foundation Specification

**SOFTWARE ARCHITECTURE SPECIFICATION**

**TECHNICAL DESIGN DOCUMENT**

**MODULE 1 --- ANTIMICROBIAL RESISTANCE**

**CHARACTERISATION ENGINE**

*Production-Grade Bioinformatics Platform*

Version 1.0 \| Confidential

> **SECTION 1 --- PROJECT OVERVIEW**

**1.1 Biological Objective**

Module 1 is designed to characterise antimicrobial resistance (AMR) determinants within assembled bacterial genomes. The biological objective is to comprehensively inventory resistance genes, resistance-conferring point mutations, mobile genetic elements carrying AMR cargo, and virulence factors, then integrate these findings into actionable phenotypic predictions (Susceptible / Intermediate / Resistant) for clinical and epidemiological interpretation.

The engine targets whole-genome sequence (WGS) data from bacterial isolates spanning Gram-positive and Gram-negative species, with priority attention to ESKAPE pathogens (Enterococcus faecium, Staphylococcus aureus, Klebsiella pneumoniae, Acinetobacter baumannii, Pseudomonas aeruginosa, Enterobacter spp.) and NIAID priority pathogens listed under the WHO Critical and High priority tiers.

**1.2 Computational Objective**

The computational objective is to build a scalable, reproducible, and auditable bioinformatics pipeline that:

-   Accepts assembled FASTA genomes (single isolate or batch) as primary input.

-   Screens input sequences against curated AMR reference databases (CARD, NCBI AMRFinderPlus, ResFinder, Abricate) using Smith-Waterman and BWT-based alignment strategies.

-   Detects chromosomal and plasmid-encoded resistance genes with identity/coverage thresholds configurable per clinical context.

-   Identifies known resistance-conferring point mutations from curated mutation catalogues.

-   Classifies identified determinants into resistance mechanism categories: beta-lactamase production, efflux pump overexpression, target site modification, enzyme inactivation, and outer membrane permeability alterations.

-   Generates phenotype predictions mapped to EUCAST and CLSI breakpoints.

-   Assigns confidence scores reflecting alignment quality, database concordance, and epidemiological support.

-   Exports a structured Module 2 input dataset (module2_input.csv) for downstream genotype--phenotype concordance analysis.

**1.3 Expected Users**

  ------------------------- -------------------------------------------------------------------- ---------------------------------
  **User Role**             **Use Case**                                                         **Typical Volume**

  Clinical Microbiologist   Characterise AMR profile of patient isolates to guide therapy        Single to tens per day

  Public Health Analyst     Surveillance screening of community and hospital-acquired isolates   Hundreds to thousands per batch

  Research Scientist        Comparative AMR genomics across isolate collections                  Large project batches

  Bioinformatics Engineer   Pipeline maintenance, validation, and QC                             Development and CI workflows

  Laboratory Director       Report review and sign-off for clinical reporting                    Review-level access
  ------------------------- -------------------------------------------------------------------- ---------------------------------

**1.4 Scope**

Module 1 is explicitly scoped to:

-   FASTA input processing (assembled genome or consensus sequence).

-   AMR gene detection using BLAST-based and sequence-alignment methods.

-   Chromosomal point mutation detection via reference-based comparison.

-   Resistance mechanism classification using rule-based and ML-augmented engines.

-   Phenotype prediction with S/I/R classifications per antibiotic class.

-   Virulence factor profiling using VFDB and VirulenceFinder.

-   Confidence scoring and structured output generation.

-   Export of structured data for Module 2 integration.

**1.5 Out-of-Scope**

-   Raw reads assembly (no de novo assembly within Module 1).

-   Short-read or long-read basecalling (upstream of this platform).

-   Transmission cluster analysis (Module 3 scope).

-   Mobile genetic element origin tracing (Module 3 scope).

-   Phenotypic MIC data management (clinical LIMS scope).

-   MLST typing, serotyping (future module scope).

**1.6 Future Integration with Modules 2 and 3**

Module 1 is architected as the upstream provider for the downstream analytical modules:

  ----------------------- --------------------------------------------------------------------- ----------------------------------------------------
  **Integration Point**   **Module 2 (Genotype--Phenotype Concordance)**                        **Module 3 (MGE Origin Tracing)**

  Primary Input           module2_input.csv from Module 1 Export Service                        AMR gene coordinates and contig IDs from Module 1

  Key Fields              Gene name, mechanism, predicted S/I/R, confidence                     Contig sequence, gene location, replicon typing

  Dependency              All Module 1 services must complete before Module 2 executes          Operates in parallel after AMR Detection completes

  Versioning              Schema versioned; Module 1 output schema is contract-locked at v1.0   Gene coordinate schema versioned separately
  ----------------------- --------------------------------------------------------------------- ----------------------------------------------------

> **SECTION 2 --- SYSTEM VISION**

**2.1 Input Specification**

The platform accepts the following primary input formats:

-   Assembled bacterial genome FASTA --- single contig or multi-contig assembly output from SPAdes, Unicycler, Flye, or equivalent assemblers.

-   Consensus genome FASTA --- generated from variant calling pipelines or reference-guided assembly.

> **Constraint:** Raw FASTQ input is explicitly out-of-scope. Users must assemble reads prior to submission. This boundary ensures platform reproducibility and reduces compute overhead for core AMR characterisation.

**2.2 Platform Outputs**

  ------------------------------- ---------------- ------------------------------------------------------------------------------------------------------------------------------
  **Output Artefact**             **Format**       **Description**

  AMR Gene Inventory              JSON, TSV        Complete list of detected resistance genes with gene name, database source, identity%, coverage%, and coordinates

  Resistance Mutation Inventory   JSON, TSV        Point mutations in housekeeping and resistance genes with amino acid change and clinical significance

  Mechanism Classification        JSON, TSV        Assignment of each determinant to resistance mechanism category (beta-lactamase, efflux, target modification, etc.)

  Phenotype Prediction            JSON, TSV, PDF   S/I/R predictions per antibiotic with clinical breakpoint source (EUCAST/CLSI) and confidence score

  Virulence Factor Profile        JSON, TSV        Virulence gene inventory from VFDB and VirulenceFinder with function annotations

  Confidence Scores               Embedded JSON    Per-gene and per-prediction confidence values based on alignment quality, database concordance, and clinical evidence weight

  Module 2 Export                 CSV              Structured genotype--phenotype linkage table for downstream Module 2 analysis

  Summary PDF Report              PDF              Human-readable clinical or surveillance summary report
  ------------------------------- ---------------- ------------------------------------------------------------------------------------------------------------------------------

**2.3 Complete Sample Lifecycle**

**Phase 1 --- Upload and Registration**

-   User uploads assembled_genome.fasta via REST API or web interface.

-   File is checksummed (SHA-256), stored in object storage, and a sample_id (UUID) is assigned.

-   Upload metadata (filename, size, upload timestamp, user_id, project_id) is persisted to PostgreSQL.

-   A job record is created with status = QUEUED and dispatched to the Celery job queue via Redis.

**Phase 2 --- Genome Validation**

-   Genome Validation Service pulls the FASTA from storage and validates: valid nucleotide characters, minimum assembly size (configurable, default ≥ 200 kbp), maximum contig count, N50 threshold.

-   Assembly metrics (total length, contig count, N50, GC%) are computed and stored.

-   Species prediction is attempted using Mash/Kraken2 sketch to assign expected taxonomy.

-   Validation failures terminate the job with status = FAILED and structured error report.

**Phase 3 --- Parallel AMR and Virulence Screening**

-   Nextflow DSL2 launches AMR Detection and Virulence Profiling services in parallel.

-   AMR Detection runs CARD RGI, AMRFinderPlus, ResFinder, and Abricate against the validated genome.

-   Results are merged, deduplicated, and written to the amr_genes table.

**Phase 4 --- Mutation Detection**

-   Mutation Detection Service aligns the genome against species-specific reference sequences using Needleman-Wunsch for full-length gene alignments.

-   Detected mutations are cross-referenced against the resistance mutation catalogue.

-   Confirmed resistance mutations are written to the resistance_mutations table.

**Phase 5 --- Mechanism Classification**

-   Mechanism Classification Service assigns each AMR gene and mutation to a resistance mechanism category using a rule engine backed by CARD ARO ontology.

**Phase 6 --- Phenotype Prediction**

-   Rule engine maps mechanism + gene/mutation combinations to S/I/R predictions per antibiotic class.

-   EUCAST and CLSI breakpoint tables are queried for clinical interpretation context.

-   Predictions with confidence scores are written to the phenotype_predictions table.

**Phase 7 --- Confidence Scoring**

-   Confidence Scoring Service aggregates alignment quality metrics, database concordance scores, and epidemiological evidence weights into a per-finding confidence score (0.0--1.0).

**Phase 8 --- Module 2 Export**

-   Export Service compiles module2_input.csv with standardised schema fields for downstream concordance analysis.

**Phase 9 --- Report Generation**

-   Reporting Service generates JSON, TSV, and PDF outputs and stores them in result storage.

-   Job status is updated to COMPLETED; user is notified via webhook or email.

> **SECTION 3 --- HIGH LEVEL SYSTEM ARCHITECTURE**

**3.1 Architecture Diagram**

> ┌─────────────────────────────────────────────────────────────┐
>
> │ USER LAYER │
>
> │ Web UI / CLI Client / REST API Consumer / Batch Uploader │
>
> └─────────────────────────┬───────────────────────────────────┘
>
> │ HTTPS / WebSocket
>
> ┌─────────────────────────▼───────────────────────────────────┐
>
> │ API LAYER │
>
> │ FastAPI Gateway │ JWT Auth │ Rate Limiting │ Audit │
>
> │ /api/v1/samples │ /jobs │ /reports │ /admin │
>
> └─────────┬─────────────────────────────────────┬─────────────┘
>
> │ Celery Tasks │ WebSocket
>
> ┌─────────▼────────────────────────┐ ┌─────────▼─────────────┐
>
> │ JOB MANAGEMENT LAYER │ │ NOTIFICATION LAYER │
>
> │ Celery Workers │ Redis Queue │ │ Progress Events │
>
> │ Job States │ Retry Policies │ │ Completion Webhooks │
>
> └─────────┬────────────────────────┘ └───────────────────────┘
>
> │ Nextflow Execution
>
> ┌─────────▼──────────────────────────────────────────────────┐
>
> │ WORKFLOW LAYER │
>
> │ Nextflow DSL2 Orchestration │
>
> │ validate → align → amr_detect → mutate → classify │
>
> │ → phenotype → virulence → score → export │
>
> └──┬───────────────────────────────────────────────────┬─────┘
>
> │ Docker containers │
>
> ┌──▼───────────────────────────────────────────────────▼─────┐
>
> │ ANALYSIS LAYER │
>
> │ GenomeValidation │ AlignmentSvc │ AMRDetection │
>
> │ MutationDetect │ MechClassify │ PhenotypePrediction │
>
> │ VirulenceProfil │ ConfidenceSvc │ Module2Export │
>
> └──┬───────────────────────────────────────────────────┬─────┘
>
> │ SQLAlchemy ORM │ Files
>
> ┌──▼─────────────────────┐ ┌───────────────────────────▼────┐
>
> │ DATABASE LAYER │ │ FILE STORAGE LAYER │
>
> │ PostgreSQL (primary) │ │ MinIO / S3 Object Storage │
>
> │ Redis (cache/queue) │ │ Genome FASTA, Result Files │
>
> └─────────────────────────┘ └────────────────────────────────┘
>
> │
>
> ┌─────────────────────────▼───────────────────────────────────┐
>
> │ REPORTING LAYER │
>
> │ JSON Serialiser │ TSV Writer │ PDF Generator │ Dashboards │
>
> └─────────────────────────────────────────────────────────────┘

**3.2 Layer Responsibilities**

**User Layer**

Provides all external interfaces: a web UI for interactive use, a CLI tool for batch submission, and REST API consumers for laboratory information system (LIS) integration. Users authenticate via JWT tokens issued by the API Layer.

**API Layer**

FastAPI gateway handles all HTTP ingress. Responsibilities include: request validation, JWT authentication, RBAC authorisation, rate limiting per user/project, audit logging, and routing to appropriate service handlers. Exposes versioned endpoints under /api/v1/.

**Job Management Layer**

Celery workers manage asynchronous job execution backed by Redis as the message broker. The layer governs job lifecycle state transitions (QUEUED → RUNNING → COMPLETED / FAILED / CANCELLED), retry policies with exponential back-off, and progress event publication.

**Workflow Layer**

Nextflow DSL2 orchestrates the sequence of bioinformatics services. It manages channel-based data flow between processes, resource allocation (CPU/memory per process), container execution, checkpointing, and restart from failure points.

**Analysis Layer**

Nine microservices implement the bioinformatics logic: Genome Validation, Alignment, AMR Detection, Mutation Detection, Mechanism Classification, Phenotype Prediction, Virulence Profiling, Confidence Scoring, and Module 2 Export. Each service is containerised and independently deployable.

**Database Layer**

PostgreSQL stores all structured data: sample metadata, job records, AMR findings, mutations, phenotype predictions, virulence profiles, confidence scores, and audit logs. Redis serves as message broker, job status cache, and session store.

**File Storage Layer**

MinIO-compatible S3 object storage holds: uploaded FASTA files, intermediate analysis files, result TSV/JSON files, and PDF reports. Files are addressed by sample_id-namespaced paths.

**Reporting Layer**

Generates final output artefacts: structured JSON/TSV data files, PDF summary reports, and future dashboard-ready data feeds.

> **SECTION 4 --- MICROSERVICE ARCHITECTURE**

**Service 1 --- Genome Validation Service**

  ----------------------- -----------------------------------------------------------------------------------------------------------------------------------------
  **Attribute**           **Detail**

  Purpose                 Validate uploaded FASTA files; compute assembly quality metrics; predict taxonomy

  Input                   Raw FASTA file path; sample_id; validation_config JSON (thresholds)

  Output                  validation_result.json {status, metrics: {total_length, contig_count, N50, GC_pct, max_contig, min_contig}, species_prediction}

  Dependencies            BioPython (parsing), Mash / Kraken2 (species sketch), QUAST (assembly metrics)

  API Interactions        POST /api/v1/internal/validate --- called by Job Manager on job start

  Database Interactions   INSERT INTO samples (validation_status, assembly_metrics) ON CONFLICT UPDATE

  Error Handling          FASTA parse error → FAILED; below-threshold assembly → FAILED with threshold report; taxonomy mismatch warning → WARNING (non-blocking)

  Scalability             Stateless; horizontally scalable; typical runtime \< 2 minutes for 5 Mbp assembly
  ----------------------- -----------------------------------------------------------------------------------------------------------------------------------------

**Service 2 --- Alignment Service**

  ----------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Attribute**           **Detail**

  Purpose                 Provide reusable pairwise alignment (Smith-Waterman for local, Needleman-Wunsch for global) and BWT-based whole-genome alignment supporting all downstream detection services

  Input                   query_fasta, reference_fasta, alignment_mode (local\|global\|bwt), scoring_params JSON

  Output                  alignment_result.json {alignments\[\], metrics: {identity_pct, coverage_pct, score, gaps, mismatches}}; BAM/PAF file where applicable

  Dependencies            BWA-MEM2, minimap2, custom Smith-Waterman (C extension via ctypes), BioPython pairwise2

  API Interactions        Internal library --- called by AMR Detection, Mutation Detection, and Virulence Profiling services

  Database Interactions   Alignment metrics cached in Redis (key: query_hash:ref_hash:mode, TTL 24h)

  Error Handling          Empty alignment → returns empty result with low confidence flag; reference not found → FAILED with error code ALIGN_REF_MISSING

  Scalability             CPU-bound; Nextflow allocates 4--8 CPUs per alignment process; BWT index pre-built and cached
  ----------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**Service 3 --- AMR Detection Service**

  ----------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Attribute**           **Detail**

  Purpose                 Screen genome against multiple AMR databases to produce a comprehensive, deduplicated AMR gene inventory

  Input                   validated_genome.fasta; sample_id; detection_config (identity_threshold, coverage_threshold, tool_flags)

  Output                  amr_detection_results.json: {genes: \[{gene_name, database, identity_pct, coverage_pct, contig_id, start, end, strand, drug_class, mechanism}\]}

  Dependencies            CARD RGI (≥6.0), NCBI AMRFinderPlus (≥3.11), ResFinder (≥4.1), Abricate (≥1.0), custom result merger

  API Interactions        POST /api/v1/internal/amr-detect; result pushed to job status stream

  Database Interactions   INSERT INTO amr_genes (sample_id, gene_name, database_source, identity_pct, coverage_pct, coordinates)

  Error Handling          Database timeout → retry with exponential back-off (max 3); tool execution failure → PARTIAL result with failed tool flagged; deduplication conflict → highest-identity hit wins

  Scalability             Parallelised per tool in Nextflow; CARD RGI is most CPU-intensive (8 CPUs, 16 GB RAM recommended for large genomes)
  ----------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**Service 4 --- Mutation Detection Service**

  ----------------------- ----------------------------------------------------------------------------------------------------------------------------------------------
  **Attribute**           **Detail**

  Purpose                 Identify resistance-conferring point mutations in chromosomal genes by reference-based alignment and mutation catalogue lookup

  Input                   validated_genome.fasta; species_id (from validation); mutation_catalogue.json (versioned)

  Output                  mutations_detected.json: {mutations: \[{gene, position, ref_aa, alt_aa, codon_change, clinical_significance, evidence_level}\]}

  Dependencies            BWA-MEM2 alignment, custom mutation caller, SNP-effect predictor, resistance mutation catalogue (CARD, AMRFinderPlus point mutation tables)

  API Interactions        Internal Nextflow process; results written to DB on completion

  Database Interactions   INSERT INTO resistance_mutations (sample_id, gene, position, change, significance)

  Error Handling          Species not in catalogue → WARNING; mutation at ambiguous position → flagged with LOW confidence; no mutations → empty result (not an error)

  Scalability             Medium CPU demand (4 CPUs); parallelisable per gene region of interest
  ----------------------- ----------------------------------------------------------------------------------------------------------------------------------------------

**Service 5 --- Mechanism Classification Service**

  ----------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------
  **Attribute**           **Detail**

  Purpose                 Assign each detected AMR gene and mutation to a resistance mechanism category using a rule engine backed by CARD ARO ontology

  Input                   amr_detection_results.json; mutations_detected.json; aro_ontology.json (versioned)

  Output                  mechanism_classification.json: {classified: \[{gene_or_mutation_id, mechanism_type, mechanism_subtype, aro_accession, drug_classes_affected\[\]}\]}

  Mechanism Types         antibiotic_inactivation, target_alteration, target_protection, efflux_pump, reduced_permeability, target_replacement

  Dependencies            CARD ARO ontology parser, rule engine (Python-based), custom classification override table

  Database Interactions   UPDATE amr_genes SET mechanism_type, aro_accession; UPDATE resistance_mutations SET mechanism_type

  Error Handling          Gene not in ontology → UNKNOWN mechanism (non-blocking); conflicting classifications → highest-evidence wins; stored with flag

  Scalability             Lightweight CPU process; completes in seconds; bottleneck is ARO ontology loading (cached in Redis)
  ----------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------

**Service 6 --- Phenotype Prediction Service**

  ----------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Attribute**           **Detail**

  Purpose                 Predict S/I/R clinical phenotype per antibiotic based on detected genotype using a rule engine with EUCAST and CLSI breakpoint integration

  Input                   mechanism_classification.json; breakpoint_tables.json (EUCAST/CLSI, versioned); prediction_config (breakpoint_source, organism_group)

  Output                  phenotype_predictions.json: {predictions: \[{antibiotic, antibiotic_class, predicted_phenotype, supporting_genes\[\], confidence, breakpoint_source, interpretation_notes}\]}

  Dependencies            Custom rule engine (Python), EUCAST breakpoint tables (annually updated), CLSI breakpoint tables, AMRFinderPlus phenotype table

  Database Interactions   INSERT INTO phenotype_predictions (sample_id, antibiotic, phenotype, confidence, supporting_evidence_json)

  Error Handling          Antibiotic not in breakpoint table for species → NOT_TESTABLE; conflicting evidence → INDETERMINATE with explanation; missing mechanism data → INCOMPLETE

  Scalability             Rule-engine execution; parallelisable per antibiotic class; \< 10 seconds per genome
  ----------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**Service 7 --- Virulence Profiling Service**

  ----------------------- ------------------------------------------------------------------------------------------------------------------------------------------
  **Attribute**           **Detail**

  Purpose                 Detect virulence factor genes using VFDB and VirulenceFinder databases; classify virulence gene function

  Input                   validated_genome.fasta; sample_id; virulence_config (identity_threshold, database_versions)

  Output                  virulence_profile.json: {virulence_genes: \[{gene_name, database, function_category, identity_pct, coverage_pct, coordinates}\]}

  Function Categories     toxin, adhesin, invasion, immune_evasion, siderophore, secretion_system, capsule, biofilm

  Dependencies            VFDB (Full-dataset, monthly updated), VirulenceFinder (≥2.0), Abricate VFDB profile

  Database Interactions   INSERT INTO virulence_genes (sample_id, gene_name, function_category, identity_pct, coordinates)

  Error Handling          Database lookup failure → retry; no virulence genes detected → empty result (valid); cross-database conflict → highest identity retained

  Scalability             Parallels AMR Detection in Nextflow; 4 CPUs, 8 GB RAM; runtime 5--20 minutes per genome
  ----------------------- ------------------------------------------------------------------------------------------------------------------------------------------

**Service 8 --- Confidence Scoring Service**

  ----------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Attribute**           **Detail**

  Purpose                 Compute a composite confidence score (0.0--1.0) for each AMR finding and phenotype prediction based on multiple evidence dimensions

  Input                   amr_detection_results.json; mutations_detected.json; mechanism_classification.json; phenotype_predictions.json; scoring_config.json

  Scoring Dimensions      \(1\) Alignment quality: identity×coverage product; (2) Database concordance: number of databases agreeing; (3) Clinical evidence weight: CARD evidence level (1--5); (4) Mutation catalogue confidence; (5) Phenotype rule strength

  Output                  confidence_scores.json: {scores: \[{finding_id, gene_or_mutation, overall_confidence, dimension_scores{}, interpretation_tier: HIGH/MEDIUM/LOW/INSUFFICIENT}}

  Database Interactions   UPDATE amr_genes SET confidence_score; UPDATE phenotype_predictions SET confidence_score, interpretation_tier

  Error Handling          Missing input dimension → partial score with missing dimensions flagged; score below minimum threshold → INSUFFICIENT tier

  Scalability             Pure computation; sub-second; downstream of all detection services
  ----------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

**Service 9 --- Module 2 Export Service**

  ----------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Attribute**           **Detail**

  Purpose                 Compile a standardised, schema-versioned CSV export (module2_input.csv) linking detected genotype to predicted phenotype, ready for Module 2 concordance analysis

  Input                   All completed Module 1 results for sample_id; export_config {schema_version, include_low_confidence, include_virulence}

  Output                  module2_input.csv with columns: sample_id, isolate_name, gene_name, gene_type, mechanism, drug_class, antibiotic, predicted_phenotype, confidence, evidence_genes, assembly_metrics_json, export_timestamp, schema_version

  Schema Versioning       Schema version locked at v1.0 for Module 2 compatibility; breaking changes increment major version and require Module 2 adapter update

  Database Interactions   SELECT from amr_genes, resistance_mutations, phenotype_predictions, confidence_scores; INSERT INTO module2_exports (sample_id, file_path, schema_version, export_timestamp)

  Error Handling          Missing required field → export fails with field error; schema version mismatch → REJECTED with version error; partial data (some services failed) → PARTIAL export with metadata flag

  Scalability             I/O-bound; single process; \< 5 seconds per sample
  ----------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

> **SECTION 5 --- DATA FLOW ARCHITECTURE**

**5.1 End-to-End Data Flow Diagram**

> INPUT: assembled_genome.fasta
>
> │
>
> ▼
>
> ┌─────────────────────────────────────────────────┐
>
> │ GENOME VALIDATION SERVICE │
>
> │ → validation_result.json │
>
> │ → assembly_metrics.json │
>
> └──────────────────────┬──────────────────────────┘
>
> │ validated_genome.fasta
>
> ┌────────────┴──────────────┐
>
> ▼ ▼
>
> ┌────────────────────┐ ┌───────────────────────┐
>
> │ AMR DETECTION │ │ VIRULENCE PROFILING │
>
> │ (parallel) │ │ (parallel) │
>
> │ amr_raw.json │ │ virulence.json │
>
> └─────────┬──────────┘ └───────────┬───────────┘
>
> │ │
>
> ▼ │
>
> ┌────────────────────┐ │
>
> │ MUTATION DETECTION│ │
>
> │ mutations.json │ │
>
> └─────────┬──────────┘ │
>
> ▼ │
>
> ┌────────────────────┐ │
>
> │ MECHANISM │ │
>
> │ CLASSIFICATION │ │
>
> │ mechanisms.json │ │
>
> └─────────┬──────────┘ │
>
> ▼ │
>
> ┌────────────────────┐ │
>
> │ PHENOTYPE │ │
>
> │ PREDICTION │◄───────────────┘
>
> │ predictions.json │
>
> └─────────┬──────────┘
>
> ▼
>
> ┌────────────────────┐
>
> │ CONFIDENCE │
>
> │ SCORING │
>
> │ scores.json │
>
> └─────────┬──────────┘
>
> ▼
>
> ┌────────────────────┐
>
> │ MODULE 2 EXPORT │
>
> │ module2_input.csv │
>
> └─────────┬──────────┘
>
> ▼
>
> OUTPUT: JSON / TSV / PDF reports

**5.2 Stage Transition Specifications**

  ----------------------- -------------------------------------------------------- ------------------------------------------------------------------------------------------ ----------------------------------------------------------------- ------------------------------------------- ----------------------------------------------------------------------------
  **Transition**          **Input**                                                **Output**                                                                                 **Validation Rule**                                               **Failure Mode**                            **Recovery**

  Upload → Validate       assembled_genome.fasta (raw upload)                      validation_result.json, validated_genome.fasta                                             Valid FASTA chars; size ≥200 kbp; no binary content               FASTA parse error or size below threshold   User re-uploads corrected file; new job created

  Validate → AMR Detect   validated_genome.fasta + assembly_metrics.json           amr_raw_card.json, amr_raw_amrfinder.json, amr_raw_resfinder.json, amr_raw_abricate.json   Genome file checksum verified; species_id present                 Tool execution failure or DB unavailable    Nextflow retry (max 3); partial results flagged

  AMR Detect → Mutate     validated_genome.fasta + species_id from validation      mutations_detected.json                                                                    species_id maps to mutation catalogue entry                       Species not in catalogue                    WARNING raised; pipeline continues; mutation result = empty

  Mutate → Classify       amr_raw_merged.json + mutations_detected.json            mechanism_classification.json                                                              All gene_ids from AMR detect present in input                     ARO lookup fails                            Retry ARO lookup; cache used if DB unavailable; UNKNOWN mechanism assigned

  Classify → Predict      mechanism_classification.json + breakpoint_tables.json   phenotype_predictions.json                                                                 Breakpoint table version matches config; species_group assigned   Missing breakpoint entry                    NOT_TESTABLE assigned for that antibiotic; pipeline continues

  Predict → Score         All prior result JSONs                                   confidence_scores.json                                                                     All required input files present and non-empty                    Missing input file                          Partial score computed; missing dimensions flagged

  Score → Export          confidence_scores.json + all result JSONs                module2_input.csv                                                                          Schema version match; all required fields populated               Schema validation failure                   PARTIAL export with missing field errors logged
  ----------------------- -------------------------------------------------------- ------------------------------------------------------------------------------------------ ----------------------------------------------------------------- ------------------------------------------- ----------------------------------------------------------------------------

> **SECTION 6 --- WORKFLOW ORCHESTRATION ARCHITECTURE**

**6.1 Nextflow DSL2 Design Principles**

-   All bioinformatics logic is encapsulated in versioned, containerised Nextflow processes.

-   Channels carry immutable tuples (sample_id, file_path, metadata_map) between processes.

-   Subworkflows group logically related processes and are independently testable.

-   Workflows compose subworkflows and define the global execution graph.

**6.2 Channel Architecture**

**Primary Channels**

  -------------------- -------------------------------------------------- --------------------------------------------------------------------------------------
  **Channel Name**     **Data Type**                                      **Source → Sink**

  ch_raw_fasta         tuple(sample_id, fasta_path, metadata)             Job Manager → Genome Validation Process

  ch_validated_fasta   tuple(sample_id, fasta_path, validation_metrics)   Genome Validation → AMR Detection, Mutation Detection, Virulence Profiling (fan-out)

  ch_amr_raw           tuple(sample_id, tool_name, result_json)           AMR Detection (per tool) → AMR Merge Process

  ch_amr_merged        tuple(sample_id, amr_merged_json)                  AMR Merge → Mutation Detection, Mechanism Classification

  ch_mutations         tuple(sample_id, mutations_json)                   Mutation Detection → Mechanism Classification

  ch_mechanisms        tuple(sample_id, mechanisms_json)                  Mechanism Classification → Phenotype Prediction

  ch_virulence         tuple(sample_id, virulence_json)                   Virulence Profiling → Phenotype Prediction

  ch_predictions       tuple(sample_id, predictions_json)                 Phenotype Prediction → Confidence Scoring

  ch_scores            tuple(sample_id, scores_json)                      Confidence Scoring → Module 2 Export, Reporting

  ch_module2           tuple(sample_id, module2_csv_path)                 Module 2 Export → DB Write, File Storage
  -------------------- -------------------------------------------------- --------------------------------------------------------------------------------------

**6.3 Workflow Architecture Diagram**

> workflow MODULE1_AMR {
>
> take: ch_raw_fasta
>
> main:
>
> VALIDATE_GENOME(ch_raw_fasta)
>
> │ ch_validated_fasta
>
> ├──────────────────────┐──────────────────────────┐
>
> ▼ ▼ ▼
>
> AMR_DETECT_SUBWF MUTATION_DETECT VIRULENCE_SUBWF
>
> ├ CARD_RGI │ ALIGN_REFERENCE ├ VFDB_SCREEN
>
> ├ AMRFINDERPLUS │ CALL_MUTATIONS └ VIRULENCEFINDER
>
> ├ RESFINDER └ ch_mutations
>
> └ ABRICATE
>
> │ ch_amr_raw │
>
> ▼ ▼
>
> MERGE_AMR_RESULTS MECHANISM_CLASSIFY
>
> │ ch_amr_merged │
>
> └──────────────────────────►─┤
>
> │ ch_mechanisms
>
> ▼
>
> PHENOTYPE_PREDICT
>
> (+ ch_virulence)
>
> │ ch_predictions
>
> ▼
>
> CONFIDENCE_SCORE
>
> │ ch_scores
>
> ▼
>
> MODULE2_EXPORT
>
> GENERATE_REPORTS
>
> }

**6.4 Process Resource Allocation**

  --------------------- ---------- ------------ --------------------------------------- -----------------
  **Process**           **CPUs**   **Memory**   **Container Image**                     **Max Runtime**

  VALIDATE_GENOME       2          4 GB         amr-platform/genome-validator:1.0       10 min

  CARD_RGI              8          16 GB        finlaymaguire/card-rgi:6.0              60 min

  AMRFINDERPLUS         4          8 GB         ncbi/amrfinderplus:3.11                 30 min

  RESFINDER             4          8 GB         amr-platform/resfinder:4.1              30 min

  ABRICATE              4          8 GB         staphb/abricate:1.0                     20 min

  MUTATION_DETECT       4          8 GB         amr-platform/mutation-detector:1.0      30 min

  MECHANISM_CLASSIFY    2          4 GB         amr-platform/mechanism-classifier:1.0   5 min

  PHENOTYPE_PREDICT     2          4 GB         amr-platform/phenotype-predictor:1.0    10 min

  VIRULENCE_PROFILING   4          8 GB         amr-platform/virulence-profiler:1.0     30 min

  CONFIDENCE_SCORING    1          2 GB         amr-platform/confidence-scorer:1.0      2 min

  MODULE2_EXPORT        1          2 GB         amr-platform/module2-exporter:1.0       2 min
  --------------------- ---------- ------------ --------------------------------------- -----------------

**6.5 Checkpointing and Restart Strategy**

-   Nextflow -resume flag enables process-level checkpointing; completed processes are skipped on re-run.

-   Work directory: /data/nextflow/work/{sample_id}/ --- cached per unique input hash.

-   Job Manager stores Nextflow session ID per job; resumes from last checkpoint on CELERY_RETRY.

-   Process-level retry: maxRetries = 3 with memory scaling (memory \* task.attempt) for OOM failures.

-   All intermediate files are retained for 7 days; purged by a scheduled cleanup process.

> **SECTION 7 --- COMPUTATIONAL ALGORITHM ARCHITECTURE**

**Library 1 --- Alignment Algorithms**

**Smith-Waterman (Local Alignment)**

Purpose: optimal local pairwise alignment for detecting short AMR gene fragments in assembled contigs with high sensitivity. Used in AMR Detection and Virulence Profiling for partial gene detection.

-   Implementation: C extension (libssw) wrapped via Python ctypes for performance.

-   Parameters: match_score=2, mismatch_penalty=-3, gap_open=-5, gap_extend=-2 (defaults; configurable per database context).

-   Output: alignment score, query/reference start-end, CIGAR string, identity%, coverage%.

**Needleman-Wunsch (Global Alignment)**

Purpose: full-length gene alignment for mutation detection where the complete gene must be aligned to the reference to accurately call point mutations.

-   Implementation: BioPython pairwise2 with custom scoring matrices; used for genes \< 5 kbp.

-   Usage context: Mutation Detection Service, gene-level identity verification.

**Reusability Strategy**

Packaged as amr_platform.algorithms.alignment Python module. Exposes AlignmentEngine class with methods: align_local(), align_global(), align_bwt(). All downstream services import from this shared module.

**Library 2 --- Search Algorithms**

**Burrows-Wheeler Transform (BWT) and FM-Index**

Purpose: ultra-fast exact and approximate string matching against large AMR database reference collections. Enables rapid screening of assembled genomes against CARD, AMRFinderPlus, and VFDB.

-   BWT index pre-built for each database release; stored in indexed_databases/ volume.

-   FM-Index queried per assembled contig; backtrack search for approximate matches (≤2 mismatches).

-   Reuse in Module 3: MGE insertion site detection reuses the BWT index infrastructure.

**BWA-MEM Concepts**

BWA-MEM2 is used for whole-genome vs reference alignment in mutation detection. Seeding via super-maximal exact match (SMEM) algorithm followed by extension using Smith-Waterman.

**Library 3 --- Similarity Algorithms**

**MinHash**

Purpose: rapid genomic distance estimation for species identification and database pre-filtering. Reduces alignment workload by selecting relevant reference sequences before full alignment.

-   K-mer size: k=21; sketch size: 1000; Jaccard threshold: 0.05 for species-level match.

-   Reuse in surveillance workflows: MinHash sketches stored per isolate; used in Module 3 for MGE clustering.

**Jaccard Similarity**

Purpose: gene content similarity between isolates in batch analyses; used for deduplication of AMR gene calls across overlapping database results.

**Library 4 --- Statistical Algorithms**

  ---------------------- ----------------------------------------------------------------------- ------------------------------------------------------------------------------------
  **Algorithm**          **Formula**                                                             **Use Context**

  Bit Score              S\' = (λ × S - ln K) / ln 2                                             Normalised alignment quality; database-independent comparison

  E-value                E = K × m × n × e\^(-λS)                                                Statistical significance of alignment; threshold: E \< 1e-5 for AMR gene reporting

  Coverage %             (aligned_length / gene_length) × 100                                    Proportion of reference gene covered; threshold: ≥80% for full gene call

  Identity %             (matches / aligned_length) × 100                                        Sequence identity; threshold: ≥80% for gene call; ≥95% for variant-level call

  Composite Confidence   C = w1×identity + w2×coverage + w3×db_concordance + w4×evidence_level   Per-finding confidence score in Confidence Scoring Service
  ---------------------- ----------------------------------------------------------------------- ------------------------------------------------------------------------------------

All statistical algorithm implementations are packaged in amr_platform.algorithms.statistics. Weights (w1--w4) are configurable via platform admin settings with defaults validated against benchmark datasets.

> **SECTION 8 --- DATABASE ARCHITECTURE OVERVIEW**

**8.1 Database Responsibilities**

-   Persist all sample, job, and analysis metadata with full audit trails.

-   Store AMR detection results, mutation findings, phenotype predictions, and virulence profiles.

-   Track reference database versions used for each analysis (CARD, AMRFinderPlus, ResFinder, VFDB versions).

-   Maintain user, project, and access control data.

-   Record Module 2 export metadata and linkage.

**8.2 Data Domains**

  ----------------------- --------------------------------------------------- ----------------------------------------------------
  **Domain**              **Tables (Overview)**                               **Description**

  Identity & Access       users, projects, roles, api_keys                    Authentication and RBAC data

  Sample Management       samples, sample_metadata, assemblies                Uploaded genome records and assembly metrics

  Job Management          jobs, job_events, job_checkpoints                   Celery job lifecycle and state tracking

  AMR Findings            amr_genes, resistance_mutations, gene_annotations   Core AMR detection outputs

  Mechanism & Phenotype   mechanism_classifications, phenotype_predictions    Classification and clinical interpretation results

  Virulence               virulence_genes                                     Virulence factor profiles

  Confidence              confidence_scores                                   Scoring metadata per finding

  Reference Databases     db_versions, db_changelogs                          Database version tracking and audit

  Exports                 module2_exports, report_artefacts                   Generated output file metadata

  Audit                   audit_log, data_access_log                          Full audit trail
  ----------------------- --------------------------------------------------- ----------------------------------------------------

**8.3 Persistence Strategy**

-   Primary database: PostgreSQL 15+ with JSONB columns for flexible metadata storage alongside normalised relational structure.

-   Write-ahead logging (WAL) enabled; streaming replication to hot standby for HA.

-   Connection pooling via PgBouncer (transaction mode; max pool size 100).

**8.4 Data Retention, Versioning, and Indexing**

  ------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **Concern**               **Strategy**

  Data Retention            Genome FASTA files: 12 months active, then archive to cold storage. Analysis results: 7 years (clinical traceability). Audit logs: 10 years minimum.

  Schema Versioning         Alembic migrations for all schema changes. Migration scripts versioned in git. Downgrade migrations required for all changes.

  Reference DB Versioning   db_versions table records: db_name, version, download_date, checksum, active_flag. Analysis results linked to db_version_id at time of analysis.

  Indexing Strategy         B-tree indexes on: sample_id, job_id, user_id, project_id. GIN index on JSONB fields queried frequently (assembly_metrics, evidence). Partial indexes on job status for queue queries.

  Expected Data Growth      Estimated 10,000 samples/year × \~500 KB results each = \~5 GB/year structured data. FASTA storage: 10,000 × 5 MB = \~50 GB/year.

  Future Scalability        Table partitioning by project_id and analysis_date when \> 1M samples. Read replicas for reporting queries. TimescaleDB extension for surveillance time-series analytics.
  ------------------------- ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

> **SECTION 9 --- API ARCHITECTURE OVERVIEW**

**9.1 REST API Structure**

  -------------------- ------------------ ----------------------------------------------------------------------
  **Endpoint Group**   **Path Prefix**    **Key Operations**

  Samples              /api/v1/samples    POST (upload), GET (list/detail), DELETE

  Jobs                 /api/v1/jobs       GET (status, detail), POST (cancel), GET /jobs/{id}/progress

  Results              /api/v1/results    GET AMR genes, mutations, mechanisms, predictions, virulence, scores

  Reports              /api/v1/reports    GET JSON/TSV/PDF by sample_id and report_type

  Exports              /api/v1/exports    GET module2_input.csv by sample_id or project_id

  Projects             /api/v1/projects   CRUD for project management and isolation

  Admin                /api/v1/admin      Database version management, user admin, system health

  Auth                 /api/v1/auth       POST /login (issue JWT), POST /refresh, POST /logout
  -------------------- ------------------ ----------------------------------------------------------------------

**9.2 Authentication and Authorisation**

-   JWT-based authentication: access token (TTL 15 min) + refresh token (TTL 7 days) stored as HttpOnly cookies or Bearer header.

-   Tokens signed with RS256 (asymmetric); private key stored in Vault / environment secret; public key distributed to services.

-   RBAC roles: SUPERADMIN, ADMIN, PROJECT_OWNER, ANALYST, VIEWER. Permissions enforced per endpoint with FastAPI dependency injection.

-   Project isolation: every data query scoped to project_id from JWT claims; cross-project access explicitly denied unless ADMIN.

**9.3 Standards and Conventions**

  -------------------- -------------------------------------------------------------------------------------------------------------------------------------------------
  **Concern**          **Standard**

  Request Validation   Pydantic v2 models for all request bodies and query params; strict mode; custom validators for FASTA file validation

  Response Envelope    {\"status\": \"success\|error\", \"data\": {}, \"meta\": {pagination, timestamps}, \"errors\": \[\]}

  Error Codes          HTTP status + machine-readable error_code string (e.g. VALIDATION_FASTA_TOO_SHORT, JOB_NOT_FOUND)

  Versioning           URI versioning: /api/v1/, /api/v2/; v1 maintained for minimum 12 months after v2 release; deprecation header added

  Rate Limiting        Per user: 1000 req/hour; per IP (unauthenticated): 100 req/hour; upload endpoint: 20 uploads/hour; enforced via Redis sliding window

  Logging              Structured JSON logs (structlog); every request logged with: user_id, project_id, endpoint, method, status_code, duration_ms, request_id (UUID)

  Audit Trail          Every mutating operation (POST/PUT/DELETE/PATCH) written to audit_log table with before/after JSON snapshot

  WebSocket            FastAPI WebSocket at /ws/jobs/{job_id}/progress; emits progress events as {event, percent, message, timestamp}

  GraphQL              Strawberry-GraphQL mounted at /graphql in v2 (planned); v1 REST remains primary; same auth middleware applies
  -------------------- -------------------------------------------------------------------------------------------------------------------------------------------------

> **SECTION 10 --- JOB MANAGEMENT ARCHITECTURE**

**10.1 Job Lifecycle**

> CREATED → QUEUED → RUNNING → \[COMPLETED \| FAILED \| CANCELLED\]
>
> │
>
> └── RETRY (up to max_retries=3)

**10.2 Celery Architecture**

  ---------------- --------------------------------------------------------------------------------------------------
  **Component**    **Configuration**

  Broker           Redis 7.x; connection pool 50; sentinel HA configuration for production

  Result Backend   Redis; job result TTL 24h; final status written to PostgreSQL on completion

  Task Queues      high_priority (clinical single-sample), default (batch), low_priority (surveillance large batch)

  Workers          Separate worker pools per queue; autoscaling 2--20 workers per queue based on queue depth

  Task Routing     Task router maps sample type (clinical/batch/surveillance) to appropriate queue

  Serialisation    JSON serialiser; message size limit 10 MB (large payloads use file paths, not inline data)
  ---------------- --------------------------------------------------------------------------------------------------

**10.3 Job State Definitions**

  ----------- ----------------------------------------------------------------- ------------------------------------
  **State**   **Description**                                                   **Transitions**

  QUEUED      Job submitted; in Redis queue awaiting worker pickup              → RUNNING, → CANCELLED

  RUNNING     Celery worker executing; Nextflow workflow active                 → COMPLETED, → FAILED, → CANCELLED

  COMPLETED   All services succeeded; reports generated                         Terminal state

  FAILED      Any service failed after max retries; error details stored        → QUEUED (manual resubmit)

  CANCELLED   User or admin cancelled; Nextflow process terminated gracefully   Terminal state
  ----------- ----------------------------------------------------------------- ------------------------------------

**10.4 Retry and Recovery Policies**

-   Automatic retry on transient failures (network timeout, OOM): max 3 retries; exponential back-off (30s, 120s, 480s).

-   No retry on validation failures (FASTA invalid, schema error): immediate FAILED state with user notification.

-   Nextflow -resume used on retry to avoid re-running completed processes.

-   Progress tracking: Celery task sends progress updates to Redis pub/sub channel; WebSocket streams to client.

-   Monitoring: Flower dashboard for Celery queue visibility; Prometheus metrics for queue depth, task latency, failure rate.

> **SECTION 11 --- FILE MANAGEMENT ARCHITECTURE**

**11.1 Storage Tiers**

  -------------- --------------------------------------- --------------------------------------------- -------------------------------------------------- -------------------------------------------------
  **Tier**       **Storage System**                      **Contents**                                  **Retention**                                      **Access Pattern**

  Upload         MinIO/S3: uploads/                      Raw user-uploaded FASTA files                 30 days post-analysis                              Write-once; read by validation service

  Intermediate   Nextflow work dir (local NFS)           Tool output files during pipeline execution   7 days; auto-purged                                Read/write during workflow; not user-accessible

  Results        MinIO/S3: results/{sample_id}/          JSON, TSV, PDF output files                   12 months active; then archive                     Read on demand; served via presigned URL

  Archive        MinIO/S3 Glacier-equivalent: archive/   Long-term result storage post-active period   7 years (clinical traceability)                    Infrequent access; restore-on-request

  Reference DB   Read-only NFS volume                    CARD, AMRFinderPlus, VFDB, etc.               Updated on new DB release; old versions retained   Read-only; bulk sequential reads by tools
  -------------- --------------------------------------- --------------------------------------------- -------------------------------------------------- -------------------------------------------------

**11.2 File Naming Conventions**

> {sample_id}/{analysis_version}/{service_name}/{output_type}.{ext}
>
> Example: a3f8b2c1-4d5e/v1.0.0/amr_detection/amr_merged.json
>
> Example: a3f8b2c1-4d5e/v1.0.0/reports/phenotype_report.pdf

**11.3 Integrity and Security**

-   SHA-256 checksum computed on upload; stored in samples.upload_checksum; verified before every pipeline run.

-   All S3 objects encrypted at rest (AES-256 SSE); in transit via TLS 1.3.

-   Presigned URLs (TTL 1 hour) used for all file download access; direct bucket access prohibited.

-   Large file upload (\>100 MB): multipart upload with 10 MB chunks; resumable upload support via TUS protocol.

> **SECTION 12 --- REPORTING ARCHITECTURE**

**12.1 Output Formats**

  ---------------- ------------------------------------------- ----------------------------------------------------------------------------------------------------- ----------------------------------------------------------
  **Format**       **Generator**                               **Contents**                                                                                          **Consumer**

  JSON             FastAPI response serialiser (Pydantic)      Complete structured results per API endpoint; machine-readable                                        API clients, Module 2, LIS integration

  TSV              Python csv module with tab delimiter        Flat tabular exports: AMR genes, mutations, predictions per sample                                    Bioinformaticians, surveillance teams, R/Python analysis

  PDF              WeasyPrint/ReportLab; HTML template → PDF   Clinical summary: resistance profile, key findings, phenotype table, QC metrics, interpretive notes   Clinicians, lab directors, public health reports

  CSV (Module 2)   Module 2 Export Service                     Standardised genotype-phenotype linkage table                                                         Module 2 concordance engine
  ---------------- ------------------------------------------- ----------------------------------------------------------------------------------------------------- ----------------------------------------------------------

**12.2 Future Reporting Capabilities**

-   Dashboard integration: JSON data feeds to Grafana or custom React dashboard for real-time surveillance visualisations.

-   Surveillance reporting: aggregate AMR prevalence reports per project, organism, geographic region, and time period.

-   Automated scheduled reports: weekly/monthly batch summary PDFs dispatched to project owners.

> **SECTION 13 --- SECURITY ARCHITECTURE**

  --------------------- ---------------------------------------------------------------------------- -----------------------------------------------------------------------------------------------------------
  **Security Domain**   **Control**                                                                  **Implementation**

  Authentication        JWT RS256 tokens; MFA optional for ADMIN roles                               FastAPI security dependency; token refresh endpoint; session revocation via Redis blocklist

  Authorisation         RBAC with project-scoped data isolation                                      Permission matrix enforced via FastAPI depends(); project_id claim in JWT; ORM-level row filtering

  Secrets Management    No secrets in code or environment files in production                        HashiCorp Vault for DB credentials, API keys, JWT private keys; Vault agent sidecar in Kubernetes

  Container Security    Non-root containers; read-only root filesystem; no privileged mode           Dockerfile USER instruction; securityContext in K8s pods; image scanning with Trivy in CI/CD

  Database Security     Encrypted connections; least-privilege DB users; no direct internet access   TLS for all PostgreSQL connections; separate DB users per service; firewall rules; pgaudit extension

  Audit Logging         Immutable audit trail for all data access and mutations                      audit_log table with row-level before/after snapshots; log forwarding to SIEM; tamper-evident hashing

  User Isolation        Complete data isolation between users; project-scoped access                 All queries include project_id filter; API-level validation; no cross-user data in responses

  Project Isolation     Data and results fully partitioned per project                               S3 bucket policies scoped by project_id prefix; DB row security policies

  Input Sanitisation    All inputs validated and sanitised before processing                         Pydantic strict models; file type validation; FASTA character whitelist; SQL injection prevention via ORM

  Dependency Security   Automated vulnerability scanning of Python and container dependencies        Dependabot / Renovate for dependency updates; Snyk/Trivy in CI; SBOM generated per release
  --------------------- ---------------------------------------------------------------------------- -----------------------------------------------------------------------------------------------------------

> **SECTION 14 --- DEPLOYMENT ARCHITECTURE**

**14.1 Docker Compose Stack (Development / Staging)**

> services:
>
> postgres:
>
> image: postgres:15-alpine
>
> volumes: \[postgres_data:/var/lib/postgresql/data\]
>
> environment: \[POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD\]
>
> redis:
>
> image: redis:7-alpine
>
> command: redis-server \--appendonly yes
>
> minio:
>
> image: minio/minio:latest
>
> command: server /data \--console-address \":9001\"
>
> api:
>
> build: ./services/api
>
> depends_on: \[postgres, redis, minio\]
>
> ports: \[\"8000:8000\"\]
>
> environment: \[DATABASE_URL, REDIS_URL, S3_ENDPOINT, JWT_PRIVATE_KEY_PATH\]
>
> celery_worker:
>
> build: ./services/api
>
> command: celery -A app.celery worker -Q high_priority,default,low_priority
>
> volumes: \[nextflow_work:/data/nextflow, reference_dbs:/data/databases:ro\]
>
> flower:
>
> image: mher/flower:latest
>
> depends_on: \[redis\]
>
> ports: \[\"5555:5555\"\]

**14.2 Production Deployment Architecture**

> ┌──────────────────────────────────────────────────────────────┐
>
> │ KUBERNETES CLUSTER │
>
> │ │
>
> │ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
>
> │ │ API Pods │ │ Celery Worker│ │ Nextflow Pods │ │
>
> │ │ (3 replicas) │ │ Pods (auto) │ │ (job-scoped) │ │
>
> │ └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘ │
>
> │ │ │ │ │
>
> │ ┌──────▼─────────────────▼────────────────────▼─────────┐ │
>
> │ │ Internal Service Mesh (mTLS) │ │
>
> │ └──────────────────────────────────────────────────────┘ │
>
> │ │
>
> │ ┌────────────────┐ ┌──────────────┐ ┌────────────────┐ │
>
> │ │ PostgreSQL │ │ Redis │ │ MinIO │ │
>
> │ │ (StatefulSet) │ │ Cluster │ │ Object Store │ │
>
> │ └────────────────┘ └──────────────┘ └────────────────┘ │
>
> └──────────────────────────────────────────────────────────────┘
>
> │
>
> ┌────────▼───────────────────────────────────────────────────┐
>
> │ INGRESS: nginx / Traefik + TLS termination │
>
> │ Load Balancer → API Service │
>
> └────────────────────────────────────────────────────────────┘

**14.3 Kubernetes Compatibility Design**

-   All services stateless; state persisted to PostgreSQL, Redis, or MinIO --- never in container memory across requests.

-   ConfigMaps for environment configuration; Secrets for credentials (sourced from Vault via External Secrets Operator).

-   HorizontalPodAutoscaler on API and Celery worker deployments; scale on CPU (70%) and queue depth metrics.

-   PersistentVolumeClaims for: reference database volume (ReadOnlyMany), Nextflow work directory (ReadWriteMany via NFS).


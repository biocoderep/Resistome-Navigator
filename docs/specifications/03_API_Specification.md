# 03 — REST API and Service Contract Specification

> **MVP Implementation Note:** Build only the sections marked 🟢 MVP now.

| Section | Feature | Phase |
|---------|---------|-------|
| 4 — Authentication API | JWT register/login/refresh | 🟡 Phase 2 |
| 7 — Sample Management API | POST/GET /samples, file upload | 🟢 MVP |
| 8 — File Upload API | Upload FASTA, chunked upload | 🟢 MVP |
| 10 — AMR Detection API | POST/GET /module1/amr-detection | 🟢 MVP |
| 11 — Mutation Detection API | /module1/mutations | 🟡 Phase 2 |
| 12 — Mechanism API | /module1/mechanisms | 🟡 Phase 2 |
| 13 — Phenotype Prediction API | /module1/predict | 🟠 Phase 3 |
| 14 — Virulence API | /module1/virulence | 🔵 Phase 4 |
| 17 — WebSocket Architecture | Real-time progress events | 🟠 Phase 3 |

> **🟢 MVP Auth:** No JWT in MVP. Use a simple API key header `X-API-Key` or skip auth entirely for local development.

---

**REST API & SERVICE CONTRACT**

**SPECIFICATION**

**ACS --- Version 1.0**

**MODULE 1 --- ANTIMICROBIAL RESISTANCE CHARACTERISATION ENGINE**

FastAPI · PostgreSQL · Celery · Redis · Nextflow DSL2

CONFIDENTIAL --- Internal Engineering Document

> **SECTION 1 --- API OBJECTIVES**

**1.1 Purpose**

The Module 1 REST API is the authoritative, versioned communication contract between all consumers and the AMR Characterisation Engine backend. It exposes every capability of the bioinformatics pipeline --- from genome upload through AMR detection, phenotype prediction, and report generation --- as a secure, stateless, and reproducible HTTP interface.

**1.2 Target Consumers**

  ------------------------------------- -------------------------- ------------------------------- ----------------------------------------
  **Consumer**                          **Access Pattern**         **Authentication**              **Notes**

  Web Frontend (React/Vue)              Browser HTTP + WebSocket   JWT Bearer / HttpOnly cookie    Primary interactive interface

  CLI Client (Python)                   HTTP REST batch            API Token (Bearer)              Batch submission and polling

  Laboratory Information System (LIS)   REST integration           API Token + webhook callbacks   Clinical workflow integration

  Module 2 Service                      Internal HTTP REST         Service-to-service API Token    Consumes Module 1 export endpoints

  Module 3 Service                      Internal HTTP REST         Service-to-service API Token    Consumes AMR gene coordinate endpoints

  CI/CD Pipeline                        REST (testing)             API Token                       Contract tests, integration tests

  Nextflow Callback                     Internal POST              Internal service token          Reports progress and results
  ------------------------------------- -------------------------- ------------------------------- ----------------------------------------

**1.3 Design Principles**

  ---------------- ------------------------------------------------------------------------------------------------------------
  **Principle**    **Implementation**

  Stateless        No server-side session state; all context carried in JWT claims or request body

  REST             Resource-oriented URLs; correct HTTP verbs; standard status codes; HATEOAS links on collection responses

  JSON First       All request/response bodies application/json; multipart/form-data for file uploads only

  Versioning       URI path versioning: /api/v1/; v1 maintained ≥ 12 months after v2 launch

  Error Standard   Uniform error envelope {status, error_code, message, details, request_id} on all 4xx/5xx responses

  Auth Strategy    JWT RS256 access tokens (15 min TTL) + refresh tokens (7 days); API tokens for CLI/service accounts

  Idempotency      POST endpoints for job submission accept idempotency-key header; duplicate submissions return existing job

  Async First      All bioinformatics operations return job_id immediately; clients poll or receive WebSocket events
  ---------------- ------------------------------------------------------------------------------------------------------------

> **SECTION 2 --- API ARCHITECTURE**

**2.1 Architecture Diagram**

> ┌────────────────────────────────────────────────────────────────┐
>
> │ CLIENT LAYER │
>
> │ Web Browser │ CLI Tool │ LIS System │ Module 2/3 Services │
>
> └───────────────────────────┬────────────────────────────────────┘
>
> │ HTTPS / WSS
>
> ┌───────────────────────────▼────────────────────────────────────┐
>
> │ API GATEWAY LAYER │
>
> │ nginx / Traefik │ TLS Termination │ Rate Limit (Redis) │
>
> │ Request Logging │ Correlation ID Injection │
>
> └───────────────────────────┬────────────────────────────────────┘
>
> │
>
> ┌───────────────────────────▼────────────────────────────────────┐
>
> │ AUTHENTICATION LAYER (FastAPI) │
>
> │ JWT Validation (RS256) │ API Token Lookup │ MFA Check │
>
> │ FastAPI Depends() middleware on every protected route │
>
> └───────────────────────────┬────────────────────────────────────┘
>
> │
>
> ┌───────────────────────────▼────────────────────────────────────┐
>
> │ VALIDATION LAYER (Pydantic v2) │
>
> │ Request body schemas │ Query param validators │
>
> │ File type/size checks │ Custom business rule validators │
>
> └───────────────────────────┬────────────────────────────────────┘
>
> │
>
> ┌───────────────────────────▼────────────────────────────────────┐
>
> │ BUSINESS LOGIC LAYER (FastAPI Routers) │
>
> │ Auth │ Users │ Projects │ Samples │ Files │ Module1 │ Reports │
>
> │ Workflow │ Admin │
>
> └────┬────────────────────────────────────────────┬──────────────┘
>
> │ SQLAlchemy ORM │ Celery tasks
>
> ┌────▼───────────────┐ ┌───────────▼──────────────┐
>
> │ DATABASE LAYER │ │ WORKFLOW LAYER │
>
> │ PostgreSQL (sync) │ │ Celery + Redis Queue │
>
> │ Redis (cache) │ │ Nextflow DSL2 Executor │
>
> └────────────────────┘ └──────────────────────────┘
>
> │ WebSocket events
>
> ┌───────────────────────────▼────────────────────────────────────┐
>
> │ NOTIFICATION LAYER (WebSocket / Webhook) │

**2.2 Layer Responsibilities**

  ---------------- ------------------------------------ --------------------------------------------------------------------------------------------------
  **Layer**        **Framework/Tool**                   **Responsibilities**

  API Gateway      nginx/Traefik                        TLS termination, rate limiting, correlation ID injection, access logging, static asset serving

  Authentication   FastAPI Depends(), python-jose       JWT signature validation, token expiry check, API token lookup, user/project context injection

  Validation       Pydantic v2 strict models            Schema validation, type coercion, custom validators, file type checks, business rule enforcement

  Business Logic   FastAPI routers + service classes    Domain logic, permission checks, orchestration of DB and Celery calls, response assembly

  Workflow         Celery 5.x + Redis 7.x               Async job dispatch, Nextflow execution, progress tracking, retry management

  Database         SQLAlchemy 2 async + asyncpg         Persistence, query execution, transaction management, ORM session lifecycle

  Notification     FastAPI WebSocket + httpx webhooks   Real-time progress events, job completion callbacks, report generation alerts
  ---------------- ------------------------------------ --------------------------------------------------------------------------------------------------

> **SECTION 3 --- API VERSIONING**

**3.1 Versioning Strategy**

-   URI path versioning: /api/v1/, /api/v2/ --- version embedded in URL for clarity and cacheability.

-   Version is tied to breaking-change boundary; additive changes (new fields, new optional params) do not increment version.

-   v1 remains available ≥ 12 months after v2 release; sunset date communicated via Deprecation and Sunset headers.

**3.2 Version Compatibility Rules**

  -------------------------------- ----------------------------------- -------------------------------------------------
  **Change Type**                  **Version Impact**                  **Example**

  Add new optional request field   Non-breaking --- same version       Add optional notes field to sample creation

  Add new response field           Non-breaking --- same version       Add species_taxid to sample response

  Remove or rename field           Breaking --- new version required   Rename identity to identity_pct

  Change field type                Breaking --- new version required   confidence: string → float

  Remove endpoint                  Breaking --- deprecation cycle      3-month deprecation notice + Deprecation header

  Change authentication method     Breaking --- new version required   Switch from Basic to JWT

  Change error response shape      Breaking --- new version required   Add error_code field to all error responses
  -------------------------------- ----------------------------------- -------------------------------------------------

**3.3 Deprecation Headers**

> Deprecation: true
>
> Sunset: Sat, 01 Jan 2027 00:00:00 GMT
>
> Link: \<https://docs.amrplatform.io/api/migration/v1-to-v2\>; rel=\"deprecation\"
>
> **SECTION 4 --- AUTHENTICATION API**

**4.1 Endpoint: POST /api/v1/auth/register**

**POST** **/api/v1/auth/register**

Creates a new user account. Only available when ALLOW_REGISTRATION=true in environment config; disabled in clinical-only deployments.

**Request Body**

> {
>
> \"email\": \"analyst@hospital.org\", // required, valid email, unique
>
> \"username\": \"j.smith\", // required, 3-50 chars, alphanumeric+underscore
>
> \"password\": \"Str0ng!Pass#2025\", // required, ≥12 chars, complexity rules
>
> \"full_name\": \"Jane Smith\" // optional

**Response 201**

> {
>
> \"status\": \"success\",
>
> \"data\": {
>
> \"user_id\": \"a3f8b2c1-\...\",
>
> \"email\": \"analyst@hospital.org\",
>
> \"username\": \"j.smith\",
>
> \"created_at\": \"2025-06-01T10:00:00Z\"
>
> }
>
> }

**Error Responses**

  ------------ ----------------------- ----------------------------------------------------
  **Status**   **error_code**          **Condition**

  400          VALIDATION_ERROR        Invalid email, weak password, or username format

  409          EMAIL_ALREADY_EXISTS    Email address already registered

  409          USERNAME_TAKEN          Username already in use

  403          REGISTRATION_DISABLED   ALLOW_REGISTRATION=false in configuration
  ------------ ----------------------- ----------------------------------------------------

**4.2 Endpoint: POST /api/v1/auth/login**

**POST** **/api/v1/auth/login**

**Request Body**

> {
>
> \"email\": \"analyst@hospital.org\", // required
>
> \"password\": \"Str0ng!Pass#2025\", // required

**Response 200**

> {
>
> \"status\": \"success\",
>
> \"data\": {
>
> \"access_token\": \"eyJhbGciOiJSUzI1NiJ9\...\", // JWT; TTL 15 min
>
> \"refresh_token\": \"eyJhbGciOiJSUzI1NiJ9\...\", // JWT; TTL 7 days
>
> \"token_type\": \"Bearer\",
>
> \"expires_in\": 900,
>
> \"user\": { \"id\": \"\...\", \"email\": \"\...\", \"roles\": \[\"ANALYST\"\] }
>
> }
>
> }
>
> **Security:** Tokens also set as HttpOnly SameSite=Strict cookies for browser clients. Rate limited: 5 failed attempts per 15 min per IP triggers 429 + 30-second lockout.

**4.3 Endpoint: POST /api/v1/auth/logout**

**POST** **/api/v1/auth/logout**

Revokes the refresh token and adds access token JTI to Redis blocklist for remaining TTL.

> Authorization: Bearer {access_token}
>
> Response 200: { \"status\": \"success\", \"data\": { \"message\": \"Logged out\" } }

**4.4 Endpoint: POST /api/v1/auth/refresh**

**POST** **/api/v1/auth/refresh**

> {
>
> \"refresh_token\": \"eyJhbGciOiJSUzI1NiJ9\...\"

Returns new access_token + new refresh_token (token rotation). Old refresh token is revoked on use.

**4.5 Endpoint: GET /api/v1/auth/me**

**GET** **/api/v1/auth/me**

Returns current authenticated user profile, roles, and project memberships.

> Authorization: Bearer {access_token}
>
> {
>
> \"status\": \"success\",
>
> \"data\": {
>
> \"id\": \"a3f8b2c1-\...\", \"email\": \"\...\", \"username\": \"\...\",
>
> \"roles\": \[\"ANALYST\"\], \"projects\": \[{\"id\":\"\...\", \"name\":\"\...\", \"role\":\"ANALYST\"}\],
>
> \"mfa_enabled\": false, \"last_login_at\": \"2025-06-01T09:55:00Z\"
>
> }
>
> }

**4.6 JWT Token Architecture**

  ------------------- ----------------------------------------------------------------------- -------------------------------------
  **Field**           **Access Token**                                                        **Refresh Token**

  Algorithm           RS256                                                                   RS256

  TTL                 900 seconds (15 min)                                                    604800 seconds (7 days)

  Claims              sub (user_id), jti, iat, exp, email, roles\[\], project_ids\[\]         sub, jti, iat, exp, token_family

  Storage (browser)   Memory / HttpOnly cookie                                                HttpOnly SameSite=Strict cookie

  Revocation          JTI blocklist in Redis (remaining TTL)                                  Deleted from sessions table + Redis

  Key rotation        New key pair deployed; old public key retained for TTL of live tokens   Same policy
  ------------------- ----------------------------------------------------------------------- -------------------------------------

> **SECTION 5 --- USER MANAGEMENT API**

  ------------ ------------------------------------ ---------------- ---------------------------------------
  **Method**   **Path**                             **Permission**   **Description**

  GET          /api/v1/users                        ADMIN            List all users (paginated)

  GET          /api/v1/users/{id}                   ADMIN or self    Get user by ID

  PUT          /api/v1/users/{id}                   ADMIN or self    Full update of user profile

  PATCH        /api/v1/users/{id}                   ADMIN or self    Partial update

  DELETE       /api/v1/users/{id}                   ADMIN            Soft-delete user (cannot delete self)

  PATCH        /api/v1/users/{id}/status            ADMIN            Activate or deactivate user account

  GET          /api/v1/users/{id}/roles             ADMIN            List roles assigned to user

  POST         /api/v1/users/{id}/roles             ADMIN            Assign role to user

  DELETE       /api/v1/users/{id}/roles/{role_id}   ADMIN            Remove role from user
  ------------ ------------------------------------ ---------------- ---------------------------------------

**5.1 User Response Schema**

> {
>
> \"id\": \"uuid\",
>
> \"email\": \"string\",
>
> \"username\": \"string\",
>
> \"full_name\": \"string \| null\",
>
> \"is_active\": \"boolean\",
>
> \"mfa_enabled\": \"boolean\",
>
> \"roles\": \[\"string\"\],
>
> \"created_at\": \"datetime\",
>
> \"last_login_at\":\"datetime \| null\"
>
> **Security:** password_hash, mfa_secret, and session data NEVER returned in any user response. Superadmin flag omitted for non-superadmin callers.
>
> **SECTION 6 --- PROJECT MANAGEMENT API**

  ------------ ----------------------------------------- ---------------- -----------------------------------------------------------
  **Method**   **Path**                                  **Permission**   **Description**

  POST         /api/v1/projects                          ANALYST+         Create project; creator becomes PROJECT_OWNER

  GET          /api/v1/projects                          Authenticated    List projects user is member of (paginated, filterable)

  GET          /api/v1/projects/{id}                     Project member   Get project detail with settings and member count

  PUT          /api/v1/projects/{id}                     PROJECT_OWNER    Update project name, description, type

  DELETE       /api/v1/projects/{id}                     PROJECT_OWNER    Soft-delete project (RESTRICTED if samples exist)

  GET          /api/v1/projects/{id}/members             Project member   List project members with roles

  POST         /api/v1/projects/{id}/members             PROJECT_OWNER    Add member to project with role assignment

  PATCH        /api/v1/projects/{id}/members/{user_id}   PROJECT_OWNER    Change member role

  DELETE       /api/v1/projects/{id}/members/{user_id}   PROJECT_OWNER    Remove member from project

  GET          /api/v1/projects/{id}/settings            PROJECT_OWNER    Get project analysis settings

  PUT          /api/v1/projects/{id}/settings            PROJECT_OWNER    Update analysis settings (thresholds, tools, breakpoints)

  GET          /api/v1/projects/{id}/stats               Project member   Sample count, job stats, result summary
  ------------ ----------------------------------------- ---------------- -----------------------------------------------------------

**6.1 Project Create Request**

> {
>
> \"name\": \"ICU AMR Surveillance 2025\", // required, 3-200 chars
>
> \"slug\": \"icu-amr-2025\", // optional; auto-generated if omitted
>
> \"description\": \"\...\", // optional
>
> \"project_type\": \"surveillance\" // research\|clinical\|surveillance\|batch

**6.2 Filtering and Pagination**

> GET /api/v1/projects?page=1&page_size=20&type=surveillance&search=ICU&sort=created_at&order=desc
>
> **SECTION 7 --- SAMPLE MANAGEMENT API**

  ------------ ------------------------------ ------------------------------------------------------------------------
  **Method**   **Path**                       **Description**

  POST         /api/v1/samples                Register new sample (without file; file attached via Files API)

  GET          /api/v1/samples                List samples in project (paginated, filterable by species/status/date)

  GET          /api/v1/samples/{id}           Sample detail with assembly metrics and job history

  PUT          /api/v1/samples/{id}           Update sample metadata

  DELETE       /api/v1/samples/{id}           Soft-delete sample (RESTRICTED if reports exist)

  POST         /api/v1/samples/bulk-upload    Register multiple samples from CSV manifest

  GET          /api/v1/samples/{id}/jobs      List all analysis jobs for sample

  GET          /api/v1/samples/{id}/results   Aggregated Module 1 results for sample

  GET          /api/v1/samples/{id}/files     List associated genome files
  ------------ ------------------------------ ------------------------------------------------------------------------

**7.1 Sample Create Request Schema**

> {
>
> \"project_id\": \"uuid\", // required
>
> \"isolate_name\": \"E.coli_ICU_01\", // required, unique within project
>
> \"species\": \"Escherichia coli\", // recommended
>
> \"species_taxid\": 562, // optional; looked up if species provided
>
> \"host\": \"human\", // optional
>
> \"collection_date\":\"2025-05-15\", // optional, ISO date
>
> \"source_type\": \"clinical\", // clinical\|environmental\|surveillance
>
> \"location\": \"ICU Ward 3\", // optional
>
> \"country_code\": \"GBR\", // optional, ISO 3166-1 alpha-3
>
> \"metadata\": {\"ward\":\"ICU\",\"patient_id\":\"ANON-001\"} // optional KV pairs

**7.2 Bulk Upload (POST /api/v1/samples/bulk-upload)**

Accepts multipart/form-data with a CSV manifest file. CSV columns: isolate_name (required), species, host, collection_date, source_type, location, country_code, plus any metadata\_ prefixed columns.

> {
>
> \"status\": \"success\",
>
> \"data\": {
>
> \"created\": 45,
>
> \"failed\": 2,
>
> \"errors\": \[{\"row\": 12, \"field\": \"collection_date\", \"message\": \"Invalid date format\"}\]
>
> }
>
> }
>
> **SECTION 8 --- FILE UPLOAD API**

  ------------ -------------------------------------------- -------------------------------------------------------------
  **Method**   **Path**                                     **Description**

  POST         /api/v1/files/upload                         Upload genome FASTA file (multipart); returns file_id

  POST         /api/v1/files/upload/init                    Initialise chunked upload; returns upload_id and chunk URLs

  PUT          /api/v1/files/upload/{upload_id}/chunk/{n}   Upload individual chunk (n = 0-based index)

  POST         /api/v1/files/upload/{upload_id}/complete    Finalise chunked upload; triggers checksum verification

  GET          /api/v1/files/{id}                           File metadata (name, size, checksum, status)

  GET          /api/v1/files/{id}/download                  Redirect to presigned download URL (TTL 1 hour)

  DELETE       /api/v1/files/{id}                           Delete file from storage (RESTRICTED if analysis exists)
  ------------ -------------------------------------------- -------------------------------------------------------------

**8.1 Standard Upload (≤ 100 MB)**

> POST /api/v1/files/upload
>
> Content-Type: multipart/form-data
>
> Form fields:
>
> file: \[binary FASTA content\] // required
>
> sample_id: \"uuid\" // required --- associates file to sample
>
> file_type: \"assembly_fasta\" // assembly_fasta\|consensus_fasta\|contigs_fasta
>
> checksum: \"sha256hex\" // optional; if provided, verified server-side

**8.2 File Response Schema**

> {
>
> \"status\": \"success\",
>
> \"data\": {
>
> \"file_id\": \"uuid\",
>
> \"filename\": \"assembly.fasta\",
>
> \"file_size_bytes\": 4823049,
>
> \"checksum_sha256\": \"a3b4c5\...\",
>
> \"upload_status\": \"COMPLETE\", // PENDING\|SCANNING\|COMPLETE\|FAILED
>
> \"storage_path\": \"uploads/{sample_id}/assembly.fasta\",
>
> \"uploaded_at\": \"2025-06-01T10:05:00Z\"
>
> }
>
> }

**8.3 Chunked Upload Flow**

  ------------------- ------------------------------------------------------------------------------ -----------------------------------------------------------------
  **Step**            **Request**                                                                    **Response**

  1\. Initialise      POST /files/upload/init {sample_id, filename, file_size_bytes, total_chunks}   {upload_id, chunk_size, expires_at}

  2\. Upload chunks   PUT /files/upload/{upload_id}/chunk/{n} \[binary chunk body\]                  {chunk_n, checksum_received, status: \"received\"}

  3\. Complete        POST /files/upload/{upload_id}/complete {chunks_checksums:\[\]}                {file_id, checksum_verified: true, upload_status: \"COMPLETE\"}

  Retry chunk         Re-PUT any chunk (idempotent by chunk number)                                  Overwrites previous chunk; no error if already received
  ------------------- ------------------------------------------------------------------------------ -----------------------------------------------------------------

**8.4 File Validation Rules**

-   File extension: .fasta, .fa, .fna, .fasta.gz, .fa.gz only.

-   Maximum file size: 2 GB (configurable per deployment).

-   FASTA character validation: nucleotide characters only (A,C,G,T,N,U,R,Y,S,W,K,M,B,D,H,V and IUPAC ambiguity codes).

-   Minimum sequence length: 200 bp (rejects phage-scale or test sequences unless override flag set).

-   Malware / ClamAV scan initiated asynchronously after upload; file status remains SCANNING until complete.

> **SECTION 9 --- GENOME VALIDATION API**

  ------------ ------------------------------------------- ---------------------------------------------------
  **Method**   **Path**                                    **Description**

  POST         /api/v1/module1/validate                    Submit genome validation job

  GET          /api/v1/module1/validate/{job_id}           Get validation job status

  GET          /api/v1/module1/validate/{job_id}/results   Get full validation results with assembly metrics
  ------------ ------------------------------------------- ---------------------------------------------------

**9.1 Validation Request**

> {
>
> \"sample_id\": \"uuid\", // required
>
> \"file_id\": \"uuid\", // required --- must be in COMPLETE state
>
> \"config\": { \"min_length_bp\": 200000, \"max_contig_count\": 2000 } // optional overrides

**9.2 Validation Result Response**

> {
>
> \"status\": \"success\",
>
> \"data\": {
>
> \"job_id\": \"uuid\",
>
> \"sample_id\": \"uuid\",
>
> \"validation_status\": \"PASSED_WITH_WARNINGS\",
>
> \"metrics\": {
>
> \"total_length_bp\": 4823049,
>
> \"contig_count\": 142,
>
> \"n50_bp\": 87423,
>
> \"gc_percent\": 50.7,
>
> \"n_percent\": 0.02,
>
> \"longest_contig\": 241337,
>
> \"species_prediction\": \"Escherichia coli\",
>
> \"species_confidence\": 0.9987
>
> },
>
> \"warnings\": \[{\"code\":\"HIGH_CONTIG_COUNT\",\"message\":\"142 contigs exceeds recommended 100\",\"threshold\":100,\"observed\":142}\],
>
> \"errors\": \[\]
>
> }
>
> }
>
> **SECTION 10 --- AMR DETECTION API**

  ------------ -------------------------------------------------------- --------------------------------------------
  **Method**   **Path**                                                 **Description**

  POST         /api/v1/module1/amr-detection                            Submit AMR detection job

  GET          /api/v1/module1/amr-detection/{job_id}                   Poll job status and progress

  GET          /api/v1/module1/amr-detection/{job_id}/results           Retrieve full AMR gene inventory

  GET          /api/v1/module1/amr-detection/{job_id}/results/summary   Summary: gene count by drug class

  GET          /api/v1/samples/{id}/amr-genes                           All AMR genes for a sample across all jobs
  ------------ -------------------------------------------------------- --------------------------------------------

**10.1 AMR Detection Request**

> {
>
> \"sample_id\": \"uuid\", // required
>
> \"assembly_id\": \"uuid\", // required
>
> \"tools\": \[\"CARD\",\"AMRFinderPlus\",\"ResFinder\",\"Abricate\"\], // optional override
>
> \"identity_threshold\": 80.0, // optional; default from project settings
>
> \"coverage_threshold\": 80.0 // optional; default from project settings

**10.2 AMR Gene Result Schema (per gene)**

> {
>
> \"amr_gene_id\": \"uuid\",
>
> \"gene_name\": \"blaCTX-M-15\",
>
> \"gene_family\": \"CTX-M beta-lactamase\",
>
> \"aro_accession\": \"ARO:3000016\",
>
> \"drug_class\": \"cephalosporin\",
>
> \"antibiotic_class\": \"beta-lactam\",
>
> \"mechanism_type\": \"antibiotic_inactivation\",
>
> \"confidence_tier\": \"HIGH\",
>
> \"confidence_score\": 0.9821,
>
> \"hits\": \[
>
> {
>
> \"detection_tool\": \"CARD\",
>
> \"hit_category\": \"Perfect\",
>
> \"identity_pct\": 100.0,
>
> \"coverage_pct\": 100.0,
>
> \"contig_id\": \"NODE_1_length_241337\",
>
> \"contig_start\": 14523,
>
> \"contig_end\": 15322,
>
> \"strand\": \"+\",
>
> \"bit_score\": 1643.2,
>
> \"e_value\": 0.0
>
> }
>
> \]
>
> }
>
> **SECTION 11 --- MUTATION DETECTION API**

  ------------ -------------------------------------------- ------------------------------------------
  **Method**   **Path**                                     **Description**

  POST         /api/v1/module1/mutations                    Submit mutation detection job

  GET          /api/v1/module1/mutations/{job_id}           Poll job status

  GET          /api/v1/module1/mutations/{job_id}/results   Full mutation inventory with evidence

  GET          /api/v1/samples/{id}/mutations               All resistance mutations for a sample
  ------------ -------------------------------------------- ------------------------------------------

**11.1 Mutation Result Schema (per mutation)**

> {
>
> \"mutation_id\": \"uuid\",
>
> \"gene_name\": \"gyrA\",
>
> \"position\": 83,
>
> \"ref_amino_acid\":\"Ser\",
>
> \"alt_amino_acid\":\"Leu\",
>
> \"codon_change\": \"TCG→TTG\",
>
> \"mutation_type\": \"SNP\",
>
> \"clinical_significance\": \"resistance\",
>
> \"associated_drug\": \"fluoroquinolone\",
>
> \"confidence_score\": 0.9450,
>
> \"evidence\": \[
>
> {\"type\":\"in_vitro\",\"level\":1,\"pmid\":\"12345678\",\"description\":\"\...\"}
>
> \]
>
> }
>
> **SECTION 12 --- MECHANISM CLASSIFICATION API**

  ------------ --------------------------------------------- ------------------------------------------------------------------------------
  **Method**   **Path**                                      **Description**

  POST         /api/v1/module1/mechanisms                    Submit mechanism classification (usually auto-triggered after AMR detection)

  GET          /api/v1/module1/mechanisms/{job_id}           Poll status

  GET          /api/v1/module1/mechanisms/{job_id}/results   Classified mechanisms with gene associations

  GET          /api/v1/samples/{id}/mechanisms               All classified mechanisms for a sample
  ------------ --------------------------------------------- ------------------------------------------------------------------------------

**12.1 Mechanism Result Schema**

> {
>
> \"mechanism_id\": \"uuid\",
>
> \"class\": \"antibiotic_inactivation\",
>
> \"name\": \"Class A beta-lactamase\",
>
> \"aro_accession\": \"ARO:0010001\",
>
> \"drug_classes\": \[\"cephalosporin\",\"penicillin\",\"monobactam\"\],
>
> \"confidence\": 0.97,
>
> \"associated_genes\":\[{\"gene_name\":\"blaCTX-M-15\",\"amr_gene_id\":\"uuid\"}\]
>
> }
>
> **SECTION 13 --- PHENOTYPE PREDICTION API**

  ------------ -------------------------------------------------- ------------------------------------------
  **Method**   **Path**                                           **Description**

  POST         /api/v1/module1/predict                            Submit phenotype prediction job

  GET          /api/v1/module1/predict/{job_id}                   Poll status

  GET          /api/v1/module1/predict/{job_id}/results           Full S/I/R predictions per antibiotic

  GET          /api/v1/module1/predict/{job_id}/results/summary   Resistance profile heatmap-ready summary

  GET          /api/v1/samples/{id}/predictions                   Latest predictions for a sample
  ------------ -------------------------------------------------- ------------------------------------------

**13.1 Prediction Request**

> {
>
> \"sample_id\": \"uuid\",
>
> \"breakpoint_source\":\"EUCAST\", // EUCAST \| CLSI
>
> \"organism_group\": \"Enterobacterales\" // optional; inferred from species if omitted

**13.2 Prediction Result Schema (per antibiotic)**

> {
>
> \"prediction_id\": \"uuid\",
>
> \"antibiotic\": \"ceftriaxone\",
>
> \"antibiotic_class\": \"cephalosporin\",
>
> \"predicted_sir\": \"R\", // S \| I \| R \| U (undetermined)
>
> \"confidence_score\": 0.9640,
>
> \"confidence_tier\": \"HIGH\",
>
> \"breakpoint_source\": \"EUCAST\",
>
> \"breakpoint_version\":\"2025.1\",
>
> \"is_not_testable\": false,
>
> \"interpretation_notes\": \"blaCTX-M-15 (Perfect hit, 100% identity/coverage) confers resistance to all 3GC\",
>
> \"supporting_genes\": \[{\"gene_name\":\"blaCTX-M-15\",\"contribution_weight\":0.95}\],
>
> \"supporting_mutations\": \[\],
>
> \"supporting_mechanisms\":\[{\"mechanism\":\"Class A beta-lactamase\",\"contribution_weight\":0.95}\]
>
> }
>
> **SECTION 14 --- VIRULENCE PROFILING API**

  ------------ -------------------------------------------- ------------------------------------------
  **Method**   **Path**                                     **Description**

  POST         /api/v1/module1/virulence                    Submit virulence profiling job

  GET          /api/v1/module1/virulence/{job_id}           Poll status

  GET          /api/v1/module1/virulence/{job_id}/results   Full virulence gene inventory

  GET          /api/v1/samples/{id}/virulence               Latest virulence profile for a sample
  ------------ -------------------------------------------- ------------------------------------------

**14.1 Virulence Result Schema (per gene)**

> {
>
> \"vf_id\": \"uuid\",
>
> \"gene_name\": \"stx1\",
>
> \"vfdb_id\": \"VF0001\",
>
> \"function_category\": \"toxin\",
>
> \"function_description\": \"Shiga toxin type 1 --- AB5 toxin targeting host ribosomes\",
>
> \"detection_tool\": \"VFDB\",
>
> \"identity_pct\": 99.1,
>
> \"coverage_pct\": 100.0,
>
> \"contig_id\": \"NODE_5_length_52341\",
>
> \"confidence_score\": 0.9910
>
> }
>
> **SECTION 15 --- REPORT GENERATION API**

  ------------ -------------------------------------- -----------------------------------------------
  **Method**   **Path**                               **Description**

  POST         /api/v1/reports/generate               Request report generation for a sample or job

  GET          /api/v1/reports/{report_id}            Report metadata, status, and format list

  GET          /api/v1/reports/{report_id}/download   Redirect to presigned download URL

  GET          /api/v1/samples/{id}/reports           List all reports for a sample

  GET          /api/v1/projects/{id}/reports          List all reports in a project
  ------------ -------------------------------------- -----------------------------------------------

**15.1 Report Generate Request**

> {
>
> \"sample_id\": \"uuid\", // required
>
> \"job_id\": \"uuid\", // optional; defaults to latest completed job
>
> \"report_type\": \"full_report\", // amr_summary\|phenotype_report\|virulence_report\|full_report
>
> \"formats\": \[\"JSON\",\"TSV\",\"PDF\"\] // default: all three

**15.2 Report Metadata Response**

> {
>
> \"status\": \"success\",
>
> \"data\": {
>
> \"report_id\": \"uuid\",
>
> \"sample_id\": \"uuid\",
>
> \"report_type\": \"full_report\",
>
> \"schema_version\": \"v1.0\",
>
> \"pipeline_version\":\"1.2.0\",
>
> \"status\": \"READY\",
>
> \"generated_at\": \"2025-06-01T10:30:00Z\",
>
> \"files\": \[
>
> {\"format\":\"JSON\",\"file_size_bytes\":84920,\"download_url\":\"/reports/{id}/download?format=JSON\"},
>
> {\"format\":\"TSV\", \"file_size_bytes\":12400,\"download_url\":\"/reports/{id}/download?format=TSV\"},
>
> {\"format\":\"PDF\", \"file_size_bytes\":205400,\"download_url\":\"/reports/{id}/download?format=PDF\"}
>
> \]
>
> }
>
> }
>
> **SECTION 16 --- WORKFLOW EXECUTION API**

  ------------ ---------------------------------- ---------------------------------------------------
  **Method**   **Path**                           **Description**

  POST         /api/v1/workflow/run               Submit full Module 1 pipeline for a sample

  POST         /api/v1/workflow/cancel/{job_id}   Cancel running or queued job

  POST         /api/v1/workflow/retry/{job_id}    Retry failed job (from last checkpoint)

  GET          /api/v1/workflow/{job_id}          Full job detail including workflow run metadata

  GET          /api/v1/workflow/{job_id}/status   Lightweight status + progress (for polling)

  GET          /api/v1/workflow/{job_id}/steps    List all Nextflow process steps with timings

  GET          /api/v1/workflow/{job_id}/logs     Paginated task logs (latest 500 lines by default)
  ------------ ---------------------------------- ---------------------------------------------------

**16.1 Workflow Run Request**

> {
>
> \"sample_id\": \"uuid\", // required
>
> \"assembly_id\": \"uuid\", // required
>
> \"config\": {} // optional overrides; merged with project settings

**16.2 Job Status Response**

> {
>
> \"status\": \"success\",
>
> \"data\": {
>
> \"job_id\": \"uuid\",
>
> \"sample_id\": \"uuid\",
>
> \"status\": \"RUNNING\",
>
> \"progress_pct\": 62,
>
> \"current_step\": \"PHENOTYPE_PREDICT\",
>
> \"steps_completed\":\[\"VALIDATE\",\"AMR_DETECT\",\"MUTATION_DETECT\",\"MECHANISM_CLASSIFY\"\],
>
> \"steps_remaining\":\[\"PHENOTYPE_PREDICT\",\"VIRULENCE_PROFILE\",\"CONFIDENCE_SCORE\",\"MODULE2_EXPORT\"\],
>
> \"submitted_at\": \"2025-06-01T10:00:00Z\",
>
> \"started_at\": \"2025-06-01T10:00:45Z\",
>
> \"estimated_completion\": \"2025-06-01T10:45:00Z\"
>
> }
>
> }

**16.3 Job State Machine**

> CREATED → QUEUED → RUNNING → COMPLETED
>
> └──(error)──→ FAILED ──(retry)──→ QUEUED
>
> └──(cancel)─→ CANCELLED

  ----------- ------------------------------------------ --------------------------------------
  **State**   **Description**                            **Allowed Transitions**

  QUEUED      In Redis queue; awaiting worker            → RUNNING, → CANCELLED

  RUNNING     Celery worker active; Nextflow executing   → COMPLETED, → FAILED, → CANCELLED

  COMPLETED   All steps succeeded; reports generated     Terminal

  FAILED      Step failed after max retries              → QUEUED (via retry endpoint)

  CANCELLED   User or admin cancelled                    Terminal
  ----------- ------------------------------------------ --------------------------------------

> **SECTION 17 --- WEBSOCKET ARCHITECTURE**

**17.1 WebSocket Endpoint**

> WSS /api/v1/ws/jobs/{job_id}
>
> WSS /api/v1/ws/projects/{project_id} // project-level feed (all job events in project)
>
> Authorization: Bearer {access_token} // in query param ?token= or first message

**17.2 Event Payloads**

  ------------------ -------------------------------- --------------------------------------------------------------------------------
  **Event**          **Trigger**                      **Payload Fields**

  job_created        Job registered in DB             job_id, sample_id, status, submitted_at

  job_started        Celery worker picked up job      job_id, started_at, queue_name

  job_progress       Nextflow step completed          job_id, progress_pct, current_step, steps_completed\[\], step_duration_seconds

  job_completed      All steps succeeded              job_id, completed_at, duration_seconds, report_ids\[\]

  job_failed         Step failed after max retries    job_id, failed_at, error_code, error_message, failed_step

  report_generated   Report file written to storage   report_id, report_type, formats\[\], download_urls{}

  job_cancelled      User or admin cancelled          job_id, cancelled_at, cancelled_by
  ------------------ -------------------------------- --------------------------------------------------------------------------------

**17.3 Message Envelope**

> {
>
> \"event\": \"job_progress\",
>
> \"job_id\": \"uuid\",
>
> \"timestamp\": \"2025-06-01T10:25:00Z\",
>
> \"payload\": {
>
> \"progress_pct\": 62,
>
> \"current_step\": \"PHENOTYPE_PREDICT\",
>
> \"steps_completed\": \[\"VALIDATE\",\"AMR_DETECT\",\"MUTATION_DETECT\",\"MECHANISM_CLASSIFY\"\],
>
> \"step_duration_seconds\": 147
>
> }
>
> }

**17.4 Reconnect and Authentication Logic**

-   Client sends token as first text frame immediately after connection: {\"type\":\"auth\",\"token\":\"Bearer eyJ\...\"}

-   Server responds: {\"type\":\"auth_ok\",\"connection_id\":\"uuid\"} or closes with 4001 Unauthorized.

-   Automatic reconnect: client implements exponential back-off (1s, 2s, 4s, 8s, max 60s).

-   Server sends {\"type\":\"ping\"} every 30 seconds; client responds {\"type\":\"pong\"}. Idle connections closed after 90s.

-   On reconnect, client sends last_event_timestamp to receive missed events (server buffers 5 minutes of events per connection).

> **SECTION 18 --- REQUEST VALIDATION (PYDANTIC SCHEMAS)**

**18.1 Base Schemas**

> \# schemas/base.py
>
> from pydantic import BaseModel, ConfigDict
>
> from datetime import datetime
>
> from uuid import UUID
>
> class APIResponse(BaseModel):
>
> status: Literal\[\"success\", \"error\"\]
>
> data: Any \| None = None
>
> meta: dict \| None = None
>
> errors: list\[dict\] \| None = None
>
> request_id: UUID \| None = None

**18.2 Sample Create Schema**

> class SampleCreateRequest(BaseModel):
>
> model_config = ConfigDict(strict=True)
>
> project_id: UUID
>
> isolate_name: str = Field(min_length=1, max_length=200)
>
> species: str \| None = Field(default=None, max_length=200)
>
> species_taxid: int \| None = Field(default=None, gt=0)
>
> host: str \| None = Field(default=None, max_length=100)
>
> collection_date: date \| None = None
>
> source_type: Literal\[\"clinical\",\"environmental\",\"surveillance\"\] \| None = None
>
> location: str \| None = Field(default=None, max_length=200)
>
> country_code: str \| None = Field(default=None, pattern=r\"\^\[A-Z\]{3}\$\")
>
> metadata: dict\[str, str \| int \| float\] = {}
>
> \@field_validator(\"isolate_name\")
>
> \@classmethod
>
> def sanitise_name(cls, v: str) -\> str:
>
> return v.strip()

**18.3 AMR Detection Request Schema**

> class AMRDetectionRequest(BaseModel):
>
> sample_id: UUID
>
> assembly_id: UUID
>
> tools: list\[Literal\[\"CARD\",\"AMRFinderPlus\",\"ResFinder\",\"Abricate\"\]\] = \[
>
> \"CARD\",\"AMRFinderPlus\",\"ResFinder\",\"Abricate\"\]
>
> identity_threshold: float = Field(default=80.0, ge=50.0, le=100.0)
>
> coverage_threshold: float = Field(default=80.0, ge=50.0, le=100.0)

**18.4 Pagination Schema**

> class PaginationParams(BaseModel):
>
> page: int = Field(default=1, ge=1)
>
> page_size: int = Field(default=20, ge=1, le=200)
>
> sort: str = \"created_at\"
>
> order: Literal\[\"asc\",\"desc\"\] = \"desc\"
>
> **SECTION 19 --- ERROR HANDLING STANDARD**

**19.1 Standard Error Envelope**

> {
>
> \"status\": \"error\",
>
> \"error_code\": \"VALIDATION_ERROR\", // machine-readable; see catalogue below
>
> \"message\": \"Request validation failed\", // human-readable summary
>
> \"details\": \[ // optional; validation specifics
>
> {\"field\":\"identity_threshold\",\"message\":\"Value must be between 50.0 and 100.0\",\"value\":45.0}
>
> \],
>
> \"request_id\": \"uuid\", // correlates with server logs
>
> \"docs_url\": \"https://docs.amrplatform.io/api/errors/VALIDATION_ERROR\"

**19.2 HTTP Status Code and Error Code Catalogue**

  ----------------- ----------------------- ------------------------------------------------------------------------
  **HTTP Status**   **error_code**          **Scenario**

  400               VALIDATION_ERROR        Pydantic schema validation failure; field-level details in details\[\]

  400               INVALID_FASTA           Uploaded file is not valid FASTA format

  400               ASSEMBLY_TOO_SHORT      Assembly below minimum length threshold

  400               FILE_SCAN_PENDING       File upload still being virus scanned; retry after delay

  401               UNAUTHORIZED            Missing or malformed Authorization header

  401               TOKEN_EXPIRED           JWT access token has expired; refresh required

  401               TOKEN_REVOKED           Token has been revoked (logout or rotation)

  403               FORBIDDEN               Authenticated but insufficient permissions for this resource

  403               PROJECT_ACCESS_DENIED   User not a member of the requested project

  404               SAMPLE_NOT_FOUND        sample_id does not exist or is soft-deleted

  404               JOB_NOT_FOUND           job_id does not exist or belongs to different project

  404               FILE_NOT_FOUND          file_id not found or already deleted

  409               DUPLICATE_JOB           Identical job already queued/running for this sample (idempotency)

  409               SAMPLE_HAS_REPORTS      Cannot delete sample with existing reports

  422               UNPROCESSABLE_ENTITY    Request is syntactically valid but semantically invalid

  429               RATE_LIMIT_EXCEEDED     Request rate limit exceeded; Retry-After header provided

  500               INTERNAL_ERROR          Unhandled server error; request_id for support reference

  502               WORKFLOW_UNAVAILABLE    Nextflow execution service unreachable

  503               DATABASE_UNAVAILABLE    PostgreSQL connection pool exhausted or unreachable
  ----------------- ----------------------- ------------------------------------------------------------------------

> **SECTION 20 --- LOGGING AND AUDITING**

**20.1 Request Log Schema (structlog JSON)**

> {
>
> \"timestamp\": \"2025-06-01T10:05:23.412Z\",
>
> \"level\": \"INFO\",
>
> \"event\": \"api_request\",
>
> \"request_id\": \"uuid\", // injected by middleware; present on every log line
>
> \"trace_id\": \"uuid\", // OpenTelemetry trace ID
>
> \"user_id\": \"uuid \| null\",
>
> \"project_id\": \"uuid \| null\",
>
> \"method\": \"POST\",
>
> \"path\": \"/api/v1/module1/amr-detection\",
>
> \"status_code\": 202,
>
> \"duration_ms\": 143,
>
> \"ip\": \"10.0.1.45\",
>
> \"user_agent\": \"amr-cli/1.0.0\"

**20.2 Audit Log Events**

  ---------------------- ----------------------------- -----------------------------------------------
  **Event Type**         **Trigger**                   **Fields Captured**

  user_login             Successful POST /auth/login   user_id, ip, user_agent, timestamp

  user_login_failed      ≥ 3 failed login attempts     email_attempted, ip, attempt_count, timestamp

  sample_created         POST /samples                 user_id, project_id, sample_id, isolate_name

  file_uploaded          POST /files/upload complete   user_id, file_id, sample_id, checksum

  job_submitted          POST /workflow/run            user_id, job_id, sample_id, config_snapshot

  report_downloaded      GET /reports/{id}/download    user_id, report_id, format, ip

  project_member_added   POST /projects/{id}/members   actor_id, target_user_id, role, project_id

  api_token_created      POST /users/{id}/api-tokens   user_id, token_name, scopes

  sample_deleted         DELETE /samples/{id}          user_id, sample_id, project_id, reason
  ---------------------- ----------------------------- -----------------------------------------------

**20.3 Correlation ID Propagation**

-   X-Request-ID header accepted from client; if absent, server generates UUID and injects it.

-   Request ID included in every log line, every error response, and all downstream Celery task logs.

-   X-Trace-ID propagated to Nextflow tasks via environment variable for end-to-end distributed tracing.

> **SECTION 21 --- OPENAPI DESIGN**

**21.1 Tag Structure**

  ------------------- --------------------------- ----------------------------------------------
  **Tag**             **Endpoints**               **Description**

  auth                /auth/\*                    Authentication and session management

  users               /users/\*                   User profile and role management

  projects            /projects/\*                Project CRUD, membership, settings

  samples             /samples/\*                 Sample registration, metadata, bulk upload

  files               /files/\*                   Genome file upload, download, management

  genome-validation   /module1/validate/\*        FASTA validation and assembly metrics

  amr-detection       /module1/amr-detection/\*   AMR gene detection results

  mutations           /module1/mutations/\*       Resistance mutation detection

  mechanisms          /module1/mechanisms/\*      Resistance mechanism classification

  phenotype           /module1/predict/\*         Phenotype (S/I/R) prediction

  virulence           /module1/virulence/\*       Virulence factor profiling

  workflow            /workflow/\*                Job submission, status, cancellation

  reports             /reports/\*                 Report generation and download

  admin               /admin/\*                   Reference database management, system health
  ------------------- --------------------------- ----------------------------------------------

**21.2 OpenAPI Document Header**

> openapi: \"3.1.0\"
>
> info:
>
> title: \"AMR Platform --- Module 1 API\"
>
> version: \"1.0.0\"
>
> description: \"REST API for AMR Characterisation Engine\"
>
> contact:
>
> name: \"AMR Platform Engineering\"
>
> email: \"api@amrplatform.io\"
>
> servers:
>
> \- url: \"https://api.amrplatform.io/api/v1\"
>
> description: \"Production\"
>
> \- url: \"https://staging-api.amrplatform.io/api/v1\"
>
> description: \"Staging\"
>
> **SECTION 22 --- PERFORMANCE DESIGN**

**22.1 Pagination Standard**

> GET /api/v1/samples?page=2&page_size=50&sort=created_at&order=desc
>
> Response meta:
>
> {
>
> \"pagination\": {
>
> \"page\": 2, \"page_size\": 50,
>
> \"total_items\": 1247, \"total_pages\": 25,
>
> \"has_next\": true, \"has_previous\": true,
>
> \"links\": {
>
> \"first\": \"/api/v1/samples?page=1&page_size=50\",
>
> \"prev\": \"/api/v1/samples?page=1&page_size=50\",
>
> \"next\": \"/api/v1/samples?page=3&page_size=50\",
>
> \"last\": \"/api/v1/samples?page=25&page_size=50\"
>
> }
>
> }
>
> }

**22.2 Performance Controls**

  ------------------------ ------------------------------------------------------------------------------------------------------ ----------------------------------------------------------------------
  **Control**              **Implementation**                                                                                     **Default / Limit**

  Pagination               page + page_size on all list endpoints; cursor-based for \> 10k rows                                   Default 20; max 200

  Filtering                Query params per resource: species=, status=, date_from=, date_to=, search=                            All filterable fields indexed

  Sorting                  sort= (field) + order= (asc\|desc)                                                                     Default: created_at desc

  Field selection          ?fields=id,name,status --- sparse fieldset support on large responses                                  Optional on heavy endpoints

  Response caching         ETag + Last-Modified on GET responses for reference data; Cache-Control: max-age=300 for DB versions   Cache-Control per endpoint

  Rate limiting            Redis sliding window counter per user_id + IP                                                          1000 req/hr authenticated; 100 req/hr unauthenticated; 20 uploads/hr

  Compression              gzip/br encoding on all responses \> 1 KB                                                              Accept-Encoding: gzip; br

  Async execution          All bioinformatics endpoints return 202 Accepted immediately with job_id; no synchronous blocking      \< 100ms for submission

  Large result streaming   GET /samples/{id}/amr-genes returns paginated; TSV download is streamed via StreamingResponse          Streaming for \> 1000 genes
  ------------------------ ------------------------------------------------------------------------------------------------------ ----------------------------------------------------------------------

> **SECTION 23 --- TESTING STRATEGY**

**23.1 Test Layers**

  ------------------- ------------------------------------------------ --------------------------------------------------------------------------- -----------------------------------------------
  **Layer**           **Framework**                                    **Scope**                                                                   **Target Coverage**

  Unit Tests          pytest + unittest.mock                           Individual service functions, Pydantic validators, business logic           ≥ 90% line coverage

  Integration Tests   pytest + TestClient (FastAPI) + testcontainers   Full endpoint tests against real PostgreSQL + Redis in Docker               ≥ 80% endpoint coverage

  Contract Tests      schemathesis (OpenAPI fuzzing)                   Auto-generate tests from OpenAPI spec; verify all responses match schemas   100% schema compliance

  Security Tests      bandit (SAST) + OWASP ZAP (DAST)                 SQL injection, JWT bypass, IDOR, rate limit bypass, auth bypass             Zero High/Critical findings

  Performance Tests   locust                                           Upload throughput, result retrieval latency under load                      \< 200ms p95 for GET; \< 100ms for submission

  Load Tests          k6                                               100 concurrent users, 500 samples/hour batch scenario                       Zero 5xx; p99 \< 2s
  ------------------- ------------------------------------------------ --------------------------------------------------------------------------- -----------------------------------------------

**23.2 Key Integration Test Scenarios**

-   Full happy path: register → upload FASTA → validate → submit workflow → poll until COMPLETED → download PDF report.

-   Auth flow: register → login → use access token → expire token → use refresh → logout → verify token revoked.

-   Idempotency: submit identical workflow twice with same idempotency-key → second returns first job_id.

-   Permission boundary: VIEWER role cannot POST to /module1/amr-detection → verify 403 with FORBIDDEN.

-   Large file: upload 500 MB FASTA via chunked upload → verify checksum → trigger validation → COMPLETED.

-   Failed job retry: inject Celery failure → verify FAILED state → POST /workflow/retry → verify QUEUED → COMPLETED.

-   Rate limit: exceed 1000 req/hr → verify 429 + Retry-After header → verify counter resets after window.

> **SECTION 24 --- FINAL DELIVERABLES**

**24.1 Complete Endpoint Catalogue**

  -------- ------------ --------------------------------------------- --------------- ------------
  **\#**   **Method**   **Path**                                      **Auth**        **Async**

  1        POST         /api/v1/auth/register                         None            No

  2        POST         /api/v1/auth/login                            None            No

  3        POST         /api/v1/auth/logout                           JWT             No

  4        POST         /api/v1/auth/refresh                          Refresh Token   No

  5        GET          /api/v1/auth/me                               JWT             No

  6        GET          /api/v1/users                                 JWT+ADMIN       No

  7        GET          /api/v1/users/{id}                            JWT             No

  8        PUT          /api/v1/users/{id}                            JWT             No

  9        PATCH        /api/v1/users/{id}/status                     JWT+ADMIN       No

  10       DELETE       /api/v1/users/{id}                            JWT+ADMIN       No

  11       POST         /api/v1/projects                              JWT             No

  12       GET          /api/v1/projects                              JWT             No

  13       GET          /api/v1/projects/{id}                         JWT+Member      No

  14       PUT          /api/v1/projects/{id}                         JWT+Owner       No

  15       DELETE       /api/v1/projects/{id}                         JWT+Owner       No

  16       POST         /api/v1/projects/{id}/members                 JWT+Owner       No

  17       DELETE       /api/v1/projects/{id}/members/{uid}           JWT+Owner       No

  18       GET          /api/v1/projects/{id}/settings                JWT+Owner       No

  19       PUT          /api/v1/projects/{id}/settings                JWT+Owner       No

  20       POST         /api/v1/samples                               JWT+Member      No

  21       GET          /api/v1/samples                               JWT+Member      No

  22       GET          /api/v1/samples/{id}                          JWT+Member      No

  23       PUT          /api/v1/samples/{id}                          JWT+Member      No

  24       DELETE       /api/v1/samples/{id}                          JWT+Member      No

  25       POST         /api/v1/samples/bulk-upload                   JWT+Member      No

  26       GET          /api/v1/samples/{id}/results                  JWT+Member      No

  27       POST         /api/v1/files/upload                          JWT+Member      No

  28       POST         /api/v1/files/upload/init                     JWT+Member      No

  29       PUT          /api/v1/files/upload/{uid}/chunk/{n}          JWT+Member      No

  30       POST         /api/v1/files/upload/{uid}/complete           JWT+Member      No

  31       GET          /api/v1/files/{id}/download                   JWT+Member      No

  32       DELETE       /api/v1/files/{id}                            JWT+Member      No

  33       POST         /api/v1/module1/validate                      JWT+Member      Yes (202)

  34       GET          /api/v1/module1/validate/{jid}                JWT+Member      No

  35       GET          /api/v1/module1/validate/{jid}/results        JWT+Member      No

  36       POST         /api/v1/module1/amr-detection                 JWT+Member      Yes (202)

  37       GET          /api/v1/module1/amr-detection/{jid}/results   JWT+Member      No

  38       POST         /api/v1/module1/mutations                     JWT+Member      Yes (202)

  39       GET          /api/v1/module1/mutations/{jid}/results       JWT+Member      No

  40       POST         /api/v1/module1/mechanisms                    JWT+Member      Yes (202)

  41       GET          /api/v1/module1/mechanisms/{jid}/results      JWT+Member      No

  42       POST         /api/v1/module1/predict                       JWT+Member      Yes (202)

  43       GET          /api/v1/module1/predict/{jid}/results         JWT+Member      No

  44       POST         /api/v1/module1/virulence                     JWT+Member      Yes (202)

  45       GET          /api/v1/module1/virulence/{jid}/results       JWT+Member      No

  46       POST         /api/v1/workflow/run                          JWT+Member      Yes (202)

  47       POST         /api/v1/workflow/cancel/{jid}                 JWT+Member      No

  48       POST         /api/v1/workflow/retry/{jid}                  JWT+Member      No

  49       GET          /api/v1/workflow/{jid}/status                 JWT+Member      No

  50       GET          /api/v1/workflow/{jid}/steps                  JWT+Member      No

  51       GET          /api/v1/workflow/{jid}/logs                   JWT+Member      No

  52       POST         /api/v1/reports/generate                      JWT+Member      Yes (202)

  53       GET          /api/v1/reports/{rid}                         JWT+Member      No

  54       GET          /api/v1/reports/{rid}/download                JWT+Member      No

  55       WSS          /api/v1/ws/jobs/{jid}                         JWT (frame)     Persistent

  56       WSS          /api/v1/ws/projects/{pid}                     JWT (frame)     Persistent
  -------- ------------ --------------------------------------------- --------------- ------------


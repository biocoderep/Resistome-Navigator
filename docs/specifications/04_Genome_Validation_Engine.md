# 04 — Genome Validation Engine

> **MVP Implementation Note:** Implement core validation only. Advanced analyses are Phase 2.

| Section | Feature | Phase |
|---------|---------|-------|
| 3 — Input Validation | FASTA structure, IUPAC chars | 🟢 MVP |
| 4 — File Integrity | MD5/SHA256, file size | 🟢 MVP |
| 5 — Assembly Statistics | N50, GC%, contig count | 🟢 MVP |
| 6 — GC Content Analysis | GC%, per-contig GC | 🟢 MVP |
| 7 — Ambiguous Base Analysis | N%, N-run detection | 🟢 MVP |
| 8 — Contig Analysis | Fragmentation classification | 🟢 MVP |
| 9 — Duplicate Contig Detection | MinHash similarity | 🟡 Phase 2 |
| 10 — Sequence Complexity | Shannon entropy | 🟡 Phase 2 |
| 11 — K-mer Analysis | k-mer spectra, coverage estimate | 🟡 Phase 2 |
| 13 — Taxonomic Consistency | Mash species prediction | 🟡 Phase 2 |
| 14 — Contamination Screening | GC deviation, k-mer anomalies | 🟡 Phase 2 |

> **🟢 MVP Validation Output:** `validation_status.json` with PASS/WARNING/FAIL, basic assembly metrics, GC%, N%, contig count.

---

**GENOME VALIDATION ENGINE**

**TECHNICAL DESIGN SPECIFICATION**

**MODULE 1A --- AMR CHARACTERISATION ENGINE**

*First Analytical Stage of the AMR Platform Pipeline*

Python · FastAPI · PostgreSQL · Celery · Nextflow DSL2 · BioPython

Version 1.0 --- CONFIDENTIAL --- Direct Implementation Ready

> **SECTION 1 --- PURPOSE AND SCOPE**

**1.1 Purpose**

The Genome Validation Engine (GVE) is the mandatory first analytical gate of Module 1. Every uploaded bacterial genome FASTA must pass through the GVE before any downstream AMR analysis is permitted. The engine evaluates genome assembly integrity, quality, completeness, and suitability to ensure reliable AMR gene detection, mutation calling, and phenotype prediction.

**1.2 Validation Gate Principle**

> **Critical Rule:** No downstream Nextflow process (AMR Detection, Mutation Detection, Mechanism Classification, Phenotype Prediction, Virulence Profiling, Module 2 Export) may execute if the GVE returns a FAIL status. A WARNING status allows pipeline continuation with degraded confidence scores attached to all downstream results.

**1.3 Downstream Dependencies**

  ----------------------------------------- -------------------------------- -----------------------------------------------------------------------------
  **Downstream Module**                     **GVE Requirement**              **Impact of GVE Failure**

  AMR Gene Detection (CARD/AMRFinderPlus)   PASS or WARNING                  FAIL: pipeline halted; WARNING: low confidence tier applied to all AMR hits

  Mutation Detection                        PASS or WARNING                  FAIL: halted; WARNING: mutation confidence capped at MEDIUM

  Mechanism Classification                  PASS (derived from AMR detect)   N/A direct; inherits AMR detect result

  Phenotype Prediction                      PASS (derived from mechanisms)   N/A direct; inherits confidence caps

  Virulence Profiling                       PASS or WARNING                  FAIL: halted; WARNING: low confidence tier applied

  Module 2 Export                           PASS required for full export    WARNING: partial export flagged is_partial=true
  ----------------------------------------- -------------------------------- -----------------------------------------------------------------------------

> **SECTION 2 --- SUPPORTED INPUTS**

**2.1 Accepted File Formats**

  --------------------------- ---------------------------- ----------------------------------------------- ---------------------------------------------
  **Format**                  **Extension(s)**             **Handling**                                    **Notes**

  Uncompressed FASTA          .fasta, .fa, .fna            Direct parse with BioPython SeqIO               Most common assembly output

  Gzip-compressed FASTA       .fasta.gz, .fa.gz, .fna.gz   gzip.open() → BioPython SeqIO                   SPAdes / Flye compressed outputs

  Multi-contig FASTA          Any above extension          All contigs parsed and individually validated   Standard WGS assembly output

  Single-contig (consensus)   .fasta/.fa/.fna              Parsed as 1-contig assembly                     Nanopore medaka consensus, reference-guided

  Contigs file                contigs.fasta (any name)     Same as multi-contig                            SPAdes contigs.fasta output
  --------------------------- ---------------------------- ----------------------------------------------- ---------------------------------------------

**2.2 Rejected Input Types**

-   Raw FASTQ reads --- rejected with error code INPUT_NOT_ASSEMBLED.

-   BAM/SAM files --- rejected with error code UNSUPPORTED_FORMAT.

-   GenBank / EMBL format --- rejected with error code UNSUPPORTED_FORMAT; user directed to convert.

-   Files exceeding 2 GB --- rejected with error code FILE_TOO_LARGE.

-   Password-protected archives --- rejected with error code ENCRYPTED_FILE.

> **SECTION 3 --- INPUT VALIDATION**

**3.1 FASTA Structure Validation**

Performed using BioPython SeqIO with a strict custom parser wrapper. Validation applies to every record in the multi-FASTA file.

  ----------------------- --------------------------------------------------------------------------------------- -------------------------------
  **Check**               **Rule**                                                                                **Error Code on Failure**

  File not empty          File size \> 0 bytes                                                                    FILE_EMPTY

  FASTA format            First non-whitespace character is \"\>\"                                                NOT_FASTA_FORMAT

  Header format           Each record starts with \"\> \" and contains ≥1 non-whitespace character after \"\>\"   MALFORMED_HEADER

  Header uniqueness       No duplicate sequence IDs (first word of header line)                                   DUPLICATE_HEADER

  Sequence present        Every header must be followed by ≥1 sequence line before next header or EOF             EMPTY_SEQUENCE

  Sequence characters     Only IUPAC nucleotide characters allowed (see Section 3.2)                              INVALID_NUCLEOTIDE

  No binary content       All bytes in sequence lines are printable ASCII                                         BINARY_CONTENT

  File encoding           UTF-8 or ASCII only; BOM stripped if present                                            ENCODING_ERROR

  No truncation           File does not end mid-sequence line (gzip EOF check)                                    TRUNCATED_FILE

  Minimum record length   Each contig sequence ≥ 200 bp (configurable)                                            CONTIG_TOO_SHORT
  ----------------------- --------------------------------------------------------------------------------------- -------------------------------

**3.2 Allowed IUPAC Nucleotide Characters**

  ------------------------- ---------------------------- ------------------------------------------------------
  **Character**             **Meaning**                  **Action**

  A, T, G, C                Standard bases               Counted as defined bases

  N                         Any base (ambiguous)         Counted; contributes to N%

  R, Y, S, W, K, M          Two-base ambiguity codes     Accepted; flagged in complexity report

  B, D, H, V                Three-base ambiguity codes   Accepted; flagged in complexity report

  Lowercase a,t,g,c,n\...   Soft-masked bases            Converted to uppercase for all metric calculations

  All other characters      Invalid                      INVALID_NUCLEOTIDE error; line and position reported
  ------------------------- ---------------------------- ------------------------------------------------------

**3.3 Validation Implementation**

> \# genome_validator/input_validator.py
>
> import gzip, re
>
> from Bio import SeqIO
>
> from pathlib import Path
>
> from .models import ValidationResult, ValidationError
>
> IUPAC = set(\"ATGCNRYSWKMBDHVatgcnryswkmbdhv\")
>
> def validate_fasta(file_path: Path) -\> ValidationResult:
>
> errors, warnings = \[\], \[\]
>
> opener = gzip.open if str(file_path).endswith(\".gz\") else open
>
> seen_ids = set()
>
> with opener(file_path, \"rt\", encoding=\"utf-8\", errors=\"strict\") as fh:
>
> for rec in SeqIO.parse(fh, \"fasta\"):
>
> seq_str = str(rec.seq).upper()
>
> if rec.id in seen_ids:
>
> errors.append(ValidationError(code=\"DUPLICATE_HEADER\", contig=rec.id))
>
> seen_ids.add(rec.id)
>
> invalid = set(seq_str) - IUPAC
>
> if invalid:
>
> errors.append(ValidationError(code=\"INVALID_NUCLEOTIDE\",
>
> contig=rec.id, detail=f\"Found: {invalid}\"))
>
> if len(seq_str) \< 200:
>
> warnings.append(ValidationError(code=\"CONTIG_TOO_SHORT\",
>
> contig=rec.id, detail=f\"{len(seq_str)} bp\"))
>
> **SECTION 4 --- FILE INTEGRITY CHECKS**

**4.1 Integrity Calculations**

> \# genome_validator/integrity.py
>
> import hashlib, gzip, os
>
> from pathlib import Path
>
> from dataclasses import dataclass
>
> \@dataclass
>
> class IntegrityReport:
>
> file_path: str
>
> file_size_bytes: int
>
> md5: str
>
> sha256: str
>
> is_gzipped: bool
>
> uncompressed_size: int \| None
>
> record_count: int
>
> encoding: str
>
> def compute_integrity(path: Path) -\> IntegrityReport:
>
> md5h = hashlib.md5()
>
> sha256h = hashlib.sha256()
>
> size = os.path.getsize(path)
>
> with open(path, \"rb\") as f:
>
> for chunk in iter(lambda: f.read(65536), b\"\"):
>
> md5h.update(chunk); sha256h.update(chunk)
>
> is_gz = str(path).endswith(\".gz\")
>
> unc_size = None
>
> if is_gz:
>
> with gzip.open(path, \"rb\") as gz:
>
> unc_size = sum(len(c) for c in iter(lambda: gz.read(65536), b\"\"))

**4.2 Integrity Report Schema (JSON)**

> {
>
> \"file_path\": \"/data/uploads/a3f8b2c1/assembly.fasta.gz\",
>
> \"file_size_bytes\": 1843200,
>
> \"md5\": \"d41d8cd98f00b204e9800998ecf8427e\",
>
> \"sha256\": \"e3b0c44298fc1c149afb\...\",
>
> \"is_gzipped\": true,
>
> \"uncompressed_size\": 4823049,
>
> \"record_count\": 142,
>
> \"encoding\": \"UTF-8\"
>
> **SECTION 5 --- ASSEMBLY STATISTICS ENGINE**

**5.1 Metrics Computed**

  ----------------------- ----------------------------------------------------------------- --------------------------------------------
  **Metric**              **Formula / Method**                                              **Python Implementation**

  Total Assembly Length   Sum of all contig lengths                                         sum(len(r.seq) for r in records)

  Number of Contigs       Count of FASTA records                                            len(records)

  Average Contig Length   total_length / contig_count                                       statistics.mean(lengths)

  Median Contig Length    50th percentile of contig lengths                                 statistics.median(lengths)

  Maximum Contig Length   Longest single contig                                             max(lengths)

  Minimum Contig Length   Shortest single contig                                            min(lengths)

  N50                     Contig length at which 50% of assembly is covered (sorted desc)   Custom n50() function (see below)

  N90                     Contig length at which 90% of assembly is covered                 Custom n_stat(records, 0.90)

  L50                     Number of contigs at N50                                          Custom l50() function

  Assembly Span           Total length including Ns                                         Same as total_length for assembled genomes

  GC Percentage           (G+C) / (A+T+G+C) × 100                                           See Section 6

  N Percentage            N bases / total bases × 100                                       See Section 7
  ----------------------- ----------------------------------------------------------------- --------------------------------------------

**5.2 N50 Implementation**

> def n_stat(lengths: list\[int\], fraction: float) -\> int:
>
> \"\"\"Return Nx statistic (e.g. N50 when fraction=0.5).\"\"\"
>
> sorted_lens = sorted(lengths, reverse=True)
>
> target = sum(sorted_lens) \* fraction
>
> cumsum = 0
>
> for length in sorted_lens:
>
> cumsum += length
>
> if cumsum \>= target:
>
> return length

**5.3 assembly_metrics.json Schema**

> {
>
> \"sample_id\": \"uuid\",
>
> \"assembly_id\": \"uuid\",
>
> \"total_length_bp\": 4823049,
>
> \"contig_count\": 142,
>
> \"mean_contig_bp\": 33965,
>
> \"median_contig_bp\": 18450,
>
> \"max_contig_bp\": 241337,
>
> \"min_contig_bp\": 214,
>
> \"n50_bp\": 87423,
>
> \"n90_bp\": 21340,
>
> \"l50\": 18,
>
> \"gc_percent\": 50.71,
>
> \"n_percent\": 0.03,
>
> \"assembly_span_bp\": 4823049,
>
> \"computed_at\": \"2025-06-01T10:08:32Z\"
>
> **SECTION 6 --- GC CONTENT ANALYSIS**

**6.1 Calculations**

> def gc_analysis(records: list) -\> GCReport:
>
> whole_genome_gc = compute_gc(concat_all_sequences(records))
>
> per_contig = \[{\"id\": r.id, \"length\": len(r.seq),
>
> \"gc_pct\": compute_gc(str(r.seq))} for r in records\]
>
> gc_values = \[c\[\"gc_pct\"\] for c in per_contig\]
>
> mean_gc = statistics.mean(gc_values)
>
> variance = statistics.variance(gc_values) if len(gc_values) \> 1 else 0.0
>
> \# Outlier detection: contigs with GC deviate \> 3 SD from mean
>
> outliers = \[c for c in per_contig if abs(c\[\"gc_pct\"\] - mean_gc) \> 3 \* variance\*\*0.5\]

**6.2 GC Thresholds by Organism Group**

  ---------------------------- ----------------------- --------------------------------------------
  **Organism Group**           **Expected GC Range**   **Flag Condition**

  General bacteria             30--75%                 Warning if whole-genome GC outside 25--75%

  Staphylococcus aureus        32--34%                 Warning if \> 37% or \< 29%

  Escherichia coli             50--52%                 Warning if \> 55% or \< 47%

  Pseudomonas aeruginosa       66--68%                 Warning if \> 72% or \< 62%

  Mycobacterium tuberculosis   65--66%                 Warning if \> 70% or \< 60%

  Unknown species              30--75% (general)       Warning outside range; contamination note
  ---------------------------- ----------------------- --------------------------------------------

**6.3 gc_analysis.json Schema**

> {
>
> \"whole_genome_gc_pct\": 50.71,
>
> \"mean_contig_gc_pct\": 50.68,
>
> \"gc_variance\": 2.14,
>
> \"gc_std_dev\": 1.46,
>
> \"per_contig\": \[{\"id\":\"NODE_1\",\"length\":241337,\"gc_pct\":50.82}, \...\],
>
> \"outlier_contigs\": \[{\"id\":\"NODE_88\",\"length\":4210,\"gc_pct\":28.1,\"deviation_sd\":15.5}\],
>
> \"flag\": \"CONTAMINATION_SUSPECTED\",
>
> \"flag_reason\": \"Contig NODE_88 GC% deviates 15.5 SD from assembly mean\"
>
> **SECTION 7 --- AMBIGUOUS BASE ANALYSIS**

**7.1 N% Calculation and Thresholds**

> def ambiguity_analysis(records: list) -\> AmbiguityReport:
>
> total_bases = sum(len(r.seq) for r in records)
>
> n_count = sum(str(r.seq).upper().count(\"N\") for r in records)
>
> n_pct = (n_count / total_bases) \* 100 if total_bases \> 0 else 0.0
>
> other_ambig = sum( \# IUPAC non-N ambiguity
>
> sum(str(r.seq).upper().count(c) for c in \"RYSWKMBDHV\")
>
> for r in records)

  --------------------------------- --------------- --------------- --------------------
  **Metric**                        **PASS**        **WARNING**     **FAIL**

  N Percentage (whole genome)       \< 1%           1% -- 5%        \> 5%

  Largest N-run in single contig    \< 100 bp       100 -- 500 bp   \> 500 bp

  Number of contigs with \> 10% N   0               1 -- 3          \> 3

  Other IUPAC ambiguity bases       \< 0.1%         0.1 -- 1%       \> 1%
  --------------------------------- --------------- --------------- --------------------

**7.2 ambiguity_report.json Schema**

> {
>
> \"total_bases\": 4823049,
>
> \"n_count\": 1447,
>
> \"n_percent\": 0.030,
>
> \"n_status\": \"PASS\",
>
> \"longest_n_run\": {\"contig\":\"NODE_7\",\"run_length\":42,\"position\":18450},
>
> \"per_contig_n\": \[{\"id\":\"NODE_1\",\"n_count\":0,\"n_pct\":0.0}, \...\],
>
> \"other_ambiguity_pct\": 0.001
>
> **SECTION 8 --- CONTIG ANALYSIS**

**8.1 Contig Quality Thresholds**

  ------------------------------------- --------------- ---------------- --------------- ---------------
  **Metric**                            **Excellent**   **Acceptable**   **Poor**        **Failed**

  Contig Count                          \< 100          100 -- 300       300 -- 1000     \> 1000

  N50 (for 5 Mb genome)                 \> 100 kbp      50 -- 100 kbp    20 -- 50 kbp    \< 20 kbp

  Longest Contig                        \> 500 kbp      100 -- 500 kbp   50 -- 100 kbp   \< 50 kbp

  Min Contig Length (after filtering)   \> 1000 bp      500 -- 1000 bp   200 -- 500 bp   \< 200 bp
  ------------------------------------- --------------- ---------------- --------------- ---------------

**8.2 Fragmentation Detection**

> def classify_fragmentation(contig_count: int, n50_bp: int, genome_size_mb: float) -\> str:
>
> \# Adjust thresholds by genome size (larger genomes expect more contigs)
>
> adjusted_threshold = 100 \* (genome_size_mb / 5.0)
>
> if contig_count \< adjusted_threshold and n50_bp \> 100_000:
>
> return \"EXCELLENT\"
>
> elif contig_count \< adjusted_threshold \* 3 and n50_bp \> 50_000:
>
> return \"ACCEPTABLE\"
>
> elif contig_count \< adjusted_threshold \* 10:
>
> return \"POOR\"
>
> else: return \"HIGHLY_FRAGMENTED\"

**8.3 contig_report.json Schema**

> {
>
> \"contig_count\": 142,
>
> \"fragmentation_class\": \"ACCEPTABLE\",
>
> \"length_distribution\": {
>
> \"0-500\": 3, \"500-1000\": 8, \"1000-5000\": 24,
>
> \"5000-10000\": 31, \"10000-50000\": 52, \"\>50000\": 24
>
> },
>
> \"short_contig_count_below_500bp\": 3
>
> **SECTION 9 --- DUPLICATE CONTIG DETECTION**

**9.1 Detection Methods**

  -------------------- ---------------------------------------- ---------------------------------------------- ---------------------------------
  **Method**           **Use Case**                             **Implementation**                             **Threshold**

  Exact hash match     Identical sequence duplicates            hashlib.sha256 of normalised sequence string   Exact match = DUPLICATE

  MinHash similarity   Near-identical contigs (≥ 95% similar)   datasketch MinHash (k=21, num_perm=128)        Jaccard ≥ 0.95 = NEAR_DUPLICATE

  Length + GC filter   Pre-filter for expensive comparison      Group contigs by length ± 5% and GC ± 2%       Applied before MinHash
  -------------------- ---------------------------------------- ---------------------------------------------- ---------------------------------

**9.2 Implementation**

> from datasketch import MinHash
>
> def minhash_contig(seq: str, num_perm=128, k=21) -\> MinHash:
>
> mh = MinHash(num_perm=num_perm)
>
> for i in range(len(seq) - k + 1):
>
> mh.update(seq\[i:i+k\].encode(\"utf-8\"))
>
> return mh

**9.3 duplicate_contig_report.json Schema**

> {
>
> \"exact_duplicates\": \[{\"contig_a\":\"NODE_44\",\"contig_b\":\"NODE_88\",\"type\":\"EXACT\"}\],
>
> \"near_duplicates\": \[{\"contig_a\":\"NODE_21\",\"contig_b\":\"NODE_67\",\"jaccard\":0.97,\"type\":\"NEAR\"}\],
>
> \"total_duplicate_pairs\": 2,
>
> \"recommendation\": \"Remove duplicates before AMR analysis to avoid inflated gene counts\"
>
> **SECTION 10 --- SEQUENCE COMPLEXITY ANALYSIS**

**10.1 Shannon Entropy**

Shannon entropy H = −Σ p(x) log₂ p(x) where p(x) = frequency of base x. Calculated per contig over sliding 100 bp windows.

  ------------------------- --------------------- --------------------------------------------------------------------
  **Shannon Entropy (H)**   **Classification**    **Interpretation**

  H ≥ 1.80                  HIGH_COMPLEXITY       Normal bacterial sequence; AMR analysis reliable

  1.50 ≤ H \< 1.80          MEDIUM_COMPLEXITY     Moderate repetition; acceptable; note in report

  1.20 ≤ H \< 1.50          LOW_COMPLEXITY        Significant repetition; reduce confidence for affected contigs

  H \< 1.20                 VERY_LOW_COMPLEXITY   High homopolymer / repeat; likely assembly artefact or contaminant
  ------------------------- --------------------- --------------------------------------------------------------------

**10.2 Homopolymer Detection**

> def find_homopolymers(seq: str, min_run=10) -\> list\[dict\]:
>
> import re
>
> runs = \[\]
>
> for base in \"ATGCN\":
>
> for m in re.finditer(f\"{base}{{{min_run},}}\", seq.upper()):
>
> runs.append({\"base\":base,\"start\":m.start(),\"end\":m.end(),\"length\":len(m.group())})
>
> return sorted(runs, key=lambda x: x\[\"length\"\], reverse=True)

**10.3 complexity_report.json Schema**

> {
>
> \"mean_shannon_entropy\": 1.91,
>
> \"min_contig_entropy\": 1.43,
>
> \"low_complexity_contigs\": \[{\"id\":\"NODE_99\",\"entropy\":1.43,\"reason\":\"AAAAAAA repeat\"}\],
>
> \"total_homopolymer_runs\": 12,
>
> \"longest_homopolymer\": {\"base\":\"A\",\"length\":22,\"contig\":\"NODE_12\",\"position\":44210}
>
> **SECTION 11 --- K-MER ANALYSIS**

**11.1 K-mer Spectrum Generation**

> from collections import Counter
>
> def kmer_spectrum(sequences: list\[str\], k: int) -\> dict:
>
> counter = Counter()
>
> for seq in sequences:
>
> s = seq.upper()
>
> for i in range(len(s) - k + 1):
>
> kmer = s\[i:i+k\]
>
> if \"N\" not in kmer: \# skip k-mers spanning Ns
>
> counter\[kmer\] += 1
>
> total = sum(counter.values())
>
> unique = len(counter)
>
> once = sum(1 for v in counter.values() if v == 1) \# error k-mers
>
> return {\"k\":k,\"total\":total,\"unique\":unique,\"singleton_pct\":once/total\*100}

**11.2 Contamination Signal from K-mer Analysis**

  ---------------------------------- ------------------------------------------- ---------------------------------------------------
  **Signal**                         **Detection Method**                        **Classification**

  Bimodal k-mer frequency            Two distinct peaks in frequency histogram   Possible mixed-species contamination

  Very high singleton %              Singletons \> 80% of unique k-mers          Low coverage / assembly errors

  Unexpected high-frequency k-mers   k-mers with freq \> 3× mean frequency       Repeat regions or contamination

  Coverage depth estimate            Peak of k-mer frequency distribution        Expected 20--200× for WGS; \< 5× warns INCOMPLETE
  ---------------------------------- ------------------------------------------- ---------------------------------------------------

**11.3 kmer_report.json Schema**

> {
>
> \"k21\": {\"total_kmers\":4721843,\"unique_kmers\":4410211,\"singleton_pct\":12.4,\"coverage_estimate\":1.07},
>
> \"k31\": {\"total_kmers\":4700284,\"unique_kmers\":4380192,\"singleton_pct\":11.9,\"coverage_estimate\":1.07},
>
> \"k51\": {\"total_kmers\":4658123,\"unique_kmers\":4300100,\"singleton_pct\":13.1,\"coverage_estimate\":1.08},
>
> \"contamination_signals\": \[\],
>
> \"assembly_completeness_estimate\": \"HIGH\"
>
> **SECTION 12 --- GENOME SIZE VALIDATION**

**12.1 Expected Size Ranges**

  ------------------------- -------------------- ---------------------------------------------------
  **Classification**        **Expected Range**   **Action if Outside Range**

  General bacteria          0.5 -- 15 Mb         WARNING; continue with contamination check

  Mycoplasma / Ureaplasma   0.5 -- 1.0 Mb        Species-specific: acceptable if species confirmed

  E. coli / Salmonella      4.5 -- 5.8 Mb        WARNING if \< 4.0 or \> 6.5 Mb

  S. aureus                 2.7 -- 3.0 Mb        WARNING if \< 2.5 or \> 3.5 Mb

  P. aeruginosa             6.0 -- 7.0 Mb        WARNING if \< 5.5 or \> 8.0 Mb

  K. pneumoniae             5.0 -- 6.5 Mb        WARNING if \< 4.5 or \> 7.5 Mb

  Too small (universal)     \< 0.5 Mb            FAIL: INCOMPLETE_ASSEMBLY or wrong organism

  Too large (universal)     \> 15 Mb             FAIL: likely contamination or eukaryotic DNA
  ------------------------- -------------------- ---------------------------------------------------

**12.2 genome_size_report.json Schema**

> {
>
> \"assembly_size_mb\": 4.823,
>
> \"expected_min_mb\": 4.0,
>
> \"expected_max_mb\": 6.5,
>
> \"size_status\": \"PASS\",
>
> \"size_percentile_for_species\": 42.0
>
> **SECTION 13 --- TAXONOMIC CONSISTENCY CHECK**

**13.1 Check Logic**

If species metadata was provided at sample registration, the GVE compares computed assembly characteristics against species-specific expected ranges. If no species is provided, a Mash sketch-based species prediction is attempted.

  ------------------------- --------------------------------------------------------------- -----------------------------------------------------------------------
  **Check**                 **Data Source**                                                 **Flag Condition**

  GC% vs expected range     species_gc_ranges table (seeded from NCBI RefSeq stats)         WARNING if deviation \> 5 percentage points

  Genome size vs expected   species_size_ranges table                                       WARNING if outside ± 20% of median for species

  Contig count vs typical   species_assembly_stats table                                    INFO if contig count \> 3× typical for species

  Mash species prediction   Mash sketch against RefSeq bacterial database (≥1000 genomes)   WARNING if predicted species ≠ registered species (confidence ≥ 0.95)
  ------------------------- --------------------------------------------------------------- -----------------------------------------------------------------------

**13.2 taxonomy_consistency_report.json Schema**

> {
>
> \"registered_species\": \"Escherichia coli\",
>
> \"mash_predicted_species\":\"Escherichia coli\",
>
> \"mash_confidence\": 0.9987,
>
> \"mash_distance\": 0.0013,
>
> \"gc_expected_range\": \[50.0, 52.0\],
>
> \"gc_observed\": 50.71,
>
> \"gc_consistent\": true,
>
> \"size_expected_range_mb\":\[4.5, 5.8\],
>
> \"size_observed_mb\": 4.823,
>
> \"size_consistent\": true,
>
> \"taxonomy_status\": \"CONSISTENT\"
>
> **SECTION 14 --- CONTAMINATION SCREENING**

**14.1 Contamination Signals Matrix**

  --------------------------- ---------------------------------------------------- ------------ --------------------------------------------
  **Signal**                  **Detection Method**                                 **Weight**   **Threshold**

  GC outlier contigs          Contigs with GC deviate \> 3 SD from assembly mean   High         ≥ 1 outlier contig → MODERATE risk

  Bimodal GC distribution     Hartigans dip test on per-contig GC histogram        High         p \< 0.05 → MODERATE risk

  K-mer frequency anomalies   Bimodal k-mer spectrum                               High         Detected → MODERATE risk

  Length outlier contigs      Contigs \> 3 SD from mean length AND different GC    Medium       ≥ 2 contigs → LOW risk

  Low-complexity spikes       Isolated very-low-entropy contigs (\< 1.2)           Medium       ≥ 1 contig → LOW risk

  Genome size \> 8 Mb         Total assembly size                                  Medium       \> 10 Mb → HIGH risk (possible eukaryotic)

  Taxonomy mismatch           Mash prediction ≠ registered species                 High         Mismatch confidence ≥ 0.95 → HIGH risk
  --------------------------- ---------------------------------------------------- ------------ --------------------------------------------

**14.2 Contamination Risk Classification**

  ---------------- ---------------------------------------------- -----------------------------------------------------------
  **Risk Level**   **Criteria**                                   **Pipeline Action**

  LOW_RISK         0--1 low-weight signals                        Proceed; note in report

  MODERATE_RISK    ≥ 1 high-weight signal OR ≥ 3 low signals      Proceed with WARNING; confidence capped at MEDIUM

  HIGH_RISK        ≥ 2 high-weight signals OR taxonomy mismatch   FAIL; require user review and acknowledgement to override
  ---------------- ---------------------------------------------- -----------------------------------------------------------

**14.3 contamination_report.json Schema**

> {
>
> \"risk_level\": \"LOW_RISK\",
>
> \"signals_detected\": 0,
>
> \"signals\": \[\],
>
> \"gc_outlier_contigs\": \[\],
>
> \"bimodal_gc\": false,
>
> \"taxonomy_mismatch\": false,
>
> \"recommendation\": \"No contamination signals detected. Proceed with analysis.\"
>
> **SECTION 15 --- QUALITY SCORING ENGINE**

**15.1 Composite Score Formula**

Quality Score Q = Σ (weight_i × component_score_i), normalised to 0--100.

  ----------------------------- ------------ -------------------------------------------------------------------- ----------------
  **Component**                 **Weight**   **Score Method**                                                     **Max Points**

  N50 relative to genome size   25%          100 × min(N50 / (genome_size_bp × 0.02), 1.0)                        25

  Contig count score            20%          100 × max(0, 1 − (contig_count / 1000))                              20

  N% score                      20%          100 if N% \< 1%; 60 if 1--5%; 0 if \> 5%                             20

  GC consistency                10%          100 if PASS; 60 if WARN (deviation 2--5 SD); 0 if species mismatch   10

  Contamination score           15%          100 if LOW_RISK; 60 if MODERATE; 0 if HIGH_RISK                      15

  Complexity score              5%           100 × (mean_entropy / 2.0) capped at 100                             5

  Assembly size score           5%           100 if size in expected range; 50 if WARN; 0 if FAIL                 5
  ----------------------------- ------------ -------------------------------------------------------------------- ----------------

**15.2 Quality Classification**

  ----------------- -------------------- ------------------------------------------------------------------
  **Score Range**   **Classification**   **Pipeline Decision**

  85 -- 100         EXCELLENT            PASS --- proceed; full confidence scores applied

  70 -- 84          GOOD                 PASS --- proceed; standard confidence scores applied

  55 -- 69          ACCEPTABLE           WARNING --- proceed; confidence scores capped at MEDIUM

  40 -- 54          POOR                 WARNING --- proceed with strong caveat; confidence capped at LOW

  \< 40             FAILED               FAIL --- halt pipeline; user review required
  ----------------- -------------------- ------------------------------------------------------------------

**15.3 quality_score.json Schema**

> {
>
> \"overall_score\": 87.4,
>
> \"classification\": \"EXCELLENT\",
>
> \"components\": {
>
> \"n50_score\": 23.2,
>
> \"contig_score\": 18.6,
>
> \"n_percent_score\": 20.0,
>
> \"gc_consistency\": 10.0,
>
> \"contamination\": 15.0,
>
> \"complexity\": 4.8,
>
> \"size_score\": 5.0
>
> },
>
> \"computed_at\": \"2025-06-01T10:09:14Z\"
>
> **SECTION 16 --- PASS / FAIL DECISION ENGINE**

**16.1 Decision Rules**

  ------------------------ --------------------------------------- -------------- -----------------------------------------------------------------------------------
  **Rule**                 **Condition**                           **Decision**   **Override Allowed**

  Critical FASTA error     Any FAIL-level input validation error   FAIL           No --- hard block

  Genome too small         Assembly \< 0.5 Mb                      FAIL           No --- hard block

  Genome too large         Assembly \> 15 Mb                       FAIL           Admin override only

  N% too high              N% \> 5%                                FAIL           Yes --- user can acknowledge and override to WARNING

  High contamination       contamination_risk = HIGH_RISK          FAIL           Yes --- user acknowledgement required; override adds OVERRIDE flag to all results

  Quality score failed     overall_score \< 40                     FAIL           Yes --- user acknowledgement; all downstream results flagged QUALITY_OVERRIDE

  N% warning               N% 1--5%                                WARNING        N/A --- auto-proceed

  Moderate contamination   contamination_risk = MODERATE_RISK      WARNING        N/A --- auto-proceed

  Poor quality             overall_score 40--54                    WARNING        N/A --- auto-proceed

  All checks passed        No FAILs; quality ≥ 55                  PASS           N/A
  ------------------------ --------------------------------------- -------------- -----------------------------------------------------------------------------------

**16.2 validation_status.json Schema**

> {
>
> \"sample_id\": \"uuid\",
>
> \"assembly_id\": \"uuid\",
>
> \"status\": \"PASS\", // PASS \| WARNING \| FAIL
>
> \"quality_class\": \"EXCELLENT\",
>
> \"quality_score\": 87.4,
>
> \"fail_reasons\": \[\],
>
> \"warnings\": \[\],
>
> \"override_status\": null, // null \| USER_OVERRIDE \| ADMIN_OVERRIDE
>
> \"override_by\": null,
>
> \"override_at\": null,
>
> \"proceed_to_amr\": true,
>
> \"confidence_cap\": \"FULL\" // FULL \| MEDIUM \| LOW (based on warnings)
>
> **SECTION 17 --- DATABASE INTEGRATION**

**17.1 Table Mappings**

  --------------------------- ----------------------------- --------------------------------------------------------------------------------- --------------------------------------------------------------------------
  **Output Data**             **Table**                     **Key Columns**                                                                   **Notes**

  Assembly metadata           assemblies                    id, sample_id, assembler, assembly_version                                        Created on file upload; updated with validated_fasta_path after GVE PASS

  Assembly statistics         assembly_metrics              assembly_id, total_length_bp, contig_count, n50_bp, gc_percent, n_percent, \...   Inserted after statistics engine completes

  Validation report           validation_reports            assembly_id, job_id, validation_status, warnings JSONB, errors JSONB              One row per GVE run (reruns create new row)

  Quality score               assembly_metrics (extended)   quality_score, quality_classification, confidence_cap                             Added as columns on assembly_metrics; single row per assembly

  GC analysis (extended)      assembly_metrics              gc_percent, gc_variance, gc_outlier_contigs JSONB                                 GC detail stored as JSONB; per-contig in separate JSON file

  Contamination report        assembly_metrics              contamination_risk, contamination_signals JSONB                                   Risk level stored as enum; signals as JSONB array

  File integrity              sample_files                  checksum_sha256, file_size_bytes, upload_status                                   Updated from SCANNING to COMPLETE after GVE integrity check

  Validation status (final)   samples.status                status = VALID \| INVALID \| VALID_WITH_WARNINGS                                  Updated on GVE completion; drives pipeline gate

  Override records            audit_logs                    action=VALIDATION_OVERRIDE, before_state, after_state                             Immutable record of any user/admin override
  --------------------------- ----------------------------- --------------------------------------------------------------------------------- --------------------------------------------------------------------------

**17.2 Additional Column Additions to assembly_metrics**

> ALTER TABLE assembly_metrics ADD COLUMN IF NOT EXISTS
>
> quality_score NUMERIC(5,2),
>
> quality_classification VARCHAR(20),
>
> confidence_cap VARCHAR(20) DEFAULT \'FULL\',
>
> contamination_risk VARCHAR(20),
>
> contamination_signals JSONB,
>
> gc_outlier_contigs JSONB,
>
> gc_variance NUMERIC(8,4),
>
> duplicate_pairs INTEGER DEFAULT 0,
>
> mean_shannon_entropy NUMERIC(6,4),
>
> kmer_coverage_estimate NUMERIC(8,2),
>
> taxonomy_status VARCHAR(30);
>
> **SECTION 18 --- FASTAPI DESIGN**

**18.1 Endpoints**

  ------------ -------------------------------------------- ------------------------------------------ ---------------------------------------------------------------
  **Method**   **Path**                                     **Response**                               **Description**

  POST         /api/v1/module1/validate                     202 Accepted {job_id}                      Submit genome validation job; returns immediately with job_id

  GET          /api/v1/module1/validate/{job_id}            200 {status, progress_pct, current_step}   Poll job status and progress

  GET          /api/v1/module1/validate/{job_id}/results    200 {all sub-reports}                      Full validation results (all JSON sub-reports merged)

  GET          /api/v1/module1/validate/{job_id}/report     302 Redirect to PDF URL                    Download PDF validation report

  POST         /api/v1/module1/validate/{job_id}/override   200 {new_status}                           ADMIN/Owner: override FAIL to WARNING with justification
  ------------ -------------------------------------------- ------------------------------------------ ---------------------------------------------------------------

**18.2 Submit Endpoint --- Request Schema**

> class ValidationRequest(BaseModel):
>
> model_config = ConfigDict(strict=True)
>
> sample_id: UUID
>
> file_id: UUID \# must be in upload_status=COMPLETE
>
> assembly_id: UUID \| None = None \# auto-created if None
>
> config: ValidationConfig = ValidationConfig()
>
> class ValidationConfig(BaseModel):
>
> min_length_bp: int = Field(default=200_000, ge=10_000, le=1_000_000)
>
> max_contig_count: int = Field(default=2000, ge=1, le=50_000)
>
> n_fail_threshold: float = Field(default=5.0, ge=1.0, le=50.0)
>
> n_warn_threshold: float = Field(default=1.0, ge=0.1, le=5.0)
>
> run_kmer_analysis: bool = True

**18.3 Submit Endpoint --- Response Schema**

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
> \"assembly_id\": \"uuid\",
>
> \"status\": \"QUEUED\",
>
> \"submitted_at\":\"2025-06-01T10:00:00Z\",
>
> \"estimated_duration_seconds\": 120
>
> }
>
> }

**18.4 Results Endpoint --- Response Schema**

> {
>
> \"job_id\": \"uuid\",
>
> \"validation_status\": \"PASS\",
>
> \"quality_score\": 87.4,
>
> \"quality_class\": \"EXCELLENT\",
>
> \"proceed_to_amr\": true,
>
> \"confidence_cap\": \"FULL\",
>
> \"assembly_metrics\": { \...assembly_metrics.json content\... },
>
> \"gc_analysis\": { \...gc_analysis.json content\... },
>
> \"ambiguity_report\": { \...ambiguity_report.json content\... },
>
> \"contig_report\": { \...contig_report.json content\... },
>
> \"complexity_report\": { \...complexity_report.json content\... },
>
> \"contamination_report\": { \...contamination_report.json content\... },
>
> \"quality_score_detail\": { \...quality_score.json content\... },
>
> \"taxonomy_report\": { \...taxonomy_consistency_report.json content\... },
>
> \"report_files\": \[{\"format\":\"JSON\",\"url\":\"\...\"}, {\"format\":\"PDF\",\"url\":\"\...\"}\]
>
> **SECTION 19 --- CELERY TASK DESIGN**

**19.1 Task Architecture**

> \# tasks/genome_validation_task.py
>
> from celery import Task
>
> from app.celery_app import celery
>
> from genome_validator import GenomeValidationEngine
>
> \@celery.task(
>
> bind=True, name=\"module1.validate_genome\",
>
> max_retries=3,
>
> default_retry_delay=30,
>
> soft_time_limit=1800, \# 30 min; kills task if exceeded
>
> time_limit=2100, \# 35 min hard kill
>
> track_started=True,
>
> )
>
> def validate_genome_task(self, job_id: str, config: dict) -\> dict:
>
> engine = GenomeValidationEngine(job_id=job_id, config=config)
>
> try:
>
> self.update_state(state=\"RUNNING\", meta={\"progress\": 0, \"step\": \"LOADING\"})
>
> result = engine.run(progress_callback=lambda p,s: self.update_state(
>
> state=\"RUNNING\", meta={\"progress\": p, \"step\": s}))
>
> return {\"status\": \"COMPLETED\", \"result\": result}
>
> except Exception as exc:
>
> raise self.retry(exc=exc, countdown=60 \* (self.request.retries + 1))

**19.2 Task Progress Steps**

  ------------------- ---------------- ----------------------------------------------------
  **Step Name**       **Progress %**   **Description**

  LOADING             0--5             Load FASTA from storage; decompress if gzipped

  INTEGRITY_CHECK     5--10            SHA256 / MD5 computation; record count

  INPUT_VALIDATION    10--20           FASTA structure; nucleotide character validation

  STATISTICS          20--30           Total length, contig stats, N50/N90/L50

  GC_ANALYSIS         30--40           Whole genome and per-contig GC; outlier detection

  AMBIGUITY           40--45           N% computation; N-run detection

  CONTIG_ANALYSIS     45--50           Fragmentation classification; length distribution

  DUPLICATES          50--58           Hash and MinHash duplicate detection

  COMPLEXITY          58--65           Shannon entropy; homopolymer detection

  KMER                65--75           k-mer spectrum (k=21,31,51); contamination signals

  GENOME_SIZE         75--80           Size range validation against expected

  TAXONOMY            80--85           Mash species prediction and consistency check

  CONTAMINATION       85--90           Risk aggregation across all signals

  QUALITY_SCORE       90--95           Composite score computation

  DECISION            95--98           PASS/WARNING/FAIL determination

  REPORT_GENERATION   98--100          JSON/TSV/PDF report assembly; DB write
  ------------------- ---------------- ----------------------------------------------------

> **SECTION 20 --- NEXTFLOW DSL2 PROCESS DESIGN**

**20.1 Process Specification**

> process GENOME_VALIDATION {
>
> tag \"\${meta.sample_id}\"
>
> label \"process_medium\"
>
> cpus 2
>
> memory \"4 GB\"
>
> time \"30.min\"
>
> container \"amr-platform/genome-validator:1.0.0\"
>
> input:
>
> tuple val(meta), path(fasta)
>
> // meta: \[sample_id, job_id, assembly_id, species, config_json\]
>
> output:
>
> tuple val(meta), path(\"validation_report.json\"), emit: validation_report
>
> tuple val(meta), path(\"assembly_metrics.json\"), emit: assembly_metrics
>
> tuple val(meta), path(\"gc_analysis.json\"), emit: gc_analysis
>
> tuple val(meta), path(\"ambiguity_report.json\"), emit: ambiguity
>
> tuple val(meta), path(\"contig_report.json\"), emit: contig_report
>
> tuple val(meta), path(\"duplicate_contig_report.json\"), emit: duplicates
>
> tuple val(meta), path(\"complexity_report.json\"), emit: complexity
>
> tuple val(meta), path(\"kmer_report.json\"), emit: kmer
>
> tuple val(meta), path(\"genome_size_report.json\"), emit: genome_size
>
> tuple val(meta), path(\"taxonomy_consistency_report.json\"),emit: taxonomy
>
> tuple val(meta), path(\"contamination_report.json\"), emit: contamination
>
> tuple val(meta), path(\"quality_score.json\"), emit: quality_score
>
> tuple val(meta), path(\"validation_status.json\"), emit: status
>
> tuple val(meta), path(\"final_validation_report.pdf\"), emit: pdf_report
>
> script:
>
> \"\"\"
>
> genome-validate \\
>
> \--input \${fasta} \\
>
> \--sample-id \${meta.sample_id} \\
>
> \--job-id \${meta.job_id} \\
>
> \--species \"\${meta.species ?: \"\"}\" \\
>
> \--config \"\${meta.config_json}\" \\
>
> \--output-dir . \\
>
> \--threads \${task.cpus}
>
> \"\"\"
>
> }
>
> // Gate process: only emit if validation PASS or WARNING
>
> process VALIDATION_GATE {
>
> tag \"\${meta.sample_id}\"
>
> input:
>
> tuple val(meta), path(status_json)
>
> output:
>
> tuple val(meta), path(status_json), emit: proceed
>
> script:
>
> \"\"\"
>
> python -c \"
>
> import json, sys
>
> s = json.load(open(\'\${status_json}\'))\[\'status\'\]
>
> sys.exit(0 if s in \[\'PASS\',\'WARNING\'\] else 1)
>
> \"
>
> \"\"\"

**20.2 Subworkflow Integration**

> workflow VALIDATION_SUBWORKFLOW {
>
> take: ch_raw_input // tuple(meta, fasta)
>
> main:
>
> GENOME_VALIDATION(ch_raw_input)
>
> VALIDATION_GATE(GENOME_VALIDATION.out.status)
>
> emit:
>
> validated = VALIDATION_GATE.out.proceed
>
> assembly_metrics = GENOME_VALIDATION.out.assembly_metrics
>
> all_reports = GENOME_VALIDATION.out.validation_report
>
> **SECTION 21 --- TESTING STRATEGY**

**21.1 Test Suite Structure**

  -------------------------- ------------------------- ---------------------------------------------------------------------- ---------------------------------------------------------------------------------
  **Test Type**              **Framework**             **Scope**                                                              **Key Scenarios**

  Unit Tests                 pytest                    Individual validator functions, metric calculations, scoring formula   ≥ 95% line coverage on genome_validator/ package

  FASTA Validation Tests     pytest + fixtures         All valid and invalid FASTA permutations                               Valid; empty file; binary; duplicate headers; invalid chars; truncated; gzipped

  Metric Calculation Tests   pytest + numpy            N50, GC%, N%, quality score formula                                    Known-answer tests using pre-computed reference assemblies

  Contamination Tests        pytest                    GC outlier detection, k-mer anomaly, taxonomy mismatch                 Synthetic contaminated FASTA files; spike-in foreign sequences

  Integration Tests          pytest + testcontainers   Full FastAPI endpoint → Celery → DB round-trip                         POST validate → poll → COMPLETED; FAIL scenarios; override flow

  Performance Tests          pytest-benchmark          Processing time for 1 Mb, 5 Mb, 15 Mb assemblies                       5 Mb assembly \< 120 seconds end-to-end; 15 Mb \< 300 seconds

  Regression Tests           pytest fixtures           Validate output stability across code changes                          Reference assemblies produce identical quality scores ± 0.01 across versions
  -------------------------- ------------------------- ---------------------------------------------------------------------- ---------------------------------------------------------------------------------

**21.2 Reference Test Assemblies**

  ------------------------------------- ------------- ------------------------ ---------------------------------------
  **Assembly**                          **Species**   **Expected Quality**     **Purpose**

  GCF_000005845.2 (E. coli K-12)        E. coli       EXCELLENT (≥ 85)         High-quality reference; baseline pass

  Synthetic fragmented (1000 contigs)   E. coli       POOR (40--54)            Fragmentation WARNING test

  Synthetic N-rich (8% N)               E. coli       FAILED (N% FAIL)         N% threshold FAIL test

  Synthetic contaminated (GC spike)     E. coli       MODERATE contamination   Contamination detection test

  Synthetic small (0.3 Mb)              Any           FAILED (too small)       Genome size FAIL test

  Synthetic duplicates (5 pairs)        E. coli       WARNING (duplicates)     Duplicate detection test
  ------------------------------------- ------------- ------------------------ ---------------------------------------

> **SECTION 22 --- REPORT GENERATION**

**22.1 Report Formats**

  ---------------- ------------------------------------------- ------------------------------------------------------------------------------------------------- -----------------------------------------------------------------
  **Format**       **Generator**                               **Contents**                                                                                      **Consumer**

  JSON (master)    Python json.dumps; pydantic .model_dump()   All sub-reports merged into single structured document                                            API responses, Module 2 linkage, downstream services

  TSV (tabular)    Python csv.writer (tab delimiter)           Assembly metrics table + AMR summary rows; one row per sample                                     Bioinformaticians, R/Python analysis, surveillance spreadsheets

  PDF (clinical)   WeasyPrint (HTML → PDF) or ReportLab        Formatted report: metrics, GC chart, contig distribution, quality score gauge, PASS/FAIL banner   Clinicians, lab directors, quality review
  ---------------- ------------------------------------------- ------------------------------------------------------------------------------------------------- -----------------------------------------------------------------

**22.2 PDF Report Sections**

-   Page 1 Header: Sample ID, isolate name, analysis date, pipeline version, quality score badge (colour-coded: green/amber/red).

-   Section 1 --- Assembly Statistics Table: total length, contig count, N50, GC%, N%.

-   Section 2 --- GC Distribution Chart: per-contig GC histogram (matplotlib → PNG embedded in PDF).

-   Section 3 --- Contig Length Distribution: bar chart of contig size bins.

-   Section 4 --- Ambiguity and Complexity: N% gauge, Shannon entropy, homopolymer summary.

-   Section 5 --- Contamination Assessment: risk level badge, signals table, outlier contigs list.

-   Section 6 --- Quality Score Breakdown: component score bar chart, overall score, classification.

-   Section 7 --- PASS / WARNING / FAIL Banner: prominent, coloured, with reasons listed.

-   Page Footer: sample_id, job_id, db versions used, operator name, timestamp.

> **SECTION 23 --- FINAL OUTPUT FILES**

  ---------------------------------- ------------ ------------------- ---------------------------------------------------------
  **File**                           **Format**   **Size Estimate**   **Contents**

  validation_report.json             JSON         5--20 KB            Master merged validation report (all sub-reports)

  assembly_metrics.json              JSON         1--2 KB             Total length, contig count, N50, N90, L50, GC%, N%

  gc_analysis.json                   JSON         10--100 KB          Per-contig GC values, outliers, variance, distribution

  ambiguity_report.json              JSON         2--10 KB            N count, N%, per-contig N, N-run locations

  contig_report.json                 JSON         5--20 KB            Length distribution, fragmentation class, contig list

  duplicate_contig_report.json       JSON         1--5 KB             Duplicate pairs, similarity scores

  complexity_report.json             JSON         5--15 KB            Shannon entropy per contig, homopolymer locations

  kmer_report.json                   JSON         2--5 KB             k-mer spectrum summary for k=21,31,51

  genome_size_report.json            JSON         1 KB                Size Mb, expected range, status

  taxonomy_consistency_report.json   JSON         2 KB                Mash prediction, GC consistency, size consistency

  contamination_report.json          JSON         2--5 KB             Risk level, signals, outlier contigs

  quality_score.json                 JSON         1--2 KB             Component scores, overall score, classification

  validation_status.json             JSON         1 KB                Final PASS/WARNING/FAIL; confidence cap; proceed_to_amr

  final_validation_report.pdf        PDF          100--300 KB         Full formatted PDF with charts and tables
  ---------------------------------- ------------ ------------------- ---------------------------------------------------------

> **SECTION 24 --- FINAL DELIVERABLE: IMPLEMENTATION PLAN**

**24.1 Python Package Structure**

> genome_validator/
>
> ├── \_\_init\_\_.py \# GenomeValidationEngine class; public API
>
> ├── cli.py \# genome-validate CLI entrypoint
>
> ├── engine.py \# Orchestrator; calls all sub-validators in sequence
>
> ├── models.py \# Pydantic models for all report schemas
>
> ├── integrity.py \# File integrity (MD5/SHA256, gzip detection)
>
> ├── input_validator.py \# FASTA structure and character validation
>
> ├── statistics.py \# N50, GC%, N%, assembly metrics
>
> ├── gc_analysis.py \# GC per-contig, outlier detection
>
> ├── ambiguity.py \# N% analysis, N-run detection
>
> ├── contig_analysis.py \# Fragmentation classification, distribution
>
> ├── duplicate_detector.py \# Hash + MinHash duplicate detection
>
> ├── complexity.py \# Shannon entropy, homopolymer detection
>
> ├── kmer_analysis.py \# k-mer spectrum (k=21,31,51)
>
> ├── genome_size.py \# Size range validation
>
> ├── taxonomy.py \# Mash sketch, species consistency
>
> ├── contamination.py \# Risk aggregation across signals
>
> ├── quality_scorer.py \# Composite score formula
>
> ├── decision_engine.py \# PASS/WARNING/FAIL determination
>
> ├── report_generator.py \# JSON/TSV/PDF assembly
>
> ├── db_writer.py \# SQLAlchemy DB persistence calls
>
> └── tests/
>
> ├── fixtures/ \# Reference FASTA files for tests
>
> ├── test_input_validator.py
>
> ├── test_statistics.py
>
> ├── test_gc_analysis.py
>
> ├── test_duplicate_detector.py
>
> ├── test_contamination.py
>
> ├── test_quality_scorer.py
>
> └── test_integration.py

**24.2 Dependencies**

  ------------------------ ------------- ---------------------------------------------------
  **Package**              **Version**   **Purpose**

  biopython                ≥ 1.83        FASTA parsing, SeqIO

  datasketch               ≥ 1.6         MinHash for duplicate detection

  numpy                    ≥ 1.26        Array operations for k-mer spectra and statistics

  scipy                    ≥ 1.12        Hartigan\'s dip test for bimodal GC detection

  matplotlib               ≥ 3.8         Chart generation for PDF report (embedded PNG)

  weasyprint               ≥ 62          HTML → PDF report generation

  pydantic                 ≥ 2.6         Schema validation for all report models

  mash (external binary)   ≥ 2.3         Species prediction sketch comparison

  celery                   ≥ 5.3         Async task execution

  sqlalchemy               ≥ 2.0         DB persistence

  pytest                   ≥ 8.0         Test framework

  pytest-benchmark         ≥ 4.0         Performance benchmarks
  ------------------------ ------------- ---------------------------------------------------

**24.3 Docker Container Specification**

> FROM python:3.12-slim
>
> RUN apt-get update && apt-get install -y \\
>
> mash libgomp1 libgfortran5 && \\
>
> rm -rf /var/lib/apt/lists/\*
>
> WORKDIR /app
>
> COPY requirements.txt .
>
> RUN pip install \--no-cache-dir -r requirements.txt
>
> COPY genome_validator/ ./genome_validator/
>
> RUN pip install -e .
>
> USER 1000:1000 \# non-root; UID 1000
>
> ENTRYPOINT \[\"genome-validate\"\]

**24.4 Implementation Phase Checklist**

  -------------------------------- --------------------------------------------------------------------- -------------- ------------------------------------------------------------------------------
  **Phase**                        **Tasks**                                                             **Duration**   **Acceptance Criteria**

  1 --- Core parsing               Input validator, integrity checks, FASTA parsing, statistics engine   3 days         All unit tests pass; 5 Mb FASTA parsed in \< 10s

  2 --- Analysis modules           GC, N%, contig, duplicates, complexity, k-mer                         4 days         Known-answer tests pass for all metrics; reference assembly scores correctly

  3 --- Taxonomy & contamination   Mash integration, taxonomy check, contamination risk aggregation      3 days         Contamination test fixtures produce expected risk levels

  4 --- Scoring & decision         Quality scorer, PASS/FAIL decision engine, override logic             2 days         Quality score formula validated against 6 reference assemblies

  5 --- Report generation          JSON/TSV/PDF report assembly, chart generation                        3 days         PDF renders correctly; all 14 output files generated

  6 --- API & Celery integration   FastAPI endpoints, Celery task, progress tracking, DB writes          3 days         End-to-end integration test: POST → COMPLETED → PDF download

  7 --- Nextflow process           DSL2 GENOME_VALIDATION process, VALIDATION_GATE, subworkflow          2 days         Nextflow pipeline executes in Docker; channels emit correct outputs

  8 --- Testing & hardening        Full test suite, performance benchmarks, regression tests             3 days         ≥ 95% unit coverage; 5 Mb \< 120s; 15 Mb \< 300s; no regressions
  -------------------------------- --------------------------------------------------------------------- -------------- ------------------------------------------------------------------------------
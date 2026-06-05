# 06 — AMR Detection Engine

> **MVP Implementation Note:** Build CARD and AMRFinderPlus integration now. ResFinder and Abricate are Phase 2.

| Section | Tool | Phase |
|---------|------|-------|
| 6 — CARD RGI Integration | CARD RGI (Perfect/Strict/Loose hits) | 🟢 MVP |
| 7 — AMRFinderPlus Integration | NCBI AMRFinderPlus | 🟢 MVP |
| 8 — ResFinder Integration | ResFinder 4.1 | 🟡 Phase 2 |
| 9 — Abricate Integration | Abricate multi-db | 🟡 Phase 2 |
| 10 — Hit Detection Engine | Identity, coverage, bit score | 🟢 MVP |
| 11–15 — Hit Classification | Perfect/Strict/Loose/Nudged | 🟢 MVP |
| 16 — Evidence Aggregation | Cross-database consensus | 🟢 MVP (2-tool version) |
| 17 — Deduplication | Overlap detection, merge | 🟡 Phase 2 (4-tool) |
| 20 — Confidence Scoring | Weighted composite score | 🟢 MVP (simplified) |

> **🟢 MVP Output:** `amr_genes.tsv` and `amr_genes.json` from CARD + AMRFinderPlus with identity, coverage, drug class, and hit type.

---

**AMR DETECTION ENGINE**

**TECHNICAL DESIGN SPECIFICATION**

**MODULE 1C --- AMR CHARACTERISATION ENGINE**

*CARD · AMRFinderPlus · ResFinder · Abricate · ARG-ANNOT*

Python · FastAPI · PostgreSQL · Celery · Nextflow DSL2

Version 1.0 --- CONFIDENTIAL --- Direct Implementation Ready

> **SECTION 1 --- PURPOSE AND SCOPE**

**1.1 Purpose**

The AMR Detection Engine (ADE) is the core biological analysis component of Module 1. It screens assembled bacterial genome FASTA files against multiple curated AMR gene databases, aggregates evidence across tools, deduplicates overlapping hits, and produces a confidence-ranked, ontology-mapped AMR gene inventory that feeds the Mechanism Classification, Phenotype Prediction, and Module 2 Concordance Analysis engines.

**1.2 Pipeline Position**

> **Prerequisite:** The Genome Validation Engine (Module 1A) must return PASS or WARNING before the ADE executes. The validated FASTA path from assembly_metrics.validated_fasta_path is used as input --- never the raw uploaded file.

**1.3 Biological Scope**

  -------------------------------------- -------------------------------------------------------------------- -----------------------
  **Resistance Class**                   **Key Genes Detected**                                               **Clinical Priority**

  Beta-lactams (including carbapenems)   blaTEM, blaSHV, blaCTX-M, blaKPC, blaNDM, blaOXA, blaVIM, blaIMP     CRITICAL

  Fluoroquinolones                       gyrA/B mutations, parC/E mutations, qnrA/B/S, qepA, aac(6\')-Ib-cr   CRITICAL

  Aminoglycosides                        aac(3), aac(6\'), aph(3\'), aph(6), ant(2\'\')                       HIGH

  Macrolides / MLSB                      ermA/B/C, mefA/E, msrA, mph genes                                    HIGH

  Tetracyclines                          tetA/B/C/M/O/X, tet(34), tet(41)                                     HIGH

  Sulfonamides / Trimethoprim            sul1/2/3, dfrA genes                                                 MEDIUM

  Glycopeptides (vancomycin)             vanA/B/C/D/E/G/H/L/M/N                                               CRITICAL

  Polymyxins (colistin)                  mcr-1 through mcr-9, chromosomal mgrB/phoQ/pmrA mutations            CRITICAL

  Rifampicin                             rpoB mutations                                                       HIGH

  Chloramphenicol                        catA/B, cmlA, floR                                                   MEDIUM
  -------------------------------------- -------------------------------------------------------------------- -----------------------

> **SECTION 2 --- SUPPORTED DATABASES**

  ---------------------------- ---------------------------------- --------------------------------------------------------------------- -------------------------------------------- ---------------
  **Database**                 **Version Tracked**                **Scope**                                                             **Hit Types**                                **License**

  CARD (RGI)                   ≥ 3.2.x                            Curated AMR genes and variants + CARD Ontology (ARO)                  Perfect / Strict / Loose / Nudged            CC BY 4.0

  NCBI AMRFinderPlus           ≥ 3.11.x (database ≥ 2024-01-31)   NCBI-curated AMR genes, stress response, virulence                    Gene-based; point mutations; protein BLAST   Public domain

  ResFinder                    ≥ 4.1.x                            Acquired resistance genes; species-specific point mutations           Gene-based (BLAST); PointFinder mutations    Apache 2.0

  Abricate                     ≥ 1.0.x                            Screen of CARD/ResFinder/ARG-ANNOT/NCBI/MEGARES databases via BLAST   BLAST-based (DNA)                            GPL v2

  ARG-ANNOT                    ≥ NT v6                            Antibiotic resistance gene annotation database                        BLAST-based (NT)                             Academic

  NCBI AMR Reference Gene DB   As bundled with AMRFinderPlus      HMM profiles for protein families                                     HMM-based                                    Public domain
  ---------------------------- ---------------------------------- --------------------------------------------------------------------- -------------------------------------------- ---------------

> **SECTION 3 --- DETECTION WORKFLOW**

**3.1 End-to-End Workflow Diagram**

> INPUT: validated_genome.fasta
>
> │
>
> ▼
>
> ┌──────────────────────────────────────────────────────────┐
>
> │ GENOME PARSING ENGINE │
>
> │ contig_registry = \[{id, length, gc_pct, seq_hash}\] │
>
> └──────────────────────────────┬───────────────────────────┘
>
> │ validated FASTA
>
> ┌────────────────────┼──────────────────────────┐
>
> ▼ ▼ ▼
>
> ┌──────────────┐ ┌──────────────────┐ ┌────────────────────┐
>
> │ CARD RGI │ │ AMRFinderPlus │ │ ResFinder + │
>
> │ (Perfect / │ │ (gene + point │ │ Abricate + │
>
> │ Strict / │ │ mutation mode) │ │ ARG-ANNOT │
>
> │ Loose hits) │ └────────┬─────────┘ └─────────┬──────────┘
>
> └──────┬───────┘ │ │
>
> └────────────────────┼────────────────────────┘
>
> │ raw_hits\[\] per tool
>
> ▼
>
> ┌────────────────────────────────────────────────┐
>
> │ HIT VALIDATION & METRICS ENGINE │
>
> │ identity, coverage, bit_score, e_value │
>
> └───────────────────────┬────────────────────────┘
>
> │
>
> ┌───────────────────────▼────────────────────────┐
>
> │ GENE DEDUPLICATION ENGINE │
>
> │ merge overlapping hits; canonical gene call │
>
> └───────────────────────┬────────────────────────┘
>
> │
>
> ┌───────────────────────▼────────────────────────┐
>
> │ EVIDENCE AGGREGATION ENGINE │
>
> │ cross-database consensus; agreement score │
>
> └───────────────────────┬────────────────────────┘
>
> │
>
> ┌──────────────────────┼──────────────────────┐
>
> ▼ ▼ ▼
>
> ┌───────────────┐ ┌──────────────────┐ ┌─────────────────┐
>
> │ ONTOLOGY │ │ DRUG CLASS │ │ MECHANISM │
>
> │ MAPPING │ │ CLASSIFICATION │ │ PRE-ANNOTATION │
>
> └───────┬───────┘ └────────┬─────────┘ └────────┬────────┘
>
> └────────────────────┼─────────────────────-─┘
>
> ▼
>
> ┌─────────────────────────────────────────────────┐
>
> │ CONFIDENCE SCORING ENGINE │
>
> │ composite_score ∈ \[0,1\] → HIGH/MEDIUM/LOW │
>
> └───────────────────────┬─────────────────────────┘
>
> │
>
> OUTPUT: amr_genes.json / amr_genes.tsv / amr_detection_report.pdf
>
> **SECTION 4 --- DATABASE MANAGEMENT ENGINE**

**4.1 Implementation: database_manager.py**

> \"\"\"AMR database lifecycle manager --- Module 1C v1.0.0\"\"\"
>
> import hashlib, subprocess, json
>
> from pathlib import Path
>
> from datetime import datetime
>
> from sqlalchemy.orm import Session
>
> class DatabaseManager:
>
> def \_\_init\_\_(self, db_root: Path, session: Session):
>
> self.db_root = db_root
>
> self.session = session
>
> def download(self, db_name: str, version: str \| None = None) -\> \"DBVersion\":
>
> \"\"\"Download and register a database version.\"\"\"
>
> downloader = self.\_get_downloader(db_name)
>
> dest = self.db_root / db_name / (version or \"latest\")
>
> dest.mkdir(parents=True, exist_ok=True)
>
> downloader.fetch(dest)
>
> checksums = self.\_checksum_directory(dest)
>
> return self.\_register(db_name, version, dest, checksums)
>
> def \_checksum_directory(self, path: Path) -\> dict\[str, str\]:
>
> result = {}
>
> for f in path.rglob(\"\*\"):
>
> if f.is_file():
>
> sha256 = hashlib.sha256(f.read_bytes()).hexdigest()
>
> result\[str(f.relative_to(path))\] = sha256
>
> return result
>
> def verify(self, db_version_id: str) -\> bool:
>
> \"\"\"Re-verify all checksums for a registered DB version.\"\"\"
>
> \...
>
> def activate(self, db_version_id: str):
>
> \"\"\"Set a DB version as active; deactivate previous.\"\"\"
>
> \...
>
> def rollback(self, db_name: str):
>
> \"\"\"Reactivate previous version of a database.\"\"\"

**4.2 Downloader Implementations**

  --------------- ------------------------------------------------------------------------ ----------------------- -----------------------------------------
  **Database**    **Download Method**                                                      **Update Frequency**    **Index Required**

  CARD            Download card-data.tar.gz from card.mcmaster.ca; extract; run rgi load   Irregular (\~monthly)   Yes --- rgi load \--card_json card.json

  AMRFinderPlus   amrfinder \--update (uses NCBI FTP)                                      Monthly                 Yes --- built by amrfinder \--update

  ResFinder       git clone/pull from bitbucket.org/genomicepidemiology/resfinder_db       Irregular               Yes --- python INSTALL.py

  Abricate        abricate \--setupdb (downloads from each configured source)              On demand               Yes --- BLAST makeblastdb per database

  ARG-ANNOT       Direct FASTA download from URMITE website; manual versioning             Infrequent              Yes --- BLAST makeblastdb
  --------------- ------------------------------------------------------------------------ ----------------------- -----------------------------------------

> **SECTION 5 --- GENOME PARSING ENGINE**

**5.1 Implementation: genome_parser.py**

> \"\"\"Genome parser for AMR detection --- Module 1C v1.0.0\"\"\"
>
> import hashlib, gzip
>
> from Bio import SeqIO
>
> from dataclasses import dataclass
>
> from pathlib import Path
>
> \@dataclass
>
> class ContigRecord:
>
> contig_id: str
>
> length: int
>
> gc_pct: float
>
> seq_hash: str \# SHA256 of uppercase sequence
>
> sequence: str \# uppercase, N-replaced
>
> def parse_genome(fasta_path: Path) -\> list\[ContigRecord\]:
>
> opener = gzip.open if str(fasta_path).endswith(\".gz\") else open
>
> records = \[\]
>
> with opener(fasta_path, \"rt\") as fh:
>
> for rec in SeqIO.parse(fh, \"fasta\"):
>
> seq = str(rec.seq).upper()
>
> gc = (seq.count(\"G\") + seq.count(\"C\")) / max(len(seq), 1) \* 100
>
> records.append(ContigRecord(
>
> contig_id = rec.id,
>
> length = len(seq),
>
> gc_pct = round(gc, 3),
>
> seq_hash = hashlib.sha256(seq.encode()).hexdigest(),
>
> sequence = seq))
>
> return records
>
> **SECTION 6 --- CARD RGI INTEGRATION**

**6.1 Implementation: card_adapter.py**

> \"\"\"CARD RGI adapter --- Module 1C v1.0.0\"\"\"
>
> import subprocess, json, tempfile
>
> from pathlib import Path
>
> from .result_models import RawHit
>
> class CARDAdapter:
>
> def \_\_init\_\_(self, card_json: Path, db_version_id: str):
>
> self.card_json = card_json
>
> self.db_version_id = db_version_id
>
> def run(self, fasta: Path, threads: int = 4,
>
> include_loose: bool = True) -\> list\[RawHit\]:
>
> with tempfile.TemporaryDirectory() as tmp:
>
> out_prefix = Path(tmp) / \"rgi_out\"
>
> cmd = \[
>
> \"rgi\", \"main\",
>
> \"\--input_sequence\", str(fasta),
>
> \"\--output_file\", str(out_prefix),
>
> \"\--local\", \"\--clean\",
>
> \"\--num_threads\", str(threads),
>
> \"\--input_type\", \"contig\",
>
> \"\--alignment_tool\", \"BLAST\",
>
> \]
>
> if not include_loose: cmd += \[\"\--exclude_nudge\"\]
>
> subprocess.run(cmd, check=True, capture_output=True, text=True)
>
> return self.\_parse_output(out_prefix.with_suffix(\".txt\"))
>
> def \_parse_output(self, txt_path: Path) -\> list\[RawHit\]:
>
> hits = \[\]
>
> with open(txt_path) as f:
>
> headers = f.readline().strip().split(\"\\t\")
>
> for line in f:
>
> row = dict(zip(headers, line.strip().split(\"\\t\")))
>
> hits.append(RawHit(
>
> tool = \"CARD\",
>
> gene_name = row\[\"Best_Hit_ARO\"\],
>
> aro_accession = row\[\"ARO\"\],
>
> drug_class = row\[\"Drug Class\"\],
>
> resistance_mechanism = row\[\"Resistance Mechanism\"\],
>
> hit_category = row\[\"Cut_Off\"\], \# Perfect/Strict/Loose
>
> identity_pct = float(row\[\"Best_Identities\"\]),
>
> coverage_pct = float(row\[\"%Coverage\"\]),
>
> contig_id = row\[\"Contig\"\],
>
> start = int(row\[\"Start\"\]),
>
> end = int(row\[\"Stop\"\]),
>
> strand = row\[\"Orientation\"\],
>
> db_version_id = self.db_version_id)
>
> )
>
> return hits
>
> **SECTION 7 --- AMRFINDERPLUS INTEGRATION**

**7.1 Implementation: amrfinder_adapter.py**

> \"\"\"AMRFinderPlus adapter --- Module 1C v1.0.0\"\"\"
>
> import subprocess, csv, io
>
> from pathlib import Path
>
> class AMRFinderAdapter:
>
> def \_\_init\_\_(self, db_path: Path, db_version_id: str):
>
> self.db_path = db_path
>
> self.db_version_id = db_version_id
>
> def run(self, fasta: Path, organism: str \| None = None,
>
> threads: int = 4) -\> list\[RawHit\]:
>
> cmd = \[\"amrfinder\", \"\--nucleotide\", str(fasta),
>
> \"\--database\", str(self.db_path),
>
> \"\--threads\", str(threads), \"\--plus\"\]
>
> if organism: cmd += \[\"\--organism\", organism\]
>
> result = subprocess.run(cmd, check=True, capture_output=True, text=True)
>
> return self.\_parse_tsv(result.stdout)
>
> def \_parse_tsv(self, tsv_text: str) -\> list\[RawHit\]:
>
> hits = \[\]
>
> reader = csv.DictReader(io.StringIO(tsv_text), delimiter=\"\\t\")
>
> for row in reader:
>
> if row.get(\"Element type\") not in (\"AMR\", \"STRESS\"): continue
>
> hits.append(RawHit(
>
> tool = \"AMRFinderPlus\",
>
> gene_name = row\[\"Gene symbol\"\],
>
> drug_class = row\[\"Drug class\"\],
>
> identity_pct = float(row\[\"% Identity to reference sequence\"\] or 0),
>
> coverage_pct = float(row\[\"% Coverage of reference sequence\"\] or 0),
>
> contig_id = row\[\"Contig id\"\],
>
> start = int(row\[\"Start\"\] or 0),
>
> end = int(row\[\"Stop\"\] or 0),
>
> strand = row\[\"Strand\"\],
>
> db_version_id = self.db_version_id))
>
> return hits
>
> **SECTION 8 --- RESFINDER AND ABRICATE INTEGRATION**

**8.1 Implementation: resfinder_adapter.py**

> class RESFinderAdapter:
>
> def run(self, fasta: Path, species: str \| None = None) -\> list\[RawHit\]:
>
> cmd = \[\"python\", \"-m\", \"resfinder\",
>
> \"-i\", str(fasta), \"-o\", \"/tmp/resfinder_out\",
>
> \"-s\", species or \"Other\", \"\--acquired\"\]
>
> subprocess.run(cmd, check=True, capture_output=True)
>
> return self.\_parse_resfinder_results(Path(\"/tmp/resfinder_out\"))
>
> def \_parse_resfinder_results(self, out_dir: Path) -\> list\[RawHit\]:
>
> result_file = out_dir / \"ResFinder_results_tab.txt\"
>
> hits = \[\]
>
> with open(result_file) as f:
>
> reader = csv.DictReader(f, delimiter=\"\\t\")
>
> for row in reader:
>
> if row\[\"Phenotype\"\] == \"Unknown\": continue
>
> hits.append(RawHit(
>
> tool=\"ResFinder\", gene_name=row\[\"Resistance gene\"\],
>
> drug_class=row\[\"Phenotype\"\],
>
> identity_pct=float(row\[\"Identity\"\]),
>
> coverage_pct=float(row\[\"Coverage\"\]), \...))
>
> return hits

**8.2 Implementation: abricate_adapter.py**

> class AbricateAdapter:
>
> DATABASES = \[\"card\", \"resfinder\", \"ncbi\", \"argannot\", \"vfdb\", \"megares\"\]
>
> def run(self, fasta: Path, databases: list\[str\] \| None = None,
>
> min_identity: float = 75.0, min_coverage: float = 60.0) -\> list\[RawHit\]:
>
> dbs = databases or \[\"card\", \"ncbi\", \"argannot\"\]
>
> all_hits = \[\]
>
> for db in dbs:
>
> cmd = \[\"abricate\", \"\--db\", db,
>
> \"\--minid\", str(min_identity),
>
> \"\--mincov\", str(min_coverage), str(fasta)\]
>
> result = subprocess.run(cmd, check=True, capture_output=True, text=True)
>
> all_hits.extend(self.\_parse_abricate(result.stdout, db))
>
> return all_hits
>
> **SECTION 9 --- HIT DETECTION AND METRICS ENGINE**

**9.1 RawHit Data Model**

> from dataclasses import dataclass, field
>
> \@dataclass
>
> class RawHit:
>
> tool: str
>
> gene_name: str
>
> aro_accession: str \| None = None
>
> drug_class: str \| None = None
>
> resistance_mechanism: str \| None = None
>
> hit_category: str \| None = None \# Perfect\|Strict\|Loose\|Nudged
>
> identity_pct: float = 0.0
>
> coverage_pct: float = 0.0
>
> contig_id: str = \"\"
>
> start: int = 0
>
> end: int = 0
>
> strand: str = \"+\"
>
> alignment_score:float = 0.0
>
> bit_score: float = 0.0
>
> e_value: float = 1.0
>
> db_version_id: str = \"\"

**9.2 Hit Validation Rules**

  ------------------------------- ---------------------------------------------- ---------------------------------------------
  **Rule**                        **Threshold**                                  **Action on Failure**

  Minimum identity (reportable)   ≥ 75%                                          Hit discarded; not stored

  Minimum coverage (reportable)   ≥ 50%                                          Hit discarded; not stored

  Minimum contig length           ≥ 200 bp (contig containing hit)               WARNING flag on hit; lower confidence

  Maximum e-value                 ≤ 1×10⁻³ (BLAST hits only)                     Hit discarded if e_value \> threshold

  Hit coordinates valid           start \< end; start ≥ 1; end ≤ contig_length   Hit discarded; parsing error logged

  Non-empty gene name             len(gene_name) ≥ 2                             Hit discarded; malformed tool output logged
  ------------------------------- ---------------------------------------------- ---------------------------------------------

> **SECTION 10 --- IDENTITY, COVERAGE, AND HIT CLASSIFICATION**

**10.1 Metric Formulae**

> \# hit_metrics.py
>
> def identity_pct(matches: int, aln_length: int) -\> float:
>
> return round(matches / aln_length \* 100, 3) if aln_length else 0.0
>
> def coverage_pct(covered_bases: int, reference_length: int) -\> float:
>
> return round(covered_bases / reference_length \* 100, 3) if reference_length else 0.0

**10.2 Hit Classification Engine**

> def classify_hit(identity: float, coverage: float, aro_exists: bool) -\> str:
>
> if identity == 100.0 and coverage \>= 60.0:
>
> return \"Perfect\"
>
> elif identity \>= 90.0 and coverage \>= 60.0:
>
> return \"Strict\"
>
> elif identity \>= 80.0 and coverage \>= 50.0:
>
> return \"Loose\"
>
> elif identity \>= 75.0 and coverage \>= 40.0 and aro_exists:
>
> return \"Nudged\"
>
> return \"Subthreshold\" \# not reportable

  -------------- ------------------------ ------------------------ ------------------------ ------------------
  **Category**   **Identity Threshold**   **Coverage Threshold**   **Confidence Ceiling**   **Reportable**

  Perfect        = 100%                   ≥ 60%                    HIGH (1.0)               Yes

  Strict         ≥ 90%                    ≥ 60%                    HIGH (≤ 0.95)            Yes

  Loose          ≥ 80%                    ≥ 50%                    MEDIUM (≤ 0.75)          Yes

  Nudged         ≥ 75%                    ≥ 40% (partial)          LOW (≤ 0.55)             Yes (with flag)

  Subthreshold   \< 75%                   Any                      None                     No --- discarded
  -------------- ------------------------ ------------------------ ------------------------ ------------------

> **SECTION 11 --- ONTOLOGY MAPPING ENGINE**

**11.1 Implementation: ontology_mapper.py**

> \"\"\"CARD ARO ontology mapper --- Module 1C v1.0.0\"\"\"
>
> import json
>
> from functools import lru_cache
>
> from pathlib import Path
>
> class OntologyMapper:
>
> def \_\_init\_\_(self, aro_json: Path):
>
> self.aro = json.loads(aro_json.read_text())
>
> self.\_index = {entry\[\"accession\"\]: entry
>
> for entry in self.aro\[\"CARD_AROterm\"\]}
>
> \@lru_cache(maxsize=2048)
>
> def lookup(self, aro_accession: str) -\> dict:
>
> entry = self.\_index.get(aro_accession, {})
>
> return {
>
> \"aro_accession\": aro_accession,
>
> \"gene_name\": entry.get(\"name\", \"UNKNOWN\"),
>
> \"gene_family\": self.\_get_category(entry, \"AMR Gene Family\"),
>
> \"drug_class\": self.\_get_category(entry, \"Drug Class\"),
>
> \"resistance_mechanism\": self.\_get_category(entry, \"Resistance Mechanism\"),
>
> \"aro_category\": self.\_get_category(entry, \"AMR Category\")}
>
> def \_get_category(self, entry: dict, cat_name: str) -\> str \| None:
>
> cats = entry.get(\"ARO_category\", {}).get(cat_name, \[\])
>
> return cats\[0\].get(\"category_aro_name\") if cats else None
>
> **SECTION 12 --- EVIDENCE AGGREGATION ENGINE**

**12.1 Implementation: evidence_aggregation.py**

> \"\"\"Multi-database evidence aggregation --- Module 1C v1.0.0\"\"\"
>
> from collections import defaultdict
>
> \@dataclass
>
> class AggregatedGene:
>
> canonical_name: str
>
> aro_accession: str \| None
>
> supporting_tools: list\[str\] \# e.g. \[\"CARD\",\"AMRFinderPlus\"\]
>
> best_identity: float
>
> best_coverage: float
>
> best_hit_category: str
>
> drug_class: str \| None
>
> mechanism: str \| None
>
> all_hits: list\[RawHit\]
>
> agreement_score: float \# 0--1
>
> conflict_flags: list\[str\]
>
> def aggregate_hits(hits: list\[RawHit\],
>
> identity_threshold: float = 80.0,
>
> coverage_threshold: float = 60.0) -\> list\[AggregatedGene\]:
>
> \"\"\"Group hits by canonical gene name; compute agreement scores.\"\"\"
>
> grouped = defaultdict(list)
>
> for hit in hits:
>
> key = normalise_gene_name(hit.gene_name)
>
> grouped\[key\].append(hit)
>
> result = \[\]
>
> for canonical, gene_hits in grouped.items():
>
> tools = list({h.tool for h in gene_hits})
>
> best = max(gene_hits, key=lambda h: h.identity_pct \* h.coverage_pct)
>
> agreement = len(tools) / 4.0 \# 4 = max tools
>
> result.append(AggregatedGene(
>
> canonical_name=canonical, aro_accession=best.aro_accession,
>
> supporting_tools=tools, best_identity=best.identity_pct,
>
> best_coverage=best.coverage_pct,
>
> best_hit_category=classify_hit(best.identity_pct, best.coverage_pct, bool(best.aro_accession)),
>
> drug_class=best.drug_class, mechanism=best.resistance_mechanism,
>
> all_hits=gene_hits, agreement_score=agreement, conflict_flags=\[\]))
>
> return result
>
> **SECTION 13 --- GENE DEDUPLICATION ENGINE**

**13.1 Overlap Detection**

> \"\"\"Gene deduplication engine --- Module 1C v1.0.0\"\"\"
>
> def find_overlapping_hits(hits: list\[RawHit\],
>
> overlap_threshold: float = 0.5) -\> list\[tuple\]:
>
> \"\"\"Identify hits on the same contig that overlap by \>= overlap_threshold.\"\"\"
>
> overlaps = \[\]
>
> contig_hits = defaultdict(list)
>
> for h in hits: contig_hits\[h.contig_id\].append(h)
>
> for contig, chits in contig_hits.items():
>
> for i, a in enumerate(chits):
>
> for b in chits\[i+1:\]:
>
> overlap = min(a.end, b.end) - max(a.start, b.start)
>
> if overlap \> 0:
>
> span = max(a.end, b.end) - min(a.start, b.start)
>
> if overlap / span \>= overlap_threshold:
>
> overlaps.append((a, b, overlap/span))
>
> return overlaps

**13.2 Deduplication Rules**

  -------------------------------------------------------- --------------------------- --------------------------------------------------------------------------------
  **Scenario**                                             **Rule**                    **Action**

  Same gene, same coordinates, different tools             Identical hit               Merge; list all supporting tools in supporting_tools\[\]

  Same gene family, overlapping coordinates (≥ 50%)        Nested/overlapping hit      Retain hit with higher (identity × coverage); log other as supporting evidence

  Different genes, overlapping coordinates (≥ 80%)         Fragmented or fusion gene   Flag GENE_OVERLAP; retain both with overlap_flag=true

  Same gene, non-overlapping fragments of same reference   Fragmented hit              Merge fragments; compute combined coverage; flag FRAGMENTED_HIT

  Different gene name, same ARO accession                  Synonym                     Use canonical ARO name; store alias in amr_annotations
  -------------------------------------------------------- --------------------------- --------------------------------------------------------------------------------

> **SECTION 14 --- DRUG CLASSIFICATION ENGINE**

**14.1 Implementation: drug_classification.py**

> \# Canonical drug class normalisation map
>
> DRUG_CLASS_MAP = {
>
> \# Beta-lactam family
>
> \"penicillin\": \"beta-lactam\",
>
> \"cephalosporin\": \"beta-lactam\",
>
> \"carbapenem\": \"beta-lactam\",
>
> \"monobactam\": \"beta-lactam\",
>
> \"cephamycin\": \"beta-lactam\",
>
> \# Direct classes
>
> \"fluoroquinolone\": \"fluoroquinolone\",
>
> \"aminoglycoside\": \"aminoglycoside\",
>
> \"macrolide\": \"macrolide\",
>
> \"tetracycline\": \"tetracycline\",
>
> \"sulfonamide\": \"sulfonamide\",
>
> \"glycopeptide\": \"glycopeptide\",
>
> \"polymyxin\": \"polymyxin\",
>
> \"rifamycin\": \"rifamycin\",
>
> \"chloramphenicol\": \"chloramphenicol\",
>
> \"lincosamide\": \"macrolide\", \# MLSB class
>
> \"streptogramin\": \"macrolide\", \# MLSB class
>
> \"trimethoprim\": \"sulfonamide\",
>
> }
>
> def normalise_drug_class(raw_class: str) -\> str:
>
> clean = raw_class.lower().strip()
>
> return DRUG_CLASS_MAP.get(clean, clean)
>
> **SECTION 15 --- MECHANISM PRE-ANNOTATION ENGINE**

**15.1 Implementation: mechanism_preannotation.py**

> MECHANISM_MAP = {
>
> \"antibiotic inactivation\": \"antibiotic_inactivation\",
>
> \"antibiotic efflux\": \"efflux_pump\",
>
> \"target alteration\": \"target_alteration\",
>
> \"target protection\": \"target_protection\",
>
> \"target replacement\": \"target_replacement\",
>
> \"reduced permeability\": \"reduced_permeability\",
>
> \"enzymatic modification\": \"enzymatic_modification\",
>
> }
>
> \# Gene-name prefix heuristic for when ARO mechanism is unavailable
>
> GENE_PREFIX_MECHANISM = {
>
> \"bla\": \"antibiotic_inactivation\", \# beta-lactamases
>
> \"van\": \"target_alteration\", \# vancomycin resistance
>
> \"mcr\": \"target_alteration\", \# colistin resistance
>
> \"erm\": \"target_alteration\", \# MLSB methyltransferases
>
> \"tet\": \"efflux_pump\", \# most tetracycline efflux
>
> \"qnr\": \"target_protection\", \# quinolone resistance proteins
>
> \"aac\": \"antibiotic_inactivation\", \# aminoglycoside acetyltransferases
>
> \"aph\": \"antibiotic_inactivation\", \# aminoglycoside phosphotransferases
>
> }
>
> def preannotate_mechanism(aro_mechanism: str \| None, gene_name: str) -\> str:
>
> if aro_mechanism:
>
> return MECHANISM_MAP.get(aro_mechanism.lower(), \"unknown\")
>
> prefix = gene_name\[:3\].lower()
>
> return GENE_PREFIX_MECHANISM.get(prefix, \"unknown\")
>
> **SECTION 16 --- CONFIDENCE SCORING ENGINE**

**16.1 Composite Confidence Formula**

Confidence C = w₁×identity_score + w₂×coverage_score + w₃×db_agreement + w₄×hit_category_score + w₅×bitscore_norm

  ---------------------- ------------ ------------ ---------------------------------------------------
  **Component**          **Symbol**   **Weight**   **Calculation**

  Identity score         w₁           0.30         identity_pct / 100

  Coverage score         w₂           0.25         min(coverage_pct / 100, 1.0)

  Database agreement     w₃           0.25         len(supporting_tools) / 4 (max 4 tools)

  Hit category score     w₄           0.15         Perfect=1.0; Strict=0.85; Loose=0.65; Nudged=0.45

  Bit-score normalised   w₅           0.05         min(bit_score / 1000, 1.0)
  ---------------------- ------------ ------------ ---------------------------------------------------

**16.2 Implementation: confidence_engine.py**

> \"\"\"AMR detection confidence scoring --- Module 1C v1.0.0\"\"\"
>
> WEIGHTS = {\"identity\":0.30, \"coverage\":0.25, \"agreement\":0.25,
>
> \"category\":0.15, \"bitscore\":0.05}
>
> CATEGORY_SCORE = {\"Perfect\":1.0,\"Strict\":0.85,\"Loose\":0.65,\"Nudged\":0.45}
>
> def compute_confidence(gene: \"AggregatedGene\") -\> dict:
>
> identity_s = gene.best_identity / 100
>
> coverage_s = min(gene.best_coverage / 100, 1.0)
>
> agreement_s = len(gene.supporting_tools) / 4
>
> category_s = CATEGORY_SCORE.get(gene.best_hit_category, 0.40)
>
> bitscore_s = min(gene.best_bit_score / 1000, 1.0)
>
> score = (WEIGHTS\[\"identity\"\] \* identity_s +
>
> WEIGHTS\[\"coverage\"\] \* coverage_s +
>
> WEIGHTS\[\"agreement\"\] \* agreement_s +
>
> WEIGHTS\[\"category\"\] \* category_s +
>
> WEIGHTS\[\"bitscore\"\] \* bitscore_s)
>
> tier = \"HIGH\" if score\>=0.80 else \"MEDIUM\" if score\>=0.55 else \"LOW\"
>
> return {\"score\": round(score, 4), \"tier\": tier}
>
> **SECTION 17 --- AMR RESULT OBJECT MODEL**

**17.1 AMRGeneResult Dataclass**

> \@dataclass
>
> class AMRGeneResult:
>
> \# Identity
>
> gene_name: str
>
> aro_accession: str \| None
>
> gene_family: str \| None
>
> \# Classification
>
> drug_class: str \| None \# normalised
>
> drug_class_raw: list\[str\] \# raw strings from tools
>
> antibiotic_class: str \| None \# broad class (e.g. \"beta-lactam\")
>
> mechanism_type: str \| None \# pre-annotated mechanism
>
> hit_type: str \# Perfect\|Strict\|Loose\|Nudged
>
> \# Metrics
>
> identity_pct: float
>
> coverage_pct: float
>
> bit_score: float
>
> e_value: float
>
> \# Genomic location
>
> contig_id: str
>
> start: int
>
> end: int
>
> strand: str
>
> \# Evidence
>
> supporting_dbs: list\[str\] \# databases confirming this call
>
> agreement_score: float
>
> db_version_ids: dict\[str, str\] \# {tool: db_version_id}
>
> \# Confidence
>
> confidence_score: float
>
> confidence_tier: str
>
> **SECTION 18 --- DATABASE DESIGN**

**18.1 Core Table Relationships**

  -------------------------- ------------------------------------------------------------------------------------------------------------------------------ ----------------------------------------------------------------------------------------------------
  **Table**                  **Key Columns Added/Modified**                                                                                                 **Notes**

  amr_genes                  gene_family, aro_accession, drug_class, antibiotic_class, mechanism_type, hit_type, agreement_score, supporting_dbs TEXT\[\]   One row per unique gene per sample; confidence_score, confidence_tier from confidence_scores table

  amr_hits                   detection_tool, hit_category, identity_pct, coverage_pct, contig_id, start, end, strand, bit_score, e_value, raw_result_json   One row per tool per hit; multiple rows per amr_gene (FK: amr_gene_id)

  amr_annotations            amr_gene_id, annotation_source, key, value                                                                                     Flexible KV annotations; stores ARO ontology data, alias names, cross-references

  gene_evidence (new)        amr_gene_id, tool, db_version_id, hit_rank, agreement_flag                                                                     Explicit evidence linkage table; replaces TEXT\[\] for queryability

  drug_classes (reference)   id, canonical_name, broad_class, who_priority                                                                                  Reference data; amr_genes.drug_class FK to this table
  -------------------------- ------------------------------------------------------------------------------------------------------------------------------ ----------------------------------------------------------------------------------------------------

**18.2 gene_evidence Table**

> CREATE TABLE gene_evidence (
>
> id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
>
> amr_gene_id UUID NOT NULL REFERENCES amr_genes(id) ON DELETE CASCADE,
>
> tool VARCHAR(50) NOT NULL,
>
> db_version_id UUID NOT NULL REFERENCES database_versions(id),
>
> hit_rank SMALLINT DEFAULT 1,
>
> agreement_flag BOOLEAN DEFAULT TRUE,
>
> conflicting_call VARCHAR(200),
>
> recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
>
> CONSTRAINT uq_evidence UNIQUE (amr_gene_id, tool)
>
> );
>
> CREATE INDEX idx_evidence_gene ON gene_evidence (amr_gene_id);
>
> **SECTION 19 --- FASTAPI SERVICE DESIGN**

  ------------ -------------------------------------------------------- ------------------------------------------ ------------------------------------------------------
  **Method**   **Path**                                                 **Response**                               **Description**

  POST         /api/v1/module1/amr-detection                            202 {job_id}                               Submit AMR detection job; async; returns immediately

  GET          /api/v1/module1/amr-detection/{job_id}                   200 {status, progress_pct, current_step}   Poll job status

  GET          /api/v1/module1/amr-detection/{job_id}/results           200 {amr_genes\[\]}                        Full AMR gene inventory with all metrics

  GET          /api/v1/module1/amr-detection/{job_id}/results/summary   200 {by_drug_class{}}                      Gene counts by drug class and mechanism

  GET          /api/v1/module1/amr-detection/{job_id}/report            302 PDF redirect                           Download PDF detection report

  GET          /api/v1/samples/{id}/amr-genes                           200 {amr_genes\[\], pagination}            All genes for a sample across all jobs
  ------------ -------------------------------------------------------- ------------------------------------------ ------------------------------------------------------

**19.1 Detection Request Schema**

> class AMRDetectionRequest(BaseModel):
>
> model_config = ConfigDict(strict=True)
>
> sample_id: UUID
>
> assembly_id: UUID
>
> tools: list\[Literal\[\"CARD\",\"AMRFinderPlus\",\"ResFinder\",\"Abricate\"\]\]
>
> = \[\"CARD\",\"AMRFinderPlus\",\"ResFinder\",\"Abricate\"\]
>
> identity_threshold: float = Field(default=80.0, ge=75.0, le=100.0)
>
> coverage_threshold: float = Field(default=60.0, ge=40.0, le=100.0)
>
> include_loose: bool = True
>
> organism: str \| None = None \# for AMRFinderPlus organism-mode
>
> db_version_ids: dict\[str, str\] = {} \# optional pin per tool

**19.2 AMR Gene Result Response Schema**

> {
>
> \"amr_gene_id\": \"uuid\",
>
> \"gene_name\": \"blaCTX-M-15\",
>
> \"aro_accession\": \"ARO:3000016\",
>
> \"gene_family\": \"CTX-M beta-lactamase\",
>
> \"drug_class\": \"beta-lactam\",
>
> \"antibiotic_class\": \"cephalosporin\",
>
> \"mechanism_type\": \"antibiotic_inactivation\",
>
> \"hit_type\": \"Perfect\",
>
> \"identity_pct\": 100.0,
>
> \"coverage_pct\": 100.0,
>
> \"contig_id\": \"NODE_1_length_241337\",
>
> \"start\": 14523,
>
> \"end\": 15322,
>
> \"strand\": \"+\",
>
> \"supporting_dbs\": \[\"CARD\",\"AMRFinderPlus\",\"Abricate\"\],
>
> \"agreement_score\": 0.75,
>
> \"confidence_score\": 0.9410,
>
> \"confidence_tier\": \"HIGH\"
>
> **SECTION 20 --- CELERY INTEGRATION**

**20.1 Task Architecture**

> \@celery.task(bind=True, name=\"module1.amr_detection\",
>
> max_retries=3, soft_time_limit=7200, time_limit=8400)
>
> def amr_detection_task(self, job_id: str, config: dict) -\> dict:
>
> engine = AMRDetectionEngine(job_id=job_id, config=config)
>
> try:
>
> self.update_state(state=\"RUNNING\", meta={\"progress\": 0, \"step\": \"PARSING\"})
>
> result = engine.run(
>
> progress_cb=lambda p,s: self.update_state(
>
> state=\"RUNNING\", meta={\"progress\": p, \"step\": s}))
>
> return {\"status\": \"COMPLETED\", \"amr_gene_count\": len(result.genes)}

**20.2 Task Progress Steps**

  --------------- ---------------- ------------------------------------------------------------
  **Step**        **Progress %**   **Description**

  PARSING         0--5             Parse validated FASTA; build contig registry

  CARD_RGI        5--30            CARD RGI execution (longest single step; \~60% of runtime)

  AMRFINDERPLUS   30--50           AMRFinderPlus execution

  RESFINDER       50--65           ResFinder execution

  ABRICATE        65--75           Abricate multi-database screen

  VALIDATION      75--80           Hit validation and metric calculation

  DEDUPLICATION   80--84           Overlap detection and hit merging

  AGGREGATION     84--88           Cross-database evidence aggregation

  ONTOLOGY        88--91           ARO ontology mapping

  DRUG_CLASS      91--93           Drug class normalisation

  MECHANISM       93--95           Mechanism pre-annotation

  CONFIDENCE      95--98           Confidence score computation

  REPORT          98--100          JSON/TSV/PDF generation; DB persistence
  --------------- ---------------- ------------------------------------------------------------

> **SECTION 21 --- NEXTFLOW DSL2 PROCESS DESIGN**

**21.1 Main Process**

> process AMR_DETECT_CARD {
>
> tag \"\${meta.sample_id}\"
>
> label \"process_high\"
>
> cpus 8
>
> memory \"16 GB\"
>
> time \"60.min\"
>
> container \"finlaymaguire/card-rgi:6.0\"
>
> input:
>
> tuple val(meta), path(fasta)
>
> path card_db
>
> output:
>
> tuple val(meta), path(\"card_rgi_results.txt\"), emit: card_raw
>
> tuple val(meta), path(\"card_rgi_results.json\"), emit: card_json
>
> script:
>
> \"\"\"
>
> rgi load \--card_json \${card_db}/card.json \--local
>
> rgi main \\
>
> \--input_sequence \${fasta} \\
>
> \--output_file card_rgi_results \\
>
> \--local \--clean \--alignment_tool BLAST \\
>
> \--num_threads \${task.cpus} \\
>
> \--input_type contig
>
> \"\"\"
>
> }
>
> process AMR_DETECT_AMRFINDER {
>
> tag \"\${meta.sample_id}\"
>
> label \"process_medium\"
>
> cpus 4; memory \"8 GB\"; time \"30.min\"
>
> container \"ncbi/amrfinderplus:3.11\"
>
> input: tuple val(meta), path(fasta); path amrfinder_db
>
> output: tuple val(meta), path(\"amrfinder_results.tsv\"), emit: amrfinder_raw
>
> script:
>
> \"\"\"
>
> amrfinder \--nucleotide \${fasta} \\
>
> \--database \${amrfinder_db} \\
>
> \--threads \${task.cpus} \--plus \\
>
> \--output amrfinder_results.tsv
>
> \"\"\"
>
> }
>
> workflow AMR_DETECTION_SUBWORKFLOW {
>
> take:
>
> ch_validated_fasta // tuple(meta, fasta)
>
> ch_card_db
>
> ch_amrfinder_db
>
> main:
>
> AMR_DETECT_CARD(ch_validated_fasta, ch_card_db)
>
> AMR_DETECT_AMRFINDER(ch_validated_fasta, ch_amrfinder_db)
>
> // ResFinder and Abricate processes follow same pattern
>
> AMR_AGGREGATE(
>
> ch_validated_fasta
>
> .join(AMR_DETECT_CARD.out.card_raw)
>
> .join(AMR_DETECT_AMRFINDER.out.amrfinder_raw)
>
> )
>
> emit:
>
> amr_genes_json = AMR_AGGREGATE.out.amr_genes_json
>
> amr_genes_tsv = AMR_AGGREGATE.out.amr_genes_tsv
>
> **SECTION 22 --- TESTING STRATEGY**

  ------------------------ ------------------------- ---------------------------------------------------------------- -----------------------------------------------------------------------
  **Test Type**            **Framework**             **Scope**                                                        **Key Scenarios**

  Unit Tests               pytest                    All adapter parsers, metric calculations, classification logic   ≥ 95% coverage; mock subprocess calls for tool execution

  Integration Tests        pytest + testcontainers   End-to-end: submit job → COMPLETED → results in DB               E. coli K-12 reference → expect blaTEM-1, aac(3)

  Reference Genome Tests   pytest fixtures           NCBI reference genomes with known AMR profiles                   5 reference genomes; compare detected genes to published AMR profiles

  AMR Benchmark Datasets   pytest fixtures           PATRIC/NCBI benchmark isolates (EBI AMR Benchmark v2)            Recall ≥ 0.95; precision ≥ 0.90 on benchmark set for CARD

  Regression Tests         pytest + snapshot         Re-run 10 reference FASTAs; compare gene lists                   No gene drops or additions without version increment

  Performance Tests        pytest-benchmark          5 Mb E. coli genome end-to-end                                   All 4 tools complete \< 15 min; aggregation \< 30 s
  ------------------------ ------------------------- ---------------------------------------------------------------- -----------------------------------------------------------------------

**22.1 Reference Test Isolates**

  ----------------- ------------------------- ----------------------------------- --------------------
  **Accession**     **Species**               **Key AMR Genes Expected**          **Source**

  GCF_000005845.2   E. coli K-12 MG1655       None (AMR-negative control)         NCBI RefSeq

  GCF_000750555.1   E. coli UTI89             blaTEM-1, aac(3)-IV, sul1           NCBI RefSeq

  GCF_001457655.1   K. pneumoniae KPNIH1      blaKPC-2, blaTEM-1, aac(3), sul1    NCBI RefSeq

  GCF_000462885.1   A. baumannii ATCC 17978   blaOXA-51, aac(3), armA             NCBI RefSeq

  GCF_000006765.1   P. aeruginosa PAO1        MexAB-OprM efflux, intrinsic AmpC   NCBI RefSeq
  ----------------- ------------------------- ----------------------------------- --------------------

> **SECTION 23 --- REPORT GENERATION**

  -------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------
  **Format**                 **Contents**                                                                                                                                                               **Consumer**

  amr_genes.tsv              Tab-delimited: sample_id, gene_name, aro_accession, drug_class, mechanism, identity_pct, coverage_pct, hit_type, confidence_score, supporting_dbs, contig_id, start, end   Bioinformaticians; R/Python analysis

  amr_genes.json             Full AMRGeneResult objects with nested hits\[\], evidence\[\], and ontology fields                                                                                         API, Module 2 export, downstream services

  amr_hits.tsv               Per-tool hit detail: tool, gene, identity, coverage, e_value, bit_score, coordinates                                                                                       Audit; BLAST-level validation

  gene_evidence.tsv          Evidence matrix: gene × tool agreement table; rows = genes, cols = CARD/AMRFinder/ResFinder/Abricate                                                                       Surveillance analysts

  drug_classification.tsv    Summary: drug_class, gene_count, gene_names\[\], resistance_classes\[\]                                                                                                    Clinical summary; dashboard

  confidence_scores.json     Per-gene: overall_score, components{identity,coverage,agreement,category,bitscore}, tier                                                                                   Confidence audit; Module 2

  amr_detection_report.pdf   Clinical report: species header, AMR gene table by drug class, confidence heat-row colour, mechanism summary, caveats                                                      Clinicians; lab directors
  -------------------------- -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- -------------------------------------------

> **SECTION 24 --- IMPLEMENTATION PLAN AND DELIVERABLES**

**24.1 Python Package Structure**

> amr_detection/
>
> ├── \_\_init\_\_.py \# AMRDetectionEngine orchestrator class
>
> ├── database_manager.py \# DB download, verify, activate, rollback
>
> ├── genome_parser.py \# FASTA parsing → ContigRecord list
>
> ├── result_models.py \# RawHit, AggregatedGene, AMRGeneResult dataclasses
>
> ├── adapters/
>
> │ ├── card_adapter.py \# CARD RGI subprocess wrapper + parser
>
> │ ├── amrfinder_adapter.py
>
> │ ├── resfinder_adapter.py
>
> │ └── abricate_adapter.py
>
> ├── hit_metrics.py \# identity_pct, coverage_pct, classify_hit
>
> ├── ontology_mapper.py \# ARO ontology lookup with LRU cache
>
> ├── evidence_aggregation.py \# Cross-database aggregation + agreement scoring
>
> ├── deduplication_engine.py \# Overlap detection and hit merging
>
> ├── drug_classification.py \# Drug class normalisation map
>
> ├── mechanism_preannotation.py
>
> ├── confidence_engine.py \# Weighted composite confidence scoring
>
> ├── report_generator.py \# JSON/TSV/PDF assembly
>
> ├── db_writer.py \# SQLAlchemy persistence
>
> ├── celery_tasks.py \# Celery task wrapper
>
> └── tests/
>
> ├── fixtures/ \# Reference FASTA files + expected outputs
>
> ├── test_card_adapter.py
>
> ├── test_aggregation.py
>
> ├── test_deduplication.py
>
> ├── test_confidence.py
>
> └── test_integration.py

**24.2 Dependencies**

  ------------- ------------- ------------------------------------------------
  **Package**   **Version**   **Purpose**

  biopython     ≥ 1.83        FASTA parsing

  rgi (CARD)    ≥ 6.0         CARD RGI executable (in Docker container)

  amrfinder     ≥ 3.11        AMRFinderPlus executable (in Docker container)

  datasketch    ≥ 1.6         MinHash for gene deduplication similarity

  pydantic      ≥ 2.6         Request/response schema validation

  sqlalchemy    ≥ 2.0         DB persistence

  celery        ≥ 5.3         Async task execution

  weasyprint    ≥ 62          PDF report generation

  pytest        ≥ 8.0         Test framework
  ------------- ------------- ------------------------------------------------

**24.3 Implementation Checklist**

  --------------------------------- ---------------------------------------------------------------------------------- -------------- ---------------------------------------------------------------------------------------------
  **Phase**                         **Deliverables**                                                                   **Duration**   **Acceptance Criteria**

  1 --- Tool adapters               card_adapter.py, amrfinder_adapter.py, resfinder_adapter.py, abricate_adapter.py   4 days         Each adapter produces valid RawHit list from real tool output; mocked subprocess tests pass

  2 --- Hit engine                  hit_metrics.py, deduplication_engine.py, evidence_aggregation.py                   3 days         Overlap detection tests pass; aggregation agreement score correct for known multi-tool hits

  3 --- Ontology & classification   ontology_mapper.py, drug_classification.py, mechanism_preannotation.py             2 days         ARO lookup returns correct drug_class for 50 known ARO accessions

  4 --- Confidence & result model   confidence_engine.py, result_models.py                                             2 days         Confidence formula validated; Perfect hit with 4 agreeing tools = score ≥ 0.95

  5 --- DB persistence              db_writer.py; amr_genes, amr_hits, gene_evidence tables                            2 days         E2E test: 5 reference genomes → DB; all genes retrievable via API

  6 --- API & Celery                FastAPI routes, celery_tasks.py, Pydantic schemas                                  2 days         POST detect → 202; poll → COMPLETED; GET results returns AMR gene list

  7 --- Nextflow                    DSL2 processes and AMR_DETECTION_SUBWORKFLOW                                       2 days         Nextflow pipeline runs in Docker; emits correct output channels

  8 --- Reports & tests             report_generator.py, full test suite, benchmarks                                   3 days         ≥ 95% coverage; recall ≥ 0.95 on benchmark set; E. coli \< 15 min
  --------------------------------- ---------------------------------------------------------------------------------- -------------- ---------------------------------------------------------------------------------------------
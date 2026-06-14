"""Generate ``reference_cds.fasta`` from the mutation knowledgebase.

This produces a *placeholder* reference CDS set that is internally consistent
with ``mutation_knowledgebase.json`` (the codon at each annotated protein
position translates to the KB reference amino acid). It is intended as a
runnable starting point — replace the generated FASTA with curated reference
CDS (CARD / PointFinder / NCBI) for production-grade gene localisation against
real assemblies.

Usage (run on the project's execution machine):

    python -m backend.mutation_engine.data.build_reference_cds

Only the standard library is required.
"""

from __future__ import annotations

import json
from pathlib import Path

from backend.mutation_engine.reference_loader import synthesize_references_from_kb

HERE = Path(__file__).parent
KB_PATH = HERE / "mutation_knowledgebase.json"
OUT_PATH = HERE / "reference_cds.fasta"

LINE_WIDTH = 70


def _wrap(seq: str, width: int = LINE_WIDTH) -> str:
    return "\n".join(seq[i : i + width] for i in range(0, len(seq), width))


def main() -> None:
    kb = json.loads(KB_PATH.read_text(encoding="utf-8"))
    references = synthesize_references_from_kb(kb.get("entries", []))

    lines = []
    for gene, seq in sorted(references.items()):
        lines.append(
            f">{gene} placeholder_reference_cds "
            f"derived_from=mutation_knowledgebase length_bp={len(seq)}"
        )
        lines.append(_wrap(seq))

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(references)} reference CDS to {OUT_PATH}")


if __name__ == "__main__":
    main()

"""Sequence manipulation utilities"""

def complement(seq: str) -> str:
    table = str.maketrans("ATGCatgc", "TACGtacg")
    return seq.translate(table)

def reverse_complement(seq: str) -> str:
    return complement(seq)[::-1]

def normalise(seq: str) -> str:
    return seq.upper().replace("U", "T")

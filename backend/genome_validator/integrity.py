"""File integrity checks (MD5/SHA256 computation)."""

from __future__ import annotations

import gzip
import hashlib
import os
from pathlib import Path

from Bio import SeqIO

from .models import IntegrityReport


def compute_integrity(file_path: Path) -> IntegrityReport:
    """Compute file integrity metrics (MD5, SHA256, record count).
    
    Args:
        file_path: Path to FASTA file (may be gzipped).
    
    Returns:
        IntegrityReport with checksums and metadata.
    """
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()
    
    file_size_bytes = os.path.getsize(file_path)
    is_gzipped = str(file_path).endswith(".gz")
    
    # Compute hashes on compressed file
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            md5_hash.update(chunk)
            sha256_hash.update(chunk)
    
    # Count records and compute uncompressed size
    record_count = 0
    uncompressed_size = None
    
    try:
        opener = gzip.open if is_gzipped else open
        with opener(file_path, "rt", encoding="utf-8") as fh:
            for record in SeqIO.parse(fh, "fasta"):
                record_count += 1
                
        # For gzipped files, get uncompressed size
        if is_gzipped:
            uncompressed_size = 0
            with gzip.open(file_path, "rb") as gz:
                while True:
                    chunk = gz.read(65536)
                    if not chunk:
                        break
                    uncompressed_size += len(chunk)
    except Exception:
        # If parsing fails, just record count as 0
        record_count = 0
    
    return IntegrityReport(
        file_path=str(file_path),
        file_size_bytes=file_size_bytes,
        md5=md5_hash.hexdigest(),
        sha256=sha256_hash.hexdigest(),
        is_gzipped=is_gzipped,
        uncompressed_size=uncompressed_size,
        record_count=record_count,
        encoding="UTF-8" if is_gzipped else "UTF-8",
    )


__all__ = ["compute_integrity"]

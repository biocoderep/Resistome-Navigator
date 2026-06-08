"""Sample upload service.

Encapsulates the business logic for registering a sample from an uploaded
FASTA file: extension validation, deterministic storage, checksum
computation, and creation of the ``Sample`` and ``SampleFile`` records.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from dataclasses import dataclass
from typing import BinaryIO

from sqlalchemy.orm import Session

from backend.models.sample import Sample
from backend.models.sample_file import SampleFile

ALLOWED_EXTENSIONS: tuple[str, ...] = (".fasta", ".fa", ".fna")
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "data/uploads")
STORED_EXTENSION: str = ".fasta"
_CHUNK_SIZE = 1024 * 1024  # 1 MiB


class UploadValidationError(ValueError):
    """Raised when an uploaded file fails validation."""


@dataclass(frozen=True)
class UploadResult:
    """Outcome of a successful sample upload."""

    sample_id: uuid.UUID
    file_name: str
    status: str


def _validate_extension(filename: str) -> None:
    """Reject any filename whose extension is not an accepted FASTA type."""
    lower = filename.lower()
    if not lower.endswith(ALLOWED_EXTENSIONS):
        raise UploadValidationError(
            "Unsupported file extension; allowed: "
            + ", ".join(ALLOWED_EXTENSIONS)
        )


def create_sample_with_file(
    db: Session,
    *,
    isolate_name: str,
    species: str | None,
    original_filename: str,
    file_stream: BinaryIO,
) -> UploadResult:
    """Validate, store, and persist an uploaded sample FASTA file.

    The file is written to ``UPLOAD_DIR`` under a deterministic name derived
    from the new sample's UUID (``<sample_uuid>.fasta``). On any failure the
    partially written file is removed and the transaction is rolled back.
    """
    if not original_filename:
        raise UploadValidationError("A file with a filename is required.")
    _validate_extension(original_filename)

    name = isolate_name.strip()
    if not name:
        raise UploadValidationError("isolate_name must not be empty.")

    sample = Sample(
        isolate_name=name,
        species=species,
        status="UPLOADED",
    )
    db.add(sample)
    db.flush()  # populate sample.id

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    stored_name = f"{sample.id}{STORED_EXTENSION}"
    dest_path = os.path.join(UPLOAD_DIR, stored_name)

    hasher = hashlib.sha256()
    total = 0
    try:
        with open(dest_path, "wb") as out:
            while chunk := file_stream.read(_CHUNK_SIZE):
                total += len(chunk)
                hasher.update(chunk)
                out.write(chunk)
    except Exception:
        db.rollback()
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise

    sample_file = SampleFile(
        sample_id=sample.id,
        file_name=stored_name,
        file_path=dest_path,
        file_type="assembly_fasta",
        file_size=total,
        checksum=hasher.hexdigest(),
    )
    db.add(sample_file)
    db.commit()

    return UploadResult(
        sample_id=sample.id,
        file_name=stored_name,
        status=sample.status,
    )


__all__ = [
    "ALLOWED_EXTENSIONS",
    "UPLOAD_DIR",
    "UploadResult",
    "UploadValidationError",
    "create_sample_with_file",
]
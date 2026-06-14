"""Celery task for off-thread PDF report generation.

Report rendering (matplotlib) is CPU-bound and must never run on the FastAPI
event loop, so the API enqueues this task and returns immediately.
"""

from __future__ import annotations

import logging
import os

from celery import shared_task

from backend.database.session import SessionLocal
from backend.reporting.data_access import build_cohort_report, build_isolate_report
from backend.reporting.pdf_report import (
    generate_cohort_report_pdf,
    generate_isolate_report_pdf,
)

logger = logging.getLogger(__name__)

REPORT_DIR = os.getenv("AMR_REPORT_DIR", "/tmp/amr_reports")


@shared_task(bind=True, name="reports.generate", max_retries=2, track_started=True)
def generate_report_task(self, target_type: str, target_id: str, out_dir: str | None = None):
    """Generate a single-isolate or cohort-batch PDF report.

    Args:
        target_type: "isolate" or "cohort".
        target_id: sample_id (isolate) or batch_id (cohort).
        out_dir: optional output directory (default: AMR_REPORT_DIR).
    """
    out_dir = out_dir or REPORT_DIR
    os.makedirs(out_dir, exist_ok=True)
    db = SessionLocal()
    try:
        if target_type == "cohort":
            data = build_cohort_report(db, target_id)
            out_path = os.path.join(out_dir, f"cohort_{target_id}.pdf")
            generate_cohort_report_pdf(data, out_path)
        else:
            data = build_isolate_report(db, target_id)
            out_path = os.path.join(out_dir, f"isolate_{target_id}.pdf")
            generate_isolate_report_pdf(data, out_path)

        logger.info("Report generated: %s", out_path)
        return {
            "status": "COMPLETED",
            "target_type": target_type,
            "target_id": str(target_id),
            "path": out_path,
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("Report generation failed: %s", exc)
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


__all__ = ["generate_report_task"]

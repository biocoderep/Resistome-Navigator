"""PDF report routes — enqueue generation and download results.

Generation is offloaded to Celery (CPU-bound matplotlib rendering), so these
endpoints return immediately with a task id; clients poll status then download.
"""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from backend.celery_app import celery_app
from backend.tasks.report_tasks import generate_report_task

router = APIRouter(prefix="/reports", tags=["reports"])


def _queued(task_id: str, target_type: str, target_id: str) -> Dict[str, Any]:
    return {
        "task_id": task_id,
        "status": "QUEUED",
        "target_type": target_type,
        "target_id": target_id,
    }


@router.post(
    "/isolate/{sample_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a single-isolate PDF report",
)
def request_isolate_report(sample_id: uuid.UUID) -> Dict[str, Any]:
    task = generate_report_task.delay("isolate", str(sample_id))
    return _queued(task.id, "isolate", str(sample_id))


@router.post(
    "/cohort/{batch_id}",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a cohort-batch PDF report",
)
def request_cohort_report(batch_id: str) -> Dict[str, Any]:
    task = generate_report_task.delay("cohort", str(batch_id))
    return _queued(task.id, "cohort", str(batch_id))


@router.get("/status/{task_id}", summary="Poll report generation status")
def report_status(task_id: str) -> Dict[str, Any]:
    res = AsyncResult(task_id, app=celery_app)
    payload: Dict[str, Any] = {"task_id": task_id, "state": res.state}
    if res.successful():
        payload["result"] = res.result
    elif res.failed():
        payload["error"] = str(res.result)
    return payload


@router.get("/download/{task_id}", summary="Download a completed PDF report")
def download_report(task_id: str):
    res = AsyncResult(task_id, app=celery_app)
    if not res.successful():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Report not ready (state={res.state}).",
        )
    path = (res.result or {}).get("path")
    if not path or not os.path.exists(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found.",
        )
    return FileResponse(
        path, media_type="application/pdf", filename=os.path.basename(path)
    )


__all__ = ["router"]

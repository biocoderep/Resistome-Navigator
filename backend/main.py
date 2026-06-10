"""FastAPI application entrypoint for the AMR Platform MVP API."""

from __future__ import annotations

from fastapi import FastAPI

from backend.api.routes import analysis_routes, sample_routes, validation_routes, batch_routes

app = FastAPI(
    title="AMR Platform API (MVP)",
    description="Module 1 — Antimicrobial Resistance Characterisation (MVP).",
    version="1.0.0",
)

app.include_router(sample_routes.router, prefix="/api/v1")
app.include_router(analysis_routes.router, prefix="/api/v1")
app.include_router(validation_routes.router, prefix="/api/v1")
app.include_router(batch_routes.router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}
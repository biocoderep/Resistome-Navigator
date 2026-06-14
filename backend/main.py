"""FastAPI application entrypoint for the AMR Platform MVP API."""

from __future__ import annotations

from fastapi import FastAPI

from backend.api.routes import analysis_routes, sample_routes, validation_routes, batch_routes, surveillance_routes, isolate_routes, report_routes

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AMR Platform API (MVP)",
    description="Module 1 — Antimicrobial Resistance Characterisation (MVP).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(sample_routes.router, prefix="/api/v1")
app.include_router(analysis_routes.router, prefix="/api/v1")
app.include_router(validation_routes.router, prefix="/api/v1")
app.include_router(batch_routes.router, prefix="/api/v1")
app.include_router(surveillance_routes.router, prefix="/api/v1")
app.include_router(isolate_routes.router, prefix="/api/v1")
app.include_router(report_routes.router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}
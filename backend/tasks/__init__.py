"""Celery tasks for AMR Platform."""

from .genome_validation_task import validate_genome_task

__all__ = ["validate_genome_task"]

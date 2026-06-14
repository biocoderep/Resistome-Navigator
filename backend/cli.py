"""Command-line entrypoints for the AMR Platform.

Console scripts (registered in pyproject.toml):
    genome-validate  -> validate a genome assembly FASTA
    amr-pipeline     -> grouped CLI: validate / analyze / report

These are thin wrappers over the same engines used by the API and Nextflow, so
terminal users get identical results without standing up the web stack.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Optional

import click

TEAL = "teal"
RED = "red"
YELLOW = "yellow"
GREEN = "green"


def _echo_kv(key: str, value, color: Optional[str] = None) -> None:
    click.echo(f"  {key:<22} " + click.style(str(value), fg=color, bold=True))


def _write_json(data: dict, output: Optional[str]) -> None:
    if output:
        Path(output).write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        click.echo(click.style(f"\n✓ Written: {output}", fg=GREEN))


# --------------------------------------------------------------------------- #
# genome-validate
# --------------------------------------------------------------------------- #


@click.command(name="genome-validate")
@click.argument("fasta", type=click.Path(exists=True, dir_okay=False))
@click.option("--sample-id", default=None, help="Sample identifier (default: filename).")
@click.option("--species", default=None, help="Expected species, if known.")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Write the full JSON validation report to this path.")
@click.option("--quiet", is_flag=True, help="Suppress the summary table.")
def genome_validate(fasta, sample_id, species, output, quiet):
    """Validate a genome assembly FASTA and report quality + AMR-readiness."""
    from backend.genome_validator import GenomeValidationEngine, ValidationConfig

    sample_id = sample_id or Path(fasta).stem
    engine = GenomeValidationEngine(config=ValidationConfig())
    report = engine.validate(file_path=Path(fasta), sample_id=sample_id, species=species)

    data = report.model_dump() if hasattr(report, "model_dump") else report.dict()

    if not quiet:
        status = report.validation_status
        color = GREEN if status == "PASS" else (YELLOW if status == "WARN" else RED)
        click.echo(click.style(f"\nGenome Validation — {sample_id}", fg=TEAL, bold=True))
        _echo_kv("Status", status, color)
        _echo_kv("Quality score", f"{report.quality_score:.1f}")
        _echo_kv("Quality class", report.quality_class)
        _echo_kv("Proceed to AMR", report.proceed_to_amr, GREEN if report.proceed_to_amr else RED)
        _echo_kv("Confidence cap", report.confidence_cap)

    _write_json(data, output)
    sys.exit(0 if report.proceed_to_amr else 2)


# --------------------------------------------------------------------------- #
# amr-pipeline group
# --------------------------------------------------------------------------- #


@click.group(name="amr-pipeline")
@click.version_option(package_name="amr-platform", message="%(version)s")
def cli():
    """AMR Characterisation Platform command-line interface."""


cli.add_command(genome_validate, name="validate")


@cli.command(name="analyze")
@click.argument("fasta", type=click.Path(exists=True, dir_okay=False))
@click.option("--sample-id", default=None, help="Sample identifier (default: filename).")
@click.option("--species", default="Unknown", help="Species, if known.")
@click.option("--validation", type=click.Path(exists=True), default=None,
              help="Genome validation report JSON (auto-run if omitted).")
@click.option("--amr", type=click.Path(exists=True), default=None,
              help="AMR detection report JSON (e.g. from CARD RGI / AMRFinderPlus).")
@click.option("--reference-fasta", type=click.Path(exists=True), default=None,
              help="Curated reference CDS FASTA for mutation detection.")
@click.option("--output", "-o", type=click.Path(), default="isolate_report.json",
              help="Where to write the isolate report JSON.")
def analyze(fasta, sample_id, species, validation, amr, reference_fasta, output):
    """Run the per-isolate biological analysis and emit isolate_report.json.

    If no --validation report is supplied, genome validation is run first. The
    --amr report is optional; without it, gene-based findings are empty and only
    mutation/virulence/phenotype-from-mutations are produced.
    """
    from backend.pipeline.isolate_pipeline import run_isolate_analysis

    sample_id = sample_id or Path(fasta).stem

    if validation:
        validation_report = json.loads(Path(validation).read_text(encoding="utf-8"))
    else:
        from backend.genome_validator import GenomeValidationEngine, ValidationConfig

        click.echo(click.style("Running genome validation…", fg=TEAL))
        vr = GenomeValidationEngine(config=ValidationConfig()).validate(
            file_path=Path(fasta), sample_id=sample_id, species=species
        )
        validation_report = vr.model_dump() if hasattr(vr, "model_dump") else vr.dict()

    amr_report = json.loads(Path(amr).read_text(encoding="utf-8")) if amr else {}

    click.echo(click.style("Running biological characterisation…", fg=TEAL))
    report = run_isolate_analysis(
        sample_id=sample_id,
        assembly_path=fasta,
        species=species,
        validation_report=validation_report,
        amr_report=amr_report,
        config={"reference_fasta": reference_fasta},
    )

    Path(output).write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    s = report["summary"]
    click.echo(click.style(f"\nIsolate analysis — {sample_id}", fg=TEAL, bold=True))
    _echo_kv("AMR genes", s["total_amr_genes"])
    _echo_kv("Mutations", s["total_mutations"])
    _echo_kv("Mechanisms", s["total_mechanisms"])
    _echo_kv("Resistant drugs", s["total_resistant_phenotypes"], RED)
    _echo_kv("Virulence genes", s["total_virulence_genes"])
    click.echo(click.style(f"\n✓ Written: {output}", fg=GREEN))


@cli.command(name="report")
@click.argument("report_json", type=click.Path(exists=True, dir_okay=False))
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Output PDF path (default: <input>.pdf).")
@click.option("--mode", type=click.Choice(["single", "cohort", "auto"]), default="auto",
              help="Report type. 'auto' infers from the JSON shape.")
def report(report_json, output, mode):
    """Generate a publication-quality PDF from an isolate or cohort report JSON."""
    from backend.reporting.pdf_report import generate_report_pdf

    data = json.loads(Path(report_json).read_text(encoding="utf-8"))
    output = output or str(Path(report_json).with_suffix(".pdf"))
    resolved_mode = None if mode == "auto" else mode
    generate_report_pdf(data, output, mode=resolved_mode)
    click.echo(click.style(f"✓ PDF report written: {output}", fg=GREEN))


if __name__ == "__main__":
    cli()

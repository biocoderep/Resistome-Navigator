"""Publication-quality PDF report service.

Dynamically renders either a **Single Isolate Report** or a comprehensive
**Cohort Batch Report** depending on the job type, using matplotlib's vector
PDF backend (no extra dependency beyond matplotlib, which is already required).

Design: clean, light, clinical/research aesthetic matching the frontend design
tokens (white cards, light-grey surface, deep-teal accent, fixed S/I/R colours).
Saved at 300 dpi so rasterised elements are publication-ready; vector text/lines
remain crisp at any zoom.

Entrypoints:
    generate_isolate_report_pdf(report, out_path)
    generate_cohort_report_pdf(cohort, out_path)
    generate_report_pdf(data, out_path, mode=None)   # dynamic dispatch
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import matplotlib

matplotlib.use("Agg")  # headless

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.colors import ListedColormap, BoundaryNorm  # noqa: E402

# --------------------------------------------------------------------------- #
# Clinical light theme (mirrors frontend/src/theme/tokens.ts)
# --------------------------------------------------------------------------- #
SURFACE_BASE = "#F3F4F6"
SURFACE_CARD = "#FFFFFF"
SURFACE_BORDER = "#E5E7EB"
TEXT_PRIMARY = "#111827"
TEXT_SECONDARY = "#4B5563"
TEXT_MUTED = "#9CA3AF"
ACCENT_TEAL = "#005D5D"

SIR_COLORS = {"S": "#2E7D32", "I": "#F9A825", "R": "#C62828"}
SIR_NA = "#CBD5E1"
TIER_COLORS = {"HIGH": "#005D5D", "MEDIUM": "#0F62FE", "LOW": "#8A3800"}

CATEGORICAL = [
    "#6929c4", "#1192e8", "#005d5d", "#9f1853", "#fa4d56", "#198038",
    "#002d9c", "#ee5396", "#b28600", "#009d9a", "#8a3800", "#a56eff",
]

A4_PORTRAIT = (8.27, 11.69)
A4_LANDSCAPE = (11.69, 8.27)


def _apply_style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "figure.facecolor": SURFACE_CARD,
        "axes.facecolor": SURFACE_CARD,
        "axes.edgecolor": SURFACE_BORDER,
        "axes.labelcolor": TEXT_SECONDARY,
        "text.color": TEXT_PRIMARY,
        "xtick.color": TEXT_SECONDARY,
        "ytick.color": TEXT_SECONDARY,
        "axes.grid": False,
        "savefig.facecolor": SURFACE_CARD,
    })


def _sir_color(sir: Optional[str]) -> str:
    return SIR_COLORS.get(str(sir or "").upper(), SIR_NA)


def _trunc(value: Any, width: int = 28) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= width else text[: width - 1] + "…"


def _new_page(figsize=A4_PORTRAIT):
    fig = plt.figure(figsize=figsize)
    fig.patch.set_facecolor(SURFACE_CARD)
    return fig


def _draw_header(fig, title: str, subtitle: str, meta: Dict[str, str]) -> None:
    """Top banner with title, subtitle and a teal rule."""
    fig.text(0.06, 0.955, title, fontsize=20, fontweight="bold", color=TEXT_PRIMARY)
    fig.text(0.06, 0.93, subtitle, fontsize=11, color=ACCENT_TEAL, fontweight="bold")
    # teal rule
    fig.add_artist(plt.Line2D([0.06, 0.94], [0.918, 0.918], color=ACCENT_TEAL, lw=2))
    y = 0.90
    for key, val in meta.items():
        fig.text(0.06, y, f"{key}:", fontsize=9, color=TEXT_MUTED)
        fig.text(0.24, y, _trunc(val, 70), fontsize=9, color=TEXT_PRIMARY, fontweight="medium")
        y -= 0.022


def _metric_cards(fig, top: float, metrics: List[tuple]) -> None:
    """A row of summary stat cards."""
    n = len(metrics)
    if n == 0:
        return
    left, right = 0.06, 0.94
    gap = 0.015
    width = (right - left - gap * (n - 1)) / n
    for i, (label, value) in enumerate(metrics):
        x = left + i * (width + gap)
        ax = fig.add_axes([x, top - 0.08, width, 0.08])
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor(SURFACE_BORDER)
        ax.set_facecolor(SURFACE_BASE)
        ax.text(0.5, 0.62, str(value), ha="center", va="center",
                fontsize=18, fontweight="bold", color=ACCENT_TEAL, transform=ax.transAxes)
        ax.text(0.5, 0.22, label, ha="center", va="center",
                fontsize=7.5, color=TEXT_SECONDARY, transform=ax.transAxes)


def _table(fig, rect, columns: Sequence[str], rows: List[List[Any]],
           sir_col: Optional[int] = None, title: Optional[str] = None,
           col_widths: Optional[Sequence[float]] = None) -> None:
    """Render a clinical table inside ``rect`` (l, b, w, h)."""
    ax = fig.add_axes(rect)
    ax.axis("off")
    if title:
        ax.set_title(title, loc="left", fontsize=12, fontweight="bold",
                     color=TEXT_PRIMARY, pad=10)
    if not rows:
        ax.text(0.0, 0.95, "No records.", fontsize=9, color=TEXT_MUTED,
                transform=ax.transAxes, va="top")
        return

    cell_text = [[_trunc(c, 30) for c in row] for row in rows]
    table = ax.table(cellText=cell_text, colLabels=list(columns),
                     cellLoc="left", loc="upper left",
                     colWidths=list(col_widths) if col_widths else None)
    table.auto_set_font_size(False)
    table.set_fontsize(7.5)
    table.scale(1, 1.35)

    ncols = len(columns)
    for (r, c), cell in table.get_celld().items():
        cell.set_edgecolor(SURFACE_BORDER)
        cell.set_linewidth(0.5)
        if r == 0:  # header row
            cell.set_facecolor(ACCENT_TEAL)
            cell.set_text_props(color="#FFFFFF", fontweight="bold")
        else:
            cell.set_facecolor(SURFACE_CARD if r % 2 else SURFACE_BASE)
            if sir_col is not None and c == sir_col:
                sir = str(rows[r - 1][c]).upper()
                cell.set_facecolor(_sir_color(sir))
                cell.set_text_props(color="#FFFFFF", fontweight="bold")


# --------------------------------------------------------------------------- #
# Single isolate report
# --------------------------------------------------------------------------- #


def _isolate_overview_page(pdf: PdfPages, report: Dict[str, Any]) -> None:
    fig = _new_page()
    summary = report.get("summary", {})
    patho = report.get("pathogenicity", {})
    _draw_header(
        fig,
        "Single Isolate AMR Report",
        report.get("species") or "Unknown organism",
        {
            "Sample ID": report.get("sample_id", "-"),
            "Genome quality": report.get("genome_quality", "-"),
            "Validation": report.get("validation_status", "-"),
            "Generated": report.get("generated_at", "-"),
            "Pipeline": report.get("pipeline_stage", "-"),
        },
    )
    _metric_cards(fig, 0.80, [
        ("AMR genes", summary.get("total_amr_genes", 0)),
        ("Mutations", summary.get("total_mutations", 0)),
        ("Mechanisms", summary.get("total_mechanisms", 0)),
        ("Resistant drugs", summary.get("total_resistant_phenotypes", 0)),
        ("Virulence", summary.get("total_virulence_genes", 0)),
    ])

    # Phenotype (antibiogram) table
    phenos = report.get("phenotypes", [])
    rows = [
        [p.get("drug"), p.get("drug_class"), p.get("predicted_sir"),
         p.get("confidence_tier"), _fmt_pct(p.get("confidence_score"), scale=100)]
        for p in phenos
    ]
    _table(fig, [0.06, 0.40, 0.88, 0.28],
           ["Drug", "Class", "S/I/R", "Confidence", "Score"],
           rows, sir_col=2, title="Predicted Antibiogram")

    # Pathogenicity strip
    fig.text(0.06, 0.34, "Pathogenicity", fontsize=12, fontweight="bold", color=TEXT_PRIMARY)
    fig.text(0.06, 0.31,
             f"Risk class: {patho.get('risk_class', '-')}    "
             f"Risk score: {patho.get('risk_score', 0)}    "
             f"VF genes: {patho.get('total_vf_genes', 0)}    "
             f"High-risk: {patho.get('high_risk_count', 0)}",
             fontsize=9.5, color=TEXT_SECONDARY)

    _footer(fig, report.get("sample_id", ""))
    pdf.savefig(fig, dpi=300)
    plt.close(fig)


def _isolate_scatter_page(pdf: PdfPages, report: Dict[str, Any]) -> None:
    """Identity vs Coverage scatter — gene-call confidence visualisation."""
    genes = [
        g for g in report.get("amr_genes", [])
        if g.get("identity_percent") is not None and g.get("coverage_percent") is not None
    ]
    fig = _new_page()
    _draw_header(fig, "AMR Gene Confidence", "Identity vs Coverage",
                 {"Sample ID": report.get("sample_id", "-")})
    ax = fig.add_axes([0.12, 0.30, 0.78, 0.52])
    if genes:
        xs = [float(g.get("coverage_percent") or 0) for g in genes]
        ys = [float(g.get("identity_percent") or 0) for g in genes]
        sizes = [80 + 240 * float(g.get("confidence_score") or 0) for g in genes]
        ax.scatter(xs, ys, s=sizes, c=ACCENT_TEAL, alpha=0.65,
                   edgecolors="#FFFFFF", linewidths=0.8, zorder=3)
        for g, x, y in zip(genes, xs, ys):
            ax.annotate(_trunc(g.get("gene_name"), 14), (x, y), fontsize=7,
                        color=TEXT_SECONDARY, xytext=(4, 4), textcoords="offset points")
        # quality quadrant guides
        ax.axhline(95, color=SIR_COLORS["I"], ls="--", lw=1, alpha=0.7)
        ax.axvline(80, color=SIR_COLORS["I"], ls="--", lw=1, alpha=0.7)
    else:
        ax.text(0.5, 0.5, "No identity/coverage data available", ha="center",
                va="center", color=TEXT_MUTED, transform=ax.transAxes)
    ax.set_xlabel("Coverage (%)")
    ax.set_ylabel("Identity (%)")
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 105)
    for spine in ax.spines.values():
        spine.set_edgecolor(SURFACE_BORDER)
    _footer(fig, report.get("sample_id", ""))
    pdf.savefig(fig, dpi=300)
    plt.close(fig)


def _isolate_detail_pages(pdf: PdfPages, report: Dict[str, Any]) -> None:
    # AMR genes
    fig = _new_page()
    _draw_header(fig, "Detected Determinants", "AMR genes & resistance mutations",
                 {"Sample ID": report.get("sample_id", "-")})
    gene_rows = [
        [g.get("gene_name"), g.get("antibiotic_class"), g.get("resistance_mechanism"),
         _fmt_pct(g.get("identity_percent")), _fmt_pct(g.get("coverage_percent")),
         _fmt_pct(g.get("confidence_score"), scale=100)]
        for g in report.get("amr_genes", [])
    ]
    _table(fig, [0.06, 0.50, 0.88, 0.34],
           ["Gene", "Class", "Mechanism", "Ident%", "Cov%", "Conf"],
           gene_rows, title="AMR Genes")

    mut_rows = [
        [m.get("gene_name"), m.get("mutation"), m.get("effect"),
         m.get("classification"), m.get("drug_class"), m.get("sir_prediction")]
        for m in report.get("mutations", [])
    ]
    _table(fig, [0.06, 0.10, 0.88, 0.34],
           ["Gene", "Mutation", "Effect", "Classification", "Class", "S/I/R"],
           mut_rows, sir_col=5, title="Resistance Mutations")
    _footer(fig, report.get("sample_id", ""))
    pdf.savefig(fig, dpi=300)
    plt.close(fig)

    # Mechanisms + virulence
    fig = _new_page()
    _draw_header(fig, "Mechanisms & Virulence", "Resistance mechanisms and virulence factors",
                 {"Sample ID": report.get("sample_id", "-")})
    mech_rows = [
        [m.get("mechanism_name"), ", ".join(m.get("drug_classes", []) or []),
         str(len(m.get("supporting_genes", []) or [])),
         str(len(m.get("supporting_mutations", []) or [])),
         m.get("confidence_tier")]
        for m in report.get("mechanisms", [])
    ]
    _table(fig, [0.06, 0.50, 0.88, 0.34],
           ["Mechanism", "Drug classes", "#Genes", "#Muts", "Conf"],
           mech_rows, title="Resistance Mechanisms")

    vir_rows = [
        [v.get("gene_name"), v.get("virulence_category"),
         _fmt_pct(v.get("identity_percent")), _fmt_pct(v.get("coverage_percent")),
         "Yes" if v.get("is_high_risk") else "No"]
        for v in report.get("virulence_genes", [])
    ]
    _table(fig, [0.06, 0.10, 0.88, 0.34],
           ["Gene", "Category", "Ident%", "Cov%", "High-risk"],
           vir_rows, title="Virulence Factors")
    _footer(fig, report.get("sample_id", ""))
    pdf.savefig(fig, dpi=300)
    plt.close(fig)


def generate_isolate_report_pdf(report: Dict[str, Any], out_path: str) -> str:
    """Generate a single-isolate PDF report. Returns the output path."""
    _apply_style()
    with PdfPages(out_path) as pdf:
        _isolate_overview_page(pdf, report)
        _isolate_scatter_page(pdf, report)
        _isolate_detail_pages(pdf, report)
        _set_pdf_metadata(pdf, f"AMR Single Isolate Report - {report.get('sample_id', '')}")
    return out_path


# --------------------------------------------------------------------------- #
# Cohort batch report
# --------------------------------------------------------------------------- #


def _cohort_overview_page(pdf: PdfPages, cohort: Dict[str, Any]) -> None:
    fig = _new_page()
    isolates = (cohort.get("population_barcode", {}) or {}).get("isolates", [])
    antibiogram = cohort.get("antibiogram", []) or cohort.get("cohort_antibiogram_summary", [])
    _draw_header(
        fig,
        "Cohort Batch AMR Report",
        cohort.get("batch_name") or "Population surveillance summary",
        {
            "Batch ID": cohort.get("batch_id", "-"),
            "Total isolates": str(cohort.get("total_isolates", len(isolates))),
            "Antibiotics tested": str(len(antibiogram)),
            "Generated": cohort.get("generated_at", "-"),
        },
    )
    n_mdr = sum(1 for i in isolates if _is_mdr(i))
    _metric_cards(fig, 0.80, [
        ("Isolates", cohort.get("total_isolates", len(isolates))),
        ("Antibiotics", len(antibiogram)),
        ("MDR isolates", n_mdr),
    ])

    # Resistance frequency (stacked S/I/R per antibiotic)
    ax = fig.add_axes([0.10, 0.12, 0.82, 0.55])
    if antibiogram:
        labels = [a.get("antibiotic") for a in antibiogram]
        s = [float(a.get("s_pct", 0)) for a in antibiogram]
        i = [float(a.get("i_pct", 0)) for a in antibiogram]
        r = [float(a.get("r_pct", 0)) for a in antibiogram]
        x = range(len(labels))
        ax.bar(x, s, color=SIR_COLORS["S"], label="S")
        ax.bar(x, i, bottom=s, color=SIR_COLORS["I"], label="I")
        ax.bar(x, r, bottom=[a + b for a, b in zip(s, i)], color=SIR_COLORS["R"], label="R")
        ax.set_xticks(list(x))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("Isolates (%)")
        ax.set_ylim(0, 100)
        ax.legend(loc="upper right", frameon=False, fontsize=8, ncol=3)
        ax.set_title("Resistance Class Frequency", loc="left", fontsize=12,
                     fontweight="bold", color=TEXT_PRIMARY)
    else:
        ax.axis("off")
        ax.text(0.5, 0.5, "No antibiogram summary available", ha="center",
                va="center", color=TEXT_MUTED, transform=ax.transAxes)
    for spine in ax.spines.values():
        spine.set_edgecolor(SURFACE_BORDER)
    _footer(fig, cohort.get("batch_id", ""))
    pdf.savefig(fig, dpi=300)
    plt.close(fig)


def _cohort_heatmap_page(pdf: PdfPages, cohort: Dict[str, Any]) -> None:
    """Clinical antibiogram heatmap: isolates (Y) x antibiotics (X)."""
    barcode = cohort.get("population_barcode", {}) or {}
    antibiotics = barcode.get("antibiotics", [])
    isolates = barcode.get("isolates", [])

    fig = _new_page(A4_LANDSCAPE)
    _draw_header(fig, "Clinical Antibiogram Heatmap",
                 "Per-isolate susceptibility profile",
                 {"Batch ID": cohort.get("batch_id", "-")})

    if antibiotics and isolates:
        sir_to_int = {"S": 0, "I": 1, "R": 2}
        matrix = []
        ylabels = []
        for iso in isolates:
            profile = iso.get("profile", {})
            matrix.append([sir_to_int.get(str(profile.get(ab, "")).upper(), 3)
                           for ab in antibiotics])
            ylabels.append(_trunc(iso.get("filename") or iso.get("sample_id"), 22))

        cmap = ListedColormap([SIR_COLORS["S"], SIR_COLORS["I"], SIR_COLORS["R"], SIR_NA])
        norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)

        ax = fig.add_axes([0.18, 0.12, 0.70, 0.68])
        ax.imshow(matrix, aspect="auto", cmap=cmap, norm=norm)
        ax.set_xticks(range(len(antibiotics)))
        ax.set_xticklabels(antibiotics, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(len(ylabels)))
        ax.set_yticklabels(ylabels, fontsize=7)
        ax.set_xticks([x - 0.5 for x in range(1, len(antibiotics))], minor=True)
        ax.set_yticks([y - 0.5 for y in range(1, len(ylabels))], minor=True)
        ax.grid(which="minor", color=SURFACE_CARD, linewidth=1.2)
        ax.tick_params(which="minor", length=0)
        # legend
        handles = [plt.Rectangle((0, 0), 1, 1, color=SIR_COLORS[k]) for k in ("S", "I", "R")]
        ax.legend(handles, ["Susceptible", "Intermediate", "Resistant"],
                  loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False, fontsize=8)
    else:
        fig.text(0.5, 0.5, "No per-isolate susceptibility data available",
                 ha="center", va="center", color=TEXT_MUTED)

    _footer(fig, cohort.get("batch_id", ""))
    pdf.savefig(fig, dpi=300)
    plt.close(fig)


def generate_cohort_report_pdf(cohort: Dict[str, Any], out_path: str) -> str:
    """Generate a cohort batch PDF report. Returns the output path."""
    _apply_style()
    with PdfPages(out_path) as pdf:
        _cohort_overview_page(pdf, cohort)
        _cohort_heatmap_page(pdf, cohort)
        _set_pdf_metadata(pdf, f"AMR Cohort Batch Report - {cohort.get('batch_id', '')}")
    return out_path


# --------------------------------------------------------------------------- #
# Dispatch + helpers
# --------------------------------------------------------------------------- #


def generate_report_pdf(data: Dict[str, Any], out_path: str,
                        mode: Optional[str] = None) -> str:
    """Dispatch to the single or cohort generator based on ``mode`` or shape."""
    if mode is None:
        mode = "cohort" if ("population_barcode" in data or "antibiogram" in data
                            or "batch_id" in data) else "single"
    if mode == "cohort":
        return generate_cohort_report_pdf(data, out_path)
    return generate_isolate_report_pdf(data, out_path)


def _fmt_pct(value: Any, scale: float = 1.0) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value) * scale:.1f}"
    except (TypeError, ValueError):
        return "-"


def _is_mdr(isolate: Dict[str, Any]) -> bool:
    profile = isolate.get("profile", {})
    return sum(1 for v in profile.values() if str(v).upper() == "R") >= 3


def _footer(fig, identifier: str) -> None:
    fig.text(0.06, 0.04, "AMR Characterisation Platform", fontsize=7, color=TEXT_MUTED)
    fig.text(0.94, 0.04, _trunc(identifier, 40), fontsize=7, color=TEXT_MUTED, ha="right")


def _set_pdf_metadata(pdf: PdfPages, title: str) -> None:
    d = pdf.infodict()
    d["Title"] = title
    d["Author"] = "AMR Characterisation Platform"
    d["Subject"] = "Antimicrobial Resistance Characterisation"


__all__ = [
    "generate_isolate_report_pdf",
    "generate_cohort_report_pdf",
    "generate_report_pdf",
]

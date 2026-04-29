# // reporting.py
from pathlib import Path
from datetime import datetime

import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, HRFlowable, PageBreak,
    KeepTogether
)
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate


# ============================================================
# COLOUR PALETTE
# ============================================================

NAVY    = colors.HexColor("#1a2e4a")
STEEL   = colors.HexColor("#2d6a9f")
CRIMSON = colors.HexColor("#b03a2e")
AMBER   = colors.HexColor("#d4a017")
LIGHT   = colors.HexColor("#f4f6f9")
MID     = colors.HexColor("#dce3ed")
WHITE   = colors.white
BLACK   = colors.black


# ============================================================
# STYLES
# ============================================================

def build_styles():

    base = getSampleStyleSheet()

    styles = {}

    styles["cover_title"] = ParagraphStyle(
        "cover_title",
        fontSize=26,
        leading=32,
        textColor=WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=8,
    )

    styles["cover_sub"] = ParagraphStyle(
        "cover_sub",
        fontSize=13,
        leading=18,
        textColor=MID,
        fontName="Helvetica",
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    styles["section_header"] = ParagraphStyle(
        "section_header",
        fontSize=14,
        leading=18,
        textColor=NAVY,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=4,
        borderPad=0,
    )

    styles["pair_header"] = ParagraphStyle(
        "pair_header",
        fontSize=11,
        leading=14,
        textColor=WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
    )

    styles["body"] = ParagraphStyle(
        "body",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2c2c2c"),
        fontName="Helvetica",
        spaceAfter=4,
    )

    styles["caption"] = ParagraphStyle(
        "caption",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#555555"),
        fontName="Helvetica-Oblique",
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    styles["metric_label"] = ParagraphStyle(
        "metric_label",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#444444"),
        fontName="Helvetica-Bold",
    )

    styles["metric_value"] = ParagraphStyle(
        "metric_value",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1a2e4a"),
        fontName="Helvetica",
    )

    styles["warn"] = ParagraphStyle(
        "warn",
        fontSize=8,
        leading=11,
        textColor=CRIMSON,
        fontName="Helvetica-Oblique",
    )

    styles["footer"] = ParagraphStyle(
        "footer",
        fontSize=7,
        leading=10,
        textColor=colors.HexColor("#888888"),
        fontName="Helvetica",
        alignment=TA_CENTER,
    )

    return styles


# ============================================================
# HEADER / FOOTER CANVAS
# ============================================================

class ReportCanvas:

    def __init__(self, title, total_pairs):
        self.title       = title
        self.total_pairs = total_pairs
        self._pagecount  = 0

    def on_page(self, canvas, doc):

        canvas.saveState()

        W, H = A4

        # ── top bar ──────────────────────────────────────────
        if doc.page > 1:
            canvas.setFillColor(NAVY)
            canvas.rect(0, H - 1.1*cm, W, 1.1*cm, fill=1, stroke=0)

            canvas.setFont("Helvetica-Bold", 8)
            canvas.setFillColor(WHITE)
            canvas.drawString(1.2*cm, H - 0.72*cm, self.title)

            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(MID)
            canvas.drawRightString(
                W - 1.2*cm,
                H - 0.72*cm,
                f"Spin-Dependent Exotic Interactions — Asymmetry Analysis"
            )

        # ── bottom bar ───────────────────────────────────────
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, W, 0.8*cm, fill=1, stroke=0)

        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MID)
        canvas.drawString(
            1.2*cm, 0.27*cm,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        canvas.drawCentredString(
            W / 2, 0.27*cm,
            f"Page {doc.page}"
        )
        canvas.drawRightString(
            W - 1.2*cm, 0.27*cm,
            f"{self.total_pairs} matter-antimatter pairs analysed"
        )

        canvas.restoreState()


# ============================================================
# HELPERS
# ============================================================

def fmt_sci(val, decimals=3):
    """Format a float in scientific notation for PDF (no unicode super)."""
    if val is None or not np.isfinite(val):
        return "N/A"
    s = f"{val:.{decimals}e}"
    # e.g. "1.234e-05"  →  "1.234 x 10^-5"  using reportlab super tag
    mantissa, exp = s.split("e")
    exp_int = int(exp)
    return f"{mantissa} x 10<super>{exp_int}</super>"


def significance_label(p_value):
    if p_value < 0.001:
        return "***  (p < 0.001)"
    elif p_value < 0.01:
        return "**   (p < 0.01)"
    elif p_value < 0.05:
        return "*    (p < 0.05)"
    else:
        return "ns   (p >= 0.05)"


def asymmetry_interpretation(mean_abs_A):
    if mean_abs_A > 0.5:
        return "Strong asymmetry — large CPT-sensitive difference."
    elif mean_abs_A > 0.2:
        return "Moderate asymmetry — measurable matter/antimatter difference."
    elif mean_abs_A > 0.05:
        return "Weak asymmetry — marginal difference within constraints."
    else:
        return "Near-symmetric — matter and antimatter bounds are consistent."


# ============================================================
# COVER PAGE
# ============================================================

def build_cover(styles, total_pairs, skipped, timestamp):

    W, H = A4
    story = []

    # Navy background block — simulate with a coloured table
    cover_table = Table(
        [[Paragraph(
            "Spin-Dependent Exotic Interactions",
            styles["cover_title"]
        )],
        [Paragraph(
            "Matter–Antimatter Asymmetry Analysis Report",
            styles["cover_sub"]
        )],
        [Spacer(1, 0.3*cm)],
        [Paragraph(
            f"Generated: {timestamp}",
            styles["cover_sub"]
        )]],
        colWidths=[W - 4*cm],
    )

    cover_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",   (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 18),
        ("LEFTPADDING",  (0, 0), (-1, -1), 24),
        ("RIGHTPADDING", (0, 0), (-1, -1), 24),
        ("ROUNDEDCORNERS", [8]),
    ]))

    story.append(Spacer(1, 2*cm))
    story.append(cover_table)
    story.append(Spacer(1, 1*cm))

    # Summary stats box
    stats_data = [
        ["Metric", "Value"],
        ["Pairs analysed",      str(total_pairs)],
        ["Pairs skipped",       str(skipped)],
        ["Analysis timestamp",  timestamp],
        ["Framework",           "SPINDEP v1.0"],
        ["Method",              "log-interpolated chi-squared asymmetry"],
    ]

    stats_table = Table(stats_data, colWidths=[6*cm, 9*cm])
    stats_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), STEEL),
        ("TEXTCOLOR",    (0, 0), (-1, 0), WHITE),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("BACKGROUND",   (0, 1), (-1, -1), LIGHT),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT]),
        ("GRID",         (0, 0), (-1, -1), 0.4, MID),
        ("LEFTPADDING",  (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))

    story.append(stats_table)
    story.append(PageBreak())

    return story


# ============================================================
# SUMMARY TABLE PAGE
# ============================================================

def build_summary_table(rows, styles):

    story = []
    story.append(Paragraph("Summary of All Pairs", styles["section_header"]))
    story.append(HRFlowable(width="100%", thickness=1, color=STEEL, spaceAfter=8))

    headers = [
        "Coupling", "Potential", "Sector",
        "Matter source", "Antimatter source",
        "|A| mean", "chi2", "p-value"
    ]

    col_w = [2.3*cm, 1.8*cm, 1.6*cm, 3.2*cm, 3.2*cm, 1.6*cm, 1.6*cm, 1.8*cm]

    data = [headers]

    for r in rows:
        p_label = significance_label(r["p_value"])[:2].strip()
        data.append([
            r["coupling"],
            r["potential"],
            r["sector"],
            r["matter_source"],
            r["antimatter_source"],
            f"{r['mean_abs_A']:.3f}",
            f"{r['chi2']:.1f}",
            f"{r['p_value']:.3e} {p_label}",
        ])

    tbl = Table(data, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7.5),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT]),
        ("GRID",          (0, 0), (-1, -1), 0.3, MID),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))

    story.append(tbl)
    story.append(PageBreak())

    return story


# ============================================================
# PER-PAIR SECTION
# ============================================================

def build_pair_section(row, plot_path, styles, pair_index, total_pairs):

    story = []

    # ── pair header banner ───────────────────────────────────
    banner_text = (
        f"Pair {pair_index}/{total_pairs}  |  "
        f"{row['coupling']}  ·  {row['potential']}  ·  {row['sector']}"
    )

    banner = Table(
        [[Paragraph(banner_text, styles["pair_header"])]],
        colWidths=["100%"],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), STEEL),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))

    story.append(KeepTogether([banner, Spacer(1, 0.3*cm)]))

    # ── source row ───────────────────────────────────────────
    source_data = [
        [
            Paragraph("<b>Matter dataset</b>", styles["body"]),
            Paragraph(row["matter_source"], styles["body"]),
            Paragraph("<b>Antimatter dataset</b>", styles["body"]),
            Paragraph(row["antimatter_source"], styles["body"]),
        ],
        [
            Paragraph("<b>Interaction class</b>", styles["body"]),
            Paragraph(row["interaction_class"], styles["body"]),
            Paragraph("<b>Lambda range</b>", styles["body"]),
            Paragraph(
                f"{row['lambda_min']:.2e} – {row['lambda_max']:.2e} m",
                styles["body"]
            ),
        ],
    ]

    src_tbl = Table(source_data, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm])
    src_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT),
        ("GRID",          (0, 0), (-1, -1), 0.3, MID),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    story.append(src_tbl)
    story.append(Spacer(1, 0.35*cm))

    # ── statistics metrics ───────────────────────────────────
    p  = row["p_value"]
    chi2 = row["chi2"]
    dof  = row["dof"]
    A    = row["mean_abs_A"]

    sig_label = significance_label(p)
    interp    = asymmetry_interpretation(A)

    metrics_data = [
        ["Statistic", "Value", "Interpretation"],
        ["Mean |A_alpha|",   f"{A:.4f}",      interp],
        ["chi-squared",      f"{chi2:.3f}",   f"dof = {int(dof)}"],
        ["p-value",          f"{p:.4e}",      sig_label],
        ["lambda min",       f"{row['lambda_min']:.3e} m", ""],
        ["lambda max",       f"{row['lambda_max']:.3e} m", ""],
    ]

    met_tbl = Table(
        metrics_data,
        colWidths=[3.8*cm, 4*cm, 10.2*cm]
    )
    met_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT]),
        ("GRID",          (0, 0), (-1, -1), 0.3, MID),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    story.append(met_tbl)
    story.append(Spacer(1, 0.4*cm))

    # ── plot ─────────────────────────────────────────────────
    if plot_path and Path(plot_path).exists():

        img = Image(str(plot_path), width=16*cm, height=12.8*cm)
        caption = Paragraph(
            f"Figure: Coupling upper bounds vs interaction range λ (top panel) "
            f"and asymmetry parameter A<sub>α</sub> (bottom panel) for the "
            f"{row['sector']} sector under {row['potential']} potential.",
            styles["caption"]
        )
        story.append(KeepTogether([img, caption]))

    else:
        story.append(Paragraph(
            "[Plot not available — no overlapping lambda range]",
            styles["warn"]
        ))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID, spaceAfter=4))
    story.append(PageBreak())

    return story


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def generate_report(summary_rows, plots_dir, output_path):
    """
    summary_rows : list of dicts from pipeline summary_rows
    plots_dir    : Path to plots directory
    output_path  : Path for the output PDF
    """

    plots_dir   = Path(plots_dir)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles    = build_styles()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total_pairs = len(summary_rows)
    skipped     = 0  # rows with no plot (lambda skip)

    # ── count skipped ────────────────────────────────────────
    def plot_path_for(row):
        name = (
            f"{row['coupling']}_"
            f"{row['potential']}_"
            f"{row['sector']}.png"
        )
        p = plots_dir / name
        return p if p.exists() else None

    for row in summary_rows:
        if plot_path_for(row) is None:
            skipped += 1

    # ── build document ───────────────────────────────────────
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=1.8*cm,
        rightMargin=1.8*cm,
        topMargin=1.6*cm,
        bottomMargin=1.4*cm,
        title="Spin-Dependent Exotic Interactions — Asymmetry Report",
        author="SPINDEP Framework",
    )

    rc = ReportCanvas(
        title=f"SPINDEP Analysis  |  {timestamp}",
        total_pairs=total_pairs,
    )

    story = []

    # Cover
    story += build_cover(styles, total_pairs, skipped, timestamp)

    # Summary table
    story += build_summary_table(summary_rows, styles)

    # Per-pair sections
    for idx, row in enumerate(summary_rows, start=1):
        pp = plot_path_for(row)
        story += build_pair_section(row, pp, styles, idx, total_pairs)

    doc.build(story, onFirstPage=rc.on_page, onLaterPages=rc.on_page)

    print(f"[REPORT] Saved → {output_path}")
    return output_path
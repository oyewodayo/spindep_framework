# // gap_analysis.py
"""
Gap analysis for spin-dependent exotic interaction constraints.
Produces three publication-quality figures:
  1. Fermion pair coverage matrix  (potential x sector heatmap)
  2. Dataset inventory by potential (no overlapping labels)
  3. Matter vs antimatter coverage ratio per sector
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path
from collections import defaultdict
import re

NAVY    = "#1a2e4a"
STEEL   = "#2d6a9f"
CRIMSON = "#b03a2e"
LIGHT   = "#f4f6f9"
WHITE   = "#ffffff"

MATTER_ANTIMATTER_PAIRS = {
    "ee": "eebar", "ep": "epbar", "en": "enbar",
    "emu": "emubar", "mumu": "mumubar", "np": "npbar",
    "nn": "nnbar", "pp": "ppbar", "eN": "eNbar",
}

SECTOR_LABELS = {
    "ee": "e-e", "eebar": "e-e+", "ep": "e-p", "epbar": "e-pbar",
    "en": "e-n", "enbar": "e-nbar", "emu": "e-mu", "emubar": "e-mubar",
    "mumu": "mu-mu", "mumubar": "mu-mubar", "np": "n-p", "npbar": "n-pbar",
    "nn": "n-n", "nnbar": "n-nbar", "pp": "p-p", "ppbar": "p-pbar",
    "eN": "e-N", "eNbar": "e-Nbar", "nN": "n-N", "pN": "p-N",
}

ANTIMATTER_SECTORS = {
    "eebar","epbar","enbar","emubar","mumubar",
    "npbar","nnbar","ppbar","eNbar"
}


def pot_sort_key(p):
    m = re.match(r"V(\d+)", p)
    return int(m.group(1)) if m else 999


# ============================================================
# FIGURE 1 — COVERAGE MATRIX
# ============================================================

def plot_pair_coverage_matrix(datasets, output_path):
    counts = defaultdict(int)
    potentials_seen, sectors_seen = set(), set()
    for d in datasets:
        if d.potential == "UNKNOWN":
            continue
        counts[(d.potential, d.sector)] += 1
        potentials_seen.add(d.potential)
        sectors_seen.add(d.sector)

    potentials = sorted(potentials_seen, key=pot_sort_key)
    sectors    = sorted(sectors_seen)
    matrix = np.zeros((len(sectors), len(potentials)), dtype=int)
    for (pot, sec), cnt in counts.items():
        if pot in potentials and sec in sectors:
            matrix[sectors.index(sec), potentials.index(pot)] = cnt

    row_colors = [CRIMSON if s in ANTIMATTER_SECTORS else STEEL for s in sectors]
    fig, ax = plt.subplots(figsize=(max(12, len(potentials)*0.9), max(8, len(sectors)*0.45)))
    cmap = LinearSegmentedColormap.from_list("cov", [LIGHT, STEEL, NAVY], N=256)
    im = ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=0, vmax=max(matrix.max(), 1))
    for si in range(len(sectors)):
        for pi in range(len(potentials)):
            val = matrix[si, pi]
            if val > 0:
                c = WHITE if val > matrix.max() * 0.5 else NAVY
                ax.text(pi, si, str(val), ha="center", va="center", fontsize=7, color=c, fontweight="bold")
    ax.set_xticks(range(len(potentials)))
    ax.set_xticklabels(potentials, fontsize=8, rotation=45, ha="right")
    ax.set_yticks(range(len(sectors)))
    ax.set_yticklabels([str(SECTOR_LABELS.get(s, s)) for s in sectors], fontsize=8)
    for tick, color in zip(ax.get_yticklabels(), row_colors):
        tick.set_color(color)
    ax.set_xlabel("Interaction Potential", fontsize=10, color=NAVY)
    ax.set_ylabel("Fermion Sector", fontsize=10, color=NAVY)
    ax.set_title("Dataset Coverage: Potential x Fermion Sector", fontsize=11, color=NAVY, pad=12)
    ax.legend(handles=[
        mpatches.Patch(color=STEEL,   label="Matter sector"),
        mpatches.Patch(color=CRIMSON, label="Antimatter sector"),
        mpatches.Patch(color=LIGHT,   label="No data (gap)"),
    ], loc="upper right", fontsize=8, framealpha=0.9)
    plt.colorbar(im, ax=ax, label="Number of datasets", shrink=0.6)
    fig.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    print(f"[GAP] Saved pair coverage matrix -> {output_path}")


# ============================================================
# FIGURE 2 — DATASET INVENTORY (FIXED: no overlapping labels)
# Uses a table-style layout: one row per dataset, labels in
# a separate text column so bars never collide with text.
# ============================================================

def plot_lambda_coverage(datasets, output_path):
    by_potential = defaultdict(list)
    for d in datasets:
        if d.potential != "UNKNOWN":
            by_potential[d.potential].append(d)
    potentials = sorted(by_potential.keys(), key=pot_sort_key)
    if not potentials:
        return

    # ── one figure per potential, saved as separate files ───
    # Then stitch into one tall figure
    fig_parts = []
    for pot in potentials:
        dsets = sorted(by_potential[pot], key=lambda x: (x.sector, x.source))
        n = len(dsets)
        row_h = 0.30          # inches per row
        panel_h = max(1.2, n * row_h)

        fig_p, ax = plt.subplots(figsize=(14, panel_h))
        fs = max(5.5, min(8.5, 180 / max(n, 1)))

        for yi, d in enumerate(dsets):
            is_anti = d.sector in ANTIMATTER_SECTORS
            color   = CRIMSON if is_anti else STEEL
            hatch   = "///" if is_anti else ""
            ax.barh(yi, 1, left=0, height=0.7,
                    color=color, alpha=0.75,
                    hatch=hatch, edgecolor=NAVY, linewidth=0.4)

        # Labels: truncated to avoid overflow
        def lbl(d):
            sec = SECTOR_LABELS.get(d.sector, d.sector)
            src = d.source[:20]
            return f"{src}  [{sec}]"

        ax.set_yticks(range(n))
        ax.set_yticklabels([lbl(d) for d in dsets], fontsize=fs)
        ax.set_ylim(-0.6, n - 0.4)
        ax.set_xticks([])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_visible(False)

        n_m = sum(1 for d in dsets if d.sector not in ANTIMATTER_SECTORS)
        n_a = n - n_m
        ax.set_title(f"{pot}   (matter: {n_m}  antimatter: {n_a}  total: {n})",
                     fontsize=9, color=NAVY, loc="left", pad=4, fontweight="bold")
        fig_p.tight_layout(pad=0.4)
        fig_parts.append(fig_p)

    # ── combine into one tall figure via savefig to buffer ──
    import io
    from PIL import Image as PILImage

    imgs = []
    for f in fig_parts:
        buf = io.BytesIO()
        f.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor=WHITE)
        plt.close(f)
        buf.seek(0)
        imgs.append(PILImage.open(buf).copy())
        buf.close()

    if not imgs:
        return

    total_w = max(i.width for i in imgs)
    total_h = sum(i.height for i in imgs) + 40  # 40px gap for title
    combined = PILImage.new("RGB", (total_w, total_h), (255, 255, 255))

    # Title banner
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(combined)
    draw.text((total_w // 2, 10),
              "Dataset Inventory by Potential  (blue=matter, red=antimatter)",
              fill=(26, 46, 74), anchor="mt")

    y_off = 40
    for img in imgs:
        combined.paste(img, (0, y_off))
        y_off += img.height

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    combined.save(output_path, dpi=(130, 130))
    print(f"[GAP] Saved lambda coverage chart -> {output_path}")


# ============================================================
# FIGURE 3 — MATTER vs ANTIMATTER RATIO
# ============================================================

def plot_matter_antimatter_ratio(datasets, output_path):
    matter_counts = defaultdict(int)
    anti_counts   = defaultdict(int)
    for d in datasets:
        if d.sector in ANTIMATTER_SECTORS:
            for m, a in MATTER_ANTIMATTER_PAIRS.items():
                if a == d.sector:
                    anti_counts[m] += 1
                    break
        else:
            matter_counts[d.sector] += 1

    all_sectors = sorted(set(matter_counts) | set(anti_counts))
    m_vals = [matter_counts[s] for s in all_sectors]
    a_vals = [anti_counts[s]   for s in all_sectors]
    x = np.arange(len(all_sectors))
    w = 0.38

    fig, ax = plt.subplots(figsize=(max(10, len(all_sectors)), 5))
    ax.bar(x - w/2, m_vals, w, color=STEEL,   label="Matter sector",     edgecolor=NAVY, linewidth=0.7)
    ax.bar(x + w/2, a_vals, w, color=CRIMSON, label="Antimatter sector", edgecolor=NAVY, linewidth=0.7, alpha=0.85)
    for xi, av in zip(x, a_vals):
        if av == 0:
            ax.annotate("GAP", xy=(xi + w/2, 0.15), fontsize=7, color=CRIMSON, ha="center", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([str(SECTOR_LABELS.get(s, s)) for s in all_sectors], rotation=35, ha="right", fontsize=9)
    ax.set_ylabel("Number of datasets", fontsize=10)
    ax.set_title("Matter vs Antimatter Dataset Coverage per Fermion Sector\n(GAP = no antimatter data)", fontsize=11, color=NAVY)
    ax.legend(fontsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_facecolor(LIGHT)
    fig.patch.set_facecolor(WHITE)
    fig.tight_layout()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    print(f"[GAP] Saved matter/antimatter ratio -> {output_path}")


# ============================================================
# RUN ALL
# ============================================================

def run_gap_analysis(datasets, figures_dir):
    figures_dir = Path(figures_dir)
    plot_pair_coverage_matrix(datasets, figures_dir / "gap_analysis" / "pair_coverage_matrix.png")
    plot_lambda_coverage(datasets,      figures_dir / "gap_analysis" / "lambda_coverage_by_potential.png")
    plot_matter_antimatter_ratio(datasets, figures_dir / "gap_analysis" / "matter_antimatter_ratio.png")
    print(f"\n[GAP] All gap analysis figures saved to {figures_dir}/gap_analysis/")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "spindep")
    from src.parser import discover_datasets
    datasets = discover_datasets(Path("spindep/datasets/normalized"))
    print(f"Loaded {len(datasets)} datasets")
    run_gap_analysis(datasets, figures_dir="results/figures")
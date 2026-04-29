import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.stats import chi2 as chi2_dist


# ══════════════════════════════════════════════════════════════════
#  DATA LOADING
# ══════════════════════════════════════════════════════════════════

def load_dataset(filepath):
    """
    Load a CSV constraint file and clean it for log-space interpolation.
    Expects two columns: lambda_m (interaction range), gAgA_abs (coupling bound).
    """
    df = pd.read_csv(filepath, header=None, names=["lambda_m", "gAgA_abs"])
    df = df.apply(pd.to_numeric, errors="coerce").dropna()
    df = df[(df["lambda_m"] > 0) & (df["gAgA_abs"] > 0)]
    df = df.sort_values("lambda_m").reset_index(drop=True)
    return df


def label_from_filename(filepath):
    """
    Auto-generate a plot label directly from the CSV filename.
    Eliminates the risk of label/file mismatches.

    Filename format: {potential}{Author}_{Year}_{m}_{abs}_{fermion_pair}.csv
    Example: 2Ficek_2017_V2_m_abs_ee.csv  →  "Ficek 2017 (e-e)"
    """
    fermion_map = {
        "ee":     "e-e",
        "eebar":  "e-e\u207a",        # e-e⁺  positronium
        "emu":    "e-\u03bc\u207a",   # e-µ⁺  muonium
        "ebare":  "e-p\u0305",        # e-p̄   antiprotonic He
        "emubar": "e-\u03bc\u0305",   # e-µ̄
        "eN":     "e-N",
        "en":     "e-n",
        "ep":     "e-p",
    }
    name      = os.path.basename(filepath).replace(".csv", "")
    parts     = name.split("_")
    pair_tag  = parts[-1]
    year_part = [p for p in parts if p.isdigit() and len(p) == 4]
    author    = parts[0].lstrip("0123456789")
    year      = year_part[0] if year_part else "?"
    pair      = fermion_map.get(pair_tag, pair_tag)
    return f"{author} {year} ({pair})"


# ══════════════════════════════════════════════════════════════════
#  INTERPOLATION
# ══════════════════════════════════════════════════════════════════

def make_log_interpolator(df):
    """
    Build an interpolator that works in log-log space.

    WHY: constraint curves follow power laws, so straight lines in
    log-log space. Linear interpolation on raw values produces curved
    artefacts between sparse data points and is physically incorrect.
    """
    log_lam = np.log10(df["lambda_m"].values)
    log_g   = np.log10(df["gAgA_abs"].values)
    f = interp1d(log_lam, log_g, kind="linear",
                 bounds_error=False, fill_value=np.nan)
    return lambda lam: 10 ** f(np.log10(lam))


# ══════════════════════════════════════════════════════════════════
#  ASYMMETRY COMPUTATION
# ══════════════════════════════════════════════════════════════════

def compute_asymmetry(df_matter, df_antimatter, n_points=200):
    """
    Compute the LINEAR sensitivity asymmetry A_α over the overlapping λ range.

    INTERPRETATION:
      A_α ≈  0  → both sectors constrained equally
      A_α → +1  → matter sector far weaker (higher bound = less sensitive)
      A_α → -1  → antimatter sector far weaker

    LIMITATION: saturates near ±1 when curves differ by more than ~1 order
    of magnitude, giving no information about HOW different they are.
    Use compute_log_asymmetry for that.

    NOTE: inputs are upper bounds, not measured values with uncertainties.
    This is a gap-analysis tool, NOT a direct CPT violation test.
    """
    lam_min = max(df_matter["lambda_m"].min(),
                  df_antimatter["lambda_m"].min())
    lam_max = min(df_matter["lambda_m"].max(),
                  df_antimatter["lambda_m"].max())

    if lam_min >= lam_max:
        print("Warning: no overlapping λ range between the two datasets.")
        return None, None, None

    lam_grid = np.logspace(np.log10(lam_min), np.log10(lam_max), n_points)

    f_m = make_log_interpolator(df_matter)
    f_a = make_log_interpolator(df_antimatter)
    g_m = f_m(lam_grid)
    g_a = f_a(lam_grid)

    valid    = np.isfinite(g_m) & np.isfinite(g_a)
    lam_grid = lam_grid[valid]
    g_m      = g_m[valid]
    g_a      = g_a[valid]

    denom = g_m + g_a
    A_lin = np.where(denom > 0, (g_m - g_a) / denom, np.nan)

    return lam_grid, A_lin, (g_m, g_a)


def compute_log_asymmetry(df_matter, df_antimatter, n_points=200):
    """
    Compute THREE asymmetry measures over the overlapping λ range.

    ┌─────────────────────────────────────────────────────────────────┐
    │  R_log   = log10(g_matter / g_antimatter)                       │
    │            MOST INFORMATIVE. Unbounded. R = +n means matter     │
    │            is n orders of magnitude weaker. R = 0 means equal.  │
    │                                                                 │
    │  A_log   = (log g_m - log g_a) / (|log g_m| + |log g_a|)       │
    │            Normalised log asymmetry. Bounded [-1, +1] but NOT    │
    │            saturated like A_linear when curves differ greatly.  │
    │                                                                 │
    │  A_lin   = (g_m - g_a) / (g_m + g_a)                           │
    │            Original linear asymmetry. Included for comparison.  │
    │            Nearly always ±1 when curves differ by >1 order.     │
    └─────────────────────────────────────────────────────────────────┘

    Returns: lam_grid, R_log, A_log, A_lin, (g_m, g_a)
             or (None, None, None, None, None) if no overlap exists.
    """
    lam_min = max(df_matter["lambda_m"].min(),
                  df_antimatter["lambda_m"].min())
    lam_max = min(df_matter["lambda_m"].max(),
                  df_antimatter["lambda_m"].max())

    if lam_min >= lam_max:
        print("Warning: no overlapping λ range between the two datasets.")
        return None, None, None, None, None

    lam_grid = np.logspace(np.log10(lam_min), np.log10(lam_max), n_points)

    f_m = make_log_interpolator(df_matter)
    f_a = make_log_interpolator(df_antimatter)
    g_m = f_m(lam_grid)
    g_a = f_a(lam_grid)

    valid    = np.isfinite(g_m) & np.isfinite(g_a) & (g_m > 0) & (g_a > 0)
    lam_grid = lam_grid[valid]
    g_m      = g_m[valid]
    g_a      = g_a[valid]

    log_gm = np.log10(g_m)
    log_ga = np.log10(g_a)

    # ── Log ratio: unbounded, most informative ──
    R_log = log_gm - log_ga

    # ── Normalised log asymmetry: bounded [-1, +1] ──
    denom_log = np.abs(log_gm) + np.abs(log_ga)
    A_log = np.where(denom_log > 0, (log_gm - log_ga) / denom_log, np.nan)

    # ── Linear asymmetry: for comparison only ──
    denom_lin = g_m + g_a
    A_lin = np.where(denom_lin > 0, (g_m - g_a) / denom_lin, np.nan)

    return lam_grid, R_log, A_log, A_lin, (g_m, g_a)


# ══════════════════════════════════════════════════════════════════
#  STATISTICS
# ══════════════════════════════════════════════════════════════════

def chi_squared_sensitivity(g_m, g_a, sigma_frac=0.1):
    """
    Compute a chi-squared-like sensitivity-disagreement statistic.

    IMPORTANT: since we have upper bounds rather than Gaussian measurements,
    a true chi-squared cannot be computed. We assign a conventional
    fractional uncertainty sigma = sigma_frac * mean(g), which is a
    standard 10% systematic floor used in phenomenology papers.
    State this approximation explicitly in your thesis.

    Returns: chi2_total, degrees_of_freedom, p_value
    """
    sigma_sq   = (sigma_frac * (g_m + g_a) / 2) ** 2
    chi2_vals  = (g_m - g_a) ** 2 / sigma_sq
    chi2_total = np.nansum(chi2_vals)
    dof        = int(np.sum(np.isfinite(chi2_vals)))
    p_value    = 1 - chi2_dist.cdf(chi2_total, df=dof)
    return chi2_total, dof, p_value


def print_summary(lam_grid, R_log, A_log, A_lin, g_m, g_a,
                  matter_label, antimatter_label, potential_term):
    """Print a concise numerical summary for the Results chapter."""
    chi2, dof, pval = chi_squared_sensitivity(g_m, g_a)

    print("\n" + "═" * 60)
    print(f"  {potential_term}")
    print(f"  Matter:    {matter_label}")
    print(f"  Antimatter: {antimatter_label}")
    print("═" * 60)
    print(f"  Overlap range : {lam_grid.min():.2e} – {lam_grid.max():.2e} m")
    print(f"  Grid points   : {len(lam_grid)}")
    print()
    print(f"  Log ratio R(λ):")
    print(f"    Mean         : {np.nanmean(R_log):+.3f} orders of magnitude")
    print(f"    Peak         : {np.nanmax(np.abs(R_log)):.3f} orders")
    print(f"    at λ         : {lam_grid[np.nanargmax(np.abs(R_log))]:.2e} m")
    print(f"    Direction    : {'matter weaker' if np.nanmean(R_log) > 0 else 'antimatter weaker'}")
    print()
    print(f"  Normalised log asymmetry A_log:")
    print(f"    Mean |A_log| : {np.nanmean(np.abs(A_log)):.4f}")
    print()
    print(f"  Linear asymmetry A_lin:")
    print(f"    Mean |A_lin| : {np.nanmean(np.abs(A_lin)):.4f}  (expect ≈1 if R_log >> 0)")
    print()
    print(f"  χ² (approx, σ_frac=0.1):")
    print(f"    χ²           : {chi2:.2f}")
    print(f"    dof          : {dof}")
    print(f"    p-value      : {pval:.4f}")
    print(f"    CPT status   : {'consistent' if pval > 0.05 else 'TENSION (bounds disagree)'}")
    print("═" * 60 + "\n")


# ══════════════════════════════════════════════════════════════════
#  PLOTTING
# ══════════════════════════════════════════════════════════════════

def plot_linear_asymmetry(lam_grid, A_lin, g_m, g_a,
                          matter_label, antimatter_label,
                          potential_term, output_path=None):
    """
    Two-panel figure: constraint curves (top) + linear asymmetry A_α (bottom).

    Best for: showing WHETHER an asymmetry exists.
    Limitation: saturates at ±1 when curves differ by >1 order of magnitude.
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8),
                                   sharex=True,
                                   gridspec_kw={"height_ratios": [2, 1]})

    # ── Top panel: constraint curves ──
    ax1.loglog(lam_grid, g_m, color="steelblue", lw=2,
               label=f"Matter: {matter_label}")
    ax1.loglog(lam_grid, g_a, color="crimson", lw=2, linestyle="--",
               label=f"Antimatter: {antimatter_label}")
    ax1.set_ylabel(r"$|g_A g_A|$", fontsize=12)
    ax1.set_title(f"{potential_term} — linear asymmetry", fontsize=13)
    ax1.legend(fontsize=9)
    ax1.grid(True, which="both", ls="--", alpha=0.4)

    # ── Bottom panel: A_α ──
    ax2.semilogx(lam_grid, A_lin, color="darkorange", lw=1.5)
    ax2.axhline(0, color="gray", lw=0.8, ls="--")
    ax2.fill_between(lam_grid, A_lin, 0,
                     where=(A_lin > 0), alpha=0.15, color="steelblue",
                     label="Matter weaker")
    ax2.fill_between(lam_grid, A_lin, 0,
                     where=(A_lin < 0), alpha=0.15, color="crimson",
                     label="Antimatter weaker")
    ax2.set_xlabel("Interaction range λ (m)", fontsize=12)
    ax2.set_ylabel(r"$A_\alpha = \frac{g_m - g_{\bar{m}}}{g_m + g_{\bar{m}}}$",
                   fontsize=11)
    ax2.set_ylim(-1.1, 1.1)
    ax2.legend(fontsize=8, loc="upper right")
    ax2.grid(True, which="both", ls="--", alpha=0.4)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {output_path}")
    plt.show()


def plot_log_asymmetry(lam_grid, R_log, A_log, A_lin, g_m, g_a,
                       matter_label, antimatter_label,
                       potential_term, output_path=None):
    """
    Four-panel figure:
      Panel 1: raw constraint curves (log-log)
      Panel 2: log ratio R(λ) — HOW MANY orders of magnitude apart
      Panel 3: normalised log asymmetry A_log — bounded, not saturated
      Panel 4: A_log vs A_lin comparison — shows why log is better here

    Best for: quantifying the SIZE of the asymmetry and comparing across
    different potential terms in your constraint atlas.
    """
    fig, axes = plt.subplots(4, 1, figsize=(10, 14),
                             sharex=True,
                             gridspec_kw={"height_ratios": [2, 1.2, 1, 1]})
    ax1, ax2, ax3, ax4 = axes

    # ── Panel 1: constraint curves ──
    ax1.loglog(lam_grid, g_m, color="steelblue", lw=2,
               label=f"Matter: {matter_label}")
    ax1.loglog(lam_grid, g_a, color="crimson", lw=2, linestyle="--",
               label=f"Antimatter: {antimatter_label}")
    ax1.set_ylabel(r"$|g_A g_A|$", fontsize=12)
    ax1.set_title(f"{potential_term} — log asymmetry analysis", fontsize=13)
    ax1.legend(fontsize=9)
    ax1.grid(True, which="both", ls="--", alpha=0.4)

    # ── Panel 2: log ratio R(λ) ──
    ax2.semilogx(lam_grid, R_log, color="darkorange", lw=2)
    ax2.axhline(0, color="gray", lw=0.8, ls="--")
    ax2.fill_between(lam_grid, R_log, 0,
                     where=(R_log > 0), alpha=0.15, color="steelblue",
                     label="Matter weaker")
    ax2.fill_between(lam_grid, R_log, 0,
                     where=(R_log < 0), alpha=0.15, color="crimson",
                     label="Antimatter weaker")
    ax2.set_ylabel(r"$R(\lambda) = \log_{10}\!\left(\frac{g_m}{g_{\bar{m}}}\right)$",
                   fontsize=11)
    ax2.legend(fontsize=8, loc="upper right")
    ax2.grid(True, which="both", ls="--", alpha=0.4)

    # Annotate peak
    peak_idx = np.nanargmax(np.abs(R_log))
    peak_val = R_log[peak_idx]
    peak_lam = lam_grid[peak_idx]
    offset_x = peak_lam * 5 if peak_lam * 5 < lam_grid.max() else peak_lam / 5
    ax2.annotate(
        f"Peak: {peak_val:+.2f} orders\nλ = {peak_lam:.1e} m",
        xy=(peak_lam, peak_val),
        xytext=(offset_x, peak_val * 0.6),
        fontsize=8,
        arrowprops=dict(arrowstyle="->", color="black", lw=0.8),
        bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.7)
    )

    # ── Panel 3: normalised log asymmetry ──
    ax3.semilogx(lam_grid, A_log, color="purple", lw=2,
                 label=r"$A_{\log}$ (normalised log asymmetry)")
    ax3.axhline(0, color="gray", lw=0.8, ls="--")
    ax3.fill_between(lam_grid, A_log, 0,
                     where=(A_log > 0), alpha=0.12, color="steelblue")
    ax3.fill_between(lam_grid, A_log, 0,
                     where=(A_log < 0), alpha=0.12, color="crimson")
    ax3.set_ylabel(r"$A_{\log}$", fontsize=12)
    ax3.set_ylim(-1.1, 1.1)
    ax3.legend(fontsize=8, loc="upper right")
    ax3.grid(True, which="both", ls="--", alpha=0.4)

    # ── Panel 4: A_log vs A_lin comparison ──
    ax4.semilogx(lam_grid, A_log, color="purple", lw=2,
                 label=r"$A_{\log}$ — normalised log (informative)")
    ax4.semilogx(lam_grid, A_lin, color="gray", lw=1.5, linestyle=":",
                 label=r"$A_{\rm lin}$ — linear (saturated)")
    ax4.axhline(0, color="gray", lw=0.8, ls="--")
    ax4.set_xlabel("Interaction range λ (m)", fontsize=12)
    ax4.set_ylabel("Asymmetry", fontsize=11)
    ax4.set_ylim(-1.1, 1.1)
    ax4.legend(fontsize=8, loc="upper right")
    ax4.grid(True, which="both", ls="--", alpha=0.4)

    # Shared note
    fig.text(0.01, 0.01,
             "Note: inputs are upper bounds, not measured values. "
             "Asymmetry measures sensitivity gap, not CPT violation directly.",
             fontsize=7, color="gray", style="italic")

    plt.tight_layout(rect=[0, 0.02, 1, 1])
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {output_path}")
    plt.show()


# ══════════════════════════════════════════════════════════════════
#  MAIN — runs both plots when script is executed
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    # ── Set your data folder path here ────────────────────────────
    BASE = (
        "/mnt/c/Users/DELL/Documents/MSC RESEARCH/Data/"
        "Spin-Dependent-5th-Force-Limits-v3.2/"
        "Lei-Cong-Spin-Dependent-5th-Force-Limits-a604398/"
        "Dataset/normalized/gAgA/lepton-lepton"
    )

    # ── File selection ─────────────────────────────────────────────
    # Matter sector:    Ficek 2017 — helium fine structure (e-e)
    # Antimatter sector: Karshenboim 2011 — positronium HFS (e-e⁺)
    # This is a genuine CPT pair: same interaction, opposite sector.
    matter_file    = os.path.join(BASE, "2Ficek_2017_V2_m_abs_ee.csv")
    antimatter_file = os.path.join(BASE, "2Karshenboim_2011_3_m_abs_eebar.csv")

    # ── Labels from filenames — never hard-coded ──────────────────
    label_m  = label_from_filename(matter_file)
    label_am = label_from_filename(antimatter_file)
    print(f"Matter label:     {label_m}")
    print(f"Antimatter label: {label_am}")

    # ── Load data ──────────────────────────────────────────────────
    df_matter     = load_dataset(matter_file)
    df_antimatter = load_dataset(antimatter_file)

    # ── Compute log asymmetry (all three measures) ─────────────────
    result = compute_log_asymmetry(df_matter, df_antimatter)
    lam, R_log, A_log, A_lin, (g_m, g_a) = result

    if lam is None:
        print("Exiting: no overlapping λ range found.")
        exit()

    # ── Print numerical summary ────────────────────────────────────
    print_summary(lam, R_log, A_log, A_lin, g_m, g_a,
                  matter_label=label_m,
                  antimatter_label=label_am,
                  potential_term="V2 gAgA")

    # ── Plot 1: linear asymmetry ───────────────────────────────────
    plot_linear_asymmetry(lam, A_lin, g_m, g_a,
                          matter_label=label_m,
                          antimatter_label=label_am,
                          potential_term="V2 gAgA",
                          output_path="V2_asymmetry_linear.pdf")

    # ── Plot 2: log asymmetry (four-panel) ────────────────────────
    plot_log_asymmetry(lam, R_log, A_log, A_lin, g_m, g_a,
                       matter_label=label_m,
                       antimatter_label=label_am,
                       potential_term="V2 gAgA",
                       output_path="V2_asymmetry_log.pdf")
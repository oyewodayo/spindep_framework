import os                          # ← add this
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d


def load_dataset(filepath):
    df = pd.read_csv(filepath, header=None, names=["lambda_m", "gAgA_abs"])
    df = df.apply(pd.to_numeric, errors="coerce").dropna()
    df = df[(df["lambda_m"] > 0) & (df["gAgA_abs"] > 0)]
    df = df.sort_values("lambda_m").reset_index(drop=True)
    return df


def make_log_interpolator(df):
    log_lam = np.log10(df["lambda_m"].values)
    log_g   = np.log10(df["gAgA_abs"].values)
    f = interp1d(log_lam, log_g, kind="linear",
                 bounds_error=False, fill_value=np.nan)
    return lambda lam: 10**f(np.log10(lam))


def compute_asymmetry(df_matter, df_antimatter, n_points=200):
    lam_min = max(df_matter["lambda_m"].min(),
                  df_antimatter["lambda_m"].min())
    lam_max = min(df_matter["lambda_m"].max(),
                  df_antimatter["lambda_m"].max())

    if lam_min >= lam_max:
        print("Warning: no overlapping λ range.")
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
    A = np.where(denom > 0, (g_m - g_a) / denom, np.nan)
    return lam_grid, A, (g_m, g_a)


def chi_squared_sensitivity(g_m, g_a, sigma_frac=0.1):
    from scipy.stats import chi2 as chi2_dist
    sigma_sq   = (sigma_frac * (g_m + g_a) / 2)**2
    chi2_vals  = (g_m - g_a)**2 / sigma_sq
    chi2_total = np.nansum(chi2_vals)
    dof        = np.sum(np.isfinite(chi2_vals))
    p_value    = 1 - chi2_dist.cdf(chi2_total, df=dof)
    return chi2_total, dof, p_value


def plot_asymmetry(lam_grid, A, g_m, g_a,
                   matter_label, antimatter_label,
                   potential_term, output_path=None):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8),
                                   sharex=True,
                                   gridspec_kw={"height_ratios": [2, 1]})
    ax1.loglog(lam_grid, g_m, color="steelblue",
               lw=2, label=f"Matter: {matter_label}")
    ax1.loglog(lam_grid, g_a, color="crimson",
               lw=2, linestyle="--", label=f"Antimatter: {antimatter_label}")
    ax1.set_ylabel(r"$|g_A g_A|$", fontsize=12)
    ax1.set_title(f"{potential_term} — matter vs antimatter constraints", fontsize=13)
    ax1.legend(fontsize=9)
    ax1.grid(True, which="both", ls="--", alpha=0.4)

    ax2.semilogx(lam_grid, A, color="darkorange", lw=1.5)
    ax2.axhline(0, color="gray", lw=0.8, ls="--")
    ax2.fill_between(lam_grid, A, 0, where=(A > 0),
                     alpha=0.15, color="steelblue", label="Matter weaker")
    ax2.fill_between(lam_grid, A, 0, where=(A < 0),
                     alpha=0.15, color="crimson",   label="Antimatter weaker")
    ax2.set_xlabel("Interaction range λ (m)", fontsize=12)
    ax2.set_ylabel(r"$A_\alpha$", fontsize=12)
    ax2.set_ylim(-1.1, 1.1)
    ax2.legend(fontsize=8, loc="upper right")
    ax2.grid(True, which="both", ls="--", alpha=0.4)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.show()


def label_from_filename(filepath):
    """Auto-generate a plot label from the CSV filename."""
    fermion_map = {
        "ee":     "e-e",
        "eebar":  "e-e\u207a",       # e-e⁺
        "emu":    "e-\u03bc\u207a",  # e-µ⁺
        "ebare":  "e-p\u0305",       # e-p̄
        "emubar": "e-\u03bc\u0305",  # e-µ̄
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


# ── Example usage ─────────────────────────────────────────────
BASE = (
    "/mnt/c/Users/DELL/Documents/MSC RESEARCH/Data/"
    "Spin-Dependent-5th-Force-Limits-v3.2/"
    "Lei-Cong-Spin-Dependent-5th-Force-Limits-a604398/"
    "Dataset/normalized/gAgA/lepton-lepton"
)

matter_file    = BASE + "/2Ficek_2017_V2_m_abs_ee.csv"
antimatter_file = BASE + "/2Karshenboim_2011_3_m_abs_eebar.csv"

# Labels generated from filenames — never typed by hand
label_m  = label_from_filename(matter_file)
label_am = label_from_filename(antimatter_file)
print(f"Matter label:    {label_m}")
print(f"Antimatter label: {label_am}")

df_matter     = load_dataset(matter_file)
df_antimatter = load_dataset(antimatter_file)

lam, A, (g_m, g_a) = compute_asymmetry(df_matter, df_antimatter)

if lam is not None:
    chi2, dof, pval = chi_squared_sensitivity(g_m, g_a, sigma_frac=0.1)
    print(f"χ² = {chi2:.2f}  |  dof = {dof}  |  p-value = {pval:.4f}")
    print(f"Mean |A_α| = {np.nanmean(np.abs(A)):.4f}")

    plot_asymmetry(lam, A, g_m, g_a,
                   matter_label=label_m,       # ← from filename
                   antimatter_label=label_am,  # ← from filename
                   potential_term="V2 gAgA",
                   output_path="V2_asymmetry_ee_vs_eebar.pdf")
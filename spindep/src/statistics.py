# // statistics.py
"""
Statistical tests for matter-antimatter CPT consistency.

Two chi-squared implementations:

1. chi_squared_sensitivity(g_m, g_a, sigma_frac=0.1)
   Original uniform-uncertainty version. Uses a single fractional
   uncertainty sigma_frac applied symmetrically to both curves.
   Kept for backward compatibility.

2. chi_squared_weighted(g_m, g_a, sigma_m, sigma_a)
   Weighted chi-squared using per-point uncertainties derived from
   the local smoothness of each constraint curve (log-log curvature
   method). Physically motivated: smooth constraint curves have low
   local uncertainty; rapidly varying curves have higher uncertainty.

3. estimate_uncertainty(lam, g)
   Estimates per-point fractional uncertainty from the log-log
   second derivative (curvature) of the constraint curve. This
   is the standard approach when error bars are not published.

4. chi_squared_from_datasets(df_m, df_a, lam_grid)
   Full pipeline: interpolate both datasets onto a common grid,
   estimate per-point uncertainties, return weighted chi-squared
   result with full diagnostics.
"""

import numpy as np
from scipy.stats import chi2 as chi2_dist
from scipy.interpolate import interp1d


# ============================================================
# 1. ORIGINAL UNIFORM CHI-SQUARED (backward compatible)
# ============================================================

def chi_squared_sensitivity(g_m, g_a, sigma_frac=0.1):
    """
    Chi-squared test with uniform fractional uncertainty.

    Parameters
    ----------
    g_m, g_a    : array-like — coupling bounds on common lambda grid
    sigma_frac  : float — fractional uncertainty (default 10%)

    Returns
    -------
    chi2_total, dof, p_value
    """
    g_m = np.asarray(g_m, dtype=float)
    g_a = np.asarray(g_a, dtype=float)

    sigma_sq   = (sigma_frac * (g_m + g_a) / 2) ** 2
    chi2_vals  = (g_m - g_a) ** 2 / sigma_sq
    chi2_total = float(np.nansum(chi2_vals))
    dof        = int(np.sum(np.isfinite(chi2_vals)))
    p_value    = 1.0 - chi2_dist.cdf(chi2_total, df=dof)

    return chi2_total, dof, p_value


# ============================================================
# 2. UNCERTAINTY ESTIMATION FROM CURVE SMOOTHNESS
# ============================================================

def estimate_uncertainty(lam, g, min_frac=0.02, max_frac=0.50,
                         baseline_frac=0.05):
    """
    Estimate per-point fractional uncertainty from the local
    curvature of the constraint curve in log-log space.

    Rationale
    ---------
    Published constraint curves are theoretical upper bounds derived
    from experimental data. The smoothness of the curve in log(g)
    vs log(lambda) space reflects how well-constrained the bound is:
      - Very smooth (low curvature) → low local uncertainty (~2-5%)
      - Rapidly changing (high curvature) → higher uncertainty (~10-30%)
      - Kinks or features → potential systematic effects (~30-50%)

    This is the standard approach used when original error bars are
    not published (which is the case for most constraint curves in
    the Dobrescu-Mocioiu literature).

    Parameters
    ----------
    lam          : array — lambda values (metres), sorted ascending
    g            : array — coupling upper bounds
    min_frac     : float — minimum fractional uncertainty floor (2%)
    max_frac     : float — maximum fractional uncertainty cap (50%)
    baseline_frac: float — baseline added to all points (5%)

    Returns
    -------
    sigma_frac : array — per-point fractional uncertainty estimate
    """
    lam = np.asarray(lam, dtype=float)
    g   = np.asarray(g,   dtype=float)

    if len(lam) < 3:
        return np.full(len(lam), baseline_frac)

    # Work in log-log space
    log_lam = np.log10(np.maximum(lam, 1e-40))
    log_g   = np.log10(np.maximum(g,   1e-40))

    # Numerical second derivative (curvature in log-log space)
    # d²(log g)/d(log lam)²  via central differences
    curvature = np.zeros(len(lam))

    for i in range(1, len(lam) - 1):
        dlam_fwd = log_lam[i+1] - log_lam[i]
        dlam_bwd = log_lam[i]   - log_lam[i-1]
        dg_fwd   = log_g[i+1]   - log_g[i]
        dg_bwd   = log_g[i]     - log_g[i-1]

        if dlam_fwd > 0 and dlam_bwd > 0:
            d2 = (dg_fwd / dlam_fwd - dg_bwd / dlam_bwd) / \
                 (0.5 * (dlam_fwd + dlam_bwd))
            curvature[i] = abs(d2)

    # Endpoints: copy from neighbours
    curvature[0]  = curvature[1]  if len(curvature) > 1 else 0.0
    curvature[-1] = curvature[-2] if len(curvature) > 1 else 0.0

    # Normalise curvature to a fractional uncertainty
    # Curvature of 0 → baseline_frac; large curvature → max_frac
    c_max = np.percentile(curvature[curvature > 0], 95) if np.any(curvature > 0) else 1.0
    c_max = max(c_max, 1e-10)

    sigma_frac = baseline_frac + (max_frac - baseline_frac) * np.clip(curvature / c_max, 0, 1)
    sigma_frac = np.clip(sigma_frac, min_frac, max_frac)

    return sigma_frac


# ============================================================
# 3. WEIGHTED CHI-SQUARED WITH PER-POINT UNCERTAINTIES
# ============================================================

def chi_squared_weighted(g_m, g_a, sigma_m, sigma_a):
    """
    Weighted chi-squared test using per-point uncertainties.

    The test statistic at each lambda point is:

        chi2_i = (g_m_i - g_a_i)^2 / (sigma_m_i^2 + sigma_a_i^2)

    where sigma_m_i = sigma_frac_m_i * g_m_i  (absolute uncertainty)
          sigma_a_i = sigma_frac_a_i * g_a_i

    The total chi2 is the sum over all valid points.
    Under the null hypothesis (CPT symmetry, g_m = g_a), this
    follows a chi-squared distribution with dof = number of points.

    Parameters
    ----------
    g_m, g_a       : array — coupling bounds on common lambda grid
    sigma_m, sigma_a: array — per-point FRACTIONAL uncertainties
                     (same shape as g_m, g_a)

    Returns
    -------
    chi2_total : float
    dof        : int
    p_value    : float
    sigma_combined : array — combined absolute uncertainty per point
    """
    g_m     = np.asarray(g_m,     dtype=float)
    g_a     = np.asarray(g_a,     dtype=float)
    sigma_m = np.asarray(sigma_m, dtype=float)
    sigma_a = np.asarray(sigma_a, dtype=float)

    # Convert fractional to absolute uncertainties
    abs_sigma_m = sigma_m * g_m
    abs_sigma_a = sigma_a * g_a

    # Combined variance: propagation of independent uncertainties
    combined_var = abs_sigma_m ** 2 + abs_sigma_a ** 2

    # Guard against zero variance
    valid = np.isfinite(g_m) & np.isfinite(g_a) & (combined_var > 0)

    chi2_vals = np.where(
        valid,
        (g_m - g_a) ** 2 / np.where(combined_var > 0, combined_var, 1.0),
        np.nan
    )

    chi2_total = float(np.nansum(chi2_vals))
    dof        = int(np.sum(valid))
    p_value    = 1.0 - chi2_dist.cdf(chi2_total, df=max(dof, 1))

    sigma_combined = np.sqrt(combined_var)

    return chi2_total, dof, p_value, sigma_combined


# ============================================================
# 4. FULL PIPELINE: DATASET → WEIGHTED CHI-SQUARED
# ============================================================

def chi_squared_from_datasets(df_m, df_a, lam_grid=None, n_points=300):
    """
    Full weighted chi-squared pipeline from raw DataFrames.

    Steps:
      1. Determine overlapping lambda range
      2. Build common log-spaced grid
      3. Log-linear interpolation of both curves onto grid
      4. Estimate per-point uncertainties from curvature
      5. Compute weighted chi-squared

    Parameters
    ----------
    df_m, df_a : pd.DataFrame with columns [lambda_m, coupling_abs]
    lam_grid   : optional pre-computed lambda grid (array)
    n_points   : int — grid resolution if lam_grid not provided

    Returns
    -------
    result : dict with keys:
        lam_grid       : common lambda array
        g_m, g_a       : interpolated coupling arrays
        sigma_frac_m   : per-point fractional uncertainty for matter
        sigma_frac_a   : per-point fractional uncertainty for antimatter
        sigma_combined : per-point combined absolute uncertainty
        chi2_uniform   : chi2 with uniform 10% uncertainty (original)
        chi2_weighted  : chi2 with per-point estimated uncertainties
        dof_uniform    : degrees of freedom (uniform)
        dof_weighted   : degrees of freedom (weighted)
        pval_uniform   : p-value (uniform)
        pval_weighted  : p-value (weighted)
        mean_abs_A     : mean |A_alpha|
        improvement    : ratio chi2_weighted / chi2_uniform
    """
    lam_m = df_m["lambda_m"].values
    g_m_raw = df_m["coupling_abs"].values
    lam_a = df_a["lambda_m"].values
    g_a_raw = df_a["coupling_abs"].values

    # 1. Overlap range
    lam_min = max(lam_m.min(), lam_a.min())
    lam_max = min(lam_m.max(), lam_a.max())

    if lam_min >= lam_max:
        return None

    # 2. Common grid
    if lam_grid is None:
        lam_grid = np.logspace(np.log10(lam_min), np.log10(lam_max), n_points)

    # 3. Interpolate in log-log space
    def log_interp(lam_src, g_src, lam_tgt):
        f = interp1d(
            np.log10(lam_src), np.log10(np.maximum(g_src, 1e-300)),
            kind="linear", bounds_error=False, fill_value=np.nan
        )
        return 10 ** f(np.log10(lam_tgt))

    g_m = log_interp(lam_m, g_m_raw, lam_grid)
    g_a = log_interp(lam_a, g_a_raw, lam_grid)

    valid = np.isfinite(g_m) & np.isfinite(g_a)
    if not np.any(valid):
        return None

    # 4. Per-point uncertainties
    # Estimate from original dense curves, then interpolate to grid
    sigma_frac_m_dense = estimate_uncertainty(lam_m, g_m_raw)
    sigma_frac_a_dense = estimate_uncertainty(lam_a, g_a_raw)

    sigma_frac_m = log_interp(lam_m, sigma_frac_m_dense, lam_grid)
    sigma_frac_a = log_interp(lam_a, sigma_frac_a_dense, lam_grid)

    # Fill NaN uncertainty with baseline
    sigma_frac_m = np.where(np.isfinite(sigma_frac_m), sigma_frac_m, 0.10)
    sigma_frac_a = np.where(np.isfinite(sigma_frac_a), sigma_frac_a, 0.10)

    # Clip to physical range
    sigma_frac_m = np.clip(sigma_frac_m, 0.02, 0.50)
    sigma_frac_a = np.clip(sigma_frac_a, 0.02, 0.50)

    # 5. Chi-squared — both versions
    chi2_u, dof_u, pval_u = chi_squared_sensitivity(
        g_m[valid], g_a[valid], sigma_frac=0.10
    )

    chi2_w, dof_w, pval_w, sigma_combined = chi_squared_weighted(
        g_m[valid], g_a[valid],
        sigma_frac_m[valid], sigma_frac_a[valid]
    )

    # Asymmetry parameter
    denom = g_m + g_a
    A = np.where(denom > 0, (g_m - g_a) / denom, np.nan)
    mean_abs_A = float(np.nanmean(np.abs(A)))

    return {
        "lam_grid":       lam_grid,
        "g_m":            g_m,
        "g_a":            g_a,
        "A_alpha":        A,
        "sigma_frac_m":   sigma_frac_m,
        "sigma_frac_a":   sigma_frac_a,
        "sigma_combined": sigma_combined,
        "chi2_uniform":   chi2_u,
        "chi2_weighted":  chi2_w,
        "dof_uniform":    dof_u,
        "dof_weighted":   dof_w,
        "pval_uniform":   pval_u,
        "pval_weighted":  pval_w,
        "mean_abs_A":     mean_abs_A,
        "mean_sigma_m":   float(np.nanmean(sigma_frac_m[valid])),
        "mean_sigma_a":   float(np.nanmean(sigma_frac_a[valid])),
        "improvement":    chi2_w / chi2_u if chi2_u > 0 else 1.0,
    }


# ============================================================
# 5. UNCERTAINTY SUMMARY TABLE (for report / thesis)
# ============================================================

def uncertainty_summary(results_list):
    """
    Given a list of chi_squared_from_datasets() result dicts,
    return a summary comparing uniform vs weighted chi-squared.

    Parameters
    ----------
    results_list : list of dicts (from chi_squared_from_datasets)

    Returns
    -------
    rows : list of dicts suitable for pd.DataFrame
    """
    rows = []
    for r in results_list:
        if r is None:
            continue
        rows.append({
            "chi2_uniform":    r["chi2_uniform"],
            "chi2_weighted":   r["chi2_weighted"],
            "dof":             r["dof_weighted"],
            "pval_uniform":    r["pval_uniform"],
            "pval_weighted":   r["pval_weighted"],
            "mean_sigma_m_%":  round(r["mean_sigma_m"] * 100, 1),
            "mean_sigma_a_%":  round(r["mean_sigma_a"] * 100, 1),
            "mean_abs_A":      round(r["mean_abs_A"], 4),
            "chi2_ratio_w/u":  round(r["improvement"], 3),
        })
    return rows


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    import pandas as pd

    print("=== statistics.py self-test ===\n")

    # Synthetic test: matter bound 10x tighter than antimatter
    lam = np.logspace(-12, -8, 300)
    g_m = 1e-10 * (lam / 1e-10) ** (-0.5)   # matter: tight
    g_a = 1e-8  * (lam / 1e-10) ** (-0.5)   # antimatter: weak (10x)

    df_m = pd.DataFrame({"lambda_m": lam, "coupling_abs": g_m})
    df_a = pd.DataFrame({"lambda_m": lam, "coupling_abs": g_a})

    result = chi_squared_from_datasets(df_m, df_a)
    if result is None:
        raise ValueError("chi_squared_from_datasets returned None; check input datasets")

    print(f"Uniform chi2:  {result['chi2_uniform']:.1f}  (dof={result['dof_uniform']})  p={result['pval_uniform']:.3e}")
    print(f"Weighted chi2: {result['chi2_weighted']:.1f}  (dof={result['dof_weighted']})  p={result['pval_weighted']:.3e}")
    print(f"Mean |A_alpha|:      {result['mean_abs_A']:.4f}")
    print(f"Mean sigma_m:        {result['mean_sigma_m']*100:.1f}%")
    print(f"Mean sigma_a:        {result['mean_sigma_a']*100:.1f}%")
    print(f"chi2 ratio (w/u):    {result['improvement']:.3f}")
    print(f"\nExpected |A| ~ {abs(1e-10 - 1e-8)/(1e-10 + 1e-8):.4f}  (analytic)")
    print("\nSelf-test complete.")
# // statistics.py
import numpy as np

from scipy.stats import chi2 as chi2_dist


def chi_squared_sensitivity(g_m, g_a, sigma_frac=0.1):

    sigma_sq = (
        sigma_frac * (g_m + g_a) / 2
    )**2

    chi2_vals = (g_m - g_a)**2 / sigma_sq

    chi2_total = np.nansum(chi2_vals)

    dof = np.sum(np.isfinite(chi2_vals))

    p_value = 1 - chi2_dist.cdf(chi2_total, df=dof)

    return chi2_total, dof, p_value
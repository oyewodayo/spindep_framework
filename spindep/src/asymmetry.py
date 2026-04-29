# // asymmetry.py
import numpy as np

from .interpolation import make_log_interpolator


def compute_asymmetry(df_m, df_a, n_points=300):

    try:

        lam_min = max(
            df_m["lambda_m"].min(),
            df_a["lambda_m"].min()
        )

        lam_max = min(
            df_m["lambda_m"].max(),
            df_a["lambda_m"].max()
        )

        if lam_min >= lam_max:
            return None, None, None

        lam_grid = np.logspace(
            np.log10(lam_min),
            np.log10(lam_max),
            n_points
        )

        f_m = make_log_interpolator(df_m)
        f_a = make_log_interpolator(df_a)

        g_m = f_m(lam_grid)
        g_a = f_a(lam_grid)

        valid = np.isfinite(g_m) & np.isfinite(g_a)

        if not np.any(valid):
            return None, None, None

        lam_grid = lam_grid[valid]
        g_m      = g_m[valid]
        g_a      = g_a[valid]

        denom = g_m + g_a

        A = np.where(
            denom > 0,
            (g_m - g_a) / denom,
            np.nan
        )

        return lam_grid, A, (g_m, g_a)

    except Exception as e:
        print(f"  [ASYMMETRY ERROR] {e}")
        return None, None, None
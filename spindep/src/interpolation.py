# // interpolation.py
import numpy as np
from scipy.interpolate import interp1d


def make_log_interpolator(df):

    log_lam = np.log10(df["lambda_m"].values)

    log_g = np.log10(df["coupling_abs"].values)

    f = interp1d(
        log_lam,
        log_g,
        kind="linear",
        bounds_error=False,
        fill_value=np.nan
    )

    return lambda lam: 10**f(np.log10(lam))
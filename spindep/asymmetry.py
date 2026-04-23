"""
asymmetry.py — CPT Asymmetry Analysis

For each (potential, coupling, λ) triple where both a matter and an
antimatter constraint exist, computes:

    A_α(λ) = [g_matter(λ) − g_antimatter(λ)] / [g_matter(λ) + g_antimatter(λ)]

and the consistency (chi-squared) test for CPT invariance (A_α = 0).

Classes
-------
CPTPair          : A matched (matter, antimatter) pair of ConstraintDatasets
CPTAnalyzer      : High-level driver — finds all pairs and runs analyses
AsymmetryResult  : Output of a single pair analysis

Reference
---------
Dobrescu & Mocioiu (2006); SME framework: Kostelecký & Samuel (1989).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence
import warnings

import numpy as np
from scipy import stats

from .loader import ConstraintDB, ConstraintDataset
from .utils import CPT_PAIRS, logspace_overlap, potential_label


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class CPTPair:
    """
    A matched matter / antimatter pair for a given (potential, coupling).

    Attributes
    ----------
    pot_code    : potential code string
    coupling    : coupling type, e.g. 'gAgA'
    matter      : ConstraintDataset from the matter sector
    antimatter  : ConstraintDataset from the antimatter sector
    """
    pot_code:    str
    coupling:    str
    matter:      ConstraintDataset
    antimatter:  ConstraintDataset

    def __repr__(self) -> str:
        return (
            f"<CPTPair V{self.pot_code} {self.coupling} | "
            f"matter={self.matter.pair}[{self.matter.reference}] "
            f"vs antimatter={self.antimatter.pair}[{self.antimatter.reference}]>"
        )


@dataclass
class AsymmetryResult:
    """
    Output of CPTAnalyzer.analyze() for one CPTPair.

    Attributes
    ----------
    pair        : the CPTPair used
    lam         : λ grid (metres)
    A           : asymmetry A_α(λ)   — shape (n_points,)
    g_matter    : interpolated matter bound on the grid
    g_antimatter: interpolated antimatter bound on the grid
    chi2        : chi-squared statistic (A vs 0 test)
    p_value     : p-value for CPT invariance hypothesis
    dof         : degrees of freedom
    lam_range   : (λ_min, λ_max) of the overlap region
    """
    pair:          CPTPair
    lam:           np.ndarray
    A:             np.ndarray
    g_matter:      np.ndarray
    g_antimatter:  np.ndarray
    chi2:          float
    p_value:       float
    dof:           int
    lam_range:     tuple[float, float]

    @property
    def cpt_consistent(self) -> bool:
        """True if p_value > 0.05 (no significant CPT violation detected)."""
        return self.p_value > 0.05

    @property
    def summary_line(self) -> str:
        lo, hi = self.lam_range
        verdict = "CPT-consistent" if self.cpt_consistent else "CPT-TENSION"
        return (
            f"V{self.pair.pot_code} {self.pair.coupling} | "
            f"{self.pair.matter.pair} vs {self.pair.antimatter.pair} | "
            f"λ=[{lo:.2e},{hi:.2e}] m | "
            f"χ²={self.chi2:.2f} (dof={self.dof}) p={self.p_value:.3f} → {verdict}"
        )


# ---------------------------------------------------------------------------
# CPT Analyzer
# ---------------------------------------------------------------------------

class CPTAnalyzer:
    """
    Finds all matter/antimatter pairs in a ConstraintDB and computes
    the CPT asymmetry parameter A_α(λ) for each.

    Parameters
    ----------
    db          : ConstraintDB
    n_points    : number of points on the λ interpolation grid (default 300)
    sigma_frac  : fractional uncertainty assumed for each bound
                  (used in chi-squared; default 0.10 = 10%)
    """

    def __init__(
        self,
        db:          ConstraintDB,
        n_points:    int   = 300,
        sigma_frac:  float = 0.10,
    ):
        self.db         = db
        self.n_points   = n_points
        self.sigma_frac = sigma_frac
        self._pairs:   list[CPTPair] = []
        self._results: list[AsymmetryResult] = []

    # ------------------------------------------------------------------
    # Pair discovery

    def find_pairs(
        self,
        pot_codes: list[str] | None = None,
        couplings: list[str] | None = None,
    ) -> list[CPTPair]:
        """
        Search the DB for all (matter, antimatter) matched pairs.

        For each element of CPT_PAIRS and each (potential, coupling)
        combination, takes the best (widest λ range) dataset from each
        sector.

        Parameters
        ----------
        pot_codes : restrict to these potential codes (None = all)
        couplings : restrict to these coupling types  (None = all)

        Returns
        -------
        list of CPTPair objects; also stored in self._pairs
        """
        pots  = pot_codes or self.db.pot_codes
        coups = couplings or self.db.couplings
        pairs: list[CPTPair] = []

        for pot in pots:
            for coup in coups:
                for matter_token, anti_token in CPT_PAIRS:
                    m_ds = self._best(pot, coup, matter_token)
                    a_ds = self._best(pot, coup, anti_token)
                    if m_ds is None or a_ds is None:
                        continue
                    # Require overlapping λ range
                    overlap = logspace_overlap(m_ds.lam, a_ds.lam,
                                              self.n_points)
                    if overlap is None:
                        continue
                    pairs.append(CPTPair(
                        pot_code=pot,
                        coupling=coup,
                        matter=m_ds,
                        antimatter=a_ds,
                    ))

        self._pairs = pairs
        print(f"[CPTAnalyzer] Found {len(pairs)} matched CPT pairs.")
        return pairs

    def _best(
        self,
        pot_code: str,
        coupling: str,
        pair:     str,
    ) -> ConstraintDataset | None:
        """Return the widest-λ-range dataset for the given keys, or None."""
        candidates = self.db.query(pot_code=pot_code,
                                   coupling=coupling,
                                   pair=pair)
        if not candidates:
            return None
        return max(candidates, key=lambda ds: np.log10(ds.lam.max() / ds.lam.min()))

    # ------------------------------------------------------------------
    # Analysis

    def analyze(
        self,
        pairs: list[CPTPair] | None = None,
    ) -> list[AsymmetryResult]:
        """
        Compute A_α(λ) and chi-squared CPT test for each pair.

        Parameters
        ----------
        pairs : list of CPTPair to analyse (defaults to self._pairs;
                call find_pairs() first)

        Returns
        -------
        list of AsymmetryResult, also stored in self._results
        """
        pairs = pairs or self._pairs
        if not pairs:
            raise RuntimeError(
                "No pairs found. Run find_pairs() before analyze()."
            )
        results = []
        for cp in pairs:
            res = self._analyze_one(cp)
            if res is not None:
                results.append(res)
        self._results = results
        return results

    def _analyze_one(self, cp: CPTPair) -> AsymmetryResult | None:
        lam_grid = logspace_overlap(cp.matter.lam, cp.antimatter.lam,
                                    self.n_points)
        if lam_grid is None:
            return None

        g_m = cp.matter.interp(lam_grid)
        g_a = cp.antimatter.interp(lam_grid)

        # Mask any NaN values that might appear at grid edges
        mask = np.isfinite(g_m) & np.isfinite(g_a) & (g_m + g_a > 0)
        if mask.sum() < 10:
            return None

        lam_grid = lam_grid[mask]
        g_m = g_m[mask]
        g_a = g_a[mask]

        A = (g_m - g_a) / (g_m + g_a)

        # Chi-squared: test A_α = 0
        # Uncertainty on A propagated from fractional uncertainty on g
        sigma_gm = self.sigma_frac * g_m
        sigma_ga = self.sigma_frac * g_a
        denom = (g_m + g_a) ** 2
        sigma_A = np.sqrt(
            (2 * g_a / denom * sigma_gm) ** 2 +
            (2 * g_m / denom * sigma_ga) ** 2
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            chi2_vals = (A / sigma_A) ** 2
            chi2 = float(np.nansum(chi2_vals))

        dof = int(np.sum(np.isfinite(chi2_vals)))
        p_value = float(1 - stats.chi2.cdf(chi2, df=dof)) if dof > 0 else np.nan

        return AsymmetryResult(
            pair=cp,
            lam=lam_grid,
            A=A,
            g_matter=g_m,
            g_antimatter=g_a,
            chi2=chi2,
            p_value=p_value,
            dof=dof,
            lam_range=(float(lam_grid.min()), float(lam_grid.max())),
        )

    # ------------------------------------------------------------------
    # Reporting

    def print_report(self, results: list[AsymmetryResult] | None = None) -> None:
        """Print a concise summary table of all CPT pair analyses."""
        results = results or self._results
        if not results:
            print("No results. Run analyze() first.")
            return

        print("\n" + "=" * 80)
        print("CPT ASYMMETRY REPORT")
        print("=" * 80)
        tensions = [r for r in results if not r.cpt_consistent]
        for r in sorted(results, key=lambda r: r.p_value):
            print(r.summary_line)
        print("-" * 80)
        print(f"Total pairs: {len(results)}  |  "
              f"CPT tensions (p<0.05): {len(tensions)}")
        print("=" * 80 + "\n")

    def tension_pairs(
        self,
        results: list[AsymmetryResult] | None = None,
    ) -> list[AsymmetryResult]:
        """Return only results where CPT tension (p < 0.05) is detected."""
        results = results or self._results
        return [r for r in results if not r.cpt_consistent]

    def most_asymmetric(
        self,
        results: list[AsymmetryResult] | None = None,
        n: int = 5,
    ) -> list[AsymmetryResult]:
        """Return the n pairs with highest |A_α| (peak absolute asymmetry)."""
        results = results or self._results
        return sorted(results,
                      key=lambda r: float(np.nanmax(np.abs(r.A))),
                      reverse=True)[:n]
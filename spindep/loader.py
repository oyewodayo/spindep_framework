"""
loader.py — Data loading and the central ConstraintDB registry.

Filename convention (Cong et al. 2025):
    {potential_code}{Author}{Year}_{coupling}_{fermion_pair}.csv

Examples:
    2Almasi2020_gAgA_m_abs_ee.csv
    3Wineland1991_gAgA_m_abs_eebar.csv
    45Hunter2013_gpgp_m_abs_emu.csv

Columns in each CSV: λ (m),  |g·g| (dimensionless coupling upper bound)
"""

from __future__ import annotations

import os
import re
import glob
from dataclasses import dataclass, field
from typing import Iterator

import numpy as np
import pandas as pd

from .utils import classify_sector, COUPLING_LABELS

# ---------------------------------------------------------------------------
# Filename parser
# ---------------------------------------------------------------------------

_FNAME_RE = re.compile(
    r"^(?P<pot_code>\d+)"          # leading number(s) = potential code
    r"(?P<author>[A-Z][a-zA-Z]+)"  # Author (capital-first word)
    r"(?P<year>\d{4})"             # Year
    r"_(?P<coupling>[^_]+)"        # coupling type (gAgA, gpgp, …)
    r"(?:_m_abs)?"                 # optional normalisation tag
    r"_(?P<pair>.+)$"              # fermion pair (last segment)
)


def parse_filename(stem: str) -> dict | None:
    """
    Parse a CSV filename stem into its components.

    Returns a dict with keys:
        pot_code, author, year, coupling, pair, sector
    or None if the filename does not match the expected pattern.
    """
    m = _FNAME_RE.match(stem)
    if not m:
        return None
    d = m.groupdict()
    d["sector"] = classify_sector(d["pair"])
    d["reference"] = f"{d['author']} {d['year']}"
    return d


# ---------------------------------------------------------------------------
# Single dataset
# ---------------------------------------------------------------------------

@dataclass
class ConstraintDataset:
    """
    One experimental upper-bound curve: λ vs |coupling|.

    Attributes
    ----------
    path        : absolute path to the source CSV
    pot_code    : potential code string, e.g. '2', '45'
    author      : first author surname
    year        : publication year (string)
    coupling    : coupling key, e.g. 'gAgA'
    pair        : fermion pair token, e.g. 'ee', 'eebar'
    sector      : 'matter', 'antimatter', or 'unknown'
    reference   : 'Author Year' short citation
    lam         : λ array (metres), sorted ascending
    g_bound     : |coupling| upper bound array, aligned to lam
    """
    path: str
    pot_code: str
    author: str
    year: str
    coupling: str
    pair: str
    sector: str
    reference: str
    lam: np.ndarray = field(repr=False)
    g_bound: np.ndarray = field(repr=False)

    # ------------------------------------------------------------------
    @property
    def lam_range(self) -> tuple[float, float]:
        """(λ_min, λ_max) in metres."""
        return float(self.lam.min()), float(self.lam.max())

    @property
    def coupling_label(self) -> str:
        return COUPLING_LABELS.get(self.coupling, self.coupling)

    def interp(self, lam_query: np.ndarray) -> np.ndarray:
        """
        Log-log linear interpolation of the bound at arbitrary λ values.
        Points outside the covered range return NaN.
        """
        log_lam = np.log10(self.lam)
        log_g   = np.log10(self.g_bound)
        log_q   = np.log10(lam_query)
        return 10 ** np.interp(log_q, log_lam, log_g,
                               left=np.nan, right=np.nan)

    def __repr__(self) -> str:
        lo, hi = self.lam_range
        return (
            f"<ConstraintDataset V{self.pot_code} {self.coupling} "
            f"{self.pair} [{self.reference}] "
            f"λ=[{lo:.2e},{hi:.2e}] m>"
        )


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

class ConstraintDB:
    """
    Central registry of all constraint datasets loaded from a directory tree.

    Directory layout expected:
        root/
          {coupling}/         e.g. gAgA/, gAgV/, …
            *.csv

    or a flat directory of CSVs — both are handled.

    Parameters
    ----------
    root_dir : str
        Top-level directory containing the CSV files.
    recursive : bool
        If True (default), search subdirectories recursively.
    """

    def __init__(self, root_dir: str, recursive: bool = True):
        self.root_dir = os.path.abspath(root_dir)
        self._datasets: list[ConstraintDataset] = []
        self._load(recursive)

    # ------------------------------------------------------------------
    # Loading

    def _load(self, recursive: bool) -> None:
        pattern = os.path.join(self.root_dir, "**", "*.csv") if recursive \
                  else os.path.join(self.root_dir, "*.csv")
        paths = glob.glob(pattern, recursive=recursive)
        skipped = 0
        for p in sorted(paths):
            ds = self._load_one(p)
            if ds is not None:
                self._datasets.append(ds)
            else:
                skipped += 1
        print(f"[ConstraintDB] Loaded {len(self._datasets)} datasets "
              f"({skipped} skipped — unrecognised filenames).")

    @staticmethod
    def _load_one(path: str) -> ConstraintDataset | None:
        stem = os.path.splitext(os.path.basename(path))[0]
        meta = parse_filename(stem)
        if meta is None:
            return None
        try:
            df = pd.read_csv(path, header=None, names=["lam", "g_bound"],
                             dtype=float)
            df = df.dropna().sort_values("lam")
            if len(df) < 2:
                return None
            return ConstraintDataset(
                path=path,
                lam=df["lam"].to_numpy(),
                g_bound=df["g_bound"].to_numpy(),
                **{k: meta[k] for k in
                   ("pot_code","author","year","coupling","pair","sector","reference")},
            )
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Querying

    def query(
        self,
        *,
        pot_code: str | list[str] | None = None,
        coupling: str | list[str] | None = None,
        pair: str | list[str] | None = None,
        sector: str | None = None,
    ) -> list[ConstraintDataset]:
        """
        Filter datasets by one or more criteria.

        Parameters
        ----------
        pot_code : potential code(s), e.g. '2' or ['2','3']
        coupling : coupling type(s), e.g. 'gAgA'
        pair     : fermion pair token(s), e.g. 'ee'
        sector   : 'matter' | 'antimatter' | 'unknown'

        Returns a new list; the DB itself is not modified.
        """
        def _listify(v):
            if v is None:
                return None
            return [v] if isinstance(v, str) else list(v)

        pot_codes = _listify(pot_code)
        couplings = _listify(coupling)
        pairs     = _listify(pair)

        results = []
        for ds in self._datasets:
            if pot_codes and ds.pot_code not in pot_codes:
                continue
            if couplings and ds.coupling not in couplings:
                continue
            if pairs and ds.pair not in pairs:
                continue
            if sector and ds.sector != sector:
                continue
            results.append(ds)
        return results

    # ------------------------------------------------------------------
    # Convenience accessors

    @property
    def all(self) -> list[ConstraintDataset]:
        return list(self._datasets)

    @property
    def pot_codes(self) -> list[str]:
        return sorted({ds.pot_code for ds in self._datasets})

    @property
    def couplings(self) -> list[str]:
        return sorted({ds.coupling for ds in self._datasets})

    @property
    def pairs(self) -> list[str]:
        return sorted({ds.pair for ds in self._datasets})

    def __iter__(self) -> Iterator[ConstraintDataset]:
        return iter(self._datasets)

    def __len__(self) -> int:
        return len(self._datasets)

    # ------------------------------------------------------------------
    # Summary

    def summary(self) -> pd.DataFrame:
        """
        Return a DataFrame with one row per dataset — useful for
        cataloguing and checking coverage at a glance.
        """
        rows = []
        for ds in self._datasets:
            lo, hi = ds.lam_range
            rows.append({
                "potential":  ds.pot_code,
                "coupling":   ds.coupling,
                "pair":       ds.pair,
                "sector":     ds.sector,
                "reference":  ds.reference,
                "lam_min_m":  lo,
                "lam_max_m":  hi,
                "n_points":   len(ds.lam),
            })
        return pd.DataFrame(rows).sort_values(
            ["potential", "coupling", "pair", "reference"]
        ).reset_index(drop=True)

    def __repr__(self) -> str:
        return (
            f"<ConstraintDB root='{self.root_dir}' "
            f"n={len(self._datasets)} datasets, "
            f"potentials={self.pot_codes}, "
            f"couplings={self.couplings}>"
        )
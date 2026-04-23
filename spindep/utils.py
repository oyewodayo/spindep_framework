"""
utils.py — Shared constants, mappings, and helper functions.
"""

from __future__ import annotations
import numpy as np

# ---------------------------------------------------------------------------
# Potential term catalogue
# ---------------------------------------------------------------------------

POTENTIAL_MAP: dict[str, dict] = {
    "2":  {"label": "V₂",    "description": "Monopole-dipole (σ·r̂)"},
    "3":  {"label": "V₃",    "description": "Dipole-dipole (σ₁·σ₂)"},
    "8":  {"label": "V₈",    "description": "Velocity-dependent dipole"},
    "45": {"label": "V₄₊₅",  "description": "Spin-orbit coupling"},
    "11": {"label": "V₁₁",   "description": "Monopole-monopole CP-odd"},
    "12": {"label": "V₁₂",   "description": "Mixed monopole-dipole"},
    "14": {"label": "V₁₄",   "description": "Tensor-dipole"},
    "15": {"label": "V₁₅",   "description": "Tensor-dipole (transverse)"},
    "16": {"label": "V₁₆",   "description": "Quadrupole-dipole"},
}

# ---------------------------------------------------------------------------
# Fermion pair classification
# ---------------------------------------------------------------------------

MATTER_PAIRS = frozenset([
    "ee", "eN", "eP", "nn", "pp", "np", "en",
    "ep", "mumu", "emu_matter",
])

ANTIMATTER_PAIRS = frozenset([
    "eebar",   # e⁻–e⁺
    "emu",     # e⁻–μ⁺
    "epbar",   # e⁻–p̄
    "ppbar",   # p–p̄
    "nnbar",   # n–n̄
])

PAIR_LABELS: dict[str, str] = {
    "ee":     "e⁻–e⁻",
    "eebar":  "e⁻–e⁺",
    "emu":    "e⁻–μ⁺",
    "eN":     "e⁻–N",
    "ep":     "e⁻–p",
    "epbar":  "e⁻–p̄",
    "pp":     "p–p",
    "ppbar":  "p–p̄",
    "nn":     "n–n",
    "nnbar":  "n–n̄",
    "np":     "n–p",
    "mumu":   "μ–μ",
}

# ---------------------------------------------------------------------------
# CPT partner pairs
# ---------------------------------------------------------------------------

CPT_PAIRS: list[tuple[str, str]] = [
    ("ee",   "eebar"),   # e⁻e⁻  vs  e⁻e⁺
    ("emu",  "eebar"),   # approximate if no direct e⁻μ⁺ matter counterpart
    ("pp",   "ppbar"),   # p–p   vs  p–p̄
    ("nn",   "nnbar"),   # n–n   vs  n–n̄
    ("ep",   "epbar"),   # e–p   vs  e–p̄
]

# ---------------------------------------------------------------------------
# Coupling type labels
# ---------------------------------------------------------------------------

COUPLING_LABELS: dict[str, str] = {
    "gAgA": "gᴬgᴬ",
    "gAgV": "gᴬgᵛ",
    "gpgp": "gᴾgᴾ",
    "gpgs": "gᴾgˢ",
    "gsgs": "gˢgˢ",
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def logspace_overlap(
    lam1: np.ndarray,
    lam2: np.ndarray,
    n_points: int = 200,
) -> np.ndarray | None:
    """
    Return a log-spaced grid over the overlapping λ range of two arrays.
    Returns None if there is no overlap.
    """
    lo = max(lam1.min(), lam2.min())
    hi = min(lam1.max(), lam2.max())
    if lo >= hi:
        return None
    return np.logspace(np.log10(lo), np.log10(hi), n_points)


def classify_sector(fermion_pair: str) -> str:
    """Return 'matter', 'antimatter', or 'unknown' for a fermion pair token."""
    if fermion_pair in ANTIMATTER_PAIRS:
        return "antimatter"
    if fermion_pair in MATTER_PAIRS:
        return "matter"
    return "unknown"


def potential_label(code: str) -> str:
    """Return the human-readable label for a potential code, e.g. '2' → 'V₂'."""
    return POTENTIAL_MAP.get(code, {}).get("label", f"V_{code}")
"""
spindep — Spin-Dependent Fifth-Force Constraint Analysis Framework
==================================================================
Focused on CPT asymmetry analysis and experimental gap detection
using the Lei Cong et al. (2025) dataset structure.

Usage
-----
from spindep import ConstraintDB
from spindep.asymmetry import CPTAnalyzer
from spindep.gaps import GapFinder

db = ConstraintDB("path/to/data/")
analyzer = CPTAnalyzer(db)
finder = GapFinder(db)
"""

from .loader import ConstraintDB, ConstraintDataset
from .asymmetry import CPTAnalyzer
from .gaps import GapFinder

__version__ = "0.1.0"
__all__ = ["ConstraintDB", "ConstraintDataset", "CPTAnalyzer", "GapFinder"]
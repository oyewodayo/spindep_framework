# // matcher.py
# ============================================================
# SECTOR EQUIVALENCE
# ============================================================
from .parser import SECTOR_EQUIVALENCE

SECTOR_EQUIVALENCE = {

    "ee": ["eebar"],

    "eebar": ["ee"],

    "emu": ["emubar"],

    "emubar": ["emu"],

    "ep": ["epbar"],

    "epbar": ["ep"],

    "nn": ["nnbar"],

    "nnbar": ["nn"],
}


# ============================================================
# CHECK SECTOR COMPATIBILITY
# ============================================================

def compatible_sectors(a_sector, b_sector):
    if a_sector == b_sector:
        return True
    return b_sector in SECTOR_EQUIVALENCE.get(a_sector, [])


# ============================================================
# CHECK DATASET COMPATIBILITY
# ============================================================

def are_compatible(a, b):
    return (
        a.coupling == b.coupling and
        a.potential == b.potential and
        a.interaction_class == b.interaction_class and
        compatible_sectors(a.sector, b.sector) and
        a.contains_antimatter != b.contains_antimatter
    )


# ============================================================
# BUILD MATCHED PAIRS
# ============================================================

def build_pairs(datasets):
    pairs = []
    for i in range(len(datasets)):
        for j in range(i + 1, len(datasets)):
            a = datasets[i]
            b = datasets[j]
            if are_compatible(a, b):
                matter     = a if not a.contains_antimatter else b
                antimatter = b if not a.contains_antimatter else a
                pairs.append((matter, antimatter))
    return pairs
# // parser.py
from pathlib import Path
from dataclasses import dataclass

import pandas as pd
import re


# ============================================================
# DATASET OBJECT
# ============================================================

@dataclass
class ConstraintDataset:
    filepath: Path
    filename: str
    coupling: str
    interaction_class: str
    potential: str
    source: str
    sector: str
    contains_antimatter: bool
    label: str


# ============================================================
# SECTOR ALIASES
# Raw filename token → canonical sector name
# ============================================================

SECTOR_ALIASES = {

    # electron sectors
    "ebare":     "eebar",
    "ebar":      "eebar",
    "ebarpar":   "epbar",
    "ebarpabr":  "epbar",   # double-mangled epbar
    "ebarpbar":  "epbar",

    # muon sectors
    "emubare":   "emubar",
    "emubar":    "emubar",
    "emubar":    "emubar",
    "mumubare":  "mumubar",

    # nucleon sectors
    "epbare":    "epbar",
    "nnbare":    "nnbar",
    "ppbare":    "ppbar",
    "pnbar":     "npbar",
    "np":        "np",      # neutron-proton (matter)
    "pn":        "np",      # alias

    # nucleus sectors
    "nN":        "nN",
    "pN":        "pN",
    "eN":        "eN",

   # --- new: exotic lepton sectors ---
    "muplus":   "mubar",      # μ⁺ antimuon
    "eeplus":   "eebar",      # e⁺e⁻ positronium-like
    "mu":       "mu",         # bare muon (Supernova_mu_mu → mumu handled below)

   # --- new: exotic hadronic sectors ---
    "antipHe":  "antipHe",    # antiproton-Helium
    "ddmu":     "ddmu",       # muonic deuterium
    "muN":      "muN",        # muon-nucleus

    # --- new: experiment-type labels (map to their fermion sector) ---
    "Casimir":  "ee",         # Casimir = electron-electron
    "EMM":      "eN",         # electron-molecule = lepton-nucleon
    "EEP":      "eN",         # equivalence principle = lepton-nucleon
    "Torsion":  "ee",         # torsion balance = electron-electron
    "MS":       "nN",         # molecular spectroscopy = nucleon-nucleus

    # astrophysical / special
    "eastro":    "eastro",
    "eeastro":   "eastro",
    "NNastro":   "NNastro",
    "eNastro":  "eastro",   # 1a_eNastro_m_abs
    "eNastro":  "eNastro",  # or keep as distinct astrophysical sector
    "NN":       "nn",       # 45voronin, 45Su files  
    "NNastro":  "NNastro",  # 1aNNastro_m_abs — keep as-is
    "eeastro":  "eastro",
    "eNastro":  "eNastro",
    "NNastro":  "NNastro",
    "nNastro":  "nNastro",
    "pNastro":  "pNastro",
}


# ============================================================
# FERMION MAP  (canonical sector → display label)
# ============================================================

FERMION_MAP = {

    # lepton-lepton
    "ee":      "e⁻-e⁻",
    "eebar":   "e⁻-e⁺",
    "emu":     "e-μ",
    "emubar":  "e-μ̄",
    "mumu":    "μ-μ",
    "mumubar": "μ-μ̄",

    # lepton-nucleon
    "ep":      "e-p",
    "epbar":   "e-p̄",
    "en":      "e-n",
    "enbar":   "e-n̄",
    "np":      "n-p",
    "npbar":   "n-p̄",

    # lepton-nucleus
    "eN":      "e-N",
    "eNbar":   "e-N̄",
    "pN":      "p-N",
    "nN":      "n-N",

    # nucleon-nucleon
    "nn":      "n-n",
    "nnbar":   "n-n̄",
    "pp":      "p-p",
    "ppbar":   "p-p̄",

    # exotic lepton
    "mu":       "μ",
    "mumu":     "μ-μ",
    "mubar":    "μ̄",
    "muN":      "μ-N",

    # exotic hadronic
    "antipHe":  "p̄-He",
    "ddmu":     "dd-μ",

    # astrophysical
    "eastro":  "e (astro)",
    "NNastro": "N-N (astro)",
    "NNastro":  "N-N (astro)",
    "eNastro":  "e-N (astro)",  
    "eastro":   "e (astro)",
    "pNastro":  "p-N (astro)",
}


# ============================================================
# ANTIMATTER SECTORS  (canonical forms only)
# ============================================================

ANTIMATTER_SECTORS = {
    "eebar",
    "emubar",
    "mumubar",
    "epbar",
    "enbar",
    "npbar",
    "eNbar",
    "nnbar",
    "ppbar",
}


# ============================================================
# MATTER-ANTIMATTER EQUIVALENCE
# ============================================================

SECTOR_EQUIVALENCE = {
    "ee":      ["eebar"],
    "eebar":   ["ee"],
    "emu":     ["emubar"],
    "emubar":  ["emu"],
    "mumu":    ["mumubar"],
    "mumubar": ["mumu"],
    "ep":      ["epbar"],
    "epbar":   ["ep"],
    "en":      ["enbar"],
    "enbar":   ["en"],
    "np":      ["npbar"],
    "npbar":   ["np"],
    "eN":      ["eNbar"],
    "eNbar":   ["eN"],
    "nn":      ["nnbar"],
    "nnbar":   ["nn"],
    "pp":      ["ppbar"],
    "ppbar":   ["pp"],
}


FILENAME_SECTOR_OVERRIDES = {
    "Alighanbari_2020":   ("ep",   False),   # HD⁺ spectroscopy → e-p
    "Hoskins_1985":       ("nn",   False),   # torsion → n-n
    "Kapner_2007":        ("ee",   False),   # torsion → e-e
    "Chen_2016":          ("ee",   False),
    "Tan_2020":           ("ee",   False),
    "Lee_2020":           ("nn",   False),
    "Bordag_2001":        ("ee",   False),
    "Delaunay_2017":      ("ee",   False),
    "Colliders":          ("ee",   False),
    "New_constriants_1":  ("ee",   False),
    "New_constriants_2":  ("ee",   False),
    "Neutron_scattering": ("nn",   False),
    "neutron_scattering": ("nn",   False),
    "Supernova_mu_mu":    ("mumu", False),
}


# ============================================================
# KNOWN SECTORS
# ============================================================

KNOWN_SECTORS = set(FERMION_MAP.keys())


# ============================================================
# TOKENS TO SKIP IN SECTOR SEARCH
# ============================================================

SKIP_TOKENS = {"m", "M", "abs", "ABS", "copy", "Copy"}


# ============================================================
# BUILD DISPLAY LABEL
# ============================================================

def build_label(source, sector):
    pair = FERMION_MAP.get(sector, sector)
    return f"{source} ({pair})"


# ============================================================
# NORMALIZE SECTOR
# ============================================================

def normalize_sector(raw):

    s = raw.strip()

    # Strip filesystem artifacts like " copy"
    s = re.sub(r"\s*copy\s*$", "", s, flags=re.IGNORECASE)

    # Remove separators
    s = s.replace("-", "")

    # Encode explicit antiparticle + sign
    s = s.replace("+", "bar")

    # Strip stray unicode minus
    s = s.replace("−", "")

    # Resolve alias
    s = SECTOR_ALIASES.get(s, s)

    return s


# ============================================================
# EXTRACT SECTOR FROM PARTS
# Walk backward, find first token that looks like a sector
# ============================================================
def extract_sector(parts):

    skip = {"m", "M", "abs", "ABS", "copy"}
    candidates = []

    for p in reversed(parts):
        p_clean = p.strip()

        if re.match(r"^\d+$", p_clean):
            continue
        if re.match(r"^V\d+(\+\d+)?$", p_clean):
            continue
        if p_clean in skip:
            continue
        if re.match(r"^[a-zA-Z]", p_clean):
            candidates.append(p_clean)

    if not candidates:
        return "UNKNOWN"

    # If last two candidates are both short (≤2 chars), 
    # they're likely a split sector like "p"+"N" → "pN"
    if len(candidates) >= 2:
        a, b = candidates[0], candidates[1]
        if len(a) <= 2 and len(b) <= 2 and not b[0].isupper() == False:
            joined = b + a   # reversed order since we walked backward
            if joined in KNOWN_SECTORS or joined in SECTOR_ALIASES:
                return joined

    return candidates[0]

# ============================================================
# EXTRACT POTENTIAL
# ============================================================

def extract_potential(parts):

    for p in parts:
        if re.match(r"^V\d+(\+\d+)?$", p):
            return p
        # bare number like "2", "45" at start of filename
        if re.match(r"^\d+[a-z]?$", p) and len(p) <= 3:
            return f"V{p}"

    m = re.match(r"^(\d+[a-z]?)", parts[0])
    if m:
        return f"V{m.group(1)}"

    return "UNKNOWN"


# ============================================================
# EXTRACT YEAR
# ============================================================

def extract_year(parts):
    for p in parts:
        if re.match(r"^\d{4}$", p):
            return p
    return "UNKNOWN"


# ============================================================
# EXTRACT AUTHOR
# ============================================================

def extract_author(parts):

    for p in parts:

        if re.match(r"^\d+$", p):
            continue

        if re.match(r"^V?\d+[a-z]?$", p):
            continue

        if p in SKIP_TOKENS:
            continue

        if any(c.isalpha() for c in p):
            # Strip leading potential digit prefix e.g. "3Fadeev" → "Fadeev"
            author = re.sub(r"^\d+[a-z]?", "", p)
            if author:
                return author

    return "UnknownAuthor"


# ============================================================
# PARSE DATASET
# ============================================================

def parse_dataset(filepath):

    filepath = Path(filepath)
    name = filepath.stem

    # Strip filesystem copy suffix from stem
    name_clean = re.sub(r"\s*copy\s*$", "", name, flags=re.IGNORECASE)

    parts = name_clean.split("_")

    try:

        potential         = extract_potential(parts)
        year              = extract_year(parts)
        author            = extract_author(parts)
        sector_raw        = extract_sector(parts)
        sector            = normalize_sector(sector_raw)
        contains_antimatter = sector in ANTIMATTER_SECTORS


        # --- override for files with no sector token ---
        if name_clean in FILENAME_SECTOR_OVERRIDES:
            sector, contains_antimatter = FILENAME_SECTOR_OVERRIDES[name_clean]
        else:
            sector_raw          = extract_sector(parts)
            sector              = normalize_sector(sector_raw)
            contains_antimatter = sector in ANTIMATTER_SECTORS

            if sector not in KNOWN_SECTORS:
                print(f"[WARN] Unrecognized sector {sector!r} (raw={sector_raw!r}) in {name}")


        coupling          = filepath.parts[-3]
        interaction_class = filepath.parts[-2]
        source            = f"{author}{year}"
        label             = build_label(source, sector)

        return ConstraintDataset(
            filepath=filepath,
            filename=name,
            coupling=coupling,
            interaction_class=interaction_class,
            potential=potential,
            source=source,
            sector=sector,
            contains_antimatter=contains_antimatter,
            label=label,
        )

    except Exception as e:
        print(f"\n[PARSE ERROR] {name}: {e}")
        return None


# ============================================================
# DISCOVER ALL DATASETS
# ============================================================

def discover_datasets(root):

    root = Path(root)
    datasets = []

    for filepath in root.rglob("*.csv"):
        parsed = parse_dataset(filepath)
        if parsed is not None:
            datasets.append(parsed)

    return datasets


# ============================================================
# LOAD CSV DATA
# ============================================================

def load_dataset(filepath):

    df = pd.read_csv(
        filepath,
        header=None,
        names=["lambda_m", "coupling_abs"]
    )

    df = df.apply(
        pd.to_numeric,
        errors="coerce"
    ).dropna()

    df = df[
        (df["lambda_m"] > 0) &
        (df["coupling_abs"] > 0)
    ]

    return df.sort_values("lambda_m").reset_index(drop=True)
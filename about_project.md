# SPINDEP

**Spin-Dependent Exotic Interaction Analysis Framework**

A Python pipeline for systematic analysis of matter–antimatter asymmetry in spin-dependent exotic interactions, built for M.Sc./Ph.D.-level research in physics beyond the Standard Model.

---

## Overview

SPINDEP automates the comparison of experimental coupling-constant upper bounds between matter and antimatter sectors across a range of interaction ranges λ. For each compatible matter–antimatter pair, it:

1. Discovers and classifies constraint datasets from a structured directory tree
2. Matches matter datasets to their antimatter conjugates
3. Interpolates both constraint curves onto a common log-spaced λ grid
4. Computes the **asymmetry parameter** A_α = (g_matter − g_antimatter) / (g_matter + g_antimatter)
5. Runs a χ² sensitivity test to quantify the statistical significance of any observed asymmetry
6. Generates publication-quality comparison plots
7. Exports a full PDF analysis report with per-pair statistics

The framework is designed around the Dobrescu–Mocioiu potential classification (V1–V16) and covers lepton-lepton, lepton-nucleon, and nucleon-nucleon fermion sectors.

---

## Physics Background

### Potentials

Spin-dependent exotic interactions between fermions are parameterised through a set of non-relativistic potentials V_n derived from the most general Lorentz-invariant interaction Lagrangian. Each potential has a distinct spin-velocity structure and couples to specific combinations of scalar (g_S), pseudoscalar (g_P), vector (g_V), and axial-vector (g_A) couplings.

| Potential | Type | Coupling | Description |
|-----------|------|----------|-------------|
| V1 | Monopole-monopole | g_S g_S | Yukawa scalar |
| V2 | Spin-spin | g_A g_A | Axial-axial |
| V3 | Dipole-dipole | g_P g_P | Pseudoscalar |
| V4+5 | Spin-velocity | g_A g_V | Axial-vector |
| V8 | Monopole-dipole | g_S g_P | Scalar-pseudoscalar |
| V9+10 | Spin-orbit | g_P g_S | Pseudoscalar-scalar |
| V11 | Quadratic spin-velocity | g_A g_V | Transverse spin coupling |

### Asymmetry Parameter

For each pair of matter (m) and antimatter (ā) datasets, the asymmetry is defined pointwise across the shared λ range:

```
A_α(λ) = [g_m(λ) − g_ā(λ)] / [g_m(λ) + g_ā(λ)]
```

- **A_α → +1**: matter constraint is much weaker (less constrained)
- **A_α → −1**: antimatter constraint is much weaker
- **A_α ≈ 0**: matter and antimatter bounds are consistent — CPT symmetry respected within experimental sensitivity

### Fermion Sectors

| Canonical label | Physical system | Matter | Antimatter partner |
|-----------------|-----------------|--------|--------------------|
| `ee` | Electron-electron | ✓ | `eebar` (e⁻e⁺) |
| `emu` | Electron-muon | ✓ | `emubar` (e-μ̄) |
| `ep` | Electron-proton | ✓ | `epbar` (e-p̄) |
| `en` | Electron-neutron | ✓ | `enbar` |
| `np` | Neutron-proton | ✓ | `npbar` |
| `nn` | Neutron-neutron | ✓ | `nnbar` (n-n̄) |
| `pp` | Proton-proton | ✓ | `ppbar` (p-p̄) |
| `eN` | Electron-nucleus | ✓ | `eNbar` |
| `mumu` | Muon-muon | ✓ | `mumubar` (μ-μ̄) |

---

## Installation

### Prerequisites

- Python 3.10+
- Ubuntu/WSL (tested on Ubuntu 22.04)

### Setup

```bash
git clone https://github.com/your-org/spindep_framework.git
cd spindep_framework/spindep

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### Dependencies

```
numpy
scipy
pandas
matplotlib
reportlab
```

Install manually if needed:

```bash
pip install numpy scipy pandas matplotlib reportlab
```

---

## Project Structure

```
spindep_framework/
└── spindep/
    ├── main.py                    # Entry point
    ├── datasets/
    │   └── normalized/            # Constraint CSV files, organised by coupling/class
    │       ├── gAgA/
    │       │   ├── lepton-lepton/
    │       │   │   ├── 2Almasi2020_m_abs_ee.csv
    │       │   │   ├── 3Fadeev_2022_2_m_abs_ebare.csv
    │       │   │   └── ...
    │       │   └── lepton-nucleon/
    │       │       └── ...
    │       ├── gpgp/
    │       ├── gsgs/
    │       ├── gVgV/
    │       └── V1/
    ├── results/
    │   ├── plots/                 # PNG comparison plots (one per pair)
    │   ├── tables/
    │   │   ├── dataset_registry.csv   # All discovered datasets
    │   │   └── asymmetry_summary.csv  # Per-pair statistics
    │   └── reports/
    │       └── asymmetry_report.pdf   # Full analysis report
    └── src/
        ├── __init__.py
        ├── parser.py              # Dataset discovery & metadata extraction
        ├── matcher.py             # Matter-antimatter pair matching
        ├── interpolation.py       # Log-space interpolation
        ├── asymmetry.py           # Asymmetry computation
        ├── statistics.py          # Chi-squared sensitivity
        ├── plotting.py            # Matplotlib plots
        ├── reporting.py           # PDF report generation (reportlab)
        └── pipeline.py            # Orchestration
```

---

## Dataset File Naming Convention

All CSV files must follow a strict naming convention for the parser to correctly classify them:

```
{V}{Author}{Year}_{m}_{abs}_{sector}.csv
```

| Token | Meaning | Examples |
|-------|---------|---------|
| `{V}` | Potential number prefix | `2`, `3`, `45`, `1a` |
| `{Author}` | First author surname | `Fadeev`, `Karshenboim`, `Hunter` |
| `{Year}` | Publication year (4 digits) | `2022`, `2013` |
| `m` | Matter-sector flag | always `m` |
| `abs` | Absolute value flag | always `abs` |
| `{sector}` | Fermion sector | `ee`, `ebare`, `ep`, `epbar`, `en`, `nn`, `emu`, `emubar` |

### Antimatter sector aliases recognised

The parser automatically resolves alternate spellings to canonical sector names:

| Filename token | Canonical sector |
|---------------|-----------------|
| `ebare` | `eebar` |
| `ebarpabr` | `epbar` |
| `emubare` | `emubar` |
| `ebar` | `eebar` |
| `epbare` | `epbar` |
| `nnbare` | `nnbar` |

### Directory structure (for coupling/class extraction)

```
datasets/normalized/{coupling}/{interaction_class}/{filename}.csv
                     ^           ^
                     |           |
                     filepath.parts[-3]
                                 filepath.parts[-2]
```

Example:
```
datasets/normalized/gAgA/lepton-lepton/2Fadeev_2022_4_m_abs_ee.csv
         ↑          ↑    ↑
         root       coupling  interaction_class
```

### CSV format

Each CSV contains two columns with **no header**:

```
lambda_m,coupling_abs
1.23e-05,4.56e-12
...
```

| Column | Unit | Description |
|--------|------|-------------|
| `lambda_m` | metres | Interaction range λ |
| `coupling_abs` | dimensionless | Upper bound on |coupling constant| |

Both columns must be strictly positive. Rows with non-numeric or non-positive values are silently dropped.

---

## Running the Pipeline

```bash
cd spindep_framework/spindep
source .venv/bin/activate
python3 main.py
```

### Expected output

```
============================================================
DISCOVERING DATASETS
============================================================
Found 273 datasets
Found 14 valid pairs
--------------------------------------------------
2Karshenboim_2011_1_millionev_abs_ep
3Fadeev_2022_1_m_abs_ebarpabr
--------------------------------------------------
...
[REPORT] Saved → results/reports/asymmetry_report.pdf
============================================================
PIPELINE COMPLETE
============================================================
```

### Output files

| File | Description |
|------|-------------|
| `results/tables/dataset_registry.csv` | Full metadata for every discovered dataset |
| `results/tables/asymmetry_summary.csv` | Per-pair: χ², dof, p-value, mean \|A_α\|, λ range |
| `results/plots/{coupling}_{potential}_{sector}.png` | Constraint comparison + asymmetry plot |
| `results/reports/asymmetry_report.pdf` | Full PDF report (cover, summary table, per-pair sections) |

---

## Module Reference

### `parser.py`

Responsible for discovering CSV files and extracting structured metadata from filenames and directory paths.

**Key functions:**

```python
discover_datasets(root: str | Path) -> list[ConstraintDataset]
```
Recursively finds all `.csv` files under `root` and returns a list of parsed `ConstraintDataset` objects.

```python
parse_dataset(filepath: str | Path) -> ConstraintDataset | None
```
Extracts `coupling`, `interaction_class`, `potential`, `source`, `sector`, `contains_antimatter`, and `label` from a single file path. Returns `None` on parse failure.

```python
load_dataset(filepath: str | Path) -> pd.DataFrame
```
Reads a CSV and returns a cleaned DataFrame with columns `lambda_m` and `coupling_abs`, sorted by `lambda_m`.

**ConstraintDataset fields:**

| Field | Type | Description |
|-------|------|-------------|
| `filepath` | Path | Absolute path to CSV |
| `filename` | str | Stem (no extension) |
| `coupling` | str | Coupling family (from directory) |
| `interaction_class` | str | Fermion class (from directory) |
| `potential` | str | e.g. `V2`, `V4+5` |
| `source` | str | e.g. `Fadeev2022` |
| `sector` | str | Canonical sector label |
| `contains_antimatter` | bool | True for antimatter sectors |
| `label` | str | Human-readable legend label |

---

### `matcher.py`

Pairs matter datasets with their antimatter conjugates.

```python
build_pairs(datasets: list[ConstraintDataset]) -> list[tuple]
```

Returns a list of `(matter_ds, antimatter_ds)` tuples. Two datasets form a valid pair when:

- Same `coupling`
- Same `potential`
- Same `interaction_class`
- Physically conjugate sectors (e.g. `ee` ↔ `eebar`)
- Exactly one has `contains_antimatter = True`

```python
are_compatible(a: ConstraintDataset, b: ConstraintDataset) -> bool
compatible_sectors(a_sector: str, b_sector: str) -> bool
```

---

### `interpolation.py`

```python
make_log_interpolator(df: pd.DataFrame) -> Callable
```

Constructs a log-log linear interpolator from a dataset. Returns a function `f(lam) -> g` that maps interaction range values to coupling bounds, extrapolating as `nan` outside the data range.

---

### `asymmetry.py`

```python
compute_asymmetry(
    df_m: pd.DataFrame,
    df_a: pd.DataFrame,
    n_points: int = 300
) -> tuple[np.ndarray, np.ndarray, tuple] | tuple[None, None, None]
```

Computes the asymmetry parameter on a shared log-spaced λ grid. Returns `(lam_grid, A, (g_m, g_a))` or `(None, None, None)` if the datasets have no overlapping λ range.

---

### `statistics.py`

```python
chi_squared_sensitivity(
    g_m: np.ndarray,
    g_a: np.ndarray,
    sigma_frac: float = 0.1
) -> tuple[float, int, float]
```

Computes a χ² statistic measuring the significance of the difference between matter and antimatter coupling bounds, using a fractional uncertainty model σ = sigma_frac × (g_m + g_a)/2. Returns `(chi2_total, dof, p_value)`.

---

### `plotting.py`

```python
plot_asymmetry(
    lam, A, g_m, g_a,
    matter_ds, antimatter_ds,
    output_path
)
```

Generates a two-panel plot:
- **Top panel**: log-log plot of matter and antimatter coupling bounds vs λ
- **Bottom panel**: asymmetry parameter A_α vs λ with shaded regions indicating which sector is more constrained

---

### `reporting.py`

```python
generate_report(
    summary_rows: list[dict],
    plots_dir: str | Path,
    output_path: str | Path
) -> Path
```

Generates a structured PDF report using ReportLab. The report contains:
- Cover page with run metadata
- Summary table of all pairs
- One dedicated section per pair: source metadata, statistics table, plot, and physical interpretation

---

## Extending the Framework

### Adding new sectors

Edit `FERMION_MAP`, `ANTIMATTER_SECTORS`, `SECTOR_EQUIVALENCE`, and `SECTOR_ALIASES` in `parser.py`:

```python
# Add to FERMION_MAP
"taubar": "τ̄",

# Add to ANTIMATTER_SECTORS
ANTIMATTER_SECTORS.add("taubar")

# Add to SECTOR_EQUIVALENCE
SECTOR_EQUIVALENCE["tau"] = ["taubar"]
SECTOR_EQUIVALENCE["taubar"] = ["tau"]

# Add filename alias if needed
SECTOR_ALIASES["taub"] = "taubar"
```

### Adding new potentials

Edit `POTENTIAL_INFO` in `classifier.py`:

```python
POTENTIAL_INFO["V12"] = {
    "type": "tensor-tensor",
    "description": "Tensor-tensor interaction",
    "couplings": ["gTgT"]
}
```

### Handling non-standard filenames

For datasets whose filenames do not contain a parseable sector token, add an entry to `FILENAME_SECTOR_OVERRIDES` in `parser.py`:

```python
FILENAME_SECTOR_OVERRIDES["MyAuthor_2024"] = ("ep", False)
#                                               ^     ^
#                                              sector  contains_antimatter
```

---

## Interpreting Results

### asymmetry_summary.csv columns

| Column | Description |
|--------|-------------|
| `coupling` | Coupling family (e.g. `gAgA`) |
| `potential` | Potential label (e.g. `V2`) |
| `interaction_class` | Fermion class (e.g. `lepton-lepton`) |
| `sector` | Matter sector (e.g. `ee`) |
| `matter_source` | Citation key of matter dataset |
| `antimatter_source` | Citation key of antimatter dataset |
| `mean_abs_A` | Mean of \|A_α(λ)\| over the shared range |
| `chi2` | Total χ² statistic |
| `dof` | Degrees of freedom (number of valid λ points) |
| `p_value` | p-value from chi-squared CDF |
| `lambda_min` | Minimum shared interaction range (m) |
| `lambda_max` | Maximum shared interaction range (m) |

### Significance thresholds

| p-value | Interpretation |
|---------|---------------|
| p < 0.001 | *** Strong evidence for asymmetry |
| p < 0.01  | **  Moderate evidence |
| p < 0.05  | *   Marginal evidence |
| p ≥ 0.05  | ns  No significant asymmetry detected |

### Common diagnostics

**Found N datasets but 0 valid pairs**
The most common cause is sector misclassification. Run the debug block in `pipeline.py` to inspect parsed sectors and check whether `contains_antimatter` is correctly assigned.

**[SKIP] No overlapping lambda range**
The matter and antimatter datasets cover different λ ranges. This is a physical/experimental limitation of the available data, not a code error.

**[WARN] Unrecognized sector**
The sector token extracted from the filename is not in `KNOWN_SECTORS`. Either add an alias to `SECTOR_ALIASES` or add a `FILENAME_SECTOR_OVERRIDES` entry.

---

## Citation

If you use this framework in published work, please cite the relevant experimental constraint papers listed in `dataset_registry.csv` alongside this repository.

---

## License

Academic use. Contact the author for redistribution rights.

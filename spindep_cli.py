#!/usr/bin/env python3
# // spindep_cli.py
"""
SPINDEP Command-Line Interface
==============================

A single entry-point command that gives non-technical users full
access to the SPINDEP framework without touching any code.

USAGE
-----
# Full pipeline on a dataset folder:
  python spindep_cli.py run --data ./my_datasets

# Analyse just one pair of CSV files:
  python spindep_cli.py pair matter.csv antimatter.csv

# Import datasets from a different directory structure:
  python spindep_cli.py import --from /path/to/data --coupling gAgA --potential V2 --sector ee

# Run gap analysis only:
  python spindep_cli.py gaps --data ./my_datasets

# Run constraint atlas only:
  python spindep_cli.py atlas --data ./my_datasets

# Validate your dataset folder before a full run:
  python spindep_cli.py validate --data ./my_datasets

# Quick CPT test on two CSV files (no folder structure needed):
  python spindep_cli.py test matter.csv antimatter.csv --plot

INSTALL AS SYSTEM COMMAND
--------------------------
  # Option 1: alias in your shell profile
  echo 'alias spindep="python3 /path/to/spindep_cli.py"' >> ~/.bashrc
  source ~/.bashrc
  spindep run --data ./my_datasets

  # Option 2: make executable
  chmod +x spindep_cli.py
  ./spindep_cli.py run --data ./my_datasets
"""

import argparse
import sys
import shutil
import textwrap
from pathlib import Path
from datetime import datetime


# ============================================================
# COLOUR OUTPUT (works on any terminal that supports ANSI)
# ============================================================

class C:
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    BLUE   = "\033[94m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    RESET  = "\033[0m"
    GREY   = "\033[90m"

def ok(msg):    print(f"{C.GREEN}  ✓  {C.RESET}{msg}")
def info(msg):  print(f"{C.BLUE}  ●  {C.RESET}{msg}")
def warn(msg):  print(f"{C.YELLOW}  ⚠  {C.RESET}{msg}")
def err(msg):   print(f"{C.RED}  ✗  {C.RESET}{msg}")
def head(msg):  print(f"\n{C.BOLD}{C.CYAN}{msg}{C.RESET}\n{'─'*60}")
def grey(msg):  print(f"{C.GREY}{msg}{C.RESET}")


# ============================================================
# SPINDEP LOCATION DETECTION
# ============================================================

def find_spindep_src():
    """
    Locate the spindep/src directory, trying several strategies:
    1. Same directory as this script
    2. Parent directory (if running from spindep/)
    3. SPINDEP_HOME environment variable
    4. Standard install path ~/spindep_framework/spindep
    """
    import os

    candidates = [
        Path(__file__).parent / "src",
        Path(__file__).parent.parent / "spindep" / "src",
        Path(os.environ.get("SPINDEP_HOME", "")) / "src",
        Path.home() / "spindep_framework" / "spindep" / "src",
    ]
    for c in candidates:
        if c.exists() and (c / "parser.py").exists():
            return c
    return None


def load_spindep():
    """Import spindep modules, handling path setup automatically."""
    src = find_spindep_src()
    if src is None:
        err("Cannot find SPINDEP source files (src/parser.py).")
        err("Set the SPINDEP_HOME environment variable to your spindep directory:")
        grey("  export SPINDEP_HOME=/path/to/spindep_framework/spindep")
        sys.exit(1)

    sys.path.insert(0, str(src.parent))
    try:
        from src.parser          import discover_datasets, load_dataset, parse_dataset, ConstraintDataset
        from src.matcher         import build_pairs
        from src.asymmetry       import compute_asymmetry
        from src.statistics      import chi_squared_from_datasets, chi_squared_sensitivity
        from src.unit_conversion import convert_lambda_to_metres, audit_units
        from src.pipeline        import run_pipeline
        return {
            "discover_datasets":        discover_datasets,
            "load_dataset":             load_dataset,
            "parse_dataset":            parse_dataset,
            "ConstraintDataset":        ConstraintDataset,
            "build_pairs":              build_pairs,
            "compute_asymmetry":        compute_asymmetry,
            "chi_squared_from_datasets":chi_squared_from_datasets,
            "chi_squared_sensitivity":  chi_squared_sensitivity,
            "convert_lambda_to_metres": convert_lambda_to_metres,
            "audit_units":              audit_units,
            "run_pipeline":             run_pipeline,
        }
    except ImportError as e:
        err(f"Failed to import SPINDEP modules: {e}")
        err("Make sure all src/*.py files are present.")
        sys.exit(1)


# ============================================================
# COMMAND: run
# ============================================================

def cmd_run(args):
    """Full pipeline run on a dataset folder."""
    head("SPINDEP — Full Pipeline Run")

    data_root    = Path(args.data).resolve()
    results_root = Path(args.output).resolve() if args.output else data_root.parent / "results"

    if not data_root.exists():
        err(f"Data directory not found: {data_root}")
        sys.exit(1)

    # Check if it's already normalized/ or needs to be
    normalized = data_root / "normalized" if (data_root / "normalized").exists() else data_root

    info(f"Data:    {normalized}")
    info(f"Results: {results_root}")

    sp = load_spindep()
    sp["run_pipeline"](
        dataset_root=str(normalized),
        results_root=str(results_root)
    )

    ok(f"Done! Report saved to: {results_root / 'reports'}")
    ok(f"Figures saved to:       {results_root / 'figures'}")
    ok(f"Tables saved to:        {results_root / 'tables'}")


# ============================================================
# COMMAND: test (quick CPT test on two CSV files)
# ============================================================

def cmd_test(args):
    """
    Quick CPT test between two CSV files.
    No folder structure required — just pass two files.
    """
    head("SPINDEP — Quick CPT Test")

    matter_path    = Path(args.matter).resolve()
    antimatter_path = Path(args.antimatter).resolve()

    for p in [matter_path, antimatter_path]:
        if not p.exists():
            err(f"File not found: {p}")
            sys.exit(1)

    sp = load_spindep()

    info(f"Matter:    {matter_path.name}")
    info(f"Antimatter:{antimatter_path.name}")
    print()

    # Load data
    df_m = sp["load_dataset"](matter_path)
    df_a = sp["load_dataset"](antimatter_path)

    # Unit conversion
    df_m, _, unit_m = sp["convert_lambda_to_metres"](df_m, matter_path.stem,    verbose=False)
    df_a, _, unit_a = sp["convert_lambda_to_metres"](df_a, antimatter_path.stem, verbose=False)

    info(f"Matter lambda range:    {df_m['lambda_m'].min():.3e} → {df_m['lambda_m'].max():.3e} m ({unit_m})")
    info(f"Antimatter lambda range:{df_a['lambda_m'].min():.3e} → {df_a['lambda_m'].max():.3e} m ({unit_a})")

    # Run analysis
    stats = sp["chi_squared_from_datasets"](df_m, df_a, n_points=args.points)

    if stats is None:
        err("No overlapping lambda range between the two datasets.")
        err("The experiments probe different physical scales and cannot be directly compared.")
        sys.exit(0)

    # Print results
    print()
    head("Results")
    print(f"  Lambda overlap:      {stats['lam_grid'].min():.3e} → {stats['lam_grid'].max():.3e} m")
    print(f"  Mean |A_alpha|:      {C.BOLD}{stats['mean_abs_A']:.4f}{C.RESET}  ", end="")
    if stats['mean_abs_A'] > 0.5:
        print(f"{C.RED}(Strong CPT-sensitive asymmetry){C.RESET}")
    elif stats['mean_abs_A'] > 0.2:
        print(f"{C.YELLOW}(Moderate asymmetry){C.RESET}")
    else:
        print(f"{C.GREEN}(Near-symmetric){C.RESET}")

    print(f"\n  Chi-squared (uniform 10%):  {stats['chi2_uniform']:.1f}  (dof={stats['dof_uniform']})")
    print(f"  Chi-squared (weighted):     {C.BOLD}{stats['chi2_weighted']:.1f}{C.RESET}  (dof={stats['dof_weighted']})")
    print(f"  p-value (weighted):         {stats['pval_weighted']:.3e}  ", end="")
    if stats['pval_weighted'] < 0.001:
        print(f"{C.RED}*** highly significant{C.RESET}")
    elif stats['pval_weighted'] < 0.05:
        print(f"{C.YELLOW}* significant{C.RESET}")
    else:
        print(f"{C.GREEN}not significant{C.RESET}")

    print(f"\n  Mean uncertainty (matter):    {stats['mean_sigma_m']*100:.1f}%")
    print(f"  Mean uncertainty (antimatter):{stats['mean_sigma_a']*100:.1f}%")
    print(f"  chi2 ratio (weighted/uniform):{stats['improvement']:.3f}  (< 1 = more conservative)")

    # Optional plot
    if args.plot:
        import numpy as np
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use("Agg")

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

            lam  = stats["lam_grid"]
            g_m  = stats["g_m"]
            g_a  = stats["g_a"]
            A    = stats["A_alpha"]
            valid = np.isfinite(g_m) & np.isfinite(g_a)

            ax1.plot(lam[valid], g_m[valid], "-",  color="#2d6a9f", lw=1.5,
                     label=f"Matter ({matter_path.stem})")
            ax1.plot(lam[valid], g_a[valid], "--", color="#b03a2e", lw=1.5,
                     label=f"Antimatter ({antimatter_path.stem})")
            ax1.set_yscale("log"); ax1.set_xscale("log")
            ax1.set_ylabel("Coupling upper bound |g|")
            ax1.legend(fontsize=8); ax1.grid(True, which="both", ls=":", alpha=0.5)
            ax1.set_title(f"CPT Asymmetry Test\n|A_α| = {stats['mean_abs_A']:.4f}  |  χ²(w) = {stats['chi2_weighted']:.0f}", fontsize=10)

            ax2.fill_between(lam[valid], A[valid], 0,
                             where=A[valid] > 0, color="#2d6a9f", alpha=0.3, label="Matter weaker")
            ax2.fill_between(lam[valid], A[valid], 0,
                             where=A[valid] < 0, color="#b03a2e", alpha=0.3, label="Antimatter weaker")
            ax2.axhline(0, color="black", lw=0.8, ls="--")
            ax2.set_ylim(-1.1, 1.1)
            ax2.set_ylabel("A_α"); ax2.set_xlabel("λ (m)")
            ax2.legend(fontsize=8); ax2.grid(True, which="both", ls=":", alpha=0.5)

            plot_path = Path(args.plot) if args.plot != True else Path("spindep_test_result.png")
            fig.tight_layout()
            fig.savefig(plot_path, dpi=150, bbox_inches="tight")
            plt.close(fig)
            ok(f"Plot saved: {plot_path}")
        except ImportError:
            warn("matplotlib not available — skipping plot")

    # CSV export
    if args.save:
        import pandas as pd
        import numpy as np
        lam  = stats["lam_grid"]
        valid = np.isfinite(stats["g_m"]) & np.isfinite(stats["g_a"])
        df_out = pd.DataFrame({
            "lambda_m":    lam[valid],
            "g_matter":    stats["g_m"][valid],
            "g_antimatter":stats["g_a"][valid],
            "A_alpha":     stats["A_alpha"][valid],
            "sigma_m":     stats["sigma_frac_m"][valid],
            "sigma_a":     stats["sigma_frac_a"][valid],
        })
        df_out.to_csv(args.save, index=False)
        ok(f"Results saved: {args.save}")


# ============================================================
# COMMAND: validate
# ============================================================

def cmd_validate(args):
    """Validate a dataset folder before running the full pipeline."""
    head("SPINDEP — Dataset Validation")

    data_root = Path(args.data).resolve()
    normalized = data_root / "normalized" if (data_root / "normalized").exists() else data_root

    if not normalized.exists():
        err(f"Directory not found: {normalized}")
        sys.exit(1)

    sp = load_spindep()

    info(f"Scanning: {normalized}")
    datasets = sp["discover_datasets"](normalized)
    print()

    # Counts
    total   = len(datasets)
    unknown_pot = [d for d in datasets if d.potential == "UNKNOWN"]
    unknown_sec = [d for d in datasets if d.sector    == "UNKNOWN"]
    antimatter  = [d for d in datasets if d.contains_antimatter]
    matter      = [d for d in datasets if not d.contains_antimatter]

    ok(f"Total datasets discovered:   {total}")
    ok(f"Matter datasets:             {len(matter)}")
    ok(f"Antimatter datasets:         {len(antimatter)}")

    if unknown_pot:
        warn(f"Unknown potential (UNKNOWN): {len(unknown_pot)} files — these cannot be matched")
    else:
        ok("All datasets have recognised potentials")

    if unknown_sec:
        warn(f"Unknown sector (UNKNOWN):    {len(unknown_sec)} files — these cannot be matched")
    else:
        ok("All datasets have recognised sectors")

    # Unit audit
    print()
    sp["audit_units"](datasets, verbose=True)

    # Pair count
    pairs = sp["build_pairs"](datasets)
    print()
    ok(f"Valid matter-antimatter pairs: {len(pairs)}")
    if len(pairs) == 0:
        warn("No pairs found. Check that matter and antimatter files:")
        grey("  1. Are in the same coupling/ folder")
        grey("  2. Have the same potential token")
        grey("  3. Have compatible sector tokens (ee <-> eebar, ep <-> ebarpabr, etc.)")
    else:
        info("Pairs that will be analysed:")
        for m, a in pairs:
            print(f"    {C.BLUE}{m.filename}{C.RESET}  ×  {C.RED}{a.filename}{C.RESET}")


# ============================================================
# COMMAND: import
# ============================================================

def cmd_import(args):
    """
    Import CSV files from an arbitrary folder into the correct
    SPINDEP directory structure, then run the pipeline.
    """
    head("SPINDEP — Import & Run")

    src_dir  = Path(args.src).resolve()
    dest_dir = Path(args.dest).resolve() if args.dest else Path("datasets/normalized")

    coupling          = args.coupling
    interaction_class = args.interaction_class or "lepton-lepton"
    potential         = args.potential
    sector_m          = args.sector_matter
    sector_a          = args.sector_antimatter

    if not src_dir.exists():
        err(f"Source directory not found: {src_dir}")
        sys.exit(1)

    target = dest_dir / coupling / interaction_class
    target.mkdir(parents=True, exist_ok=True)

    csv_files = list(src_dir.glob("*.csv"))
    if not csv_files:
        err(f"No CSV files found in {src_dir}")
        sys.exit(1)

    info(f"Found {len(csv_files)} CSV files in {src_dir}")
    info(f"Copying to {target}")
    print()

    imported = []
    for f in csv_files:
        # Try to construct a canonical filename if not already formatted
        stem = f.stem
        if "_m_abs_" not in stem and "_abs_" not in stem:
            # Rename with potential and sector embedded
            is_anti = any(tok in stem.lower() for tok in ["anti","bar","plus","positron"])
            sector  = sector_a if is_anti else sector_m
            new_name = f"{potential}_{stem}_m_abs_{sector}.csv"
            warn(f"Renaming {f.name} -> {new_name}")
        else:
            new_name = f.name

        dest_file = target / new_name
        shutil.copy2(f, dest_file)
        ok(f"Imported: {new_name}")
        imported.append(dest_file)

    print()
    ok(f"Imported {len(imported)} files into {target}")

    if args.run:
        info("Running pipeline on imported data...")
        sp = load_spindep()
        sp["run_pipeline"](
            dataset_root=str(dest_dir),
            results_root=str(Path("results").resolve())
        )


# ============================================================
# COMMAND: gaps
# ============================================================

def cmd_gaps(args):
    """Generate gap analysis figures only."""
    head("SPINDEP — Gap Analysis")

    data_root = Path(args.data).resolve()
    normalized = data_root / "normalized" if (data_root / "normalized").exists() else data_root
    out_dir = Path(args.output).resolve() if args.output else Path("results/figures")

    sp = load_spindep()
    datasets = sp["discover_datasets"](normalized)
    info(f"Loaded {len(datasets)} datasets")

    sys.path.insert(0, str(find_spindep_src().parent))
    from src.gap_analysis import run_gap_analysis
    run_gap_analysis(datasets, figures_dir=out_dir)
    ok(f"Gap figures saved to: {out_dir / 'gap_analysis'}")


# ============================================================
# COMMAND: atlas
# ============================================================

def cmd_atlas(args):
    """Generate constraint atlas figures only."""
    head("SPINDEP — Constraint Atlas")

    data_root = Path(args.data).resolve()
    normalized = data_root / "normalized" if (data_root / "normalized").exists() else data_root
    out_dir = Path(args.output).resolve() if args.output else Path("results/figures")

    sp = load_spindep()
    datasets = sp["discover_datasets"](normalized)
    info(f"Loaded {len(datasets)} datasets")

    sys.path.insert(0, str(find_spindep_src().parent))
    from src.constraint_plots import run_constraint_plots
    run_constraint_plots(
        datasets=datasets,
        summary_rows=[],
        plots_dir=Path("results/plots"),
        figures_dir=out_dir
    )
    ok(f"Constraint atlas saved to: {out_dir / 'constraint_atlas'}")


# ============================================================
# MAIN PARSER
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        prog="spindep",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(f"""
{C.BOLD}{C.CYAN}SPINDEP — Spin-Dependent Exotic Interaction Analysis Framework{C.RESET}

Analyse matter-antimatter CPT asymmetry in exotic spin-dependent
interactions from published experimental constraint datasets.

{C.BOLD}Quick start:{C.RESET}
  spindep run   --data ./my_datasets
  spindep test  matter.csv antimatter.csv --plot
  spindep validate --data ./my_datasets
        """)
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # ── run ──────────────────────────────────────────────────
    p_run = sub.add_parser("run",
        help="Full pipeline: discover, match, analyse, report",
        description="Run the complete SPINDEP pipeline on a dataset folder.")
    p_run.add_argument("--data",   required=True, metavar="DIR",
        help="Path to dataset folder (containing normalized/ or CSV files)")
    p_run.add_argument("--output", metavar="DIR",
        help="Results output directory (default: <data>/../results)")

    # ── test ─────────────────────────────────────────────────
    p_test = sub.add_parser("test",
        help="Quick CPT test on two CSV files (no folder structure needed)",
        description="Perform a quick CPT asymmetry test between two CSV files.")
    p_test.add_argument("matter",    metavar="MATTER.CSV",
        help="Matter sector constraint CSV file")
    p_test.add_argument("antimatter",metavar="ANTIMATTER.CSV",
        help="Antimatter sector constraint CSV file")
    p_test.add_argument("--plot",    metavar="FILE.PNG", nargs="?", const=True,
        help="Save asymmetry plot (default: spindep_test_result.png)")
    p_test.add_argument("--save",    metavar="FILE.CSV",
        help="Save full results table as CSV")
    p_test.add_argument("--points",  type=int, default=300, metavar="N",
        help="Lambda grid resolution (default: 300)")

    # ── validate ─────────────────────────────────────────────
    p_val = sub.add_parser("validate",
        help="Validate dataset folder structure before running",
        description="Check datasets for naming issues, unit problems, and pairing.")
    p_val.add_argument("--data", required=True, metavar="DIR",
        help="Path to dataset folder")

    # ── import ───────────────────────────────────────────────
    p_imp = sub.add_parser("import",
        help="Import CSV files from any folder into SPINDEP structure",
        description="Copy external CSV files into the correct SPINDEP folder structure.")
    p_imp.add_argument("--from",  dest="src",  required=True, metavar="DIR",
        help="Source folder containing CSV files")
    p_imp.add_argument("--dest",  metavar="DIR",
        help="Destination (default: datasets/normalized)")
    p_imp.add_argument("--coupling",            required=True, metavar="NAME",
        help="Coupling type (e.g. gAgA, gsgs, gVgV)")
    p_imp.add_argument("--potential",           required=True, metavar="Vi",
        help="Potential version (e.g. V2, V3, V11)")
    p_imp.add_argument("--sector-matter",       required=True, metavar="SECTOR",
        help="Matter sector (e.g. ee, ep, en, nn)")
    p_imp.add_argument("--sector-antimatter",   required=True, metavar="SECTOR",
        help="Antimatter sector (e.g. eebar, epbar, enbar)")
    p_imp.add_argument("--interaction-class",   metavar="CLASS",
        help="Interaction class (default: lepton-lepton)")
    p_imp.add_argument("--run",  action="store_true",
        help="Run full pipeline after importing")

    # ── gaps ─────────────────────────────────────────────────
    p_gaps = sub.add_parser("gaps",
        help="Generate gap analysis figures only",
        description="Generate the three gap analysis figures without running the full pipeline.")
    p_gaps.add_argument("--data",   required=True, metavar="DIR")
    p_gaps.add_argument("--output", metavar="DIR")

    # ── atlas ────────────────────────────────────────────────
    p_atl = sub.add_parser("atlas",
        help="Generate constraint atlas figures only",
        description="Generate constraint atlas plots without running the full pipeline.")
    p_atl.add_argument("--data",   required=True, metavar="DIR")
    p_atl.add_argument("--output", metavar="DIR")

    # ── dispatch ─────────────────────────────────────────────
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "run":      cmd_run,
        "test":     cmd_test,
        "validate": cmd_validate,
        "import":   cmd_import,
        "gaps":     cmd_gaps,
        "atlas":    cmd_atlas,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
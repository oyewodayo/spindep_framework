#!/usr/bin/env python3
# // spindep/cli.py
"""
SPINDEP 'spin' command — entry point registered by setup.py.

After   pip install -e .   this becomes the global 'spin' command.

USAGE
─────
  spin run       --data ./datasets          # Full pipeline
  spin test      matter.csv anti.csv        # Quick CPT test on two files
  spin validate  --data ./datasets          # Pre-flight checks
  spin import    --from /data --coupling gAgA --potential V2 ...
  spin gaps      --data ./datasets          # Gap figures only
  spin atlas     --data ./datasets          # Constraint atlas only
  spin config    myconfig.yaml              # Run from a config file
  spin batch     jobs.yaml                  # Run multiple jobs

For help on any command:
  spin <command> --help
"""

import argparse
import sys
import shutil
import textwrap
import json
from pathlib import Path
from datetime import datetime


# ============================================================
# TERMINAL COLOURS
# ============================================================

class C:
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    BLUE   = "\033[94m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    MAGENTA= "\033[95m"
    RESET  = "\033[0m"
    GREY   = "\033[90m"
    DIM    = "\033[2m"

def ok(msg):     print(f"  {C.GREEN}✓{C.RESET}  {msg}")
def info(msg):   print(f"  {C.BLUE}●{C.RESET}  {msg}")
def warn(msg):   print(f"  {C.YELLOW}⚠{C.RESET}  {msg}")
def err(msg):    print(f"  {C.RED}✗{C.RESET}  {msg}", file=sys.stderr)
def grey(msg):   print(f"  {C.GREY}{msg}{C.RESET}")
def blank():     print()

def banner(title):
    width = 62
    print(f"\n{C.BOLD}{C.CYAN}{'─'*width}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}  {title}{C.RESET}")
    print(f"{C.BOLD}{C.CYAN}{'─'*width}{C.RESET}\n")

def section(title):
    print(f"\n{C.BOLD}  {title}{C.RESET}")
    print(f"  {'─' * (len(title)+2)}")


# ============================================================
# SPINDEP MODULE LOADER
# Finds src/ regardless of where the user runs 'spin' from
# ============================================================

def _find_src():
    import os
    candidates = [
        Path(__file__).parent,                                     # installed package
        Path(__file__).parent.parent / "src",                      # dev: spindep/src
        Path(os.environ.get("SPINDEP_HOME", "")) / "src",          # env var override
        Path.home() / "spindep_framework" / "spindep" / "src",     # default install
        Path.cwd() / "src",                                        # current directory
        Path.cwd() / "spindep" / "src",
    ]
    for c in candidates:
        if c.is_dir() and (c / "parser.py").exists():
            return c
    return None


def _load():
    """Import all SPINDEP modules, auto-detecting the source location."""
    src = _find_src()
    if src is None:
        err("Cannot locate SPINDEP source files.")
        blank()
        grey("  Try one of the following:")
        grey("    export SPINDEP_HOME=/path/to/spindep_framework/spindep")
        grey("    cd /path/to/spindep_framework/spindep && spin ...")
        sys.exit(1)

    root = src.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    try:
        from src.parser          import discover_datasets, load_dataset
        from src.matcher         import build_pairs
        from src.asymmetry       import compute_asymmetry
        from src.statistics      import chi_squared_from_datasets
        from src.unit_conversion import convert_lambda_to_metres, audit_units
        from src.pipeline        import run_pipeline
        from src.gap_analysis    import run_gap_analysis
        from src.constraint_plots import run_constraint_plots
        return locals()
    except ImportError as e:
        err(f"Import failed: {e}")
        grey("  Make sure all src/*.py files are present.")
        sys.exit(1)


# ============================================================
# SHARED HELPERS
# ============================================================

def _resolve_data(data_arg):
    """Find the normalized/ directory from a user-supplied path."""
    p = Path(data_arg).resolve()
    if not p.exists():
        err(f"Path not found: {p}")
        sys.exit(1)
    # Accept either the parent folder or normalized/ directly
    if (p / "normalized").is_dir():
        return p / "normalized"
    return p


def _results_dir(output_arg, data_path):
    if output_arg:
        return Path(output_arg).resolve()
    return data_path.parent.parent / "results"


def _print_pair_results(stats, matter_name="matter", anti_name="antimatter"):
    """Pretty-print chi-squared results for a single pair."""
    import numpy as np
    section("CPT Asymmetry Results")

    lam = stats["lam_grid"]
    valid = np.isfinite(stats["g_m"]) & np.isfinite(stats["g_a"])

    print(f"    Lambda overlap:        {lam[valid].min():.3e} → {lam[valid].max():.3e} m")
    print(f"    Valid points:          {valid.sum()} / {len(lam)}")
    blank()

    A = stats["mean_abs_A"]
    print(f"    Mean |A_alpha|:        {C.BOLD}{A:.4f}{C.RESET}  ", end="")
    if A > 0.5:   print(f"{C.RED}Strong CPT-sensitive asymmetry{C.RESET}")
    elif A > 0.2: print(f"{C.YELLOW}Moderate asymmetry{C.RESET}")
    else:         print(f"{C.GREEN}Near-symmetric{C.RESET}")

    blank()
    print(f"    χ² (uniform 10%):      {stats['chi2_uniform']:.1f}   dof={stats['dof_uniform']}")
    print(f"    χ² (weighted):         {C.BOLD}{stats['chi2_weighted']:.1f}{C.RESET}   dof={stats['dof_weighted']}")

    p = stats["pval_weighted"]
    sig = f"{C.RED}*** p < 0.001{C.RESET}" if p < 0.001 else \
          f"{C.YELLOW}*   p < 0.05{C.RESET}"  if p < 0.05  else \
          f"{C.GREEN}ns  p >= 0.05{C.RESET}"
    print(f"    p-value (weighted):    {p:.3e}  {sig}")

    blank()
    print(f"    σ matter   (avg):      {stats['mean_sigma_m']*100:.1f}%  (from curve curvature)")
    print(f"    σ antimatter (avg):    {stats['mean_sigma_a']*100:.1f}%  (from curve curvature)")
    print(f"    χ² ratio (w/u):        {stats['improvement']:.3f}  {'← more conservative' if stats['improvement'] < 1 else ''}")


# ============================================================
# COMMAND: run
# ============================================================

def cmd_run(args):
    banner("SPINDEP  ·  Full Pipeline")
    normalized   = _resolve_data(args.data)
    results_root = _results_dir(args.output, normalized)
    info(f"Data:    {normalized}")
    info(f"Results: {results_root}")
    blank()
    sp = _load()
    sp["run_pipeline"](dataset_root=str(normalized), results_root=str(results_root))
    blank()
    ok(f"Report:  {results_root / 'reports'}")
    ok(f"Figures: {results_root / 'figures'}")
    ok(f"Tables:  {results_root / 'tables'}")


# ============================================================
# COMMAND: test
# ============================================================

def cmd_test(args):
    import numpy as np
    banner("SPINDEP  ·  Quick CPT Test")

    m_path = Path(args.matter).resolve()
    a_path = Path(args.antimatter).resolve()
    for p, label in [(m_path, "matter"), (a_path, "antimatter")]:
        if not p.exists():
            err(f"File not found ({label}): {p}")
            sys.exit(1)

    sp = _load()
    info(f"Matter:      {m_path.name}")
    info(f"Antimatter:  {a_path.name}")
    blank()

    df_m = sp["load_dataset"](m_path)
    df_a = sp["load_dataset"](a_path)
    df_m, _, unit_m = sp["convert_lambda_to_metres"](df_m, m_path.stem, verbose=False)
    df_a, _, unit_a = sp["convert_lambda_to_metres"](df_a, a_path.stem, verbose=False)

    info(f"Matter λ:    {df_m['lambda_m'].min():.3e} → {df_m['lambda_m'].max():.3e} m  [{unit_m}]")
    info(f"Antimatter λ:{df_a['lambda_m'].min():.3e} → {df_a['lambda_m'].max():.3e} m  [{unit_a}]")

    stats = sp["chi_squared_from_datasets"](df_m, df_a, n_points=args.points)
    if stats is None:
        blank()
        err("No overlapping lambda range.")
        warn("The two datasets probe different physical scales and cannot be compared.")
        grey("  Tip: check the lambda ranges above — they must share a common range.")
        sys.exit(0)

    _print_pair_results(stats, m_path.stem, a_path.stem)

    # ── optional plot ────────────────────────────────────────
    if args.plot is not None:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            lam   = stats["lam_grid"]
            valid = np.isfinite(stats["g_m"]) & np.isfinite(stats["g_a"])
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

            ax1.plot(lam[valid], stats["g_m"][valid], "-",  color="#2d6a9f", lw=1.5, label=f"Matter ({m_path.stem})")
            ax1.plot(lam[valid], stats["g_a"][valid], "--", color="#b03a2e", lw=1.5, label=f"Antimatter ({a_path.stem})")
            ax1.set_yscale("log"); ax1.set_xscale("log")
            ax1.set_ylabel("Coupling upper bound |g|", fontsize=10)
            ax1.legend(fontsize=8); ax1.grid(True, which="both", ls=":", alpha=0.5)
            ax1.set_title(
                f"CPT Asymmetry Test  |  |Aα| = {stats['mean_abs_A']:.4f}  "
                f"|  χ²(w) = {stats['chi2_weighted']:.0f}",
                fontsize=10
            )
            A = stats["A_alpha"]
            ax2.fill_between(lam[valid], A[valid], 0,
                             where=A[valid] > 0, color="#2d6a9f", alpha=0.3, label="Matter weaker")
            ax2.fill_between(lam[valid], A[valid], 0,
                             where=A[valid] < 0, color="#b03a2e", alpha=0.3, label="Antimatter weaker")
            ax2.axhline(0, color="black", lw=0.8, ls="--")
            ax2.set_ylim(-1.1, 1.1)
            ax2.set_ylabel("Aα", fontsize=10)
            ax2.set_xlabel("Interaction range λ (m)", fontsize=10)
            ax2.legend(fontsize=8); ax2.grid(True, which="both", ls=":", alpha=0.5)

            plot_out = Path(args.plot) if args.plot else Path(f"spin_test_{m_path.stem}_vs_{a_path.stem}.png")
            fig.tight_layout()
            fig.savefig(plot_out, dpi=150, bbox_inches="tight")
            plt.close(fig)
            blank()
            ok(f"Plot saved: {plot_out}")
        except ImportError:
            warn("matplotlib not installed — skipping plot")

    # ── optional CSV save ────────────────────────────────────
    if args.save:
        import pandas as pd
        lam   = stats["lam_grid"]
        valid = np.isfinite(stats["g_m"]) & np.isfinite(stats["g_a"])
        pd.DataFrame({
            "lambda_m":     lam[valid],
            "g_matter":     stats["g_m"][valid],
            "g_antimatter": stats["g_a"][valid],
            "A_alpha":      stats["A_alpha"][valid],
            "sigma_m_frac": stats["sigma_frac_m"][valid],
            "sigma_a_frac": stats["sigma_frac_a"][valid],
        }).to_csv(args.save, index=False)
        ok(f"Results CSV: {args.save}")


# ============================================================
# COMMAND: validate
# ============================================================

def cmd_validate(args):
    banner("SPINDEP  ·  Dataset Validation")
    normalized = _resolve_data(args.data)
    info(f"Scanning: {normalized}")
    blank()

    sp = _load()
    datasets = sp["discover_datasets"](normalized)

    unknown_pot = [d for d in datasets if d.potential == "UNKNOWN"]
    unknown_sec = [d for d in datasets if d.sector    == "UNKNOWN"]
    antimatter  = [d for d in datasets if d.contains_antimatter]
    matter      = [d for d in datasets if not d.contains_antimatter]

    section("Dataset Inventory")
    ok(f"Total datasets:     {len(datasets)}")
    ok(f"Matter datasets:    {len(matter)}")
    ok(f"Antimatter datasets:{len(antimatter)}")

    if unknown_pot:
        warn(f"Unknown potential:  {len(unknown_pot)}  (will be excluded from pairing)")
        if args.verbose:
            for d in unknown_pot[:10]:
                grey(f"    {d.filename}")
    else:
        ok("All potentials recognised")

    if unknown_sec:
        warn(f"Unknown sector:     {len(unknown_sec)}  (will be excluded from pairing)")
        if args.verbose:
            for d in unknown_sec[:10]:
                grey(f"    {d.filename}")
    else:
        ok("All sectors recognised")

    blank()
    section("Unit Audit")
    sp["audit_units"](datasets, verbose=True)

    blank()
    section("Pair Matching Preview")
    pairs = sp["build_pairs"](datasets)
    if len(pairs) == 0:
        err("No valid pairs found.")
        blank()
        grey("  Checklist:")
        grey("  1. Matter and antimatter files are in the SAME coupling/ folder")
        grey("  2. Filenames encode the SAME potential token (e.g. both have V2)")
        grey("  3. Sectors are compatible (ee <-> eebar, ep <-> ebarpabr, etc.)")
        grey("  4. The interaction_class subfolder matches (lepton-lepton, etc.)")
    else:
        ok(f"Valid pairs found: {len(pairs)}")
        for m, a in pairs:
            print(f"    {C.BLUE}{m.source:<20}{C.RESET} × {C.RED}{a.source}{C.RESET}  "
                  f"[{m.coupling} · {m.potential} · {m.sector}]")


# ============================================================
# COMMAND: import
# ============================================================

def cmd_import(args):
    banner("SPINDEP  ·  Import Datasets")

    src_dir  = Path(args.src).resolve()
    dest_base = Path(args.dest).resolve() if args.dest else Path("datasets/normalized")
    target   = dest_base / args.coupling / args.interaction_class
    target.mkdir(parents=True, exist_ok=True)

    if not src_dir.exists():
        err(f"Source not found: {src_dir}")
        sys.exit(1)

    csv_files = sorted(src_dir.rglob("*.csv"))
    if not csv_files:
        err(f"No CSV files found in {src_dir}")
        sys.exit(1)

    info(f"Found {len(csv_files)} CSV files")
    info(f"Target: {target}")
    blank()

    imported = []
    for f in csv_files:
        stem = f.stem
        # Only rename if not already in SPINDEP convention
        if "_m_abs_" in stem or "_abs_" in stem:
            new_name = f.name
        else:
            is_anti = any(t in stem.lower() for t in ["anti","bar","plus","positron","pos"])
            sector  = args.sector_antimatter if is_anti else args.sector_matter
            new_name = f"{args.potential}_{stem}_m_abs_{sector}.csv"
            warn(f"Renamed: {f.name}  →  {new_name}")

        dest_file = target / new_name
        shutil.copy2(f, dest_file)
        ok(f"Imported: {new_name}")
        imported.append(dest_file)

    blank()
    ok(f"Imported {len(imported)} files to {target}")

    if args.run:
        blank()
        info("Running pipeline on imported data...")
        sp = _load()
        results = dest_base.parent.parent / "results"
        sp["run_pipeline"](dataset_root=str(dest_base), results_root=str(results))


# ============================================================
# COMMAND: gaps
# ============================================================

def cmd_gaps(args):
    banner("SPINDEP  ·  Gap Analysis")
    normalized = _resolve_data(args.data)
    out_dir    = Path(args.output).resolve() if args.output else normalized.parent.parent / "results" / "figures"
    sp = _load()
    datasets = sp["discover_datasets"](normalized)
    info(f"Loaded {len(datasets)} datasets")
    sp["run_gap_analysis"](datasets, figures_dir=out_dir)
    ok(f"Figures: {out_dir / 'gap_analysis'}")


# ============================================================
# COMMAND: atlas
# ============================================================

def cmd_atlas(args):
    banner("SPINDEP  ·  Constraint Atlas")
    normalized = _resolve_data(args.data)
    out_dir    = Path(args.output).resolve() if args.output else normalized.parent.parent / "results" / "figures"
    sp = _load()
    datasets = sp["discover_datasets"](normalized)
    info(f"Loaded {len(datasets)} datasets")
    sp["run_constraint_plots"](
        datasets=datasets,
        summary_rows=[],
        plots_dir=normalized.parent.parent / "results" / "plots",
        figures_dir=out_dir,
    )
    ok(f"Atlas: {out_dir / 'constraint_atlas'}")


# ============================================================
# COMMAND: config  (run from a YAML/JSON config file)
# ============================================================

def cmd_config(args):
    banner("SPINDEP  ·  Config-File Run")
    cfg_path = Path(args.config).resolve()
    if not cfg_path.exists():
        err(f"Config file not found: {cfg_path}")
        sys.exit(1)

    # Support both YAML and JSON
    if cfg_path.suffix in (".yaml", ".yml"):
        try:
            import yaml
            with open(cfg_path) as f:
                cfg = yaml.safe_load(f)
        except ImportError:
            err("PyYAML not installed. Run: pip install pyyaml")
            sys.exit(1)
    else:
        with open(cfg_path) as f:
            cfg = json.load(f)

    info(f"Config: {cfg_path.name}")
    blank()

    command = cfg.get("command", "run")

    if command == "run":
        data    = cfg.get("data")
        output  = cfg.get("output")
        if not data:
            err("Config must specify 'data' field")
            sys.exit(1)
        normalized   = _resolve_data(data)
        results_root = Path(output).resolve() if output else normalized.parent.parent / "results"
        sp = _load()
        sp["run_pipeline"](dataset_root=str(normalized), results_root=str(results_root))

    elif command == "test":
        matter    = cfg.get("matter")
        antimatter = cfg.get("antimatter")
        if not matter or not antimatter:
            err("Config must specify 'matter' and 'antimatter' fields for test command")
            sys.exit(1)
        # Delegate to cmd_test via Namespace
        ns = argparse.Namespace(
            matter=matter, antimatter=antimatter,
            plot=cfg.get("plot"), save=cfg.get("save"),
            points=cfg.get("points", 300)
        )
        cmd_test(ns)

    elif command == "import":
        ns = argparse.Namespace(
            src=cfg["from"], dest=cfg.get("dest"),
            coupling=cfg["coupling"], potential=cfg["potential"],
            sector_matter=cfg["sector_matter"],
            sector_antimatter=cfg["sector_antimatter"],
            interaction_class=cfg.get("interaction_class", "lepton-lepton"),
            run=cfg.get("run", False)
        )
        cmd_import(ns)

    ok("Config run complete.")


# ============================================================
# COMMAND: batch  (run multiple jobs from one file)
# ============================================================

def cmd_batch(args):
    banner("SPINDEP  ·  Batch Run")
    jobs_path = Path(args.jobs).resolve()
    if not jobs_path.exists():
        err(f"Jobs file not found: {jobs_path}")
        sys.exit(1)

    if jobs_path.suffix in (".yaml", ".yml"):
        try:
            import yaml
            with open(jobs_path) as f:
                jobs = yaml.safe_load(f)
        except ImportError:
            err("PyYAML not installed. Run: pip install pyyaml")
            sys.exit(1)
    else:
        with open(jobs_path) as f:
            jobs = json.load(f)

    if not isinstance(jobs, list):
        jobs = [jobs]

    info(f"Found {len(jobs)} job(s) in {jobs_path.name}")
    blank()

    for i, job in enumerate(jobs, 1):
        print(f"{C.BOLD}{C.MAGENTA}  ── Job {i}/{len(jobs)}: {job.get('name', 'unnamed')} ──{C.RESET}")
        # Write a temp config and run
        tmp = Path(f"/tmp/spindep_job_{i}.json")
        with open(tmp, "w") as f:
            json.dump(job, f)
        ns = argparse.Namespace(config=str(tmp))
        try:
            cmd_config(ns)
            ok(f"Job {i} complete")
        except SystemExit:
            err(f"Job {i} failed")
        blank()


# ============================================================
# COMMAND: info  (show framework status)
# ============================================================

def cmd_info(args):
    banner("SPINDEP  ·  Framework Info")
    src = _find_src()
    if src:
        ok(f"SPINDEP source: {src}")
    else:
        err("SPINDEP source not found")

    # Module versions
    section("Dependencies")
    deps = ["numpy","scipy","pandas","matplotlib","reportlab","PIL"]
    for dep in deps:
        try:
            mod = __import__(dep)
            ver = getattr(mod, "__version__", "?")
            ok(f"{dep:<15} {ver}")
        except ImportError:
            err(f"{dep:<15} NOT INSTALLED")

    # Dataset count if data dir given
    if args.data:
        blank()
        section("Dataset Summary")
        try:
            normalized = _resolve_data(args.data)
            sp = _load()
            datasets = sp["discover_datasets"](normalized)
            pairs    = sp["build_pairs"](datasets)
            info(f"Datasets:  {len(datasets)}")
            info(f"Pairs:     {len(pairs)}")
        except Exception as e:
            warn(f"Could not load datasets: {e}")


# ============================================================
# MAIN ARGUMENT PARSER
# ============================================================

EPILOG = f"""
{C.BOLD}Examples:{C.RESET}
  {C.CYAN}spin run   --data ./datasets{C.RESET}
      Full pipeline on your dataset folder.

  {C.CYAN}spin test  matter.csv antimatter.csv --plot{C.RESET}
      Quick CPT test, saves a plot.

  {C.CYAN}spin test  e_bounds.csv eplus_bounds.csv --save results.csv{C.RESET}
      Test and export full results table.

  {C.CYAN}spin validate --data ./datasets{C.RESET}
      Check structure before a full run.

  {C.CYAN}spin import --from /data/new --coupling gAgA --potential V2 \\{C.RESET}
  {C.CYAN}            --sector-matter ee --sector-antimatter eebar --run{C.RESET}
      Import files and run immediately.

  {C.CYAN}spin config  myrun.yaml{C.RESET}
      Run from a config file (no flags needed).

  {C.CYAN}spin batch   jobs.yaml{C.RESET}
      Run multiple analyses from one file.

  {C.CYAN}spin info   --data ./datasets{C.RESET}
      Show framework status and dataset summary.
"""


def main():
    parser = argparse.ArgumentParser(
        prog="spin",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=f"{C.BOLD}{C.CYAN}SPINDEP — Spin-Dependent Exotic Interaction Analysis{C.RESET}\n"
                    f"  CPT symmetry tests via matter-antimatter constraint comparison.",
        epilog=EPILOG,
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # ── run ──────────────────────────────────────────────────
    p = sub.add_parser("run", help="Full pipeline: discover → analyse → report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Run the complete SPINDEP analysis pipeline.\n\n"
                    "Example:\n  spin run --data ./datasets")
    p.add_argument("--data",   required=True, metavar="DIR",
        help="Dataset folder (containing normalized/ or CSV files)")
    p.add_argument("--output", metavar="DIR",
        help="Results output folder (default: <data>/../results)")

    # ── test ─────────────────────────────────────────────────
    p = sub.add_parser("test", help="Quick CPT test on two CSV files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Perform a CPT asymmetry test between two CSV files.\n"
                    "No folder structure required.\n\n"
                    "Example:\n  spin test matter.csv antimatter.csv --plot")
    p.add_argument("matter",     metavar="MATTER.CSV",
        help="Matter sector CSV (lambda, coupling_bound)")
    p.add_argument("antimatter", metavar="ANTIMATTER.CSV",
        help="Antimatter sector CSV (lambda, coupling_bound)")
    p.add_argument("--plot", metavar="FILE.PNG", nargs="?", const="",
        help="Save asymmetry plot (default filename if no path given)")
    p.add_argument("--save", metavar="FILE.CSV",
        help="Export full results table as CSV")
    p.add_argument("--points", type=int, default=300, metavar="N",
        help="Lambda grid resolution (default: 300)")

    # ── validate ─────────────────────────────────────────────
    p = sub.add_parser("validate", help="Pre-flight checks on dataset folder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Validate dataset structure, names, units, and pairing.\n\n"
                    "Example:\n  spin validate --data ./datasets")
    p.add_argument("--data",    required=True, metavar="DIR")
    p.add_argument("--verbose", action="store_true",
        help="Show all unrecognised files")

    # ── import ───────────────────────────────────────────────
    p = sub.add_parser("import", help="Import CSV files from any folder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Copy external CSV files into the SPINDEP structure.\n\n"
                    "Example:\n  spin import --from /data --coupling gAgA "
                    "--potential V2 \\\n             --sector-matter ee "
                    "--sector-antimatter eebar --run")
    p.add_argument("--from", dest="src", required=True, metavar="DIR",
        help="Folder containing CSV files to import")
    p.add_argument("--dest", metavar="DIR",
        help="SPINDEP datasets root (default: datasets/normalized)")
    p.add_argument("--coupling",           required=True, metavar="NAME",
        help="Coupling type: gAgA | gsgs | gVgV | gpgp | gpgs")
    p.add_argument("--potential",          required=True, metavar="Vi",
        help="Potential: V2 | V3 | V11 | V4+5 | etc.")
    p.add_argument("--sector-matter",      required=True, metavar="SECTOR",
        help="Matter sector: ee | ep | en | nn | nN | eN ...")
    p.add_argument("--sector-antimatter",  required=True, metavar="SECTOR",
        help="Antimatter sector: eebar | epbar | enbar | nnbar ...")
    p.add_argument("--interaction-class",  default="lepton-lepton", metavar="CLASS",
        help="Subfolder: lepton-lepton | lepton-nucleon | nucleon-nucleon")
    p.add_argument("--run", action="store_true",
        help="Run full pipeline immediately after import")

    # ── gaps ─────────────────────────────────────────────────
    p = sub.add_parser("gaps", help="Gap analysis figures only",
        description="Generate the three gap analysis figures.\n\n"
                    "Example:\n  spin gaps --data ./datasets")
    p.add_argument("--data",   required=True, metavar="DIR")
    p.add_argument("--output", metavar="DIR",
        help="Output folder (default: results/figures)")

    # ── atlas ────────────────────────────────────────────────
    p = sub.add_parser("atlas", help="Constraint atlas figures only",
        description="Generate constraint atlas plots.\n\n"
                    "Example:\n  spin atlas --data ./datasets")
    p.add_argument("--data",   required=True, metavar="DIR")
    p.add_argument("--output", metavar="DIR",
        help="Output folder (default: results/figures)")

    # ── config ───────────────────────────────────────────────
    p = sub.add_parser("config", help="Run from a YAML or JSON config file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Run SPINDEP from a configuration file.\n\n"
                    "Example YAML:\n"
                    "  command: run\n"
                    "  data: ./datasets\n"
                    "  output: ./results\n\n"
                    "Example:\n  spin config myrun.yaml")
    p.add_argument("config", metavar="CONFIG.yaml",
        help="Path to YAML or JSON config file")

    # ── batch ────────────────────────────────────────────────
    p = sub.add_parser("batch", help="Run multiple jobs from one YAML/JSON file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Run multiple SPINDEP analyses from one jobs file.\n\n"
                    "Example:\n  spin batch jobs.yaml")
    p.add_argument("jobs", metavar="JOBS.yaml",
        help="Path to YAML or JSON jobs file (list of job configs)")

    # ── info ─────────────────────────────────────────────────
    p = sub.add_parser("info", help="Show framework status and dependency versions",
        description="Display SPINDEP installation info.\n\n"
                    "Example:\n  spin info --data ./datasets")
    p.add_argument("--data", metavar="DIR",
        help="Optional: show dataset summary for this folder")

    # ── dispatch ─────────────────────────────────────────────
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(0)

    {
        "run":      cmd_run,
        "test":     cmd_test,
        "validate": cmd_validate,
        "import":   cmd_import,
        "gaps":     cmd_gaps,
        "atlas":    cmd_atlas,
        "config":   cmd_config,
        "batch":    cmd_batch,
        "info":     cmd_info,
    }[args.command](args)


if __name__ == "__main__":
    main()
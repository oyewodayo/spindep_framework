# // pipeline.py
from pathlib import Path
from dataclasses import asdict

import pandas as pd
import numpy as np

from .parser import (
    discover_datasets,
    load_dataset
)

from .matcher import build_pairs

from .asymmetry import compute_asymmetry

from .statistics import chi_squared_sensitivity

from .plotting import plot_asymmetry
from .reporting import generate_report


def run_pipeline(dataset_root, results_root):

    dataset_root = Path(dataset_root)

    results_root = Path(results_root)

    plots_dir = results_root / "plots"

    tables_dir = results_root / "tables"

    reports_dir = results_root / "reports"

    plots_dir.mkdir(parents=True, exist_ok=True)

    tables_dir.mkdir(parents=True, exist_ok=True)

    reports_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------
    # DISCOVER DATASETS
    # --------------------------------------------------------

    print("=" * 60)

    print("DISCOVERING DATASETS")

    print("=" * 60)

    datasets = discover_datasets(dataset_root)
    # pipeline.py, right after discover_datasets()
    for d in datasets:
        if "bar" in d.filename.lower() or "bare" in d.filename.lower():
            print(f"  {d.filename:50s} → sector={d.sector!r:12s}  antimatter={d.contains_antimatter}")

    print(f"Found {len(datasets)} datasets")

    # --------------------------------------------------------
    # EXPORT REGISTRY
    # --------------------------------------------------------

    registry = pd.DataFrame([asdict(d) for d in datasets])

    registry.to_csv(
        tables_dir / "dataset_registry.csv",
        index=False
    )

    # --------------------------------------------------------
    # BUILD MATCHED PAIRS
    # --------------------------------------------------------

    pairs = build_pairs(datasets)

    print(f"Found {len(pairs)} valid pairs")

    # --------------------------------------------------------
    # ANALYSIS LOOP
    # --------------------------------------------------------

    summary_rows = []

    for matter_ds, antimatter_ds in pairs:

        print("-" * 50)

        print(matter_ds.filename)

        print(antimatter_ds.filename)

        # ----------------------------------------------------
        # LOAD DATA
        # ----------------------------------------------------

        df_m = load_dataset(matter_ds.filepath)

        df_a = load_dataset(antimatter_ds.filepath)

        # ----------------------------------------------------
        # COMPUTE ASYMMETRY
        # ----------------------------------------------------

        result = compute_asymmetry(df_m, df_a)

        if result is None or result[0] is None:
            print(f"  [SKIP] No overlapping lambda range")
            continue

        lam, A, (g_m, g_a) = result

        # ----------------------------------------------------
        # STATISTICS
        # ----------------------------------------------------

        chi2, dof, pval = chi_squared_sensitivity(
            g_m,
            g_a
        )

        mean_abs_A = np.nanmean(np.abs(A))

        # ----------------------------------------------------
        # SAVE PLOT
        # ----------------------------------------------------

        plot_name = (
            f"{matter_ds.coupling}_"
            f"{matter_ds.potential}_"
            f"{matter_ds.sector}.png"
        )

        plot_path = plots_dir / plot_name

        plot_asymmetry(
            lam,
            A,
            g_m,
            g_a,
            matter_ds,
            antimatter_ds,
            plot_path
        )

        # ----------------------------------------------------
        # SUMMARY TABLE
        # ----------------------------------------------------

        summary_rows.append({

            "coupling":
                matter_ds.coupling,

            "potential":
                matter_ds.potential,

            "interaction_class":
                matter_ds.interaction_class,

            "sector":
                matter_ds.sector,

            "matter_source":
                matter_ds.source,

            "antimatter_source":
                antimatter_ds.source,

            "mean_abs_A":
                mean_abs_A,

            "chi2":
                chi2,

            "dof":
                dof,

            "p_value":
                pval,

            "lambda_min":
                lam.min(),

            "lambda_max":
                lam.max()
        })

    # --------------------------------------------------------
    # EXPORT SUMMARY
    # --------------------------------------------------------

    summary_df = pd.DataFrame(summary_rows)

    summary_df.to_csv(
        tables_dir / "asymmetry_summary.csv",
        index=False
    )

    print("=" * 60)

    print("PIPELINE COMPLETE")

    print("=" * 60)
    # --------------------------------------------------------
    # GENERATE REPORT
    # --------------------------------------------------------

    if summary_rows:

        report_path = reports_dir / "asymmetry_report.pdf"

        generate_report(
            summary_rows=summary_rows,
            plots_dir=plots_dir,
            output_path=report_path,
        )
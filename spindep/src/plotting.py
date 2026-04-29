# // plotting.py
import matplotlib.pyplot as plt


def plot_asymmetry(
    lam,
    A,
    g_m,
    g_a,
    matter_ds,
    antimatter_ds,
    output_path
):

    fig, (ax1, ax2) = plt.subplots(
        2,
        1,
        figsize=(10, 8),
        sharex=True,
        gridspec_kw={"height_ratios": [2, 1]}
    )

    # --------------------------------------------------------
    # TOP PANEL
    # --------------------------------------------------------

    ax1.loglog(
        lam,
        g_m,
        lw=2,
        color="steelblue",
        label=f"Matter: {matter_ds.label}"
    )

    ax1.loglog(
        lam,
        g_a,
        lw=2,
        ls="--",
        color="crimson",
        label=f"Antimatter: {antimatter_ds.label}"
    )

    ax1.set_ylabel("Coupling upper bound")

    ax1.set_title(
        f"{matter_ds.coupling} | "
        f"{matter_ds.potential} | "
        f"{matter_ds.sector}"
    )

    ax1.grid(True, which="both", ls="--", alpha=0.4)

    ax1.legend(fontsize=8)

    # --------------------------------------------------------
    # BOTTOM PANEL
    # --------------------------------------------------------

    ax2.semilogx(
        lam,
        A,
        lw=1.5,
        color="darkorange"
    )

    ax2.axhline(0, color="gray", ls="--", lw=0.8)

    ax2.fill_between(
        lam,
        A,
        0,
        where=(A > 0),
        alpha=0.15,
        color="steelblue",
        label="Matter weaker"
    )

    ax2.fill_between(
        lam,
        A,
        0,
        where=(A < 0),
        alpha=0.15,
        color="crimson",
        label="Antimatter weaker"
    )

    ax2.set_xlabel("Interaction range λ (m)")

    ax2.set_ylabel(r"$A_\alpha$")

    ax2.set_ylim(-1.1, 1.1)

    ax2.grid(True, which="both", ls="--", alpha=0.4)

    ax2.legend(fontsize=8)

    plt.tight_layout()

    plt.savefig(output_path, dpi=150)

    plt.close()
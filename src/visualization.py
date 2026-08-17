"""
visualization.py
================
Generates all charts for the Mars to Table MILP project.

Functions
---------
plot_diversity_tradeoff(results, save_path)
    Four-panel figure: diversity vs. Earth dependency, production mix for K=7,
    total-production evolution for selected K values, and net-water sensitivity
    vs. global recycling rate.

plot_production_mix(result, title, save_path)
    Stacked area chart of weekly production mix for a single K scenario.

plot_water_sensitivity(result, rates, save_path)
    Net make-up water vs. global recycling rate for a single K scenario.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_weeks(result: dict) -> list[int]:
    return sorted(set(t for (_, t) in result["weekly"].keys()))


def _all_ids(result: dict) -> list[str]:
    return sorted(set(i for (i, _) in result["weekly"].keys()))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def plot_diversity_tradeoff(
    results: list[dict],
    save_path: str = "results/diversidad_tradeoff_v3.png",
    k_highlight: list[int] | None = None,
    dpi: int = 150,
) -> None:
    """Four-panel diversity trade-off figure.

    Panel 1  — Earth dependency & average water vs. K (dual-axis line plot).
    Panel 2  — Weekly production mix for K=7 (stacked area).
    Panel 3  — Total production evolution for selected K values (line plot).
    Panel 4  — Net make-up water sensitivity to global recycling rate for K=7.

    Parameters
    ----------
    results : list[dict]
        Output of scenarios.run_k_sweep().
    save_path : str
        File path for the saved PNG.
    k_highlight : list[int], optional
        K values to show in panel 3. Defaults to [1, 5, 7, 11].
    dpi : int
        Resolution of the saved figure.
    """
    if k_highlight is None:
        k_highlight = [1, 5, 7, 11]

    factibles = [r for r in results if r.get("status") == "Optimal"]
    if not factibles:
        print("⚠️  No optimal solutions found — skipping plot.")
        return

    ks   = [r["K"] for r in factibles]
    dep  = [r["earth_dependency"] for r in factibles]

    # Infer T_WEEKS from the first feasible result
    t_weeks_list = [max(t for (_, t) in r["weekly"].keys()) for r in factibles]
    agua = [r["agua_total"] / tw for r, tw in zip(factibles, t_weeks_list)]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Mars to Table — Diversity Trade-off Analysis (v3)",
        fontsize=14, fontweight="bold", y=1.01,
    )

    # ------------------------------------------------------------------
    # Panel 1: Earth dependency & water vs. K
    # ------------------------------------------------------------------
    ax1 = axes[0, 0]
    ax1.plot(ks, dep, marker="o", color="firebrick", linewidth=2,
             label="Earth Dependency (index)")
    ax1.set_xlabel("K = minimum active species")
    ax1.set_ylabel("Earth Dependency (0 = self-sufficient)", color="firebrick")
    ax1.set_title("Cost of Diversity: Self-sufficiency")
    ax1.tick_params(axis="y", labelcolor="firebrick")
    ax1.grid(alpha=0.3)

    ax1b = ax1.twinx()
    ax1b.plot(ks, agua, marker="s", color="steelblue", linewidth=2,
              label="Avg. Water (L/day)")
    ax1b.set_ylabel("Average Water Use (L/day)", color="steelblue")
    ax1b.tick_params(axis="y", labelcolor="steelblue")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1b.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=8)

    # ------------------------------------------------------------------
    # Panel 2: Production mix for K=7
    # ------------------------------------------------------------------
    ax2 = axes[0, 1]
    k7 = next((r for r in factibles if r["K"] == 7), factibles[-1])
    weeks = _get_weeks(k7)
    ids   = _all_ids(k7)

    weekly_df = pd.DataFrame(
        [{"Candidato": i, "Semana": t, "Produccion_kg_dia": k7["weekly"].get((i, t), 0.0)}
         for i in ids for t in weeks]
    )
    pivot = (
        weekly_df
        .pivot(index="Semana", columns="Candidato", values="Produccion_kg_dia")
        .fillna(0)
        .reindex(weeks, fill_value=0)
    )
    # Keep only columns with any production
    pivot = pivot.loc[:, (pivot > 1e-6).any()]
    pivot.plot.area(ax=ax2, alpha=0.85, linewidth=0)
    ax2.set_title(f"Production Mix — K={k7['K']} minimum species")
    ax2.set_xlabel("Mission week")
    ax2.set_ylabel("Production (kg/day)")
    ax2.legend(loc="upper left", fontsize=6, ncol=2)
    ax2.grid(alpha=0.3)

    # ------------------------------------------------------------------
    # Panel 3: Total production evolution for selected K
    # ------------------------------------------------------------------
    ax3 = axes[1, 0]
    for r in factibles:
        if r["K"] in k_highlight:
            w = _get_weeks(r)
            all_i = _all_ids(r)
            weekly_total = [sum(r["weekly"].get((i, t), 0) for i in all_i) for t in w]
            ax3.plot(w, weekly_total, marker="o", label=f"K={r['K']}", alpha=0.8)
    ax3.set_xlabel("Mission week")
    ax3.set_ylabel("Total production (kg/day)")
    ax3.set_title("Production Evolution by K")
    ax3.legend(loc="best", fontsize=8)
    ax3.grid(alpha=0.3)

    # ------------------------------------------------------------------
    # Panel 4: Net water sensitivity vs. recycling rate (K=7)
    # ------------------------------------------------------------------
    ax4 = axes[1, 1]
    rates = [0.85, 0.90, 0.93, 0.95, 0.98, 0.99]
    t_weeks_k7 = max(t for (_, t) in k7["weekly"].keys())
    agua_bruta_total = k7["agua_total"]   # sum over all weeks
    netas = [agua_bruta_total * (1 - r) for r in rates]
    ax4.plot(
        [r * 100 for r in rates],
        [n / 1000 for n in netas],
        marker="o", color="darkgreen", linewidth=2,
    )
    ax4.axvline(x=95, color="gray", linestyle="--", alpha=0.5,
                label="Baseline assumption (95 %)")
    ax4.set_xlabel("Global recycling rate (%)")
    ax4.set_ylabel(f"Net make-up water (m³ over {t_weeks_k7} weeks)")
    ax4.set_title(f"Sensitivity: Net Water vs. Recycling Rate (K={k7['K']})")
    ax4.legend(fontsize=8)
    ax4.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=dpi, bbox_inches="tight")
    print(f"📊  Chart saved to {save_path}")
    plt.close(fig)


def plot_production_mix(
    result: dict,
    title: str | None = None,
    save_path: str | None = None,
    dpi: int = 150,
) -> None:
    """Stacked area chart of weekly production mix for a single K scenario.

    Parameters
    ----------
    result : dict
        A single entry from scenarios.run_k_sweep() with status == 'Optimal'.
    title : str, optional
        Figure title. Defaults to "Production Mix — K=<K>".
    save_path : str, optional
        If provided, saves the figure to this path; otherwise displays it.
    dpi : int
        Resolution of the saved figure.
    """
    if result.get("status") != "Optimal":
        print(f"⚠️  Result for K={result.get('K')} is not optimal — skipping.")
        return

    weeks = _get_weeks(result)
    ids   = _all_ids(result)

    weekly_df = pd.DataFrame(
        [{"Candidato": i, "Semana": t,
          "Produccion_kg_dia": result["weekly"].get((i, t), 0.0)}
         for i in ids for t in weeks]
    )
    pivot = (
        weekly_df
        .pivot(index="Semana", columns="Candidato", values="Produccion_kg_dia")
        .fillna(0)
        .reindex(weeks, fill_value=0)
    )
    pivot = pivot.loc[:, (pivot > 1e-6).any()]

    fig, ax = plt.subplots(figsize=(12, 6))
    pivot.plot.area(ax=ax, alpha=0.85, linewidth=0)
    ax.set_title(title or f"Production Mix — K={result['K']} minimum species")
    ax.set_xlabel("Mission week")
    ax.set_ylabel("Production (kg/day)")
    ax.legend(loc="upper left", fontsize=7, ncol=2)
    ax.grid(alpha=0.3)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=dpi, bbox_inches="tight")
        print(f"📊  Chart saved to {save_path}")
        plt.close(fig)
    else:
        plt.show()


def plot_water_sensitivity(
    result: dict,
    rates: list[float] | None = None,
    save_path: str | None = None,
    dpi: int = 150,
) -> None:
    """Net make-up water vs. global recycling rate for a single K scenario.

    Parameters
    ----------
    result : dict
        A single entry from scenarios.run_k_sweep() with status == 'Optimal'.
    rates : list[float], optional
        Recycling rates to evaluate (fractions, e.g. 0.90).
        Defaults to [0.85, 0.90, 0.93, 0.95, 0.98, 0.99].
    save_path : str, optional
        If provided, saves the figure to this path.
    dpi : int
        Resolution.
    """
    if result.get("status") != "Optimal":
        print(f"⚠️  Result for K={result.get('K')} is not optimal — skipping.")
        return

    if rates is None:
        rates = [0.85, 0.90, 0.93, 0.95, 0.98, 0.99]

    t_weeks = max(t for (_, t) in result["weekly"].keys())
    agua_total = result["agua_total"]
    netas = [agua_total * (1 - r) for r in rates]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot([r * 100 for r in rates], [n / 1000 for n in netas],
            marker="o", color="darkgreen", linewidth=2)
    ax.axvline(x=95, color="gray", linestyle="--", alpha=0.6,
               label="Baseline assumption (95 %)")
    ax.set_xlabel("Global recycling rate (%)")
    ax.set_ylabel(f"Net make-up water (m³ over {t_weeks} weeks)")
    ax.set_title(f"Water Sensitivity — K={result['K']}")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=dpi, bbox_inches="tight")
        print(f"📊  Chart saved to {save_path}")
        plt.close(fig)
    else:
        plt.show()

"""
scenarios.py
============
Runs the K-sweep scenario analysis for the Mars to Table MILP model.

The main entry point is run_k_sweep(), which iterates over a range of K values
(minimum active species) and returns a list of result dicts — one per scenario —
suitable for downstream analysis and visualisation.

A convenience function build_comparison_df() converts those results into a
tidy pandas DataFrame (one row per K) for easy export to Excel or CSV.
"""

from __future__ import annotations

import pandas as pd

from src.model import solve_model


def run_k_sweep(
    crops: dict,
    alt: dict,
    k_values: list[int] | None = None,
    **model_kwargs,
) -> list[dict]:
    """Solve the MILP for each value in k_values and return all results.

    Parameters
    ----------
    crops : dict
        Photosynthetic-crop data from data_validation.load_and_validate_data().
    alt : dict
        Alternative-protein data from data_validation.load_and_validate_data().
    k_values : list[int], optional
        Minimum-species values to evaluate.
        Defaults to [1, 3, 5, 7, 9, 11, 13, 15].
    **model_kwargs
        Forwarded to model.solve_model() — use to override mission parameters.

    Returns
    -------
    list[dict]
        Each dict has the keys returned by model.solve_model().
    """
    if k_values is None:
        k_values = [1, 3, 5, 7, 9, 11, 13, 15]

    all_ids = list(crops.keys()) + list(alt.keys())
    results: list[dict] = []

    for k in k_values:
        if k > len(all_ids):
            print(f"  ⚠️  K={k} exceeds total candidates ({len(all_ids)}). Skipping.")
            continue

        print(f"  Solving K={k} ...", end="  ")
        result = solve_model(k, crops, alt, **model_kwargs)
        results.append(result)

        status = result["status"]
        if status == "Optimal":
            print(
                f"✅  Earth dependency = {result['earth_dependency']:.4f}  |  "
                f"Active species = {len(result['active_species'])}"
            )
        else:
            print(f"❌  Status: {status}")

    return results


def build_comparison_df(results: list[dict]) -> pd.DataFrame:
    """Convert the list of scenario results into a summary DataFrame.

    Parameters
    ----------
    results : list[dict]
        Output of run_k_sweep().

    Returns
    -------
    pd.DataFrame
        One row per K; columns include K, Status, Dependencia_Tierra,
        Agua_total_prom_L_dia, Area_usada_prom_m2, Biomasa_alt_prom_kg_dia,
        Especies_activas.
    """
    rows = []
    for r in results:
        if r["status"] != "Optimal":
            rows.append({
                "K":                        r["K"],
                "Status":                   r["status"],
                "Dependencia_Tierra":        None,
                "Agua_total_prom_L_dia":     None,
                "Area_usada_prom_m2":        None,
                "Biomasa_alt_prom_kg_dia":   None,
                "Especies_activas":          None,
                "Lista_especies":            None,
            })
        else:
            t_weeks = max(t for (_, t) in r["weekly"].keys()) if r["weekly"] else 1
            rows.append({
                "K":                        r["K"],
                "Status":                   r["status"],
                "Dependencia_Tierra":        round(r["earth_dependency"], 6),
                "Agua_total_prom_L_dia":     round(r["agua_total"] / t_weeks, 2),
                "Area_usada_prom_m2":        round(r["area_prom"], 2),
                "Biomasa_alt_prom_kg_dia":   round(r["biomasa_alt_prom"], 4),
                "Especies_activas":          len(r["active_species"]),
                "Lista_especies":            "; ".join(r["active_species"]),
            })

    return pd.DataFrame(rows)


def build_weekly_detail_df(result: dict) -> pd.DataFrame:
    """Return a tidy weekly-production DataFrame for a single scenario.

    Parameters
    ----------
    result : dict
        A single entry from run_k_sweep() with status == 'Optimal'.

    Returns
    -------
    pd.DataFrame
        Columns: Candidato, Semana, Produccion_kg_dia
        Only rows where production > 1e-6 are included.
    """
    if result.get("status") != "Optimal":
        return pd.DataFrame(columns=["Candidato", "Semana", "Produccion_kg_dia"])

    rows = [
        {"Candidato": i, "Semana": t, "Produccion_kg_dia": v}
        for (i, t), v in result["weekly"].items()
        if v > 1e-6
    ]
    return pd.DataFrame(rows)

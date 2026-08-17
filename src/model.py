"""
model.py
========
Builds and solves the Mars to Table MILP model for a given K (minimum
number of active species) using PuLP + CBC.

Model summary
-------------
Decision variables
    x[(i, t)]      Continuous. Daily production of candidate i in week t
                   (kg/day edible biomass for photosynthetic crops;
                    kg/day product for alternative proteins).
    y[i]           Binary. 1 if candidate i is included in the portfolio.
    delta_prot[t]  Continuous ≥ 0. Protein deficit covered by Earth in week t (g/day).
    delta_kcal[t]  Continuous ≥ 0. Calorie deficit covered by Earth in week t (kcal/day).

Objective
    min  w_E · EarthDependency  +  w_W · TotalWater

Constraints
    - Protein supply ≥ daily crew demand (supplemented by Earth if needed)
    - Calorie supply ≥ daily crew demand (supplemented by Earth if needed)
    - Earth supplement capacity decreases linearly over the mission
    - Cultivation area ≤ maximum available
    - Daily water use ≤ maximum available
    - Alternative protein biomass ≤ maximum capacity
    - Crops cannot produce before completing their growth cycle (maturity)
    - Big-M linking: x[(i,t)] ≤ BIG_M · y[i]
    - Diversity: Σ y[i] ≥ K
"""

import math

import pulp

# ---------------------------------------------------------------------------
# Mission parameters (defaults — override by passing kwargs to solve_model)
# ---------------------------------------------------------------------------
DEFAULTS = {
    "T_WEEKS":                 16,      # planning horizon (weeks)
    "N_CREW":                  4,       # crew size
    "PROTEIN_G_DAY_PER_PERSON": 60,    # g protein / person / day
    "KCAL_DAY_PER_PERSON":    2100,    # kcal / person / day
    "MAX_AREA_M2":             100,    # m² total cultivation area
    "MAX_WATER_L_DAY":         2000,   # L / day maximum water budget
    "MAX_ALT_BIOMASS_KG_DAY":  5,      # kg / day cap on alternative proteins
    "WEIGHT_EARTH_DEPENDENCY": 1000.0, # objective weight for Earth dependency
    "WEIGHT_WATER":            0.001,  # objective weight for water (tie-breaker)
    "BIG_M":                   1e5,    # Big-M constant for activation constraints
    "MIN_AVG_KG_DIA":          0.05,   # minimum avg production for a species to "count"
}


def _earth_cap(t: int, t_weeks: int) -> float:
    """Fraction of nutritional demand that Earth can still supply in week t.

    The capacity decreases linearly: 100 % in week 1, 0 % in the final week.
    This models progressive food self-sufficiency during the mission.
    """
    return max(0.0, 1.0 - (t - 1) / (t_weeks - 1))


def solve_model(
    min_species: int,
    crops: dict,
    alt: dict,
    **kwargs,
) -> dict:
    """Build and solve the MILP for a given minimum-species value K.

    Parameters
    ----------
    min_species : int
        K — minimum number of active species (diversity constraint).
    crops : dict
        Validated photosynthetic-crop data from data_validation.load_and_validate_data().
    alt : dict
        Validated alternative-protein data from data_validation.load_and_validate_data().
    **kwargs
        Override any key from DEFAULTS.

    Returns
    -------
    dict with keys:
        K, status, earth_dependency, agua_total, area_prom,
        biomasa_alt_prom, weekly, active_species
    """
    # Merge defaults with any overrides
    p = {**DEFAULTS, **kwargs}

    T        = p["T_WEEKS"]
    n_crew   = p["N_CREW"]
    d_prot   = p["PROTEIN_G_DAY_PER_PERSON"] * n_crew    # g / day total
    d_kcal   = p["KCAL_DAY_PER_PERSON"] * n_crew          # kcal / day total
    BIG_M    = p["BIG_M"]
    w_E      = p["WEIGHT_EARTH_DEPENDENCY"]
    w_W      = p["WEIGHT_WATER"]

    all_ids = list(crops.keys()) + list(alt.keys())
    weeks   = list(range(1, T + 1))

    prob = pulp.LpProblem(f"Mars_to_Table_K{min_species}", pulp.LpMinimize)

    # ------------------------------------------------------------------
    # Decision variables
    # ------------------------------------------------------------------
    x = {
        (i, t): pulp.LpVariable(f"x_{i}_{t}_{min_species}", lowBound=0)
        for i in all_ids for t in weeks
    }
    y = {
        i: pulp.LpVariable(f"y_{i}_{min_species}", cat="Binary")
        for i in all_ids
    }
    delta_prot = {
        t: pulp.LpVariable(f"dp_{t}_{min_species}", lowBound=0)
        for t in weeks
    }
    delta_kcal = {
        t: pulp.LpVariable(f"dk_{t}_{min_species}", lowBound=0)
        for t in weeks
    }

    # ------------------------------------------------------------------
    # Objective function
    # ------------------------------------------------------------------
    water_terms = pulp.lpSum(
        crops[i]["w_i"] * crops[i]["a_i"] * x[(i, t)]
        for i in crops for t in weeks
    ) + pulp.lpSum(
        alt[i]["w_i"] * x[(i, t)]
        for i in alt for t in weeks
    )

    earth_dependency = (
        pulp.lpSum(delta_prot[t] for t in weeks) / d_prot
        + pulp.lpSum(delta_kcal[t] for t in weeks) / d_kcal
    )

    prob += (
        w_E * earth_dependency + w_W * water_terms,
        "Objective",
    )

    # ------------------------------------------------------------------
    # Weekly constraints
    # ------------------------------------------------------------------
    for t in weeks:
        # Protein supply (g / day)
        prot_supply = (
            pulp.lpSum(
                (crops[i]["r_prot_m2d"] / (crops[i]["edible_g_m2d"] / 1000))
                * x[(i, t)]
                for i in crops
            )
            + pulp.lpSum(alt[i]["r_prot_kg"] * x[(i, t)] for i in alt)
        )
        prob += prot_supply + delta_prot[t] >= d_prot,   f"Protein_t{t}"
        prob += delta_prot[t] <= _earth_cap(t, T) * d_prot, f"EarthProtCap_t{t}"

        # Calorie supply (kcal / day)
        kcal_supply = (
            pulp.lpSum(
                (crops[i]["r_kcal_m2d"] / (crops[i]["edible_g_m2d"] / 1000))
                * x[(i, t)]
                for i in crops
            )
            + pulp.lpSum(alt[i]["r_kcal_kg"] * x[(i, t)] for i in alt)
        )
        prob += kcal_supply + delta_kcal[t] >= d_kcal,   f"Calories_t{t}"
        prob += delta_kcal[t] <= _earth_cap(t, T) * d_kcal, f"EarthKcalCap_t{t}"

        # Cultivation area (m²)
        area_used = pulp.lpSum(crops[i]["a_i"] * x[(i, t)] for i in crops)
        prob += area_used <= p["MAX_AREA_M2"], f"Area_t{t}"

        # Daily water budget (L / day)
        water_day = (
            pulp.lpSum(crops[i]["w_i"] * crops[i]["a_i"] * x[(i, t)] for i in crops)
            + pulp.lpSum(alt[i]["w_i"] * x[(i, t)] for i in alt)
        )
        prob += water_day <= p["MAX_WATER_L_DAY"], f"Water_t{t}"

        # Alternative protein capacity (kg / day)
        alt_biomass = pulp.lpSum(x[(i, t)] for i in alt)
        prob += alt_biomass <= p["MAX_ALT_BIOMASS_KG_DAY"], f"AltBiomass_t{t}"

    # ------------------------------------------------------------------
    # Maturity / growth-cycle constraints
    # ------------------------------------------------------------------
    for i in all_ids:
        data      = crops.get(i) or alt.get(i)
        first_wk  = math.ceil(data["ciclo_dias"] / 7)
        for t in weeks:
            if t < first_wk:
                prob += x[(i, t)] == 0, f"Maturity_{i}_t{t}"

    # ------------------------------------------------------------------
    # Big-M activation linking
    # ------------------------------------------------------------------
    for i in all_ids:
        for t in weeks:
            prob += x[(i, t)] <= BIG_M * y[i], f"BigM_{i}_t{t}"

    # ------------------------------------------------------------------
    # Diversity constraint
    # ------------------------------------------------------------------
    prob += pulp.lpSum(y[i] for i in all_ids) >= min_species, "Diversity"

    # ------------------------------------------------------------------
    # Solve
    # ------------------------------------------------------------------
    solver = pulp.PULP_CBC_CMD(msg=0)
    prob.solve(solver)

    status = pulp.LpStatus[prob.status]
    if status != "Optimal":
        return {
            "K":      min_species,
            "status": status,
        }

    # ------------------------------------------------------------------
    # Extract results
    # ------------------------------------------------------------------
    weekly = {
        (i, t): pulp.value(x[(i, t)]) or 0.0
        for i in all_ids for t in weeks
    }

    agua_total   = sum(
        (crops[i]["w_i"] * crops[i]["a_i"] if i in crops else alt[i]["w_i"])
        * weekly[(i, t)]
        for i in all_ids for t in weeks
    )
    area_prom    = sum(
        crops[i]["a_i"] * weekly[(i, t)]
        for i in crops for t in weeks
    ) / T

    biomasa_alt_prom = sum(
        weekly[(i, t)] for i in alt for t in weeks
    ) / T

    active = [i for i in all_ids if (pulp.value(y[i]) or 0) > 0.5]

    return {
        "K":               min_species,
        "status":          status,
        "earth_dependency": pulp.value(earth_dependency),
        "agua_total":      agua_total,
        "area_prom":       area_prom,
        "biomasa_alt_prom": biomasa_alt_prom,
        "weekly":          weekly,
        "active_species":  active,
    }

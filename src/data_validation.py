"""
data_validation.py
==================
Loads and validates the Excel input data for the Mars to Table MILP model.

Expected sheets:
    - Cultivos_Fotosinteticos  (header on row 4, i.e. header=3)
    - Proteinas_Alternativas   (header on row 4, i.e. header=3)

The function load_and_validate_data() returns two dicts (crops, alt) that
are consumed directly by model.py.  It also prints warnings for non-critical
issues and raises SystemExit if critical data is missing or invalid.

Caloric values for alternative proteins (not in the Excel) are sourced from:
    FAO Nutritional Database, USDA FoodData Central,
    Oonincx et al. 2015 (J. Insects Food Feed), Finke 2002.
"""

import math
import sys

import pandas as pd

# ---------------------------------------------------------------------------
# Caloric density (kcal / kg product) for alternative protein sources.
# These are literature-derived estimates — treat as modeling assumptions.
# ---------------------------------------------------------------------------
ALT_KCAL_PER_KG: dict[str, float] = {
    "Grillo (Acheta domesticus)": 4500,
    "Tenebrio / gusano de la harina (Tenebrio molitor)": 5500,
    "Micoproteina / Fusarium venenatum (tipo Quorn)": 1100,
    "Hongo ostra / Oyster mushroom (Pleurotus ostreatus)": 330,
    "Carne cultivada / Cultivated meat (celulas animales in vitro)": 2500,
}

# Default water use for oyster mushroom (NaN in the original Excel).
# Estimated by analogy with mycoprotein. Validated range: 0.42–1.26 m³/kg DM.
# We use 1 500 L/kg fresh weight as a conservative estimate.
DEFAULT_WATER_OYSTER_MUSHROOM: float = 1500.0


def load_and_validate_data(excel_path: str) -> tuple[dict, dict]:
    """Load the Excel workbook and return validated crop and alt-protein dicts.

    Parameters
    ----------
    excel_path : str
        Path to *candidatos_mars_to_table.xlsx*.

    Returns
    -------
    crops : dict
        Keyed by candidate name; contains nutritional and resource parameters
        for photosynthetic crops.
    alt : dict
        Keyed by candidate name; contains parameters for alternative protein
        sources.

    Raises
    ------
    SystemExit
        If any critical data field is missing, NaN, negative, or zero where
        a positive value is required.
    """
    df1 = (
        pd.read_excel(excel_path, sheet_name="Cultivos_Fotosinteticos", header=3)
        .dropna(subset=["Candidato"])
    )
    df2 = (
        pd.read_excel(excel_path, sheet_name="Proteinas_Alternativas", header=3)
        .dropna(subset=["Candidato"])
    )

    crops: dict = {}
    alt: dict = {}
    errors: list[str] = []
    warnings: list[str] = []

    # ------------------------------------------------------------------
    # Photosynthetic crops
    # ------------------------------------------------------------------
    for _, row in df1.iterrows():
        name: str = row["Candidato"]

        r_prot  = float(row["r_proteina_g_m2_d"])
        r_kcal  = float(row["r_calorico_kcal_m2_d"])
        a_i     = float(row["a_i_m2_por_kg_comestible_dia"])
        w_i     = float(row["Agua_L_m2_d"])
        edible  = float(row["Biomasa_comestible_gDM_m2_d"])
        ciclo   = float(row["Ciclo_dias"])

        for label, val in [
            ("r_proteina", r_prot),
            ("r_calorico", r_kcal),
            ("a_i",        a_i),
            ("w_i",        w_i),
            ("edible",     edible),
            ("ciclo_dias", ciclo),
        ]:
            if math.isnan(val):
                errors.append(f"[{name}] {label} = NaN (critical data missing)")
            elif val < 0:
                errors.append(f"[{name}] {label} = {val} (negative — must be ≥ 0)")
            elif val == 0 and label in ("r_proteina", "r_calorico", "edible"):
                warnings.append(
                    f"[{name}] {label} = 0 (crop does not contribute this nutrient)"
                )

        if not math.isnan(ciclo) and ciclo <= 0:
            errors.append(f"[{name}] ciclo_dias = {ciclo} (must be > 0)")

        # Consistency check: calculated protein concentration vs. % DM
        if edible > 0:
            prot_conc_calc = r_prot / (edible / 1000)          # g protein / kg biomass
            prot_pct_dm = row.get("Proteina_pct_DM", float("nan"))
            if not math.isnan(float(prot_pct_dm)):
                prot_conc_expected = float(prot_pct_dm) * 10   # g / kg
                if abs(prot_conc_calc - prot_conc_expected) > prot_conc_expected * 0.5:
                    warnings.append(
                        f"[{name}] Protein inconsistency: "
                        f"calculated={prot_conc_calc:.1f} g/kg vs. "
                        f"Proteina_pct_DM*10={prot_conc_expected:.1f} g/kg"
                    )

        crops[name] = {
            "tipo":         "fotosintetico",
            "r_prot_m2d":  r_prot,    # g protein / (m² · day)
            "r_kcal_m2d":  r_kcal,    # kcal / (m² · day)
            "a_i":         a_i,        # m² / (kg edible · day)
            "w_i":         w_i,        # L / (m² · day)
            "edible_g_m2d": edible,    # g DM / (m² · day)
            "ciclo_dias":  ciclo,      # days to first harvest
        }

    # ------------------------------------------------------------------
    # Alternative protein sources
    # ------------------------------------------------------------------
    for _, row in df2.iterrows():
        name = row["Candidato"]

        r_prot_kg = float(row["r_proteina_g_por_kg_producto"])
        agua      = row["Agua_L_por_kg_producto"]
        ciclo     = float(row["Ciclo_dias"])

        # Handle missing water data (oyster mushroom)
        if pd.isna(agua):
            agua = DEFAULT_WATER_OYSTER_MUSHROOM
            warnings.append(
                f"[{name}] Agua_L_por_kg_producto = NaN in Excel. "
                f"Using default {DEFAULT_WATER_OYSTER_MUSHROOM} L/kg "
                f"(estimated by analogy with mycoprotein — validate experimentally)."
            )
        else:
            agua = float(agua)

        # Caloric density lookup
        if name not in ALT_KCAL_PER_KG:
            warnings.append(
                f"[{name}] Not found in ALT_KCAL_PER_KG. "
                f"Add estimated calories (kcal/kg product) to the dictionary. "
                f"Setting r_kcal_kg = 0 for now."
            )
            r_kcal_kg = 0.0
        else:
            r_kcal_kg = ALT_KCAL_PER_KG[name]

        # Consistency check: r_proteina_g_por_kg vs. Proteina_pct_producto
        prot_pct = row.get("Proteina_pct_producto", float("nan"))
        if not math.isnan(float(prot_pct)):
            expected_prot = float(prot_pct) * 10
            if abs(r_prot_kg - expected_prot) > 1.0:
                warnings.append(
                    f"[{name}] Inconsistency: r_proteina_g_por_kg={r_prot_kg} "
                    f"vs. Proteina_pct_producto*10={expected_prot}"
                )

        alt[name] = {
            "tipo":       "alternativo",
            "r_prot_kg":  r_prot_kg,  # g protein / kg product
            "r_kcal_kg":  r_kcal_kg,  # kcal / kg product
            "w_i":        agua,        # L / kg product
            "ciclo_dias": ciclo,       # days to first harvest
        }

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------
    if warnings:
        print("\n=== WARNINGS (non-blocking) ===")
        for w in warnings:
            print(f"  ⚠️  {w}")

    if errors:
        print("\n=== CRITICAL ERRORS (blocking) ===")
        for e in errors:
            print(f"  ❌  {e}")
        print("\n>>> Aborting: fix the errors in the Excel or code before continuing.")
        sys.exit(1)

    print(
        f"\n✅ Validation successful: {len(crops)} photosynthetic crops "
        f"and {len(alt)} alternative proteins."
    )
    return crops, alt

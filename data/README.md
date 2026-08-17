# Data — Mars to Table Optimization

## Primary dataset

### `candidatos_mars_to_table.xlsx`

The main input workbook for the MILP model. Contains two sheets:

---

### Sheet: `Cultivos_Fotosinteticos`

13 photosynthetic crop candidates. Data starts on row 4 (`header=3` in pandas).

| Column | Unit | Description |
|--------|------|-------------|
| `Candidato` | — | Species name |
| `r_proteina_g_m2_d` | g·m⁻²·day⁻¹ | Protein yield per unit area |
| `r_calorico_kcal_m2_d` | kcal·m⁻²·day⁻¹ | Caloric yield per unit area |
| `a_i_m2_por_kg_comestible_dia` | m²·(kg·day)⁻¹ | Area required per unit production |
| `Agua_L_m2_d` | L·m⁻²·day⁻¹ | Water use per unit area |
| `Biomasa_comestible_gDM_m2_d` | g DM·m⁻²·day⁻¹ | Edible dry-matter yield per area |
| `Ciclo_dias` | days | Growth cycle to first harvest |
| `Proteina_pct_DM` | % | Protein as percentage of dry matter (used for consistency checks) |

**Candidates included:**
Wheat (*Triticum aestivum*), Soybean (*Glycine max*), Potato (*Solanum tuberosum*),
Sweet potato (*Ipomoea batatas*), Lettuce (*Lactuca sativa*), Tomato (*Solanum lycopersicum*),
Rice (*Oryza sativa*), Peanut (*Arachis hypogaea*), Quinoa (*Chenopodium quinoa*),
Moringa (*Moringa oleifera*), Spirulina (*Arthrospira platensis*),
Chlorella (*Chlorella vulgaris*), Duckweed (*Lemna minor*).

---

### Sheet: `Proteinas_Alternativas`

5 alternative protein sources. Same header structure (`header=3`).

| Column | Unit | Description |
|--------|------|-------------|
| `Candidato` | — | Species / product name |
| `r_proteina_g_por_kg_producto` | g·kg⁻¹ | Protein per kg of product |
| `Agua_L_por_kg_producto` | L·kg⁻¹ | Water use per kg of product |
| `Ciclo_dias` | days | Growth/production cycle |
| `Proteina_pct_producto` | % | Protein as % of product (consistency check) |

**Note:** `Agua_L_por_kg_producto` is **NaN** for oyster mushroom. The model
substitutes a default value of 1,500 L/kg with a warning. See
`docs/assumptions.md` for the rationale.

**Note:** Caloric density (`kcal/kg`) is **not present** in this sheet. Values
are supplied from literature in `src/data_validation.py` → `ALT_KCAL_PER_KG`.

**Candidates included:**
Cricket (*Acheta domesticus*), Mealworm (*Tenebrio molitor*),
Mycoprotein / Quorn (*Fusarium venenatum*),
Oyster mushroom (*Pleurotus ostreatus*),
Cultivated meat (in-vitro animal cells).

---

## Data provenance

Nutritional and agronomic data for photosynthetic crops were compiled from:
- NASA Advanced Life Support documentation
- FAO crop composition tables
- Published controlled-environment agriculture (CEA) studies

Alternative protein data were compiled from:
- FAO Nutritional Database
- USDA FoodData Central
- Oonincx et al. 2015 (*J. Insects as Food and Feed*)
- Finke 2002 (*Zoo Biology*)
- Post 2012 (*J. Science of Food and Agriculture*)

---

## Loading the data

```python
from src.data_validation import load_and_validate_data

crops, alt = load_and_validate_data("data/candidatos_mars_to_table.xlsx")
```

The function validates all fields, raises warnings for non-critical issues,
and exits with a clear message if critical data is missing or invalid.

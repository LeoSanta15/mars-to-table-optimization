# Modeling Assumptions — Mars to Table MILP

This document distinguishes **data** (sourced from the literature or from the
NASA Mars to Table challenge dataset) from **modeling assumptions** (engineering
estimates introduced to make the model tractable). Assumptions should be treated
as hypotheses: sensitivity-testing them is part of responsible OR practice.

---

## 1. Mission Parameters

| Parameter | Value | Basis | Assumption level |
|-----------|-------|-------|-----------------|
| Crew size | 4 persons | Standard reference in NASA long-duration mission literature | Low — well-established |
| Planning horizon | 16 weeks | Chosen to cover one growing cycle for the slowest crop | Medium — could be extended to a full mission |
| Protein requirement | 60 g/person/day | WHO/FAO minimum for adults under physical activity | Low |
| Calorie requirement | 2,100 kcal/person/day | NASA standard for long-duration missions | Low |

---

## 2. Resource Limits

| Parameter | Value | Basis | Assumption level |
|-----------|-------|-------|-----------------|
| Maximum cultivation area | 100 m² | Illustrative upper bound consistent with proposed Mars habitat volumes | **High** — must be validated against mission design |
| Maximum daily water | 2,000 L/day | Consistent with ECLSS closed-loop water recovery scenarios | **High** — sensitive to ECLSS design |
| Maximum alt. protein biomass | 5 kg/day | Engineering estimate for insect/fungal bioreactor capacity | **High** |

---

## 3. Caloric Density of Alternative Proteins

These values are **not in the Excel file** and were derived from the literature:

| Candidate | kcal/kg | Source |
|-----------|---------|--------|
| Grillo (*Acheta domesticus*) | 4,500 | Finke 2002; Oonincx et al. 2015 |
| Tenebrio (*Tenebrio molitor*) | 5,500 | USDA FoodData Central; Finke 2002 |
| Mycoprotein (*Fusarium venenatum*, Quorn-type) | 1,100 | FAO Nutritional Database |
| Oyster mushroom (*Pleurotus ostreatus*) | 330 | USDA FoodData Central (fresh weight) |
| Cultivated meat (in-vitro animal cells) | 2,500 | Post et al. 2012; estimated from bovine muscle composition |

**Impact:** If caloric densities are off by ±20%, the model may select different
alternative proteins. A sensitivity analysis on these values is recommended.

---

## 4. Water Recycling Rates

The candidate-specific recycling rates used in the post-optimisation water balance
are **reasoned engineering estimates** based on ECLSS and hydroponic raceway data.
No study directly measures "water recycling rate per space food-system candidate."

| Candidate group | Assumed rate | Rationale |
|-----------------|-------------|-----------|
| Hydroponic crops (wheat, soy, potato, etc.) | 0.95–0.96 | High-efficiency closed-loop hydroponics |
| Microalgae / aquatic macrophytes | 0.94 | Slightly lower due to open raceway losses |
| Insect farming (cricket, mealworm) | 0.75 | Significant water embedded in frass and feed |
| Mycoprotein | 0.80 | Fermentation medium partially non-recoverable |
| Oyster mushroom | 0.65 | Substrate absorption losses |
| Cultivated meat | 0.70 | Cell culture medium losses |

**Default fallback:** 0.90 for any candidate not in the table.

---

## 5. Oyster Mushroom Water Use

`Agua_L_por_kg_producto` is **NaN in the original Excel file** for oyster mushroom.

**Assumed value:** 1,500 L/kg (fresh weight basis).

**Rationale:** *Pleurotus ostreatus* literature reports 0.42–1.26 m³/kg on a dry-weight
basis. Adjusting to fresh weight (~90% water content) and using a conservative
mid-range estimate gives ~1,500 L/kg fresh. This should be validated experimentally.

---

## 6. Earth Supply Capacity Decay

The fraction of nutritional demand that Earth can supply decreases linearly from
100% in week 1 to 0% in week 16:

$$\alpha(t) = \max\!\left(0,\ 1 - \frac{t-1}{T-1}\right)$$

**Assumption:** Linear decay is a simplification. In reality, the transition could be
step-wise (resupply missions), exponential (as the crew learns to farm), or depend
on mission phase. A scenario analysis with different decay functions is recommended.

---

## 7. Maturity Constraints

A candidate cannot produce before completing its growth cycle ($c_i$ days),
converted to weeks via $\lceil c_i / 7 \rceil$. This assumes:

- Growth cycles are deterministic (no stochastic yield variation).
- The entire growth cycle must complete before **any** harvest (simplification
  for crops with continuous harvest like lettuce).
- The cycle is measured from mission start (no pre-positioning).

---

## 8. Nutritional Model

The model tracks only **protein** and **calories**. It does not explicitly model:

- Micronutrients (vitamins, minerals)
- Dietary fiber
- Fat-to-protein ratios
- Food palatability / crew acceptance

Including micronutrient constraints would significantly increase model complexity
and is recommended for a production-grade system.

---

## 9. Objective Function Weights

| Weight | Value | Rationale |
|--------|-------|-----------|
| `WEIGHT_EARTH_DEPENDENCY` ($w_E$) | 1,000 | Dominant objective — self-sufficiency is the primary goal |
| `WEIGHT_WATER` ($w_W$) | 0.001 | Tie-breaker — water efficiency is secondary |

These weights encode a **value judgment** that should be discussed with mission
stakeholders. A multi-objective analysis (Pareto frontier) would be a more rigorous
approach to understanding the full trade-off surface.

---

## 10. What the Results Are (and Are Not)

> ✅ **What they are:** Optimal solutions under the stated assumptions and parameters.
> They show which portfolios are theoretically self-sufficient and how diversity
> affects resource consumption.

> ❌ **What they are not:** Experimental predictions, validated engineering designs,
> or official NASA recommendations. The model is an academic Operations Research
> case study inspired by the public NASA Mars to Table challenge.

A good optimizer identifies not only a solution but also **which assumptions most
affect the decision** — this document exists for exactly that purpose.

---

## References

- FAO/WHO (2007). *Protein and Amino Acid Requirements in Human Nutrition.*
- Finke, M.D. (2002). Complete nutrient composition of commercially raised invertebrates.
  *Zoo Biology*, 21(3), 269–285.
- Oonincx, D.G.A.B., et al. (2015). Nutritional value of insects and its significance
  for the production of insects as food. *Journal of Insects as Food and Feed*, 1(2), 103–115.
- Post, M.J. (2012). Cultured beef: medical technology to produce food.
  *Journal of the Science of Food and Agriculture*, 94(6), 1039–1041.
- USDA FoodData Central. https://fdc.nal.usda.gov/
- NASA Mars to Table Challenge. https://www.nasa.gov/prizes-challenges-and-crowdsourcing/marstotable/

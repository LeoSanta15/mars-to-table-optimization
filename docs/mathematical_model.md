# Mathematical Model — Mars to Table MILP

## 1. Problem Description

Given a crew of **N** members on a Mars mission of **T** weeks, we must decide which combination of photosynthetic crops and alternative protein sources to operate in order to **minimize dependence on Earth** while satisfying nutritional, resource, production-capacity, maturity-cycle, and biodiversity constraints.

---

## 2. Sets and Indices

| Symbol | Description |
|--------|-------------|
| $i \in \mathcal{F}$ | Photosynthetic crop candidates (13 species) |
| $i \in \mathcal{A}$ | Alternative protein candidates (5 sources) |
| $\mathcal{C} = \mathcal{F} \cup \mathcal{A}$ | All candidates |
| $t \in \{1,\ldots,T\}$ | Planning weeks ($T = 16$) |

---

## 3. Parameters

### Mission parameters

| Symbol | Value | Unit | Description |
|--------|-------|------|-------------|
| $N$ | 4 | persons | Crew size |
| $T$ | 16 | weeks | Planning horizon |
| $d_{\text{prot}}$ | $N \times 60$ | g/day | Daily protein demand |
| $d_{\text{kcal}}$ | $N \times 2{,}100$ | kcal/day | Daily calorie demand |

### Crop parameters (photosynthetic, $i \in \mathcal{F}$)

| Symbol | Column in Excel | Unit | Description |
|--------|-----------------|------|-------------|
| $r_{\text{prot},i}^{m^2}$ | `r_proteina_g_m2_d` | g·m⁻²·day⁻¹ | Protein yield per area |
| $r_{\text{kcal},i}^{m^2}$ | `r_calorico_kcal_m2_d` | kcal·m⁻²·day⁻¹ | Caloric yield per area |
| $a_i$ | `a_i_m2_por_kg_comestible_dia` | m²·kg⁻¹·day | Area required per unit production |
| $w_i^F$ | `Agua_L_m2_d` | L·m⁻²·day⁻¹ | Water use per area |
| $e_i$ | `Biomasa_comestible_gDM_m2_d` | g·m⁻²·day⁻¹ | Edible dry-matter yield per area |
| $c_i$ | `Ciclo_dias` | days | Growth cycle (days to first harvest) |

### Alternative protein parameters ($i \in \mathcal{A}$)

| Symbol | Column in Excel | Unit | Description |
|--------|-----------------|------|-------------|
| $r_{\text{prot},i}^{\text{kg}}$ | `r_proteina_g_por_kg_producto` | g·kg⁻¹ | Protein per kg of product |
| $r_{\text{kcal},i}^{\text{kg}}$ | Computed from literature | kcal·kg⁻¹ | Calories per kg of product |
| $w_i^A$ | `Agua_L_por_kg_producto` | L·kg⁻¹ | Water use per kg of product |
| $c_i$ | `Ciclo_dias` | days | Growth cycle |

### Resource limits

| Symbol | Value | Unit | Description |
|--------|-------|------|-------------|
| $A_{\max}$ | 100 | m² | Maximum cultivation area |
| $W_{\max}$ | 2,000 | L/day | Maximum daily water budget |
| $B_{\max}$ | 5 | kg/day | Maximum alternative-protein biomass |

### Objective weights

| Symbol | Value | Description |
|--------|-------|-------------|
| $w_E$ | 1,000 | Weight on Earth dependency (dominant) |
| $w_W$ | 0.001 | Weight on water use (tie-breaker) |
| $M$ | $10^5$ | Big-M constant for activation linking |

---

## 4. Decision Variables

$$x_{i,t} \geq 0$$

Daily production of candidate $i$ in week $t$.
- For $i \in \mathcal{F}$: kg/day of edible biomass.
- For $i \in \mathcal{A}$: kg/day of product.

$$y_i \in \{0, 1\}$$

Binary activation variable: 1 if candidate $i$ is part of the production portfolio, 0 otherwise.

$$\delta_{\text{prot},t} \geq 0$$

Protein deficit covered by Earth supply in week $t$ (g/day).

$$\delta_{\text{kcal},t} \geq 0$$

Calorie deficit covered by Earth supply in week $t$ (kcal/day).

---

## 5. Objective Function

$$\min \quad w_E \cdot \text{EarthDependency} + w_W \cdot \text{TotalWater}$$

where

$$\text{EarthDependency} = \frac{\sum_t \delta_{\text{prot},t}}{d_{\text{prot}}} + \frac{\sum_t \delta_{\text{kcal},t}}{d_{\text{kcal}}}$$

$$\text{TotalWater} = \sum_{i \in \mathcal{F}} \sum_t w_i^F \cdot a_i \cdot x_{i,t} + \sum_{i \in \mathcal{A}} \sum_t w_i^A \cdot x_{i,t}$$

The dominant term ($w_E$) minimises dependence on Earth; the secondary term ($w_W$) breaks ties by preferring water-efficient solutions.

---

## 6. Constraints

### 6.1 Protein supply

$$\underbrace{\sum_{i \in \mathcal{F}} \frac{r_{\text{prot},i}^{m^2}}{e_i/1000} x_{i,t}}_{\text{crops}} + \underbrace{\sum_{i \in \mathcal{A}} r_{\text{prot},i}^{\text{kg}} x_{i,t}}_{\text{alt. proteins}} + \delta_{\text{prot},t} \geq d_{\text{prot}} \qquad \forall t$$

### 6.2 Calorie supply

$$\underbrace{\sum_{i \in \mathcal{F}} \frac{r_{\text{kcal},i}^{m^2}}{e_i/1000} x_{i,t}}_{\text{crops}} + \underbrace{\sum_{i \in \mathcal{A}} r_{\text{kcal},i}^{\text{kg}} x_{i,t}}_{\text{alt. proteins}} + \delta_{\text{kcal},t} \geq d_{\text{kcal}} \qquad \forall t$$

### 6.3 Earth supply capacity (linearly decreasing)

$$\delta_{\text{prot},t} \leq \alpha(t) \cdot d_{\text{prot}}, \quad \delta_{\text{kcal},t} \leq \alpha(t) \cdot d_{\text{kcal}} \qquad \forall t$$

$$\alpha(t) = \max\!\left(0,\ 1 - \frac{t-1}{T-1}\right)$$

This models progressive mission self-sufficiency: Earth can supply 100% in week 1 and 0% in week $T$.

### 6.4 Cultivation area

$$\sum_{i \in \mathcal{F}} a_i \cdot x_{i,t} \leq A_{\max} \qquad \forall t$$

### 6.5 Water budget

$$\sum_{i \in \mathcal{F}} w_i^F \cdot a_i \cdot x_{i,t} + \sum_{i \in \mathcal{A}} w_i^A \cdot x_{i,t} \leq W_{\max} \qquad \forall t$$

### 6.6 Alternative protein capacity

$$\sum_{i \in \mathcal{A}} x_{i,t} \leq B_{\max} \qquad \forall t$$

### 6.7 Maturity / growth cycle

$$x_{i,t} = 0 \qquad \forall i \in \mathcal{C},\ t < \left\lceil c_i / 7 \right\rceil$$

### 6.8 Big-M activation linking

$$x_{i,t} \leq M \cdot y_i \qquad \forall i \in \mathcal{C},\ \forall t$$

### 6.9 Diversity constraint

$$\sum_{i \in \mathcal{C}} y_i \geq K$$

This turns biodiversity into a decision variable and allows studying the **opportunity cost of resilience**:

> *"What is the additional resource cost of requiring at least K active species?"*

---

## 7. Model Characteristics

| Property | Value |
|----------|-------|
| Type | Mixed-Integer Linear Program (MILP) |
| Solver | CBC (via PuLP) |
| Continuous variables | $x_{i,t}$, $\delta_{\text{prot},t}$, $\delta_{\text{kcal},t}$ |
| Binary variables | $y_i$ |
| Candidates $|\mathcal{C}|$ | 18 (13 crops + 5 alt. proteins) |
| Planning weeks $T$ | 16 |
| Size (approx.) | ~300 variables, ~700 constraints |

---

## 8. Scenario Analysis

The model is solved for $K \in \{1, 3, 5, 7, 9, 11, 13, 15\}$ to generate the **diversity trade-off curve**. Key output metrics per scenario:

| Metric | Description |
|--------|-------------|
| `Dependencia_Tierra` | Earth dependency index (lower = more self-sufficient) |
| `Agua_total_prom_L_dia` | Average daily water use across the mission |
| `Area_usada_prom_m2` | Average cultivation area used |
| `Biomasa_alt_prom_kg_dia` | Average alternative protein production |
| `Especies_activas` | Number of active species in the solution |

---

## 9. Water Balance Extension

Beyond the optimisation model, the notebook computes a post-hoc water balance using candidate-specific recycling rates $\rho_i \in [0, 1]$:

$$\text{Net make-up water} = \sum_{i,t} (1 - \rho_i) \cdot w_i \cdot x_{i,t}$$

A sensitivity analysis sweeps global recycling rates from 85% to 99% to quantify the dependence of net water replenishment on ECLSS efficiency assumptions.

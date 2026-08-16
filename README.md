# 🚀 Mars to Table — Operations Research Optimization

## MILP Optimization of a Food Production System for a Mars Mission

An Operations Research case study inspired by NASA's Mars to Table challenge.

The objective is to determine an optimal portfolio of crops and alternative
protein sources that minimizes dependence on Earth while satisfying nutritional,
water, land, production and biodiversity constraints.

---

## 🎯 Problem

How can a crew produce enough food during a long-duration Mars mission while
minimizing dependence on Earth?

The model considers:

- 4 crew members
- 16-week planning horizon
- 13 photosynthetic crops
- 5 alternative protein sources
- Protein requirements
- Calorie requirements
- Maximum cultivation area
- Maximum water availability
- Alternative protein capacity
- Crop maturation cycles
- Minimum biodiversity requirements
- Earth dependency

---

## 🧠 Operations Research Approach

The problem is formulated as a:

**Mixed-Integer Linear Programming (MILP)** model.

### Decision variables

`x[i,t]` — production of candidate `i` during week `t`

`y[i]` — binary variable indicating whether candidate `i`
is included in the production portfolio.

### Objective

Minimize:

Earth dependency + water consumption

subject to nutritional, resource, production and biodiversity constraints.

---

## 🔬 Key OR Concepts

- Mixed-Integer Linear Programming
- Portfolio optimization
- Resource allocation
- Capacity constraints
- Multi-period planning
- Trade-off analysis
- Sensitivity analysis
- Scenario analysis
- Supply Chain Optimization

---

## 📊 Diversity Trade-off

A key feature of the model is the parameter:

`K = minimum number of active species`

This allows us to study the trade-off between:

**Efficiency ↔ Resilience**

Increasing biodiversity may require additional resources,
but can potentially create a more resilient food-production system.

---

## 💧 Water Analysis

The model also evaluates:

- Gross water consumption
- Candidate-specific recycling rates
- Net water replenishment
- Embedded water
- Transpiration
- Sensitivity to recycling efficiency

---

## 🛠️ Technology

Python  
PuLP  
CBC Solver  
Pandas  
Matplotlib  
OpenPyXL  
Google Colab

---

## 📓 Notebook

Run the complete analysis in Google Colab:

[Open in Google Colab]([YOUR_COLAB_LINK](https://colab.research.google.com/drive/1RI7b9FgOnZNSo5h4vMQgmRMEDr2YCqSd?usp=sharing))

---

## 🌎 NASA Reference

This project is inspired by NASA's Mars to Table challenge:

https://www.nasa.gov/prizes-challenges-and-crowdsourcing/marstotable/

This is an independent Operations Research case study and is
not an official NASA model.

---

## 🚀 Future Work

Potential extensions include:

- Stochastic Optimization
- Robust Optimization
- Monte Carlo simulation
- Multi-objective optimization
- Energy constraints
- Crop failure scenarios
- Inventory and resupply
- Dynamic optimization
- Reinforcement Learning

---

## 👨‍💻 Author

Angel Santamaria Galarza

Operations Research | Supply Chain Optimization | Python

(https://www.linkedin.com/in/angel-santamaria-galarza-793980120/)

## 📄 License

MIT License

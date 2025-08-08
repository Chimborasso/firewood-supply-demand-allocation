# Firewood Supply–Demand Allocation (Hungary)

This repository contains Python code to model the spatial allocation of surplus firewood supply to industrial and residential demand centres at the municipal level. The method uses an OD (origin–destination) cost matrix and a greedy allocation algorithm with a user-defined distance cutoff, providing a fast and transparent alternative to ArcMap's Location–Allocation tool.

---

## Why Python instead of ArcMap’s Location–Allocation?

ArcMap’s *maximize capacitated coverage* solver works well for many cases, but has key limitations when applied to large, high-resolution datasets such as municipal-level biomass flows:

- **Scalability** – ArcMap’s solver becomes slow or fails with >1 million OD pairs.
- **Flexibility** – distance cutoffs and allocation rules are harder to customise.
- **Transparency & reproducibility** – Python code can be openly shared, reviewed, and adapted by others without requiring proprietary software.
- **Lightweight** – no need for Network Analyst license once the OD matrix is prepared.

This Python workflow reproduces the core allocation logic, honours capacity limits, allows distance thresholds (e.g. 50 km), and calculates weighted transport costs for industrial and residential demand separately.

---

## Workflow

1. **Prepare input data**
   - **OD_matrix_cleaned.csv** – origin, destination, and road network distance (km).
   - **demand_supply.csv** – municipal supply, industrial demand, and residential demand.

2. **Run the script**
   - Loads input CSVs.
   - Allocates surplus supply first to industrial demand, then to residential demand.
   - Respects the distance cutoff (e.g. 50 km).
   - Minimises total transport distance through greedy allocation.

3. **Output**
   - `firewood_allocation_result.csv` – allocation table with origin, destination, allocated volume, distance, demand type, and weighted cost.
   - Summary statistics on total volume allocated and weighted transport costs.

---

## Requirements

- Python ≥ 3.9  
- pandas

Install with:

```bash
pip install pandas

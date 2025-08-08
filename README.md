# Firewood Location-Allocation Model (Hungary)

This repository contains the Python implementation used in a scientific paper, to be submitted later

The model allocates projected municipal firewood supply to **industrial** and **residential** demand points, 
prioritising industrial demand and minimising transport distances.  
It applies a **greedy, distance-first** algorithm similar to GIS location–allocation, 
using an Origin–Destination (OD) distance matrix derived from a road network (e.g., OpenStreetMap).

---

## Features

- **Two-stage allocation**:  
  1. Allocate to industrial demand first  
  2. Allocate remaining supply to residential demand
- **Greedy algorithm**: iterates OD pairs sorted by shortest distance
- **Optional distance cutoff** (e.g., 50 km) to restrict allocations
- **UTF-8 with BOM** output for compatibility with Hungarian diacritics in Excel

---

## Input data

### 1. Demand–Supply CSV
Required columns:
| NAME | SUPPLY | INDUSTRIAL_DEMAND | RESIDENTIAL_DEMAND |
|------|--------|-------------------|--------------------|
| Budapest_I.  | 0     | 0     | 227   |
| Budapest_II. | 328   | 0     | 4548  |
| ...          | ...   | ...   | ...   |

> Delimiter can be `;` or `,` — the script will detect automatically.  
> Names must match the `origin_id` / `destination_id` in the OD matrix.

### 2. OD Matrix CSV
Required columns:
| origin_id | destination_id | distance_km |
|-----------|----------------|-------------|
| Budapest_I. | Budapest_II. | 4.5 |
| ...         | ...           | ... |

---

## Example usage

```bash
python firewood_allocation.py \
    --demand_supply example_data/demand_supply_example.csv \
    --od example_data/OD_matrix_cleaned_example.csv \
    --out firewood_allocation_result.csv \
    --cutoff_km 50


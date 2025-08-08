"""
Firewood Location-Allocation (Hungary) — Industrial priority, greedy distance minimization.

Overview
--------
This script allocates municipal firewood supply to industrial demand first, then to residential
demand, minimizing weighted transport effort (volume × distance) using a greedy, distance-first
strategy. Transport distances are taken from an OD (origin–destination) cost matrix built
on a road network (e.g., ArcGIS Network Analyst + OSM roads). An optional distance cutoff
(e.g., 50 km) restricts allocations to local flows.

Inputs (CSV)
------------
1) demand_supply.csv  (semicolon or comma delimited)
   Required columns:
     - NAME                  : municipality name (string) — must match OD matrix names
     - SUPPLY                : available firewood supply (m³, float)
     - INDUSTRIAL_DEMAND     : industrial demand (m³, float)
     - RESIDENTIAL_DEMAND    : residential demand (m³, float)

2) OD_matrix_cleaned.csv  (comma delimited recommended)
   Required columns:
     - origin_id             : origin municipality name (string)
     - destination_id        : destination municipality name (string)
     - distance_km           : road distance (km, float)

Outputs
-------
- firewood_allocation_result.csv
    Columns: origin_id, destination_id, allocated_volume, distance_km, demand_type, weighted_cost

- Summary is printed to stdout:
    total allocated (m³) and weighted costs (m³·km) by demand type.

Usage
-----
$ python firewood_allocation.py \
    --demand_supply demand_supply.csv \
    --od OD_matrix_cleaned.csv \
    --out firewood_allocation_result.csv \
    --cutoff_km 50

Notes
-----
- Greedy algorithm: iterates OD pairs sorted by distance; at each step allocates as much as possible
  given remaining supply + remaining demand. Not globally optimal, but transparent and fast.
- Ensure municipality names are consistent between files (diacritics, punctuation).
"""

import argparse
import pandas as pd
from pathlib import Path

def load_demand_supply(path: str) -> pd.DataFrame:
    """Load demand/supply with robust delimiter handling and enforce numeric types."""
    # Try semicolon first (common in EU exports), then comma
    try:
        df = pd.read_csv(path, delimiter=";")
        if df.shape[1] == 1:
            # Fallback to comma
            df = pd.read_csv(path)
    except Exception:
        df = pd.read_csv(path)

    # Normalize expected column names if users used alternatives
    rename_map = {
        'DEMAND_INDUSTRY': 'INDUSTRIAL_DEMAND',
        'DEMAND_RESIDENTIAL': 'RESIDENTIAL_DEMAND',
        'name': 'NAME',
        'supply': 'SUPPLY',
        'industrial_demand': 'INDUSTRIAL_DEMAND',
        'residential_demand': 'RESIDENTIAL_DEMAND',
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    required = {'NAME', 'SUPPLY', 'INDUSTRIAL_DEMAND', 'RESIDENTIAL_DEMAND'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in demand_supply: {missing}")

    # Clean numeric columns
    for col in ['SUPPLY', 'INDUSTRIAL_DEMAND', 'RESIDENTIAL_DEMAND']:
        # Replace commas as decimal separators if present, then cast
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .replace({'': '0', 'nan': '0'})
        )
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # Strip whitespace in names
    df['NAME'] = df['NAME'].astype(str).str.strip()
    return df

def load_od(path: str) -> pd.DataFrame:
    """Load OD matrix (expects comma-delimited), ensure correct dtypes."""
    od = pd.read_csv(path)
    # Normalize headers if needed
    od = od.rename(columns={
        'Origin': 'origin_id',
        'Destination': 'destination_id',
        'Distance_km': 'distance_km',
        'distance': 'distance_km'
    })
    required = {'origin_id', 'destination_id', 'distance_km'}
    missing = required - set(od.columns)
    if missing:
        raise ValueError(f"Missing required columns in OD matrix: {missing}")

    # Clean distance (guard against commas as decimal separators)
    od['distance_km'] = (
        od['distance_km']
        .astype(str)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )
    # Strip whitespace in names
    od['origin_id'] = od['origin_id'].astype(str).str.strip()
    od['destination_id'] = od['destination_id'].astype(str).str.strip()
    # Sort shortest first
    od = od.sort_values('distance_km', kind='mergesort').reset_index(drop=True)
    return od

def greedy_allocate(od_df: pd.DataFrame,
                    supply_map: dict,
                    demand_map: dict,
                    demand_type: str,
                    cutoff_km: float | None = None) -> tuple[list, float]:
    """
    Greedy distance-first allocation for a single demand map (industrial OR residential).
    Returns (allocations_list, total_weighted_cost).
    """
    allocations = []
    total_weighted_cost = 0.0

    # Iterate in ascending distance order
    for _, row in od_df.iterrows():
        o = row['origin_id']
        d = row['destination_id']
        dist = row['distance_km']

        if cutoff_km is not None and dist > cutoff_km:
            continue

        s_left = supply_map.get(o, 0.0)
        d_left = demand_map.get(d, 0.0)
        if s_left <= 0.0 or d_left <= 0.0:
            continue

        alloc = s_left if s_left < d_left else d_left
        if alloc <= 0.0:
            continue

        supply_map[o] = s_left - alloc
        demand_map[d] = d_left - alloc

        wcost = alloc * dist
        total_weighted_cost += wcost

        allocations.append({
            'origin_id': o,
            'destination_id': d,
            'allocated_volume': float(alloc),
            'distance_km': float(dist),
            'demand_type': demand_type,
            'weighted_cost': float(wcost),
        })

    return allocations, total_weighted_cost

def main(args):
    demand_supply = load_demand_supply(args.demand_supply)
    od_df = load_od(args.od)

    # Build lookup dicts
    supply = demand_supply.set_index('NAME')['SUPPLY'].to_dict()
    ind = demand_supply.set_index('NAME')['INDUSTRIAL_DEMAND'].to_dict()
    res = demand_supply.set_index('NAME')['RESIDENTIAL_DEMAND'].to_dict()

    # First pass: INDUSTRIAL priority
    alloc_ind, cost_ind = greedy_allocate(
        od_df, supply_map=supply, demand_map=ind,
        demand_type='industrial', cutoff_km=args.cutoff_km
    )

    # Second pass: RESIDENTIAL with remaining supply
    alloc_res, cost_res = greedy_allocate(
        od_df, supply_map=supply, demand_map=res,
        demand_type='residential', cutoff_km=args.cutoff_km
    )

    # Concatenate
    alloc_df = pd.DataFrame(alloc_ind + alloc_res)

    # Save (UTF-8 with BOM helps Excel with diacritics)
    out_path = Path(args.out)
    alloc_df.to_csv(out_path, index=False, encoding='utf-8-sig')

    total_alloc = alloc_df['allocated_volume'].sum() if not alloc_df.empty else 0.0
    print("✅ Allocation complete.")
    print(f"Total firewood allocated: {total_alloc:,.2f} m³")
    print(f"  ↳ Industrial weighted cost: {cost_ind:,.2f} m³·km")
    print(f"  ↳ Residential weighted cost: {cost_res:,.2f} m³·km")
    print(f"Saved results to: {out_path.resolve()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Firewood location-allocation (industrial priority).")
    parser.add_argument("--demand_supply", required=True, help="Path to demand_supply CSV.")
    parser.add_argument("--od", required=True, help="Path to OD_matrix_cleaned CSV.")
    parser.add_argument("--out", default="firewood_allocation_result.csv", help="Output CSV path.")
    parser.add_argument("--cutoff_km", type=float, default=50.0, help="Max distance (km) for allocation. Use e.g. 50.")
    args = parser.parse_args()
    main(args)

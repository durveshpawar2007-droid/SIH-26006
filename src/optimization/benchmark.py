import json
import os
import pandas as pd
from ortools.linear_solver import pywraplp

VESSEL_CAPACITY = {
    "HANDYSIZE": 32000,
    "SUPRAMAX": 50000,
    "PANAMAX": 70000,
    "CAPESIZE": 150000,
}

# Baseline Freight Cost ($/MT)
BASE_RATES = {
    ("PARADIP", "HANDYSIZE"): 23.5,
    ("PARADIP", "SUPRAMAX"): 22.0,
    ("PARADIP", "PANAMAX"): 20.2,
    ("PARADIP", "CAPESIZE"): 17.5,
    ("VIZAG", "HANDYSIZE"): 23.0,
    ("VIZAG", "SUPRAMAX"): 21.8,
    ("VIZAG", "PANAMAX"): 19.9,
    ("VIZAG", "CAPESIZE"): 17.2,
    ("HALDIA", "HANDYSIZE"): 24.5,
    ("HALDIA", "SUPRAMAX"): 22.9,
    ("HALDIA", "PANAMAX"): 21.0,
    ("HALDIA", "CAPESIZE"): 999.0,  # Infeasible draft penalty
}


def compute_plant_demands(plants_df):
  """Computes exact 30-day import requirement (MT) based on plant burn schedule."""
  demands = {}
  for _, row in plants_df.iterrows():
    monthly_import_mt = (
        30.0 * row["daily_consumption_mt"] * (row["import_share_pct"] / 100.0)
    )
    demands[row["plant"]] = monthly_import_mt
  return demands


def run_heuristic_baseline(plants_df, rate_matrix, usd_inr_rate):
  """Simulates the industry default heuristic (PSU Rule-of-Thumb):

  Dispatches primarily through each plant's designated preferred port using
  standard Panamax / Supramax spot fixtures without joint linear optimization.
  """
  total_cost_usd = 0.0
  allocation = {}

  for _, row in plants_df.iterrows():
    plant = row["plant"]
    pref_port = row["preferred_port"]
    demand_needed = 30.0 * row["daily_consumption_mt"] * (
        row["import_share_pct"] / 100.0
    )

    # Heuristic strategy: Fill demand using standard Panamax shipments
    # If Haldia, use Supramax due to draft limits
    vessel = "SUPRAMAX" if pref_port == "HALDIA" else "PANAMAX"
    cap = VESSEL_CAPACITY[vessel]
    num_vessels = int(-(-demand_needed // cap))  # Ceiling division

    cost = num_vessels * cap * rate_matrix.get((pref_port, vessel), 25.0)
    total_cost_usd += cost
    allocation[plant] = {
        "port": pref_port,
        "vessel": vessel,
        "count": num_vessels,
        "delivered_mt": num_vessels * cap,
        "cost_usd": cost,
    }

  return {
      "total_usd": total_cost_usd,
      "total_inr_cr": (total_cost_usd * usd_inr_rate) / 1e7,
      "details": allocation,
  }


def run_milp_optimizer(plants_df, ports_df, rate_matrix, usd_inr_rate):
  """Runs Google OR-Tools SCIP Mixed-Integer Linear Program."""
  capesize_ports = set(ports_df[ports_df["capesize_capable"] == True]["port"])
  plants = plants_df["plant"].tolist()
  ports = ports_df["port"].tolist()
  vessel_types = list(VESSEL_CAPACITY.keys())
  demands = compute_plant_demands(plants_df)

  solver = pywraplp.Solver.CreateSolver("SCIP")
  voyages = {}

  for pl in plants:
    for po in ports:
      for v in vessel_types:
        voyages[(pl, po, v)] = solver.IntVar(0, 10, f"v_{pl}_{po}_{v}")

  # Constraint: Haldia Port Draft Guardrail
  for pl in plants:
    for po in ports:
      if po not in capesize_ports:
        solver.Add(voyages[(pl, po, "CAPESIZE")] == 0)

  # Constraint: Plant Demand Satisfaction
  for pl in plants:
    solver.Add(
        solver.Sum(
            voyages[(pl, po, v)] * VESSEL_CAPACITY[v]
            for po in ports
            for v in vessel_types
        )
        >= demands[pl]
    )

  # Objective: Minimize Total Maritime Freight Cost
  objective = solver.Objective()
  for pl in plants:
    for po in ports:
      for v in vessel_types:
        voyage_cost = (
            rate_matrix.get((po, v), 25.0) * VESSEL_CAPACITY[v]
        )
        objective.SetCoefficient(voyages[(pl, po, v)], voyage_cost)
  objective.SetMinimization()

  status = solver.Solve()
  if status != pywraplp.Solver.OPTIMAL:
    return None

  total_cost_usd = solver.Objective().Value()
  total_cost_inr_cr = (total_cost_usd * usd_inr_rate) / 1e7

  charter_summary = []
  for pl in plants:
    for po in ports:
      for v in vessel_types:
        c = int(voyages[(pl, po, v)].solution_value())
        if c > 0:
          charter_summary.append({
              "plant": pl,
              "port": po,
              "vessel": v,
              "vessels_chartered": c,
              "tonnage_mt": c * VESSEL_CAPACITY[v],
          })

  return {
      "total_usd": total_cost_usd,
      "total_inr_cr": total_cost_inr_cr,
      "charters": charter_summary,
  }


def execute_stress_benchmarks():
  ports_df = pd.read_csv(os.path.join("data", "processed", "port_constraints.csv"))
  plants_df = pd.read_csv(os.path.join("data", "processed", "plant_params.csv"))

  scenarios = [
      {
          "name": "Baseline Market",
          "fuel_multiplier": 1.0,
          "charter_multiplier": 1.0,
          "usd_inr": 83.00,
          "notes": "Current prevailing commercial conditions",
      },
      {
          "name": "Bunker Shock (+20%)",
          "fuel_multiplier": 1.20,
          "charter_multiplier": 1.0,
          "usd_inr": 83.00,
          "notes": "VLSFO bunker costs spike from $809.5 to $971.4/MT",
      },
      {
          "name": "Forex Risk (+5% USD/INR)",
          "fuel_multiplier": 1.0,
          "charter_multiplier": 1.0,
          "usd_inr": 101.40,
          "notes": "Rupee depreciates by 5% to 101.40 vs USD",
      },
      {
          "name": "Freight Surge (+30%)",
          "fuel_multiplier": 1.0,
          "charter_multiplier": 1.30,
          "usd_inr": 83.00,
          "notes": "Baltic Dry Index volatility inflates charter rates by 30%",
      },
  ]

  results = []
  print("\n" + "=" * 90)
  print(
      f"{'SCENARIO':<25} | {'HEURISTIC (INR)':<16} | {'MILP OPT (INR)':<16} |"
      f" {'SAVINGS (INR)':<15} | {'SAVINGS %'}"
  )
  print("=" * 90)

  for sc in scenarios:
    # Scale freight rate components
    # Maritime freight is roughly 40% fuel opex + 60% vessel day charter rate
    scaled_rates = {}
    for k, v in BASE_RATES.items():
      if v >= 900.0:
        scaled_rates[k] = v
      else:
        scaled_fuel_comp = (v * 0.40) * sc["fuel_multiplier"]
        scaled_charter_comp = (v * 0.60) * sc["charter_multiplier"]
        scaled_rates[k] = scaled_fuel_comp + scaled_charter_comp

    heuristic_res = run_heuristic_baseline(plants_df, scaled_rates, sc["usd_inr"])
    milp_res = run_milp_optimizer(plants_df, ports_df, scaled_rates, sc["usd_inr"])

    cost_heur = heuristic_res["total_inr_cr"]
    cost_milp = milp_res["total_inr_cr"]
    savings_cr = cost_heur - cost_milp
    savings_pct = (savings_cr / cost_heur) * 100.0

    print(
        f"{sc['name']:<25} | ₹{cost_heur:10.2f} Cr  | ₹{cost_milp:10.2f} Cr  |"
        f" ₹{savings_cr:10.2f} Cr   | {savings_pct:6.2f}%"
    )

    results.append({
        "scenario": sc["name"],
        "notes": sc["notes"],
        "heuristic_cost_usd": heuristic_res["total_usd"],
        "heuristic_cost_inr_cr": cost_heur,
        "milp_cost_usd": milp_res["total_usd"],
        "milp_cost_inr_cr": cost_milp,
        "savings_inr_cr": savings_cr,
        "savings_percentage": round(savings_pct, 2),
        "optimized_dispatch_plan": milp_res["charters"],
    })

  print("=" * 90)

  # Export clean JSON artifact for API & Pitch Deck
  out_path = os.path.join("data", "metadata", "stress_test_benchmarks.json")
  os.makedirs(os.path.dirname(out_path), exist_ok=True)
  with open(out_path, "w") as f:
    json.dump(results, f, indent=2)

  print(f"\n[+] Benchmark metrics saved to: {out_path}")


if __name__ == "__main__":
  execute_stress_benchmarks()
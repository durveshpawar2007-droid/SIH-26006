import os
import pandas as pd
from ortools.linear_solver import pywraplp


def run_coking_coal_optimizer():
  print("=" * 65)
  print("SIH26006: Google OR-Tools Supply Chain & Freight Dispatch Engine")
  print("=" * 65)

  # 1. Load operational constraints and parameters
  port_constraints_path = os.path.join("data", "processed", "port_constraints.csv")
  plant_params_path = os.path.join("data", "processed", "plant_params.csv")

  ports_df = pd.read_csv(port_constraints_path)
  plants_df = pd.read_csv(plant_params_path)

  # Check Capesize eligibility by destination port draft
  # Haldia (max draft 9.1m) explicitly prohibits Capesize vessels
  capesize_ports = set(ports_df[ports_df["capesize_capable"] == True]["port"])

  plants = plants_df["plant"].tolist()
  ports = ports_df["port"].tolist()
  vessel_types = ["HANDYSIZE", "SUPRAMAX", "PANAMAX", "CAPESIZE"]

  # Cargo capacity per vessel class (MT)
  vessel_capacity = {
      "HANDYSIZE": 32000,
      "SUPRAMAX": 50000,
      "PANAMAX": 70000,
      "CAPESIZE": 150000,
  }

  # Estimated freight rates ($/MT) derived from market baseline/forecaster
  rate_matrix = {
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
      ("HALDIA", "CAPESIZE"): 999.0,  # Infeasible penalty rate
  }

  # 30-day coal procurement requirement (MT) derived from daily plant consumption
  # Formula: 30 days * daily_consumption * import_share_pct
  demand = {}
  for _, row in plants_df.iterrows():
    monthly_import_mt = (
        30.0 * row["daily_consumption_mt"] * (row["import_share_pct"] / 100.0)
    )
    demand[row["plant"]] = monthly_import_mt

  # 2. Initialize the Mixed-Integer Linear Programming (MILP) Solver
  solver = pywraplp.Solver.CreateSolver("SCIP")
  if not solver:
    print("[!] Error: SCIP solver not found.")
    return

  # 3. Decision Variables: integer number of vessels to charter
  # voyages[plant, port, vessel_type]
  voyages = {}
  for pl in plants:
    for po in ports:
      for v in vessel_types:
        voyages[(pl, po, v)] = solver.IntVar(
            0, 10, f"voyage_{pl}_{po}_{v}"
        )

  # 4. Physical Constraints

  # (A) Haldia Port Draft Guardrail: Force Capesize allocations to 0
  for pl in plants:
    for v in vessel_types:
      if v == "CAPESIZE":
        for po in ports:
          if po not in capesize_ports:
            solver.Add(voyages[(pl, po, v)] == 0)

  # (B) Plant Demand Satisfaction: Total imported coal must meet blast furnace burn schedule
  for pl in plants:
    solver.Add(
        solver.Sum(
            voyages[(pl, po, v)] * vessel_capacity[v]
            for po in ports
            for v in vessel_types
        )
        >= demand[pl]
    )

  # 5. Objective Function: Minimize Total Delivered Maritime Freight Expenditure ($)
  objective = solver.Objective()
  for pl in plants:
    for po in ports:
      for v in vessel_types:
        cost_per_voyage = rate_matrix.get((po, v), 25.0) * vessel_capacity[v]
        objective.SetCoefficient(voyages[(pl, po, v)], cost_per_voyage)

  objective.SetMinimization()

  # 6. Execute Optimization
  status = solver.Solve()

  if status == pywraplp.Solver.OPTIMAL:
    total_cost_usd = solver.Objective().Value()
    print("\n[+] OPTIMAL LOGISTICS PLAN FOUND:")
    print(f"    - Total 30-Day Ocean Freight Bill: ${total_cost_usd:,.2f} USD")
    print(f"    - Equivalent in INR: ₹{(total_cost_usd * 83.0 / 1e7):.2f} Crores\n")
    print("--- Optimized Vessel Charters ---")

    for pl in plants:
      delivered_mt = 0
      print(f"\n>> Plant: {pl} (Target Demand: {demand[pl]:,.0f} MT)")
      for po in ports:
        for v in vessel_types:
          count = int(voyages[(pl, po, v)].solution_value())
          if count > 0:
            volume = count * vessel_capacity[v]
            delivered_mt += volume
            print(
                f"   * Charter {count}x {v:<9} -> Discharge Port: {po:<8} | Cargo: {volume:,.0f} MT"
            )
      print(f"   Total Delivered: {delivered_mt:,.0f} MT")

    print("\n" + "=" * 65)
    print("Optimization finished successfully.")
    print("=" * 65)
  else:
    print("[!] No optimal solution found.")


if __name__ == "__main__":
  run_coking_coal_optimizer()
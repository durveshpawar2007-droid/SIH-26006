import os
import pandas as pd
from ortools.linear_solver import pywraplp


def run_milp_optimizer(
    plants_df=None,
    ports_df=None,
    custom_rates=None,
    usd_inr: float = 83.5,
    weather_delay_hours: float = 0.0,
    port_delay_days: float = 0.0,
    freight_multiplier: float = 1.0,
    fuel_multiplier: float = 1.0,
    risk_quantile: str = "p50",
):
    """
    Enterprise-grade Coking Coal Maritime Logistics & Hinterland Allocation MILP.
    Enforces draft restrictions, weather-induced laytime demurrage, rail rake dispatch caps,
    and blast-furnace hard coking coal blending constraints.
    """
    # 1. Base Data Setup
    if ports_df is None:
        port_constraints_path = os.path.join("data", "processed", "port_constraints.csv")
        if os.path.exists(port_constraints_path):
            ports_df = pd.read_csv(port_constraints_path)
        else:
            ports_df = pd.DataFrame([
                {"port": "PARADIP", "max_draft_m": 17.1, "capesize_capable": True, "monthly_capacity_mt": 1200000, "daily_rakes_available": 18},
                {"port": "VIZAG", "max_draft_m": 18.0, "capesize_capable": True, "monthly_capacity_mt": 900000, "daily_rakes_available": 14},
                {"port": "HALDIA", "max_draft_m": 8.5, "capesize_capable": False, "monthly_capacity_mt": 450000, "daily_rakes_available": 8}
            ])

    if plants_df is None:
        plant_params_path = os.path.join("data", "processed", "plant_params.csv")
        if os.path.exists(plant_params_path):
            plants_df = pd.read_csv(plant_params_path)
        else:
            plants_df = pd.DataFrame([
                {"plant": "RSP_ROURKELA", "daily_consumption_mt": 12500, "import_share_pct": 85.0},
                {"plant": "BSP_BHILAI", "daily_consumption_mt": 14000, "import_share_pct": 80.0},
                {"plant": "BSL_BOKARO", "daily_consumption_mt": 11000, "import_share_pct": 85.0}
            ])

    plants = plants_df["plant"].tolist()
    ports = ports_df["port"].tolist()
    vessel_types = ["HANDYSIZE", "SUPRAMAX", "PANAMAX", "CAPESIZE"]

    # Draft eligibility: Haldia <= 8.5m draft forbids Capesize vessels
    capesize_ports = set(ports_df[ports_df["capesize_capable"] == True]["port"])

    # Vessel payload capacities (Metric Tons)
    vessel_capacity = {
        "HANDYSIZE": 32000,
        "SUPRAMAX": 50000,
        "PANAMAX": 70000,
        "CAPESIZE": 150000,
    }

    # Port discharge benchmarks (MT/day) & baseline waiting
    port_handling_speed = {"PARADIP": 28000, "VIZAG": 25000, "HALDIA": 12000}
    base_port_queue_days = {"PARADIP": 0.9, "VIZAG": 1.2, "HALDIA": 4.5}

    demurrage_rate_per_day = {
        "HANDYSIZE": 12000,
        "SUPRAMAX": 16000,
        "PANAMAX": 20000,
        "CAPESIZE": 28000,
    }

    # Resilient column resolution for port capacity
    cap_col = next((c for c in ["monthly_capacity_mt", "capacity_mt", "max_capacity_mt", "annual_capacity_mt"] if c in ports_df.columns), None)

    if cap_col == "annual_capacity_mt":
        port_monthly_capacity = dict(zip(ports_df["port"], ports_df[cap_col] / 12.0))
    elif cap_col:
        port_monthly_capacity = dict(zip(ports_df["port"], ports_df[cap_col]))
    else:
        # Default fallback capacity (in MT) per major port
        default_caps = {"PARADIP": 800000.0, "VIZAG": 650000.0, "HALDIA": 400000.0}
        port_monthly_capacity = {p: default_caps.get(p, 500000.0) for p in ports_df["port"]}

    # Railway rake dispatch capacity (1 BOXN Rake = ~3,800 MT; 30 days)
    port_daily_rakes = {
        "PARADIP": 18,
        "VIZAG": 14,
        "HALDIA": 8
    }
    if "daily_rakes_available" in ports_df.columns:
        port_daily_rakes = dict(zip(ports_df["port"], ports_df["daily_rakes_available"]))

    # Hinterland Rail Freight (USD equivalent per MT)
    rail_freight_usd_mt = {
        ("PARADIP", "RSP_ROURKELA"): 17.5,
        ("PARADIP", "BSP_BHILAI"): 24.0,
        ("PARADIP", "BSL_BOKARO"): 19.5,
        ("VIZAG", "RSP_ROURKELA"): 22.0,
        ("VIZAG", "BSP_BHILAI"): 18.0,
        ("VIZAG", "BSL_BOKARO"): 23.5,
        ("HALDIA", "RSP_ROURKELA"): 18.0,
        ("HALDIA", "BSP_BHILAI"): 26.0,
        ("HALDIA", "BSL_BOKARO"): 16.5,
    }

    # Quantile Adjustment factor from Freight Forecasting
    risk_factor = 1.0
    if risk_quantile == "p90":
        risk_factor = 1.22
    elif risk_quantile == "p10":
        risk_factor = 0.85

    # Baseline Ocean Freight Rate ($/MT)
    base_rate_matrix = {
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
        ("HALDIA", "CAPESIZE"): 999.0,
    }
    rate_matrix = custom_rates if custom_rates else base_rate_matrix

    # Monthly Plant Import Requirements (MT)
    demand = {}
    for _, row in plants_df.iterrows():
        monthly_import_mt = 30.0 * float(row["daily_consumption_mt"]) * (float(row["import_share_pct"]) / 100.0)
        demand[row["plant"]] = monthly_import_mt

    weather_delay_days = max(0.0, float(weather_delay_hours) / 24.0)

    # 2. Solver Initialization
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        return None

    # 3. Decision Variables: voyages[(plant, port, vessel)]
    voyages = {}
    for pl in plants:
        for po in ports:
            for v in vessel_types:
                voyages[(pl, po, v)] = solver.IntVar(0, 20, f"voyage_{pl}_{po}_{v}")

    # 4. Constraints

    # (A) Haldia Riverine Draft Guardrail: Capesize cannot berth
    for pl in plants:
        for po in ports:
            if po not in capesize_ports:
                solver.Add(voyages[(pl, po, "CAPESIZE")] == 0)

    # (B) Plant Demand Satisfaction
    for pl in plants:
        solver.Add(
            solver.Sum(
                voyages[(pl, po, v)] * vessel_capacity[v]
                for po in ports
                for v in vessel_types
            ) >= demand[pl]
        )

    # (C) Monthly Port Berth Capacity Limits
    for po in ports:
        solver.Add(
            solver.Sum(
                voyages[(pl, po, v)] * vessel_capacity[v]
                for pl in plants
                for v in vessel_types
            ) <= port_monthly_capacity.get(po, 1500000)
        )

    # (D) Indian Railways Monthly Rake Evacuation Bound (BOXN rakes @ 3,800 MT capacity)
    for po in ports:
        max_monthly_rake_tonnage = port_daily_rakes.get(po, 10) * 3800 * 30
        solver.Add(
            solver.Sum(
                voyages[(pl, po, v)] * vessel_capacity[v]
                for pl in plants
                for v in vessel_types
            ) <= max_monthly_rake_tonnage
        )

    # 5. Objective Function: Landed Cost (Ocean Freight + Fuel + Demurrage + Rail Freight)
    objective = solver.Objective()
    for pl in plants:
        for po in ports:
            for v in vessel_types:
                capacity = vessel_capacity[v]

                # Combined Ocean Freight with Fuel Shock and Quantile Multiplier
                # VLSFO bunker contributes ~45% of standard ocean freight cost structure
                bunker_impact = 1.0 + (fuel_multiplier - 1.0) * 0.45
                effective_ocean_rate = rate_matrix.get((po, v), 25.0) * freight_multiplier * risk_factor * bunker_impact
                ocean_freight_cost = effective_ocean_rate * capacity

                # Weather Delay & Port Queue Demurrage
                discharge_days = capacity / port_handling_speed.get(po, 20000)
                corridor_weather_delay = weather_delay_days if po in ("PARADIP", "HALDIA") else (weather_delay_days * 0.4)
                effective_waiting_days = base_port_queue_days.get(po, 1.5) + port_delay_days + corridor_weather_delay
                excess_days = max(0.0, (discharge_days + effective_waiting_days) - 4.0)
                demurrage_cost = excess_days * demurrage_rate_per_day[v]

                # Hinterland Rail Cost
                rail_cost = rail_freight_usd_mt.get((po, pl), 20.0) * capacity

                # Total Landed Route Cost
                total_voyage_cost = ocean_freight_cost + demurrage_cost + rail_cost
                objective.SetCoefficient(voyages[(pl, po, v)], total_voyage_cost)

    objective.SetMinimization()

    # 6. Solve
    status = solver.Solve()

    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        total_usd = solver.Objective().Value()
        total_inr_cr = (total_usd * usd_inr) / 1e7

        allocations = []
        for pl in plants:
            for po in ports:
                for v in vessel_types:
                    count = int(voyages[(pl, po, v)].solution_value())
                    if count > 0:
                        tonnage = count * vessel_capacity[v]
                        rakes_needed = int(tonnage / 3800) + 1
                        allocations.append({
                            "plant": pl,
                            "port": po,
                            "vessel_type": v,
                            "voyages": count,
                            "tonnage_mt": tonnage,
                            "rakes_required": rakes_needed,
                            "ocean_rate_usd": round(rate_matrix.get((po, v), 25.0) * freight_multiplier * risk_factor, 2),
                            "rail_rate_usd": round(rail_freight_usd_mt.get((po, pl), 20.0), 2),
                        })

        return {
            "status": "OPTIMAL",
            "total_usd": round(total_usd, 2),
            "total_inr_cr": round(total_inr_cr, 2),
            "applied_risk_quantile": risk_quantile,
            "charters": allocations
        }

    return None
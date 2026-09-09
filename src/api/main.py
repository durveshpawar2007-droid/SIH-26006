import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
from src.optimization.benchmark import run_milp_optimizer, BASE_RATES

app = FastAPI(
    title="SIH-26006 Logistics Optimization Engine",
    version="1.0.0",
    description="Mathematical Dispatch Engine & Stress Testing Service for Coking Coal Supply Chain"
)

class ScenarioRequest(BaseModel):
    fuel_multiplier: float = 1.0
    charter_multiplier: float = 1.0
    usd_inr: float = 83.00

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "coking-coal-optimizer"}

@app.get("/api/v1/benchmarks")
def get_benchmarks():
    benchmark_path = os.path.join("data", "metadata", "stress_test_benchmarks.json")
    if not os.path.exists(benchmark_path):
        raise HTTPException(status_code=404, detail="Benchmark metrics not found.")
    with open(benchmark_path, "r") as f:
        data = json.load(f)
    return {"benchmarks": data}

@app.post("/api/v1/optimize")
def optimize_dispatch(params: ScenarioRequest):
    ports_df = pd.read_csv(os.path.join("data", "processed", "port_constraints.csv"))
    plants_df = pd.read_csv(os.path.join("data", "processed", "plant_params.csv"))

    scaled_rates = {}
    for k, v in BASE_RATES.items():
        if v >= 900.0:
            scaled_rates[k] = v
        else:
            scaled_fuel = (v * 0.40) * params.fuel_multiplier
            scaled_charter = (v * 0.60) * params.charter_multiplier
            scaled_rates[k] = scaled_fuel + scaled_charter

    solution = run_milp_optimizer(plants_df, ports_df, scaled_rates, params.usd_inr)
    if not solution:
        raise HTTPException(status_code=500, detail="Infeasible optimization problem.")

    return {
        "status": "OPTIMAL",
        "parameters": params.dict(),
        "total_cost_usd": solution["total_usd"],
        "total_cost_inr_crores": round(solution["total_inr_cr"], 2),
        "charter_allocations": solution["charters"]
    }
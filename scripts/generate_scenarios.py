"""
SIH26006 — Scenario Generator Script.

Creates data/synthetic/scenario_data.csv for what-if sensitivity simulations:
- Bunker fuel +20% (fuel price shock)
- Paradip port congestion +4 days (weather / peak demand surge)
- Vizag port congestion +3 days (monsoon / inner harbour wait)
- USD/INR +5% depreciation (currency risk)
- BDI / charter market surge +30% (tight bulk shipping market)

CRITICAL RULE:
Every row in this file is tagged data_type = 'SYNTHETIC' and scenario_type.
Synthetic data NEVER modifies historical market data or processed datasets.
"""

import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.constants import SYNTHETIC
from src.config.settings import DATA_PROCESSED_DIR, DATA_SYNTHETIC_DIR, LOG_FORMAT, LOG_LEVEL


def main():
    logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
    logger = logging.getLogger("generate_scenarios")

    processed_dir = Path(DATA_PROCESSED_DIR)
    synthetic_dir = Path(DATA_SYNTHETIC_DIR)
    synthetic_dir.mkdir(parents=True, exist_ok=True)

    market_path = processed_dir / "market_data.csv"
    port_path = processed_dir / "port_constraints.csv"

    if not market_path.exists():
        logger.error(f"Market data file not found: {market_path}")
        sys.exit(1)

    market_df = pd.read_csv(market_path)
    latest_rows = market_df.dropna(subset=["bunker_vlsfo", "usd_inr"]).tail(30).copy()

    scenario_rows = []

    for _, row in latest_rows.iterrows():
        dt = row["date"]
        base_bunker = row["bunker_vlsfo"]
        base_fx = row["usd_inr"]
        base_bdry = row["bdry_close"] if pd.notna(row["bdry_close"]) else 10.0

        # Scenario 1: Bunker +20%
        sc_bunker = base_bunker * 1.20
        scenario_rows.append({
            "scenario_name": "Bunker +20%",
            "date": dt,
            "variable": "bunker_vlsfo",
            "baseline_value": round(base_bunker, 2),
            "scenario_value": round(sc_bunker, 2),
            "change_pct": 20.0,
            "scenario_type": "COST_SHOCK",
            "data_type": SYNTHETIC,
        })

        # Scenario 2: USD/INR +5% Depreciation
        sc_fx = base_fx * 1.05
        scenario_rows.append({
            "scenario_name": "USD/INR +5% Depreciation",
            "date": dt,
            "variable": "usd_inr",
            "baseline_value": round(base_fx, 2),
            "scenario_value": round(sc_fx, 2),
            "change_pct": 5.0,
            "scenario_type": "FOREX_RISK",
            "data_type": SYNTHETIC,
        })

        # Scenario 3: Freight Market Surge (+30%)
        sc_bdry = base_bdry * 1.30
        scenario_rows.append({
            "scenario_name": "Freight Market Surge +30%",
            "date": dt,
            "variable": "charter_rate_proxy",
            "baseline_value": round(base_bdry, 2),
            "scenario_value": round(sc_bdry, 2),
            "change_pct": 30.0,
            "scenario_type": "MARKET_VOLATILITY",
            "data_type": SYNTHETIC,
        })

    # Scenario 4 & 5: Port Congestion Scenarios
    if port_path.exists():
        port_df = pd.read_csv(port_path)
        for _, p_row in port_df.iterrows():
            port_name = p_row["port"]
            base_wait = (p_row["avg_preberthing_wait_hrs_low"] + p_row["avg_preberthing_wait_hrs_high"]) / 2.0

            if port_name == "PARADIP":
                # Paradip congestion +4 days (+96 hrs)
                sc_wait = base_wait + 96.0
                chg = (96.0 / base_wait) * 100.0 if base_wait > 0 else 100.0
                scenario_rows.append({
                    "scenario_name": "Paradip Congestion +4 Days",
                    "date": "CURRENT_SIMULATION",
                    "variable": "paradip_preberthing_wait_hrs",
                    "baseline_value": round(base_wait, 1),
                    "scenario_value": round(sc_wait, 1),
                    "change_pct": round(chg, 1),
                    "scenario_type": "OPERATIONAL_BOTTLENECK",
                    "data_type": SYNTHETIC,
                })
            elif port_name == "VIZAG":
                # Vizag congestion +3 days (+72 hrs)
                sc_wait = base_wait + 72.0
                chg = (72.0 / base_wait) * 100.0 if base_wait > 0 else 100.0
                scenario_rows.append({
                    "scenario_name": "Vizag Congestion +3 Days",
                    "date": "CURRENT_SIMULATION",
                    "variable": "vizag_preberthing_wait_hrs",
                    "baseline_value": round(base_wait, 1),
                    "scenario_value": round(sc_wait, 1),
                    "change_pct": round(chg, 1),
                    "scenario_type": "OPERATIONAL_BOTTLENECK",
                    "data_type": SYNTHETIC,
                })

    out_df = pd.DataFrame(scenario_rows)
    out_path = synthetic_dir / "scenario_data.csv"
    out_df.to_csv(out_path, index=False)

    logger.info(f"Generated {len(out_df)} scenario simulation rows -> {out_path}")
    print(f"[OK] scenario_data.csv created: {len(out_df)} rows tagged SYNTHETIC")


if __name__ == "__main__":
    main()

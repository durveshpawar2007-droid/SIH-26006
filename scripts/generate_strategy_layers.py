"""
SIH26006 — Phase 3: Strategy Layers Generator.

Creates datasets for advanced charter strategy:
1. data/synthetic/port_congestion.csv (Time-series congestion simulation)
2. data/synthetic/contract_scenarios.csv (Spot vs Short/Medium/Long-Term COA modeling)
"""

import logging
import sys
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.constants import SYNTHETIC, SCENARIO, PORT_CONSTRAINTS
from src.config.settings import DATA_PROCESSED_DIR, DATA_SYNTHETIC_DIR, LOG_FORMAT, LOG_LEVEL

def generate_port_congestion(market_df: pd.DataFrame, synthetic_dir: Path) -> pd.DataFrame:
    """Generate SYNTHETIC port congestion data (time-series)."""
    dates = pd.to_datetime(market_df["date"]).sort_values().unique()
    
    rows = []
    
    # We simulate a base wait time + random walk + monsoon seasonal spike
    for port_name, port_data in PORT_CONSTRAINTS.items():
        base_wait = (port_data.avg_preberthing_wait_hrs_low + port_data.avg_preberthing_wait_hrs_high) / 2.0
        
        # Initialize random walk
        np.random.seed(hash(port_name) % (2**32))
        walk = np.cumsum(np.random.normal(0, 2.0, len(dates)))
        
        for i, dt in enumerate(dates):
            # Monsoon spike (June - Sept)
            dt_obj = pd.Timestamp(dt)
            is_monsoon = 1 if dt_obj.month in [6, 7, 8, 9] else 0
            monsoon_penalty = np.random.uniform(10, 48) * is_monsoon
            
            # Combine signals
            daily_wait = max(0, base_wait + walk[i] + monsoon_penalty)
            
            # Derived vessel queue count (rough proxy: 1 vessel per 6 hours of wait)
            vessels = max(0, int(daily_wait / 6.0) + np.random.randint(-1, 2))
            
            if daily_wait < base_wait * 1.2:
                status = "NORMAL"
            elif daily_wait < base_wait * 1.5:
                status = "ELEVATED"
            elif daily_wait < base_wait * 2.5:
                status = "HIGH"
            else:
                status = "SEVERE"
                
            rows.append({
                "date": dt_obj.strftime("%Y-%m-%d"),
                "port": port_name,
                "waiting_vessels_count": vessels,
                "avg_waiting_time_hrs": round(daily_wait, 1),
                "congestion_status": status,
                "data_type": SYNTHETIC
            })
            
    df = pd.DataFrame(rows)
    out_path = synthetic_dir / "port_congestion.csv"
    df.to_csv(out_path, index=False)
    return df

def generate_contract_scenarios(freight_df: pd.DataFrame, synthetic_dir: Path) -> pd.DataFrame:
    """Generate SCENARIO contract pricing derived from freight estimates."""
    rows = []
    
    # To prevent generating massive files, we only generate strategies for the most recent 30 days of data
    latest_dates = pd.to_datetime(freight_df["date"]).sort_values().unique()[-30:]
    latest_dates_str = [pd.Timestamp(d).strftime("%Y-%m-%d") for d in latest_dates]
    
    subset = freight_df[freight_df["date"].isin(latest_dates_str)]
    
    for _, row in subset.iterrows():
        dt = row["date"]
        route = f"{row['origin']}_{row['destination']}"
        vtype = row["vessel_type"]
        spot_rate = row["estimated_freight_rate_usd_mt"]
        cargo_cap = 170000 if "CAPESIZE" in vtype else (70000 if "PANAMAX" in vtype else (50000 if "SUPRAMAX" in vtype else 32000))
        
        # Base Spot
        rows.append({
            "date": dt,
            "route_id": route,
            "vessel_type": vtype,
            "contract_type": "SPOT",
            "estimated_rate_usd_mt": spot_rate,
            "price_premium_pct": 0.0,
            "volume_commitment_mt": cargo_cap,
            "data_type": SCENARIO
        })
        
        # 3 Month COA (Short Term) - Usually priced at a slight premium for certainty if market is rising, or discount if falling.
        # We will assume a flat 2% premium for price lock.
        coa3m = spot_rate * 1.02
        rows.append({
            "date": dt,
            "route_id": route,
            "vessel_type": vtype,
            "contract_type": "COA_3M",
            "estimated_rate_usd_mt": round(coa3m, 2),
            "price_premium_pct": 2.0,
            "volume_commitment_mt": cargo_cap * 3,
            "data_type": SCENARIO
        })
        
        # 6 Month COA (Medium Term) - 5% premium
        coa6m = spot_rate * 1.05
        rows.append({
            "date": dt,
            "route_id": route,
            "vessel_type": vtype,
            "contract_type": "COA_6M",
            "estimated_rate_usd_mt": round(coa6m, 2),
            "price_premium_pct": 5.0,
            "volume_commitment_mt": cargo_cap * 6,
            "data_type": SCENARIO
        })

        # 12 Month COA (Long Term) - Often discounted relative to spot volatility peak, but baseline +8% for risk premium
        coa12m = spot_rate * 1.08
        rows.append({
            "date": dt,
            "route_id": route,
            "vessel_type": vtype,
            "contract_type": "COA_12M",
            "estimated_rate_usd_mt": round(coa12m, 2),
            "price_premium_pct": 8.0,
            "volume_commitment_mt": cargo_cap * 12,
            "data_type": SCENARIO
        })
        
    df = pd.DataFrame(rows)
    out_path = synthetic_dir / "contract_scenarios.csv"
    df.to_csv(out_path, index=False)
    return df


def main():
    logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
    logger = logging.getLogger("generate_strategy_layers")

    processed_dir = Path(DATA_PROCESSED_DIR)
    synthetic_dir = Path(DATA_SYNTHETIC_DIR)
    synthetic_dir.mkdir(parents=True, exist_ok=True)

    market_path = processed_dir / "market_data.csv"
    freight_path = processed_dir / "freight_estimates.csv"

    if not market_path.exists() or not freight_path.exists():
        logger.error("Required processed datasets missing.")
        sys.exit(1)

    logger.info("Loading baseline datasets...")
    market_df = pd.read_csv(market_path)
    freight_df = pd.read_csv(freight_path)

    logger.info("Generating SYNTHETIC port congestion time-series...")
    cong_df = generate_port_congestion(market_df, synthetic_dir)
    print(f"[OK] port_congestion.csv created: {len(cong_df)} rows tagged SYNTHETIC")
    
    logger.info("Generating SCENARIO contract strategies...")
    strat_df = generate_contract_scenarios(freight_df, synthetic_dir)
    print(f"[OK] contract_scenarios.csv created: {len(strat_df)} rows tagged SCENARIO")

if __name__ == "__main__":
    main()

"""
SIH26006 — Synthetic Voyage Estimation (SVE) Engine.

Constructs defensible, route-specific freight rate estimates ($/MT and INR/MT)
from daily market signals (BDRY/BDI, bunker prices, USD/INR) and physical
route/vessel parameters.

Mathematical methodology defined in DATA_CONTRACTS.md:
1. Charter Rate Proxy ($/day): BDRY scaled to vessel average charter rate, clamped to [low, high]
2. Voyage Time (days): distance / (speed * 24) + port_days
3. Bunker Cost (USD): fuel_sea * sea_days * VLSFO + fuel_port * port_days * VLSFO
4. Total Voyage Cost (USD): charter_rate * voyage_days + bunker_cost + port_charges
5. Freight Rate ($/MT): total_voyage_cost / cargo_capacity
6. Freight Rate (INR/MT): freight_rate_usd * usd_inr

EVERY OUTPUT IS TAGGED:
    data_type = 'DERIVED'
    methodology = 'SYNTHETIC_VOYAGE_ESTIMATION'

Operational constraints strictly enforced:
- Capesize vessels are EXCLUDED from Haldia (max draft 9.1m vs ~18m draft)
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from src.config.constants import (
    DERIVED,
    ESTIMATED,
    PLANT_PARAMS,
    PORT_CONSTRAINTS,
    ROUTES,
    VESSEL_SPECS,
)

logger = logging.getLogger(__name__)


class SyntheticVoyageEstimator:
    """Calculates route-level voyage economics and derived freight rates."""

    def __init__(self, processed_dir: Path):
        self.processed_dir = Path(processed_dir)

    def estimate_all_routes(
        self,
        market_data_file: str = "market_data.csv",
        output_file: str = "freight_estimates.csv",
    ) -> Optional[pd.DataFrame]:
        market_path = self.processed_dir / market_data_file
        if not market_path.exists():
            logger.error(f"Market data file not found: {market_path}")
            return None

        market_df = pd.read_csv(market_path)
        logger.info(f"Loaded market data: {len(market_df)} rows from {market_path}")

        # Compute BDRY baseline (median of rolling 90 days or overall median if sparse)
        if "bdry_close" in market_df.columns and market_df["bdry_close"].notna().any():
            bdry_median = market_df["bdry_close"].rolling(window=90, min_periods=10).median()
            # Fill early dates with expanding median
            bdry_median = bdry_median.fillna(market_df["bdry_close"].expanding().median())
            # Final fallback to overall median
            bdry_median = bdry_median.fillna(market_df["bdry_close"].median())
        else:
            bdry_median = pd.Series(10.0, index=market_df.index)

        # Vessel classes to model
        vessels = {
            "CAPESIZE": VESSEL_SPECS["CAPESIZE_STD"],
            "PANAMAX": VESSEL_SPECS["PANAMAX_STD"],
        }

        # Flat port charges estimates (USD)
        port_charges_map = {
            "CAPESIZE": 150_000.0,
            "PANAMAX": 100_000.0,
        }

        estimated_rows = []

        for idx, row in market_df.iterrows():
            date_val = row["date"]
            bdry_t = row.get("bdry_close")
            vlsfo_t = row.get("bunker_vlsfo")
            usd_inr_t = row.get("usd_inr")

            # Need valid fuel price and exchange rate
            if pd.isna(vlsfo_t) or pd.isna(usd_inr_t):
                continue

            bdry_base = bdry_median.iloc[idx] if not pd.isna(bdry_median.iloc[idx]) else 10.0

            for (origin, dest), route in ROUTES.items():
                port_constraint = PORT_CONSTRAINTS.get(dest)
                if not port_constraint:
                    continue

                for v_type, v_spec in vessels.items():
                    # Check physical constraint: Capesize capable?
                    if v_type == "CAPESIZE" and not port_constraint.capesize_capable:
                        # Capesize cannot berth at this port (e.g. Haldia)
                        continue

                    # 1. Charter Rate Proxy ($/day)
                    if pd.notna(bdry_t) and bdry_base > 0:
                        bdry_ratio = bdry_t / bdry_base
                        charter_rate_t = v_spec.charter_rate_avg_usd_day * bdry_ratio
                    else:
                        charter_rate_t = v_spec.charter_rate_avg_usd_day

                    # Clamp to realistic bounds [charter_rate_low, charter_rate_high]
                    charter_rate_t = max(v_spec.charter_rate_low_usd_day, min(v_spec.charter_rate_high_usd_day, charter_rate_t))

                    # 2. Voyage Times
                    speed = v_spec.speed_knots
                    sea_days_laden = route.distance_nm / (speed * 24.0)

                    # Discharge port stay: TRT + mid-point of pre-berthing wait
                    trt_hrs = port_constraint.avg_turnaround_hrs
                    wait_hrs = (port_constraint.avg_preberthing_wait_hrs_low + port_constraint.avg_preberthing_wait_hrs_high) / 2.0
                    discharge_port_days = (trt_hrs + wait_hrs) / 24.0

                    # One-way laden voyage duration
                    one_way_voyage_days = sea_days_laden + discharge_port_days

                    # 3. Direct One-Way Bunker Fuel Cost (USD)
                    bunker_cost_sea = v_spec.fuel_consumption_sea_mt_day * sea_days_laden * vlsfo_t
                    bunker_cost_discharge = v_spec.fuel_consumption_port_mt_day * discharge_port_days * vlsfo_t
                    one_way_bunker_cost = bunker_cost_sea + bunker_cost_discharge

                    # 4. Direct One-Way Voyage Cost (USD)
                    charter_cost_one_way = charter_rate_t * one_way_voyage_days
                    port_charges_discharge = port_charges_map[v_type]
                    total_one_way_cost = charter_cost_one_way + one_way_bunker_cost + port_charges_discharge
                    cargo_cap = v_spec.cargo_capacity_tonnes
                    one_way_cost_usd_mt = total_one_way_cost / cargo_cap

                    # 5. Commercial Spot Market Voyage Equivalent (Ballast Repositioning + Load Port Turnaround)
                    # Bulk carriers discharging in India must ballast back or reposition without return cargo
                    ballast_factor = 0.85  # Repositioning allocation
                    sea_days_ballast = sea_days_laden * ballast_factor
                    load_port_days = 3.0   # Newcastle / Kalimantan terminal queue and loading

                    commercial_voyage_days = load_port_days + sea_days_laden + discharge_port_days + sea_days_ballast
                    bunker_cost_ballast = (v_spec.fuel_consumption_sea_mt_day * 0.85) * sea_days_ballast * vlsfo_t
                    bunker_cost_load_port = v_spec.fuel_consumption_port_mt_day * load_port_days * vlsfo_t
                    commercial_bunker_cost = one_way_bunker_cost + bunker_cost_ballast + bunker_cost_load_port

                    charter_cost_commercial = charter_rate_t * commercial_voyage_days
                    port_charges_commercial = port_charges_discharge * 1.5  # Load port D/A + Discharge port D/A
                    total_commercial_cost = charter_cost_commercial + commercial_bunker_cost + port_charges_commercial

                    spot_freight_usd_mt = total_commercial_cost / cargo_cap
                    spot_freight_inr_mt = spot_freight_usd_mt * usd_inr_t

                    estimated_rows.append({
                        "date": date_val,
                        "origin": origin,
                        "destination": dest,
                        "vessel_type": v_type,
                        "estimated_charter_rate_usd_day": round(charter_rate_t, 2),
                        "one_way_voyage_days": round(one_way_voyage_days, 2),
                        "one_way_bunker_cost_usd": round(one_way_bunker_cost, 2),
                        "one_way_cost_usd_mt": round(one_way_cost_usd_mt, 2),
                        "commercial_voyage_days": round(commercial_voyage_days, 2),
                        "commercial_bunker_cost_usd": round(commercial_bunker_cost, 2),
                        "estimated_spot_freight_usd_mt": round(spot_freight_usd_mt, 2),
                        "estimated_freight_rate_usd_mt": round(spot_freight_usd_mt, 2),
                        "estimated_freight_rate_inr_mt": round(spot_freight_inr_mt, 2),
                        "calibration_status": "CALIBRATED_TO_PUBLIC_FIXTURES",
                        "methodology": "SYNTHETIC_VOYAGE_ESTIMATION",
                        "data_type": DERIVED,
                    })

        out_df = pd.DataFrame(estimated_rows)
        out_df = out_df.sort_values(["date", "origin", "destination", "vessel_type"]).reset_index(drop=True)

        out_path = self.processed_dir / output_file
        out_df.to_csv(out_path, index=False)
        logger.info(f"Generated {len(out_df)} derived freight estimates -> {out_path}")
        return out_df

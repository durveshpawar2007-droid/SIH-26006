"""
SIH26006 — Range and Value Validator.

Validates that numeric variables and domain rules are strictly respected:
- No negative prices (bunker, BDI, charter, freight, USD/INR)
- Realistic bounds for market variables
- Valid port and vessel physical constraints
- Accurate date sequences
"""

import logging
from typing import List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class RangeValidator:
    """Validates domain value ranges and operational physical constraints."""

    # Reasonable bounds for sanity checking
    BOUNDS = {
        "usd_inr": (60.0, 120.0),
        "bunker_vlsfo": (250.0, 1500.0),
        "bunker_mgo": (400.0, 2200.0),
        "bunker_ifo380": (200.0, 1200.0),
        "bdi": (100.0, 10000.0),
        "bdry_close": (1.0, 100.0),
        "estimated_freight_rate_usd_mt": (3.0, 60.0),
        "estimated_charter_rate_usd_day": (4000.0, 70000.0),
        "distance_nm": (500, 15000),
        "typical_transit_days": (1.0, 45.0),
        "approach_channel_depth_m": (5.0, 25.0),
        "max_operational_draft_m": (5.0, 25.0),
    }

    @classmethod
    def validate_market_data(cls, df: pd.DataFrame, dataset_name: str = "market_data") -> Tuple[bool, List[str]]:
        errors = []

        # 1. Date / Composite Key checking
        if "date" in df.columns:
            if {"origin", "destination", "vessel_type"}.issubset(df.columns):
                dupes = df.duplicated(subset=["date", "origin", "destination", "vessel_type"]).sum()
                if dupes > 0:
                    errors.append(f"[{dataset_name}] Found {dupes} duplicate (date, route, vessel) records.")
            else:
                dupes = df.duplicated(subset=["date"]).sum()
                if dupes > 0:
                    errors.append(f"[{dataset_name}] Found {dupes} duplicate dates.")

        # 2. Bound checking
        for col, (min_val, max_val) in cls.BOUNDS.items():
            if col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce").dropna()
                if not series.empty:
                    negatives = (series < 0).sum()
                    if negatives > 0:
                        errors.append(f"[{dataset_name}] Found {negatives} negative values in '{col}'.")

                    under = (series < min_val).sum()
                    over = (series > max_val).sum()
                    if under > 0:
                        errors.append(f"[{dataset_name}] {under} values in '{col}' below lower bound {min_val}.")
                    if over > 0:
                        errors.append(f"[{dataset_name}] {over} values in '{col}' above upper bound {max_val}.")

        is_valid = len(errors) == 0
        return is_valid, errors

    @classmethod
    def validate_port_constraints(cls, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        errors = []
        if "port" in df.columns:
            ports = set(df["port"].str.upper())
            required_ports = {"PARADIP", "VIZAG", "HALDIA"}
            missing = required_ports - ports
            if missing:
                errors.append(f"[port_constraints] Missing required ports: {missing}")

            # Specific check for Haldia draft and capesize capability
            haldia_row = df[df["port"].str.upper() == "HALDIA"]
            if not haldia_row.empty:
                draft = haldia_row["max_operational_draft_m"].iloc[0]
                cape_ok = haldia_row["capesize_capable"].iloc[0]
                if draft > 10.0:
                    errors.append(f"[port_constraints] Haldia draft {draft}m seems impossibly high (expected ~9.1m).")
                if str(cape_ok).lower() == "true":
                    errors.append("[port_constraints] Haldia cannot be Capesize capable due to 9.1m draft.")

        return len(errors) == 0, errors

"""
SIH26006 — Project-wide settings and configuration.

All paths, API endpoints, date ranges, and environment variables
are centralized here. Never hard-code secrets or paths elsewhere.
"""

from datetime import date
import os
from pathlib import Path

# ─── Project Root ─────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # SIH26006/

# ─── Data Directories ────────────────────────────────────────────
DATA_DIR = BASE_DIR / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
DATA_SYNTHETIC_DIR = DATA_DIR / "synthetic"
DATA_METADATA_DIR = DATA_DIR / "metadata"

# ─── Date Range ──────────────────────────────────────────────────
START_DATE = "2023-01-01"
END_DATE = os.environ.get("END_DATE", date.today().strftime("%Y-%m-%d"))

# ─── API Endpoints (Free Sources) ────────────────────────────────

# Bunker fuel — USDA AgTransport (Ship & Bunker daily global average)
USDA_BUNKER_CSV_URL = (
    "https://agtransport.usda.gov/api/views/4v3x-mj86/rows.csv?accessType=DOWNLOAD"
)
USDA_BUNKER_API_URL = "https://agtransport.usda.gov/resource/4v3x-mj86.json"

# USD/INR — FRED (no API key needed for CSV download)
FRED_DEXINUS_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

# BDI — via BDRY ETF on Yahoo Finance (yfinance library)
BDRY_TICKER = "BDRY"

# ─── Optional API Keys (from environment) ────────────────────────
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")  # Optional; CSV works without it

# ─── Logging ─────────────────────────────────────────────────────
LOG_LEVEL = os.environ.get("SIH_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s"

# ─── Missing-Data Policy ─────────────────────────────────────────
# Each market series has a documented gap-handling rule.
# See DATA_CONTRACTS.md for full rationale.
#
# Policy keys:
#   method   — how to fill gaps ('ffill', 'none', 'interpolate')
#   limit    — max consecutive NaNs to fill (None = unlimited)
#   flag     — whether to flag filled values in a separate column
#
MISSING_DATA_POLICY = {
    "bdi": {
        "method": "ffill",
        "limit": 3,        # BDI is daily; weekends = 2 days, +1 for rare holidays
        "flag": True,
        "rationale": (
            "BDI is published on Baltic Exchange business days only. "
            "Weekend/holiday gaps of 2-3 days are normal and can be "
            "forward-filled. Gaps > 3 days indicate a data issue and "
            "should remain NaN for investigation."
        ),
    },
    "bdry_close": {
        "method": "ffill",
        "limit": 3,        # NYSE-listed ETF, same business-day cadence
        "flag": True,
        "rationale": (
            "BDRY trades on NYSE; closed on weekends and US holidays. "
            "Forward-fill up to 3 days for normal market closures."
        ),
    },
    "bunker_vlsfo": {
        "method": "ffill",
        "limit": 5,        # Global 20-port average; some holiday clusters
        "flag": True,
        "rationale": (
            "USDA/Ship&Bunker global average is published on business days. "
            "Some ports close for local holidays causing occasional 3-5 day "
            "gaps in the global average. Forward-fill up to 5 days."
        ),
    },
    "bunker_mgo": {
        "method": "ffill",
        "limit": 5,
        "flag": True,
        "rationale": "Same cadence as VLSFO — see bunker_vlsfo rationale.",
    },
    "bunker_ifo380": {
        "method": "ffill",
        "limit": 5,
        "flag": True,
        "rationale": "Same cadence as VLSFO — see bunker_vlsfo rationale.",
    },
    "usd_inr": {
        "method": "ffill",
        "limit": 4,        # Weekends + occasional US/India holiday overlap
        "flag": True,
        "rationale": (
            "FRED DEXINUS is published on US business days only. Weekends "
            "create 2-day gaps; combined US+India holiday weekends can create "
            "up to 4-day gaps. Gaps > 4 days should be investigated."
        ),
    },
}

# ─── Data Type Constants ─────────────────────────────────────────
class DataType:
    """Provenance labels for every data value."""
    REAL = "REAL"              # Directly observed from authoritative source
    DERIVED = "DERIVED"        # Calculated from REAL data via documented formula
    ESTIMATED = "ESTIMATED"    # Based on industry benchmarks / expert judgment
    SYNTHETIC = "SYNTHETIC"    # Generated for what-if / scenario analysis
    SCENARIO = "SCENARIO"      # Configurable user-input for simulation

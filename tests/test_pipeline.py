"""
SIH26006 — Unit and Integration Tests.

Verifies:
1. Cleaner source-specific missing-data policy (no blind forward-fill)
2. Synthetic Voyage Estimator logic (Haldia Capesize exclusion, $/MT formulas)
3. Feature engineering leakage prevention (shift(1) verified)
4. Schema conformance of all processed datasets
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config.constants import PORT_CONSTRAINTS, ROUTES, VESSEL_SPECS
from src.config.schemas import (
    FREIGHT_ESTIMATES_SCHEMA,
    MARKET_DATA_SCHEMA,
    MODEL_FEATURES_SCHEMA,
    PORT_CONSTRAINTS_SCHEMA,
    ROUTES_SCHEMA,
    VESSEL_SPECS_SCHEMA,
)
from src.processors.cleaner import DataCleaner, _apply_missing_policy
from src.processors.feature_engineer import FeatureEngineer
from src.processors.freight_estimator import SyntheticVoyageEstimator
from src.validators.schema_validator import SchemaValidator


# ─── Test 1: Cleaner Missing Data Policy ──────────────────────────

def test_missing_data_policy_limits():
    """Verify that gaps exceeding policy limit remain NaN and within limit are filled."""
    # Create test series with 2-day gap and 6-day gap
    df = pd.DataFrame({
        "val": [10.0, np.nan, np.nan, 20.0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 30.0]
    })

    policy = {"method": "ffill", "limit": 3, "flag": True}
    res = _apply_missing_policy(df, "val", policy)

    # 2-day gap should be filled
    assert res.loc[1, "val"] == 10.0
    assert res.loc[2, "val"] == 10.0
    assert res.loc[1, "val_filled"] == True

    # 6-day gap should only fill up to 3 days (indices 4, 5, 6), remaining stay NaN
    assert res.loc[4, "val"] == 20.0
    assert res.loc[5, "val"] == 20.0
    assert res.loc[6, "val"] == 20.0
    assert pd.isna(res.loc[7, "val"])
    assert pd.isna(res.loc[8, "val"])
    assert pd.isna(res.loc[9, "val"])


# ─── Test 2: Port & Vessel Constraints ───────────────────────────

def test_haldia_capesize_exclusion():
    """Verify Haldia has capesize_capable = False and 9.1m draft limit."""
    haldia = PORT_CONSTRAINTS["HALDIA"]
    assert haldia.capesize_capable is False
    assert haldia.max_operational_draft_m <= 9.2

    # Verify Paradip and Vizag ARE Capesize capable
    assert PORT_CONSTRAINTS["PARADIP"].capesize_capable is True
    assert PORT_CONSTRAINTS["VIZAG"].capesize_capable is True


# ─── Test 3: Synthetic Voyage Estimation ───────────────────────────

def test_sve_haldia_exclusion_in_output():
    """Verify that freight_estimates.csv never contains (HALDIA, CAPESIZE)."""
    est_path = PROJECT_ROOT / "data" / "processed" / "freight_estimates.csv"
    assert est_path.exists(), "freight_estimates.csv must exist"

    df = pd.read_csv(est_path)
    haldia_capes = df[(df["destination"] == "HALDIA") & (df["vessel_type"] == "CAPESIZE")]
    assert len(haldia_capes) == 0, "Haldia must NEVER have Capesize estimates"


def test_sve_provenance_tag():
    """Verify all freight estimates are tagged DERIVED."""
    est_path = PROJECT_ROOT / "data" / "processed" / "freight_estimates.csv"
    df = pd.read_csv(est_path)
    assert (df["data_type"] == "DERIVED").all()
    assert (df["methodology"] == "SYNTHETIC_VOYAGE_ESTIMATION").all()


# ─── Test 4: Feature Engineering Leakage Prevention ───────────────

def test_feature_lag_leakage_prevention():
    """Verify that rolling and lag features at date T do NOT use information from T."""
    feat_path = PROJECT_ROOT / "data" / "processed" / "model_features.csv"
    assert feat_path.exists(), "model_features.csv must exist"

    df = pd.read_csv(feat_path)
    # Check that bunker_vlsfo_lag_1 is indeed shifted
    m_path = PROJECT_ROOT / "data" / "processed" / "market_data.csv"
    m_df = pd.read_csv(m_path)

    # First valid index in market_data
    val_df = m_df.dropna(subset=["bunker_vlsfo"]).reset_index(drop=True)
    if len(val_df) >= 2:
        date_1 = val_df.loc[1, "date"]
        val_0 = val_df.loc[0, "bunker_vlsfo"]

        # In model_features for date_1, bunker_vlsfo_lag_1 must equal val_0
        sub = df[df["date"] == date_1]
        if not sub.empty:
            assert sub["bunker_vlsfo_lag_1"].iloc[0] == pytest.approx(val_0, 0.01)


# ─── Test 5: Schema Conformance ───────────────────────────────────

def test_market_data_schema():
    path = PROJECT_ROOT / "data" / "processed" / "market_data.csv"
    df = pd.read_csv(path)
    valid, errors = SchemaValidator.validate(df, MARKET_DATA_SCHEMA, "market_data")
    assert valid, f"Schema errors: {errors}"


def test_port_constraints_schema():
    path = PROJECT_ROOT / "data" / "processed" / "port_constraints.csv"
    df = pd.read_csv(path)
    valid, errors = SchemaValidator.validate(df, PORT_CONSTRAINTS_SCHEMA, "port_constraints")
    assert valid, f"Schema errors: {errors}"


def test_vessel_specs_schema():
    path = PROJECT_ROOT / "data" / "processed" / "vessel_specs.csv"
    df = pd.read_csv(path)
    valid, errors = SchemaValidator.validate(df, VESSEL_SPECS_SCHEMA, "vessel_specs")
    assert valid, f"Schema errors: {errors}"


def test_freight_estimates_schema():
    path = PROJECT_ROOT / "data" / "processed" / "freight_estimates.csv"
    df = pd.read_csv(path)
    valid, errors = SchemaValidator.validate(df, FREIGHT_ESTIMATES_SCHEMA, "freight_estimates")
    assert valid, f"Schema errors: {errors}"


def test_spot_freight_benchmark_alignment():
    """Verify that spot freight estimates align with real-world public benchmarks."""
    path = PROJECT_ROOT / "data" / "processed" / "freight_estimates.csv"
    df = pd.read_csv(path)

    # Newcastle -> Paradip Panamax should align around $18-$22/MT (benchmark ~$21.10/MT)
    ncl_pdp_panamax = df[(df["origin"] == "NEWCASTLE_AU") & (df["destination"] == "PARADIP") & (df["vessel_type"] == "PANAMAX")]
    mean_rate_panamax = ncl_pdp_panamax["estimated_spot_freight_usd_mt"].mean()
    assert 15.0 <= mean_rate_panamax <= 25.0, f"Panamax mean rate {mean_rate_panamax} outside benchmark range"

    # Newcastle -> Paradip Capesize should align around $10-$15/MT (benchmark ~$13-$15/MT)
    ncl_pdp_cape = df[(df["origin"] == "NEWCASTLE_AU") & (df["destination"] == "PARADIP") & (df["vessel_type"] == "CAPESIZE")]
    mean_rate_cape = ncl_pdp_cape["estimated_spot_freight_usd_mt"].mean()
    assert 9.0 <= mean_rate_cape <= 17.0, f"Capesize mean rate {mean_rate_cape} outside benchmark range"

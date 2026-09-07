"""
SIH26006 — Feature Engineering Engine.

Constructs ML-ready datasets for rate and price forecasting without data leakage:
- Target: freight_rate_usd_mt (DERIVED from SVE)
- Market Features: BDI/BDRY, Bunker fuel, USD/INR
- Lag Features: T-1, T-7
- Rolling Window Features: 7-day mean/std, 30-day mean
- Momentum & Relative Features: 14-day momentum, bunker/BDI ratio
- Calendar Features: day_of_week, month

LEAKAGE PREVENTION RULE:
All rolling and lag features are calculated strictly using past observations
(at or before T-1 for predicting target T, or shift(1) before rolling).
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Generates features for ML forecasting engine."""

    def __init__(self, processed_dir: Path):
        self.processed_dir = Path(processed_dir)

    def generate_features(
        self,
        market_file: str = "market_data.csv",
        freight_file: str = "freight_estimates.csv",
        output_file: str = "model_features.csv",
    ) -> Optional[pd.DataFrame]:
        market_path = self.processed_dir / market_file
        freight_path = self.processed_dir / freight_file

        if not market_path.exists() or not freight_path.exists():
            logger.error("Required market or freight estimates data file missing.")
            return None

        m_df = pd.read_csv(market_path)
        f_df = pd.read_csv(freight_path)

        m_df["date"] = pd.to_datetime(m_df["date"])
        f_df["date"] = pd.to_datetime(f_df["date"])

        m_df = m_df.sort_values("date").reset_index(drop=True)

        # 1. Feature Engineering on Market Data (preventing leakage with shift)
        # Choose BDI proxy signal: if bdi column is empty, use bdry_close
        bdi_series = m_df["bdi"].combine_first(m_df["bdry_close"])

        # Lag features
        m_df["bdi_signal"] = bdi_series
        m_df["bdi_lag_1"] = bdi_series.shift(1)
        m_df["bdi_lag_7"] = bdi_series.shift(7)

        # Rolling statistics strictly on shifted past data (shift(1))
        shifted_bdi = bdi_series.shift(1)
        m_df["bdi_rolling_mean_7"] = shifted_bdi.rolling(window=7, min_periods=3).mean()
        m_df["bdi_rolling_std_7"] = shifted_bdi.rolling(window=7, min_periods=3).std()
        m_df["bdi_rolling_mean_30"] = shifted_bdi.rolling(window=30, min_periods=7).mean()

        # 14-day momentum: (P_{t-1} - P_{t-15}) / P_{t-15} * 100
        m_df["bdi_momentum_14d"] = (
            (shifted_bdi - bdi_series.shift(15)) / bdi_series.shift(15).replace(0, np.nan)
        ) * 100.0

        # Bunker features
        bunker_s = m_df["bunker_vlsfo"]
        m_df["bunker_vlsfo_lag_1"] = bunker_s.shift(1)
        m_df["bunker_change_pct_7d"] = (
            (bunker_s.shift(1) - bunker_s.shift(8)) / bunker_s.shift(8).replace(0, np.nan)
        ) * 100.0

        # Forex features
        fx_s = m_df["usd_inr"]
        m_df["usd_inr_lag_1"] = fx_s.shift(1)
        m_df["usd_inr_change_pct_7d"] = (
            (fx_s.shift(1) - fx_s.shift(8)) / fx_s.shift(8).replace(0, np.nan)
        ) * 100.0

        # Ratio feature: bunker / BDI
        m_df["bunker_bdi_ratio"] = bunker_s.shift(1) / shifted_bdi.replace(0, np.nan)

        # 2. Merge with Route-Level Freight Targets
        # Prepare market features subset
        market_feats = m_df[[
            "date",
            "bdi",
            "bdi_lag_1",
            "bdi_lag_7",
            "bdi_rolling_mean_7",
            "bdi_rolling_std_7",
            "bdi_rolling_mean_30",
            "bunker_vlsfo",
            "bunker_vlsfo_lag_1",
            "bunker_change_pct_7d",
            "usd_inr",
            "usd_inr_lag_1",
            "usd_inr_change_pct_7d",
            "bdi_momentum_14d",
            "bunker_bdi_ratio",
        ]].copy()

        merged_features = pd.merge(
            f_df[["date", "origin", "destination", "vessel_type", "estimated_freight_rate_usd_mt"]],
            market_feats,
            on="date",
            how="inner",
        )

        merged_features = merged_features.rename(
            columns={"estimated_freight_rate_usd_mt": "freight_rate_usd_mt"}
        )

        # Calendar features
        merged_features["day_of_week"] = merged_features["date"].dt.dayofweek
        merged_features["month"] = merged_features["date"].dt.month

        # Format date back to string YYYY-MM-DD
        merged_features["date"] = merged_features["date"].dt.strftime("%Y-%m-%d")

        # Sort and clean
        merged_features = merged_features.sort_values(
            ["date", "origin", "destination", "vessel_type"]
        ).reset_index(drop=True)

        out_path = self.processed_dir / output_file
        merged_features.to_csv(out_path, index=False)
        logger.info(f"Generated ML features dataset: {len(merged_features)} rows -> {out_path}")
        return merged_features

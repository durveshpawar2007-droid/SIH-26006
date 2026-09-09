"""
SIH26006 — Machine Learning Feature Generator.
"""
import logging
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class MLFeatureEngineer:
    def __init__(self, processed_dir: Path):
        self.processed_dir = Path(processed_dir)

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        df["day_of_week"] = df["date"].dt.dayofweek
        df["month"] = df["date"].dt.month

        if "bdi" in df.columns:
            df["bdi_lag_1"] = df["bdi"].shift(1)
            df["bdi_lag_7"] = df["bdi"].shift(7)
            df["bdi_rolling_mean_7"] = df["bdi"].rolling(window=7, min_periods=1).mean()
            df["bdi_rolling_std_7"] = df["bdi"].rolling(window=7, min_periods=1).std()
            df["bdi_rolling_mean_30"] = df["bdi"].rolling(window=30, min_periods=1).mean()
            df["bdi_momentum_14d"] = df["bdi"] / df["bdi"].shift(14)

        if "bunker_vlsfo" in df.columns:
            df["bunker_vlsfo_lag_1"] = df["bunker_vlsfo"].shift(1)
            df["bunker_change_pct_7d"] = df["bunker_vlsfo"].pct_change(periods=7)

        if "usd_inr" in df.columns:
            df["usd_inr_lag_1"] = df["usd_inr"].shift(1)
            df["usd_inr_change_pct_7d"] = df["usd_inr"].pct_change(periods=7)

        if "bunker_vlsfo" in df.columns and "bdi" in df.columns:
            df["bunker_bdi_ratio"] = df["bunker_vlsfo"] / (df["bdi"] + 1e-5)

        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        return df

    def create_dataset(
        self,
        freight_file: str = "freight_estimates.csv",
        market_file: str = "market_data.csv",
        output_file: str = "model_features.csv",
    ) -> Optional[pd.DataFrame]:
        freight_path = self.processed_dir / freight_file
        market_path = self.processed_dir / market_file

        if not freight_path.exists() or not market_path.exists():
            return None

        freight_df = pd.read_csv(freight_path)
        market_df = pd.read_csv(market_path)

        merged = pd.merge(freight_df, market_df, on="date", how="left")

        groups = []
        for _, group in merged.groupby(["origin", "destination", "vessel_type", "vessel_variant"]):
            g_features = self._engineer_features(group.copy())
            groups.append(g_features)

        if not groups:
            return None

        features_df = pd.concat(groups, ignore_index=True)
        features_df = features_df.sort_values(["date", "origin", "destination", "vessel_type", "vessel_variant"])
        
        features_df["freight_rate_usd_mt"] = features_df["estimated_freight_rate_usd_mt"]

        keep_cols = [
            "date", "origin", "destination", "vessel_type", "vessel_variant",
            "freight_rate_usd_mt", "bdi", "bdi_lag_1", "bdi_lag_7",
            "bdi_rolling_mean_7", "bdi_rolling_std_7", "bdi_rolling_mean_30",
            "bunker_vlsfo", "bunker_vlsfo_lag_1", "bunker_change_pct_7d",
            "usd_inr", "usd_inr_lag_1", "usd_inr_change_pct_7d",
            "day_of_week", "month", "bdi_momentum_14d", "bunker_bdi_ratio"
        ]

        out_cols = [c for c in keep_cols if c in features_df.columns]
        features_df = features_df[out_cols]
        
        out_path = self.processed_dir / output_file
        features_df.to_csv(out_path, index=False)
        return features_df

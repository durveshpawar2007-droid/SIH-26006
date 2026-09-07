"""
SIH26006 — Market Data Merger.

Merges cleaned BDI, bunker fuel, and USD/INR datasets on date into
data/processed/market_data.csv.

Follows the schema defined in src/config/schemas.py:
- date: YYYY-MM-DD
- bdi: Baltic Dry Index (NaN if manual file not supplied, explanatory feature)
- bdry_close: Breakwave Dry Bulk Shipping ETF close price (USD)
- bunker_vlsfo: VLSFO 0.5% price (USD/MT)
- bunker_mgo: Marine Gas Oil price (USD/MT)
- bunker_ifo380: IFO 380 CST price (USD/MT)
- usd_inr: USD/INR exchange rate
- source_bdi, source_bunker, source_fx
- data_type: REAL
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class MarketDataMerger:
    """Merges cleaned individual market datasets into unified market_data.csv."""

    def __init__(self, processed_dir: Path):
        self.processed_dir = Path(processed_dir)

    def merge(
        self,
        bdi_file: str = "bdi_cleaned.csv",
        bunker_file: str = "bunker_prices_cleaned.csv",
        forex_file: str = "usd_inr_cleaned.csv",
        output_file: str = "market_data.csv",
    ) -> Optional[pd.DataFrame]:
        """
        Merge cleaned market files on 'date' with outer join, then filter
        and sort.
        """
        bdi_path = self.processed_dir / bdi_file
        bunker_path = self.processed_dir / bunker_file
        forex_path = self.processed_dir / forex_file

        dfs = {}
        if bdi_path.exists():
            dfs["bdi"] = pd.read_csv(bdi_path)
            logger.info(f"Loaded BDI: {len(dfs['bdi'])} rows")
        else:
            logger.warning(f"BDI cleaned file not found: {bdi_path}")

        if bunker_path.exists():
            dfs["bunker"] = pd.read_csv(bunker_path)
            logger.info(f"Loaded Bunker: {len(dfs['bunker'])} rows")
        else:
            logger.warning(f"Bunker cleaned file not found: {bunker_path}")

        if forex_path.exists():
            dfs["forex"] = pd.read_csv(forex_path)
            logger.info(f"Loaded Forex: {len(dfs['forex'])} rows")
        else:
            logger.warning(f"Forex cleaned file not found: {forex_path}")

        if not dfs:
            logger.error("No cleaned data files available to merge.")
            return None

        # Start with the date spine of all unique dates across available datasets
        all_dates = set()
        for df in dfs.values():
            if "date" in df.columns:
                all_dates.update(df["date"].dropna().unique())

        merged = pd.DataFrame({"date": sorted(list(all_dates))})

        # Merge BDI
        if "bdi" in dfs:
            bdi_cols = ["date"]
            for col in ["bdi", "bdry_close", "source_bdi"]:
                if col in dfs["bdi"].columns:
                    bdi_cols.append(col)
            merged = pd.merge(merged, dfs["bdi"][bdi_cols], on="date", how="left")

        # Merge Bunker
        if "bunker" in dfs:
            bunker_cols = ["date"]
            for col in ["bunker_vlsfo", "bunker_mgo", "bunker_ifo380", "source"]:
                if col in dfs["bunker"].columns:
                    bunker_cols.append(col)
            bunker_sub = dfs["bunker"][bunker_cols].rename(columns={"source": "source_bunker"})
            merged = pd.merge(merged, bunker_sub, on="date", how="left")

        # Merge Forex
        if "forex" in dfs:
            fx_cols = ["date"]
            for col in ["usd_inr", "source"]:
                if col in dfs["forex"].columns:
                    fx_cols.append(col)
            fx_sub = dfs["forex"][fx_cols].rename(columns={"source": "source_fx"})
            merged = pd.merge(merged, fx_sub, on="date", how="left")

        # Standardize source tags
        if "source_bdi" not in merged.columns:
            merged["source_bdi"] = "None"
        if "source_bunker" not in merged.columns:
            merged["source_bunker"] = "None"
        if "source_fx" not in merged.columns:
            merged["source_fx"] = "None"

        # Overall data type provenance
        merged["data_type"] = "REAL"

        # Sort chronologically
        merged = merged.sort_values("date").reset_index(drop=True)

        # Drop dates where ALL key price indicators are NaN
        price_cols = [c for c in ["bdi", "bdry_close", "bunker_vlsfo", "usd_inr"] if c in merged.columns]
        valid_mask = merged[price_cols].notna().any(axis=1)
        dropped = len(merged) - valid_mask.sum()
        if dropped > 0:
            logger.info(f"Dropped {dropped} dates with no price observations")
            merged = merged[valid_mask].reset_index(drop=True)

        # Save output
        out_path = self.processed_dir / output_file
        merged.to_csv(out_path, index=False)
        logger.info(f"Saved merged market data: {len(merged)} rows -> {out_path}")
        return merged

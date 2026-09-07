"""
Data Cleaning Module for SIH26006 Pipeline.

Handles:
- Date parsing and normalization to YYYY-MM-DD
- Deduplication (keep first occurrence)
- Source-specific missing-data handling (NOT blind forward-fill)
- Unit standardization
- Column renaming and type casting
- Provenance tagging (REAL, DERIVED, ESTIMATED, SCENARIO)

MISSING-DATA POLICY (Correction #5):
  Each market series has a documented fill policy defined in
  src/config/settings.py MISSING_DATA_POLICY. Gaps within the
  fill limit are forward-filled AND flagged with a {col}_filled
  boolean column. Gaps exceeding the limit remain NaN.
  No backward-fill. No interpolation.

Raw data is NEVER modified. All cleaning produces new files in data/processed/.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def _apply_missing_policy(
    df: pd.DataFrame,
    column: str,
    policy: dict,
) -> pd.DataFrame:
    """
    Apply source-specific missing-data policy to a single column.

    Args:
        df: DataFrame with the column to process.
        column: Name of the column.
        policy: Dict with keys: method, limit, flag, rationale.

    Returns:
        DataFrame with gap-filled column and optional _filled flag column.
    """
    if column not in df.columns:
        return df

    method = policy.get("method", "none")
    limit = policy.get("limit", None)
    should_flag = policy.get("flag", True)

    missing_before = df[column].isna().sum()

    if method == "ffill":
        # Track which values were filled
        was_na = df[column].isna()
        df[column] = df[column].ffill(limit=limit)
        filled_mask = was_na & df[column].notna()

        if should_flag:
            df[f"{column}_filled"] = filled_mask

        filled_count = filled_mask.sum()
        remaining_na = df[column].isna().sum()

        if filled_count > 0:
            logger.info(
                f"  {column}: forward-filled {filled_count} gaps "
                f"(limit={limit}), {remaining_na} NaN remaining"
            )
        if remaining_na > 0:
            logger.warning(
                f"  {column}: {remaining_na} gaps EXCEED fill limit "
                f"({limit} days) — left as NaN for investigation"
            )
    elif method == "none":
        if should_flag:
            df[f"{column}_filled"] = False
        logger.info(f"  {column}: no-fill policy — {missing_before} NaN preserved")
    else:
        logger.warning(f"  {column}: unknown fill method '{method}', skipping")

    return df


class DataCleaner:
    """Cleans and normalizes raw market data files using source-specific policies."""

    def __init__(self, raw_dir: Path, processed_dir: Path, missing_data_policy: dict):
        """
        Args:
            raw_dir: Path to raw data directory.
            processed_dir: Path to processed output directory.
            missing_data_policy: Dict from settings.MISSING_DATA_POLICY.
        """
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.policy = missing_data_policy
        self._cleaning_log: list[dict] = []

    def clean_bunker_data(self, filename: str = "bunker_prices_raw.csv") -> Optional[pd.DataFrame]:
        """
        Clean raw bunker fuel price data from USDA AgTransport.

        Returns:
            Cleaned DataFrame or None if source file missing.
        """
        filepath = self.raw_dir / filename
        if not filepath.exists():
            logger.warning(f"Bunker raw file not found: {filepath}")
            return None

        logger.info(f"Cleaning bunker data from {filepath}")
        df = pd.read_csv(filepath)
        initial_rows = len(df)

        # Parse dates
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        elif "day" in df.columns:
            df["date"] = pd.to_datetime(df["day"], errors="coerce")
        else:
            logger.error("No date column found in bunker data")
            return None

        # Drop rows with invalid dates
        invalid_dates = df["date"].isna().sum()
        if invalid_dates > 0:
            logger.warning(f"Dropping {invalid_dates} rows with invalid dates")
            df = df.dropna(subset=["date"])

        # Standardize column names (note: USDA API has typo 'intermdiate')
        column_map = {
            "vlsfo_fuel_oil_imo_2020_grade_0_5": "bunker_vlsfo",
            "marine_gas_oil": "bunker_mgo",
            "intermdiate_fuel_oil_380cst": "bunker_ifo380",
            "intermdiate_fuel_oil_180cst": "bunker_ifo180",
        }
        df = df.rename(columns=column_map)

        price_cols = ["bunker_vlsfo", "bunker_mgo", "bunker_ifo380", "bunker_ifo180"]
        available_price_cols = [c for c in price_cols if c in df.columns]

        # Convert to numeric
        for col in available_price_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Remove duplicates by date (keep first)
        dupes = df.duplicated(subset=["date"], keep="first").sum()
        if dupes > 0:
            logger.info(f"Removing {dupes} duplicate dates")
        df = df.drop_duplicates(subset=["date"], keep="first")

        # Sort by date
        df = df.sort_values("date").reset_index(drop=True)

        # Validate: no negative prices
        for col in available_price_cols:
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                logger.warning(f"Found {neg_count} negative values in {col}, setting to NaN")
                df.loc[df[col] < 0, col] = pd.NA

        # Validate: no extreme prices (> $2000/MT is suspicious)
        for col in available_price_cols:
            extreme = (df[col] > 2000).sum()
            if extreme > 0:
                logger.warning(f"Found {extreme} extreme values (>$2000/MT) in {col}")

        # Apply source-specific missing-data policy (NOT blind forward-fill)
        logger.info("Applying source-specific missing-data policies:")
        for col in available_price_cols:
            policy = self.policy.get(col, {"method": "none", "limit": None, "flag": True})
            df = _apply_missing_policy(df, col, policy)

        # Add metadata columns
        df["currency"] = "USD"
        df["unit"] = "USD/MT"
        df["source"] = "USDA_AgTransport_ShipAndBunker"
        df["data_type"] = "REAL"

        # Format date
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

        # Select final columns (include _filled flag columns)
        output_cols = ["date"] + available_price_cols
        flag_cols = [f"{c}_filled" for c in available_price_cols if f"{c}_filled" in df.columns]
        output_cols += flag_cols + ["currency", "unit", "source", "data_type"]
        df = df[[c for c in output_cols if c in df.columns]]

        self._log_cleaning("bunker_prices", initial_rows=initial_rows, final_rows=len(df),
                           duplicates_removed=dupes, invalid_dates=invalid_dates)
        logger.info(f"Bunker data cleaned: {initial_rows} → {len(df)} rows")
        return df

    def clean_forex_data(self, filename: str = "usd_inr_raw.csv") -> Optional[pd.DataFrame]:
        """
        Clean raw USD/INR exchange rate data from FRED.

        Returns:
            Cleaned DataFrame or None if source file missing.
        """
        filepath = self.raw_dir / filename
        if not filepath.exists():
            logger.warning(f"Forex raw file not found: {filepath}")
            return None

        logger.info(f"Cleaning forex data from {filepath}")
        df = pd.read_csv(filepath)
        initial_rows = len(df)

        # Parse dates — FRED uses 'DATE' column
        date_col = "DATE" if "DATE" in df.columns else "date"
        df["date"] = pd.to_datetime(df[date_col], errors="coerce")

        invalid_dates = df["date"].isna().sum()
        if invalid_dates > 0:
            logger.warning(f"Dropping {invalid_dates} rows with invalid dates")
            df = df.dropna(subset=["date"])

        # Parse values — FRED uses 'DEXINUS' and '.' for missing
        value_col = "DEXINUS" if "DEXINUS" in df.columns else "usd_inr"
        df["usd_inr"] = pd.to_numeric(df[value_col].replace(".", pd.NA), errors="coerce")

        # Remove duplicates
        dupes = df.duplicated(subset=["date"], keep="first").sum()
        if dupes > 0:
            logger.info(f"Removing {dupes} duplicate dates")
        df = df.drop_duplicates(subset=["date"], keep="first")

        # Sort
        df = df.sort_values("date").reset_index(drop=True)

        # Validate range (reasonable INR/USD between 60 and 120)
        out_of_range = ((df["usd_inr"] < 60) | (df["usd_inr"] > 120)).sum()
        if out_of_range > 0:
            logger.warning(f"Found {out_of_range} USD/INR values outside expected range (60-120)")

        # Apply source-specific policy
        logger.info("Applying source-specific missing-data policy:")
        policy = self.policy.get("usd_inr", {"method": "ffill", "limit": 4, "flag": True})
        df = _apply_missing_policy(df, "usd_inr", policy)

        # Metadata
        df["source"] = "FRED_DEXINUS"
        df["data_type"] = "REAL"
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

        output_cols = ["date", "usd_inr"]
        if "usd_inr_filled" in df.columns:
            output_cols.append("usd_inr_filled")
        output_cols += ["source", "data_type"]
        df = df[output_cols]

        self._log_cleaning("usd_inr", initial_rows=initial_rows, final_rows=len(df),
                           duplicates_removed=dupes, invalid_dates=invalid_dates)
        logger.info(f"Forex data cleaned: {initial_rows} → {len(df)} rows")
        return df

    def clean_bdi_data(self, filename: str = "bdi_raw.csv") -> Optional[pd.DataFrame]:
        """
        Clean raw BDI / BDRY data.

        Returns:
            Cleaned DataFrame or None if source file missing.
        """
        filepath = self.raw_dir / filename
        if not filepath.exists():
            logger.warning(f"BDI raw file not found: {filepath}")
            return None

        logger.info(f"Cleaning BDI data from {filepath}")
        df = pd.read_csv(filepath)
        initial_rows = len(df)

        # Parse dates
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        invalid_dates = df["date"].isna().sum()
        if invalid_dates > 0:
            df = df.dropna(subset=["date"])

        # Ensure numeric columns
        for col in ["bdi", "bdry_close", "bdry_open", "bdry_high", "bdry_low", "bdry_volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Remove duplicates
        dupes = df.duplicated(subset=["date"], keep="first").sum()
        if dupes > 0:
            logger.info(f"Removing {dupes} duplicate dates")
        df = df.drop_duplicates(subset=["date"], keep="first")

        # Sort
        df = df.sort_values("date").reset_index(drop=True)

        # Validate BDI range (typical: 300–6000, extreme: 100–10000)
        if "bdi" in df.columns:
            bdi_valid = df["bdi"].notna()
            out_of_range = ((df.loc[bdi_valid, "bdi"] < 100) | (df.loc[bdi_valid, "bdi"] > 10000)).sum()
            if out_of_range > 0:
                logger.warning(f"Found {out_of_range} BDI values outside typical range (100-10000)")

        # Apply source-specific policies
        logger.info("Applying source-specific missing-data policies:")
        for col in ["bdi", "bdry_close"]:
            if col in df.columns:
                policy = self.policy.get(col, {"method": "ffill", "limit": 3, "flag": True})
                df = _apply_missing_policy(df, col, policy)

        # Metadata
        if "data_type" not in df.columns:
            df["data_type"] = "REAL"
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

        # Select output columns
        output_cols = ["date"]
        for col in ["bdi", "bdry_close", "bdi_filled", "bdry_close_filled",
                     "source_bdi", "source_bdry", "data_type"]:
            if col in df.columns:
                output_cols.append(col)
        df = df[output_cols]

        self._log_cleaning("bdi", initial_rows=initial_rows, final_rows=len(df),
                           duplicates_removed=dupes, invalid_dates=invalid_dates)
        logger.info(f"BDI data cleaned: {initial_rows} → {len(df)} rows")
        return df

    def _log_cleaning(self, dataset: str, **kwargs) -> None:
        """Record cleaning operations for quality reporting."""
        entry = {"dataset": dataset, **kwargs}
        self._cleaning_log.append(entry)

    @property
    def cleaning_summary(self) -> list[dict]:
        """Return all cleaning operations performed."""
        return self._cleaning_log.copy()

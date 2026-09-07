"""
SIH26006 — Data Cleaning Script.

Reads raw data files from data/raw/, applies source-specific cleaning
and missing-data policies, outputs to data/processed/.

Usage:
    python scripts/clean_data.py
    python scripts/clean_data.py --skip-bunker --skip-forex
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import (
    DATA_RAW_DIR, DATA_PROCESSED_DIR,
    MISSING_DATA_POLICY, LOG_FORMAT, LOG_LEVEL,
)
from src.processors.cleaner import DataCleaner


def main():
    parser = argparse.ArgumentParser(description="Clean raw data files")
    parser.add_argument("--skip-bunker", action="store_true")
    parser.add_argument("--skip-forex", action="store_true")
    parser.add_argument("--skip-bdi", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
    logger = logging.getLogger("clean_data")

    raw_dir = Path(DATA_RAW_DIR)
    processed_dir = Path(DATA_PROCESSED_DIR)

    if not raw_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        logger.error("Run 'python scripts/collect_data.py' first.")
        sys.exit(1)

    cleaner = DataCleaner(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        missing_data_policy=MISSING_DATA_POLICY,
    )

    results = {}

    if not args.skip_bunker:
        logger.info("-" * 50)
        logger.info("Cleaning bunker fuel data...")
        df = cleaner.clean_bunker_data()
        if df is not None and not df.empty:
            outpath = processed_dir / "bunker_prices_cleaned.csv"
            df.to_csv(outpath, index=False)
            results["bunker"] = {"status": "OK", "rows": len(df), "path": str(outpath)}
            logger.info(f"Saved: {outpath} ({len(df)} rows)")
        else:
            results["bunker"] = {"status": "FAILED", "rows": 0}
            logger.warning("Bunker cleaning failed or produced empty output")

    if not args.skip_forex:
        logger.info("-" * 50)
        logger.info("Cleaning forex data...")
        df = cleaner.clean_forex_data()
        if df is not None and not df.empty:
            outpath = processed_dir / "usd_inr_cleaned.csv"
            df.to_csv(outpath, index=False)
            results["forex"] = {"status": "OK", "rows": len(df), "path": str(outpath)}
            logger.info(f"Saved: {outpath} ({len(df)} rows)")
        else:
            results["forex"] = {"status": "FAILED", "rows": 0}
            logger.warning("Forex cleaning failed or produced empty output")

    if not args.skip_bdi:
        logger.info("-" * 50)
        logger.info("Cleaning BDI data...")
        df = cleaner.clean_bdi_data()
        if df is not None and not df.empty:
            outpath = processed_dir / "bdi_cleaned.csv"
            df.to_csv(outpath, index=False)
            results["bdi"] = {"status": "OK", "rows": len(df), "path": str(outpath)}
            logger.info(f"Saved: {outpath} ({len(df)} rows)")
        else:
            results["bdi"] = {"status": "FAILED", "rows": 0}
            logger.warning("BDI cleaning failed or produced empty output")

    # Summary
    logger.info("-" * 50)
    logger.info("=== Cleaning Summary ===")
    for name, info in results.items():
        logger.info(f"  {name.ljust(10)}: {info['status']} ({info['rows']} rows)")

    # Log cleaning operations
    for entry in cleaner.cleaning_summary:
        logger.debug(f"  Cleaning log: {entry}")

    if any(r["status"] == "FAILED" for r in results.values()):
        logger.warning("Some cleaning steps failed. Check raw data availability.")
        sys.exit(1)
    else:
        logger.info("All cleaning steps completed successfully.")


if __name__ == "__main__":
    main()

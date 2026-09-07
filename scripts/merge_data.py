"""
SIH26006 — Market Data Merge Script.

Orchestrates merging cleaned market files into data/processed/market_data.csv.

Usage:
    python scripts/merge_data.py
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import DATA_PROCESSED_DIR, LOG_FORMAT, LOG_LEVEL
from src.processors.merger import MarketDataMerger


def main():
    logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
    logger = logging.getLogger("merge_data")

    processed_dir = Path(DATA_PROCESSED_DIR)
    if not processed_dir.exists():
        logger.error(f"Processed directory does not exist: {processed_dir}")
        sys.exit(1)

    logger.info("Merging cleaned market data...")
    merger = MarketDataMerger(processed_dir=processed_dir)
    df = merger.merge()

    if df is not None and not df.empty:
        logger.info(f"Successfully merged market data ({len(df)} rows).")
        print(f"[OK] Merged market data created: {len(df)} rows")
        sys.exit(0)
    else:
        logger.error("Failed to merge market data.")
        sys.exit(1)


if __name__ == "__main__":
    main()

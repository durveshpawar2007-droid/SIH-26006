"""
SIH26006 — Freight Estimates Generator Script.

Executes the Synthetic Voyage Estimation model to generate
data/processed/freight_estimates.csv.

Usage:
    python scripts/generate_freight_estimates.py
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import DATA_PROCESSED_DIR, LOG_FORMAT, LOG_LEVEL
from src.processors.freight_estimator import SyntheticVoyageEstimator


def main():
    logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
    logger = logging.getLogger("generate_freight_estimates")

    processed_dir = Path(DATA_PROCESSED_DIR)
    estimator = SyntheticVoyageEstimator(processed_dir=processed_dir)

    logger.info("Executing Synthetic Voyage Estimation model...")
    df = estimator.estimate_all_routes()

    if df is not None and not df.empty:
        logger.info(f"Successfully generated freight estimates ({len(df)} rows).")
        print(f"[OK] freight_estimates.csv created: {len(df)} rows across routes/vessels")
        sys.exit(0)
    else:
        logger.error("Failed to generate freight estimates.")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
SIH26006 — Feature Generation Script.

Executes FeatureEngineer to produce data/processed/model_features.csv for ML handoff.

Usage:
    python scripts/generate_features.py
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import DATA_PROCESSED_DIR, LOG_FORMAT, LOG_LEVEL
from src.processors.feature_engineer import FeatureEngineer


def main():
    logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
    logger = logging.getLogger("generate_features")

    processed_dir = Path(DATA_PROCESSED_DIR)
    engineer = FeatureEngineer(processed_dir=processed_dir)

    logger.info("Generating model features dataset...")
    df = engineer.generate_features()

    if df is not None and not df.empty:
        logger.info(f"Successfully generated model features ({len(df)} rows).")
        print(f"[OK] model_features.csv created: {len(df)} rows ready for ML modeling")
        sys.exit(0)
    else:
        logger.error("Failed to generate model features.")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
SIH26006 — End-to-End Data Engineering Pipeline Orchestrator.

Orchestrates the full data pipeline:
1. Generate static reference data (ports, vessels, routes, plant parameters)
2. Collect raw market data (USDA Bunker, FRED USD/INR, Yahoo BDRY/BDI)
3. Clean raw datasets with source-specific missing-data policies
4. Merge cleaned market datasets on date -> market_data.csv
5. Run Synthetic Voyage Estimation -> freight_estimates.csv
6. Generate ML forecasting features -> model_features.csv
7. Generate what-if scenario layer -> scenario_data.csv
8. Validate all datasets and generate metadata/data_quality_report.json

Usage:
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --skip-collect  (use existing raw data)
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.settings import (
    DATA_METADATA_DIR,
    DATA_PROCESSED_DIR,
    DATA_RAW_DIR,
    DATA_SYNTHETIC_DIR,
    END_DATE,
    LOG_FORMAT,
    LOG_LEVEL,
    START_DATE,
)


def run_stage(command: list[str], stage_name: str, logger: logging.Logger) -> bool:
    logger.info("=" * 60)
    logger.info(f"STAGE: {stage_name}")
    logger.info(f"Command: {' '.join(command)}")
    logger.info("=" * 60)

    result = subprocess.run(command)
    if result.returncode != 0:
        logger.error(f"Stage '{stage_name}' FAILED with exit code {result.returncode}")
        return False
    logger.info(f"Stage '{stage_name}' COMPLETED successfully.\n")
    return True


def main():
    parser = argparse.ArgumentParser(description="Run end-to-end SIH26006 data pipeline")
    parser.add_argument("--skip-collect", action="store_true", help="Skip data collection, use existing data/raw/")
    parser.add_argument("--start-date", default=START_DATE, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=END_DATE, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
    logger = logging.getLogger("run_pipeline")

    # Ensure directories exist
    for p in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_SYNTHETIC_DIR, DATA_METADATA_DIR]:
        Path(p).mkdir(parents=True, exist_ok=True)

    stages = []

    # 1. Static Reference Data
    stages.append(([sys.executable, "scripts/generate_static_data.py"], "Generate Static Data"))

    # 2. Collect Data
    if not args.skip_collect:
        collect_cmd = [
            sys.executable,
            "scripts/collect_data.py",
            "--start-date",
            args.start_date,
            "--end-date",
            args.end_date,
        ]
        stages.append((collect_cmd, "Collect Raw Market Data"))

    # 3. Clean Data
    stages.append(([sys.executable, "scripts/clean_data.py"], "Clean Market Data"))

    # 4. Merge Data
    stages.append(([sys.executable, "scripts/merge_data.py"], "Merge Market Datasets"))

    # 5. Synthetic Voyage Estimation (Freight Rates)
    stages.append(([sys.executable, "scripts/generate_freight_estimates.py"], "Synthetic Voyage Estimation"))

    # 6. Feature Engineering
    stages.append(([sys.executable, "scripts/generate_features.py"], "Generate ML Features"))

    # 7. Scenario Generation
    stages.append(([sys.executable, "scripts/generate_scenarios.py"], "Generate Synthetic Scenarios"))

    # 8. Validation and Quality Reporting
    stages.append(([sys.executable, "scripts/validate_data.py"], "Validate Datasets & Report Quality"))

    # Execute stages in strict sequential pipeline order
    for cmd, name in stages:
        success = run_stage(cmd, name, logger)
        if not success:
            logger.critical(f"Pipeline ABORTED due to failure in stage: {name}")
            sys.exit(1)

    logger.info("=" * 60)
    logger.info("PIPELINE EXECUTION FINISHED SUCCESSFULLY!")
    logger.info(f"Processed datasets: {DATA_PROCESSED_DIR}")
    logger.info(f"Synthetic datasets: {DATA_SYNTHETIC_DIR}")
    logger.info(f"Quality & metadata: {DATA_METADATA_DIR}")
    logger.info("=" * 60)
    print("\n[SUCCESS] Entire SIH26006 Data Pipeline executed cleanly.")


if __name__ == "__main__":
    main()

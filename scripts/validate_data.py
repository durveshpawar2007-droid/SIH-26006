"""
SIH26006 — Data Validation Script.

Executes schema checks, range checks, and generates data/metadata/data_quality_report.json.

Usage:
    python scripts/validate_data.py
"""

import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.schemas import (
    FREIGHT_ESTIMATES_SCHEMA,
    MARKET_DATA_SCHEMA,
    MODEL_FEATURES_SCHEMA,
    PLANT_PARAMS_SCHEMA,
    PORT_CONSTRAINTS_SCHEMA,
    ROUTES_SCHEMA,
    VESSEL_SPECS_SCHEMA,
)
from src.config.settings import DATA_METADATA_DIR, DATA_PROCESSED_DIR, LOG_FORMAT, LOG_LEVEL
from src.validators.quality_reporter import QualityReporter
from src.validators.range_validator import RangeValidator
from src.validators.schema_validator import SchemaValidator


def main():
    logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
    logger = logging.getLogger("validate_data")

    processed_dir = Path(DATA_PROCESSED_DIR)
    metadata_dir = Path(DATA_METADATA_DIR)

    reporter = QualityReporter(metadata_dir=metadata_dir)
    full_report = {}
    overall_errors = 0

    datasets_to_check = [
        ("market_data.csv", MARKET_DATA_SCHEMA, "market_data"),
        ("port_constraints.csv", PORT_CONSTRAINTS_SCHEMA, "port_constraints"),
        ("vessel_specs.csv", VESSEL_SPECS_SCHEMA, "vessel_specs"),
        ("routes.csv", ROUTES_SCHEMA, "routes"),
        ("plant_params.csv", PLANT_PARAMS_SCHEMA, "plant_params"),
        ("freight_estimates.csv", FREIGHT_ESTIMATES_SCHEMA, "freight_estimates"),
        ("model_features.csv", MODEL_FEATURES_SCHEMA, "model_features"),
    ]

    for filename, schema, name in datasets_to_check:
        filepath = processed_dir / filename
        if not filepath.exists():
            logger.debug(f"Skipping {filename} (not generated yet)")
            continue

        logger.info(f"Validating {filename}...")
        df = pd.read_csv(filepath)
        dataset_errors = []

        # 1. Schema Validation
        valid_schema, schema_errs = SchemaValidator.validate(df, schema, name)
        dataset_errors.extend(schema_errs)

        # 2. Domain / Range Validation
        if name in ["market_data", "freight_estimates", "model_features"]:
            valid_range, range_errs = RangeValidator.validate_market_data(df, name)
            dataset_errors.extend(range_errs)
        elif name == "port_constraints":
            valid_port, port_errs = RangeValidator.validate_port_constraints(df)
            dataset_errors.extend(port_errs)

        overall_errors += len(dataset_errors)

        # 3. Report Analysis
        analysis = reporter.analyze_dataset(df, name, errors=dataset_errors)
        full_report[name] = analysis

    # Save comprehensive report
    report_path = reporter.save_report(full_report)
    print(f"[OK] Quality report generated: {report_path}")

    if overall_errors > 0:
        logger.warning(f"Validation completed with {overall_errors} warning(s)/error(s).")
    else:
        logger.info("All validated datasets PASSED with zero errors.")


if __name__ == "__main__":
    main()

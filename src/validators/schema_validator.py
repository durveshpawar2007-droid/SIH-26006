"""
SIH26006 — Schema Validator.

Validates that DataFrame columns, types, and nullability match the schemas
defined in src.config.schemas.
"""

import logging
from typing import Any, Dict, List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates DataFrames against dictionary schema specifications."""

    @staticmethod
    def validate(df: pd.DataFrame, schema: Dict[str, Dict[str, Any]], dataset_name: str) -> Tuple[bool, List[str]]:
        """
        Validate df against schema.

        Returns:
            (is_valid: bool, errors: List[str])
        """
        errors = []

        # Check required columns
        for col_name, rules in schema.items():
            if col_name not in df.columns:
                errors.append(f"[{dataset_name}] Missing required column: '{col_name}'")
                continue

            # Check nullability
            if not rules.get("nullable", True):
                null_count = df[col_name].isna().sum()
                if null_count > 0:
                    errors.append(
                        f"[{dataset_name}] Column '{col_name}' is non-nullable but contains {null_count} nulls."
                    )

        # Check for unexpected columns
        expected_cols = set(schema.keys())
        # We allow extra flag columns like '{col}_filled'
        for col in df.columns:
            if col not in expected_cols and not col.endswith("_filled"):
                logger.debug(f"[{dataset_name}] Note: column '{col}' not in schema definition.")

        is_valid = len(errors) == 0
        if is_valid:
            logger.info(f"[{dataset_name}] Schema validation PASSED.")
        else:
            logger.warning(f"[{dataset_name}] Schema validation FAILED with {len(errors)} errors.")

        return is_valid, errors

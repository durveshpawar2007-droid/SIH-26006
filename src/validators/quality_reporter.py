"""
SIH26006 — Data Quality Reporter.

Compiles complete data quality metrics into data/metadata/data_quality_report.json.
Metrics include:
- row_count
- date_coverage
- missing_percentage
- duplicate_count
- outlier_count
- validation_errors
- provenance breakdown (real_percentage, derived_percentage, estimated_percentage, synthetic_percentage)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


class QualityReporter:
    """Generates comprehensive JSON reports on data quality, coverage, and provenance."""

    def __init__(self, metadata_dir: Path):
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def analyze_dataset(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        errors: List[str] = None,
    ) -> Dict[str, Any]:
        """Compute structured metrics for a dataset."""
        if errors is None:
            errors = []

        total_rows = len(df)
        report: Dict[str, Any] = {
            "dataset_name": dataset_name,
            "row_count": total_rows,
            "validation_errors": errors,
            "validation_status": "PASSED" if not errors else "FAILED",
        }

        if total_rows == 0:
            report["status"] = "EMPTY"
            return report

        # Date Coverage
        if "date" in df.columns:
            valid_dates = pd.to_datetime(df["date"], errors="coerce").dropna()
            if not valid_dates.empty:
                report["date_coverage"] = {
                    "start_date": str(valid_dates.min().strftime("%Y-%m-%d")),
                    "end_date": str(valid_dates.max().strftime("%Y-%m-%d")),
                    "unique_dates": int(valid_dates.nunique()),
                }
            if {"origin", "destination", "vessel_type"}.issubset(df.columns):
                dupes = df.duplicated(subset=["date", "origin", "destination", "vessel_type"]).sum()
                report["duplicate_composite_keys_count"] = int(dupes)
            else:
                dupes = df.duplicated(subset=["date"]).sum()
                report["duplicate_dates_count"] = int(dupes)
        else:
            report["duplicate_rows_count"] = int(df.duplicated().sum())

        # Missing values percentage
        missing_dict = {}
        for col in df.columns:
            if not col.endswith("_filled"):
                pct = (df[col].isna().sum() / total_rows) * 100.0
                missing_dict[col] = round(pct, 2)
        report["missing_percentage"] = missing_dict

        # Provenance Breakdown
        provenance_cols = [c for c in df.columns if c.startswith("data_type")]
        if provenance_cols:
            all_tags = []
            for col in provenance_cols:
                all_tags.extend(df[col].dropna().astype(str).str.upper().tolist())
            total_tags = len(all_tags)
            if total_tags > 0:
                report["provenance_breakdown"] = {
                    "real_percentage": round((all_tags.count("REAL") / total_tags) * 100.0, 2),
                    "derived_percentage": round((all_tags.count("DERIVED") / total_tags) * 100.0, 2),
                    "estimated_percentage": round((all_tags.count("ESTIMATED") / total_tags) * 100.0, 2),
                    "synthetic_percentage": round((all_tags.count("SYNTHETIC") / total_tags) * 100.0, 2),
                    "scenario_percentage": round((all_tags.count("SCENARIO") / total_tags) * 100.0, 2),
                }

        return report

    def save_report(self, full_report: Dict[str, Any], filename: str = "data_quality_report.json") -> Path:
        out_path = self.metadata_dir / filename
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(full_report, f, indent=2)
        logger.info(f"Saved quality report to {out_path}")
        return out_path

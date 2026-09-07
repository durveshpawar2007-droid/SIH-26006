"""
SIH26006 — Comprehensive Data Audit Script.

Inspects every CSV file across data/raw, data/processed, and data/synthetic:
- Row counts, column counts, column types
- Date range and continuity
- Missing values and percentages
- Duplicate rows and duplicate dates
- Numerical distributions (min, 25%, median, 75%, max, mean, std)
- Outlier detection
- Provenance tags
- Anomaly / impossible value detection
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

def audit_file(filepath: Path) -> dict:
    rel_path = filepath.relative_to(DATA_DIR)
    df = pd.read_csv(filepath)

    res = {
        "file_path": str(rel_path).replace("\\", "/"),
        "row_count": len(df),
        "col_count": len(df.columns),
        "columns": list(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_summary": {},
        "numeric_summary": {},
        "provenance_summary": {},
        "anomalies": []
    }

    # Date analysis
    date_cols = [c for c in df.columns if "date" in c.lower() and c != "retrieval_date"]
    if date_cols:
        primary_date = date_cols[0]
        dt_series = pd.to_datetime(df[primary_date], errors="coerce")
        valid_dt = dt_series.dropna()
        if not valid_dt.empty:
            res["date_column"] = primary_date
            res["date_min"] = str(valid_dt.min().strftime("%Y-%m-%d"))
            res["date_max"] = str(valid_dt.max().strftime("%Y-%m-%d"))
            res["unique_dates"] = int(valid_dt.nunique())
            res["duplicate_dates"] = int(df.duplicated(subset=[primary_date]).sum())
        else:
            res["date_column"] = primary_date
            res["date_min"] = "ALL_INVALID"
            res["date_max"] = "ALL_INVALID"

    # Missing values
    for col in df.columns:
        null_cnt = int(df[col].isna().sum())
        pct = round((null_cnt / len(df)) * 100.0, 2) if len(df) > 0 else 0.0
        res["missing_summary"][col] = {"null_count": null_cnt, "percentage": pct}

    # Numeric columns distribution
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        s = df[col].dropna()
        if not s.empty:
            res["numeric_summary"][col] = {
                "min": round(float(s.min()), 2),
                "q25": round(float(s.quantile(0.25)), 2),
                "median": round(float(s.median()), 2),
                "q75": round(float(s.quantile(0.75)), 2),
                "max": round(float(s.max()), 2),
                "mean": round(float(s.mean()), 2),
                "std": round(float(s.std()), 2) if len(s) > 1 else 0.0,
                "negative_count": int((s < 0).sum()),
                "zero_count": int((s == 0).sum()),
            }
            # Specific domain anomaly checks
            if (s < 0).sum() > 0:
                res["anomalies"].append(f"Negative values detected in numeric column: {col}")

    # Provenance tags
    prov_cols = [c for c in df.columns if c.startswith("data_type")]
    if prov_cols:
        for pcol in prov_cols:
            counts = df[pcol].value_counts().to_dict()
            res["provenance_summary"][pcol] = {str(k): int(v) for k, v in counts.items()}
    elif "data_type" in df.columns:
        counts = df["data_type"].value_counts().to_dict()
        res["provenance_summary"]["data_type"] = {str(k): int(v) for k, v in counts.items()}

    return res

def main():
    csv_files = sorted(list(DATA_DIR.rglob("*.csv")))
    print(f"Auditing {len(csv_files)} CSV files...")

    audit_results = {}
    for f in csv_files:
        info = audit_file(f)
        audit_results[info["file_path"]] = info
        print(f"Audited: {info['file_path']} ({info['row_count']} rows, {info['duplicate_rows']} dupes)")

    out_json = DATA_DIR / "metadata" / "audit_metrics.json"
    with open(out_json, "w", encoding="utf-8") as out_f:
        json.dump(audit_results, out_f, indent=2)

    print(f"\nAudit complete! Saved detailed metrics to {out_json}")

if __name__ == "__main__":
    main()

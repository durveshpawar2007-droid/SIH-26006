import json
from pathlib import Path

audit_path = Path("data/metadata/audit_metrics.json")
with open(audit_path, "r", encoding="utf-8") as f:
    d = json.load(f)

first_files = [
    "processed/bdi_cleaned.csv",
    "processed/bunker_prices_cleaned.csv",
    "processed/freight_estimates.csv",
    "processed/market_data.csv",
    "processed/model_features.csv",
]

for k in first_files:
    v = d[k]
    print("=" * 50)
    print(f"FILE: {k}")
    print("=" * 50)
    print(f"  Rows: {v['row_count']} | Columns: {v['col_count']} | Duplicate Rows: {v['duplicate_rows']}")
    if "date_min" in v:
        print(f"  Date Span: {v['date_min']} to {v['date_max']} ({v.get('unique_dates', 'N/A')} unique dates)")
    print(f"  Provenance: {v.get('provenance_summary', {})}")
    print("  Missing Values:")
    for col, m in v.get("missing_summary", {}).items():
        if m["null_count"] > 0:
            print(f"    - {col}: {m['null_count']} nulls ({m['percentage']}%)")
    print("  Numeric Summary:")
    for ncol, num in v.get("numeric_summary", {}).items():
        print(f"    - {ncol}: min={num['min']}, median={num['median']}, max={num['max']}, mean={num['mean']}, std={num['std']}")
    print()

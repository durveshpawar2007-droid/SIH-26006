"""
Generate static reference CSV files and compatibility matrix.

Creates:
- data/processed/port_constraints.csv (Indian East Coast Destinations)
- data/processed/origin_port_constraints.csv (Origins)
- data/processed/vessel_specs.csv
- data/processed/routes.csv
- data/processed/plant_params.csv
- data/processed/compatibility_matrix.csv (Priority 5 Physical Compatibility Engine)
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.constants import (
    PORT_CONSTRAINTS,
    ORIGIN_PORT_CONSTRAINTS,
    VESSEL_SPECS,
    ROUTES,
    PLANT_PARAMS,
)
from src.config.settings import DATA_PROCESSED_DIR

def _save_df(df: pd.DataFrame, filename: str, output_dir: Path):
    path = output_dir / filename
    try:
        df.to_csv(path, index=False)
        print(f"[OK] {filename}: {len(df)} rows -> {path}")
    except PermissionError:
        print(f"[SKIP] {filename} is locked; keeping existing file.")
    return path

def generate_origin_port_constraints(output_dir: Path):
    rows = [vars(pc) for pc in ORIGIN_PORT_CONSTRAINTS.values()]
    _save_df(pd.DataFrame(rows), "origin_port_constraints.csv", output_dir)

def generate_port_constraints(output_dir: Path):
    rows = [vars(pc) for pc in PORT_CONSTRAINTS.values()]
    _save_df(pd.DataFrame(rows), "port_constraints.csv", output_dir)

def generate_vessel_specs(output_dir: Path):
    rows = [vars(vs) for vs in VESSEL_SPECS.values()]
    _save_df(pd.DataFrame(rows), "vessel_specs.csv", output_dir)

def generate_routes(output_dir: Path):
    rows = [vars(rd) for rd in ROUTES.values()]
    _save_df(pd.DataFrame(rows), "routes.csv", output_dir)

def generate_plant_params(output_dir: Path):
    rows = [vars(pp) for pp in PLANT_PARAMS.values()]
    _save_df(pd.DataFrame(rows), "plant_params.csv", output_dir)

def generate_compatibility_matrix(output_dir: Path):
    """Priority 5: Physical Compatibility Engine"""
    rows = []
    
    for route_id, route in ROUTES.items():
        orig_port = ORIGIN_PORT_CONSTRAINTS.get(route.origin_port)
        dest_port = PORT_CONSTRAINTS.get(route.destination_port)
        
        if not orig_port or not dest_port:
            continue
            
        for vessel_id, vessel in VESSEL_SPECS.items():
            # Check draft compatibility
            orig_draft_ok = vessel.draft_m <= orig_port.max_draft_m
            dest_draft_ok = vessel.draft_m <= dest_port.max_operational_draft_m
            
            # Check dimensional compatibility (LOA / Beam)
            orig_dim_ok = vessel.loa_m <= orig_port.max_loa_m and vessel.beam_m <= orig_port.max_beam_m
            dest_dim_ok = vessel.loa_m <= dest_port.max_loa_m and vessel.beam_m <= dest_port.max_beam_m
            
            # Specific port restrictions (e.g. Haldia capesize ban)
            dest_restrict_ok = True
            if dest_port.capesize_capable is False and "CAPESIZE" in vessel.vessel_type:
                dest_restrict_ok = False
                
            orig_compatible = orig_draft_ok and orig_dim_ok
            dest_compatible = dest_draft_ok and dest_dim_ok and dest_restrict_ok
            overall = orig_compatible and dest_compatible
            
            reasons = []
            if not orig_draft_ok: reasons.append(f"Origin draft limit {orig_port.max_draft_m}m")
            if not orig_dim_ok: reasons.append("Origin dimensional limit")
            if not dest_draft_ok: reasons.append(f"Dest draft limit {dest_port.max_operational_draft_m}m")
            if not dest_dim_ok: reasons.append("Dest dimensional limit")
            if not dest_restrict_ok: reasons.append("Dest strict vessel ban")
            
            rows.append({
                "route_id": route.route_id,
                "origin_port": orig_port.origin_port,
                "destination_port": dest_port.port,
                "vessel_type": vessel.vessel_type,
                "vessel_variant": vessel.variant,
                "origin_compatible": orig_compatible,
                "destination_compatible": dest_compatible,
                "overall_compatible": overall,
                "constraint_failure_reason": " | ".join(reasons) if not overall else "None",
                "provenance": "DERIVED"
            })
            
    df = pd.DataFrame(rows)
    _save_df(df, "compatibility_matrix.csv", output_dir)

def main():
    output_dir = DATA_PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Generating static reference data and compatibility matrix")
    print("=" * 60)

    generate_origin_port_constraints(output_dir)
    generate_port_constraints(output_dir)
    generate_vessel_specs(output_dir)
    generate_routes(output_dir)
    generate_plant_params(output_dir)
    generate_compatibility_matrix(output_dir)

    print("=" * 60)
    print("All static data files generated successfully.")

if __name__ == "__main__":
    main()

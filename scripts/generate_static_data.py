"""
Generate static reference CSV files from constants.

Creates:
- data/processed/port_constraints.csv
- data/processed/vessel_specs.csv
- data/processed/routes.csv
- data/processed/plant_params.csv

These are generated from the verified constants in src/config/constants.py,
NOT from invented data. Each value carries provenance metadata.
"""

import sys
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config.constants import PORT_CONSTRAINTS, VESSEL_SPECS, ROUTES, PLANT_PARAMS
from src.config.settings import DATA_PROCESSED_DIR


def generate_port_constraints(output_dir: Path) -> Path:
    """Generate port_constraints.csv from PORT_CONSTRAINTS constants."""
    rows = []
    for port_id, pc in PORT_CONSTRAINTS.items():
        rows.append({
            "port": pc.port,
            "approach_channel_depth_m": pc.approach_channel_depth_m,
            "entrance_channel_depth_m": pc.entrance_channel_depth_m,
            "berth_depth_m": pc.berth_depth_m,
            "max_operational_draft_m": pc.max_operational_draft_m,
            "tidal_range_m": pc.tidal_range_m,
            "max_loa_m": pc.max_loa_m,
            "max_beam_m": pc.max_beam_m,
            "coal_berths_description": pc.coal_berths_description,
            "handling_capacity_mtpa": pc.handling_capacity_mtpa,
            "vessel_restrictions": pc.vessel_restrictions,
            "capesize_capable": pc.capesize_capable,
            "avg_turnaround_hrs": pc.avg_turnaround_hrs,
            "avg_preberthing_wait_hrs_low": pc.avg_preberthing_wait_hrs_low,
            "avg_preberthing_wait_hrs_high": pc.avg_preberthing_wait_hrs_high,
            "tidal_constraints": pc.tidal_constraints,
            "source": pc.source_infrastructure,
            "source_url": pc.source_url,
            "retrieval_date": pc.retrieval_date,
            "data_type_infrastructure": pc.data_type_infrastructure,
            "data_type_trt": pc.data_type_trt,
            "data_type_wait": pc.data_type_wait,
        })

    df = pd.DataFrame(rows)
    path = output_dir / "port_constraints.csv"
    try:
        df.to_csv(path, index=False)
        print(f"[OK] port_constraints.csv: {len(df)} rows -> {path}")
    except PermissionError:
        print(f"[SKIP] port_constraints.csv is locked by another program; keeping existing file.")
    return path


def generate_vessel_specs(output_dir: Path) -> Path:
    """Generate vessel_specs.csv from VESSEL_SPECS constants."""
    rows = []
    for spec_id, vs in VESSEL_SPECS.items():
        rows.append({
            "vessel_type": vs.vessel_type,
            "variant": vs.variant,
            "dwt_tonnes": vs.dwt_tonnes,
            "dwt_min_tonnes": vs.dwt_min_tonnes,
            "dwt_max_tonnes": vs.dwt_max_tonnes,
            "cargo_capacity_tonnes": vs.cargo_capacity_tonnes,
            "cargo_capacity_min_tonnes": vs.cargo_capacity_min_tonnes,
            "cargo_capacity_max_tonnes": vs.cargo_capacity_max_tonnes,
            "typical_draft_m": vs.typical_draft_m,
            "loa_m": vs.loa_m,
            "beam_m": vs.beam_m,
            "speed_knots": vs.speed_knots,
            "speed_ballast_knots": vs.speed_ballast_knots,
            "fuel_consumption_sea_mt_day": vs.fuel_consumption_sea_mt_day,
            "fuel_consumption_ballast_mt_day": vs.fuel_consumption_ballast_mt_day,
            "fuel_consumption_port_mt_day": vs.fuel_consumption_port_mt_day,
            "fuel_type": vs.fuel_type,
            "charter_rate_low_usd_day": vs.charter_rate_low_usd_day,
            "charter_rate_high_usd_day": vs.charter_rate_high_usd_day,
            "charter_rate_avg_usd_day": vs.charter_rate_avg_usd_day,
            "daily_opex_usd_day": vs.daily_opex_usd_day,
            "gear_type": vs.gear_type,
            "source": vs.source,
            "data_type_physical": vs.data_type_physical,
            "data_type_fuel": vs.data_type_fuel,
            "data_type_charter": vs.data_type_charter,
            "data_type_opex": vs.data_type_opex,
        })

    df = pd.DataFrame(rows)
    path = output_dir / "vessel_specs.csv"
    try:
        df.to_csv(path, index=False)
        print(f"[OK] vessel_specs.csv: {len(df)} rows -> {path}")
    except PermissionError:
        print(f"[SKIP] vessel_specs.csv is locked by another program; keeping existing file.")
    return path


def generate_routes(output_dir: Path) -> Path:
    """Generate routes.csv from ROUTES constants."""
    rows = []
    for route_key, rd in ROUTES.items():
        rows.append({
            "origin": rd.origin,
            "destination": rd.destination,
            "distance_nm": rd.distance_nm,
            "typical_transit_days": rd.typical_transit_days,
            "route_notes": rd.route_notes,
            "vessel_restrictions": rd.vessel_restrictions,
            "source": rd.source,
            "data_type": rd.data_type,
        })

    df = pd.DataFrame(rows)
    path = output_dir / "routes.csv"
    try:
        df.to_csv(path, index=False)
        print(f"[OK] routes.csv: {len(df)} rows -> {path}")
    except PermissionError:
        print(f"[SKIP] routes.csv is locked by another program; keeping existing file.")
    return path


def generate_plant_params(output_dir: Path) -> Path:
    """Generate plant_params.csv from PLANT_PARAMS constants."""
    rows = []
    for plant_id, pp in PLANT_PARAMS.items():
        rows.append({
            "plant": pp.plant,
            "annual_coking_coal_mt": pp.annual_coking_coal_mt,
            "daily_consumption_mt": pp.daily_consumption_mt,
            "import_share_pct": pp.import_share_pct,
            "specific_consumption_t_per_t_hm": pp.specific_consumption_t_per_t_hm,
            "min_safe_stock_days": pp.min_safe_stock_days,
            "max_storage_mt": pp.max_storage_mt,
            "current_stockpile_mt": pp.current_stockpile_mt,
            "preferred_port": pp.preferred_port,
            "source": pp.source,
            "data_type_consumption": pp.data_type_consumption,
            "data_type_stockpile": pp.data_type_stockpile,
        })

    df = pd.DataFrame(rows)
    path = output_dir / "plant_params.csv"
    try:
        df.to_csv(path, index=False)
        print(f"[OK] plant_params.csv: {len(df)} rows -> {path}")
    except PermissionError:
        print(f"[SKIP] plant_params.csv is locked by another program; keeping existing file.")
    return path


def main():
    """Generate all static reference CSV files."""
    output_dir = DATA_PROCESSED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Generating static reference data files")
    print("=" * 60)

    generate_port_constraints(output_dir)
    generate_vessel_specs(output_dir)
    generate_routes(output_dir)
    generate_plant_params(output_dir)

    print("=" * 60)
    print("All static data files generated successfully.")


if __name__ == "__main__":
    main()

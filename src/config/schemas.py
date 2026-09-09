"""
SIH26006 — Expected column schemas for all output datasets.

Each schema is a dict of {column_name: {dtype, nullable, description, data_type}}.
Used by validators to enforce structure and by documentation to define contracts.
"""

MARKET_DATA_SCHEMA = {
    "date":          {"dtype": "str",   "nullable": False, "description": "Business day date (YYYY-MM-DD)"},
    "bdi":           {"dtype": "float", "nullable": True,  "description": "Baltic Dry Index (points). Explanatory feature, NOT target."},
    "bdry_close":    {"dtype": "float", "nullable": True,  "description": "BDRY ETF close price (USD). Charter-rate proxy signal."},
    "bunker_vlsfo":  {"dtype": "float", "nullable": True,  "description": "VLSFO 0.5% global 20-port average (USD/MT)"},
    "bunker_mgo":    {"dtype": "float", "nullable": True,  "description": "Marine Gas Oil global 20-port average (USD/MT)"},
    "bunker_ifo380": {"dtype": "float", "nullable": True,  "description": "IFO 380 CST global 20-port average (USD/MT)"},
    "usd_inr":       {"dtype": "float", "nullable": True,  "description": "USD/INR exchange rate (INR per 1 USD)"},
    "source_bdi":    {"dtype": "str",   "nullable": True,  "description": "BDI data source identifier"},
    "source_bunker": {"dtype": "str",   "nullable": True,  "description": "Bunker data source identifier"},
    "source_fx":     {"dtype": "str",   "nullable": True,  "description": "FX data source identifier"},
    "data_type":     {"dtype": "str",   "nullable": False, "description": "Provenance: REAL for all market observations"},
}

FREIGHT_ESTIMATES_SCHEMA = {
    "date":                            {"dtype": "str",   "nullable": False, "description": "Business day date"},
    "origin":                          {"dtype": "str",   "nullable": False, "description": "Origin port"},
    "destination":                     {"dtype": "str",   "nullable": False, "description": "Destination port"},
    "vessel_type":                     {"dtype": "str",   "nullable": False, "description": "Vessel class"},
    "vessel_variant":                  {"dtype": "str",   "nullable": False, "description": "Vessel variant"},
    "estimated_charter_rate_usd_day":  {"dtype": "float", "nullable": False, "description": "Charter rate proxy from BDRY scaling (USD/day)"},
    "one_way_voyage_days":             {"dtype": "float", "nullable": False, "description": "One-way laden sea steaming + discharge port dwell days"},
    "one_way_bunker_cost_usd":         {"dtype": "float", "nullable": False, "description": "Direct one-way bunker fuel expenditure (USD)"},
    "one_way_cost_usd_mt":             {"dtype": "float", "nullable": False, "description": "Direct one-way laden trip logistics cost (USD/MT)"},
    "commercial_voyage_days":          {"dtype": "float", "nullable": False, "description": "Commercial voyage duration including load port dwell and ballast return allocation"},
    "commercial_bunker_cost_usd":      {"dtype": "float", "nullable": False, "description": "Commercial cycle bunker fuel expenditure including ballast leg (USD)"},
    "estimated_spot_freight_usd_mt":   {"dtype": "float", "nullable": False, "description": "Commercial spot voyage fixture equivalent rate (USD/MT)"},
    "estimated_freight_rate_usd_mt":   {"dtype": "float", "nullable": False, "description": "Target freight rate (USD/MT)"},
    "estimated_freight_rate_inr_mt":   {"dtype": "float", "nullable": False, "description": "Target freight rate converted to INR (INR/MT)"},
    "calibration_status":              {"dtype": "str",   "nullable": False, "description": "Benchmark calibration status against public fixture data"},
    "methodology":                     {"dtype": "str",   "nullable": False, "description": "Always SYNTHETIC_VOYAGE_ESTIMATION"},
    "data_type":                       {"dtype": "str",   "nullable": False, "description": "Always DERIVED — never REAL"},
}

MODEL_FEATURES_SCHEMA = {
    "date":                  {"dtype": "str",   "nullable": False, "description": "Business day date"},
    "origin":                {"dtype": "str",   "nullable": False, "description": "Route origin"},
    "destination":           {"dtype": "str",   "nullable": False, "description": "Route destination"},
    "vessel_type":           {"dtype": "str",   "nullable": False, "description": "Vessel class"},
    "vessel_variant":        {"dtype": "str",   "nullable": False, "description": "Vessel variant"},
    "freight_rate_usd_mt":   {"dtype": "float", "nullable": True,  "description": "Target variable (DERIVED via SVE)"},
    "bdi":                   {"dtype": "float", "nullable": True,  "description": "BDI — explanatory feature only"},
    "bdi_lag_1":             {"dtype": "float", "nullable": True,  "description": "BDI at T-1"},
    "bdi_lag_7":             {"dtype": "float", "nullable": True,  "description": "BDI at T-7"},
    "bdi_rolling_mean_7":    {"dtype": "float", "nullable": True,  "description": "7-day rolling mean BDI"},
    "bdi_rolling_std_7":     {"dtype": "float", "nullable": True,  "description": "7-day rolling std dev BDI"},
    "bdi_rolling_mean_30":   {"dtype": "float", "nullable": True,  "description": "30-day rolling mean BDI"},
    "bunker_vlsfo":          {"dtype": "float", "nullable": True,  "description": "VLSFO price"},
    "bunker_vlsfo_lag_1":    {"dtype": "float", "nullable": True,  "description": "VLSFO at T-1"},
    "bunker_change_pct_7d":  {"dtype": "float", "nullable": True,  "description": "7-day VLSFO % change"},
    "usd_inr":               {"dtype": "float", "nullable": True,  "description": "USD/INR rate"},
    "usd_inr_lag_1":         {"dtype": "float", "nullable": True,  "description": "USD/INR at T-1"},
    "usd_inr_change_pct_7d": {"dtype": "float", "nullable": True,  "description": "7-day FX % change"},
    "day_of_week":           {"dtype": "float",   "nullable": True,  "description": "Day of week (Mon=0)"},
    "month":                 {"dtype": "float",   "nullable": True,  "description": "Month (1-12)"},
    "bdi_momentum_14d":      {"dtype": "float", "nullable": True,  "description": "14-day BDI momentum"},
    "bunker_bdi_ratio":      {"dtype": "float", "nullable": True,  "description": "VLSFO/BDI ratio"},
}

PORT_CONSTRAINTS_SCHEMA = {
    "port":                         {"dtype": "str",   "nullable": False, "description": "Port name"},
    "country":                      {"dtype": "str",   "nullable": False, "description": "Country"},
    "approach_channel_depth_m":     {"dtype": "float", "nullable": False, "description": "Approach channel depth (meters)"},
    "entrance_channel_depth_m":     {"dtype": "float", "nullable": True,  "description": "Entrance channel depth (meters)"},
    "berth_depth_m":                {"dtype": "float", "nullable": False, "description": "Berth depth at coal berths (meters)"},
    "max_operational_draft_m":      {"dtype": "float", "nullable": False, "description": "Maximum permitted operational draft (meters)"},
    "tidal_range_m":                {"dtype": "float", "nullable": True,  "description": "Tidal range"},
    "max_loa_m":                    {"dtype": "float", "nullable": False, "description": "Max LOA permitted (meters)"},
    "max_beam_m":                   {"dtype": "float", "nullable": False, "description": "Max beam permitted (meters)"},
    "coal_berths_description":      {"dtype": "str",   "nullable": False, "description": "Description of coal handling berths"},
    "handling_capacity_mtpa":       {"dtype": "float", "nullable": False, "description": "Rated handling capacity (MTPA)"},
    "cargo_handling_rate_mt_day":   {"dtype": "float", "nullable": False, "description": "Daily handling rate"},
    "vessel_restrictions":          {"dtype": "str",   "nullable": False, "description": "Vessel type/size restrictions"},
    "capesize_capable":             {"dtype": "bool",  "nullable": False, "description": "Can accept Capesize vessels"},
    "avg_turnaround_hrs":           {"dtype": "float", "nullable": False, "description": "Average TRT (hours)"},
    "avg_preberthing_wait_hrs_low": {"dtype": "float", "nullable": False, "description": "Pre-berthing wait low estimate (hours)"},
    "avg_preberthing_wait_hrs_high":{"dtype": "float", "nullable": False, "description": "Pre-berthing wait high estimate (hours)"},
    "tidal_constraints":            {"dtype": "str",   "nullable": True,  "description": "Tidal/seasonal restrictions"},
    "source_infrastructure":        {"dtype": "str",   "nullable": False, "description": "Data source"},
    "source_url":                   {"dtype": "str",   "nullable": False, "description": "Source URL for verification"},
    "provenance":                   {"dtype": "str",   "nullable": False, "description": "Provenance tag"},
}

VESSEL_SPECS_SCHEMA = {
    "vessel_type":                  {"dtype": "str",   "nullable": False, "description": "CAPESIZE or PANAMAX"},
    "variant":                      {"dtype": "str",   "nullable": False, "description": "Variant"},
    "dwt_tonnes":                   {"dtype": "int",   "nullable": False, "description": "Representative deadweight tonnage (MT)"},
    "cargo_capacity_mt":            {"dtype": "int",   "nullable": False, "description": "Representative coal payload (MT)"},
    "draft_m":                      {"dtype": "float", "nullable": False, "description": "Typical laden draft (meters)"},
    "loa_m":                        {"dtype": "float", "nullable": False, "description": "Length overall (meters)"},
    "beam_m":                       {"dtype": "float", "nullable": False, "description": "Beam (meters)"},
    "speed_knots":                  {"dtype": "float", "nullable": False, "description": "Economic laden speed (knots)"},
    "fuel_consumption_sea_mt_day":  {"dtype": "float", "nullable": False, "description": "Laden sea fuel consumption (MT VLSFO/day)"},
    "fuel_consumption_port_mt_day": {"dtype": "float", "nullable": False, "description": "Port fuel consumption (MT VLSFO/day)"},
    "daily_opex_usd_day":           {"dtype": "float", "nullable": False, "description": "Daily vessel OPEX (USD/day)"},
    "charter_rate_reference":       {"dtype": "float", "nullable": False, "description": "Charter rate average (USD/day)"},
    "source":                       {"dtype": "str",   "nullable": False, "description": "Data source"},
    "provenance":                   {"dtype": "str",   "nullable": False, "description": "Provenance tag"},
}

ROUTES_SCHEMA = {
    "route_id":                {"dtype": "str",   "nullable": False, "description": "Route identifier"},
    "origin_port":             {"dtype": "str",   "nullable": False, "description": "Origin port/region"},
    "origin_country":          {"dtype": "str",   "nullable": False, "description": "Origin country"},
    "destination_port":        {"dtype": "str",   "nullable": False, "description": "Destination port"},
    "destination_country":     {"dtype": "str",   "nullable": False, "description": "Destination country"},
    "distance_nautical_miles": {"dtype": "int",   "nullable": False, "description": "Distance (nautical miles)"},
    "estimated_sailing_days":  {"dtype": "float", "nullable": False, "description": "Transit days"},
    "route_notes":             {"dtype": "str",   "nullable": True,  "description": "Routing notes"},
    "vessel_restrictions":     {"dtype": "str",   "nullable": True,  "description": "Vessel restrictions on route"},
    "source":                  {"dtype": "str",   "nullable": False, "description": "Distance data source"},
    "provenance":              {"dtype": "str",   "nullable": False, "description": "Provenance tag"},
}

PLANT_PARAMS_SCHEMA = {
    "plant":                          {"dtype": "str",   "nullable": False, "description": "Plant identifier"},
    "annual_coking_coal_mt":          {"dtype": "float", "nullable": False, "description": "Annual consumption (million MT)"},
    "daily_consumption_mt":           {"dtype": "float", "nullable": False, "description": "Daily consumption (MT/day)"},
    "import_share_pct":               {"dtype": "float", "nullable": False, "description": "Import share (%)"},
    "specific_consumption_t_per_t_hm":{"dtype": "float", "nullable": False, "description": "Coking coal per tonne hot metal"},
    "min_safe_stock_days":            {"dtype": "int",   "nullable": False, "description": "Minimum safe stock (days)"},
    "max_storage_mt":                 {"dtype": "float", "nullable": False, "description": "Max storage capacity (MT)"},
    "current_stockpile_mt":           {"dtype": "float", "nullable": False, "description": "Current stockpile (MT)"},
    "preferred_port":                 {"dtype": "str",   "nullable": False, "description": "Preferred receiving port"},
    "source":                         {"dtype": "str",   "nullable": False, "description": "Data source"},
    "data_type":                      {"dtype": "str",   "nullable": False, "description": "Provenance tag"},
}

PORT_CONGESTION_SCHEMA = {
    "date":                  {"dtype": "str",   "nullable": False, "description": "Business day date"},
    "port":                  {"dtype": "str",   "nullable": False, "description": "Indian destination port"},
    "waiting_vessels_count": {"dtype": "int",   "nullable": False, "description": "Simulated number of vessels at anchorage"},
    "avg_waiting_time_hrs":  {"dtype": "float", "nullable": False, "description": "Simulated waiting time in hours"},
    "congestion_status":     {"dtype": "str",   "nullable": False, "description": "Categorical severity (LOW, NORMAL, HIGH, SEVERE)"},
    "data_type":             {"dtype": "str",   "nullable": False, "description": "Provenance tag (SYNTHETIC)"},
}

CONTRACT_SCENARIOS_SCHEMA = {
    "date":                  {"dtype": "str",   "nullable": False, "description": "Business day date"},
    "route_id":              {"dtype": "str",   "nullable": False, "description": "Route ID"},
    "vessel_type":           {"dtype": "str",   "nullable": False, "description": "Vessel class"},
    "contract_type":         {"dtype": "str",   "nullable": False, "description": "SPOT, COA_3M, COA_6M, COA_12M"},
    "estimated_rate_usd_mt": {"dtype": "float", "nullable": False, "description": "Projected rate per MT"},
    "price_premium_pct":     {"dtype": "float", "nullable": False, "description": "Premium or discount vs Spot"},
    "volume_commitment_mt":  {"dtype": "float", "nullable": False, "description": "Assumed volume commitment for contract"},
    "data_type":             {"dtype": "str",   "nullable": False, "description": "Provenance tag (SCENARIO)"},
}

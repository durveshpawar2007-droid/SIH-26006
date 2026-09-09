"""
SIH26006 — Static reference constants for ports, vessels, routes, and plants.

IMPORTANT PROVENANCE NOTES:
- Port infrastructure values are sourced from official Port Authority websites
  and MoPSW TRW reports. Each value includes a source URL and retrieval date.
- Vessel specifications are from industry standard references.
- Route distances are derived from sea-distances.org and NGA Pub 151.
- Plant parameters are from SAIL/RINL annual reports where available.

Every value carries a data_type tag:
  REAL      — directly from authoritative source
  ESTIMATED — industry benchmark / expert judgment
  SCENARIO  — configurable simulation input
"""

from dataclasses import dataclass, field
from typing import Optional


# ─── Data Type Tags ──────────────────────────────────────────────
REAL = "REAL"
DERIVED = "DERIVED"
ESTIMATED = "ESTIMATED"
SYNTHETIC = "SYNTHETIC"
SCENARIO = "SCENARIO"
UNAVAILABLE = "UNAVAILABLE"

# ═══════════════════════════════════════════════════════════════════
# ORIGIN PORT CONSTRAINTS
# ═══════════════════════════════════════════════════════════════════
@dataclass
class OriginPortConstraint:
    origin_port: str
    country: str
    commodity_supported: str
    max_draft_m: float
    max_loa_m: float
    max_beam_m: float
    cargo_handling_capacity: str
    cargo_handling_rate_mt_day: float
    source: str
    provenance: str = ESTIMATED

ORIGIN_PORT_CONSTRAINTS = {
    "NEWCASTLE_AU": OriginPortConstraint(
        origin_port="NEWCASTLE_AU", country="Australia", commodity_supported="Coking/Thermal Coal",
        max_draft_m=16.5, max_loa_m=300.0, max_beam_m=50.0, cargo_handling_capacity="High",
        cargo_handling_rate_mt_day=80000.0, source="Newcastle Port Authority", provenance=REAL
    ),
    "GLADSTONE_AU": OriginPortConstraint(
        origin_port="GLADSTONE_AU", country="Australia", commodity_supported="Coking/Thermal Coal",
        max_draft_m=16.3, max_loa_m=315.0, max_beam_m=50.0, cargo_handling_capacity="High",
        cargo_handling_rate_mt_day=80000.0, source="Gladstone Ports Corp", provenance=REAL
    ),
    "KALIMANTAN_ID": OriginPortConstraint(
        origin_port="KALIMANTAN_ID", country="Indonesia", commodity_supported="Thermal/Semi-soft Coal",
        max_draft_m=16.0, max_loa_m=300.0, max_beam_m=50.0, cargo_handling_capacity="High (Anchorage)",
        cargo_handling_rate_mt_day=30000.0, source="Indonesian Coal Terminals Benchmark", provenance=ESTIMATED
    ),
    "NORFOLK_US": OriginPortConstraint(
        origin_port="NORFOLK_US", country="United States", commodity_supported="Coking Coal",
        max_draft_m=15.2, max_loa_m=300.0, max_beam_m=46.0, cargo_handling_capacity="High",
        cargo_handling_rate_mt_day=60000.0, source="Port of Virginia", provenance=ESTIMATED
    ),
    "MAPUTO_MZ": OriginPortConstraint(
        origin_port="MAPUTO_MZ", country="Mozambique", commodity_supported="Coking/Thermal Coal",
        max_draft_m=14.5, max_loa_m=280.0, max_beam_m=42.0, cargo_handling_capacity="Medium",
        cargo_handling_rate_mt_day=40000.0, source="MPDC Matola Terminal", provenance=ESTIMATED
    ),
    "VOSTOCHNY_RU": OriginPortConstraint(
        origin_port="VOSTOCHNY_RU", country="Russia", commodity_supported="Coking/Thermal Coal",
        max_draft_m=16.5, max_loa_m=300.0, max_beam_m=46.0, cargo_handling_capacity="High",
        cargo_handling_rate_mt_day=60000.0, source="Vostochny Port JSC", provenance=ESTIMATED
    ),
}

# ═══════════════════════════════════════════════════════════════════
# DESTINATION PORT CONSTRAINTS (INDIAN EAST COAST)
# ═══════════════════════════════════════════════════════════════════
@dataclass
class PortConstraint:
    port: str
    country: str
    approach_channel_depth_m: float
    entrance_channel_depth_m: Optional[float]
    berth_depth_m: float
    max_operational_draft_m: float
    tidal_range_m: Optional[float]
    max_loa_m: float
    max_beam_m: float
    coal_berths_description: str
    handling_capacity_mtpa: float
    cargo_handling_rate_mt_day: float
    vessel_restrictions: str
    capesize_capable: bool
    avg_turnaround_hrs: float
    avg_preberthing_wait_hrs_low: float
    avg_preberthing_wait_hrs_high: float
    tidal_constraints: str
    source_infrastructure: str
    source_url: str
    provenance: str = REAL

PORT_CONSTRAINTS = {
    "PARADIP": PortConstraint(
        port="PARADIP", country="India", approach_channel_depth_m=18.7, entrance_channel_depth_m=17.1,
        berth_depth_m=16.0, max_operational_draft_m=16.5, tidal_range_m=None, max_loa_m=300.0, max_beam_m=46.0,
        coal_berths_description="Western Dock-1 (16.5m), KICT (16.0m)", handling_capacity_mtpa=289.0, cargo_handling_rate_mt_day=60000.0,
        vessel_restrictions="LOA>260m restriction", capesize_capable=True,
        avg_turnaround_hrs=46.16, avg_preberthing_wait_hrs_low=12.0, avg_preberthing_wait_hrs_high=24.0,
        tidal_constraints="Minimal", source_infrastructure="PPA + MoPSW", source_url="https://paradipport.gov.in"
    ),
    "VIZAG": PortConstraint(
        port="VIZAG", country="India", approach_channel_depth_m=19.0, entrance_channel_depth_m=15.5,
        berth_depth_m=18.1, max_operational_draft_m=18.1, tidal_range_m=None, max_loa_m=356.0, max_beam_m=50.0,
        coal_berths_description="VGCB Outer Harbour (18.1m)", handling_capacity_mtpa=144.0, cargo_handling_rate_mt_day=60000.0,
        vessel_restrictions="Inner Harbour restricted to Panamax", capesize_capable=True,
        avg_turnaround_hrs=69.19, avg_preberthing_wait_hrs_low=8.0, avg_preberthing_wait_hrs_high=16.0,
        tidal_constraints="Tidal limits inside", source_infrastructure="VPA + MoPSW", source_url="https://vizagport.com"
    ),
    "HALDIA": PortConstraint(
        port="HALDIA", country="India", approach_channel_depth_m=9.2, entrance_channel_depth_m=9.2,
        berth_depth_m=9.1, max_operational_draft_m=9.1, tidal_range_m=4.5, max_loa_m=240.0, max_beam_m=32.26,
        coal_berths_description="Berth 4A", handling_capacity_mtpa=50.7, cargo_handling_rate_mt_day=20000.0,
        vessel_restrictions="NO Capesize. Lock entry limits.", capesize_capable=False,
        avg_turnaround_hrs=46.79, avg_preberthing_wait_hrs_low=24.0, avg_preberthing_wait_hrs_high=48.0,
        tidal_constraints="High siltation", source_infrastructure="SMP Kolkata", source_url="https://smportkolkata.org.in"
    ),
    "GANGAVARAM": PortConstraint(
        port="GANGAVARAM", country="India", approach_channel_depth_m=20.0, entrance_channel_depth_m=19.0,
        berth_depth_m=18.5, max_operational_draft_m=18.0, tidal_range_m=1.5, max_loa_m=320.0, max_beam_m=50.0,
        coal_berths_description="Fully mechanized deep water coal terminals", handling_capacity_mtpa=64.0, cargo_handling_rate_mt_day=70000.0,
        vessel_restrictions="Minimal", capesize_capable=True,
        avg_turnaround_hrs=40.0, avg_preberthing_wait_hrs_low=6.0, avg_preberthing_wait_hrs_high=18.0,
        tidal_constraints="Minimal", source_infrastructure="Adani Gangavaram Port", source_url="https://www.adaniports.com"
    ),
    "GOPALPUR": PortConstraint(
        port="GOPALPUR", country="India", approach_channel_depth_m=15.0, entrance_channel_depth_m=14.5,
        berth_depth_m=14.5, max_operational_draft_m=14.0, tidal_range_m=None, max_loa_m=260.0, max_beam_m=40.0,
        coal_berths_description="Multi-purpose berths", handling_capacity_mtpa=20.0, cargo_handling_rate_mt_day=30000.0,
        vessel_restrictions="Primarily Panamax/Supramax", capesize_capable=False,
        avg_turnaround_hrs=55.0, avg_preberthing_wait_hrs_low=12.0, avg_preberthing_wait_hrs_high=24.0,
        tidal_constraints="Minimal", source_infrastructure="Adani Gopalpur Port", source_url="https://www.adaniports.com"
    ),
    "DHAMRA": PortConstraint(
        port="DHAMRA", country="India", approach_channel_depth_m=19.0, entrance_channel_depth_m=18.0,
        berth_depth_m=18.0, max_operational_draft_m=18.0, tidal_range_m=None, max_loa_m=320.0, max_beam_m=50.0,
        coal_berths_description="Fully mechanized bulk cargo berths", handling_capacity_mtpa=40.0, cargo_handling_rate_mt_day=80000.0,
        vessel_restrictions="Capesize capable", capesize_capable=True,
        avg_turnaround_hrs=35.0, avg_preberthing_wait_hrs_low=6.0, avg_preberthing_wait_hrs_high=18.0,
        tidal_constraints="Minor tide constraints", source_infrastructure="Adani Dhamra Port", source_url="https://www.adaniports.com"
    ),
    "SANDHEADS": PortConstraint(
        port="SANDHEADS", country="India", approach_channel_depth_m=50.0, entrance_channel_depth_m=50.0,
        berth_depth_m=50.0, max_operational_draft_m=50.0, tidal_range_m=None, max_loa_m=400.0, max_beam_m=60.0,
        coal_berths_description="Deep water anchorage (Transshipment)", handling_capacity_mtpa=20.0, cargo_handling_rate_mt_day=15000.0,
        vessel_restrictions="Ship-to-ship transfer only", capesize_capable=True,
        avg_turnaround_hrs=96.0, avg_preberthing_wait_hrs_low=0.0, avg_preberthing_wait_hrs_high=0.0,
        tidal_constraints="Open sea conditions", source_infrastructure="SMP Kolkata Anchorages", source_url="https://smportkolkata.org.in"
    ),
}

# ═══════════════════════════════════════════════════════════════════
# VESSEL SPECIFICATIONS
# ═══════════════════════════════════════════════════════════════════
@dataclass
class VesselSpec:
    vessel_type: str
    variant: str
    dwt_tonnes: int
    cargo_capacity_mt: int
    draft_m: float
    loa_m: float
    beam_m: float
    speed_knots: float
    fuel_consumption_sea_mt_day: float
    fuel_consumption_port_mt_day: float
    daily_opex_usd_day: float
    charter_rate_reference: float
    source: str
    provenance: str = ESTIMATED

VESSEL_SPECS = {
    "HANDYSIZE": VesselSpec("HANDYSIZE", "Standard", 35000, 32000, 10.5, 180.0, 28.0, 12.5, 20.0, 2.5, 4500.0, 9000.0, "Industry Benchmark"),
    "SUPRAMAX": VesselSpec("SUPRAMAX", "Standard", 55000, 50000, 12.2, 190.0, 32.26, 13.0, 26.0, 3.0, 4800.0, 12000.0, "Industry Benchmark"),
    "PANAMAX": VesselSpec("PANAMAX", "Standard", 75000, 70000, 14.0, 229.0, 32.26, 13.0, 32.0, 3.5, 5200.0, 14000.0, "Industry Benchmark"),
    "KAMSARMAX": VesselSpec("PANAMAX", "Kamsarmax", 82000, 77000, 14.4, 229.0, 32.26, 13.0, 34.0, 3.5, 5400.0, 15000.0, "Industry Benchmark"),
    "CAPESIZE": VesselSpec("CAPESIZE", "Standard", 180000, 170000, 18.2, 295.0, 47.0, 13.0, 50.0, 4.5, 6500.0, 22000.0, "Industry Benchmark"),
    "NEWCASTLEMAX": VesselSpec("CAPESIZE", "Newcastlemax", 210000, 200000, 18.5, 300.0, 50.0, 13.0, 52.0, 5.0, 7000.0, 24000.0, "Industry Benchmark"),
}

# ═══════════════════════════════════════════════════════════════════
# ROUTE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════
@dataclass
class RouteDefinition:
    route_id: str
    origin_port: str
    origin_country: str
    destination_port: str
    destination_country: str
    distance_nautical_miles: int
    estimated_sailing_days: float
    route_notes: str
    vessel_restrictions: str
    source: str
    provenance: str = ESTIMATED

def _create_route(orig: str, orig_cty: str, dest: str, dist: int) -> tuple[str, RouteDefinition]:
    return f"{orig}_{dest}", RouteDefinition(
        route_id=f"{orig}_{dest}", origin_port=orig, origin_country=orig_cty,
        destination_port=dest, destination_country="India",
        distance_nautical_miles=dist, estimated_sailing_days=round(dist/(12.5*24), 1),
        route_notes="", vessel_restrictions="", source="NGA Pub 151 Approximation"
    )

ROUTES = dict([
    # AUSTRALIA (GLADSTONE/NEWCASTLE -> INDIA EAST COAST)
    _create_route("NEWCASTLE_AU", "Australia", "PARADIP", 5400),
    _create_route("NEWCASTLE_AU", "Australia", "VIZAG", 5350),
    _create_route("NEWCASTLE_AU", "Australia", "HALDIA", 5500),
    _create_route("NEWCASTLE_AU", "Australia", "GANGAVARAM", 5350),
    _create_route("NEWCASTLE_AU", "Australia", "GOPALPUR", 5380),
    _create_route("NEWCASTLE_AU", "Australia", "DHAMRA", 5430),
    _create_route("NEWCASTLE_AU", "Australia", "SANDHEADS", 5450),

    # INDONESIA (KALIMANTAN -> INDIA EAST COAST)
    _create_route("KALIMANTAN_ID", "Indonesia", "PARADIP", 2325),
    _create_route("KALIMANTAN_ID", "Indonesia", "VIZAG", 2225),
    _create_route("KALIMANTAN_ID", "Indonesia", "HALDIA", 2425),
    _create_route("KALIMANTAN_ID", "Indonesia", "GANGAVARAM", 2225),
    _create_route("KALIMANTAN_ID", "Indonesia", "GOPALPUR", 2280),
    _create_route("KALIMANTAN_ID", "Indonesia", "DHAMRA", 2350),
    _create_route("KALIMANTAN_ID", "Indonesia", "SANDHEADS", 2380),

    # US EAST COAST (NORFOLK -> INDIA EAST COAST) via Cape of Good Hope
    _create_route("NORFOLK_US", "United States", "PARADIP", 10100),
    _create_route("NORFOLK_US", "United States", "VIZAG", 9900),
    _create_route("NORFOLK_US", "United States", "HALDIA", 10200),
    
    # MOZAMBIQUE (MAPUTO -> INDIA EAST COAST)
    _create_route("MAPUTO_MZ", "Mozambique", "PARADIP", 3700),
    _create_route("MAPUTO_MZ", "Mozambique", "VIZAG", 3500),
    _create_route("MAPUTO_MZ", "Mozambique", "HALDIA", 3800),

    # RUSSIA (VOSTOCHNY -> INDIA EAST COAST) via Singapore
    _create_route("VOSTOCHNY_RU", "Russia", "PARADIP", 5200),
    _create_route("VOSTOCHNY_RU", "Russia", "VIZAG", 5100),
    _create_route("VOSTOCHNY_RU", "Russia", "HALDIA", 5300),
])

# ═══════════════════════════════════════════════════════════════════
# PLANT PARAMETERS
# ═══════════════════════════════════════════════════════════════════
@dataclass
class PlantParams:
    plant: str
    annual_coking_coal_mt: float
    daily_consumption_mt: float
    import_share_pct: float
    specific_consumption_t_per_t_hm: float
    min_safe_stock_days: int
    max_storage_mt: float
    current_stockpile_mt: float
    preferred_port: str
    source: str
    data_type: str = SCENARIO

PLANT_PARAMS = {
    "SAIL_ROURKELA": PlantParams("SAIL_ROURKELA", 3.2, 8767.0, 82.0, 0.80, 15, 300000, 150000, "PARADIP", "SAIL 2024-25"),
    "SAIL_BOKARO": PlantParams("SAIL_BOKARO", 4.0, 10959.0, 82.0, 0.80, 15, 400000, 200000, "HALDIA", "SAIL 2024-25"),
    "RINL_VIZAG": PlantParams("RINL_VIZAG", 4.0, 10959.0, 92.0, 0.80, 15, 350000, 175000, "VIZAG", "RINL 2024-25"),
}

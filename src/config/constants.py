"""
SIH26006 — Static reference constants for ports, vessels, routes, and plants.

IMPORTANT PROVENANCE NOTES:
- Port infrastructure values are sourced from official Port Authority websites
  and MoPSW TRW reports. Each value includes a source URL and retrieval date.
- Vessel specifications are from industry standard references.
- Route distances are from sea-distances.org and NGA Pub 151.
- Plant parameters are from SAIL/RINL annual reports where available;
  stockpile/storage values are SCENARIO inputs (configurable).

Every value carries a data_type tag:
  REAL      — directly from authoritative source
  ESTIMATED — industry benchmark / expert judgment
  SCENARIO  — configurable simulation input
"""

from dataclasses import dataclass, field
from typing import Optional


# ─── Data Type Tags ──────────────────────────────────────────────
# Imported from settings but duplicated here for standalone use
REAL = "REAL"
DERIVED = "DERIVED"
ESTIMATED = "ESTIMATED"
SYNTHETIC = "SYNTHETIC"
SCENARIO = "SCENARIO"


# ═══════════════════════════════════════════════════════════════════
# PORT CONSTRAINTS
# ═══════════════════════════════════════════════════════════════════
# NOTE: These values are PRELIMINARY and must be verified against
# current authoritative sources before use in production.
# See PORT_DATA_SOURCES for the reference URLs to verify against.

@dataclass
class PortConstraint:
    """Physical and operational constraints for a single port."""
    port: str
    # Depth specifications (meters) — DISTINGUISH these clearly
    approach_channel_depth_m: float
    entrance_channel_depth_m: Optional[float]
    berth_depth_m: float
    max_operational_draft_m: float       # Max draft actually permitted
    tidal_range_m: Optional[float]       # Spring tide range if relevant

    # Dimensional limits
    max_loa_m: float
    max_beam_m: float

    # Capacity
    coal_berths_description: str
    handling_capacity_mtpa: float

    # Vessel restrictions
    vessel_restrictions: str
    capesize_capable: bool

    # Turnaround and waiting
    avg_turnaround_hrs: float            # FY2024-25 MoPSW TRW data
    avg_preberthing_wait_hrs_low: float  # Range low estimate
    avg_preberthing_wait_hrs_high: float # Range high estimate
    tidal_constraints: str

    # Provenance
    source_infrastructure: str
    source_trt: str
    source_url: str
    retrieval_date: str
    data_type_infrastructure: str = REAL
    data_type_trt: str = REAL
    data_type_wait: str = ESTIMATED      # Wait times are ranges, not precise


# NOTE: These values require verification against the actual Port Authority
# websites listed in source_url. The values below are from research conducted
# on 2026-09-07 using MoPSW TRW reports and port authority publications.
# They should be cross-checked before final use.

PORT_CONSTRAINTS = {
    "PARADIP": PortConstraint(
        port="PARADIP",
        approach_channel_depth_m=18.7,
        entrance_channel_depth_m=17.1,
        berth_depth_m=16.0,             # Standard coal berths
        max_operational_draft_m=16.5,    # Western Dock-1 (deepest)
        tidal_range_m=None,              # Minimal tidal impact
        max_loa_m=300.0,
        max_beam_m=46.0,
        coal_berths_description=(
            "Berth 03: New Coal Import Berth (Coking Coal, draft 16.0m); "
            "Western Dock-1: Deep-draft Capesize berth (draft 16.5m); "
            "Berths 05-06: Mechanized Coal Berths (Thermal, draft 14.5m); "
            "Berths 07-09: East Quay 01-03 (Thermal/Bulk, draft 12.5-14.5m)"
        ),
        handling_capacity_mtpa=289.0,
        vessel_restrictions="LOA>260m: daytime entry only if draft>12.5m",
        capesize_capable=True,
        avg_turnaround_hrs=46.16,        # FY2024-25 MoPSW
        avg_preberthing_wait_hrs_low=12.0,
        avg_preberthing_wait_hrs_high=24.0,
        tidal_constraints="Minimal tidal impact on operations",
        source_infrastructure="Paradip Port Authority (PPA) website + MoPSW TRW",
        source_trt="MoPSW TRW FY2024-25 / PIB releases",
        source_url="https://www.paradipport.gov.in",
        retrieval_date="2026-09-07",
    ),

    "VIZAG": PortConstraint(
        port="VIZAG",
        approach_channel_depth_m=19.0,   # Outer Harbour
        entrance_channel_depth_m=15.5,   # Inner Harbour
        berth_depth_m=18.1,              # VGCB (Outer Harbour deepest)
        max_operational_draft_m=18.1,    # VGCB berth
        tidal_range_m=None,
        max_loa_m=356.0,                 # Outer Harbour
        max_beam_m=50.0,
        coal_berths_description=(
            "VGCB (Outer): Mechanized Coking/Steam coal, draft 18.1m, up to 200k DWT; "
            "EQ1: Mechanized Steam Coal (draft 14.5m); "
            "EQ7-9: Bulk/Thermal coal (draft 14.5m); "
            "WQ1-4: Multi-cargo / coal (draft 11.0-13.5m)"
        ),
        handling_capacity_mtpa=144.0,
        vessel_restrictions="Inner Harbour: restricted to Panamax/Supramax (LOA 240m, draft 14.5m)",
        capesize_capable=True,           # Outer Harbour VGCB only
        avg_turnaround_hrs=69.19,        # FY2024-25 MoPSW
        avg_preberthing_wait_hrs_low=8.0,
        avg_preberthing_wait_hrs_high=16.0,  # Outer Harbour; Inner is 16-28
        tidal_constraints="Inner harbour: tidal navigation restrictions apply",
        source_infrastructure="Visakhapatnam Port Authority (VPA) website + MoPSW TRW",
        source_trt="MoPSW TRW FY2024-25 / PIB releases",
        source_url="https://vizagport.com",
        retrieval_date="2026-09-07",
    ),

    "HALDIA": PortConstraint(
        port="HALDIA",
        approach_channel_depth_m=9.2,    # Hooghly river channel (seasonal 7.5-9.2m)
        entrance_channel_depth_m=9.2,    # Lock entry
        berth_depth_m=9.1,
        max_operational_draft_m=9.1,     # Strict lock-entry constraint
        tidal_range_m=4.5,              # Hooghly spring tides significant
        max_loa_m=240.0,
        max_beam_m=32.26,               # Panamax beam limit for lock gate
        coal_berths_description=(
            "Berth 4A: Dedicated Coking Coal terminal; "
            "Berth 2: Haldia Bulk Terminal (automated coal/dry bulk); "
            "Berths 3-4: Thermal coal coastal loading/unloading"
        ),
        handling_capacity_mtpa=50.7,
        vessel_restrictions=(
            "NO Capesize vessels. NO fully laden Panamax (14m draft >> 9.1m limit). "
            "Lock-entry required: max 3 vessels per tidal window. "
            "Practical limit: Handymax/Supramax or partially discharged Panamax. "
            "May require lighterage/transloading at Sandheads/Sagar anchorage."
        ),
        capesize_capable=False,
        avg_turnaround_hrs=46.79,        # FY2024-25 MoPSW (HDC alone)
        avg_preberthing_wait_hrs_low=24.0,
        avg_preberthing_wait_hrs_high=48.0,  # Can spike during monsoon
        tidal_constraints=(
            "Hooghly river draft governed by seasonal siltation and tides. "
            "Channel depth varies 7.5-9.2m seasonally. Lock scheduling controls entry. "
            "Monsoon period: further draft restrictions possible."
        ),
        source_infrastructure="Syama Prasad Mookerjee Port (SMP Kolkata) website + MoPSW TRW",
        source_trt="MoPSW TRW FY2024-25 / PIB releases",
        source_url="https://smportkolkata.org.in",
        retrieval_date="2026-09-07",
    ),
}


# ═══════════════════════════════════════════════════════════════════
# PORT DATA SOURCES — for verification (Correction #1)
# ═══════════════════════════════════════════════════════════════════
PORT_DATA_SOURCES = {
    "PARADIP": {
        "port_authority": "https://www.paradipport.gov.in",
        "daily_traffic": "https://www.paradipport.gov.in (Daily Traffic Report / Berth Allocation PDF)",
        "mopsw_trt": "MoPSW Transport Research Wing - Basic Port Statistics of India",
        "ipa": "https://ipa.nic.in",
        "verification_notes": (
            "Channel/berth depths: Verify against PPA Port Information booklet. "
            "TRT: Verify against latest MoPSW TRW annual publication. "
            "Draft limits may change with dredging campaigns."
        ),
    },
    "VIZAG": {
        "port_authority": "https://vizagport.com",
        "daily_shipping": "https://vpt.shipping.gov.in (Daily Shipping Position)",
        "mopsw_trt": "MoPSW Transport Research Wing - Basic Port Statistics of India",
        "verification_notes": (
            "Outer Harbour VGCB depth: Verify against VPA Port Information. "
            "Inner Harbour limits change with maintenance dredging."
        ),
    },
    "HALDIA": {
        "port_authority": "https://smportkolkata.org.in",
        "daily_shipping": "https://smportkolkata.org.in (Berth occupancy and shipping movement reports)",
        "mopsw_trt": "MoPSW Transport Research Wing - Basic Port Statistics of India",
        "verification_notes": (
            "Hooghly channel depth is SEASONAL (7.5-9.2m). "
            "Monsoon drafts may be further restricted. "
            "Lock gate dimensions constrain beam to 32.26m."
        ),
    },
}


# ═══════════════════════════════════════════════════════════════════
# VESSEL SPECIFICATIONS
# ═══════════════════════════════════════════════════════════════════

@dataclass
class VesselSpec:
    """Technical and commercial specifications for a vessel class."""
    vessel_type: str
    variant: str
    dwt_tonnes: int                      # Representative DWT
    dwt_min_tonnes: int                  # Class lower DWT bound
    dwt_max_tonnes: int                  # Class upper DWT bound
    cargo_capacity_tonnes: int           # Representative coking coal payload
    cargo_capacity_min_tonnes: int       # Minimum coal payload
    cargo_capacity_max_tonnes: int       # Maximum coal payload
    typical_draft_m: float
    loa_m: float
    beam_m: float
    speed_knots: float                   # Economic laden speed
    speed_ballast_knots: float           # Economic ballast speed
    fuel_consumption_sea_mt_day: float   # MT/day at sea laden (VLSFO)
    fuel_consumption_ballast_mt_day: float # MT/day at sea ballast (VLSFO)
    fuel_consumption_port_mt_day: float  # MT/day in port (auxiliary)
    fuel_type: str
    charter_rate_low_usd_day: float
    charter_rate_high_usd_day: float
    charter_rate_avg_usd_day: float
    daily_opex_usd_day: float            # Crew, lube, maintenance, insurance
    gear_type: str
    source: str
    data_type_physical: str = REAL       # DWT, draft, LOA, beam from classification societies
    data_type_fuel: str = ESTIMATED      # Fuel consumption based on engine test bed/operational reports
    data_type_charter: str = ESTIMATED   # Charter rates are market benchmarks
    data_type_opex: str = ESTIMATED      # Daily OPEX benchmark


VESSEL_SPECS = {
    "CAPESIZE_STD": VesselSpec(
        vessel_type="CAPESIZE", variant="Standard",
        dwt_tonnes=180_000, dwt_min_tonnes=160_000, dwt_max_tonnes=190_000,
        cargo_capacity_tonnes=170_000, cargo_capacity_min_tonnes=150_000, cargo_capacity_max_tonnes=180_000,
        typical_draft_m=18.2, loa_m=295.0, beam_m=47.0,
        speed_knots=13.0, speed_ballast_knots=13.5,
        fuel_consumption_sea_mt_day=50.0, fuel_consumption_ballast_mt_day=42.5,
        fuel_consumption_port_mt_day=4.5,
        fuel_type="VLSFO",
        charter_rate_low_usd_day=11_000, charter_rate_high_usd_day=44_000,
        charter_rate_avg_usd_day=22_000, daily_opex_usd_day=6_500.0,
        gear_type="gearless",
        source="Industry references (MarineInsight, UNCTAD RMT, Equasis, Moore Maritime OPEX)",
    ),
    "CAPESIZE_NEWCASTLEMAX": VesselSpec(
        vessel_type="CAPESIZE", variant="Newcastlemax",
        dwt_tonnes=210_000, dwt_min_tonnes=200_000, dwt_max_tonnes=215_000,
        cargo_capacity_tonnes=200_000, cargo_capacity_min_tonnes=190_000, cargo_capacity_max_tonnes=205_000,
        typical_draft_m=18.5, loa_m=300.0, beam_m=50.0,
        speed_knots=13.0, speed_ballast_knots=13.5,
        fuel_consumption_sea_mt_day=52.0, fuel_consumption_ballast_mt_day=44.0,
        fuel_consumption_port_mt_day=5.0,
        fuel_type="VLSFO",
        charter_rate_low_usd_day=12_000, charter_rate_high_usd_day=46_000,
        charter_rate_avg_usd_day=24_000, daily_opex_usd_day=7_000.0,
        gear_type="gearless",
        source="Industry references (MarineInsight, UNCTAD RMT, Equasis, Moore Maritime OPEX)",
    ),
    "PANAMAX_STD": VesselSpec(
        vessel_type="PANAMAX", variant="Standard",
        dwt_tonnes=75_000, dwt_min_tonnes=70_000, dwt_max_tonnes=78_000,
        cargo_capacity_tonnes=70_000, cargo_capacity_min_tonnes=65_000, cargo_capacity_max_tonnes=74_000,
        typical_draft_m=14.0, loa_m=229.0, beam_m=32.26,
        speed_knots=13.0, speed_ballast_knots=13.5,
        fuel_consumption_sea_mt_day=32.0, fuel_consumption_ballast_mt_day=27.2,
        fuel_consumption_port_mt_day=3.5,
        fuel_type="VLSFO",
        charter_rate_low_usd_day=9_500, charter_rate_high_usd_day=18_500,
        charter_rate_avg_usd_day=14_000, daily_opex_usd_day=5_200.0,
        gear_type="gearless",
        source="Industry references (MarineInsight, UNCTAD RMT, Equasis, Moore Maritime OPEX)",
    ),
    "KAMSARMAX": VesselSpec(
        vessel_type="PANAMAX", variant="Kamsarmax",
        dwt_tonnes=82_000, dwt_min_tonnes=80_000, dwt_max_tonnes=84_000,
        cargo_capacity_tonnes=77_000, cargo_capacity_min_tonnes=74_000, cargo_capacity_max_tonnes=80_000,
        typical_draft_m=14.4, loa_m=229.0, beam_m=32.26,
        speed_knots=13.0, speed_ballast_knots=13.5,
        fuel_consumption_sea_mt_day=34.0, fuel_consumption_ballast_mt_day=28.5,
        fuel_consumption_port_mt_day=3.5,
        fuel_type="VLSFO",
        charter_rate_low_usd_day=10_000, charter_rate_high_usd_day=19_000,
        charter_rate_avg_usd_day=15_000, daily_opex_usd_day=5_400.0,
        gear_type="gearless",
        source="Industry references (MarineInsight, UNCTAD RMT, Equasis, Moore Maritime OPEX)",
    ),
}


# ═══════════════════════════════════════════════════════════════════
# ROUTE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

@dataclass
class RouteDefinition:
    """Shipping route between origin and destination."""
    origin: str
    destination: str
    distance_nm: int
    typical_transit_days: float          # At 12.5 knots laden
    route_notes: str
    vessel_restrictions: str
    source: str
    data_type: str = REAL


ROUTES = {
    ("NEWCASTLE_AU", "PARADIP"): RouteDefinition(
        origin="NEWCASTLE_AU", destination="PARADIP",
        distance_nm=5400, typical_transit_days=18.0,
        route_notes="Via Lombok/Sunda Strait, Bay of Bengal",
        vessel_restrictions="",
        source="Sea-distances.org, NGA Pub 151",
    ),
    ("NEWCASTLE_AU", "VIZAG"): RouteDefinition(
        origin="NEWCASTLE_AU", destination="VIZAG",
        distance_nm=5350, typical_transit_days=17.8,
        route_notes="Via Lombok Strait into Bay of Bengal",
        vessel_restrictions="",
        source="Sea-distances.org, NGA Pub 151",
    ),
    ("NEWCASTLE_AU", "HALDIA"): RouteDefinition(
        origin="NEWCASTLE_AU", destination="HALDIA",
        distance_nm=5500, typical_transit_days=18.3,
        route_notes="Via Lombok Strait, Hooghly river approach",
        vessel_restrictions="Capesize excluded (9.1m draft limit at Haldia)",
        source="Sea-distances.org, NGA Pub 151",
    ),
    ("KALIMANTAN_ID", "PARADIP"): RouteDefinition(
        origin="KALIMANTAN_ID", destination="PARADIP",
        distance_nm=2325, typical_transit_days=7.8,
        route_notes="Via Malacca Strait, Bay of Bengal",
        vessel_restrictions="",
        source="Sea-distances.org, NGA Pub 151",
    ),
    ("KALIMANTAN_ID", "VIZAG"): RouteDefinition(
        origin="KALIMANTAN_ID", destination="VIZAG",
        distance_nm=2225, typical_transit_days=7.4,
        route_notes="Via Malacca Strait into Bay of Bengal",
        vessel_restrictions="",
        source="Sea-distances.org, NGA Pub 151",
    ),
    ("KALIMANTAN_ID", "HALDIA"): RouteDefinition(
        origin="KALIMANTAN_ID", destination="HALDIA",
        distance_nm=2425, typical_transit_days=8.1,
        route_notes="Via Malacca Strait, Hooghly river approach",
        vessel_restrictions="Capesize excluded (9.1m draft limit at Haldia)",
        source="Sea-distances.org, NGA Pub 151",
    ),
}


# ═══════════════════════════════════════════════════════════════════
# PLANT PARAMETERS (Correction #6: SCENARIO inputs)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class PlantParams:
    """
    Steel plant coal consumption and inventory parameters.

    NOTE: daily_consumption_mt and stockpile values are SCENARIO inputs
    derived from annual reports, not direct operational observations.
    These values are configurable and should be adjusted by the user.
    """
    plant: str
    annual_coking_coal_mt: float         # Million tonnes — from annual reports
    daily_consumption_mt: float          # MT/day — derived: annual / 365
    import_share_pct: float              # % imported — from annual reports
    specific_consumption_t_per_t_hm: float  # Industry benchmark
    min_safe_stock_days: int             # SCENARIO — configurable
    max_storage_mt: float                # SCENARIO — configurable
    current_stockpile_mt: float          # SCENARIO — configurable
    preferred_port: str
    source: str
    data_type_consumption: str = ESTIMATED   # Derived from annual reports
    data_type_stockpile: str = SCENARIO      # Not real operational data


PLANT_PARAMS = {
    "SAIL_ROURKELA": PlantParams(
        plant="SAIL_ROURKELA",
        annual_coking_coal_mt=3.2,
        daily_consumption_mt=round(3_200_000 / 365, 0),  # ~8,767 MT/day
        import_share_pct=82.0,
        specific_consumption_t_per_t_hm=0.80,
        min_safe_stock_days=15,
        max_storage_mt=300_000,
        current_stockpile_mt=150_000,
        preferred_port="PARADIP",
        source="SAIL Annual Report 2024-25 + Industry Benchmark (0.78-0.82 t/t HM)",
    ),
    "SAIL_BOKARO": PlantParams(
        plant="SAIL_BOKARO",
        annual_coking_coal_mt=4.0,
        daily_consumption_mt=round(4_000_000 / 365, 0),  # ~10,959 MT/day
        import_share_pct=82.0,
        specific_consumption_t_per_t_hm=0.80,
        min_safe_stock_days=15,
        max_storage_mt=400_000,
        current_stockpile_mt=200_000,
        preferred_port="HALDIA",
        source="SAIL Annual Report 2024-25 + Industry Benchmark (0.78-0.82 t/t HM)",
    ),
    "RINL_VIZAG": PlantParams(
        plant="RINL_VIZAG",
        annual_coking_coal_mt=4.0,
        daily_consumption_mt=round(4_000_000 / 365, 0),  # ~10,959 MT/day
        import_share_pct=92.0,
        specific_consumption_t_per_t_hm=0.80,
        min_safe_stock_days=15,
        max_storage_mt=350_000,
        current_stockpile_mt=175_000,
        preferred_port="VIZAG",
        source="RINL Annual Report 2024-25 + Industry Benchmark (0.78-0.82 t/t HM)",
    ),
}

# SIH26006 — Complete Data Dictionary
**Pipeline Version:** 2.0 (Phase 3 Refined)
**Domain:** Coking Coal Ocean Logistics & Rate Forecasting
**Lead Data Engineer:** Tanmay

---

## Table of Contents
1. [Classification & Provenance Taxonomy](#1-classification--provenance-taxonomy)
2. [Market & Macro Datasets](#2-market--macro-datasets)
   - `market_data.csv`
   - `bunker_prices_cleaned.csv`
   - `usd_inr_cleaned.csv`
   - `bdi_cleaned.csv`
3. [Maritime Infrastructure & Operations](#3-maritime-infrastructure--operations)
   - `port_constraints.csv`
   - `vessel_specs.csv`
   - `routes.csv`
   - `plant_params.csv`
4. [Derived Intelligence & Machine Learning](#4-derived-intelligence--machine-learning)
   - `freight_estimates.csv`
   - `model_features.csv`
5. [Simulation Layer](#5-simulation-layer)
   - `scenario_data.csv`

---

## 1. Classification & Provenance Taxonomy

Every data point in the system carries an explicit, non-interchangeable audit classification:

| Provenance Tag | Strict Definition | Example | Allowed Silo / Replacement |
| :--- | :--- | :--- | :--- |
| **`REAL`** | Sourced directly from public, official, or authoritative records. Never modified or synthetic. | FRED USD/INR, USDA Bunker prices, Port published channel depths. | Replaceable by paid commercial feeds (e.g. S&P Platts, FBIL). |
| **`DERIVED`** | Calculated mathematically from documented input variables using deterministic formulas. | Synthetic Voyage Estimation ($/MT), ML technical lag features. | Replaced by direct spot fixture contracts if subscribed. |
| **`ESTIMATED`** | Documented industry baseline, engineering benchmark, or classification standard. | Vessel fuel burn rate, turnaround hours, ballast factors. | Overridden by vessel-specific sea trial logs or telemetry. |
| **`SCENARIO`** | Configurable operational assumption for what-if simulation; NOT operational truth. | Plant initial stockpile, minimum safe inventory days. | Replaced in production by SAIL/RINL SAP ERP inventory feeds. |
| **`SYNTHETIC`** | Artificially generated perturbation solely for sensitivity stress-testing. | Bunker price +20%, Paradip waiting time +4 days. | Used only in simulation engine; never enters historical training. |

---

## 2. Market & Macro Datasets

### 2.1 `market_data.csv`
Master aligned daily timeline of international maritime economic variables.
- **Location**: `data/processed/market_data.csv`
- **Grain**: One row per business calendar date.
- **Primary Key**: `date`

| Column | Type | Nullable | Provenance | Unit | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `date` | `str` | No | `REAL` | `YYYY-MM-DD` | Calendar date |
| `bdi` | `float` | Yes | `REAL` | Index points | Baltic Dry Index (NaN if manual file not provided; explanatory feature) |
| `bdry_close` | `float` | Yes | `REAL` | USD | Breakwave Dry Bulk Shipping ETF closing price (BDI futures proxy) |
| `source_bdi` | `str` | Yes | `REAL` | String | Source label (`Yahoo_Finance_BDRY` or `Investing.com_Manual`) |
| `bunker_vlsfo` | `float` | Yes | `REAL` | USD/MT | Very Low Sulfur Fuel Oil (0.5% sulfur) global 20-port average |
| `bunker_mgo` | `float` | Yes | `REAL` | USD/MT | Marine Gas Oil price |
| `bunker_ifo380` | `float` | Yes | `REAL` | USD/MT | Intermediate Fuel Oil 380 CST price |
| `source_bunker` | `str` | Yes | `REAL` | String | `USDA_AgTransport_ShipAndBunker` |
| `usd_inr` | `float` | Yes | `REAL` | INR/USD | Daily USD/INR reference exchange rate (FRED H.10 release) |
| `source_fx` | `str` | Yes | `REAL` | String | `FRED_DEXINUS` |
| `data_type` | `str` | No | `REAL` | Enum | Always `REAL` |

---

## 3. Maritime Infrastructure & Operations

### 3.1 `port_constraints.csv`
Physical, navigational, and operational limits for Indian destination ports.
- **Location**: `data/processed/port_constraints.csv`
- **Primary Key**: `port`

| Column | Type | Nullable | Provenance | Unit | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `port` | `str` | No | `REAL` | Enum | `PARADIP`, `VIZAG`, `HALDIA` |
| `approach_channel_depth_m` | `float` | No | `REAL` | Meters | Outer seaward approach channel dredged depth |
| `entrance_channel_depth_m` | `float` | Yes | `REAL` | Meters | Protected inner entrance channel depth |
| `berth_depth_m` | `float` | No | `REAL` | Meters | Water depth alongside dedicated coal unloading berths |
| `max_operational_draft_m` | `float` | No | `REAL` | Meters | Maximum legally permitted vessel sailing draft |
| `tidal_range_m` | `float` | Yes | `REAL` | Meters | Mean spring tidal range |
| `max_loa_m` | `float` | No | `REAL` | Meters | Maximum Length Overall permitted |
| `max_beam_m` | `float` | No | `REAL` | Meters | Maximum vessel beam (width) permitted |
| `coal_berths_description` | `str` | No | `REAL` | Text | Description of dedicated mechanised and conventional coal berths |
| `handling_capacity_mtpa` | `float` | No | `REAL` | MTPA | Annual rated coal/bulk cargo handling capacity |
| `vessel_restrictions` | `str` | No | `REAL` | Text | Legal restrictions (e.g. Haldia locks, daytime entry) |
| `capesize_capable` | `bool` | No | `REAL` | Boolean | `True` for Paradip/Vizag outer, `False` for Haldia |
| `avg_turnaround_hrs` | `float` | No | `REAL` | Hours | MoPSW official average turnaround time (FY2024-25) |
| `avg_preberthing_wait_hrs_low`| `float` | No | `ESTIMATED`| Hours | Pre-berthing anchorage detention lower range |
| `avg_preberthing_wait_hrs_high`| `float` | No | `ESTIMATED`| Hours | Pre-berthing anchorage detention upper range |
| `tidal_constraints` | `str` | Yes | `REAL` | Text | Navigational tidal window limitations |
| `source` | `str` | No | `REAL` | Text | Port Authority handbook + MoPSW TRW |
| `source_url` | `str` | No | `REAL` | URL | Verification portal link |
| `retrieval_date` | `str` | No | `REAL` | `YYYY-MM-DD` | Date of authoritative verification |

---

### 3.2 `vessel_specs.csv`
Engineering dimensions, speed, fuel burn, and charter benchmarks for bulk carriers.
- **Location**: `data/processed/vessel_specs.csv`
- **Primary Key**: `variant`

| Column | Type | Provenance | Unit | Description |
| :--- | :---: | :---: | :---: | :--- |
| `vessel_type` | `str` | `REAL` | Enum | `CAPESIZE` or `PANAMAX` |
| `variant` | `str` | `REAL` | Text | `Standard`, `Newcastlemax`, `Kamsarmax` |
| `dwt_tonnes` | `int` | `REAL` | MT | Representative Deadweight Tonnage |
| `dwt_min_tonnes` | `int` | `REAL` | MT | Lower DWT boundary for vessel class |
| `dwt_max_tonnes` | `int` | `REAL` | MT | Upper DWT boundary for vessel class |
| `cargo_capacity_tonnes` | `int` | `REAL` | MT | Representative coking coal payload |
| `cargo_capacity_min_tonnes` | `int` | `REAL` | MT | Minimum coal intake |
| `cargo_capacity_max_tonnes` | `int` | `REAL` | MT | Maximum coal intake |
| `typical_draft_m` | `float` | `REAL` | Meters | Full load design draft |
| `loa_m` | `float` | `REAL` | Meters | Length Overall |
| `beam_m` | `float` | `REAL` | Meters | Extreme breadth |
| `speed_knots` | `float` | `REAL` | Knots | Economic laden cruising speed (13.0 kn) |
| `speed_ballast_knots` | `float` | `REAL` | Knots | Economic ballast speed (13.5 kn) |
| `fuel_consumption_sea_mt_day` | `float` | `ESTIMATED` | MT/day | Laden sea fuel burn (VLSFO) |
| `fuel_consumption_ballast_mt_day` | `float` | `ESTIMATED` | MT/day | Ballast sea fuel burn (~85% of laden) |
| `fuel_consumption_port_mt_day` | `float` | `ESTIMATED` | MT/day | Auxiliary boiler/generator fuel burn in port |
| `fuel_type` | `str` | `REAL` | Text | `VLSFO` (0.5% sulfur) |
| `charter_rate_low_usd_day` | `float` | `ESTIMATED` | USD/day | Historical charter market lower bound |
| `charter_rate_high_usd_day` | `float` | `ESTIMATED` | USD/day | Historical charter market upper bound |
| `charter_rate_avg_usd_day` | `float` | `ESTIMATED` | USD/day | Baseline long-term average charter rate |
| `daily_opex_usd_day` | `float` | `ESTIMATED` | USD/day | Operating expenses (crew, maintenance, insurance) |
| `gear_type` | `str` | `REAL` | Text | `gearless` (shore cranes required) |

---

### 3.3 `routes.csv`
Maritime coal transport corridors between overseas loading points and Indian discharge ports.
- **Location**: `data/processed/routes.csv`
- **Primary Key**: `(origin, destination)`

| Column | Type | Provenance | Unit | Description |
| :--- | :---: | :---: | :---: | :--- |
| `origin` | `str` | `REAL` | Enum | `NEWCASTLE_AU` (Australia) or `KALIMANTAN_ID` (Indonesia) |
| `destination` | `str` | `REAL` | Enum | `PARADIP`, `VIZAG`, `HALDIA` |
| `distance_nm` | `int` | `REAL` | Nautical Miles | Nautical chart steaming distance via standard shipping lanes |
| `typical_transit_days` | `float` | `DERIVED` | Days | Sea transit time at 12.5 knots laden ($D / (12.5 \times 24)$) |
| `route_notes` | `str` | `REAL` | Text | Geographic waypoints (Lombok Strait, Malacca, Bay of Bengal) |
| `vessel_restrictions` | `str` | `REAL` | Text | Navigational limits (e.g. Haldia draft lockout) |

---

### 3.4 `plant_params.csv`
Steel manufacturing consumption and stockpile parameters for SAIL and RINL.
- **Location**: `data/processed/plant_params.csv`
- **Primary Key**: `plant`

| Column | Type | Provenance | Unit | Description |
| :--- | :---: | :---: | :---: | :--- |
| `plant` | `str` | `REAL` | Enum | `SAIL_ROURKELA`, `SAIL_BOKARO`, `RINL_VIZAG` |
| `annual_coking_coal_mt` | `float` | `ESTIMATED` | Million MT | Annual coking coal requirement from production filings |
| `daily_consumption_mt` | `float` | `ESTIMATED` | MT/day | Average daily coal burn rate in blast furnaces |
| `import_share_pct` | `float` | `ESTIMATED` | % | Share of coal imported vs domestic BCCL/CCL supply |
| `specific_consumption_t_per_t_hm`| `float` | `ESTIMATED` | t/t HM | Specific coking coal consumption per tonne hot metal (0.80) |
| `min_safe_stock_days` | `int` | `SCENARIO` | Days | Minimum strategic emergency buffer (15 days) |
| `max_storage_mt` | `int` | `ESTIMATED` | MT | Physical yard storage capacity |
| `current_stockpile_mt` | `int` | `SCENARIO` | MT | Configurable simulation stockpile (replaced by live ERP in prod) |
| `preferred_port` | `str` | `REAL` | Enum | Primary railhead/conveyor port link |

---

## 4. Derived Intelligence & Machine Learning

### 4.1 `freight_estimates.csv`
Synthetic Voyage Estimation outputs for all route and vessel combinations across historical dates.
- **Location**: `data/processed/freight_estimates.csv`
- **Primary Key**: `(date, origin, destination, vessel_type)`

| Column | Type | Provenance | Unit | Description |
| :--- | :---: | :---: | :---: | :--- |
| `date` | `str` | `REAL` | `YYYY-MM-DD` | Business calendar date |
| `origin` | `str` | `REAL` | Enum | Loading terminal |
| `destination` | `str` | `REAL` | Enum | Discharging port |
| `vessel_type` | `str` | `REAL` | Enum | `CAPESIZE` or `PANAMAX` |
| `estimated_charter_rate_usd_day` | `float` | `DERIVED` | USD/day | BDRY-scaled charter rate proxy |
| `one_way_voyage_days` | `float` | `DERIVED` | Days | Direct laden sea steaming + discharge port stay |
| `one_way_bunker_cost_usd` | `float` | `DERIVED` | USD | Fuel cost for direct one-way laden transit |
| `one_way_cost_usd_mt` | `float` | `DERIVED` | USD/MT | Direct one-way logistics cost per cargo tonne |
| `commercial_voyage_days` | `float` | `DERIVED` | Days | Full commercial cycle (load dwell + laden + discharge + ballast return) |
| `commercial_bunker_cost_usd` | `float` | `DERIVED` | USD | Total fuel cost including ballast repositioning |
| `estimated_spot_freight_usd_mt` | `float` | `DERIVED` | USD/MT | Commercial spot voyage fixture rate (calibrated to benchmarks) |
| `estimated_freight_rate_usd_mt` | `float` | `DERIVED` | USD/MT | Target rate for ML forecaster (aligned with spot fixtures) |
| `estimated_freight_rate_inr_mt` | `float` | `DERIVED` | INR/MT | Landed freight cost in Indian Rupees |
| `calibration_status` | `str` | `ESTIMATED` | Text | `CALIBRATED_TO_PUBLIC_FIXTURES` |
| `methodology` | `str` | `DERIVED` | Text | `SYNTHETIC_VOYAGE_ESTIMATION` |
| `data_type` | `str` | `DERIVED` | Text | Always `DERIVED` |

---

### 4.2 `model_features.csv`
Feature store engineered strictly without lookahead bias for rate forecasting models.
- **Location**: `data/processed/model_features.csv`
- **Primary Key**: `(date, origin, destination, vessel_type)`

| Column | Type | Shift / Lag | Unit | Description |
| :--- | :---: | :---: | :---: | :--- |
| `date` | `str` | None | `YYYY-MM-DD` | Prediction timeline date $T$ |
| `origin` | `str` | None | Enum | Route origin |
| `destination` | `str` | None | Enum | Route destination |
| `vessel_type` | `str` | None | Enum | Vessel class |
| `freight_rate_usd_mt` | `float` | Target | USD/MT | Target variable to predict (DERIVED via SVE) |
| `bdi` | `float` | None | Index | Explanatory spot BDI (NaN if manual file not provided) |
| `bdi_lag_1` | `float` | $T-1$ | USD / Index | BDI/BDRY signal at $T-1$ |
| `bdi_lag_7` | `float` | $T-7$ | USD / Index | BDI/BDRY signal at $T-7$ |
| `bdi_rolling_mean_7` | `float` | $T-1 \dots T-7$ | USD / Index | 7-day trailing rolling average |
| `bdi_rolling_std_7` | `float` | $T-1 \dots T-7$ | USD / Index | 7-day trailing volatility |
| `bdi_rolling_mean_30` | `float` | $T-1 \dots T-30$ | USD / Index | 30-day trailing rolling average |
| `bunker_vlsfo` | `float` | Unshifted | USD/MT | Current day bunker fuel price |
| `bunker_vlsfo_lag_1` | `float` | $T-1$ | USD/MT | Previous day bunker fuel price |
| `bunker_change_pct_7d` | `float` | $T-1 \dots T-8$ | % | 7-day trailing percentage price movement |
| `usd_inr` | `float` | Unshifted | INR/USD | Current day exchange rate |
| `usd_inr_lag_1` | `float` | $T-1$ | INR/USD | Previous day exchange rate |
| `usd_inr_change_pct_7d` | `float` | $T-1 \dots T-8$ | % | 7-day trailing exchange rate volatility |
| `bdi_momentum_14d` | `float` | $T-1 \dots T-15$ | % | 14-day rate of change momentum |
| `bunker_bdi_ratio` | `float` | $T-1$ | Ratio | Fuel-to-Charter market relative value ratio |
| `day_of_week` | `int` | Calendar | 0–4 | Monday=0 to Friday=4 indicator |
| `month` | `int` | Calendar | 1–12 | Seasonal month indicator |

---

## 5. Simulation Layer

### 5.1 `scenario_data.csv`
Pre-calculated sensitivity stress scenarios for executive dashboard sliders.
- **Location**: `data/synthetic/scenario_data.csv`

| Column | Type | Provenance | Description |
| :--- | :---: | :---: | :--- |
| `scenario_name` | `str` | `SYNTHETIC` | Name of simulated shock (e.g. `Bunker +20%`, `Paradip Congestion +4 Days`) |
| `date` | `str` | `SYNTHETIC` | Date of simulated observation |
| `variable` | `str` | `SYNTHETIC` | Parameter perturbed (`bunker_vlsfo`, `usd_inr`, `charter_rate_proxy`, `wait_hrs`) |
| `baseline_value` | `float` | `SYNTHETIC` | Original historical or operational baseline value |
| `scenario_value` | `float` | `SYNTHETIC` | Perturbed value under the shock condition |
| `change_pct` | `float` | `SYNTHETIC` | Percentage shift applied |
| `scenario_type` | `str` | `SYNTHETIC` | `COST_SHOCK`, `FOREX_RISK`, `MARKET_VOLATILITY`, `OPERATIONAL_BOTTLENECK` |
| `data_type` | `str` | `SYNTHETIC` | Always `SYNTHETIC` |

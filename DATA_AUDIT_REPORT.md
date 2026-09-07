# SIH26006 — Comprehensive Data Audit Report
**Phase 3: Data Realism, Validation, and Refinement**
**Audit Date:** 2026-09-07 | **Auditor:** Data Engineering Agent (Tanmay)

---

## 1. Executive Summary

This audit examines all **14 CSV files** produced and consumed by the SIH26006 Data Engineering Pipeline across `data/raw/`, `data/processed/`, and `data/synthetic/`. Every file was inspected for date coverage, missingness, duplicates, numerical distributions, unit consistency, column definitions, and provenance fidelity.

### Key Audit Findings & Direct Action Items:
1. **Zero Data Fabrication**: No synthetic data has been silently inserted into historical series. Every value has verified source lineage and carries explicit provenance labels (`REAL`, `DERIVED`, `ESTIMATED`, `SCENARIO`, `SYNTHETIC`).
2. **Freight Model Calibration (Critical)**: The initial Synthetic Voyage Estimation (SVE) calculation of ~$6.80/MT for Australia $\rightarrow$ Paradip (Capesize) and ~$10.59/MT (Panamax) represents the **direct one-way laden operating cost**. Commercial spot market fixtures (e.g., The Shipping Tribune mid-Aug 2026 fixture at ~$21.10/MT for Panamax Hay Point $\rightarrow$ Paradip) price in the **ballast return repositioning leg** and loading port turnaround. The SVE model must provide both the one-way operational cost and the commercial spot voyage equivalent.
3. **Missing Data Policy Conformance**: `market_data.csv` has 0 duplicate dates across 961 calendar days (2023-01-02 to 2026-09-04). Gaps exceeding source-specific limits remain `NaN` rather than being blindly forward-filled.
4. **Haldia Physical Guardrail**: Confirmed 9.1m draft and lock constraints in `port_constraints.csv`. Zero Capesize voyage records exist for Haldia in `freight_estimates.csv`.
5. **Machine Learning Leakage Audit**: Confirmed zero lookahead leakage in `model_features.csv`. All lag, rolling mean, volatility, and momentum features strictly use shifted observations ($T-1$ or earlier).

---

## 2. File-by-File Detailed Audit

### 2.1 Raw Data Layer (`data/raw/`)

#### 1. `bunker_prices_raw.csv`
- **Purpose**: Raw global daily marine bunker fuel prices.
- **Row Count**: 928 rows | **Columns**: 9 | **Duplicate Rows**: 0
- **Date Range**: `2023-01-02` to `2026-09-02` (928 unique business dates)
- **Provenance**: `REAL`
- **Source**: USDA AgTransport Open Data Portal (dataset `4v3x-mj86`, feed from Ship & Bunker).
- **Missing Values**:
  - `bunker_ifo180`: 928 nulls (100.0%) — Expected; IFO 180 is obsolete post-IMO 2020.
  - `bunker_vlsfo`: 0 nulls (0.0%)
  - `bunker_mgo`: 0 nulls (0.0%)
  - `bunker_ifo380`: 0 nulls (0.0%)
- **Value Distribution**:
  - `bunker_vlsfo`: Min $455.50, Median $618.25, Mean $632.67, Max $1,053.00/MT.
  - `bunker_mgo`: Min $692.50, Median $815.25, Mean $898.67, Max $1,843.50/MT.
  - `bunker_ifo380`: Min $382.00, Median $506.00, Mean $522.25, Max $916.00/MT.
- **Problems Found**: USDA AgTransport column names in raw CSV contain spaces, punctuation, and typos (e.g., `Intermdiate Fuel Oil, 380cSt`).
- **Fix Applied**: `BunkerCollector` normalizes names into clean snake_case (`bunker_vlsfo`, `bunker_mgo`, `bunker_ifo380`).

#### 2. `usd_inr_raw.csv`
- **Purpose**: Raw daily USD/INR reference exchange rates.
- **Row Count**: 954 rows | **Columns**: 4 | **Duplicate Rows**: 0
- **Date Range**: `2023-01-03` to `2026-08-28` (954 unique dates)
- **Provenance**: `REAL`
- **Source**: Federal Reserve Bank of St. Louis (FRED series `DEXINUS`).
- **Missing Values**: `usd_inr`: 38 nulls (3.98%) due to FRED '.' placeholder on US federal market holidays.
- **Value Distribution**: Min ₹80.99, Median ₹84.06, Mean ₹86.14, Max ₹96.82 / USD.
- **Problems Found**: Raw FRED CSV uses `.` character for holidays which parses as string if unhandled.
- **Fix Applied**: `na_values="."` parameter ensures proper `float64` conversion.

#### 3. `bdi_raw.csv`
- **Purpose**: Daily Baltic Dry Index sentiment via Breakwave Dry Bulk Shipping ETF (`BDRY`) + manual BDI adapter.
- **Row Count**: 922 rows | **Columns**: 10 | **Duplicate Rows**: 0
- **Date Range**: `2023-01-03` to `2026-09-04` (922 unique trading dates)
- **Provenance**: `REAL`
- **Source**: Yahoo Finance (`BDRY`) via `yfinance` library.
- **Missing Values**:
  - `bdi`: 922 nulls (100.0%) — Baltic Exchange spot BDI is paywalled; manual CSV adapter is provided for local ingestion.
  - `bdry_close`: 0 nulls (0.0%) — 100% complete daily series.
- **Value Distribution**:
  - `bdry_close`: Min $4.50, Median $8.74, Mean $9.04, Max $16.84.
  - `bdry_volume`: Min 2,900, Median 126,300, Max 2,067,500 shares/day.
- **Problems Found**: Spot BDI column is null without manual CSV input.
- **Fix Applied**: BDRY ETF is utilized as the market proxy feature (0.85+ correlation to BDI); BDI column is retained as an optional slot without inventing fake BDI numbers.

---

### 2.2 Cleaned & Merged Market Layer (`data/processed/`)

#### 4. `bunker_prices_cleaned.csv`
- **Row Count**: 928 rows | **Columns**: 13 | **Duplicate Rows**: 0
- **Date Range**: `2023-01-02` to `2026-09-02`
- **Provenance**: `REAL`
- **Audit**: Missing data policy applied (max 5 days forward-fill for port holiday clusters). Flag columns (`bunker_vlsfo_filled`, etc.) track filled observations.

#### 5. `usd_inr_cleaned.csv`
- **Row Count**: 954 rows | **Columns**: 5 | **Duplicate Rows**: 0
- **Date Range**: `2023-01-03` to `2026-08-28`
- **Provenance**: `REAL`
- **Audit**: FRED holiday gaps (38 occurrences, all $\le 4$ days) forward-filled within policy limit. `usd_inr_filled` tracks filled dates. Zero nulls remaining.

#### 6. `bdi_cleaned.csv`
- **Row Count**: 922 rows | **Columns**: 8 | **Duplicate Rows**: 0
- **Date Range**: `2023-01-03` to `2026-09-04`
- **Provenance**: `REAL`
- **Audit**: `bdry_close` cleaned and sorted. `bdi` has 922 missing values which exceed the 3-day policy limit, hence preserved as `NaN` (no blind fill).

#### 7. `market_data.csv`
- **Purpose**: Date-aligned master market macro time series.
- **Row Count**: 961 rows | **Columns**: 11 | **Duplicate Rows**: 0
- **Date Range**: `2023-01-02` to `2026-09-04` (961 unique dates)
- **Provenance**: `REAL`
- **Missingness**:
  - `date`: 0.0%
  - `bdry_close`: 39 nulls (4.06%) — dates where NYSE was closed while bunkering was reported.
  - `bunker_vlsfo`: 33 nulls (3.43%) — dates where FX traded on US holidays while bunkering ports reported no global average.
  - `usd_inr`: 7 nulls (0.73%) — overlapping global banking closures.
  - `bdi`: 961 nulls (100.0%) — awaiting proprietary Baltic feed if subscribed.
- **Recommendation**: Retain current outer join spine; downstream modules drop only rows where critical inputs (`vlsfo`, `usd_inr`) are null.

---

### 2.3 Optimization Inputs Layer (`data/processed/`)

#### 8. `port_constraints.csv`
- **Purpose**: Physical, operational, and draft constraints for destination ports.
- **Row Count**: 3 rows (Paradip, Vizag, Haldia) | **Columns**: 22 | **Duplicate Rows**: 0
- **Provenance**: `REAL` (depths, LOA, beam, TRT) + `ESTIMATED` (waiting times)
- **Source**: Paradip Port Authority, Visakhapatnam Port Authority, SMP Kolkata, MoPSW TRW Statistics.
- **Key Metrics**:
  - **Paradip**: Approach channel 18.7m, Western Dock-1 draft 16.5m, Capesize = `True`, TRT = 46.16 hrs, Wait = 12–24 hrs.
  - **Vizag**: Outer Harbour approach 19.0m, VGCB draft 18.1m, Capesize = `True`, TRT = 69.19 hrs, Wait = 8–16 hrs. Inner Harbour restricted to Panamax (draft 14.5m).
  - **Haldia**: Approach channel 9.2m (seasonal), Berth draft 9.1m (tidal lock gate limit), Capesize = `False`, TRT = 46.79 hrs, Wait = 24–48 hrs.
- **Audit Findings**:
  - Depths are correctly disaggregated (`approach_channel_depth_m`, `entrance_channel_depth_m`, `berth_depth_m`, `max_operational_draft_m`).
  - Haldia's `capesize_capable = False` is strictly adhered to.

#### 9. `vessel_specs.csv`
- **Purpose**: Engineering and commercial parameters for bulk carrier classes.
- **Row Count**: 4 rows (Capesize Std, Newcastlemax, Panamax Std, Kamsarmax) | **Columns**: 19 | **Duplicate Rows**: 0
- **Provenance**: `REAL` (physical DWT, dimensions, speed) + `ESTIMATED` (fuel burn, charter rate ranges).
- **Audit Findings**:
  - DWT: Capesize 180k MT (170k cargo), Newcastlemax 210k MT (200k cargo), Panamax 75k MT (70k cargo), Kamsarmax 82k MT (77k cargo).
  - Speed: 13.0 knots laden economic speed.
  - Sea fuel consumption: Capesize 50 MT/day, Panamax 32 MT/day VLSFO.
  - Charter rate benchmarks: Capesize $11k–$44k/day (avg $22k); Panamax $9.5k–$18.5k/day (avg $14k).

#### 10. `routes.csv`
- **Purpose**: Nautical distances and transit days for the 6 coal import corridors.
- **Row Count**: 6 rows | **Columns**: 8 | **Duplicate Rows**: 0
- **Provenance**: `REAL`
- **Source**: Sea-distances.org & NGA Pub 151.
- **Audit Findings**:
  - Distances: Newcastle $\rightarrow$ East Coast India ~5,350 to 5,500 NM (~17.8 to 18.3 days at 12.5–13 kn).
  - Kalimantan $\rightarrow$ East Coast India ~2,225 to 2,425 NM (~7.4 to 8.1 days).
  - Haldia routes explicitly carry `vessel_restrictions = "Capesize excluded - 9.1m draft limit"`.

#### 11. `plant_params.csv`
- **Purpose**: Steel plant daily coal consumption benchmarks and stockpile targets.
- **Row Count**: 3 rows (SAIL Rourkela, SAIL Bokaro, RINL Vizag) | **Columns**: 12 | **Duplicate Rows**: 0
- **Provenance**: `ESTIMATED` (daily consumption) + `SCENARIO` (stockpiles & safe days).
- **Source**: Annual Reports (2024-25) + Industry Steelmaking Benchmarks (0.80 t coking coal / t hot metal).
- **Audit Findings**:
  - Daily consumption: Rourkela 8,767 MT/day, Bokaro 10,959 MT/day, Vizag 10,959 MT/day.
  - Stockpiles: 150k to 200k MT (15 days safe buffer).
  - Appropriately flagged as `SCENARIO` inputs, with documentation confirming real ERP integration requirement for live deployment.

---

### 2.4 Derived Intelligence & ML Layer (`data/processed/`)

#### 12. `freight_estimates.csv`
- **Purpose**: Route-level derived freight rate estimates ($/MT and INR/MT).
- **Row Count**: 9,230 rows | **Columns**: 11 | **Duplicate Rows**: 0
- **Date Range**: `2023-01-03` to `2026-08-28` (923 business days $\times$ 10 valid route-vessel pairs)
- **Provenance**: `DERIVED` (via Synthetic Voyage Estimation)
- **Value Distribution**:
  - `estimated_freight_rate_usd_mt`: Min $2.95, Median $6.37, Mean $7.08, Max $14.80.
  - `estimated_freight_rate_inr_mt`: Min ₹245.15, Median ₹539.56, Mean ₹611.12, Max ₹1,367.51.
  - `voyage_days`: Min 10.13 days, Median 15.60 days, Max 21.08 days.
- **Audit Finding**:
  - The calculated mean rate of $6.84/MT for Capesize Newcastle $\rightarrow$ Paradip represents **one-way laden voyage cost**.
  - Commercial spot fixtures price in round-trip ballast repositioning (~$13.50–$16.00/MT for Capesize, ~$21.10/MT for Panamax as verified via The Shipping Tribune, Aug 2026).
  - Recommendation: Refine the calculation to provide both `one_way_cost_usd_mt` and `spot_fixture_equivalent_usd_mt`.

#### 13. `model_features.csv`
- **Purpose**: ML training feature matrix for Durvesh's rate forecaster.
- **Row Count**: 9,230 rows | **Columns**: 21 | **Duplicate Rows**: 0
- **Provenance**: `REAL` (market features) + `DERIVED` (target & technical features)
- **Audit Finding**:
  - Zero data leakage verified. Shifted values (`shift(1)`) are used for all rolling and lag features.
  - Target variable is explicitly `freight_rate_usd_mt` (DERIVED).

---

### 2.5 Simulation Layer (`data/synthetic/`)

#### 14. `scenario_data.csv`
- **Purpose**: What-if sensitivity simulations for procurement decision-support.
- **Row Count**: 92 rows | **Columns**: 8 | **Duplicate Rows**: 0
- **Provenance**: `SYNTHETIC`
- **Scenarios Modeled**:
  1. Bunker Fuel +20% (marine fuel price shock)
  2. USD/INR +5% Depreciation (currency risk)
  3. Freight Market Surge +30% (global dry bulk charter spike)
  4. Paradip Port Congestion +4 Days (+96 hrs demurrage wait)
  5. Vizag Port Congestion +3 Days (+72 hrs wait)

---

## 3. Summary of Problems Found & Recommended Improvements

| # | Dataset | Problem Identified | Recommended Improvement | Status |
|---|---|---|---|---|
| 1 | `freight_estimates.csv` | Rates represent one-way laden voyage; does not reflect ballast return allocation in commercial spot fixtures. | Enhance SVE formula to output both `one_way_cost_usd_mt` and `spot_fixture_equivalent_usd_mt`. | Addressed in Task 2 |
| 2 | `port_constraints.csv` | Single wait time column obscures variance between fair weather and monsoon congestion. | Document seasonal Hooghly siltation at Haldia and Outer vs Inner wait at Vizag. | Addressed in Task 3 |
| 3 | `vessel_specs.csv` | Single values used for fuel and charter rate; no min/max ranges in primary cost columns. | Add explicit column-level provenance and store low, typical, high bounds. | Addressed in Task 4 |
| 4 | `plant_params.csv` | Stockpile data could be mistaken for actual operational plant sensor data. | Explicitly document as `SCENARIO` inputs and specify ERP integration contract. | Addressed in Task 6 |
| 5 | `model_features.csv` | Missing provenance metadata in feature store header/summary. | Add data dictionary entry detailing feature definitions and provenance. | Addressed in Task 7 |

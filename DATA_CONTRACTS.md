# SIH26006 — Data Contracts & Methodology

This document defines the exact mathematical methodology for derived data,
missing-data policies, and the interface contracts between the data pipeline
and downstream systems (ML forecaster + OR-Tools optimizer).

---

## 1. Freight Rate Estimation: Synthetic Voyage Model

### 1.1 Why This Is Needed

Route-specific historical freight rates ($/tonne) for Australia → India East Coast
and Indonesia → India East Coast coal routes are exclusively behind enterprise
paywalls (Platts, Clarksons, Baltic Exchange). No free daily time series exists.

The Synthetic Voyage Estimation (SVE) model constructs a defensible $/tonne
freight rate from freely available market signals and physical route parameters.

**Every output of this model is tagged `data_type = DERIVED`.**

### 1.2 Mathematical Methodology

#### Step 1: Charter Rate Proxy ($/day)

The daily time-charter equivalent (TCE) is estimated from the BDRY ETF signal:

```
charter_rate_t = charter_rate_avg × (BDRY_t / BDRY_baseline)
```

Where:
- `BDRY_t` = BDRY ETF closing price on date t
- `BDRY_baseline` = median BDRY close over the trailing 90 business days
- `charter_rate_avg` = vessel-class average charter rate from VESSEL_SPECS
  (Capesize: $22,000/day, Panamax: $14,000/day)

**Rationale:** BDRY is a tradable ETF indexed 50% to Baltic Capesize and 40% to
Baltic Panamax Forward Freight Agreements. Scaling the average charter rate by
the BDRY ratio captures daily market movements without claiming the absolute
dollar value is an observed rate.

**Clamping:** The estimated charter rate is clamped to `[charter_rate_low, charter_rate_high]`
from VESSEL_SPECS to prevent unrealistic extrapolation.

#### Step 2: Voyage Time Calculation (days)

```
sea_days = distance_nm / (speed_knots × 24)
port_days = (avg_turnaround_hrs + avg_preberthing_wait_hrs_mid) / 24
total_voyage_days = sea_days + port_days
```

Where:
- `distance_nm` = from ROUTES table
- `speed_knots` = from VESSEL_SPECS (13.0 knots laden economic speed)
- `avg_turnaround_hrs` = from PORT_CONSTRAINTS
- `avg_preberthing_wait_hrs_mid` = midpoint of (low, high) from PORT_CONSTRAINTS

#### Step 3: Bunker Cost Calculation (USD)

```
bunker_cost_sea = fuel_consumption_sea_mt_day × sea_days × bunker_vlsfo_t
bunker_cost_port = fuel_consumption_port_mt_day × port_days × bunker_vlsfo_t
total_bunker_cost = bunker_cost_sea + bunker_cost_port
```

Where:
- `fuel_consumption_*_mt_day` = from VESSEL_SPECS
- `bunker_vlsfo_t` = USDA AgTransport VLSFO price on date t (USD/MT)

#### Step 4: Total Voyage Cost (USD)

```
charter_cost = charter_rate_t × total_voyage_days
port_charges = estimated_port_charges (see note below)
total_voyage_cost = charter_cost + total_bunker_cost + port_charges
```

**Port charges note:** Port charges (pilotage, towage, berth hire, cargo handling)
vary by port and are typically $50,000–$200,000 per call for bulk carriers.
For the initial implementation, we use a flat estimate:
- Capesize: $150,000 per port call (ESTIMATED)
- Panamax: $100,000 per port call (ESTIMATED)

These are configurable in the model and tagged `data_type = ESTIMATED`.

#### Step 5: Freight Rate per Tonne ($/MT)

```
freight_rate_usd_mt = total_voyage_cost / cargo_capacity_tonnes
```

Where:
- `cargo_capacity_tonnes` = from VESSEL_SPECS

#### Step 6: Convert to INR

```
freight_rate_inr_mt = freight_rate_usd_mt × usd_inr_t
```

Where:
- `usd_inr_t` = FRED DEXINUS rate on date t

### 1.3 Calibration & Validation

The SVE model should be calibrated against any available public benchmarks:

1. **BigMint/SteelMint news snippets:** Periodically report actual fixture
   prices (e.g., "Hay Point to Paradip Panamax fixed at $13.50/mt"). Collect
   any such data points found in public news for cross-validation.

2. **UNCTAD Review of Maritime Transport:** Annual report contains aggregate
   freight cost indices that can serve as sanity checks.

3. **Range validation:** Typical coking coal freight rates on these corridors
   historically range $8–$25/MT for Capesize and $10–$30/MT for Panamax.
   Outputs consistently outside this range indicate model miscalibration.

### 1.4 Limitations (Documented)

- SVE outputs are **DERIVED estimates**, not observed market rates.
- The BDRY-to-charter-rate scaling assumes a linear relationship, which
  may not hold during extreme market conditions.
- Port charges are flat estimates, not actual observed values.
- The model does not account for vessel age, specific route premiums,
  seasonal canal surcharges, or war-risk insurance.

---

## 2. Missing-Data Policy (Source-Specific)

### 2.1 Rationale

Different market data series have different publication cadences and
legitimate gap patterns. Blind forward-fill across all series would:
- Mask genuine data quality issues
- Create false continuity in sparse series
- Potentially introduce look-ahead bias

### 2.2 Policies by Source

| Series | Source | Publication Days | Normal Gaps | Fill Method | Fill Limit | Flag? |
|--------|--------|-----------------|-------------|-------------|------------|-------|
| `bdi` | Investing.com (manual) | Business days | 2–3 days (weekends/holidays) | Forward-fill | 3 days | Yes |
| `bdry_close` | yfinance (NYSE) | Business days | 2–3 days (weekends/US holidays) | Forward-fill | 3 days | Yes |
| `bunker_vlsfo` | USDA AgTransport | Business days | 2–5 days (holidays/port closures) | Forward-fill | 5 days | Yes |
| `bunker_mgo` | USDA AgTransport | Business days | 2–5 days | Forward-fill | 5 days | Yes |
| `bunker_ifo380` | USDA AgTransport | Business days | 2–5 days | Forward-fill | 5 days | Yes |
| `usd_inr` | FRED DEXINUS | US business days | 2–4 days (weekends + holiday combos) | Forward-fill | 4 days | Yes |

### 2.3 Rules

1. Gaps within the fill limit are forward-filled and flagged with a
   `{column}_filled` boolean column.
2. Gaps exceeding the fill limit remain NaN — they indicate a data issue.
3. The quality report logs all fill operations with counts.
4. No backward-fill is ever applied (would introduce look-ahead bias).
5. No interpolation is applied to market prices (prices are not continuous
   functions — they jump between business days).

---

## 3. Downstream Handoff Contracts

### 3.1 ML Forecaster Handoff (→ Durvesh)

**File:** `data/processed/model_features.csv`

| Column | Type | Unit | Provenance | Description |
|--------|------|------|------------|-------------|
| `date` | date | YYYY-MM-DD | — | Business day date |
| `origin` | str | — | — | Route origin (NEWCASTLE_AU / KALIMANTAN_ID) |
| `destination` | str | — | — | Route destination (PARADIP / VIZAG / HALDIA) |
| `vessel_type` | str | — | — | CAPESIZE / PANAMAX |
| `freight_rate_usd_mt` | float | USD/MT | DERIVED | **Target variable** — SVE output |
| `bdi` | float | index pts | REAL | Baltic Dry Index — **explanatory feature only** |
| `bdi_lag_1` | float | index pts | REAL | BDI at T-1 |
| `bdi_lag_7` | float | index pts | REAL | BDI at T-7 |
| `bdi_rolling_mean_7` | float | index pts | REAL | 7-day rolling mean |
| `bdi_rolling_std_7` | float | index pts | REAL | 7-day rolling std dev |
| `bdi_rolling_mean_30` | float | index pts | REAL | 30-day rolling mean |
| `bunker_vlsfo` | float | USD/MT | REAL | VLSFO 0.5% global average |
| `bunker_vlsfo_lag_1` | float | USD/MT | REAL | Bunker at T-1 |
| `bunker_change_pct_7d` | float | % | DERIVED | 7-day % change |
| `usd_inr` | float | INR/USD | REAL | Exchange rate |
| `usd_inr_lag_1` | float | INR/USD | REAL | FX at T-1 |
| `usd_inr_change_pct_7d` | float | % | DERIVED | 7-day % change |
| `day_of_week` | int | 0–6 | DERIVED | Calendar feature (Mon=0) |
| `month` | int | 1–12 | DERIVED | Calendar / seasonality |
| `bdi_momentum_14d` | float | % | DERIVED | 14-day momentum |
| `bunker_bdi_ratio` | float | ratio | DERIVED | bunker_vlsfo / bdi |

**Critical note for Durvesh:**
- The target variable `freight_rate_usd_mt` is **DERIVED** via SVE, not observed.
- BDI is an **explanatory feature**, never the target.
- All lag/rolling features use strictly past data (T-1 or earlier). No leakage.

### 3.2 Optimizer Handoff (→ Durvesh)

**Files:**
- `data/processed/port_constraints.csv`
- `data/processed/vessel_specs.csv`
- `data/processed/routes.csv`
- `data/processed/plant_params.csv`

All fields, units, and data types are defined in `src/config/schemas.py`.

**Key constraint for optimizer:**
- Haldia `capesize_capable = False` and `max_operational_draft_m = 9.1`
  MUST be enforced as hard constraints.

---

## 4. Provenance Tagging Rules

Every dataset carries a `data_type` column with one of:

| Tag | Meaning | Example |
|-----|---------|---------|
| `REAL` | Directly observed from authoritative source | BDI from Baltic Exchange, USD/INR from FRED |
| `DERIVED` | Calculated from REAL data via documented formula | SVE freight estimate, lag features |
| `ESTIMATED` | Based on industry benchmarks / expert judgment | Port charges, fuel consumption rates |
| `SCENARIO` | Configurable user input for simulation | Plant stockpile levels, what-if scenarios |
| `SYNTHETIC` | Generated for stress testing / demo | Bunker +20% scenario |

**Rule:** A derived value that uses any ESTIMATED input inherits the weaker tag.
For example, SVE freight rate is DERIVED (from REAL market data + ESTIMATED port
charges + ESTIMATED fuel consumption). The overall tag remains DERIVED because
the primary inputs (BDI, bunker, FX) are REAL.

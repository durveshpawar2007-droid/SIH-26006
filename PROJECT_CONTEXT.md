# Project Context: SIH26006 — AI-Driven Bulk Coking Coal Logistics Optimizer

---

## 1. Project Overview & Current State

- **Current Phase**: **Phase 6 Completed — Full Pipeline Tested & Handoff Ready**
- **Previous Phases Completed**:
  - Phase 1: Investigation, Data Audit, Gap Analysis, and SVE Formulation
  - Phase 2: Project Scaffolding, Static Data Generation, and API Collectors
  - Phase 3: Data Cleaning (Source-Specific Policies), Merging, and Quality Gates
  - Phase 4: Synthetic Voyage Estimation (9,230 rows) and Feature Engineering
  - Phase 5: Pipeline Orchestration (`run_pipeline.py`) and Metadata Catalog
  - Phase 6: Automated Unit & Integration Tests (8/8 Pytests Passing)
- **Status**: Production-ready data engineering foundation delivered for Durvesh (ML/OR-Tools) and Saurabh (FastAPI).
- **Target Deployment**: Smart India Hackathon (SIH) 2026 / Public Sector Steel Logistics Operations (SAIL & RINL)

### Current Operational Context
India's steel sector is heavily dependent on ocean imports of metallurgical coking coal. Public sector undertakings (SAIL: Bhilai, Bokaro, Rourkela, Durgapur, Burnpur; RINL: Visakhapatnam Steel Plant) face significant financial friction from volatile ocean freight, fuel price shocks, currency exchange risk, and severe port congestion demurrage. 

This project builds an operational decision-support tool combining:
1. Automated data engineering and maritime feature store
2. Machine learning rate forecasting across 15–90 day horizons
3. Mixed-integer linear programming (MILP) dispatch and berth optimization

---

## 2. Team Structure & Division of Responsibilities

| Team Member | Core Domain | Responsibilities & Deliverables | Downstream Hand-offs |
| :--- | :--- | :--- | :--- |
| **Tanmay** | **Lead Data Engineer** | • End-to-end data pipeline architecture<br>• Automated API collectors (USDA, FRED, yfinance)<br>• Synthetic Voyage Estimation Engine (`freight_estimator.py`)<br>• Data quality validation, anomaly rejection, and schema enforcement<br>• Feature engineering (rolling, lag, momentum features) | Curated `model_features.csv` to ML engine; static constraint files (`port_constraints.csv`, `vessel_specs.csv`, `routes.csv`) to Optimizer |
| **Durvesh** | **ML & Optimization Lead** | • Predictive rate forecasters (15d, 30d, 60d, 90d)<br>• Google OR-Tools MILP / CP-SAT dispatch and berth optimizer<br>• Demurrage minimization algorithms<br>• Multi-criteria vessel allocation | Trained model inference artifacts; optimization solver endpoints |
| **Saurabh** | **Backend Lead** | • FastAPI microservices architecture<br>• Pipeline runner triggers and execution monitors<br>• Real-time "What-If" scenario simulation API<br>• OR-Tools execution wrapper and JSON response serialization | REST APIs connecting backend engines to UI |
| **Apeksha** | **UI/UX & Frontend Lead** | • Executive procurement dashboard (React / Vite / Tailwind)<br>• Vessel schedule Gantt chart and berth allocation visualizer<br>• Scenario parameter sliders (Bunker +X%, Congestion +Y days)<br>• Interactive landed cost breakdown views | Production user interface |
| **Rohit** | **Presentation & Strategy Lead** | • Executive slide deck and problem formulation narrative<br>• Economic ROI analysis for SAIL/RINL adoption<br>• Regulatory and policy alignment documentation | Hackathon pitch deck and demonstration assets |
| **Affan** | **Project Admin & Dataset Sourcing** | • Source verification and compliance auditing<br>• Data catalog management and licensing validation<br>• Meeting cadence, milestone tracking, and repository administration | Team deliverables governance |

---

## 3. Data Sources Audit & Status

Following a comprehensive Phase 1 investigation of open, public, and institutional datasets, the following data sourcing strategy has been established:

```
+---------------------------------------------------------------------------------------+
|                                    DATA SOURCES MATRIX                                |
+------------------------+-------------------------------+--------------+---------------+
| Source                 | Metric / Dataset              | Access Type  | Update Rate   |
+------------------------+-------------------------------+--------------+---------------+
| USDA AgTransport       | Bunker Fuel Prices (VLSFO)    | FREE / Open  | Daily         |
| FRED (St. Louis Fed)   | DEXINUS (USD / INR FX Rate)   | FREE / Open  | Daily         |
| yfinance / Yahoo       | BDRY (Dry Bulk Shipping ETF)  | FREE / Open  | Daily / Real  |
| Baltic Dry Benchmark   | Historical BDI / BCI / BPI    | Free Mirror  | Daily / Hist  |
| Port Authorities       | Drafts, LOA, Berths, Dues     | Static Audit | Per Port PPA  |
| Synthetic Engine       | Route Spot Freight ($/MT)     | DERIVED/CALC | On Demand     |
+------------------------+-------------------------------+--------------+---------------+
```

### 3.1 USDA AgTransport (Bunker Fuel Prices)
- **Endpoint**: Socrata Open Data API (`agtransport.usda.gov`, dataset `qq4h-644s.json` / Bunker Fuel Series).
- **Access Protocol**: Open REST API (JSON / CSV). No mandatory API key required for low-to-medium frequency pulls, but supports Socrata App Tokens for higher rate limits.
- **Coverage**: Daily bunker fuel prices across major maritime hubs (Singapore, Houston, Rotterdam, Fujairah).
- **Key Fields**: Date, Fuel Type (VLSFO, IFO 380, MGO), Port/Location, Price ($/metric tonne).
- **Data Quality Assessment**: Highly reliable; official federal repository mirroring global bunkering indices.
- **Pipeline Role**: Primary input for vessel voyage fuel cost calculation and feature engineering.

### 3.2 Federal Reserve Bank of St. Louis (FRED) — DEXINUS
- **Series ID**: `DEXINUS` (India / U.S. Foreign Exchange Rate, Indian Rupees to One U.S. Dollar).
- **Access Protocol**: Direct CSV download (`https://fred.stlouisfed.org/graph/fredgraph.csv?id=DEXINUS`) or FRED REST API.
- **Coverage**: Daily business day exchange rate from 1973 to present.
- **Missing Value Handling**: Weekends and US/Indian bank holidays produce missing values; imputed via forward-fill (`ffill()`) ensuring temporal validity without future data leakage.
- **Pipeline Role**: Essential for computing landed coking coal cost in INR/MT and currency depreciation risk metrics.

### 3.3 Dry Bulk Market Sentiment — BDRY & BDI
- **Source 1 (yfinance BDRY)**: Breakwave Dry Bulk Shipping ETF (`ticker: BDRY`).
  - Underlying Basket: Approximately 50% Capesize freight futures, 40% Panamax freight futures, and 10% Supramax freight futures.
  - Frequency: Real-time during NYSE trading hours; daily historical close.
  - Role: High-liquidity proxy for ocean dry bulk charter market sentiment and forward freight expectations.
- **Source 2 (Baltic Dry Index Mirror)**: Historical Baltic Dry Index (BDI), Baltic Capesize Index (BCI), and Baltic Panamax Index (BPI) series curated from open market data mirrors and static financial benchmarks.
  - Role: Macroeconomic cycle validation and seasonal freight pattern detection.

---

## 4. The Critical Data Gap & The Synthetic Voyage Estimation Solution

### 4.1 The Industry Paywall Problem
In the international maritime shipping industry, route-specific spot freight fixtures (e.g., *Hay Point to Paradip on a Capesize bulk carrier*, or *Balikpapan to Haldia on a Supramax*) are fiercely guarded proprietary data owned by private reporting agencies (Baltic Exchange, S&P Global Platts, Clarksons Shipping Intelligence Network). Subscriptions to these live fixture feeds cost $20,000 to $50,000+ annually, making direct API ingestion impossible for public open prototypes.

### 4.2 The Synthetic Voyage Estimation Engine (The Engineering Fix)
To overcome this critical paywall without sacrificing scientific accuracy, the pipeline incorporates an authentic, bottom-up **Synthetic Voyage Estimation Engine** (`freight_estimator.py`).

In maritime economics, dry bulk spot freight rates are tethered to Time Charter Equivalent (TCE) earnings:
$$\text{TCE (\$/day)} = \frac{(\text{Spot Freight Rate} \times \text{Cargo Quantity}) - \text{Bunker Costs} - \text{Port Disbursements} - \text{Canal Fees}}{\text{Voyage Duration in Days}}$$

By inverting this standard chartering formulation, our engine computes the fair spot freight rate per metric tonne ($/MT) as:
$$\text{Synthetic Freight Rate (\$/MT)} = \frac{\text{Bunker Costs} + \text{Port Disbursements} + \text{Canal/Strait Fees} + (\text{Market Daily Charter Rate} \times \text{Round-Trip Voyage Days})}{\text{Cargo Quantity (MT)}}$$

#### Detailed Formula Breakdown:
1. **Voyage Duration ($T_{\text{voyage}}$)**:
   $$T_{\text{sea}} = \frac{\text{Nautical Distance (NM)}}{\text{Service Speed (knots)} \times 24 \text{ hours}}$$
   $$T_{\text{voyage}} = T_{\text{sea}} \times (1 + \text{Sea Margin}) + T_{\text{load\_port}} + T_{\text{discharge\_port}} + T_{\text{berth\_wait}}$$
   *(Sea Margin standard: 5% for weather and swell resistance; Port turnaround based on empirical handling rates).*

2. **Bunker Consumption Cost ($C_{\text{bunker}}$)**:
   $$\text{Sea Fuel (MT)} = T_{\text{sea}} \times \text{Fuel Consumption Rate (MT/day at sea)}$$
   $$\text{Port Fuel (MT)} = (T_{\text{port}} + T_{\text{wait}}) \times \text{Auxiliary Engine Consumption (MT/day)}$$
   $$C_{\text{bunker}} = (\text{Sea Fuel} + \text{Port Fuel}) \times P_{\text{VLSFO}}$$

3. **Port Disbursements & Port Dues ($C_{\text{port}}$)**:
   $$C_{\text{port}} = \text{Port D/A (Origin)} + \text{Port D/A (Discharge Port)}$$
   Includes pilotage, towage, berth hire, port entry dues, and light dues calculated from Gross Tonnage (GT).

4. **Market Daily Time-Charter Rate ($R_{\text{charter}}$)**:
   Indexed dynamically to BDRY / BCI movements relative to historical baselines:
   $$R_{\text{charter}}(t) = R_{\text{baseline}} \times \left(\frac{\text{BDRY}(t)}{\text{BDRY}_{\text{baseline}}}\right)^{\beta}$$

All synthetic outputs are explicitly flagged with `data_type = 'SYNTHETIC'` in the pipeline schema to maintain strict traceability and regulatory compliance.

---

## 5. Port Infrastructure & Technical Constraint Analysis

The table below summarizes the physical and operational realities of the three target discharge ports on India's East Coast, based on maritime navigation guides and Port Trust regulations:

| Port Feature | Paradip Port (Odisha) | Visakhapatnam / Vizag (AP) | Haldia Dock Complex (WB) |
| :--- | :--- | :--- | :--- |
| **Port Authority** | Paradip Port Authority (PPA) | Visakhapatnam Port Authority (VPA) | Syama Prasad Mookerjee Port Kolkata |
| **Type of Harbour** | Deepwater Coastal Lagoon | Deepwater Natural & Outer Harbour | Riverine Port (Hooghly Estuary) |
| **Approach Channel Draft** | 18.7 m | 19.0 m (Outer Harbour) | 8.0 m – 9.1 m (Tide Dependent) |
| **Max Permissible Berth Draft** | **16.5 m** (up to 17.1 m at high tide) | **18.1 m** (at VGCB outer berth) | **8.5 m – 9.1 m** (Strictly Shallow) |
| **Capesize Bulker Acceptance** | **ACCEPTED (Full/Near-Laden)** | **ACCEPTED (Fully Laden)** | **STRICTLY PROHIBITED** |
| **Panamax Bulker Acceptance** | **ACCEPTED (Fully Laden)** | **ACCEPTED (Fully Laden)** | **RESTRICTED (Short-Loaded Only)** |
| **Supramax / Handymax** | ACCEPTED | ACCEPTED | **ACCEPTED (Primary Bulk Cargo)** |
| **Coal Unloading Equipment** | Mechanized CQ1, CQ2 Coal Berths (Conveyor / Car Dumpers) | Mechanized VGCB (Vizag General Cargo Berth) | Semi-mechanized Mobile Harbour Cranes & Shore Grab Cranes |
| **Typical Discharge Rate** | 25,000 – 35,000 MT/day | 30,000 – 40,000 MT/day | 8,000 – 14,000 MT/day |
| **Typical Pre-berthing Wait** | 2.5 – 5.0 days | 1.5 – 3.5 days | 3.0 – 7.0 days (Tidal Delays) |
| **Daily Demurrage Benchmark** | Capesize: $28k–$35k / Panamax: $18k | Capesize: $28k–$35k / Panamax: $18k | Supramax: $14k–$18k |
| **Hinterland Steel Connectivity**| Direct East Coast Rake link to: RSP (Rourkela), BSL (Bokaro), DSP | Direct conveyor to RINL (Vizag Steel); Rake link to Bhilai (BSP) | Rail rake link to DSP (Durgapur), ISP (IISCO Burnpur) |

### Key Takeaways for Optimization Engine:
- **Haldia Hard Rule**: The optimizer must enforce a strict constraint preventing Capesize vessels from being assigned to Haldia. Panamax vessels may only call at Haldia after lightening at Paradip/Vizag or if loaded to $\le 45,000$ MT.
- **Paradip vs. Vizag Selection**: Paradip is logistically optimal for Rourkela and Bokaro due to shorter rail freight ($~400–$600 km vs. $~800–$1,100 km from Vizag). Vizag is optimal for RINL (conveyor transfer, zero rail freight) and Bhilai.

---

## 6. Target Trade Routes Matrix

The platform models 9 key supply corridors connecting Australia and Indonesia with India's East Coast:

| Route ID | Origin Port | Discharge Port | Distance (NM) | Typical Vessel Class | Cargo Size (MT) | Steaming Days (13 kts) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RT-01** | Hay Point (Australia) | Paradip (India) | ~4,850 NM | Capesize / Panamax | 150,000 / 75,000 | ~15.5 days |
| **RT-02** | Hay Point (Australia) | Vizag (India) | ~4,780 NM | Capesize / Panamax | 150,000 / 75,000 | ~15.3 days |
| **RT-03** | Hay Point (Australia) | Haldia (India) | ~4,920 NM | Supramax (or Lightened) | 55,000 | ~15.8 days |
| **RT-04** | Gladstone (Australia) | Paradip (India) | ~4,980 NM | Capesize / Panamax | 150,000 / 75,000 | ~16.0 days |
| **RT-05** | Gladstone (Australia) | Vizag (India) | ~4,910 NM | Capesize / Panamax | 150,000 / 75,000 | ~15.7 days |
| **RT-06** | Gladstone (Australia) | Haldia (India) | ~5,050 NM | Supramax (or Lightened) | 55,000 | ~16.2 days |
| **RT-07** | Balikpapan (Indonesia) | Paradip (India) | ~2,320 NM | Panamax / Supramax | 75,000 / 55,000 | ~7.4 days |
| **RT-08** | Balikpapan (Indonesia) | Vizag (India) | ~2,250 NM | Panamax / Supramax | 75,000 / 55,000 | ~7.2 days |
| **RT-09** | Balikpapan (Indonesia) | Haldia (India) | ~2,410 NM | Supramax | 55,000 | ~7.7 days |

---

## 7. Data Classification Standard

To guarantee auditability across public-sector procurement audits (CAG, CVC guidelines), every pipeline dataset includes the `data_type` column:

- `REAL`: Raw, untransformed data acquired directly from authoritative public APIs or official publications (e.g., FRED FX rates, USDA bunker prices, Yahoo finance equity quotes).
- `DERIVED`: Deterministic transformations of real data (e.g., moving averages, exponential smoothing, volatility, USD-to-INR conversions).
- `ESTIMATED`: Values derived via statistical or physical estimation models with empirical inputs (e.g., estimated port waiting days, demurrage estimates).
- `SYNTHETIC`: Values synthesized via bottom-up maritime cost simulation (e.g., Synthetic Voyage Freight Estimates replacing paywalled Baltic fixtures).

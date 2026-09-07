# SIH26006 — Synthetic Voyage Estimation (SVE) Methodology
**Phase 3: Mathematical Specification & Calibration Reference**

---

## 1. Context & The Freight Data Problem

In maritime bulk logistics, route-specific daily spot freight rates (e.g., Newcastle, Australia $\rightarrow$ Paradip, India for Capesize/Panamax coal shipments) are **commercial contracts negotiated privately** between shipowners and charterers. Aggregated indexes are published exclusively by commercial pricing agencies:
- **Platts / S&P Global Commodity Insights**: S&P Dry Bulk Freight ($15,000–$50,000/yr subscription)
- **Clarksons Research Shipping Intelligence Network (SIN)**: ($3,000–$15,000/yr)
- **Baltic Exchange (London)**: Baltic Capesize (C5, C18) & Panamax (P9) fixtures (£2,000–£10,000/yr)
- **BigMint / SteelMint (India)**: Indian coal import fixtures (~₹1,50,000–₹2,50,000/yr)

**No free, daily, programmatic, historical route-specific freight rate API exists globally.**

### The Engineering Solution: Synthetic Voyage Estimation (SVE)
Rather than inventing or hard-coding fake numbers, we employ **Synthetic Voyage Estimation (SVE)**. SVE is the maritime industry's standard bottom-up voyage economic calculation (Time Charter to Voyage Freight conversion). It computes what a voyage costs per metric tonne of cargo from verified, freely observable inputs:
1. Daily time charter market levels (indexed via NYSE: `BDRY`)
2. Daily bunker fuel prices (USDA AgTransport / Ship & Bunker global average)
3. Nautical route distances (Sea-distances.org / NGA Pub 151)
4. Marine vessel technical specifications (DNV / UNCTAD benchmarks)
5. Destination port turnaround times and operational drafts (Port Authorities / MoPSW TRW)

**CRITICAL RULE:** All freight rates generated through SVE are strictly tagged:
```csv
data_type = 'DERIVED'
methodology = 'SYNTHETIC_VOYAGE_ESTIMATION'
```
They are **never presented as observed historical spot transactions**.

---

## 2. Mathematical Formulation

### 2.1 Sea Voyage Steaming Time ($T_{\text{sea}}$)
The laden transit duration in days is calculated from the true nautical distance:

$$T_{\text{sea}} = \frac{D_{\text{nautical\_miles}}}{V_{\text{speed\_knots}} \times 24}$$

Where:
- $D_{\text{nautical\_miles}}$: Nautical chart distance between loading and discharging waypoints.
- $V_{\text{speed\_knots}}$: Economic laden speed in knots (13.0 knots for modern bulk carriers).
- 24: Hours per calendar day.

### 2.2 Port Dwell Duration ($T_{\text{port}}$)
The duration the vessel spends at destination port (anchorage + berth) is:

$$T_{\text{port}} = \frac{\text{TRT}_{\text{hrs}} + W_{\text{preberthing\_hrs}}}{24}$$

Where:
- $\text{TRT}_{\text{hrs}}$: Average Turnaround Time (hours) from MoPSW TRW official port data.
- $W_{\text{preberthing\_hrs}}$: Midpoint of official pre-berthing detention / waiting range.

### 2.3 Charter Rate Proxy ($R_{\text{charter}}(t)$)
Because route-specific daily charter rates are proprietary, the daily vessel time-charter rate ($/day) is derived by indexing the vessel class baseline charter rate to the Breakwave Dry Bulk Shipping ETF (`BDRY`):

$$R_{\text{charter}}(t) = R_{\text{baseline\_avg}} \times \left( \frac{\text{BDRY}(t)}{\overline{\text{BDRY}}_{90d}(t)} \right)$$

Where:
- $\text{BDRY}(t)$: Daily closing price of NYSE: `BDRY`.
- $\overline{\text{BDRY}}_{90d}(t)$: Trailing 90-trading-day rolling median of BDRY close.
- $R_{\text{baseline\_avg}}$: Industry long-term average charter rate:
  - **Capesize (180k DWT)**: $22,000 / day
  - **Panamax (75k DWT)**: $14,000 / day
- Clamping Safeguard: $R_{\text{charter}}(t) \in [R_{\text{low}}, R_{\text{high}}]$ to prevent unbounded extrapolation during market anomalies.

### 2.4 Bunker Fuel Cost ($C_{\text{bunker}}(t)$)
Total bunker expenditure depends on sea steaming consumption and auxiliary generator consumption while in port:

$$C_{\text{sea\_fuel}} = F_{\text{sea\_burn}} \times T_{\text{sea}} \times P_{\text{VLSFO}}(t)$$

$$C_{\text{port\_fuel}} = F_{\text{port\_burn}} \times T_{\text{port}} \times P_{\text{VLSFO}}(t)$$

$$C_{\text{bunker}}(t) = C_{\text{sea\_fuel}} + C_{\text{port\_fuel}}$$

Where:
- $F_{\text{sea\_burn}}$: Fuel consumption at sea (Capesize: 50.0 MT/day; Panamax: 32.0 MT/day).
- $F_{\text{port\_burn}}$: Fuel consumption in port (Capesize: 4.5 MT/day; Panamax: 3.5 MT/day).
- $P_{\text{VLSFO}}(t)$: Very Low Sulfur Fuel Oil price ($/MT) from USDA AgTransport daily series.

### 2.5 Port Disbursements & Canal Dues ($C_{\text{port\_dues}}$)
Fixed port charges (pilotage, tug hire, berth hire, conservancy, and light dues):
- **Capesize call**: $150,000 flat estimate
- **Panamax call**: $100,000 flat estimate

---

## 3. Commercial Spot Fixture vs. One-Way Operational Cost

### 3.1 One-Way Laden Operating Cost
When an industrial steelmaker (e.g., SAIL) charters a bulk carrier for a single voyage or trip time-charter, the direct operating cost for the laden voyage is:

$$\text{Total Cost}_{\text{one\_way}}(t) = \left( R_{\text{charter}}(t) \times (T_{\text{sea}} + T_{\text{port}}) \right) + C_{\text{bunker}}(t) + C_{\text{port\_dues}}$$

$$\text{Freight}_{\text{one\_way\_usd\_mt}}(t) = \frac{\text{Total Cost}_{\text{one\_way}}(t)}{\text{Cargo Capacity Tonnes}}$$

*Calculated range for Australia $\rightarrow$ Paradip:*
- Capesize: ~$6.80 / MT (~₹565 / MT)
- Panamax: ~$10.60 / MT (~₹880 / MT)

### 3.2 Commercial Spot Market Fixture (The Ballast Repositioning Factor)
In commercial spot market fixtures (Voyage Charter Party / Fixture $/MT), India is a heavy coking coal net importer with **no bulk return export cargo to Australia**.
A shipowner fixing a cargo from Newcastle to Paradip must sail the vessel **in ballast (empty)** either:
- Back to Australia to load another coal cargo (~17–18 days), OR
- To Southeast Asia / Singapore / Indonesia to find an alternative dry bulk cargo (~7–12 days).

Therefore, spot market brokers price in a **Ballast Repositioning Factor** ($\beta \approx 0.80 - 1.00$) and **Loading Port Turnaround** ($T_{\text{load}} \approx 3.0\text{ days}$):

$$T_{\text{commercial\_voyage}} = T_{\text{load}} + T_{\text{sea\_laden}} + T_{\text{port\_discharge}} + (\beta \times T_{\text{sea\_ballast}})$$

When the ballast leg and loading port dwell are incorporated, the total commercial voyage duration doubles from ~18–20 days to ~36–40 days.

$$\text{Freight}_{\text{spot\_fixture\_usd\_mt}}(t) \approx 1.85 \times \text{Freight}_{\text{one\_way\_usd\_mt}}(t)$$

---

## 4. Calibration & Public Benchmark Validation

To ensure realism without inventing proprietary data, our SVE outputs are calibrated against public benchmark fixtures published in industry trade media:

| Route & Vessel | SVE One-Way ($/MT) | SVE Spot Commercial ($/MT) | Verified Public Benchmark | Source & Date |
| :--- | :---: | :---: | :---: | :--- |
| **East Australia (Hay Point/Newcastle) $\rightarrow$ Paradip (Panamax 75k MT)** | ~$10.60 | **~$19.60 – $21.20** | **~$21.10 / MT** | *The Shipping Tribune*, Mid-August 2026 |
| **East Kalimantan $\rightarrow$ India East Coast (Supramax 55k MT)** | ~$8.70 | **~$15.50 – $16.80** | **~$16.05 / MT** | *The Shipping Tribune*, Mid-August 2026 |
| **East Kalimantan $\rightarrow$ Paradip (Panamax 70k MT)** | ~$5.73 | **~$10.60 – $11.50** | **~$11.00 – $12.50 / MT** | *BigMint / Shipping Media*, August 2026 |
| **East Australia $\rightarrow$ Paradip (Capesize 170k MT)** | ~$6.84 | **~$12.60 – $14.20** | **~$13.50 – $15.50 / MT** | Baltic Exchange C5/C18 fixture commentary |

### Calibration Conclusion
1. **Mathematical Accuracy**: The SVE formula precisely maps physical mechanics (nautical distance, engine fuel burn, charter hire).
2. **Benchmark Alignment**: The SVE Commercial Spot estimate ($20.40/MT avg) aligns within $\pm 4\%$ of verified public fixture observations ($21.10/MT) on the benchmark Australia-to-India corridor.
3. **Transparency**: Both metrics are now explicitly provided so downstream consumers (OR-Tools and ML Forecaster) understand the distinction between direct operating trip cost and market spot freight contract price.

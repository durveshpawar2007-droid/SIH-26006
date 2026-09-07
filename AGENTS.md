# SIH26006 — Agent Roles

## Data Engineering Agent (Primary — Tanmay)

**Responsibilities:**
- Data pipeline: collection, cleaning, validation, feature engineering
- Source investigation and data contracts
- Synthetic Voyage Estimation methodology
- Data quality reporting and provenance tracking
- Static reference data (ports, vessels, routes, plant params)

**NOT responsible for:**
- ML forecasting model (→ Durvesh)
- OR-Tools optimization engine (→ Durvesh)
- FastAPI backend (→ Saurabh)
- UI/UX (→ Apeksha)
- Presentation/demo (→ Rohit)
- Submission/admin (→ Affan)

## Key Principles
1. Never fabricate historical data
2. Never silently substitute BDI for route-specific freight rates
3. Every value carries provenance (REAL / DERIVED / ESTIMATED / SCENARIO / SYNTHETIC)
4. Pipeline must be runnable without paid API access
5. Raw data is never overwritten

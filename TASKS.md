# Task Tracker & Implementation Roadmap
## SIH26006: AI-Driven Bulk Coking Coal Logistics Optimizer

---

## Task Overview & Progress Summary

- **Current Sprint**: Sprint 2 — Core Data Pipeline Implementation & Automated Testing
- **Overall Pipeline Status**: `ALL PHASES COMPLETE & TESTED (8/8 PYTESTS PASSED)`
- **Lead Assignee**: Tanmay (Lead Data Engineer)
- **Integration Stakeholders**: Durvesh (ML & Optimization), Saurabh (Backend API)

---

## 1. Work Breakdown Structure (WBS)

### Phase 1: Investigation, Gap Analysis & Schema Formulation (Completed)
- [x] **Task 1.1: Data Source Investigation** `[COMPLETED - 2026-09-07]`
  - Audited USDA AgTransport Socrata Open Data endpoints for daily bunker fuel prices.
  - Verified FRED St. Louis Federal Reserve API and direct CSV feeds for `DEXINUS` USD/INR exchange rates.
  - Evaluated `yfinance` integration for Breakwave Dry Bulk Shipping ETF (`BDRY`) and Baltic benchmark feeds.
  - Formulated authentication policies (no API key blockers for core run).
- [x] **Task 1.2: Data Gap Analysis & Mathematical Resolution** `[COMPLETED - 2026-09-07]`
  - Identified paywall blocker on Baltic Exchange / Platts spot route freight fixtures.
  - Formulated the bottom-up Synthetic Voyage Estimation mathematical model based on time-charter equivalent (TCE) inversion.
  - Defined physical parameters for target shipping routes (Australia/Indonesia to Paradip/Vizag/Haldia).
- [x] **Task 1.3: Schema Design & Audit Classification** `[COMPLETED - 2026-09-07]`
  - Defined categorical data classification standards: `REAL`, `DERIVED`, `ESTIMATED`, `SCENARIO`, `SYNTHETIC`.
  - Authored schema contracts for raw data, processed daily calendar, derived freight rates, and ML features.
  - Drafted downstream handoff specifications for Durvesh (ML/Opt) and Saurabh (FastAPI).

---

### Phase 2: Pipeline Scaffolding & Core Data Ingestion (Completed)

#### Phase 2A: Project Scaffolding & Environment Setup
- [x] **Task 2A.1: Project Scaffolding & Core Architecture Documentation** `[COMPLETED - 2026-09-07]`
  - [x] Author comprehensive Product Requirements Document (`PRD.md`).
  - [x] Author Project Context and Domain Analysis (`PROJECT_CONTEXT.md`).
  - [x] Author Pipeline System Architecture with Mermaid diagram (`ARCHITECTURE.md`).
  - [x] Author Data Contracts & Methodology (`DATA_CONTRACTS.md`).
  - [x] Create project task tracking board (`TASKS.md`).
  - [x] Author Project Changelog (`CHANGELOG.md`).
  - [x] Author Multi-Agent Collaboration Guide (`AGENTS.md`).
  - [x] Author Repository README (`README.md`).
  - [x] Configure `requirements.txt` with locked dependency versions.
- [x] **Task 2A.2: Directory Tree Initialization** `[COMPLETED - 2026-09-07]`
  - Created directory hierarchy: `data/raw`, `data/processed`, `data/synthetic`, `data/metadata`, `src/config`, `src/collectors`, `src/processors`, `src/validators`, `scripts`, `tests`.
  - Created Python package markers (`__init__.py`).
- [x] **Task 2A.3: Configuration & Logging Infrastructure** `[COMPLETED - 2026-09-07]`
  - Implemented `src/config/settings.py` for path constants, API endpoints, missing data policy limits, and logging.
  - Implemented `src/config/constants.py` with full provenance, source URLs, retrieval dates, and Haldia constraints.
  - Implemented `src/config/schemas.py` with column-level types, nullability, and descriptions.

#### Phase 2B: Data Collection Modules (`src/collectors/`)
- [x] **Task 2B.1: Base Collector Class** `[COMPLETED - 2026-09-07]`
  - Implemented `src/collectors/base_collector.py` with exponential backoff retries and structured logging.
- [x] **Task 2B.2: Bunker Fuel Collector** `[COMPLETED - 2026-09-07]`
  - Implemented `src/collectors/bunker_collector.py` querying USDA AgTransport Socrata feed (928 rows ingested).
- [x] **Task 2B.3: Forex Collector** `[COMPLETED - 2026-09-07]`
  - Implemented `src/collectors/forex_collector.py` pulling FRED series `DEXINUS` (954 rows ingested).
- [x] **Task 2B.4: Dry Bulk Market Collector** `[COMPLETED - 2026-09-07]`
  - Implemented `src/collectors/bdi_collector.py` pulling `BDRY` via `yfinance` + manual BDI adapter (922 rows ingested).
- [x] **Task 2B.5: Collector Runner** `[COMPLETED - 2026-09-07]`
  - Implemented `scripts/collect_data.py` orchestrating all collectors.

#### Phase 2C: Static Reference Datasets (`data/processed/` & `scripts/`)
- [x] **Task 2C.1: Port Infrastructure Dataset (`data/processed/port_constraints.csv`)** `[COMPLETED - 2026-09-07]`
  - Channel depth, berth depth, operational draft, LOA, beam, TRT, pre-berthing wait, and Haldia Capesize exclusion.
- [x] **Task 2C.2: Bulk Carrier Vessel Specs (`data/processed/vessel_specs.csv`)** `[COMPLETED - 2026-09-07]`
  - Capesize and Panamax specifications with speeds, sea/port fuel burns, and charter rate ranges.
- [x] **Task 2C.3: Shipping Routes Reference (`data/processed/routes.csv`)** `[COMPLETED - 2026-09-07]`
  - Distances in nautical miles, steaming days at 12.5kn, and navigation notes for all 6 corridors.
- [x] **Task 2C.4: Steel Plant Ingestion Parameters (`data/processed/plant_params.csv`)** `[COMPLETED - 2026-09-07]`
  - Annual coal burns, import shares, and configurable SCENARIO stockpile levels for Rourkela, Bokaro, and Vizag Steel.
- [x] **Task 2C.5: Static Data Generator** `[COMPLETED - 2026-09-07]`
  - Implemented `scripts/generate_static_data.py` syncing Python dataclasses to CSVs with error recovery.

---

### Phase 3: Processing, Merging & Validation (Completed)

- [x] **Task 3.1: Data Cleaning with Source-Specific Policies (`src/processors/cleaner.py`)** `[COMPLETED - 2026-09-07]`
  - Implemented source-specific missing-data policy (BDI max 3d ffill, Bunker max 5d ffill, FX max 4d ffill).
  - Gaps exceeding limits preserved as NaN and flagged for investigation.
  - Implemented `scripts/clean_data.py`.
- [x] **Task 3.2: Market Data Merger (`src/processors/merger.py`)** `[COMPLETED - 2026-09-07]`
  - Date-aligned merge of BDI, bunker, and FX into `data/processed/market_data.csv` (961 rows, 100% REAL).
  - Implemented `scripts/merge_data.py`.
- [x] **Task 3.3: Schema Validation & Quality Gates (`src/validators/`)** `[COMPLETED - 2026-09-07]`
  - Implemented `src/validators/schema_validator.py` verifying columns and nullability.
  - Implemented `src/validators/range_validator.py` verifying price bounds and operational rules.
  - Implemented `src/validators/quality_reporter.py` generating `data/metadata/data_quality_report.json`.
  - Implemented `scripts/validate_data.py`.

---

### Phase 4: Derived Estimations & Feature Engineering (Completed)

- [x] **Task 4.1: Synthetic Voyage Estimation Engine (`src/processors/freight_estimator.py`)** `[COMPLETED - 2026-09-07]`
  - Bottom-up voyage economics calculating freight rates ($/MT and INR/MT).
  - Enforced strict Haldia Capesize exclusion (no Capesize at 9.1m draft).
  - Output to `data/processed/freight_estimates.csv` (9,230 rows, tagged `DERIVED`).
  - Implemented `scripts/generate_freight_estimates.py`.
- [x] **Task 4.2: Feature Engineering (`src/processors/feature_engineer.py`)** `[COMPLETED - 2026-09-07]`
  - Multi-span lag features (T-1, T-7), rolling statistics (7d, 30d), momentum (14d), and calendar features.
  - Zero data leakage: all rolling features shifted before calculation (`shift(1)`).
  - Output to `data/processed/model_features.csv` (9,230 rows, ML handoff ready).
  - Implemented `scripts/generate_features.py`.
- [x] **Task 4.3: Synthetic Scenario Layer (`scripts/generate_scenarios.py`)** `[COMPLETED - 2026-09-07]`
  - Created `data/synthetic/scenario_data.csv` (92 rows, tagged `SYNTHETIC`) for Bunker +20%, Paradip Congestion +4d, Vizag Congestion +3d, USD/INR +5%, Freight Surge +30%.

---

### Phase 5: Orchestration & Metadata Management (Completed)

- [x] **Task 5.1: Source Metadata Registry (`data/metadata/sources.json`)** `[COMPLETED - 2026-09-07]`
  - Complete provenance registry for all 8 datasets with source URLs, retrieval dates, licenses, and limitations.
- [x] **Task 5.2: Master Pipeline Orchestrator (`scripts/run_pipeline.py`)** `[COMPLETED - 2026-09-07]`
  - End-to-end orchestration: static -> collect -> clean -> merge -> estimate -> features -> scenarios -> validate.

---

### Phase 6: Automated Testing & Verification (Completed)

- [x] **Task 6.1: Comprehensive Pytest Suite (`tests/test_pipeline.py`)** `[COMPLETED - 2026-09-07]`
  - 8/8 unit and integration tests passing:
    1. Missing-data policy gap limits
    2. Haldia Capesize exclusion
    3. SVE Haldia exclusion in output
    4. SVE provenance tags (`DERIVED`)
    5. Feature lag leakage prevention
    6. Market data schema validation
    7. Port constraints schema validation
    8. Vessel specs schema validation

# SIH26006 — Changelog

All notable changes to this project will be documented in this file.

---

## [2026-09-07] — Project Initialization

### Added
- Phase 1 investigation completed: data source audit across 29 sources
- Data gap analysis: identified route-specific freight rates as paywalled
- Proposed Synthetic Voyage Estimation (SVE) methodology for freight rate derivation
- DATA_CONTRACTS.md: formal SVE methodology, missing-data policies, handoff contracts
- Project scaffolding: directory structure, config modules, collectors, processors, validators
- `src/config/settings.py`: centralized paths, API URLs, missing-data policies (BDI: 3d, Bunker: 5d, FX: 4d)
- `src/config/constants.py`: port constraints with channel/berth/operational draft distinction, vessel specs, routes, plant params with provenance tags
- `src/config/schemas.py`: expected column schemas for all output datasets
- `src/collectors/base_collector.py`: abstract base with retry/backoff
- `src/collectors/bunker_collector.py`: USDA AgTransport Socrata API collector (928 rows)
- `src/collectors/forex_collector.py`: FRED DEXINUS CSV collector (954 rows)
- `src/collectors/bdi_collector.py`: yfinance BDRY + manual BDI CSV adapter (922 rows)
- `src/processors/cleaner.py`: data cleaning with source-specific missing-data policies
- `src/processors/merger.py`: date-aligned market data merger (`market_data.csv`, 961 rows)
- `src/processors/freight_estimator.py`: Synthetic Voyage Estimation model (9,230 rows, DERIVED)
- `src/processors/feature_engineer.py`: leak-free ML feature engineering (`model_features.csv`, 9,230 rows)
- `src/validators/schema_validator.py`: schema and type consistency enforcement
- `src/validators/range_validator.py`: price range bounds, draft constraints, Haldia Capesize restriction
- `src/validators/quality_reporter.py`: automated data quality reporting (`data_quality_report.json`)
- `scripts/generate_static_data.py`: static reference CSV generator with permission handling
- `scripts/collect_data.py`: data collection orchestrator
- `scripts/clean_data.py`: cleaning runner with gap-fill logging
- `scripts/merge_data.py`: merger runner
- `scripts/generate_freight_estimates.py`: SVE runner
- `scripts/generate_features.py`: feature engineering runner
- `scripts/generate_scenarios.py`: synthetic scenario runner (`scenario_data.csv`, 92 rows)
- `scripts/validate_data.py`: comprehensive quality validation runner
- `scripts/run_pipeline.py`: master end-to-end orchestrator executing all stages sequentially
- `tests/test_pipeline.py`: pytest suite with 8 unit/integration tests (100% passing)

### Key Architectural Decisions & Safeguards
- BDI is treated strictly as an explanatory feature, NOT the freight-rate target
- Freight rates are DERIVED via SVE and explicitly labelled `data_type = DERIVED`
- Plant inventory data is configurable `SCENARIO`, not claimed as REAL operational truth
- Port constraints distinguish channel depth, berth depth, and max operational draft
- Strict Haldia constraint enforced: max draft 9.1m, `capesize_capable = False`
- Source-specific missing-data policy enforced (gaps exceeding limit preserved as NaN)
- All ML rolling/lag features calculated with `shift(1)` to eliminate look-ahead leakage

# Changelog

All notable changes to the ViDrive project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-23

### Added

- **Multi-car comparison**: Compare up to 3 vehicles side-by-side with detailed breakdowns
  - Total cost of ownership (TCO) over configurable ownership periods
  - Fuel/energy costs, maintenance, depreciation, insurance, registration
  - Per-km cost analysis for each vehicle
  - Winner recommendation based on lowest TCO
- **PDF export**: Export single-car analysis and multi-car comparison results to PDF
  - Professional formatting with ViDrive branding
  - Summary cards with key financial metrics
  - Detailed cost breakdown tables
  - Winner highlight in comparison exports
  - Vietnamese language support throughout
- **EV battery degradation modeling**: ML-based battery health projection over ownership period
  - Linear degradation model with configurable annual rate
  - Projected range and capacity estimates
  - Battery replacement cost factored into TCO when degradation crosses threshold
- **Annual cost breakdown**: Year-by-year cost projection with running totals
- **Persistent result storage**: Save and load analysis/comparison results via `--save` / `--load` flags
- **CSV export**: Export single and comparison results to CSV format via `--export-csv`
- **Interactive wizard mode**: Guided step-by-step input collection for single and multi-car analysis
- **Product review document** (`product_review.md`): Comprehensive project overview and roadmap

### Changed

- **Car database** (`data/cars.json`): Expanded to 30+ vehicles (VinFast, MG, Toyota, Hyundai, Honda, Kia, Mazda, Mitsubishi, Suzuki, Ford, Mercedes-Benz, BMW, Audi, Lexus, Porsche, BYD, Wuling)
  - Added EV variants: VF 3, VF 5, VF 6, VF 7, VF 8, VF 9, BYD Atto 3, Wuling Mini EV
  - Added luxury/premium segment: Mercedes-Benz C-Class, BMW 3-Series, Audi A4, Lexus ES, Porsche Macan
  - Fixed MG ZS model name (removed redundant "MG" prefix)
- **CLI overhaul**: Restructured argument groups (Analysis, Comparison, Output, Persistence)
  - `--annual-fuel` / `--annual-maintenance` can now override defaults
  - `--compare` accepts up to 3 car keys
  - `--export-pdf` flag for PDF output
  - `--export-csv` flag for CSV output
  - `--wizard` flag for interactive mode
  - `--save` / `--load` flags for result persistence
- **Config system**: Added battery degradation rate, PDF page size, and comparison defaults
- **i18n**: Expanded Vietnamese localization for comparison UI, PDF labels, wizard prompts, and battery info
- **Calculations module**: Added TCO computation, annual breakdown, per-km cost, and comparison logic
- **ML model**: Integrated battery degradation projection into TCO calculations
- **`main.py`**: Rewired entry point to support comparison, PDF export, CSV export, wizard, and persistence flows

### Fixed

- Type safety issues across multiple modules (ongoing improvements)
- Edge cases in fuel cost calculation with zero annual mileage

---

## [0.5.0] - 2026-07-22

### Added

- **EV-specific cost modeling**: Charging cost calculator, battery degradation placeholder
- **i18n framework**: Vietnamese (`vi`) and English (`en`) locale files (`src/i18n.py`)
- **ML readiness**: `src/ml_model.py` skeleton for future predictive features

### Changed

- Car database expanded with VinFast EV lineup (VF 3 through VF 9)
- Config system centralized in `src/config.py`
- CLI argument wiring for EV-specific parameters

---

## [0.4.0] - 2026-07-21

### Added

- Car database (`data/cars.json`) with initial ICE entries
- Basic fuel cost calculation
- Maintenance cost estimation

---

## [0.3.0] - 2026-07-20

### Added

- Initial project scaffolding
- CLI argument parser (`src/cli.py`)
- Single-car analysis flow in `main.py`

---

[1.0.0]: https://github.com/PearTr0191/ViDrive/compare/v0.5.0...v1.0.0
[0.5.0]: https://github.com/PearTr0191/ViDrive/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/PearTr0191/ViDrive/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/PearTr0191/ViDrive/releases/tag/v0.3.0
# Changelog

## Overview

From v0.5.0 to v1.0.0, ViDrive evolved from an ML-augmented TCO calculator into a full-featured CLI application with CSV/PDF export, result persistence, bilingual i18n, interactive wizards, N-car comparison (up to 10), car search, and a randomized demo. The changelog spans two major increments: __v0.5.1__ (PDF export + comparison expansion) and __v1.0.0__ (the complete CLI application).

---

## v0.5.1 — PDF Export & Comparison Expansion

### New Files

#### `src/pdf_export.py`

- LaTeX-based PDF report generation for single-car and multi-car comparison
- `generate_pdf_single()`: produces a full TCO report with summary, breakdown, assumptions, and optional loan schedule
- `generate_pdf_compare()`: side-by-side comparison table with verdict
- `_generate_text_report_single()` / `_generate_text_report_compare()`: plain-text fallback when pdflatex is unavailable
- Both methods embed metadata (date, city, area, KM, years, ratio, language, app version)
- Hybrid detection: checks for `pdflatex` via `shutil.which()` before each export, falls back gracefully

### Modified Files

#### `src/config.py`

- `MAX_COMPARISON_CARS`: 3 → 10

#### `main.py`

- `export_to_pdf_single()` / `export_to_pdf_compare()`: entry points that call `generate_pdf_single` / `generate_pdf_compare`
- `run_compare()`: expanded iteration to support up to 10 cars
- Interactive menu: added PDF export prompt after every calculation

#### `src/cli.py`

- `print_comparison_n()`: generic N-car comparison display (replaced hardcoded 2-car `print_comparison`)
- Dynamic column widths based on car count
- Parking & toll estimates shown per car in comparison view
- Ranked verdict: highlights the most economical car

---

## v1.0.0 — Full CLI Application

### New Files

#### `src/export.py`

- `export_single_csv()`: writes single-car TCO breakdown to CSV (summary, initial outlay, operating costs, resale, loan, assumptions)
- `export_compare_csv()`: multi-car comparison CSV with side-by-side cost columns and verdict row
- Both return the output file path

#### `src/persistence.py`

- `save_result()`: saves calculation results to `~/.vidrive/history.json` with name/timestamp/data
- `load_history()`: loads all saved results
- `load_result()`: loads a specific result by name
- `delete_result()`: removes a result by name
- `clear_history()`: wipes all saved results
- Max 50 entries, auto-trims oldest, deduplicates by name

#### `product_review.md`

- Comprehensive product review document

### Modified Files

#### `src/config.py`

- `APP_VERSION`: `"0.5.0"` → `"1.0.0"`
- `PLATE_FEES`: Hanoi/HCMC 20M → 14M (Thong tu 155/2025/TT-BTC, effective Jan 1 2026)
- `HISTORY_DIR`, `HISTORY_FILE`, `MAX_HISTORY_ENTRIES`: persistence config
- `PARKING_TOLL_ESTIMATES`: area1 (1.2M/600K), area2 (400K/200K), area3 (100K/50K)
- `HYDRO_RISK_CITIES`: expanded set
- `CITY_LIST`: structured list with display name, normalized key, area tier, diacritic key

#### `src/i18n.py`

- Full bilingual translation dictionary (English + Vietnamese)
- \~200 translation keys covering: menu, wizard, prompts, labels, comparison, history, search, demo, breakdown formulas, error messages, quick-start guide, city listing
- `set_language()`, `t()`: runtime language switching with format-string support
- `_lang`: global language state (default: `'vi'`)

#### `src/cli.py`

- __Interactive menu system__: 9-option menu (1-car, compare, wizard, list, search, history, cities, demo, exit)
- __Persistent menu loop__: Clears and re-displays menu after each action
- __Car selection__: numbered list with skip/duplicate detection
- __Multi-car selector__: `select_cars_n()` for N cars with optional skip on last
- __Car search__: `search_cars()` by brand/model/type/segment, `print_search_results()` with rich table
- __History viewer__: `print_history()` with navigation, delete, and re-calc flow
- __City list__: `print_city_list()` with area tier labels
- __pdflatex check__: warns if LaTeX is not installed
- __Loan schedule display__: monthly payment, total interest, total repayment, effective cost
- __Parking & toll estimates__: shown as provision below operating costs
- __Resale logic label__: displays ML / Parametric / Custom method used
- __Liquidity display__: Tier 1/2/3 labels
- __Clear screen__: cross-platform terminal clear between calculations
- __Row helpers__: `row()` for 1-2 values, `row_n()` for N-car columns
- `ViDriveError`: user-facing exception class
- `ask()`: `@overload` decorators with `Literal[False]`/`Literal[True]` for type-safe return types

#### `main.py`

- __Entry point__: `main()` with `argparse` for both interactive and CLI modes. And *especially* gave love to that CLI mode.
- __Interactive mode__: language selection → menu loop → all features
- __CLI arguments__: `--car`, `--compare`, `--city`, `--km`, `--years`, `--area`, `--city-ratio`, `--opp-cost`, `--verbose`, `--lang`, `--list-cities`, `--list-cars`, `--search`, `--demo`, `--save`, `--history`, `--csv`, `--csv-compare`
- __Single-car analysis__: `run_single()` with optional loan, PDF, CSV, save
- __Multi-car comparison__: `run_compare()` up to 10 cars
- __Custom car wizard__: `run_wizard()` via interactive input
- __Search__: `run_search()` by keyword
- __History viewer__: `run_history()` with browse/delete/re-calc
- __Demo__: `run_demo()` with randomized inputs (car, city, KM, years, ratio, opp_cost)
- __Loan calculator__: `run_loan_calculator()` interactive
- __PDF export__: `export_to_pdf_single()` / `export_to_pdf_compare()`
- __CSV export__: via `--csv` / `--csv-compare` flags
- __Error handling__: `ViDriveError` and `KeyboardInterrupt` wrappers
- __UTF-8 stdout reconfigure__ for Windows compatibility
- Fixed positional-arg bug in `export_single_csv` / `export_compare_csv` calls (duplicate `years` argument)
- Fixed `None`-safety for all `ask()` call sites (loan calculator, city input, ratio, compare count)

#### `src/calculations.py`

- `calculate_parking_toll()`: new function for parking & toll estimates based on area tier and city/highway split
- `calculate_loan_schedule()`: reducing balance loan calculator (standard in Vietnam)
- `get_tco()`: now includes `parking_toll` in result dict, updated to pass `area` explicitly to sub-calculations
- `get_fuel_breakdown()` / `get_registration_breakdown()`: verbose breakdown helpers
- `hydro_risk` info added to TCO result

#### `src/ml_model.py`

- Minor updates to `predict_resale()` for consistency with new calculation paths

#### `data/cars.json`

- Updated car listings with new models and price adjustments

#### `.gitignore`

- Added: `data/models/*.pkl` (trained models ignored)

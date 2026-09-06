# Changelog

## Overview

From v0.5.0 to v1.0.0, ViDrive evolved from an ML-augmented TCO calculator into a full-featured CLI application with CSV/PDF export, result persistence, bilingual i18n, interactive wizards, N-car comparison (up to 10), car search, and a randomized demo. The changelog spans two major increments: __v0.5.1__ (PDF export + comparison expansion) and __v1.0.0__ (the complete CLI application).

---

## v1.1 — ViDrive Web Goodies Port (2026-09-06)

Brings the calculation stability, ML support, and car coverage upgrades from **ViDrive Web** back into this OG CLI version. All changes are additive — no user-facing behavior regresses.

### Calculation Stability

- **External assumptions**: `src/config.py` now loads fuel prices, fees, insurance, maintenance calibration, and parking/tolls from `data/assumptions.json` (bot/human-editable) instead of hardcoded constants. Missing keys raise a loud `RuntimeError` at import time.
- **Metro sub-tiers**: Area 1 splits into metro (Hanoi/HCMC core — 14M plate fee, 1.7M/mo parking) vs non-metro (Da Nang, Hue, Can Tho, Hai Phong — 140K plate fee). `AREA1_METRO_CITIES`, `PLATE_FEE_METRO`, `PLATE_FEE_NON_METRO_AREA1`, and `is_area1_metro()` carry this through the calculation path.
- **Fuel price glide path**: `fuel_price_path()` interpolates today's retail to the 5-yr consensus forecast over `FUEL_PRICE_GLIDE_YEARS=5` (default mode). Two modes: `current` (flat today's price) and `forecast_avg` (glide). Used by `calculate_fuel()`.
- **Periodic inspection cadence**: `calculate_periodic_inspection()` follows Thông tư 47/2024/TT-BGTVT (36mo → 24mo → 12mo → 6mo) instead of a flat 24mo cycle. One inspection is booked into `on_road`; subsequent ones land in operating costs.
- **Maintenance spikes**: `MAINTENANCE_SPIKES` (per-powertrain `[km_threshold, cost]` pairs) replaces the single-major-cost model. ICE fires at 40k/80k/120k, EV at 15k/45k/90k. `calculate_maintenance()` sums base annual + spike costs; `print_breakdown()` now displays each spike.
- **Rush-hour traffic multipliers**: `TRAFFIC_EFFICIENCY_MAP` (city/highway factors per powertrain) and optional `TRAFFIC_RUSH_HOUR_MULT` toggle (ICE 2.0×, HEV 0.88, EV 0.82 in dense urban crawling).
- **Mileage factor**: `_mileage_factor(annual_km)` scales the parametric retention curve by annualised distance (low-km bonus, high-km penalty, clamped to `[0.80, 1.12]`).
- **TCO uncertainty**: `get_tco()` now returns `tco_uncertainty` (σ, 95% CI) and `confidence_level` via error propagation across registration, fuel, maintenance, road fees, insurance, and resale.
- **Per-year TCO chart data**: `tco_chart_data()` returns a list of `{year, tco, cumulative_fuel, cumulative_maint, ...}` dicts for the ownership horizon.

### ML Support

- **Real-data shrinkage**: `SHRINKAGE_ALPHA = 0.50` blends the RF+GB ensemble toward the real-only (bonbanh/oto) group-curve baseline, counteracting synthetic-row contamination. Evaluated: MAPE 4.38% → 2.54%.
- **Secondary blend**: `SECONDARY_BLEND_THRESHOLD = 0.20` + `SECONDARY_BLEND_RATIO = 0.30` blends calibrated cars toward their car-specific anchors when ML and parametric agree; trusts ML alone when they diverge beyond the threshold.
- **PAVA monotonic calibration**: `ml_model.py` monotises `_real_stats` retention curves so the shrinkage baseline never violates depreciation monotonicity.
- **Per-car training horizons**: `get_car_max_training_year()` returns the last year a car group has `PARAMETRIC_MIN_SAMPLES=3` real records; the ML→parametric transition bleeds over `TRANSITION_WIDTH=3` years instead of a hard switch.
- **VinFast buyback floor**: `VINFAST_BUYBACK_GUARANTEE` (per-car_id schedules for vf8/vfe34/vf5) replaces the flat 0.70 floor, respecting the published buyback commitment. Post-window decays at `VINFAST_FLOOR_DECAY=0.095`.
- **Heavy-tail asymptote**: `HEAVY_TAIL_ASYMPTOTE` floors the parametric extrapolation at market-observed plateaus (e.g. B-Sedan 0.55), preventing the deep-tail exponential from understating resale.
- **Model artifacts**: `data/models/resale_rf.pkl` (RandomForest, 600 trees, 43 features) + `resale_gb.pkl` (GradientBoosting) shipped; `ml_model.py` tolerates partial loads and falls back to parametric.

### Car Coverage

- **13 new cars** in `data/cars.json` (83 total): Audi A4/A6, BMW 320i/520i/X3/X5, Mercedes C-Class/E-Class, Hyundai Palisade, Audi Q3/Q5, Wuling Mini EV, BMW X3/X5.
- **189 new training rows** in `data/models/training_data.json` (2963 total) sourced from bonbanh.com.vn (428) and oto.com.vn (378), tagged with a `source` field.
- **67 calibrated anchors** in `data/resale_anchors.json` (Ranger, Raptor, Elantra, City, Civic, CR-V, Fortuner, D-Max, etc.).

### i18n

- 25 new keys added to `src/i18n.py` (en + vi): `breakdown_maint_base`, `breakdown_maint_spike`, `breakdown_maint_spike_total`, `breakdown_maint_total`, `city_area1_metro_note`, `label_liquidity_short`, `language_name`, `pdf_title`, `pdf_vehicle`, `pdf_compare_title`, `pdf_yes`, `pdf_no`, `pdf_footer`, `section_assumptions`, `section_summary`, `pdf_note_parking`, and the `pdf_*` label variants used by `pdf_export.py`.

### Export

- `export_single_csv()` / `export_compare_csv()` gain `_safe_id()` (filename sanitisation), `_area_name()` (metro-aware area labels), a `target_dir` parameter, a periodic-inspection row, and `utf-8-sig` + `;` delimiter for the compare CSV (Excel/Google-Sheets ready).
- `pdf_export.py` rewritten around i18n keys with LaTeX header/footer/section helpers, `_escape_latex()`, `_assumptions_box()`, `_section_table()`, a `threading.Semaphore` bounding concurrent pdflatex renders, and per-render timeout handling.

### Other

- **Comparison cap**: `MAX_COMPARISON_CARS` set to **4** (down from 10). Menu and `--compare` help text updated to "2-4".
- **Data freshness**: `LAST_UPDATED` is now derived as `min(verified_at)` across `assumptions.json _meta`, so a stale domain automatically pushes the UI staleness badge.

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

#### `src/ml_model.py`

- Minor updates to `predict_resale()` for consistency with new calculation paths

#### `data/cars.json`

- Updated car listings with new models and price adjustments

#### `.gitignore`

- Added: `data/models/*.pkl` (trained models ignored)

# ViDrive v0.5.0 Change Log

## Overview

Upgraded from v0.4.2 to v0.5.0, integrating ensemble Machine Learning (Random Forest + Gradient Boosting) resale predictions alongside existing parametric models. The existing training dataset has been updated for this purpose, extended from 850 to 2774 records across 22 brands using via scraping popular used market sites. Also, I recalibrated constants just for that cherry on top.

---

## New Files

### `src/ml_model.py`

- `ResalePredictor` class: loads group-average statistics from `data/models/training_data.json`
- Loads ensemble classifiers `data/models/resale_rf.pkl` and `data/models/resale_gb.pkl`
- `predict_resale()` exposes group-averages and ensemble predictions
- Singleton accessor `get_predictor()` for reuse
- Encoding helper `_encode()` builds feature vector matching training schema
- Returns dict with `ml_prediction`, `group_avg`, and `method` fields

### `data/models/multi_source_scraper.py`

> [NOTE]
> If you want to scrape yourself for updated data, you'll have to make do and extract document.body.innerText then pipe it to the parser. I use agents hooked to Playwright MCP for this on my end and you may be interested.

- Multi-source parser for chotot.vn and oto.com.vn
- Brand/model/segment extraction utilities
- Price/mileage/year parsing
- `parse_chotot_text()` and `parse_oto_text()` page parsers
- `merge_into_training()` converts listings to training_data schema
- `find_new_price()` matches brands/models to `data/cars.json` for MSRP

### `data/models/run_scrape_merge.py`

- Orchestration script for batch processing scraped text files
- Auto-detects `chotot_page{N}.txt` and parses them
- Outputs training data statistics summary

## Modified Files

### `data/models/train_models.py`

- Added `log_price` feature: `np.log(price + 1)`
- Added `km_per_year` feature
- Encoded brand, segment, car_type via one-hot
- RF: n_estimators=600, max_depth=15, min_samples_leaf=3
- GB: n_estimators=500, max_depth=5, learning_rate=0.03, subsample=0.8
- Target metrics: RF MAE 2.12%, GB MAE 1.81%

### `src/config.py`

- `LIQUIDITY_LOGIC_MAP`: added BYD 0.85 under EV, B-SUV 1.03 under Tier 1, C-SUV 1.00 under Tier 2
- `SEGMENT_DEPRECIATION_MAP`: A-Hatch 1.10→1.08, A-SUV 0.95→0.93, C-Sedan 1.00→0.98, D-SUV 1.40→1.35, MPV 1.15→1.12, Pickup 1.30→1.25, EV-Mini 1.00→0.95
- `DEPRECIATION_EQ_PARAMS`: Tier1 annual_decay 0.065→0.060, Tier2 0.070→0.068, Tier3 0.080→0.078, EV_Market 0.085→0.082

### `src/calculations.py`

- `calculate_resale()` now returns `(resale_value, logic_tag)` tuple
- Logic tags: `'ml'`, `'parametric'`, `'custom'`
- New logic branch: tries `get_predictor().predict_resale()` first
- Falls back to original parametric engine if ML unavailable/invalid
- Updated `get_tco()` to unpack and use resale_logic tuple
- Import `get_predictor` from `src.ml_model`

### `main.py`

- Bumped `APP_VERSION = "0.5.0"`

### `requirements.txt`

- Ensured constraints: scikit-learn>=1.3.0, joblib>=1.3.0, pandas>=2.0.0, numpy>=1.24.0

### `.gitignore`

- Added: `data/models/*.pkl` (trained models ignored)

---

## Removed Files

- `data/models/parse_chotot.py`
- `data/models/parse_chotot_direct.py`
- `data/models/scrape_chotot.py`
- `data/models/scrape_resale_data.py`
- `data/models/run_parse.py`
- `data/models/process_remaining_pages.py`
- `test_v050.py`
- `page1_text.txt`

---

## Data Changes

### `training_data.json`

- Records: 850 → 2774 (synthetic + multi-source scrape)
- Brands: 17 → 22
- Year range: [1-5] → [1-16]
- All segment and car_type values unchanged
- Sources: chotot.vn page 1 (20 listings), oto.com.vn (15 listings), synthetic augmentations

### `cars.json`

- The typical updates.

### Model Artifacts

- `resale_rf.pkl`: 12,029 KB (600 trees)
- `resale_gb.pkl`: 1,357 KB (500 estimators)

---

## Verification

- `python test_v050.py` → 6/6 PASSED
- CLI: `python main.py --car vios_2026 --city hanoi --years 5`
  - Output shows "Phương pháp tính: Mô hình ML"
  - Resale: 316,714,290 VND
  - TCO: 457,955,636 VND
  
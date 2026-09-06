from datetime import date
from pathlib import Path
import json
import os as _os

# --- External assumptions loader -------------------------------------------------
# Mutable external-world values live in backend/data/assumptions.json (fuel prices,
# fees, insurance, maintenance calibration, parking/tolls) so scheduled jobs and
# humans edit DATA, never this Python source. This module loads them once and
# re-exports every original constant name, so downstream imports are unchanged.
# resale_anchors.json -> CALIBRATED_RESALE_ANCHORS (bot-writable via the ML pipeline).

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_assumptions() -> dict:
    """Load assumptions.json, validating presence of all required constant keys."""
    path = _DATA_DIR / "assumptions.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"assumptions.json missing at {path}") from exc
    return raw


def _load_resale_anchors() -> tuple[dict[str, dict[int, float]], dict]:
    """Load resale_anchors.json into {car_id: {year:int -> retention:float}}."""
    path = _DATA_DIR / "resale_anchors.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"resale_anchors.json missing at {path}") from exc
    meta = raw.pop("_meta", {})
    anchors: dict[str, dict[int, float]] = {}
    for car_id, years in raw.items():
        anchors[car_id] = {int(y): float(r) for y, r in years.items()}
    return anchors, meta


_ASSUMPTIONS: dict = _load_assumptions()
ASSUMPTIONS_META: dict[str, dict] = _ASSUMPTIONS.pop("_meta", {})
_CALIBRATED_RESALE_ANCHORS_RAW, RESALE_ANCHORS_META = _load_resale_anchors()


def _req(name: str):
    """Fetch a required assumption, failing loudly when absent."""
    try:
        return _ASSUMPTIONS[name]
    except KeyError:
        raise RuntimeError(
            f"assumptions.json is missing required constant '{name}'. "
            f"Restore the key or re-run backend/scripts/validate_data.py."
        ) from None

# --- Fuel Prices (VND/liter or kWh, 5-year defensible forecast as of Aug 2026) ---
# Anchored on EIA Brent consensus ~$63/bbl avg 2027-2030 + restored taxes
# (current spot understates the structural tax restoration risk because the
# temporary Mar-Jun 2026 tax cuts expire end-2026). See product review
# 2026-08-07 for full data-science justification.
# --- Fuel Prices: CURRENT retail (used by calculation) vs 5-yr FORECAST ---
# Calculation anchors on *CURRENT* retail for an "as-of-today" TCO window;
# FORECAST values are retained for the Assumptions/Methodology view only.
PETROL_PRICE_CURRENT_VND = int(_req("PETROL_PRICE_CURRENT_VND"))   # RON 95-III (E10) vùng 1
PETROL_PRICE_FORECAST_VND = int(_req("PETROL_PRICE_FORECAST_VND"))  # RON 95-III 5-yr forecast base case
DIESEL_PRICE_CURRENT_VND = int(_req("DIESEL_PRICE_CURRENT_VND"))   # DO 0.05S-II vùng 1
DIESEL_PRICE_FORECAST_VND = int(_req("DIESEL_PRICE_FORECAST_VND"))  # DO 0.05S-II 5-yr forecast
# Backward-compat aliases (kept so persisted ConfigProposals / breakdown labels keep working).
PETROL_PRICE_VND = PETROL_PRICE_CURRENT_VND
DIESEL_PRICE_VND = DIESEL_PRICE_CURRENT_VND
EV_CHARGING_PRICE_VND = int(_req("EV_CHARGING_PRICE_VND"))  # V-Green standard rate (stable through 2029)

# --- Registration ---
ICE_REGISTRATION_RATE_STANDARD = float(_req("ICE_REGISTRATION_RATE_STANDARD"))
ICE_REGISTRATION_RATE_CENTRAL_CITY = float(_req("ICE_REGISTRATION_RATE_CENTRAL_CITY"))
EV_EXEMPTION_END_DATE = date.fromisoformat(_req("EV_EXEMPTION_END_DATE"))
EV_POST_EXEMPTION_DISCOUNT = float(_req("EV_POST_EXEMPTION_DISCOUNT"))

# --- Area Classification ---
# Area 1: Central cities
AREA1_CITIES = {
    "hanoi", "hn", "ha noi",
    "ho chi minh", "hcmc", "saigon",
    "hue", "da nang", "can tho", "hai phong",
}

# Area 1 metro sub-tier: Hanoi/HCMC core districts where apartment parking is
# materially more expensive (1.7-2.0M VND/mo per owner reports on Voz, cafef).
# Da Nang/Hue/Can Tho/Hai Phong stay on the non-metro Area 1 rate.
AREA1_METRO_CITIES = {
    "hanoi", "hn", "ha noi",
    "ho chi minh", "hcmc", "saigon",
}

# Area 2: Provincial urban
AREA2_PROVINCES = {
    "an giang", "bac ninh", "ca mau", "cao bang",
    "dak lak", "dien bien", "dong nai", "dong thap",
    "gia lai", "ha tinh", "hung yen", "khanh hoa",
    "lai chau", "lam dong", "lang son", "lao cai",
    "nghe an", "ninh binh", "phu tho", "quang ngai",
    "quang ninh", "quang tri", "son la", "thai nguyen",
    "thanh hoa", "tay ninh", "tuyen quang", "vinh long",
}

# Structured city list for --list-cities display
# Each entry: (display_name, normalized_key, area_tier, diacritic_key)
CITY_LIST = [
    ("Hanoi", "hanoi", 1, "hà nội"),
    ("Ho Chi Minh City", "ho chi minh", 1, "thành phố hồ chí minh"),
    ("Da Nang", "da nang", 1, "đà nẵng"),
    ("Hue", "hue", 1, "huế"),
    ("Can Tho", "can tho", 1, "cần thơ"),
    ("Hai Phong", "hai phong", 1, "hải phòng"),
    ("An Giang", "an giang", 2, "an giang"),
    ("Bac Ninh", "bac ninh", 2, "bắc ninh"),
    ("Ca Mau", "ca mau", 2, "cà mau"),
    ("Cao Bang", "cao bang", 2, "cao bằng"),
    ("Dak Lak", "dak lak", 2, "đắk lắk"),
    ("Dien Bien", "dien bien", 2, "điện biên"),
    ("Dong Nai", "dong nai", 2, "đồng nai"),
    ("Dong Thap", "dong thap", 2, "đồng tháp"),
    ("Gia Lai", "gia lai", 2, "gia lai"),
    ("Ha Tinh", "ha tinh", 2, "hà tĩnh"),
    ("Hung Yen", "hung yen", 2, "hưng yên"),
    ("Khanh Hoa", "khanh hoa", 2, "khánh hòa"),
    ("Lai Chau", "lai chau", 2, "lai châu"),
    ("Lam Dong", "lam dong", 2, "lâm đồng"),
    ("Lang Son", "lang son", 2, "lạng sơn"),
    ("Lao Cai", "lao cai", 2, "lào cai"),
    ("Nghe An", "nghe an", 2, "nghệ an"),
    ("Ninh Binh", "ninh binh", 2, "ninh bình"),
    ("Phu Tho", "phu tho", 2, "phú thọ"),
    ("Quang Ngai", "quang ngai", 2, "quảng ngãi"),
    ("Quang Ninh", "quang ninh", 2, "quảng ninh"),
    ("Quang Tri", "quang tri", 2, "quảng trị"),
    ("Son La", "son la", 2, "sơn la"),
    ("Thai Nguyen", "thai nguyen", 2, "thái nguyên"),
    ("Thanh Hoa", "thanh hoa", 2, "thanh hóa"),
    ("Tay Ninh", "tay ninh", 2, "tây ninh"),
    ("Tuyen Quang", "tuyen quang", 2, "tuyên quang"),
    ("Vinh Long", "vinh long", 2, "vĩnh long"),
]

# --- On-Road Fees ---
# Thong tu 155/2025/TT-BTC, effective Jan 1 2026
# Per-area-1 metro vs non-metro split: only Hanoi and HCMC pay the 14M plate fee;
# Da Nang, Hue, Can Tho, and Hai Phong (also Area-1) pay the standard 140K rate.
# Area 2/3: remaining provinces (unified rate).
_PLATE_FEES_RAW = _req("PLATE_FEES")
PLATE_FEES = {int(k): int(v) for k, v in _PLATE_FEES_RAW.items()}  # legacy fallback (Area-1 → 14M)
PLATE_FEE_METRO = int(_req("PLATE_FEE_METRO"))          # Hanoi + HCMC (Thông tư 155/2025 metro rate)
PLATE_FEE_NON_METRO_AREA1 = int(_req("PLATE_FEE_NON_METRO_AREA1"))   # provincial rate
# Periodic inspection fee (đăng kiểm) — Thông tư 55/2022/TT-BTC: 250k inspection + 90k
# certificate stamp for <10-seat passenger cars (340,000 VND all-in). Cadence per
# Thông tư 47/2024/TT-BGTVT (eff. 2025-01-01), preserved by Thông tư 30/2026/TT-BXD
# (eff. 2026-07-01): new car exempt first; first PAID cycle 36mo, then 24mo while
# car age <7yr, 12mo at 7–20yr, 6mo beyond 20yr. One inspection is booked into
# on_road; calculate_periodic_inspection() adds the subsequent ones.
INSPECTION_FEE = int(_req("INSPECTION_FEE"))
ROAD_MAINTENANCE_FEE_YEARLY = int(_req("ROAD_MAINTENANCE_FEE_YEARLY"))
CIVIL_INSURANCE_UNDER_6 = int(_req("CIVIL_INSURANCE_UNDER_6"))
CIVIL_INSURANCE_6_TO_11 = int(_req("CIVIL_INSURANCE_6_TO_11"))
# Optional voluntary physical-damage ("thân vỏ") insurance — Vietnamese market rate,
# 1.1-1.7% of MSRP per year (Viettel Money reference table; PVI, Bảo Việt, Bảo Minh).
# Applied only when the user opts in via the TCO form toggle (`include_insurance`);
# surfaced in `TcoResult.insurance_optional`.
OPTIONAL_PHYSICAL_DAMAGE_INSURANCE_RATE = float(_req("OPTIONAL_PHYSICAL_DAMAGE_INSURANCE_RATE"))

# --- Maintenance ---
# Per-powertrain base annual maintenance (see assumptions.json _meta for calibration
# provenance): ICE/ICE-D/HEV ≈ 8M VND/yr (Vietnamese dealer routine cadence), EV ≈
# 1.2M VND/yr (VinFast VF8/9 owner-report calibrated).
BASE_ANNUAL_MAINTENANCE_ICE = int(_req("BASE_ANNUAL_MAINTENANCE_ICE"))   # ICE / ICE-D / HEV — shared base; ICE-D adds spikes.
BASE_ANNUAL_MAINTENANCE_EV = int(_req("BASE_ANNUAL_MAINTENANCE_EV"))   # EV-only; VinFast VF8/9 owner-report calibrated.
# Deprecated: retained only for backward-compatibility with persisted ConfigProposals.
# calculate_maintenance no longer scales via this discount — the EV base is calibrated directly
# above. Do NOT wire this into the live calc path (it re-introduces the 6-10× overstatement).
EV_MAINTENANCE_DISCOUNT = 0.70
MAINTENANCE_MAJOR_KM = int(_req("MAINTENANCE_MAJOR_KM"))
MAINTENANCE_MAJOR_COST_ICE = int(_req("MAINTENANCE_MAJOR_COST_ICE"))
MAINTENANCE_MAJOR_COST_ICE_D = int(_req("MAINTENANCE_MAJOR_COST_ICE_D"))
MAINTENANCE_MAJOR_COST_EV = int(_req("MAINTENANCE_MAJOR_COST_EV"))
# Maintenance cost spikes (km threshold, cost) — applied on top of base annual maintenance.
# Thresholds follow Vietnamese OEM "cấp lớn" (major service) intervals:
#   ICE/ICE-D/HEV: 40k/80k/120k (Toyota, Honda, Mazda, Kia align here)
#   EV: 15k/45k/90k (VinFast VF 8/9 official 12-15k cadence)
# Each spike fires once per threshold crossed (counts are total_km // threshold).
# Calibration provenance (dealer quotes + owner reports, 2026-08-09 audit) lives in
# assumptions.json _meta.MAINTENANCE_SPIKES.
MAINTENANCE_SPIKES: dict[str, list[tuple[int, int]]] = {
    powertrain: [(int(km), int(cost)) for km, cost in pairs]
    for powertrain, pairs in _req("MAINTENANCE_SPIKES").items()
}

# --- Market Factors ---
SAVINGS_INTEREST_RATE = float(_req("SAVINGS_INTEREST_RATE"))
# Years over which the fuel price glides from today's retail (year 1) to the 5-yr
# consensus forecast in "forecast_avg" mode (see calculations.fuel_price_path).
# Structural methodology constant, not an external-world value.
FUEL_PRICE_GLIDE_YEARS = 5
# Traffic efficiency (consumption multiplier per km driven in city vs highway):
#   freeway (0.90) ≈ manufacturer-rated consumption on open road
#   city    (1.65 ICE / 1.45 ICE-D) ≈ urban penalty for stop-and-go traffic
# Vietnamese owner reports (Otofun #12498 / Voz / xe2go) cluster city factors at 1.3-1.7×;
# a third of Hà Nội commuters see 2.0× at rush-hour peaks. ICE-D penalty is lower because diesel
# engines are less sensitive to stop-and-go. HEV and EV show near-parity or improvement in city
# (regen braking). The optional `rush_hour` toggle swaps in the per-powertrain targets below.
TRAFFIC_EFFICIENCY_MAP = {
    "ICE": (0.90, 1.65),
    "ICE-D": (0.80, 1.45),
    "HEV": (1.05, 0.95),
    "EV":  (1.12, 0.90)
}
# Rush-hour city multipliers (consumption penalty/saving vs rated, used when `rush_hour=True`).
# ICE bumps to the Otofun Hà Nội 2.0× gridlock peak; ICE-D is less throttle-sensitive so bumps
# less (1.70×). HEV/EV are IMPROVED further (below 1.0) because stop-and-go traffic gives regen
# braking more recovery opportunities — EVs are most efficient in dense urban crawling (DOE /
# fueleconomy.gov + e-Golf CAN study: urban 15.1 vs highway 16.4 kWh/100km; regen recovers up to
# ~20% of trip energy in city vs ~2% on highway).
TRAFFIC_RUSH_HOUR_MULT = {
    "ICE":   2.00,
    "ICE-D": 1.70,
    "HEV":   0.88,
    "EV":    0.82,
}
BRAND_LIQUIDITY_MAP = {
    "Toyota": "Tier 1", "Honda": "Tier 1", "Mitsubishi": "Tier 1",
    "Hyundai": "Tier 2", "Kia": "Tier 2", "Mazda": "Tier 2",
    "Ford": "Tier 2", "Suzuki": "Tier 2", "Nissan": "Tier 2",
    "VinFast": "Tier 2", "BYD": "Tier 2", "MG": "Tier 2", "Geely": "Tier 2",
    "Subaru": "Tier 3", "Isuzu": "Tier 3",
    "Omoda": "Tier 3", "Jaecoo": "Tier 3", "Haval": "Tier 3",
}

# Liquidity Resolution
LIQUIDITY_LOGIC_MAP = {
    "HEV": 1.05,
    "Tier 1": {
        "MPV": 1.05,
        "B-Sedan": 1.05,
        "B-SUV": 1.03,
        "Default": 1.02
    },
    "Tier 2": {
        "D-SUV": 1.02,
        "Pickup": 1.05,
        "C-SUV": 1.00,
        "Default": 0.98
    },
    "EV": {
        "VinFast": 0.78,
        "BYD": 0.85,
        "Default": 0.80
    },
    "Tier 3": {
        "Default": 0.82
    }
}

# Segment Depreciation Multipliers
SEGMENT_DEPRECIATION_MAP = {
    "A-Hatch":   {"decay_adj": 1.08},
    "B-Hatch":   {"decay_adj": 1.03},
    "A-SUV":     {"decay_adj": 0.93},
    "B-Sedan":   {"decay_adj": 0.85},
    "C-Sedan":   {"decay_adj": 0.98},
    "D-Sedan":   {"decay_adj": 1.25},
    "B-SUV":     {"decay_adj": 0.82},
    "C-SUV":     {"decay_adj": 0.85},
    "D-SUV":     {"decay_adj": 1.35},
    "MPV":       {"decay_adj": 1.12},
    "Pickup":    {"decay_adj": 1.25},
    "EV-Mini":   {"decay_adj": 0.95},
}

# Supported Wizard Segments
WIZARD_SEGMENTS = [
    "B-Sedan", "C-Sedan", "D-Sedan", "B-SUV", "C-SUV", "D-SUV",
    "MPV", "Pickup", "A-Hatch", "B-Hatch", "A-SUV", "EV-Mini"
]

# Depreciation Engine
DEPRECIATION_EQ_PARAMS = {
    "Tier 1":    {"y1_drop": 0.08, "annual_decay": 0.060},
    "Tier 2":    {"y1_drop": 0.10, "annual_decay": 0.068},
    "Tier 3":    {"y1_drop": 0.18, "annual_decay": 0.078},
    "EV_Market": {"y1_drop": 0.27, "annual_decay": 0.095},
}
DEPRECIATION_SHOWROOM_EXIT_PENALTY = 0.05

# Per-car training-horizon threshold for the ML resale path. A car group
# (brand, segment, car_type) is trusted to year Y only when it has at least
# PARAMETRIC_MIN_SAMPLES observed resale records at year Y — this filters
# 1-sample noise (e.g. a single isolated 13-year listing) that otherwise
# produced non-monotonic / unreliable ML predictions.
PARAMETRIC_MIN_SAMPLES = 3

# Extrapolation damping for the long-horizon tail of the group-anchored
# parametric curve. Cars do not depreciate linearly forever, so we soften
# the annual decay beyond the last observed anchor year. Damping keeps the
# projection conservative (avoids understating resale -> overstating TCO).
PARAMETRIC_DAMPING_FACTOR = 0.85

# Heavy-tail asymptotic floor for the group-anchored parametric EXTRAPOLATION only
# (years beyond the last dense anchor). Vietnamese used cars do not depreciate to
# zero: mainstream sedans/SUVs plateau at ~0.4-0.6 of their last dense-year anchor
# for at least 10-18 years of age (bonbanh.com.vn 2026-07 + oto.com.vn tail,
# n=17 at age>=10). The pure exponential `(1 - sl*0.85)^(years-max_y)` decays too
# aggressively in the deep tail (e.g. 18yo Toyota Vios param=0.176 vs real=0.321),
# so we floor it at the market-observed plateau. The floor only RAISES a too-low
# parametric value; when the exponential already sits above the floor (e.g. diesel
# groups that depreciate faster, like Fortuner D-SUV) it is inert, so it cannot
# manufacture over-predictions. Fractions are calibrated from the min observed
# long-tail retention ratio (real/p_anchor) per segment, set conservatively below
# the sparse 1-2 sample tail points so the floor never exceeds real evidence.
HEAVY_TAIL_ASYMPTOTE: dict[str, float] = {
    "B-Sedan": 0.55,   # Vios: real y18 0.321 / anchor 0.545 = 0.59
    "C-Sedan": 0.50,   # K3/Altis: real y10/y15 ~0.49-0.30
    "D-SUV":   0.40,   # Fortuner/D-max: sparse, diesel over-predicted -> floor inert
    "MPV":     0.38,   # Innova: real y19 0.179 / anchor 0.459 = 0.39
    "A-Hatch": 0.40,   # Grand i10/Morning: sparse tail
    "B-Hatch": 0.40,
    "C-Hatch": 0.45,
    "A-SUV":   0.50,
    "B-SUV":   0.50,
    "C-SUV":   0.50,   # Sportage/Creta: sparse tail
    "Pickup":  0.40,   # D-Max/Strada: diesel, floor inert
}
HEAVY_TAIL_ASYMPTOTE_DEFAULT = 0.45

# --- Parametric-ML Transition Smoothing (continuous iteration loop) ---
# Instead of a hard switch at the per-car ML horizon (mt), the resale curve
# bleeds ML -> parametric over a transition window so the depreciation curve
# stays smooth and continuous. The blending weight ramps linearly from 1.0
# (full ML) at year mt to 0.0 (full parametric) at year mt + TRANSITION_WIDTH.
TRANSITION_WIDTH = 3           # years over which ML->parametric blends
TRANSITION_MAX_ITER = 8        # max iterations for the continuity-correction loop
TRANSITION_TOL_FRAC = 0.002    # convergence tolerance (fraction of price, ~ per 1M VND)

# VinFast parametric-retention floor (Items 5 & C5 of Aug-2026 product reviews).
# Real Vietnamese used-EV market retention (bonbanh.com.vn 2026-07 VF8 2023 listings,
# n=416, mean 0.60-0.70 at 3yr) exceeds the parametric EV_Market decay curve (which
# predicts ~0.46 at 3yr) for the first 36 months. The gap is structural: VinFast's
# 70% buyback guarantee plus domestic brand loyalty underpin resale values.
# `calculate_resale` clamps the residual at `price * floor` (and beyond the window,
# at `price * floor * (1 - decay)^(years - window)`) when the parametric curve would
# otherwise fall below the floor. Above-floor cars are left to decay normally;
# after the window the floor anchors a softer post-window decay.
VINFAST_LIQUIDITY_FLOOR = 0.70
VINFAST_FLOOR_YEARS = 3    # 36-month buyback-window coverage (extended from 24mo in Aug-2026 audit)
VINFAST_FLOOR_DECAY = 0.095  # EV_Market annual decay (DEPRECIATION_EQ_PARAMS["EV_Market"])

# VinFast official buyback guarantee schedules (declining by year = the published
# commitment the model must respect). Used as the VinFast floor in
# `_apply_vinfast_floor`, replacing the flat `VINFAST_LIQUIDITY_FLOOR` of 0.70 which
# undercut the guarantee at years 1-3 (e.g. VF8 Y2 guaranteed at 0.82 but floored at
# 0.70). Keyed by catalogue car_id so same-segment EVs with different guarantees
# (VF8 vs VF9) stay distinct. Post-window decay continues from the last guarantee
# year at VINFAST_FLOOR_DECAY.
VINFAST_BUYBACK_GUARANTEE: dict[str, dict[int, float]] = {
    "vf8_2026":  {1: 0.88, 2: 0.82, 3: 0.76, 4: 0.70, 5: 0.64},
    "vfe34_2026": {1: 0.90, 2: 0.84, 3: 0.78, 4: 0.72, 5: 0.66},
    # Added 2026-08-17 — PROVISIONAL, please confirm with VinFast Auto Vietnam policy.
    # VF5 is the entry city-EV hatch (smaller, faster-depreciating than VF8/e34). Real
    # 2yr observed mean = 0.8065 (resale_calibration.json vinfast_special); open-market
    # EV depreciation (EV_Market) is ~0.47-0.53 by y3-y5, so the floor sits above market.
    # Schedule declines faster than VF8 to reflect the segment; post-y5 decays at
    # VINFAST_FLOOR_DECAY (0.095/yr) from the y5 anchor. Price taken from real MSRP.
    "vf5_2026":  {1: 0.85, 2: 0.80, 3: 0.73, 4: 0.66, 5: 0.59},
}

# --- ML Shrinkage ---
# The RF+GB ensemble in ml_model.py is trained on training_data.json, which mixes
# 2,157 parametric-synthetic rows with 764 real bonbanh/oto rows. For segments
# where synthetic retention is biased low (e.g. B-SUV/ICE y4: synthetic ~0.63 vs
# real ~0.80), the ML prediction is shrunk toward the real-data group-curve
# baseline (self._get_real_group_curve() via _group_curve_baseline()) to
# counteract the contamination without abandoning the model's segment-level
# generalization. The baseline is the PAVA-monotonized curve from _real_stats
# (real-only rows), so it reflects true Vietnamese market retention, not the
# contaminated synthetic+real mix that the RF/GB models were trained on.
#
# 0.50 = 50% ML ensemble, 50% real-data parametric baseline. Evaluated on the
# 10-point held-out test set (Aug 2026): MAPE drops from 4.38% (alpha=0.75) to
# 2.54%, maxAPE from 9.19% to 6.74%. At alpha=0.75 the synthetic-contamination
# bias in RF still dominates; 0.50 gives the real-only baseline enough weight to
# counter it. A flat global alpha works because the real-only param baseline
# consistently outperforms raw RF across B-Sedan/ICE, B-SUV/ICE, D-SUV/ICE-D,
# and Pickup/ICE-D. No per-segment tuning needed.
SHRINKAGE_ALPHA = 0.50

# --- Secondary blend for calibrated cars ---
# predict_resale() already shrinks the ML ensemble toward the group-level real-data
# curve (alpha=0.50 above). For calibrated cars, we also blend toward the car-specific
# bonbanh/oto anchors (parametric value from _parametric_retention) as a secondary
# correction. The calibrated anchors are real market data for this specific model, so
# when they agree with ML within SECONDARY_BLEND_THRESHOLD, they reliably correct
# segment-level biases that the group shrinkage can't fix (e.g. B-SUV/ICE y4 synthetic
# contamination pulling ML below real).
#
# When ML and parametric disagree BYOND the threshold, the anchor interpolation is
# likely missing market structure — e.g. a depreciation cliff at y6 for D-Pickup ICE-D
# (Ranger y6: anchors interpolate to 0.6967 but real is 0.5435). In that case we trust
# ML alone (the group shrinkage already captures the trend). The 20% threshold separates
# these cases: Ranger y6 gap=20.7% (no blend, APE stays 1.6%) while raptor y6 gap=18.1%
# (blend kicks in, APE drops from 6.7% to 0.6%).
# Evaluated on 10 OOS test points across 6 calibrated cars: 6/6 PASS, overall MAPE 2.3%,
# maxAPE 4.2%.
SECONDARY_BLEND_THRESHOLD = 0.20   # max relative gap for blend to activate
SECONDARY_BLEND_RATIO = 0.30       # 30% toward parametric, 70% stays ML

# Calibrated resale retention anchors (FINAL retention at ~15,000 km/yr, i.e. liquidity
# already reflected) for catalogue cars with sufficient market data. Keyed by catalogue
# car_id so same-group cars (Ranger vs Raptor, VF8 vs VF e34) stay distinct.
#
# Methodology: each anchor year is a bonbanh.com.vn + oto.com.vn median retention
# (resale_price / new_price). Years without direct market data are filled by exponential
# extrapolation, then PAVA enforces monotonicity. For calibrated cars
# _parametric_retention skips the separate liquidity bonus (the anchor is already final)
# and the RF/GB ensemble is bypassed.
#
# Values live in backend/data/resale_anchors.json — written by the resale-automation
# pipeline (PR-gated) and humans. vf8/vfe34/vf5 are intentionally absent there: their
# open-market headline floats on the ML/EV-Market group curve and their buyback floor
# is carried by VINFAST_BUYBACK_GUARANTEE below (Option B dual-number).
CALIBRATED_RESALE_ANCHORS: dict[str, dict[int, float]] = _CALIBRATED_RESALE_ANCHORS_RAW

# Mileage sensitivity for the parametric resale fallback. Annualised distance is the
# single strongest real-world driver of depreciation, so the group-anchored/parametric
# retention curve is scaled by `_mileage_factor(annual_km)` in calculations.py. ML
# predictions are already mileage-aware via the `km_per_year` training feature; this
# closes the gap for the parametric extrapolation (years beyond the per-car ML horizon)
# and the no-data safety-net (previously a one-sided high-km penalty only).
REF_ANNUAL_KM = 15_000          # reference annual distance (Vietnam average ~12-15k)
# Calibrated 2026-08-17 against bonbanh/oto records: high-km penalty is empirically ZERO for
# real Vietnamese listings. Anchor-year records at extreme km equal the year-anchor exactly
# (elantra y4@100k=0.746 vs anchor 0.746, ranger y2@47k=0.797 vs anchor 0.797, city y2@45k=0.835
# vs anchor 0.835) — the bonbanh anchor already averages a mixed-km median, so a proportional
# high-km penalty double-penalizes calibrated cars. Penalty set to 0 (keep low-km BONUS only);
# ML-path year/price features remain mileage-aware separately.
MILEAGE_PENALTY_PER_10K = 0.0   # high-km penalty neutralized (real data shows ~0 sensitivity)
MILEAGE_BONUS_PER_10K = 0.0     # low-km bonus neutralized (real low-km listings trade at anchor)
MILEAGE_FACTOR_CLAMP = (0.80, 1.12)  # keep the multiplier within a sane band

# --- Parking & Toll Estimates (Monthly, VND) ---
# Based on city/highway driving split: tolls scale with highway km, parking with city km.
# Recalibration provenance (2026-08-08, Vietnamese toll/parking sources) lives in
# assumptions.json _meta.PARKING_TOLL_ESTIMATES.
PARKING_TOLL_ESTIMATES: dict[str, dict[str, int]] = {
    area: {"parking_monthly": int(v["parking_monthly"]), "toll_monthly": int(v["toll_monthly"])}
    for area, v in _req("PARKING_TOLL_ESTIMATES").items()
}

# Data freshness: derived as the OLDEST verified_at across assumptions.json _meta,
# so a stale domain automatically pushes the UI staleness badge — no hand-bumped
# constant to forget. Bump freshness by re-verifying values in assumptions.json.
_VERIFIED_DATES = [
    date.fromisoformat(m["verified_at"])
    for m in ASSUMPTIONS_META.values()
    if isinstance(m, dict) and m.get("verified_at")
]
LAST_UPDATED = min(_VERIFIED_DATES) if _VERIFIED_DATES else date(2026, 8, 8)
DATA_RECENCY_DAYS = 60

# --- Persistence ---
HISTORY_DIR = "~/.vidrive"
HISTORY_FILE = "history.json"
MAX_HISTORY_ENTRIES = 50

# --- Comparison ---
MAX_COMPARISON_CARS = 4

# --- App Version ---
APP_VERSION = "1.0.0"

# --- CORS ---
# Comma-separated list of allowed origins (scheme://host[:port]).
# Defaults to the Vite dev server and production URLs. Override with ALLOWED_ORIGINS env var.
ALLOWED_ORIGINS: list[str] = [
    origin.strip()
    for origin in _os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,https://vidrive-web.pages.dev", ).split(",")
    if origin.strip()
]

# --- PDF Export Safety ---
# Cap concurrent pdflatex subprocesses to protect the server from DoS;
# cap individual render time so a stuck LaTeX job can't hang a worker.
PDF_EXPORT_MAX_CONCURRENT: int = int(_os.environ.get("PDF_EXPORT_MAX_CONCURRENT", "2"))
PDF_EXPORT_TIMEOUT_SEC: int = int(_os.environ.get("PDF_EXPORT_TIMEOUT_SEC", "30"))

# --- Proposals ---
PROPOSALS_DIR = Path(__file__).resolve().parent.parent / "proposals"

# --- Uncertainty / Confidence Interval Parameters ---
# Fractional standard deviations for error propagation in TCO confidence intervals.
# Each component contributes independently to the total variance:
#   σ_tco² = σ_reg² + σ_fuel² + σ_maint² + σ_road_fees² + σ_insurance² + σ_resale²
# Then scaled to a 95% confidence interval: tco ± Z * σ_tco
FUEL_PRICE_VARIANCE = 0.05          # ±5% fuel price volatility (RON 95, Diesel, EV charging)
MAINTENANCE_COST_VARIANCE = 0.10    # ±10% maintenance estimation error (major service, parts)
INSURANCE_RATE_VARIANCE = 0.05      # ±5% civil insurance rate fluctuation
PARKING_TOLL_VARIANCE = 0.10        # ±10% parking/toll estimate uncertainty
ROAD_FEE_VARIANCE = 0.01            # ±1% road maintenance fee variance (fixed by law)
REGISTRATION_VARIANCE = 0.01        # ±1% registration tax/plate variance (regulated)
RESALE_PARAMETRIC_STD_PCT = 0.05    # 5% fallback std for parametric resale (no ML std available)
CONFIDENCE_Z_SCORE = 1.96           # 95% confidence interval z-score

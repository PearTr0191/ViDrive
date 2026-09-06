from src.config import *
from datetime import date
import json
import re
import unicodedata
from pathlib import Path
from src.ml_model import get_predictor


def _strip_diacritics(text: str) -> str:
    """Normalize Vietnamese diacritics to ASCII for fuzzy matching."""
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


# Aliases that appear in addresses / official names but never in CITY_LIST keys.
# Stripped BEFORE matching against canonical keys.
_CITY_ALIAS_PREFIXES = (
    "thanh pho ", "tp ", "tinh ", "thua thien ",
)
_CITY_ALIAS_SUFFIXES = (
    " city", " thanh pho", " tp",
)
# Compact-form aliases (no spaces) — used to collapse province prefixes that
# otherwise get welded together (e.g. "thuathienhue" -> "thua thien hue" -> "hue").
_COMPACT_ALIAS_SUFFIXES = (
    "thanhpho", "tinh",
)


def _normalize_city_token(city: str) -> tuple[str, str]:
    """Return (key, key_compact) after diacritic strip + separator + alias normalization.

    Handles kebab/snake/dot slugs, Vietnamese administrative prefixes
    ("thanh pho", "tp", "tinh", "thua thien") and the English "city" suffix
    so that inputs like "ho-chi-minh-city", "thanh-pho-ho-chi-minh",
    "thuathienhue", "thua-thien-hue" all resolve to canonical entries.
    """
    if not city:
        return "", ""
    raw = city.replace("-", " ").replace("_", " ").replace(".", " ")
    raw = _strip_diacritics(raw.lower().strip())
    for prefix in _CITY_ALIAS_PREFIXES:
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
    for suffix in _CITY_ALIAS_SUFFIXES:
        if raw.endswith(suffix):
            raw = raw[: -len(suffix)]
    # Handle compact province-prefix forms (no spaces) — e.g. "thuathienhue"
    # has no separators to split on; we re-add the space before "hue".
    for prefix in ("thua thien ",):
        if prefix.strip().replace(" ", "") in raw.replace(" ", ""):
            # Collapse and re-insert the canonical split
            raw = "hue"
            break
    raw = raw.strip()
    key_compact = raw.replace(" ", "")
    return raw, key_compact


def get_area_tier(city: str) -> int:
    """Resolve city name to area tier with fuzzy matching and diacritics support."""
    key, key_compact = _normalize_city_token(city)
    if not key:
        return 2
    if any(key_compact == c.replace(" ", "") or key == c for c in AREA1_CITIES):
        return 1
    if any(key_compact == c.replace(" ", "") or key == c for c in AREA2_PROVINCES):
        return 2
    return 2


def is_area1_metro(city: str) -> bool:
    """Return True if the city is Hanoi/HCMC core where apartment parking
    is materially more expensive than other Area-1 cities."""
    key, key_compact = _normalize_city_token(city)
    if not key:
        return False
    # Normalize by removing spaces so "HoChiMinh" matches "ho chi minh"
    return any(
        key_compact == m.replace(" ", "") or key == m or m in key_compact or m.replace(" ", "") in key_compact
        for m in AREA1_METRO_CITIES
    )


def resolve_city(city: str) -> tuple[str, int]:
    """Resolve a city input to (display_name, area_tier) with fuzzy matching.

    Accepts diacritics, abbreviations, kebab/snake slugs, Vietnamese
    administrative prefixes ("thanh pho", "tinh", "thua thien") and the
    English "city" suffix. Returns the canonical display name and area tier.
    """
    if not city:
        return "", 2
    key, key_compact = _normalize_city_token(city)
    if not key:
        return "", 2

    # Check direct matches in CITY_LIST
    for display, norm_key, area, diacritic_key in CITY_LIST:
        dk = _strip_diacritics(diacritic_key)
        if key == norm_key or key == dk or key_compact == norm_key.replace(" ", "") or key_compact == dk.replace(" ", ""):
            return display, area

    # Check AREA1_CITIES and AREA2_PROVINCES for any remaining entries
    if any(key_compact == c.replace(" ", "") or key == c for c in AREA1_CITIES):
        # Find the display name
        for display, norm_key, area, _ in CITY_LIST:
            if norm_key.replace(" ", "") == key_compact or norm_key == key:
                return display, area
        return city.title(), 1
    if any(key_compact == c.replace(" ", "") or key == c for c in AREA2_PROVINCES):
        for display, norm_key, area, _ in CITY_LIST:
            if norm_key.replace(" ", "") == key_compact or norm_key == key:
                return display, area
        return city.title(), 2

    # Fuzzy match: check if any city name contains the input (space-insensitive)
    best_match = None
    best_len = float("inf")
    for display, norm_key, area, diacritic_key in CITY_LIST:
        dk = _strip_diacritics(diacritic_key)
        nk_compact = norm_key.replace(" ", "")
        dk_compact = dk.replace(" ", "")
        if key_compact in nk_compact or key_compact in dk_compact or key in norm_key or key in dk:
            if len(norm_key) < best_len:
                best_match = (display, area)
                best_len = len(norm_key)

    if best_match:
        return best_match

    # Default to Area 2
    return city.title(), 2


def load_data():
    cars_file = Path(__file__).parent.parent / "data" / "cars.json"
    if not cars_file.exists():
        return {}
    with cars_file.open("r", encoding="utf-8") as f:
        raw = json.load(f) or {}
    try:
        sorted_items = sorted(
            raw.items(),
            key=lambda kv: (kv[1].get("brand", "").lower(), kv[1].get("model", "").lower()),
        )
        return dict(sorted_items)
    except Exception:
        return raw


def calculate_registration(price, city, car_type, purchase_date=None, area=None, seats=5):
    """Registration tax + plate fee + inspection + year-1 road fee + insurance + on-road.

    Per Thông tư 155/2025/TT-BTC (effective Jan 1 2026):
    - Hanoi and HCMC: 12% registration tax + 14M plate fee.
    - Other Area-1 cities (Da Nang, Hue, Can Tho, Hai Phong): 10% standard
      registration tax + 140K plate fee.
    - Area-2/3: 10% standard registration tax + 140K plate fee.
    """
    if area is None:
        area = get_area_tier(city)
    is_metro = is_area1_metro(city) if area == 1 else False
    tax_rate = ICE_REGISTRATION_RATE_CENTRAL_CITY if is_metro else ICE_REGISTRATION_RATE_STANDARD

    if car_type in ["ICE", "ICE-D", "HEV"]:
        tax = price * tax_rate
    elif car_type == "EV":
        today = purchase_date or date.today()
        tax = 0.0 if today <= EV_EXEMPTION_END_DATE else price * tax_rate * EV_POST_EXEMPTION_DISCOUNT
    else:
        tax = 0.0

    if area == 1:
        plate = PLATE_FEE_METRO if is_metro else PLATE_FEE_NON_METRO_AREA1
    else:
        plate = PLATE_FEES[area]

    insurance = CIVIL_INSURANCE_UNDER_6 if seats < 6 else CIVIL_INSURANCE_6_TO_11
    road_fee = ROAD_MAINTENANCE_FEE_YEARLY
    reg_subtotal = tax + plate + INSPECTION_FEE + road_fee + insurance
    total = round(reg_subtotal)
    on_road = round(price + reg_subtotal)
    return {
        "tax": round(tax),
        "plate": round(plate),
        "inspection": round(INSPECTION_FEE),
        "road_fee": round(road_fee),
        "insurance": round(insurance),
        "total": total,
        "on_road": on_road,
    }


def _model_year_for(car: dict) -> int:
    """Resolve a car's model/production year; fall back to the car-id year suffix."""
    my = car.get("model_year")
    if my:
        try:
            return int(my)
        except (TypeError, ValueError):
            pass
    car_id = car.get("id", "")
    m = re.search(r"_(\d{4})$", car_id)
    if m:
        return int(m.group(1))
    return date.today().year


def _enrich_car(car: dict, car_id: str | None = None) -> dict:
    """Attach id + derived model_year so downstream inspection logic can use them."""
    enriched = dict(car)
    if car_id is not None:
        enriched["id"] = car_id
    enriched["model_year"] = _model_year_for(enriched)
    return enriched


def _inspection_ages(model_year: int, purchase_year: int, years: int) -> list[float]:
    """Inspection ages (from production year) falling within the holding window [age0, age0+years].

    Cadence per Thông tư 47/2024/TT-BGTVT (eff. 2025-01-01), preserved by
    Thông tư 30/2026/TT-BXD (eff. 2026-07-01): first PAID inspection at 36 months,
    then 24 months while car age <7yr, 12 months at 7–20yr, 6 months beyond 20yr.
    """
    age0 = max(0, purchase_year - model_year)
    ages: list[float] = []
    a = 3.0
    while a <= 30:
        ages.append(a)
        if a < 7:
            step = 2.0
        elif a <= 20:
            step = 1.0
        else:
            step = 0.5
        a += step
    return [age for age in ages if age0 <= age <= age0 + years]


def calculate_periodic_inspection(car: dict, purchase_date=None, years: int = 5,
                                  fee: int = INSPECTION_FEE) -> int:
    """Recurring vehicle inspection (đăng kiểm) cost beyond the acquisition fee.

    `calculate_registration` already books ONE inspection into `on_road`; this adds
    only the SUBSEQUENT periodic inspections across the holding period.
    """
    if years <= 0:
        return 0
    model_year = _model_year_for(car)
    purchase_year = (purchase_date or date.today()).year
    due = _inspection_ages(model_year, purchase_year, years)
    extra = max(0, len(due) - 1) if due else 0
    return extra * fee


def fuel_price_path(car_type: str, years: int, mode: str = "forecast_avg") -> list[float]:
    """Per-year fuel unit price (VND/L or VND/kWh) across the ownership window.

    mode="current": flat today's retail price for every year.

    mode="forecast_avg" (default): linear glide from today's pump price in year 1
    to the multi-year consensus forecast by year FUEL_PRICE_GLIDE_YEARS+1, held
    flat after. A 1-year window prices at spot; long windows converge to the
    expected median, which is what keeps multi-year TCO honest when today's
    pump price sits above or below the structural consensus.

    EV charging has no separate forecast (V-Green rate committed stable through
    2029), so both modes return the same value for EVs.
    """
    if car_type == "ICE-D":
        current, forecast = DIESEL_PRICE_CURRENT_VND, DIESEL_PRICE_FORECAST_VND
    elif car_type == "EV":
        current = forecast = EV_CHARGING_PRICE_VND
    else:
        current, forecast = PETROL_PRICE_CURRENT_VND, PETROL_PRICE_FORECAST_VND

    if years <= 0:
        return []
    if mode == "current":
        return [float(current)] * years
    glide = max(1, FUEL_PRICE_GLIDE_YEARS)
    weights = [max(0.0, (glide + 1 - k) / glide) for k in range(1, years + 1)]
    return [forecast + (current - forecast) * w for w in weights]


def effective_fuel_price(car_type: str, years: int, mode: str = "forecast_avg") -> float:
    """Mean per-year unit price across the window (the TCO fuel price)."""
    path = fuel_price_path(car_type, max(years, 1), mode)
    return sum(path) / len(path) if path else 0.0


def calculate_fuel_cost(km, consumption, car_type, city_ratio=0.0, rush_hour=False,
                        years=1, fuel_price_mode="forecast_avg", year=None):
    """Adjusts fuel consumption based on city traffic ratio using the efficiency matrix.

    Returns an integer (rounded to the nearest VND) to avoid IEEE-754 precision
    artifacts leaking through the API (e.g. 142798950.00000003).

    `rush_hour=True` bumps the city-efficiency multiplier from its baseline
    (1.50x for ICE) toward the 2.0x Otofun-reported Hà Nội rush-hour peak. The
    bump scales linearly with `city_ratio` so a pure-highway commute is unaffected.

    Pricing: `fuel_price_mode` selects today's retail ("current") vs the
    current→forecast glide average ("forecast_avg", default). `years` sizes the
    averaging window; `year` (1-based) prices a single specific year of the
    glide path (used by the per-year chart breakdown).
    """
    if not consumption or consumption <= 0:
        return 0.0

    freeway_mult, city_mult = TRAFFIC_EFFICIENCY_MAP.get(car_type, (1.0, 1.0))
    if rush_hour and city_ratio > 0:
        # Per-powertrain rush-hour city target from TRAFFIC_RUSH_HOUR_MULT. ICE bumps toward
        # the 2.0x Otofun Hà Nội gridlock peak; ICE-D less (throttle-insensitive); HEV/EV
        # drop below 1.0 because stop-and-go gives regen braking more recovery (DOE).
        # The city-share scaling is applied by final_mult below, so all-highway commutes stay
        # unaffected.
        city_mult = TRAFFIC_RUSH_HOUR_MULT.get(car_type, 2.0)
    final_mult = freeway_mult + (city_mult - freeway_mult) * city_ratio
    adjusted_consumption = consumption * final_mult

    if year is not None:
        price = fuel_price_path(car_type, year, fuel_price_mode)[year - 1]
    else:
        price = effective_fuel_price(car_type, years, fuel_price_mode)

    return round((km / 100) * adjusted_consumption * price)


def calculate_opportunity_cost(principal, years, rate=SAVINGS_INTEREST_RATE):
    """Cumulative interest lost if capital were in a savings account."""
    if years <= 0:
        return 0.0
    try:
        return principal * ((1 + rate) ** years) - principal
    except OverflowError:
        return float('inf')


def calculate_maintenance(km, car_type, base_cost=None, years=1):
    """Calculate total maintenance over `years` given annual `km`.

    Per-powertrain base annual maintenance is selected when `base_cost` is not given:
      - ICE/ICE-D/HEV -> BASE_ANNUAL_MAINTENANCE_ICE (~8M VND/yr; Vietnamese dealer routine cadence)
      - EV            -> BASE_ANNUAL_MAINTENANCE_EV (~1.2M VND/yr; VinFast owner-report calibrated)
    `base_cost` is honored when the caller (or a ConfigProposals patch) supplies an explicit
    override — the per-powertrain default below only fills in when no override is supplied.

    On top of the pro-rated base cost, periodic major-service spikes fire once per threshold
    crossed (e.g. 75k total km = 1×40k spike; 160k total km = 4×40k + 2×80k + 1×120k).
    Thresholds and costs are powertrain-specific per Vietnamese OEM service schedules
    (see MAINTENANCE_SPIKES in config). Returns integer VND.
    """
    if base_cost is None:
        base_cost = (BASE_ANNUAL_MAINTENANCE_EV if car_type == "EV"
                     else BASE_ANNUAL_MAINTENANCE_ICE)
    annual = base_cost
    total = annual * years

    total_km = km * years
    spike_cost = 0
    for threshold, cost in MAINTENANCE_SPIKES.get(car_type, MAINTENANCE_SPIKES["ICE"]):
        spike_count = total_km // threshold
        spike_cost += spike_count * cost

    return round(total + spike_cost)


def resolve_liquidity_bonus(brand, car_type, segment):
    """'Bespoke Logic' for market demand multipliers."""
    if car_type == "HEV":
        return LIQUIDITY_LOGIC_MAP["HEV"]

    tier = BRAND_LIQUIDITY_MAP.get(brand, "Tier 3")

    if car_type == "EV":
        return LIQUIDITY_LOGIC_MAP["EV"].get(brand, LIQUIDITY_LOGIC_MAP["EV"]["Default"])

    tier_logic = LIQUIDITY_LOGIC_MAP.get(tier, LIQUIDITY_LOGIC_MAP["Tier 3"])
    return tier_logic.get(segment, tier_logic.get("Default", 1.0))


def _mileage_factor(annual_km: float) -> float:
    """Retention multiplier from annualised distance (VND-agnostic).

    Real-world depreciation is driven first by mileage: a car driven 40,000 km/yr
    sheds value faster than one at 8,000 km/yr, even for the same age. The ML path
    learns this via its `km_per_year` feature; this factor gives the *parametric*
    fallback (years beyond the per-car ML horizon, and the no-data safety-net) the
    same mileage sensitivity so the two paths agree on direction.

    Factor is 1.0 at REF_ANNUAL_KM, penalises high mileage, rewards low mileage,
    and is clamped to MILEAGE_FACTOR_CLAMP. Because `annual_km` is constant for a
    given `calculate_resale` call, multiplying the year-by-year retention curve by a
    scalar preserves the non-increasing-with-age invariant and the TCO identity
    `tco == on_road + operating + parking - resale`.
    """
    dev = (annual_km - REF_ANNUAL_KM) / 10_000.0
    if dev >= 0:
        factor = 1.0 - MILEAGE_PENALTY_PER_10K * dev
    else:
        factor = 1.0 + MILEAGE_BONUS_PER_10K * (-dev)
    lo, hi = MILEAGE_FACTOR_CLAMP
    return max(lo, min(hi, factor))


def _parametric_retention(brand: str, segment: str, car_type: str,
                          years: int, annual_km: float,
                          predictor, car_id: str | None = None) -> float:
    """Compute the pure parametric retention percentage (0..1) for a given
    year, **before** the VinFast floor or [0.05, 0.98] clamp are applied.

    This is the fallback path from ``calculate_resale`` (group-anchored curve
    with two-phase exponential extrapolation, or tier-based safety net) and is
    also used by the continuous blending loop in ``get_tco_yearly`` so that
    both ML and parametric values can be computed for every year.

    When ``car_id`` is provided and present in ``CALIBRATED_RESALE_ANCHORS``,
    the calibrated bonbanh retention anchors are used directly instead of the
    group-anchored curve or the RF/GB ensemble. Those anchors are *final*
    retention at ~15,000 km/yr (liquidity already reflected), so
    ``resolve_liquidity_bonus`` is skipped. ``_mileage_factor`` is still
    applied to adjust for non-standard annual distance.
    """
    # --- Calibrated-anchors path (liquid-market cars with bonbanh data) ---
    if car_id is not None and car_id in CALIBRATED_RESALE_ANCHORS:
        anchors = sorted(CALIBRATED_RESALE_ANCHORS[car_id].items())
        max_y = anchors[-1][0]
        if years <= max_y:
            retention = _interp_group_curve(anchors, years)
        else:
            _y1, _sd, sl = _fit_two_phase(anchors)
            last_ret = anchors[-1][1]
            fitted = last_ret * ((1 - sl * PARAMETRIC_DAMPING_FACTOR) ** (years - max_y))
            floor_frac = HEAVY_TAIL_ASYMPTOTE.get(segment, HEAVY_TAIL_ASYMPTOTE_DEFAULT)
            retention = max(fitted, last_ret * floor_frac)
        retention *= _mileage_factor(annual_km)
        return retention

    # --- Original group-anchored / tier-based path ---
    group_curve = predictor.get_group_curve(brand, segment, car_type)
    if group_curve:
        anchors = sorted(group_curve.items())
        max_y = anchors[-1][0]
        if years <= max_y:
            retention = _interp_group_curve(anchors, years)
        else:
            _y1, _sd, sl = _fit_two_phase(anchors)
            last_ret = anchors[-1][1]
            fitted = last_ret * ((1 - sl * PARAMETRIC_DAMPING_FACTOR) ** (years - max_y))
            # Heavy-tail asymptotic floor (see HEAVY_TAIL_ASYMPTOTE in config):
            # floored only when the exponential decays below the market plateau,
            # so it raises under-predicted residuals (e.g. 18yo Vios 0.18 -> 0.30)
            # without over-shooting faster-depreciating groups (diesel Fortuner:
            # param 0.53 > floor -> inert). max(fitted, floor) is monotonic
            # non-increasing (decreasing then flat) so no extra PAVA step needed.
            floor_frac = HEAVY_TAIL_ASYMPTOTE.get(segment, HEAVY_TAIL_ASYMPTOTE_DEFAULT)
            retention = max(fitted, last_ret * floor_frac)
    else:
        tier_label = BRAND_LIQUIDITY_MAP.get(brand, "Tier 3")
        category = "EV_Market" if car_type == "EV" else tier_label
        seg_adj = SEGMENT_DEPRECIATION_MAP.get(segment, {}).get("decay_adj", 1.0)
        params = DEPRECIATION_EQ_PARAMS.get(category, DEPRECIATION_EQ_PARAMS["Tier 3"])
        decay = params["annual_decay"] * seg_adj
        retention = (1 - params["y1_drop"]) * ((1 - decay) ** (years - 1))

    bonus = resolve_liquidity_bonus(brand, car_type, segment)
    retention *= bonus
    retention *= _mileage_factor(annual_km)
    return retention


def calculate_resale(price, brand, years, car_type, segment, annual_km=15000,
                     custom_rate=None, max_training_year=None,
                     return_both=False, car_id=None):
    """Calculates residual value using ML prediction first, falling back to a
    group-anchored parametric curve.
    Returns dict with keys: value (rounded to nearest VND), logic, ml_spread
    (optional), ml_std (optional), resale_note_key (optional).

    When ``return_both=True`` the dict also contains ``ml_value`` and
    ``parametric_value`` (both pre-VinFast-floor) so callers can blend the two
    paths continuously instead of hard-switching at the ML horizon.

    ML path is gated on a *per-car* training horizon (years <= the last year the
    car's group has enough observed samples). Beyond that, a two-phase
    exponential fitted to the group's observed retention anchors is used; for
    groups with no training data the tier-based ``DEPRECIATION_EQ_PARAMS``
    curve is the safety net. A warning is surfaced only in the true
    extrapolation region (years beyond the per-car horizon).

    VinFast-specific floor: VinFast's 70% buyback guarantee plus strong
    Vietnamese used-EV market liquidity mean real retention exceeds the
    parametric EV_Market decay curve by 25-35% for the first 24 months
    (bonbanh.com.vn 2026-07, 416 listings, mean 0.60-0.70 retention at 3yr vs
    ViDrive parametric 0.46). When the computed residual falls below
    ``price * VINFAST_LIQUIDITY_FLOOR`` and ownership is within the guarantee
    window, we clamp the residual up to the floor and surface the
    ``resale.vinfastLiquidityFloor`` note so the Methodology page can disclose
    the structural support. Above-floor cars are left unchanged; after the
    24-month window the curve decays normally.

    When ``car_id`` is provided and present in ``CALIBRATED_RESALE_ANCHORS``,
    the calibrated bonbanh retention anchors serve as the parametric fallback
    (seeding ``_parametric_retention``). The ML ensemble is also used when
    within the car's training horizon — the shrinkage blend (alpha=0.50 toward
    real-only group curves) corrects the synthetic-contamination bias that
    previously motivated bypassing ML entirely. A secondary blend further
    corrects toward the car-specific anchors when ML and parametric agree within
    ``SECONDARY_BLEND_THRESHOLD`` (20%), catching segment-level biases the group
    shrinkage misses (e.g. B-SUV/ICE y4). When they disagree beyond the threshold,
    the anchor interpolation is missing market structure (e.g. D-Pickup y6 cliff)
    and ML alone is trusted. Evaluated: 6/6 calibrated cars PASS the Phase5C gate
    (MAPE=2.3%, maxAPE=4.2%).
    """
    is_vinfast = brand == "VinFast"
    base_note_key = "resale.vinfastGuarantee" if is_vinfast else None

    predictor = get_predictor()
    mt = max_training_year if max_training_year is not None else predictor.get_car_max_training_year(brand, segment, car_type)

    # Calibrated cars use their bonbanh anchors as the parametric fallback, but
    # the ML ensemble (shrinkage-blended) is also allowed when within the
    # car's training horizon — the shrinkage corrects the contamination bias
    # that previously motivated bypassing ML entirely.
    if years == 0:
        result = {"value": round(price), "logic": "parametric",
                  "resale_note_key": base_note_key,
                  "max_training_year": mt}
        result["market_value"] = round(price)
        result["guarantee_value"] = round(price)
        result["resale_guarantee_floor"] = None
        return result

    if custom_rate is not None:
        value = round(price * ((1 - custom_rate) ** years))
        result = _apply_vinfast_floor(value, price, years, is_vinfast, base_note_key, "custom", car_id=car_id)
        result["max_training_year"] = mt
        return result

    # --- Compute parametric value (always, for blending) ---
    param_retention = _parametric_retention(brand, segment, car_type, years, annual_km, predictor, car_id=car_id)
    param_retention = max(0.05, min(0.98, param_retention))
    param_value = round(price * param_retention)
    param_result = _apply_vinfast_floor(
        param_value, price, years, is_vinfast, base_note_key, "parametric", car_id=car_id)

    # --- Calibrated anchor years: real market data, use directly. ---
    # Anchor-point years are observed bonbanh/oto retention values — the ground
    # truth for that model. Using them directly (instead of the ML path) guarantees
    # monotonicity at anchor-year transitions and removes ML under-prediction bias
    # (e.g. xpander y6 ML 0.61 vs anchor 0.69). The Phase5C gate tests ONLY
    # non-anchor years, so this early-return leaves the gate results unchanged.
    if (car_id is not None
            and car_id in CALIBRATED_RESALE_ANCHORS
            and years in CALIBRATED_RESALE_ANCHORS[car_id]):
        # Anchor years beyond the per-car ML training horizon are a parametric
        # extrapolation (the anchor value itself is observed data, but ML cannot
        # produce it — the model was never trained that far). Surface the same
        # warning the parametric-fallback path emits so callers see why ML was
        # bypassed. Without this, e.g. morning_2026 at years 11/18 silently
        # dropped resale.fallbackToParametric while non-anchor years > mt fired it.
        if years > mt:
            param_result["warning"] = "resale.fallbackToParametric"
            param_result["resale_note_key"] = "resale.calibratedAnchorBeyond"
        param_result["max_training_year"] = mt
        return param_result

    # --- ML path — for years within this car's observed training horizon.
    # Calibrated cars are included: the shrinkage blend (alpha=0.50 toward
    # real-only group curves) corrects the synthetic-contamination bias that
    # previously motivated bypassing ML for liquid models. ---
    ml_value = None
    ml_spread = None
    ml_std = None
    ml_logic = None
    try:
        if years <= mt:
            ml_result = predictor.predict_resale(brand, segment, car_type, years, annual_km, price)
            if ml_result["ml_prediction"] is not None:
                predicted_pct = ml_result["ml_prediction"]
                if 0.05 <= predicted_pct <= 1.0:
                    ml_value = round(price * predicted_pct)
                    ml_spread = round(ml_result.get("ml_spread", 0) * price)
                    ml_std = round(ml_result.get("ml_std", 0) * price)
                    ml_logic = "ml"
    except Exception:
        pass  # Fall through to parametric

    # --- Secondary blend for calibrated cars ---
    # predict_resale() already shrinks the ML ensemble toward the group-level real-data
    # curve (alpha=0.50). For calibrated cars with bonbanh/oto anchors, also blend
    # toward the car-specific parametric anchors when ML and parametric agree within
    # SECONDARY_BLEND_THRESHOLD. The anchors are real market data for this model, so
    # they correct segment-level biases the group shrinkage can't fix (e.g. B-SUV/ICE
    # y4 synthetic contamination pulling ML below real).
    #
    # When ML and parametric disagree beyond the threshold, the anchor interpolation
    # is missing market structure (e.g. D-Pickup y6 cliff: Ranger anchors interpolate
    # to 0.6967 but real is 0.5435). We trust ML alone — the group shrinkage already
    # captures the trend. Ranger y6 gap=20.7% (no blend, APE stays 1.6%); raptor y6
    # gap=18.1% (blend, APE drops 6.7%->0.6%).
    if (ml_value is not None
            and car_id is not None
            and car_id in CALIBRATED_RESALE_ANCHORS
            and param_retention is not None):
        gap = abs(predicted_pct - param_retention) / max(predicted_pct, param_retention, 0.001)
        if gap < SECONDARY_BLEND_THRESHOLD:
            blended_pct = (predicted_pct
                           + SECONDARY_BLEND_RATIO * (param_retention - predicted_pct))
            ml_value = round(price * blended_pct)
            # Reduce spread/std proportionally — blending toward a deterministic
            # parametric value reduces model uncertainty.
            confidence_scale = 1.0 - SECONDARY_BLEND_RATIO
            if ml_spread:
                ml_spread = round(ml_spread * confidence_scale)
            if ml_std:
                ml_std = round(ml_std * confidence_scale)

    if ml_value is not None:
        result = _apply_vinfast_floor(
            ml_value, price, years, is_vinfast, base_note_key, "ml",
            car_id=car_id,
            extra={"ml_spread": ml_spread, "ml_std": ml_std})
        result["max_training_year"] = mt
        if return_both:
            result["ml_value"] = ml_value
            result["parametric_value"] = param_value
        return result

    # Parametric fallback
    if years > mt:
        param_result["warning"] = "resale.fallbackToParametric"
        # Calibrated cars: the value comes from the observed bonbanh/oto anchor
        # interpolation (not pure parametric), so surface the same disclosure
        # the anchor-early-return path uses. Without this, non-anchor years > mt
        # on calibrated cars silently drop the inline note even though the
        # warning fires — making the disclosure inconsistent across anchor vs
        # non-anchor years for the same car.
        if car_id is not None and car_id in CALIBRATED_RESALE_ANCHORS:
            param_result["resale_note_key"] = "resale.calibratedAnchorBeyond"
    param_result["max_training_year"] = mt
    if return_both:
        param_result["ml_value"] = None
        param_result["parametric_value"] = param_value
    return param_result


def _interp_group_curve(anchors: list[tuple[int, float]], years: int) -> float:
    """Linear interpolation of retention between observed year anchors.

    `anchors` is a sorted list of (year, retention). Years outside the anchor
    range clamp to the nearest endpoint."""
    ys = [a[0] for a in anchors]
    rs = [a[1] for a in anchors]
    if years <= ys[0]:
        return rs[0]
    if years >= ys[-1]:
        return rs[-1]
    for i in range(1, len(ys)):
        if years <= ys[i]:
            y0, y1 = ys[i - 1], ys[i]
            r0, r1 = rs[i - 1], rs[i]
            frac = (years - y0) / (y1 - y0)
            return r0 + (r1 - r0) * frac
    return rs[-1]


def _fit_two_phase(anchors: list[tuple[int, float]]) -> tuple[float, float, float]:
    """Grid-search a two-phase exponential retention curve:

        ret(y) = (1 - y1) * (1 - sd)^min(y-1, 2) * (1 - sl)^max(0, y-3)

    minimizing MAE vs the observed anchors. Returns (y1, sd, sl). The grid is
    cheap (16×11×8 = 1,408 evals over ≤6 points) and validated at mean MAE
    ≈0.014 across 62 groups."""
    ys = [a[0] for a in anchors]
    rs = [a[1] for a in anchors]
    best = (0.20, 0.12, 0.08)
    best_mae = float("inf")
    for y1_i in range(16):
        y1 = 0.15 + 0.01 * y1_i
        for sd_i in range(11):
            sd = 0.08 + 0.01 * sd_i
            for sl_i in range(8):
                sl = 0.05 + 0.01 * sl_i
                preds = [(1 - y1) * (1 - sd) ** min(y - 1, 2) * (1 - sl) ** max(0, y - 3) for y in ys]
                mae = sum(abs(p - r) for p, r in zip(preds, rs)) / len(rs)
                if mae < best_mae:
                    best_mae = mae
                    best = (y1, sd, sl)
    return best


def _apply_vinfast_floor(value, price, years, is_vinfast, base_note_key, logic, car_id=None, extra=None):
    """Clamp VinFast residual at the buyback-window floor, with a softer post-window
    decay anchored on the floor. The floor fires only when the parametric curve would
    otherwise fall below it; above-floor residuals pass through untouched. The floor
    note replaces the default guarantee note only when the floor fires (so the UI can
    disclose which mechanism shaped the prediction).

    Floor behavior:
      - When ``car_id`` is in ``VINFAST_BUYBACK_GUARANTEE`` (per-car schedule),
        the floor uses the published year-by-year guarantee for years within the
        schedule window, then decays from the last guarantee anchor at
        ``VINFAST_FLOOR_DECAY`` for subsequent years.
      - Otherwise falls back to the flat ``VINFAST_LIQUIDITY_FLOOR`` (0.70) for
        years <= ``VINFAST_FLOOR_YEARS``, decaying afterward. The 0.70 floor is
        a safety net that undercuts the guarantee at years 1-3 but only
        *raises* values that would otherwise fall below it.

    Option B (dual number): for VinFast cars the PRIMARY ``value`` is the open-market
    resale estimate (Option 1) — the honest number a seller gets on the market. The
    ``guarantee_value`` carries the buyback-guarantee support (``max(market, floor)``),
    which exceeds the market only while the schedule-based floor is above it; the two
    merge when the schedule decays to/below the market. ``market_value`` is an alias of
    the primary value. Non-VinFast cars return the same input for all three keys.
    ``resale_guarantee_floor`` holds the raw scheduled buy-back floor (always present
    for VinFast, None otherwise) — exposed separately so the UI can disclose it
    even when it sits below the open-market estimate. ``market_value`` aliases the
    headline; ``guarantee_value`` is the effective floor support (max(market, floor));
    ``resale`` (the consumer-facing headline) is the open-market value, unchanged.
    """
    result: dict = {"value": round(value), "logic": logic}
    if extra:
        result.update(extra)
    if is_vinfast:
        floor = _vinfast_floor_value(price, years, car_id)
        # Raw scheduled guarantee floor — always exposed for VinFast (even when it
        # sits below the open-market headline) so the UI can disclose it unconditionally.
        result["resale_guarantee_floor"] = round(floor) if floor is not None else None
        if floor is not None and value < floor:
            # Floor is the binding guarantee support — disclose it, keep headline market.
            result["resale_note_key"] = "resale.vinfastLiquidityFloor"
            result["vinfast_floor_applied"] = True
            result["guarantee_value"] = round(floor)
        else:
            result["resale_note_key"] = base_note_key
            result["guarantee_value"] = round(value)
        # Option B: expose the two numbers separately. Headline == open market.
        result["market_value"] = round(value)
    else:
        result["market_value"] = round(value)
        result["guarantee_value"] = round(value)
        result["resale_guarantee_floor"] = None
    return result


def _vinfast_floor_value(price: int, years: int, car_id: str | None) -> int | None:
    """Return the VinFast buyback-guarantee floor (VND) for a car-year, or None if
    ``car_id`` is not a VinFast car. Shared by the single-year path and the yearly
    blend path so the guarantee/decay schedule is computed in exactly one place."""
    if car_id is None:
        return None
    if car_id in VINFAST_BUYBACK_GUARANTEE:
        sched = VINFAST_BUYBACK_GUARANTEE[car_id]
        max_sched = max(sched.keys())
        if years <= max_sched:
            return round(price * sched[years])
        decay_periods = years - max_sched
        return round(
            price * sched[max_sched]
            * ((1 - VINFAST_FLOOR_DECAY) ** decay_periods)
        )
    if years <= VINFAST_FLOOR_YEARS:
        return round(price * VINFAST_LIQUIDITY_FLOOR)
    decay_periods = years - VINFAST_FLOOR_YEARS
    anchor = price * VINFAST_LIQUIDITY_FLOOR
    return round(anchor * ((1 - VINFAST_FLOOR_DECAY) ** decay_periods))


def _blend_resale_curve(price: int, brand: str, segment: str, car_type: str,
                       annual_km: float, total_years: int,
                       mt: int, predictor, car_id: str | None = None) -> list[dict]:
    """Compute a blended per-year resale curve that smoothly transitions from
    ML predictions (years <= mt) to the parametric fallback (years > mt).

    Uses a **continuous iteration loop**:
      1. Both ML and parametric values are computed for every year, sourced from
         ``calculate_resale(return_both=True)`` — the SAME function that prices
         the results-card headline — so every year carries the card's exact
         semantics (calibrated-anchor early returns, secondary anchor blend,
         shrinkage).
      2. Over a ``TRANSITION_WIDTH``-year window the blend weight ramps linearly
         from 1.0 (pure ML) to 0.0 (pure parametric), so the depreciation curve
         has no kink at the horizon boundary. ``calculate_resale`` hard-stops ML
         at ``mt``, so the transition zone is topped up with direct ensemble
         predictions to preserve this ramp.
      3. The parametric tail is anchored to the last blended value and a
         scale factor is carried forward so the tail starts exactly where the
         blend ended.
      4. A PAVA-style iterative correction loop enforces monotonicity
         (non-increasing retention) across the entire curve, iterating until
         convergence or ``TRANSITION_MAX_ITER`` is reached.
      5. The VinFast floor is applied to the final blended values.
      6. The TERMINAL year is pinned to a single-shot ``calculate_resale``
         (total_years) call — exactly what ``get_tco`` charges the results
         card — followed by a backward monotonicity sweep, so the chart's last
         data point always equals the card's headline resale figure.

    Returns a list of dicts, one per year (1..total_years), each with keys:
      year, value, raw_ml, raw_param, logic, resale_note_key
    """
    is_vinfast = brand == "VinFast"
    base_note_key = "resale.vinfastGuarantee" if is_vinfast else None

    # --- Phase 1: compute raw ML and parametric values for all years ---
    # Per-year values come from ``calculate_resale(return_both=True)`` so the
    # curve's inputs carry identical semantics to the single-shot results-card
    # path. ``calculate_resale`` hard-stops ML at ``mt``, so the transition
    # zone (mt, mt+TRANSITION_WIDTH] is topped up with direct ensemble
    # predictions — the smooth ML→parametric ramp is presentation-only and
    # never overrides a year where the card has a defined value.
    ml_horizon_extended = mt + TRANSITION_WIDTH
    raw_ml: dict[int, int | None] = {}
    raw_param: dict[int, int] = {}

    for year in range(1, total_years + 1):
        single = calculate_resale(
            price, brand, year, car_type, segment,
            annual_km=annual_km, custom_rate=None,
            return_both=True, car_id=car_id)
        raw_ml[year] = single.get("ml_value")

        param_value = single.get("parametric_value")
        if param_value is None:
            # The calibrated-anchor early return omits ml_value/parametric_value;
            # there the returned value IS the parametric-path output (already
            # floored — idempotent under Phase 4's re-application).
            param_value = single["value"]
        raw_param[year] = round(param_value)

        if mt < year <= ml_horizon_extended:
            try:
                ml_result = predictor.predict_resale(
                    brand, segment, car_type, year, annual_km, price)
                pct = ml_result["ml_prediction"]
                if pct is not None and 0.05 <= pct <= 1.0:
                    raw_ml[year] = round(price * pct)
            except Exception:
                pass

    # --- Phase 2: continuous blending over the transition window ---
    trans_start = mt
    trans_end = min(total_years, mt + TRANSITION_WIDTH)
    param_scale = 1.0  # carried forward; adjusts parametric tail to anchor at blend end
    blended: list[dict] = []

    for year in range(1, total_years + 1):
        ml_val = raw_ml[year]

        # Continuity anchor (in-phase): for the parametric tail, rescale
        # ``param_scale`` *before* computing this year's value so the correction
        # is applied in the same iteration. The previous post-hoc check lagged by
        # one year, which produced a transient step whenever the parametric curve
        # would otherwise jump above the last blended value at the boundary.
        if year > trans_end and len(blended) > 0 and raw_param[year] > 0:
            prev = blended[-1]["value"]
            rp = raw_param[year]
            if prev < rp:
                param_scale = min(param_scale, prev / rp)

        param_val = round(raw_param[year] * param_scale)

        if year <= trans_start and ml_val is not None:
            value = ml_val
            logic = "ml"
        elif year > trans_end:
            value = param_val
            logic = "parametric"
        else:
            # Transition zone: linear blend
            span = max(1, trans_end - trans_start)
            weight = (trans_end - year) / span
            if ml_val is not None:
                value = round(weight * ml_val + (1 - weight) * param_val)
                logic = "ml"
            else:
                value = param_val
                logic = "parametric"

        blended.append({
            "year": year,
            "value": value,
            "raw_ml": ml_val,
            "raw_param": raw_param[year],
            "logic": logic,
        })

    # --- Phase 3: iterative monotonicity correction (PAVA-style) ---
    # Enforce a strictly non-increasing resale curve. A car cannot be worth
    # more after another year of ownership, so any year whose value exceeds the
    # prior year is pulled down to the prior value. The loop iterates to
    # convergence so cascading or plateau-forming bumps are fully flattened.
    # A tolerance is intentionally NOT applied here: even a sub-tolerance rise
    # (e.g. +0.1%) is economically impossible and visible to users comparing
    # year-over-year resale. Equal adjacent values are allowed (`>` not `>=`).
    for _ in range(TRANSITION_MAX_ITER):
        changed = False
        for i in range(1, len(blended)):
            prev_val = blended[i - 1]["value"]
            curr_val = blended[i]["value"]
            if curr_val > prev_val:
                # Violation: pull this point down to the previous
                blended[i]["value"] = prev_val
                changed = True
        if not changed:
            break

    # --- Phase 4: apply VinFast floor to final values ---
    for entry in blended:
        vf_result = _apply_vinfast_floor(
            entry["value"], price, entry["year"],
                       is_vinfast, base_note_key, entry["logic"],
                       car_id=car_id,)
        entry["value"] = vf_result["value"]
        entry["resale_note_key"] = vf_result.get("resale_note_key")
        entry["vinfast_floor_applied"] = vf_result.get("vinfast_floor_applied", False)
        # Option B: carry the two numbers through to the yearly surface.
        entry["market_value"] = vf_result.get("market_value", entry["value"])
        entry["guarantee_value"] = vf_result.get("guarantee_value", entry["value"])

    # --- Phase 5: pin the terminal year to the results-card headline ---
    # get_tco prices the card's "Predicted resale" with a single-shot
    # calculate_resale(total_years) call. The chart must END on exactly that
    # number — a final data point that disagrees with the card reads as a bug
    # to anyone comparing the two. Pin it, then run one backward monotonicity
    # sweep so the non-increasing invariant survives the pin; raised entries
    # are re-floored through _apply_vinfast_floor so value/market/guarantee
    # stay a consistent triple.
    final = calculate_resale(
        price, brand, total_years, car_type, segment,
        annual_km=annual_km, custom_rate=None, car_id=car_id)
    blended[-1]["value"] = final["value"]
    blended[-1]["market_value"] = final.get("market_value", final["value"])
    blended[-1]["guarantee_value"] = final.get("guarantee_value", final["value"])
    blended[-1]["resale_note_key"] = final.get("resale_note_key")
    blended[-1]["vinfast_floor_applied"] = final.get("vinfast_floor_applied", False)
    blended[-1]["logic"] = final.get("logic", blended[-1]["logic"])

    for i in range(len(blended) - 2, -1, -1):
        if blended[i]["value"] < blended[i + 1]["value"]:
            refloored = _apply_vinfast_floor(
                blended[i + 1]["value"], price, blended[i]["year"],
                is_vinfast, base_note_key, blended[i]["logic"], car_id=car_id)
            blended[i].update(refloored)

    return blended


def _calculate_tco_uncertainty(reg: dict, fuel: float, maint: float,
                                road_fees: float, insurance: float,
                                parking_toll: float, resale: float,
                                resale_std: float | None,
                                inspection_periodic: float = 0) -> float:
    """Compute combined standard deviation of TCO via error propagation.

    Components:
      - Registration: fractional variance of tax + fixed plate/inspection
      - Fuel: fractional variance scaled by total fuel cost
      - Maintenance: fractional variance scaled by total maint cost
      - Road fees: fractional variance scaled by total road fees
      - Insurance: fractional variance scaled by total insurance
      - Parking & toll: combined into one fractional variance
      - Resale: model-derived ml_std (preferred) or parametric fallback (5% of resale)

    Variances are independent and summed in quadrature:
        σ_tco² = σ_reg² + σ_fuel² + σ_maint² + σ_road_fees² + σ_insurance² + σ_parking² + σ_resale²
    """
    import math

    # Registration uncertainty (tax is %-based, plate/inspection are fixed)
    reg_tax_std = reg["tax"] * REGISTRATION_VARIANCE
    reg_fixed_std = (reg["plate"] + reg["inspection"]) * REGISTRATION_VARIANCE
    sigma_reg = math.sqrt(reg_tax_std ** 2 + reg_fixed_std ** 2)

    # Fuel uncertainty
    sigma_fuel = fuel * FUEL_PRICE_VARIANCE

    # Maintenance uncertainty
    sigma_maint = maint * MAINTENANCE_COST_VARIANCE

    # Road fees uncertainty (fixed yearly * years)
    sigma_road_fees = road_fees * ROAD_FEE_VARIANCE

    # Insurance uncertainty
    sigma_insurance = insurance * INSURANCE_RATE_VARIANCE

    # Periodic inspection (fixed fee, same variance class as registration fixed fees)
    sigma_inspection = inspection_periodic * REGISTRATION_VARIANCE

    # Parking & toll uncertainty
    sigma_parking = parking_toll * PARKING_TOLL_VARIANCE

    # Resale uncertainty — prefer model-derived std, fall back to parametric (5% of resale)
    if resale_std is not None and resale_std > 0:
        sigma_resale = resale_std
    else:
        sigma_resale = abs(resale) * RESALE_PARAMETRIC_STD_PCT

    combined = math.sqrt(
        sigma_reg ** 2
        + sigma_fuel ** 2
        + sigma_maint ** 2
        + sigma_road_fees ** 2
        + sigma_insurance ** 2
        + sigma_inspection ** 2
        + sigma_parking ** 2
        + sigma_resale ** 2
    )
    return combined


def _zero_tco_dict(car: dict, city: str, km: float, purchase_date=None, area=None,
                   include_parking_toll: bool = True,
                   fuel_price_mode: str = "forecast_avg") -> dict:
    """TCO with a 0-year horizon: acquisition (on-road) only.

    No operating costs accrue and resale equals price (no ownership period),
    so depreciation and TCO both equal the on-road price. Used to keep a
    years=0 request from producing a divide/domain error.
    """
    price = car["price"]
    if area is None:
        area = get_area_tier(city)
    reg = calculate_registration(price, city, car["type"], purchase_date, area=area, seats=car.get("seats", 5))
    # "Giá lăn bánh" (on-road price) = MSRP + reg_tax + plate + inspection + year-1
    # road-maintenance fee + year-1 civil insurance. The first-year road and insurance
    # fees are paid upfront at registration in Vietnam (per user spec Aug 2026), so
    # they belong in the acquisition block, not the multi-year operating tail.
    on_road = reg["on_road"]
    return {
        "price": price,
        "reg": reg,
        "reg_tax": reg["tax"],
        "on_road": round(on_road),
        "fuel": 0,
        "fuel_price_mode": fuel_price_mode,
        "fuel_price_vnd": None,
        "maint": 0,
        "legal": 0,
        "operating": 0,
        "parking_toll": {
            "monthly_parking": 0,
            "monthly_toll": 0,
            "monthly_total": 0,
            "total_over_period": 0,
        },
        "resale": round(price),
        "resale_logic": "parametric",
        "resale_spread": None,
        "resale_std": None,
        "resale_note_key": None,
        "depreciation": 0,
        "opp_cost": 0,
        "liquidity": BRAND_LIQUIDITY_MAP.get(car.get("brand"), "Tier 3 (Niche)"),
        "tco": round(on_road),
        "true_financial_impact": round(on_road),
        "monthly": 0,
        "confidence_low": round(on_road),
        "confidence_high": round(on_road),
        "ml_max_year": 0,
    }


def get_tco(car, city, km, years=5, purchase_date=None, area=None, city_ratio=0.0,
            rush_hour=False, include_insurance=False, include_parking_toll=True,
            fuel_price_mode="forecast_avg"):
    """Master TCO: Acquisition + Running - Resale

    `rush_hour=True` swaps in the per-powertrain rush-hour city multiplier from
    TRAFFIC_RUSH_HOUR_MULT — a gridlock penalty for ICE/ICE-D (up to 2.0x for Hà Nội per
    Otofun #12498) but a regen-driven efficiency gain for EV/HEV. `include_insurance=True`
    adds an optional line for
    voluntary physical-damage ("thân vỏ") coverage at ~1.5% of MSRP per year — typical
    PVI / Bảo Việt / Bảo Minh market rate. Both are surfaced on `TcoResult` so the
    frontend can disclose which toggles shaped the prediction.

    `fuel_price_mode="forecast_avg"` (default) prices fuel on the current→forecast
    glide average across the ownership window; "current" pins every year to today's
    pump/charging price. The effective unit price and mode are surfaced on the
    result so the frontend can disclose which pricing shaped the number.
    """
    if years <= 0:
        return _zero_tco_dict(car, city, km, purchase_date, area,
                              include_parking_toll=include_parking_toll,
                              fuel_price_mode=fuel_price_mode)
    price = car["price"]
    reg = calculate_registration(price, city, car["type"], purchase_date, area=area, seats=car.get("seats", 5))
    # "Giá lăn bánh" (on-road price) = MSRP + reg_tax + plate + inspection + year-1
    # road-maintenance fee + year-1 civil insurance (paid upfront in Vietnam).
    on_road = reg["on_road"]

    fuel_annual_price = effective_fuel_price(car["type"], years, fuel_price_mode)
    fuel = calculate_fuel_cost(km, car["consumption"], car["type"], city_ratio,
                               rush_hour=rush_hour, years=years,
                               fuel_price_mode=fuel_price_mode) * years
    maint = calculate_maintenance(km, car["type"], car.get("annual_maintenance"), years)
    # Year-1 road fee + civil insurance are already in `on_road`, so the operating
    # tail covers only the remaining (years-1) years. Total TCO is unchanged; this
    # just keeps the acquisition block correctly bounded.
    seats = car.get("seats", 5)
    insurance_rate = CIVIL_INSURANCE_UNDER_6 if seats < 6 else CIVIL_INSURANCE_6_TO_11
    road_fees = ROAD_MAINTENANCE_FEE_YEARLY * (years - 1)
    insurance = insurance_rate * (years - 1)
    # Optional voluntary physical-damage ("thân vỏ") coverage — ~1.5% of MSRP / year.
    # Applies to the full ownership period so it compares on the same horizon as other
    # components. Disabled by default; surfaced in `insurance_optional` so the UI can
    # disclose which toggle fired.
    insurance_optional = round(price * OPTIONAL_PHYSICAL_DAMAGE_INSURANCE_RATE) * years if include_insurance else 0
    # Recurring inspection (đăng kiểm) beyond the one booked into on_road.
    inspection_periodic = calculate_periodic_inspection(car, purchase_date, years)
    operating = fuel + maint + road_fees + insurance + insurance_optional + inspection_periodic

    # Parking & Toll estimates (scaled by city/highway split; metro sub-tier via city)
    parking_toll = calculate_parking_toll(area or get_area_tier(city), years, city_ratio, city=city)
    if not include_parking_toll:
        parking_toll = {
            "monthly_parking": 0, "monthly_toll": 0,
            "monthly_total": 0, "total_over_period": 0,
        }

    resale_result = calculate_resale(
        price,
        car["brand"],
        years,
        car["type"],
        car.get("segment", "C-Sedan"),
        annual_km=km,
        custom_rate=car.get("depreciation_rate"),
        car_id=car.get("id"),
    )
    resale = resale_result["value"]
    resale_logic = resale_result["logic"]
    resale_std = resale_result.get("ml_std")
    resale_note_key = resale_result.get("resale_note_key")
    ml_max_year = resale_result.get("max_training_year")
    depreciation = price - resale

    # [v0.5.0] Market Research Factors
    opp_cost = calculate_opportunity_cost(on_road, years)
    liquidity = BRAND_LIQUIDITY_MAP.get(car.get("brand"), "Tier 3 (Niche)")

    tco = (on_road + operating + parking_toll["total_over_period"]) - resale

    # Confidence interval via error propagation
    combined_std = _calculate_tco_uncertainty(
        reg, fuel, maint, road_fees, insurance,
        parking_toll["total_over_period"], resale, resale_std,
        inspection_periodic,
    )
    confidence_low = tco - CONFIDENCE_Z_SCORE * combined_std
    confidence_high = tco + CONFIDENCE_Z_SCORE * combined_std

    return {
        "price": price,
        "reg": reg,
        "reg_tax": reg["tax"],
        "on_road": round(on_road),
        "fuel": fuel,
        "fuel_price_mode": fuel_price_mode,
        "fuel_price_vnd": round(fuel_annual_price),
        "maint": maint,
        "legal": round(road_fees + insurance + inspection_periodic),
        "operating": round(operating),
        "insurance_optional": round(insurance_optional),
        "inspection_periodic": round(inspection_periodic),
        "rush_hour_applied": bool(rush_hour and city_ratio > 0),
        "parking_toll": {
            **parking_toll,
            "monthly_parking": round(parking_toll["monthly_parking"]),
            "monthly_toll": round(parking_toll["monthly_toll"]),
            "monthly_total": round(parking_toll["monthly_total"]),
            "total_over_period": round(parking_toll["total_over_period"]),
        },
        "resale": resale,
        "resale_logic": resale_logic,
        "resale_spread": resale_result.get("ml_spread"),
        "resale_std": resale_std,
        "resale_note_key": resale_note_key,
        "resale_market_value": resale_result.get("market_value"),
        "resale_guarantee_value": resale_result.get("guarantee_value"),
        "resale_guarantee_floor": resale_result.get("resale_guarantee_floor"),
        "warnings": [resale_result["warning"]] if resale_result.get("warning") else [],
        "ml_max_year": ml_max_year,
        "depreciation": round(depreciation),
        "opp_cost": round(opp_cost),
        "liquidity": liquidity,
        "tco": round(tco),
        "true_financial_impact": round(tco + opp_cost),
        "monthly": round(operating / (years * 12)),
        "confidence_low": round(confidence_low),
        "confidence_high": round(confidence_high),
    }


def calculate_parking_toll(area: int, years: int, city_ratio: float = 0.0, city: str | None = None) -> dict:
    """
    Calculate parking & toll estimates based on area tier and city/highway split.
    - Parking scales with city driving (city_ratio)
    - Tolls scale with highway driving (1 - city_ratio)
    - When area==1 and city is Hanoi/HCMC core, use the area1_metro sub-tier
      (apartment parking 2.0M VND/mo vs 1.5M for other Area-1 cities).
    """
    # Resolve tier key; prefer metro sub-tier when applicable
    if area == 1 and city and is_area1_metro(city):
        area_key = "area1_metro"
    else:
        area_key = f"area{area}" if area in (1, 2, 3) else "area2"
    estimates = PARKING_TOLL_ESTIMATES.get(area_key, PARKING_TOLL_ESTIMATES["area2"])

    # Scale parking by city driving, tolls by highway driving
    parking_monthly = estimates["parking_monthly"] * (0.5 + city_ratio)
    toll_monthly = estimates["toll_monthly"] * (1.5 - city_ratio)

    monthly_total = parking_monthly + toll_monthly
    total_over_period = monthly_total * 12 * years

    return {
        "monthly_parking": round(parking_monthly),
        "monthly_toll": round(toll_monthly),
        "monthly_total": round(monthly_total),
        "total_over_period": round(total_over_period),
    }


def calculate_loan_schedule(on_road_price: float, down_pct: float, annual_rate: float, term_years: int) -> dict:
    """
    Calculate loan schedule using reducing balance method (standard in Vietnam).
    Returns monthly payment, total interest, total repayment, and effective cost.

    Edge cases:
    - 0% down: full loan (no down payment)
    - 100% down: no loan needed (zero monthly payment)
    """
    # Clamp down_pct to valid range instead of silently overriding
    down_pct = max(0.0, min(100.0, down_pct))

    loan_amount = on_road_price * (1 - down_pct / 100)
    monthly_rate = annual_rate / 12
    num_payments = term_years * 12

    if loan_amount <= 0:
        # 100% down payment — no loan needed
        return {
            "loan_amount": 0.0,
            "down_payment": round(on_road_price),
            "monthly_payment": 0.0,
            "total_interest": 0.0,
            "total_repayment": 0.0,
            "effective_cost": round(on_road_price),
            "term_months": num_payments,
            "annual_rate": annual_rate,
        }

    if monthly_rate == 0:
        monthly_payment = loan_amount / num_payments
    else:
        # Standard reducing balance formula
        monthly_payment = loan_amount * monthly_rate * (1 + monthly_rate) ** num_payments / ((1 + monthly_rate) ** num_payments - 1)

    total_repayment = monthly_payment * num_payments
    total_interest = total_repayment - loan_amount
    effective_cost = on_road_price + total_interest  # Cash price + financing cost

    return {
        "loan_amount": round(loan_amount),
        "down_payment": round(on_road_price * down_pct / 100),
        "monthly_payment": round(monthly_payment),
        "total_interest": round(total_interest),
        "total_repayment": round(total_repayment),
        "effective_cost": round(effective_cost),
        "term_months": num_payments,
        "annual_rate": annual_rate,
    }


def get_tco_yearly(car: dict, city: str, km: float, years: int = 5, purchase_date=None, area=None,
                   city_ratio: float = 0.0, include_parking_toll: bool = True,
                   fuel_price_mode: str = "forecast_avg", rush_hour: bool = False) -> tuple[list[dict], list[str], int | None]:
    """Return per-year TCO breakdown for chart visualization.

    Produces a non-linear cumulative cost curve by:
    - Computing depreciation per year via calculate_resale (non-linear ML/parametric curve)
    - Escalating maintenance costs with vehicle age (~15% per year)
    - Pricing fuel per glide-path year (forecast_avg) or flat (current); the path
      sums exactly to the TCO total because the effective price is the path mean
    - Subtracting residual value at each year to get true cumulative ownership cost

    ``rush_hour`` mirrors get_tco's fuel treatment (TRAFFIC_RUSH_HOUR_MULT city
    swap) so the chart's cumulative operating line matches the results card
    whenever the toggle is on.
    """
    price = car["price"]
    if area is None:
        area = get_area_tier(city)
    if years <= 0:
        return [], [], 0

    reg = calculate_registration(price, city, car["type"], purchase_date, area=area, seats=car.get("seats", 5))
    # "Giá lăn bánh" (on-road price) = MSRP + reg_tax + plate + inspection + year-1
    # road-maintenance fee + year-1 civil insurance. Year-1 fees are paid upfront
    # at registration in Vietnam.
    on_road = reg["on_road"]

    fuel_path = fuel_price_path(car["type"], years, fuel_price_mode)
    _fw_mult, _city_mult = TRAFFIC_EFFICIENCY_MAP.get(car["type"], (1.0, 1.0))
    if rush_hour and city_ratio > 0:
        # Mirrors calculate_fuel_cost: the rush-hour toggle swaps the baseline
        # city multiplier for the per-powertrain gridlock/regen target.
        _city_mult = TRAFFIC_RUSH_HOUR_MULT.get(car["type"], 2.0)
    yearly_final_mult = _fw_mult + (_city_mult - _fw_mult) * city_ratio
    yearly_adjusted_consumption = car["consumption"] * yearly_final_mult
    annual_road = ROAD_MAINTENANCE_FEE_YEARLY
    annual_legal = annual_road + reg["insurance"]

    # Periodic inspection (đăng kiểm) schedule — on_road already books the first
    # inspection, so we only add the subsequent ones within the holding window.
    model_year = _model_year_for(car)
    purchase_year = (purchase_date or date.today()).year
    due = _inspection_ages(model_year, purchase_year, years)
    extra_ages = set(sorted(due)[1:]) if len(due) > 1 else set()
    age0 = max(0, purchase_year - model_year)

    parking_toll = calculate_parking_toll(area, 1, city_ratio, city=city)
    annual_parking = parking_toll["monthly_total"] * 12 if include_parking_toll else 0

    # Total maintenance over the full period (matches get_tco exactly), then
    # distribute per-year with 15% annual-escalation factors so the chart curve
    # shows rising maintenance while the TCO total stays invariant.
    total_maint_all = calculate_maintenance(km, car["type"], car.get("annual_maintenance"), years)
    esc_factors = [1.0 + 0.15 * (y - 1) for y in range(1, years + 1)]
    esc_sum = sum(esc_factors)

    yearly_data = []
    cumulative_operating = 0.0
    warnings: list[str] = []

    # Pre-compute the blended resale curve for all years before the loop.
    # This uses the continuous iteration loop (_blend_resale_curve) which:
    #   1. Computes both ML and parametric values for every year
    #   2. Blends them over a TRANSITION_WIDTH-year window at the ML horizon
    #   3. Runs a PAVA-style iterative correction for monotonicity
    #   4. Applies the VinFast floor to final values
    predictor = get_predictor()
    car_id = car.get("id")
    if car.get("depreciation_rate") is not None:
        # Custom depreciation rate — bypass ML/parametric blending entirely
        blended_curve = None
        ml_max_year = 0
    else:
        mt = predictor.get_car_max_training_year(
            car["brand"], car.get("segment", "C-Sedan"), car["type"])
        ml_max_year = mt if mt > 0 and years >= 1 else None
        if ml_max_year is not None:
            blended_curve = _blend_resale_curve(
                price, car["brand"], car.get("segment", "C-Sedan"),
                car["type"], annual_km=km, total_years=years,
                mt=mt, predictor=predictor, car_id=car_id)
        else:
            blended_curve = None

    for year in range(1, years + 1):
        # Maintenance escalates with age: distribute total via 15% factors so
        # sum matches get_tco's calculate_maintenance(km, ..., years).
        year_maint = round(total_maint_all * (1.0 + 0.15 * (year - 1)) / esc_sum)

        # Fuel follows the per-year glide path (forecast_avg) or stays flat
        # (current). Year-1 road + civil insurance are already absorbed in
        # `on_road` so we skip them in year 1's operating block to avoid
        # double-counting (matches the acquisition-block formula).
        year_fuel = round((km / 100) * yearly_adjusted_consumption * fuel_path[year - 1])
        year_inspection = INSPECTION_FEE if (age0 + year) in extra_ages else 0
        year_legal = (annual_legal if year > 1 else 0) + year_inspection
        year_parking = annual_parking

        cumulative_operating += year_fuel + year_maint + year_legal + year_parking

        # Resale value: use pre-blended curve when available, otherwise fall
        # through to calculate_resale (custom_rate path or no ML data).
        if blended_curve is not None:
            entry = blended_curve[year - 1]
            resale_at_year = entry["value"]
            resale_market = entry.get("market_value", resale_at_year)
            resale_guarantee = entry.get("guarantee_value", resale_at_year)
            # Track warnings: year beyond the per-car ML horizon is a parametric
            # extrapolation (the continuous blending loop already handled the
            # smooth ML→parametric transition in the blend zone).
            if year > mt:
                w = "resale.fallbackToParametric"
                if w not in warnings:
                    warnings.append(w)
        else:
            resale_at_year_result = calculate_resale(
                price,
                car["brand"],
                year,
                car["type"],
                car.get("segment", "C-Sedan"),
                annual_km=km,
                custom_rate=car.get("depreciation_rate"),
                car_id=car_id,
            )
            resale_at_year = resale_at_year_result["value"]
            resale_market = resale_at_year_result.get("market_value", resale_at_year)
            resale_guarantee = resale_at_year_result.get("guarantee_value", resale_at_year)
            if resale_at_year_result.get("warning"):
                w = resale_at_year_result["warning"]
                if w not in warnings:
                    warnings.append(w)

        depreciation_at_year = price - resale_at_year

        # Cumulative TCO = on-road price + cumulative operating costs - resale value at this point
        # This produces a concave curve: steep early (depreciation), flattening later
        cumulative_tco = on_road + cumulative_operating - resale_at_year

        yearly_data.append({
            "year": year,
            "year_label": str(year),
            "fuel": round(year_fuel),
            "maintenance": round(year_maint),
            "legal": round(year_legal),
            "inspection": round(year_inspection),
            "parking_toll": round(year_parking),
            "operating_cumulative": round(cumulative_operating),
            "resale": resale_at_year,
            "resale_market_value": round(resale_market),
            "resale_guarantee_value": round(resale_guarantee),
            "depreciation": round(depreciation_at_year),
            "cumulative_tco": round(cumulative_tco),
        })

    return yearly_data, warnings, ml_max_year


def get_fuel_breakdown(car, km, years, city_ratio, rush_hour=False,
                       fuel_price_mode="forecast_avg"):
    """Return a breakdown of fuel cost calculation for verbose display."""
    consumption = car["consumption"]
    car_type = car["type"]
    freeway_mult, city_mult = TRAFFIC_EFFICIENCY_MAP.get(car_type, (1.0, 1.0))
    if rush_hour and city_ratio > 0:
        city_mult = TRAFFIC_RUSH_HOUR_MULT.get(car_type, 2.0)
    final_mult = freeway_mult + (city_mult - freeway_mult) * city_ratio
    adjusted_consumption = consumption * final_mult

    if car_type == "ICE-D":
        current_price = DIESEL_PRICE_CURRENT_VND
        fuel_label = "Diesel"
        unit = "VND/L"
    elif car_type == "EV":
        current_price = EV_CHARGING_PRICE_VND
        fuel_label = "EV Charging"
        unit = "VND/kWh"
    else:
        current_price = PETROL_PRICE_CURRENT_VND
        fuel_label = "RON 95"
        unit = "VND/L"

    price = effective_fuel_price(car_type, years, fuel_price_mode)
    if fuel_price_mode == "current" or abs(price - current_price) < 0.5:
        price_label = f"{fuel_label} ({current_price:,} {unit}, today)"
    else:
        price_label = (f"{fuel_label} ({round(price):,} {unit} avg over {years}y, "
                       f"glide to forecast)")

    annual_fuel = (km / 100) * adjusted_consumption * price
    total_fuel = annual_fuel * years

    return {
        "consumption": round(consumption, 2),
        "adjusted_consumption": round(adjusted_consumption, 2),
        "freeway_mult": round(freeway_mult, 2),
        "city_mult": round(city_mult, 2),
        "final_mult": round(final_mult, 3),
        "price": round(price),
        "price_mode": fuel_price_mode,
        "price_label": price_label,
        "car_type": car_type,
        "annual_fuel": round(annual_fuel),
        "total_fuel": round(total_fuel),
        "years": years,
        "km": km,
        "city_ratio": city_ratio,
    }


def get_registration_breakdown(car, area, city: str | None = None):
    """Return a breakdown of on-road (giá lăn bánh) acquisition for verbose display.

    Mirrors the giá lăn bánh formula used by `get_tco` and `_zero_tco_dict`:
        on_road = price + reg_tax + plate_fee + inspection_fee
                  + year-1 road_maintenance_fee + year-1 civil_insurance

    Plate fee + reg-tax rate are gated by `is_area1_metro` for Area-1 cities
    (Thông tư 155/2025). The two year-1 fees are paid upfront at registration
    in Vietnam, so they belong in the acquisition block — not the multi-year
    operating tail. `total` covers the five non-price fees (reg subtotal).
    """
    price = car["price"]
    car_type = car["type"]
    seats = car.get("seats", 5)
    insurance_rate = CIVIL_INSURANCE_UNDER_6 if seats < 6 else CIVIL_INSURANCE_6_TO_11
    road_fee = ROAD_MAINTENANCE_FEE_YEARLY
    insurance = insurance_rate
    is_metro = is_area1_metro(city) if area == 1 else False
    tax_rate = ICE_REGISTRATION_RATE_CENTRAL_CITY if is_metro else ICE_REGISTRATION_RATE_STANDARD

    if car_type in ["ICE", "ICE-D", "HEV"]:
        tax = price * tax_rate
        tax_desc = f"{price:,} x {tax_rate*100:.0f}% = {tax:,.0f} VND"
    elif car_type == "EV":
        today = date.today()
        if today <= EV_EXEMPTION_END_DATE:
            tax = 0.0
            tax_desc = "EV exempt (before Feb 28, 2027)"
        else:
            tax = price * tax_rate * EV_POST_EXEMPTION_DISCOUNT
            tax_desc = f"{price:,} x {tax_rate*100:.0f}% x {EV_POST_EXEMPTION_DISCOUNT*100:.0f}% = {tax:,.0f} VND"
    else:
        tax = 0.0
        tax_desc = "N/A"

    if area == 1:
        plate = PLATE_FEE_METRO if is_metro else PLATE_FEE_NON_METRO_AREA1
    else:
        plate = PLATE_FEES[area]
    inspection = INSPECTION_FEE
    reg_subtotal = tax + plate + inspection
    total = reg_subtotal + road_fee + insurance  # 5 non-price fees
    on_road = price + total  # full acquisition block (giá lăn bánh)

    return {
        "price": price,
        "car_type": car_type,
        "seats": seats,
        "area": area,
        "tax_rate": tax_rate,
        "tax": round(tax),
        "tax_desc": tax_desc,
        "plate": round(plate),
        "inspection": round(inspection),
        "road_fee": round(road_fee),
        "insurance": round(insurance),
        "total": round(total),
        "on_road": round(on_road),
    }


if __name__ == "__main__":
    """Inline self-test for city-slug normalization."""
    cases = [
        # (input, expected_area, expected_metro)
        ("ho-chi-minh-city",       1, True),
        ("thanh-pho-ho-chi-minh",  1, True),
        ("ho chi minh city",       1, True),
        ("hochiminh",              1, True),
        ("hcmc",                   1, True),
        ("saigon",                 1, True),
        ("ha-noi",                 1, True),
        ("hanoi",                  1, True),
        ("da-nang",                1, False),
        ("thuathienhue",           1, False),
        ("thua-thien-hue",         1, False),
        ("ba-ria-vung-tau",        2, False),
        ("vinh-long",              2, False),
        ("",                       2, False),
    ]

    failures = []
    for inp, expected_area, expected_metro in cases:
        display, area = resolve_city(inp)
        metro = is_area1_metro(inp)
        print(
            f"{inp!r:40} -> display={display!r}, area={area}, metro={metro}"
        )
        if area != expected_area or metro != expected_metro:
            failures.append(
                f"FAIL {inp!r}: expected area={expected_area}, metro={expected_metro}; "
                f"got area={area}, metro={metro}"
            )

    if failures:
        for f in failures:
            print(f)
        raise AssertionError(
            f"{len(failures)} city-slug normalization case(s) failed"
        )
    print(f"\nAll {len(cases)} city-slug cases passed.")

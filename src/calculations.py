from src.config import *
from datetime import date
import json
import unicodedata
from pathlib import Path
from src.ml_model import get_predictor


def _strip_diacritics(text: str) -> str:
    """Normalize Vietnamese diacritics to ASCII for fuzzy matching."""
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def get_area_tier(city: str) -> int:
    """Resolve city name to area tier with fuzzy matching and diacritics support."""
    key = _strip_diacritics(city.lower().strip())
    if key in AREA1_CITIES:
        return 1
    if key in AREA2_PROVINCES:
        return 2
    return 2


def resolve_city(city: str) -> tuple[str, int]:
    """Resolve a city input to (display_name, area_tier) with fuzzy matching.

    Accepts diacritics, abbreviations, and common aliases.
    Returns the canonical display name and area tier.
    """
    key = _strip_diacritics(city.lower().strip())

    # Check direct matches in CITY_LIST
    for display, norm_key, area, diacritic_key in CITY_LIST:
        if key == norm_key or key == _strip_diacritics(diacritic_key):
            return display, area

    # Check AREA1_CITIES and AREA2_PROVINCES for any remaining entries
    if key in AREA1_CITIES:
        # Find the display name
        for display, norm_key, area, _ in CITY_LIST:
            if norm_key == key:
                return display, area
        return city.title(), 1
    if key in AREA2_PROVINCES:
        for display, norm_key, area, _ in CITY_LIST:
            if norm_key == key:
                return display, area
        return city.title(), 2

    # Fuzzy match: check if any city name starts with or contains the input
    best_match = None
    best_len = float("inf")
    for display, norm_key, area, diacritic_key in CITY_LIST:
        if key in norm_key or key in _strip_diacritics(diacritic_key):
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


def calculate_registration(price, city, car_type, purchase_date=None, area=None):
    """Registration tax + plate fee, auto-resolved by area tier."""
    if area is None:
        area = get_area_tier(city)
    tax_rate = ICE_REGISTRATION_RATE_CENTRAL_CITY if area == 1 else ICE_REGISTRATION_RATE_STANDARD

    if car_type in ["ICE", "ICE-D", "HEV"]:
        tax = price * tax_rate
    elif car_type == "EV":
        today = purchase_date or date.today()
        tax = 0.0 if today <= EV_EXEMPTION_END_DATE else price * tax_rate * EV_POST_EXEMPTION_DISCOUNT
    else:
        tax = 0.0

    plate = PLATE_FEES[area]
    return {
        "tax": tax,
        "plate": plate,
        "inspection": INSPECTION_FEE,
        "total": tax + plate + INSPECTION_FEE,
    }


def calculate_fuel_cost(km, consumption, car_type, city_ratio=0.0):
    """Adjusts fuel consumption based on city traffic ratio using the efficiency matrix."""
    if not consumption or consumption <= 0:
        return 0.0

    freeway_mult, city_mult = TRAFFIC_EFFICIENCY_MAP.get(car_type, (1.0, 1.0))
    final_mult = freeway_mult + (city_mult - freeway_mult) * city_ratio
    adjusted_consumption = consumption * final_mult

    if car_type in ["ICE", "HEV"]:
        price = PETROL_PRICE_VND
    elif car_type == "ICE-D":
        price = DIESEL_PRICE_VND
    else:
        price = EV_CHARGING_PRICE_VND

    return (km / 100) * adjusted_consumption * price


def calculate_opportunity_cost(principal, years, rate=SAVINGS_INTEREST_RATE):
    """Cumulative interest lost if capital were in a savings account."""
    if years <= 0:
        return 0.0
    try:
        return principal * ((1 + rate) ** years) - principal
    except OverflowError:
        return float('inf')


def get_hydro_risk_info(city):
    """Returns flood risk metadata based on city location."""
    key = _strip_diacritics(city.lower().strip())
    is_high_risk = key in HYDRO_RISK_CITIES
    return {
        "is_high_risk": is_high_risk,
        "risk_level": "High (Flood Prone)" if is_high_risk else "Moderate",
        "estimate": HYDRO_RISK_ESTIMATE if is_high_risk else HYDRO_RISK_ESTIMATE * 0.2,
    }


def calculate_maintenance(km, car_type, base_cost=8_000_000, years=1):
    annual = base_cost * (EV_MAINTENANCE_DISCOUNT if car_type == "EV" else 1.0)
    total = annual * years
    milestones = (km * years) // MAINTENANCE_MAJOR_KM
    if car_type == "EV":
        cost = MAINTENANCE_MAJOR_COST_EV
    elif car_type == "ICE-D":
        cost = MAINTENANCE_MAJOR_COST_ICE_D
    else:
        cost = MAINTENANCE_MAJOR_COST_ICE

    return total + milestones * cost


def resolve_liquidity_bonus(brand, car_type, segment):
    """'Bespoke Logic' for market demand multipliers."""
    if car_type == "HEV":
        return LIQUIDITY_LOGIC_MAP["HEV"]

    tier = BRAND_LIQUIDITY_MAP.get(brand, "Tier 3")

    if car_type == "EV":
        return LIQUIDITY_LOGIC_MAP["EV"].get(brand, LIQUIDITY_LOGIC_MAP["EV"]["Default"])

    tier_logic = LIQUIDITY_LOGIC_MAP.get(tier, LIQUIDITY_LOGIC_MAP["Tier 3"])
    return tier_logic.get(segment, tier_logic.get("Default", 1.0))


def calculate_resale(price, brand, years, car_type, segment, annual_km=15000, custom_rate=None):
    """Calculates residual value using ML prediction first, falling back to parametric.
    Returns (resale_value, logic_tag) tuple where logic_tag is 'ml', 'parametric', or 'custom'."""
    if years == 0:
        return price, "parametric"

    if custom_rate is not None:
        return price * ((1 - custom_rate) ** years), "custom"

    # Try ML prediction first
    try:
        predictor = get_predictor()
        ml_result = predictor.predict_resale(brand, segment, car_type, years, annual_km, price)
        if ml_result["ml_prediction"] is not None:
            predicted_pct = ml_result["ml_prediction"]
            if 0.05 <= predicted_pct <= 1.0:
                return price * predicted_pct, "ml"
    except Exception:
        pass  # Fall through to parametric

    # Parametric path (fallback)
    tier_label = BRAND_LIQUIDITY_MAP.get(brand, "Tier 3")
    category = "EV_Market" if car_type == "EV" else tier_label
    seg_adj = SEGMENT_DEPRECIATION_MAP.get(segment, {}).get("decay_adj", 1.0)
    params = DEPRECIATION_EQ_PARAMS.get(category, DEPRECIATION_EQ_PARAMS["Tier 3"])
    decay = params["annual_decay"] * seg_adj

    # Extra 1.5% loss per 10k km over 15k/yr
    usage_penalty = max(0, (annual_km - 15000) / 10000) * 0.015
    decay += usage_penalty

    retention = (1 - params["y1_drop"]) * ((1 - decay) ** (years - 1))
    bonus = resolve_liquidity_bonus(brand, car_type, segment)
    retention *= bonus

    return price * retention, "parametric"


def get_tco(car, city, km, years=5, purchase_date=None, area=None, city_ratio=0.0):
    """Master TCO: Acquisition + Running - Resale"""
    price = car["price"]
    reg = calculate_registration(price, city, car["type"], purchase_date, area=area)
    on_road = price + reg["total"]

    fuel = calculate_fuel_cost(km, car["consumption"], car["type"], city_ratio) * years
    maint = calculate_maintenance(km, car["type"], car.get("annual_maintenance", 8_000_000), years)
    road_fees = ROAD_MAINTENANCE_FEE_YEARLY * years
    seats = car.get("seats", 5)
    insurance_rate = CIVIL_INSURANCE_UNDER_6 if seats < 6 else CIVIL_INSURANCE_6_TO_11
    insurance = insurance_rate * years
    operating = fuel + maint + road_fees + insurance

    # Parking & Toll estimates (scaled by city/highway split)
    parking_toll = calculate_parking_toll(area or get_area_tier(city), years, city_ratio)

    resale, resale_logic = calculate_resale(
        price,
        car["brand"],
        years,
        car["type"],
        car.get("segment", "C-Sedan"),
        annual_km=km,
        custom_rate=car.get("depreciation_rate"),
    )
    depreciation = price - resale

    # [v0.5.0] Market Research Factors
    opp_cost = calculate_opportunity_cost(on_road, years)
    liquidity = BRAND_LIQUIDITY_MAP.get(car.get("brand"), "Tier 3 (Niche)")
    hydro = get_hydro_risk_info(city)

    tco = (on_road + operating) - resale

    return {
        "price": price,
        "reg": reg,
        "reg_tax": reg["tax"],
        "on_road": on_road,
        "fuel": fuel,
        "maint": maint,
        "legal": road_fees + insurance,
        "operating": operating,
        "parking_toll": parking_toll,
        "resale": resale,
        "resale_logic": resale_logic,
        "depreciation": depreciation,
        "opp_cost": opp_cost,
        "liquidity": liquidity,
        "hydro_risk": hydro,
        "tco": tco,
        "true_financial_impact": tco + opp_cost,
        "monthly": operating / (years * 12),
    }


def calculate_parking_toll(area: int, years: int, city_ratio: float = 0.0) -> dict:
    """
    Calculate parking & toll estimates based on area tier and city/highway split.
    - Parking scales with city driving (city_ratio)
    - Tolls scale with highway driving (1 - city_ratio)
    """
    area_key = f"area{area}" if area in (1, 2, 3) else "area2"
    estimates = PARKING_TOLL_ESTIMATES.get(area_key, PARKING_TOLL_ESTIMATES["area2"])

    # Scale parking by city driving, tolls by highway driving
    parking_monthly = estimates["parking_monthly"] * (0.5 + city_ratio)
    toll_monthly = estimates["toll_monthly"] * (1.5 - city_ratio)

    monthly_total = parking_monthly + toll_monthly
    total_over_period = monthly_total * 12 * years

    return {
        "monthly_parking": parking_monthly,
        "monthly_toll": toll_monthly,
        "monthly_total": monthly_total,
        "total_over_period": total_over_period,
    }


def calculate_loan_schedule(on_road_price: float, down_pct: float, annual_rate: float, term_years: int) -> dict:
    """
    Calculate loan schedule using reducing balance method (standard in Vietnam).
    Returns monthly payment, total interest, total repayment, and effective cost.
    """
    if down_pct <= 0 or down_pct >= 100:
        down_pct = 30.0

    loan_amount = on_road_price * (1 - down_pct / 100)
    monthly_rate = annual_rate / 12
    num_payments = term_years * 12

    if monthly_rate == 0:
        monthly_payment = loan_amount / num_payments
    else:
        # Standard reducing balance formula
        monthly_payment = loan_amount * monthly_rate * (1 + monthly_rate) ** num_payments / ((1 + monthly_rate) ** num_payments - 1)

    total_repayment = monthly_payment * num_payments
    total_interest = total_repayment - loan_amount
    effective_cost = on_road_price + total_interest  # Cash price + financing cost

    return {
        "loan_amount": loan_amount,
        "down_payment": on_road_price * down_pct / 100,
        "monthly_payment": monthly_payment,
        "total_interest": total_interest,
        "total_repayment": total_repayment,
        "effective_cost": effective_cost,
        "term_months": num_payments,
        "annual_rate": annual_rate,
    }


def get_fuel_breakdown(car, km, years, city_ratio):
    """Return a breakdown of fuel cost calculation for verbose display."""
    consumption = car["consumption"]
    car_type = car["type"]
    freeway_mult, city_mult = TRAFFIC_EFFICIENCY_MAP.get(car_type, (1.0, 1.0))
    final_mult = freeway_mult + (city_mult - freeway_mult) * city_ratio
    adjusted_consumption = consumption * final_mult

    if car_type in ["ICE", "HEV"]:
        price = PETROL_PRICE_VND
        price_label = f"RON 95 ({PETROL_PRICE_VND:,} VND/L)"
    elif car_type == "ICE-D":
        price = DIESEL_PRICE_VND
        price_label = f"Diesel ({DIESEL_PRICE_VND:,} VND/L)"
    else:
        price = EV_CHARGING_PRICE_VND
        price_label = f"EV Charging ({EV_CHARGING_PRICE_VND:,} VND/kWh)"

    annual_fuel = (km / 100) * adjusted_consumption * price
    total_fuel = annual_fuel * years

    return {
        "consumption": consumption,
        "adjusted_consumption": adjusted_consumption,
        "freeway_mult": freeway_mult,
        "city_mult": city_mult,
        "final_mult": final_mult,
        "price": price,
        "price_label": price_label,
        "car_type": car_type,
        "annual_fuel": annual_fuel,
        "total_fuel": total_fuel,
        "years": years,
        "km": km,
        "city_ratio": city_ratio,
    }


def get_registration_breakdown(car, area):
    """Return a breakdown of registration cost calculation for verbose display."""
    price = car["price"]
    car_type = car["type"]
    tax_rate = ICE_REGISTRATION_RATE_CENTRAL_CITY if area == 1 else ICE_REGISTRATION_RATE_STANDARD

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

    plate = PLATE_FEES[area]
    inspection = INSPECTION_FEE
    total = tax + plate + inspection

    return {
        "price": price,
        "car_type": car_type,
        "area": area,
        "tax_rate": tax_rate,
        "tax": tax,
        "tax_desc": tax_desc,
        "plate": plate,
        "inspection": inspection,
        "total": total,
    }

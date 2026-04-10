from src.config import *
from datetime import date
import json
from pathlib import Path

def get_area_tier(city: str) -> int:
    key = city.lower().strip()
    if key in AREA1_CITIES: return 1
    if key in AREA2_PROVINCES: return 2
    return 2

def load_data():
    cars_file = Path(__file__).parent.parent / "data" / "cars.json"
    if not cars_file.exists(): return {}
    with cars_file.open('r', encoding='utf-8') as f:
        raw = json.load(f) or {}
    try:
        sorted_items = sorted(raw.items(), key=lambda kv: (kv[1].get('brand', '').lower(), kv[1].get('model', '').lower()))
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
    if years <= 0: return 0.0
    return principal * ((1 + rate) ** years) - principal

def get_hydro_risk_info(city):
    """Returns flood risk metadata based on city location."""
    is_high_risk = city.lower().strip() in ["hanoi", "hn", "ho chi minh", "hcmc", "saigon"]
    return {
        "is_high_risk": is_high_risk,
        "risk_level": "High (Flood Prone)" if is_high_risk else "Moderate",
        "estimate": HYDRO_RISK_ESTIMATE if is_high_risk else HYDRO_RISK_ESTIMATE * 0.2
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
    """Encapsulates the 'Bespoke Logic' for market demand multipliers."""
    if car_type == "HEV":
        return LIQUIDITY_LOGIC_MAP["HEV"]
    
    tier = BRAND_LIQUIDITY_MAP.get(brand, "Tier 3")
    
    if car_type == "EV":
        return LIQUIDITY_LOGIC_MAP["EV"].get(brand, LIQUIDITY_LOGIC_MAP["EV"]["Default"])
    
    # Tier-based Segment Logic
    tier_logic = LIQUIDITY_LOGIC_MAP.get(tier, LIQUIDITY_LOGIC_MAP["Tier 3"])
    return tier_logic.get(segment, tier_logic.get("Default", 1.0))

def calculate_resale(price, brand, years, car_type, segment, annual_km=15000, custom_rate=None):
    """Calculates residual value using engine-resolved class liquidity bonus.
    If custom_rate is provided (from wizard), uses it as a flat annual decay."""
    if years == 0: return price

    if custom_rate is not None:
        # Wizard path: flat annual decay, no showroom or bonus adjustments
        return price * ((1 - custom_rate) ** years)

    # Parametric path
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

    return price * retention

def get_tco(car, city, km, years=5, purchase_date=None, area=None, city_ratio=0.0):
    """Master TCO: Acquisition + Running - Resale, with market research factors."""
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

    resale = calculate_resale(
        price,
        car["brand"],
        years,
        car["type"],
        car.get("segment", "C-Sedan"),
        annual_km=km,
        custom_rate=car.get("depreciation_rate")
    )
    depreciation = price - resale

    # [v0.4.0] Market Research Factors
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
        "resale": resale,
        "resale_logic": "Custom" if car.get("depreciation_rate") else "Parametric",
        "depreciation": depreciation,
        "opp_cost": opp_cost,
        "liquidity": liquidity,
        "hydro_risk": hydro,
        "tco": tco,
        "true_financial_impact": tco + opp_cost,
        "monthly": operating / (years * 12),
    }

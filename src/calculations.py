from src.config import *
from datetime import date

def calculate_registration(price, city, car_type, purchase_date=None, area=None):
    """Registration tax + plate fee, auto-resolved by area tier."""
    if area is None:
        area = get_area_tier(city)
    tax_rate = ICE_REGISTRATION_RATE_CENTRAL_CITY if area == 1 else ICE_REGISTRATION_RATE_STANDARD

    if car_type == "ICE":
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
    
    price = PETROL_PRICE_VND if car_type in ["ICE", "HEV"] else EV_CHARGING_PRICE_VND
    return (km / 100) * adjusted_consumption * price

def calculate_opportunity_cost(principal, years, rate=SAVINGS_INTEREST_RATE):
    """Cumulative interest lost if capital were in a savings account."""
    if years <= 0: return 0.0
    return principal * ((1 + rate) ** years) - principal

def get_hydro_risk_info(city):
    """Returns flood risk metadata based on city location."""
    area = get_area_tier(city)
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
    cost = MAINTENANCE_MAJOR_COST_EV if car_type == "EV" else MAINTENANCE_MAJOR_COST_ICE
    return total + milestones * cost

def calculate_resale(price, years, car_type, rate=None, brand=None, segment=None, liquidity_bonus=1.0):
    """[v0.4.0] Data-driven geometric decay models."""
    if years == 0:
        return price
        
    if rate is not None:
        initial_drop = rate + DEPRECIATION_SHOWROOM_EXIT_PENALTY
        return price * (1 - initial_drop) * ((1 - rate) ** (years - 1))

    # 1. Resolve base category
    tier_label = BRAND_LIQUIDITY_MAP.get(brand, "Tier 3")
    category = "EV_Market" if car_type == "EV" else tier_label
    
    # 2. Segment Adjustment from metadata
    seg_adj = SEGMENT_DEPRECIATION_MAP.get(segment, {}).get("decay_adj", 1.0)

    params = DEPRECIATION_EQ_PARAMS.get(category, DEPRECIATION_EQ_PARAMS["Tier 3"])
    
    # 3. Apply adjusted decay
    decay = params["annual_decay"] * seg_adj
    retention = (1 - params["y1_drop"]) * ((1 - decay) ** (years - 1))
    
    # 4. Apply per-model Liquidity Bonus from metadata
    retention *= (liquidity_bonus or 1.0)

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

    # Pass new data-driven parameters to the resale engine
    resale = calculate_resale(
        price, 
        years, 
        car["type"], 
        rate=car.get("depreciation_rate"), 
        brand=car.get("brand"),
        segment=car.get("segment"),
        liquidity_bonus=car.get("liquidity_bonus", 1.0)
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

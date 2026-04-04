from src.config import *
from datetime import date

def calculate_registration(price, city, car_type, purchase_date=None, area=None):
    """[v0.3.0] Registration tax + plate fee, auto-resolved by area tier (or explicit override)."""
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

def calculate_fuel_cost(km, consumption, car_type):
    if not consumption or consumption <= 0:
        return 0.0
    price = PETROL_PRICE_VND if car_type == "ICE" else EV_CHARGING_PRICE_VND
    return (km / 100) * consumption * price

def calculate_maintenance(km, car_type, base_cost=8_000_000, years=1):
    annual = base_cost * (EV_MAINTENANCE_DISCOUNT if car_type == "EV" else 1.0)
    total = annual * years
    milestones = (km * years) // MAINTENANCE_MAJOR_KM
    cost = MAINTENANCE_MAJOR_COST_EV if car_type == "EV" else MAINTENANCE_MAJOR_COST_ICE
    return total + milestones * cost

def calculate_resale(price, years, car_type, rate=None, brand=None):
    """[v0.2.0] Parametric depreciation with optional custom rate override."""
    if rate is not None:
        val = price * (1 - rate - DEPRECIATION_SHOWROOM_EXIT_PENALTY)
        for _ in range(years - 1):
            val *= (1 - rate)
        return val

    params = DEPRECIATION_EQ_PARAMS["vinfast_ev" if (brand == "VinFast" and car_type == "EV") else "ice"]
    if years == 0:
        return price
    retention = (1 - params["y1_drop"]) * ((1 - params["annual_decay"]) ** (years - 1))
    return price * retention

def get_tco(car, city, km, years=5, purchase_date=None, area=None):
    """Master TCO: Acquisition + Running - Resale. Area tier auto-detected from city (or override)."""
    price = car["price"]
    reg = calculate_registration(price, city, car["type"], purchase_date, area=area)

    fuel = calculate_fuel_cost(km, car["consumption"], car["type"]) * years
    maint = calculate_maintenance(km, car["type"], car.get("annual_maintenance", 8_000_000), years)
    road_fees = ROAD_MAINTENANCE_FEE_YEARLY * years
    insurance = CIVIL_INSURANCE_YEARLY * years
    operating = fuel + maint + road_fees + insurance

    resale = calculate_resale(price, years, car["type"], car.get("depreciation_rate"), car.get("brand"))
    depreciation = price - resale

    tco = (price + reg["total"] + operating) - resale

    return {
        "price": price,
        "reg": reg,
        "on_road": price + reg["total"],
        "fuel": fuel,
        "maint": maint,
        "legal": road_fees + insurance,
        "operating": operating,
        "resale": resale,
        "resale_logic": "Custom" if car.get("depreciation_rate") else "Parametric",
        "depreciation": depreciation,
        "tco": tco,
        "monthly": operating / (years * 12),
    }

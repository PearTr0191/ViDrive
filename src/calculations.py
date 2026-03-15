from src.config import *
from datetime import date

# --- Core Math Functions ---

def calculate_registration(price, city, car_type, purchase_date=None):
    # Registration tax calculation
    tax_rate = ICE_REGISTRATION_RATE_CITY if city.lower() in CITIES_WITH_HIGH_REG_FEE else ICE_REGISTRATION_RATE_PROVINCE
    
    tax_amount = 0.0
    if car_type == "ICE":
        tax_amount = price * tax_rate
    elif car_type == "EV":
        today = purchase_date or date.today()
        # EVs are tax-exempt if bought before the exemption end date
        if today <= EV_EXEMPTION_END_DATE:
            tax_amount = 0.0
        else:
            tax_amount = price * tax_rate * EV_POST_EXEMPTION_DISCOUNT
            
    plate_fee = PLATE_FEE_CITY if city.lower() in CITIES_WITH_HIGH_REG_FEE else PLATE_FEE_PROVINCE
    
    return {
        "tax": tax_amount,
        "plate": plate_fee,
        "inspection": INSPECTION_FEE,
        "total": tax_amount + plate_fee + INSPECTION_FEE
    }

def calculate_fuel_cost(km, consumption, car_type):
    # Safety check for invalid/zero consumption
    if not consumption or consumption <= 0:
        return 0.0
    price = PETROL_PRICE_VND if car_type == "ICE" else EV_CHARGING_PRICE_VND
    return (km / 100) * consumption * price

def calculate_maintenance(km, car_type, base_cost=8000000, years=1):
    annual = base_cost * (EV_MAINTENANCE_DISCOUNT if car_type == "EV" else 1.0)
    total = annual * years
    
    # Milestone checks every 40,000 km
    milestones = (km * years) // MAINTENANCE_MAJOR_KM
    cost = MAINTENANCE_MAJOR_COST_EV if car_type == "EV" else MAINTENANCE_MAJOR_COST_ICE
    total += milestones * cost
    return total

def calculate_resale(price, years, car_type, rate=None, brand=None):
    # Custom depreciation if provided
    if rate is not None:
        val = price * (1 - rate - DEPRECIATION_SHOWROOM_EXIT_PENALTY)
        for _ in range(years - 1):
            val *= (1 - rate)
        return val
    
    # Realistic exponential decay curve
    params = DEPRECIATION_EQ_PARAMS["vinfast_ev" if (brand == "VinFast" and car_type == "EV") else "ice"]
    if years == 0: return price
    retention = (1 - params["y1_drop"]) * ((1 - params["annual_decay"]) ** (years - 1))
    return price * retention

def get_tco(car, city, km, years=5, purchase_date=None):
    price = car["price"]
    reg = calculate_registration(price, city, car["type"], purchase_date)
    
    # Calc running costs
    fuel = calculate_fuel_cost(km, car["consumption"], car["type"]) * years
    maint = calculate_maintenance(km, car["type"], car.get("annual_maintenance", 8000000), years)
    
    road_fees = ROAD_MAINTENANCE_FEE_YEARLY * years
    insurance = CIVIL_INSURANCE_YEARLY * years
    
    operating_total = fuel + maint + road_fees + insurance
    
    # Calc end value
    resale = calculate_resale(price, years, car["type"], car.get("depreciation_rate"), car.get("brand"))
    depreciation = price - resale
    
    # Final TCO: (Purchase + Upfront + Operating) - Resale Price
    tco = (price + reg["total"] + operating_total) - resale
    
    return {
        "price": price,
        "reg": reg,
        "on_road": price + reg["total"],
        "fuel": fuel,
        "maint": maint,
        "legal": road_fees + insurance,
        "operating": operating_total,
        "resale": resale,
        "resale_logic": "Custom" if car.get("depreciation_rate") else "Parametric",
        "depreciation": depreciation,
        "tco": tco,
        "monthly": (fuel + maint + road_fees + insurance) / (years * 12)
    }

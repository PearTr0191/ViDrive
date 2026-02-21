from src.config import *
from datetime import date

# --- Core Math Functions ---

def calculate_registration(price, city, car_type, purchase_date=None):
    # Determine the rate based on city
    if city.lower() in CITIES_WITH_HIGH_REG_FEE:
        rate = ICE_REGISTRATION_RATE_CITY
    else:
        rate = ICE_REGISTRATION_RATE_PROVINCE
    
    # ICE logic
    if car_type == "ICE":
        return price * rate
        
    # EV logic
    if car_type == "EV":
        today = purchase_date or date.today()
        # Check if we are in the exemption period
        if today <= EV_EXEMPTION_END_DATE:
            return 0.0
        else:
            # After exemption, it's 50% of the ICE rate
            return price * rate * EV_POST_EXEMPTION_DISCOUNT
    
    return 0.0

def calculate_fuel_cost(km, consumption, car_type):
    # Simple fuel math
    # KM / 100 * Liters_or_kWh * Price
    if car_type == "ICE":
        price_per_unit = PETROL_PRICE_VND
    else:
        price_per_unit = EV_CHARGING_PRICE_VND
    
    return (km / 100) * consumption * price_per_unit

def calculate_maintenance(km, car_type, base_cost=8000000):
    # EVs are cheaper to maintain
    cost = base_cost
    if car_type == "EV":
        cost = cost * EV_MAINTENANCE_DISCOUNT
    return cost

def calculate_battery_rental(km, car_data):
    # Only for VinFast EVs with rental
    if car_data.get("type") != "EV":
        return 0.0
    
    rent_price = car_data.get("battery_rental_monthly", 0)
    
    # Check if there are tiers (like for VF5, VF3)
    tiers = car_data.get("battery_rental_tiers")
    if tiers:
        monthly_km = km / 12
        if monthly_km <= BATTERY_TIER_LOW_KM_MONTHLY:
            rent_price = tiers.get("1500", rent_price)
        elif monthly_km <= BATTERY_TIER_MID_KM_MONTHLY:
            rent_price = tiers.get("3000", rent_price)
        else:
            rent_price = tiers.get("unlimited", rent_price)
            
    return float(rent_price) * 12

def calculate_resale(price, years, car_type, rate=None):
    # Depreciation formula: Price * (1 - rate)^years
    if rate is None:
        if car_type == "EV":
            rate = DEFAULT_DEPRECIATION_EV
        else:
            rate = DEFAULT_DEPRECIATION_ICE
            
    final_value = price * ((1 - rate) ** years)
    return final_value

def get_tco(car, city, km, years=5, purchase_date=None, no_rental=False):
    # 1. Get initial costs
    price = car["price"]
    reg_fee = calculate_registration(price, city, car["type"], purchase_date)
    
    # 2. Get annual costs
    annual_fuel = calculate_fuel_cost(km, car["consumption"], car["type"])
    annual_maint = calculate_maintenance(km, car["type"], car.get("annual_maintenance", 8000000))
    
    annual_battery = 0
    if not no_rental:
        annual_battery = calculate_battery_rental(km, car)

    # 3. Scale to TCO period
    total_fuel = annual_fuel * years
    total_maint = annual_maint * years
    total_battery = annual_battery * years
    
    # 4. Depreciation
    resale = calculate_resale(price, years, car["type"], car.get("depreciation_rate"))
    
    # 5. Final Formula
    # Cost = (Buy + Reg + Fuel + Maint + Battery) - Resale
    total_cost = (price + reg_fee + total_fuel + total_maint + total_battery) - resale
    
    monthly_run_cost = (annual_fuel + annual_maint + annual_battery) / 12
    
    return {
        "price": price,
        "reg_fee": reg_fee,
        "fuel_total": total_fuel,
        "maint_total": total_maint,
        "battery_total": total_battery,
        "resale": resale,
        "tco": total_cost,
        "monthly": monthly_run_cost
    }

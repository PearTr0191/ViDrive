from datetime import date

# --- Fuel Prices (March 2026) ---
PETROL_PRICE_VND = 25575   # RON 95-III
EV_CHARGING_PRICE_VND = 3858  # VinFast public, incl. VAT

# --- Registration ---
ICE_REGISTRATION_RATE_STANDARD = 0.10
ICE_REGISTRATION_RATE_CENTRAL_CITY = 0.12
EV_EXEMPTION_END_DATE = date(2027, 2, 28)
EV_POST_EXEMPTION_DISCOUNT = 0.50

# --- Area Classification (6 Cities, 28 Provinces) ---
# Area 1: Centrally Governed Cities — 20M plate, 12% reg tax
AREA1_CITIES = {
    "hanoi", "hn", "ha noi",
    "ho chi minh", "hcmc", "saigon",
    "hue", "da nang", "can tho", "hai phong",
}

# Area 2: Provincial capitals & urban districts
AREA2_PROVINCES = {
    "an giang", "bac ninh", "ca mau", "cao bang",
    "dak lak", "dien bien", "dong nai", "dong thap",
    "gia lai", "ha tinh", "hung yen", "khanh hoa",
    "lai chau", "lam dong", "lang son", "lao cai",
    "nghe an", "ninh binh", "phu tho", "quang ngai",
    "quang ninh", "quang tri", "son la", "thai nguyen",
    "thanh hoa", "tay ninh", "tuyen quang", "vinh long",
}

def get_area_tier(city: str) -> int:
    """Return 1, 2, or 3 based on the input city/province name."""
    key = city.lower().strip()
    if key in AREA1_CITIES:
        return 1
    if key in AREA2_PROVINCES:
        return 2
    return 2  # default to provincial if unrecognized

# --- On-Road Fees ---
PLATE_FEES = {1: 20_000_000, 2: 1_000_000, 3: 200_000}
INSPECTION_FEE = 340_000
ROAD_MAINTENANCE_FEE_YEARLY = 1_560_000
CIVIL_INSURANCE_YEARLY = 480_700

# --- Maintenance ---
EV_MAINTENANCE_DISCOUNT = 0.70
MAINTENANCE_MAJOR_KM = 40_000
MAINTENANCE_MAJOR_COST_ICE = 5_000_000
MAINTENANCE_MAJOR_COST_EV = 1_500_000

# --- Depreciation ---
# V(t) = P × (1 - y1_drop) × (1 - annual_decay)^(t-1)
DEPRECIATION_EQ_PARAMS = {
    "ice":        {"y1_drop": 0.15, "annual_decay": 0.094},
    "vinfast_ev": {"y1_drop": 0.10, "annual_decay": 0.070},
}
DEPRECIATION_SHOWROOM_EXIT_PENALTY = 0.05

# --- Data Recency ---
LAST_UPDATED = date(2026, 3, 14)
DATA_RECENCY_DAYS = 270

def fmt_vnd(amount):
    return f"{amount:,.0f} VND"
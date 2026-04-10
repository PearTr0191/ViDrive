from datetime import date

# --- Fuel Prices (9-month weighted average, Apr 2026) ---
PETROL_PRICE_VND = 23850   # RON 95-III
DIESEL_PRICE_VND = 21850   # 9-month weighted average (Jul 2025 - Mar 2026)
EV_CHARGING_PRICE_VND = 2150  # 5-year weighted avg incl. 2027 promo end

# --- Registration ---
ICE_REGISTRATION_RATE_STANDARD = 0.10
ICE_REGISTRATION_RATE_CENTRAL_CITY = 0.12
EV_EXEMPTION_END_DATE = date(2027, 2, 28)
EV_POST_EXEMPTION_DISCOUNT = 0.50

# --- Area Classification ---
# Area 1: Central cities
AREA1_CITIES = {
    "hanoi", "hn", "ha noi",
    "ho chi minh", "hcmc", "saigon",
    "hue", "da nang", "can tho", "hai phong",
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

# --- On-Road Fees ---
PLATE_FEES = {1: 20_000_000, 2: 1_000_000, 3: 200_000}
INSPECTION_FEE = 290_000
ROAD_MAINTENANCE_FEE_YEARLY = 1_560_000
CIVIL_INSURANCE_UNDER_6 = 437_000
CIVIL_INSURANCE_6_TO_11 = 794_000

# --- Maintenance ---
EV_MAINTENANCE_DISCOUNT = 0.70
MAINTENANCE_MAJOR_KM = 40_000
MAINTENANCE_MAJOR_COST_ICE = 5_000_000
MAINTENANCE_MAJOR_COST_ICE_D = 6_500_000
MAINTENANCE_MAJOR_COST_EV = 1_500_000

# --- Market Factors ---
SAVINGS_INTEREST_RATE = 0.065
TRAFFIC_EFFICIENCY_MAP = {
    "ICE": (0.90, 1.50),
    "ICE-D": (0.80, 1.30),
    "HEV": (1.05, 0.95),
    "EV":  (1.12, 0.90)
}
HYDRO_RISK_ESTIMATE = 120_000_000

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
        "Default": 1.02
    },
    "Tier 2": {
        "D-SUV": 1.02,
        "Pickup": 1.05,
        "Default": 0.98
    },
    "EV": {
        "VinFast": 0.90,
        "Default": 0.80
    },
    "Tier 3": {
        "Default": 0.82
    }
}

# Segment Depreciation Multipliers
SEGMENT_DEPRECIATION_MAP = {
    "A-Hatch":   {"decay_adj": 1.10},
    "B-Hatch":   {"decay_adj": 1.05},
    "A-SUV":     {"decay_adj": 0.95},
    "B-Sedan":   {"decay_adj": 0.85},
    "C-Sedan":   {"decay_adj": 1.00},
    "D-Sedan":   {"decay_adj": 1.30},
    "B-SUV":     {"decay_adj": 0.82},
    "C-SUV":     {"decay_adj": 0.85},
    "D-SUV":     {"decay_adj": 1.40},
    "MPV":       {"decay_adj": 1.15},
    "Pickup":    {"decay_adj": 1.30},
    "EV-Mini":   {"decay_adj": 1.00},
}

# Supported Wizard Segments
WIZARD_SEGMENTS = [
    "B-Sedan", "C-Sedan", "D-Sedan", "B-SUV", "C-SUV", "D-SUV", 
    "MPV", "Pickup", "A-Hatch", "B-Hatch", "A-SUV", "EV-Mini"
]

# Depreciation Engine
DEPRECIATION_EQ_PARAMS = {
    "Tier 1":    {"y1_drop": 0.08, "annual_decay": 0.065},
    "Tier 2":    {"y1_drop": 0.10, "annual_decay": 0.070},
    "Tier 3":    {"y1_drop": 0.18, "annual_decay": 0.080},
    "EV_Market": {"y1_drop": 0.20, "annual_decay": 0.085},
}
DEPRECIATION_SHOWROOM_EXIT_PENALTY = 0.05

LAST_UPDATED = date(2026, 4, 4)
DATA_RECENCY_DAYS = 270
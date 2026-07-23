from datetime import date

# --- Fuel Prices (VND/liter, May 2026) ---
PETROL_PRICE_VND = 24150   # RON 95-III (May 28 2026 adjustment)
DIESEL_PRICE_VND = 27651   # DO 0.05S-II (May 30 2026 adjustment)
EV_CHARGING_PRICE_VND = 3858  # V-Green standard rate (since Mar 2024)

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
# Area 1: Hanoi, HCMC, Da Nang, Hue, Can Tho, Hai Phong
# Area 2/3: remaining provinces (unified rate)
PLATE_FEES = {1: 14_000_000, 2: 140_000, 3: 140_000}
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
        "VinFast": 0.90,
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
    "EV_Market": {"y1_drop": 0.20, "annual_decay": 0.082},
}
DEPRECIATION_SHOWROOM_EXIT_PENALTY = 0.05

# --- Parking & Toll Estimates (Monthly, VND) ---
# Based on city/highway driving split: tolls scale with highway km, parking with city km
# Area 1: Major city centers (Hanoi/HCMC core) - high parking, high tolls
# Area 2: City/Town - moderate parking, moderate tolls
# Area 3: Rural/District - low parking, minimal tolls
PARKING_TOLL_ESTIMATES = {
    "area1": {"parking_monthly": 1_200_000, "toll_monthly": 600_000},
    "area2": {"parking_monthly": 400_000,   "toll_monthly": 200_000},
    "area3": {"parking_monthly": 100_000,   "toll_monthly": 50_000},
}

# --- Flood / Hydro Risk Zones ---
# Cities with high flood risk (Hanoi, HCMC)
HYDRO_RISK_CITIES = {"hanoi", "hn", "ho chi minh", "hcmc", "saigon"}

LAST_UPDATED = date(2026, 7, 14)
DATA_RECENCY_DAYS = 60

# --- Persistence ---
HISTORY_DIR = "~/.vidrive"
HISTORY_FILE = "history.json"
MAX_HISTORY_ENTRIES = 50

# --- Comparison ---
MAX_COMPARISON_CARS = 10

# --- App Version ---
APP_VERSION = "1.0.0"

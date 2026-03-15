from datetime import date

# Prices (Cross-checked March 2026)
PETROL_PRICE_VND = 25575   # RON 95-III, Petrolimex 12/03/2026
EV_CHARGING_PRICE_VND = 3858  # VinFast public charging, incl. VAT

# Registration (Cross-checked March 2026)
ICE_REGISTRATION_RATE_CITY = 0.10     # Luật Lệ phí trước bạ 2024
ICE_REGISTRATION_RATE_PROVINCE = 0.10  # Provinces may add up to 50%
EV_EXEMPTION_END_DATE = date(2027, 2, 28)
EV_POST_EXEMPTION_DISCOUNT = 0.50
CITIES_WITH_HIGH_REG_FEE = {"hn", "hanoi", "hcmc", "ho chi minh", "ha noi", "saigon"}

# Maintenance
EV_MAINTENANCE_DISCOUNT = 0.70

# Depreciation - Parametric Equation (Maximum Realism)
# Value = Price * (1 - y1_drop) * (1 - annual_decay)^(years - 1)
DEPRECIATION_EQ_PARAMS = {
    "ice":         {"y1_drop": 0.15, "annual_decay": 0.094}, # ~56% retention at Year 5
    "vinfast_ev":  {"y1_drop": 0.10, "annual_decay": 0.070}, # ~66% retention at Year 5
}
DEPRECIATION_SHOWROOM_EXIT_PENALTY = 0.05   # Extra Y1 penalty when custom rate given

# On-Road Fees (Cross-checked March 2026)
PLATE_FEE_CITY = 14000000       # Thông tư 155/2025/TT-BTC
PLATE_FEE_PROVINCE = 140000      # Other provinces
INSPECTION_FEE = 290000          # 250K kiểm định + 40K GCN, per Thông tư 156/2025/TT-BTC
ROAD_MAINTENANCE_FEE_YEARLY = 1560000
CIVIL_INSURANCE_YEARLY = 480700  # 4-seat non-commercial, incl. VAT, per NĐ 67/2023

# --- Legacy Configuration Removed: Battery Tiers ---

# Maintenance Milestones (v0.2.0)
MAINTENANCE_MAJOR_KM = 40000               # Interval for major service
MAINTENANCE_MAJOR_COST_ICE = 5000000        # VND per milestone
MAINTENANCE_MAJOR_COST_EV  = 1500000        # VND per milestone

# Data Recency (v0.2.0)
LAST_UPDATED = date(2026, 3, 14)
DATA_RECENCY_DAYS = 270

def fmt_vnd(amount):
    return f"{amount:,.0f} VND"
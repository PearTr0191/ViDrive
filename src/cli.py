from src.config import BRAND_LIQUIDITY_MAP, LAST_UPDATED, DATA_RECENCY_DAYS, WIZARD_SEGMENTS
from datetime import date

def fmt_vnd(amount):
    return f"{amount:,.0f} VND"

def parse_val(text):
    if not text: return None
    text = text.lower().strip().replace(",", "")
    mult = {'k': 1_000, 'm': 1_000_000, 'b': 1_000_000_000}
    try:
        return float(text[:-1]) * mult[text[-1]] if text[-1] in mult else float(text)
    except (ValueError, IndexError, KeyError): return None

def ask(prompt, default=None, is_num=False):
    disp = f"{prompt} [{default}]: " if default else f"{prompt}: "
    while True:
        val = input(disp).strip() or default
        if not is_num: return val
        num = parse_val(str(val))
        if num is not None: return num
        print("Invalid number format. Use digits or '500m'.")

def select_car(cars, prompt="Select a car"):
    car_ids = list(cars.keys())
    if not car_ids: return None

    print(f"\n{prompt}:")
    for i, cid in enumerate(car_ids):
        print(f"  {i+1}. {cars[cid]['brand']} {cars[cid].get('model', cid)}")

    while True:
        choice = ask(f"Enter number (1-{len(car_ids)})")
        if choice and choice.isdigit() and 1 <= int(choice) <= len(car_ids):
            return car_ids[int(choice)-1]
        print(f"Invalid. Enter 1-{len(car_ids)}.")

def get_wizard_car():
    print("\n--- NEW CAR WIZARD ---")
    data = {"brand": ask("Brand"), "model": ask("Model", "Custom")}
    data["price"] = ask("Price (e.g. 500m)", is_num=True)
    data["type"] = ask("Type (ICE/ICE-D/HEV/EV)", "ICE").upper()
    data["consumption"] = ask("Consumption (L or kWh /100km)", "6.0", is_num=True)
    data["annual_maintenance"] = ask("Annual Maintenance", "8000000", is_num=True)
    data["seats"] = int(ask("Seats", "5", is_num=True))

    print("\n  Vehicle Segments:")
    for i, seg in enumerate(WIZARD_SEGMENTS):
        print(f"    {i+1}. {seg}")
    while True:
        seg_choice = ask(f"  Segment (1-{len(WIZARD_SEGMENTS)})", "1")
        if seg_choice.isdigit() and 1 <= int(seg_choice) <= len(WIZARD_SEGMENTS):
            data["segment"] = WIZARD_SEGMENTS[int(seg_choice) - 1]
            break
        print(f"  Invalid. Enter 1-{len(WIZARD_SEGMENTS)}.")

    depr = ask("Custom Annual Depreciation % (optional, e.g. 8)", "")
    data["depreciation_rate"] = float(depr) / 100 if depr else None
    return data

def check_data_recency():
    delta = (date.today() - LAST_UPDATED).days
    if delta > DATA_RECENCY_DAYS:
        print(f"  [!] Market data may be outdated (last updated {LAST_UPDATED}).\n"
              f"      Update src/config.py with current prices.\n")

def print_header():
    print("\n--- VIDRIVE TCO CALCULATOR ---\n")

def row(label, v1, v2=None, w=22):
    f1 = fmt_vnd(v1) if isinstance(v1, (int, float)) else str(v1)
    if v2 is None:
        print(f"{label:<25} {f1:>{w}}")
    else:
        f2 = fmt_vnd(v2) if isinstance(v2, (int, float)) else str(v2)
        print(f"{label:<25} {f1:>22} {f2:>22}")

def print_car_list(cars):
    print(f"{'ID':<15} {'Brand':<10} {'Model':<20} {'Price':>15} {'Liquidity':>12}")
    print("-" * 75)
    for cid, c in cars.items():
        liq = BRAND_LIQUIDITY_MAP.get(c['brand'], "Tier 3")
        print(f"{cid:<15} {c['brand']:<10} {c.get('model', cid):<20} {fmt_vnd(c['price']):>15} {liq:>12}")


def print_result(car_id, year, res, show_opp=True):
    print(f"Vehicle: {car_id.upper()}\n" + "=" * 45 + "\nSUMMARY")
    
    sections = [
        (("On-road purchase price", "on_road")),
        (("Lost Bank Interest", "opp_cost") if show_opp else (f"Net TCO ({year} Years)", "tco")),
        (("True Financial Impact", "true_financial_impact") if show_opp else None),
        (("Monthly Average", "monthly"))
    ]
    for label, key in [s for s in sections if s]: row(label, res[key], w=18)
    
    print("-" * 45 + "\n1. INITIAL OUTLAY")
    for l, k in [("MSRP Price", "price"), (" - Registration Tax", "reg_tax"), ("Total Outlay", "on_road")]:
        row(l, res[k], w=18)
    
    print("\n2. OPERATING COSTS")
    for l, k in [("Fuel / Energy", "fuel"), ("Maintenance", "maint"), ("Insurance & Fees", "legal"), ("Total Operating", "operating")]:
        row(l, res[k], w=18)
    
    print("\n3. RESALE & DEPRECIATION")
    row("Predicted Resale", res['resale'], w=18)
    row("Total Depreciation", res['depreciation'], w=18)
    print(f" Liquidity: {res['liquidity']}\n\n4. ENVIRONMENTAL RISKS (Provisions)")
    print(f" Hydro-Risk Level: {res['hydro_risk']['risk_level']}")
    row(" Est. Repair Cost", res['hydro_risk']['estimate'], w=18)
    print(" (Not included in TCO totals)\n" + "=" * 45 + "\n")

def print_comparison(c1_id, r1, c2_id, r2, show_opp=True):
    print(f"\nCOMPARISON: {c1_id.upper()} vs {c2_id.upper()}\n" + "=" * 75)
    print(f"{'Lifecycle Phase':<25} {c1_id.upper():>22} {c2_id.upper():>22}\n" + "-" * 75 + "\nSUMMARY")
    
    sum_spec = [("On-road purchase price", "on_road")]
    if show_opp: sum_spec += [("Lost Bank Interest", "opp_cost"), ("True Financial Impact", "true_financial_impact")]
    sum_spec += [("Monthly Average", "monthly")]
    for label, key in sum_spec: row(label, r1[key], r2[key])
    
    print("-" * 75 + "\n1. INITIAL OUTLAY")
    for l, k in [("MSRP Price", "price"), (" - Registration Tax", "reg_tax"), ("Total Outlay", "on_road")]:
        row(l, r1[k], r2[k])
    
    print("\n2. OPERATING COSTS")
    for l, k in [("Fuel / Energy", "fuel"), ("Maintenance", "maint"), ("Total Operating", "operating")]:
        row(l, r1[k], r2[k])

    print("\n3. RESALE & DEPRECIATION")
    row("Predicted Resale", r1['resale'], r2['resale'])
    row("Total Depreciation", r1['depreciation'], r2['depreciation'])
    row("Brand Liquidity", r1['liquidity'], r2['liquidity'])
    
    print("-" * 75 + "\n4. ENVIRONMENTAL RISKS")
    row("Hydro-Risk (Flood)", r1['hydro_risk']['risk_level'], r2['hydro_risk']['risk_level'])
    row("Repair Provision", r1['hydro_risk']['estimate'], r2['hydro_risk']['estimate'])
    
    diff = r1['tco'] - r2['tco']
    win = c2_id.upper() if diff > 0 else c1_id.upper()
    print("-" * 75 + f"\nVERDICT: {win} is MORE ECONOMICAL by {fmt_vnd(abs(diff))}\n" + "=" * 75 + "\n")

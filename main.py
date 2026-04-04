#!/usr/bin/env python3
"""
ViDrive — TCO Calculator for the Vietnamese Market
v0.3.1 — 3-tier regional fees, auto area detection, parametric depreciation
"""

APP_VERSION = "0.3.1"

import sys, os, json, argparse
from datetime import date

if sys.stdout.encoding != 'utf-8' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.config import *
from src.calculations import *
from src.cli import *

CARS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "cars.json")

def load_data():
    if not os.path.exists(CARS_FILE):
        print(f"Error: Database file not found at {CARS_FILE}")
        return {}
    with open(CARS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if not data:
            print("Warning: Database is empty!")
        return data

# --- Input Helpers ---

def parse_smart_value(text):
    """Parses shorthand like '500m', '1.2b', '15k' into numbers."""
    try:
        text = text.lower().strip().replace(",", "")
        if not text: return None
        multiplier = {'k': 1_000, 'm': 1_000_000, 'b': 1_000_000_000}
        if text[-1] in multiplier:
            return float(text[:-1]) * multiplier[text[-1]]
        return float(text)
    except:
        return None

def get_num(prompt, default=None):
    while True:
        val = parse_smart_value(get_input(prompt, default))
        if val is not None:
            return val
        print("Invalid number. Use digits or shorthand like '500m'.")

def get_input(prompt, default=None):
    disp = f"{prompt} [{default}]: " if default else f"{prompt}: "
    val = input(disp).strip()
    return val if val else default

def select_car(cars, prompt="Select a car"):
    car_ids = sorted(cars.keys())
    if not car_ids:
        print("Database is empty!")
        return None

    print(f"\n{prompt}:")
    for i, cid in enumerate(car_ids):
        c = cars[cid]
        print(f"  {i+1}. {c['brand']} {c.get('model', cid)}")

    while True:
        choice = get_input(f"Enter number (1-{len(car_ids)})")
        try:
            if not choice: continue
            idx = int(choice) - 1
            if 0 <= idx < len(car_ids):
                return car_ids[idx]
        except ValueError:
            pass
        print(f"Invalid. Enter 1-{len(car_ids)}.")

def get_custom_car_wizard():
    print("\n--- NEW CAR WIZARD ---")
    brand = get_input("Brand")
    model = get_input("Model", "Custom Model")

    price = None
    while price is None:
        price = parse_smart_value(get_input("Price (e.g. 500m or 1.2b)"))
        if price is None: print("Invalid price format.")

    ctype = ""
    while ctype not in ["ICE", "EV"]:
        ctype = get_input("Type (ICE/EV)", "ICE").upper()

    cons = get_num("Consumption (L/100km or kWh/100km)", "6.0")
    maint = get_num("Annual Maintenance (e.g. 8m)", "8000000")

    depr_raw = get_input("Depreciation Rate (optional, e.g. 0.1)", "")
    depr = float(depr_raw) if depr_raw else None

    return {
        "brand": brand, "price": price, "type": ctype,
        "consumption": cons, "annual_maintenance": maint,
        "depreciation_rate": depr,
    }

# --- Main Interactive Flow ---

def check_data_recency():
    delta = (date.today() - LAST_UPDATED).days
    if delta > DATA_RECENCY_DAYS:
        print(f"  [!] Market data may be outdated (last updated {LAST_UPDATED}).\n"
              f"      Update src/config.py with current prices.\n")

def interactive_mode(cars):
    print_header()
    print("Welcome! What would you like to do?\n"
          "1. View Costs for 1 Car\n"
          "2. Compare 2 Cars\n"
          "3. Enter a Custom Car\n"
          "4. List All Cars\n"
          "5. Exit")

    choice = get_input("Action", "1")

    if choice == "5": return

    if choice == "4":
        print_car_list(cars)
        input("\nPress Enter to return to menu...")
        return interactive_mode(cars)

    # Common params — area tier is auto-detected from city/province name
    city = get_input("City/Province", "hanoi")
    area = get_area_tier(city)
    if area == 2:
        print("\n  Is this location a City/Town (Area 2) or a Rural District (Area 3)?")
        print("    1. Provincially-governed City or Town [Default]")
        print("    2. Rural District or Commune")
        sub_choice = get_input("  Selection", "1")
        if sub_choice == "2":
            area = 3

    area_labels = {1: "Area 1 (Central City)", 2: "Area 2 (Province)", 3: "Area 3 (Rural)"}
    print(f"  → {city.title()} → {area_labels[area]}")

    km = int(parse_smart_value(get_input("Annual KM", "15000")))
    years = int(get_input("Years of ownership", "5"))

    if choice == "1":
        cid = select_car(cars)
        if cid:
            print_result(cid, years, get_tco(cars[cid], city, km, years, area=area))
    elif choice == "2":
        c1, c2 = select_car(cars, "Car 1"), select_car(cars, "Car 2")
        if c1 and c2:
            print_comparison(c1, get_tco(cars[c1], city, km, years, area=area),
                             c2, get_tco(cars[c2], city, km, years, area=area))
    elif choice == "3":
        car = get_custom_car_wizard()
        print_result(car["brand"], years, get_tco(car, city, km, years, area=area))

    cont = get_input("\nRun another calculation? (y/n)", "y")
    if cont.lower() == 'y':
        return interactive_mode(cars)

# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="ViDrive TCO Calculator")
    parser.add_argument("--city", default="hanoi")
    parser.add_argument("--km", type=float, default=15000)
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--car")
    parser.add_argument("--compare", nargs=2)

    if len(sys.argv) == 1:
        interactive_mode(load_data())
        return

    args = parser.parse_args()
    cars = load_data()

    if args.car and args.car in cars:
        print_result(args.car, args.years, get_tco(cars[args.car], args.city, args.km, args.years))
    elif args.compare:
        c1, c2 = args.compare
        if c1 in cars and c2 in cars:
            print_comparison(c1, get_tco(cars[c1], args.city, args.km, args.years),
                             c2, get_tco(cars[c2], args.city, args.km, args.years))

if __name__ == "__main__":
    main()
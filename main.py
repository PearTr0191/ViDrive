#!/usr/bin/env python3
"""
ViDrive - Minimalist TCO Calculator
v0.2.0 - Milestone Maintenance & Depreciation
"""

APP_VERSION = "0.2.0"

import sys
import argparse
import json
import os
from datetime import date

# Force UTF-8 for Windows
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

# --- TOLERABLE INPUT HELPERS ---

def parse_smart_value(text):
    """
    Allows '500m' for 500 million or '1.2b' for 1.2 billion.
    """
    try:
        text = text.lower().strip().replace(",", "")
        if not text: return None
    
        multiplier = {'k': 1_000, 'm': 1_000_000, 'b': 1_000_000_000}
        if text[-1] in multiplier:
            return float(text[:-1]) * multiplier[text[-1]]
        return float(text)
    except:
        return None

def get_num(promnpt, default=None):
    # Fix: use correct parameter name `prompt` and allow default values
    prompt = promnpt
    while True:
        val = parse_smart_value(get_input(prompt, default))
        if val is not None:
            return val
        print("Invalid number, please use digits only or tags like '500m'.")

def get_years(prompt, default="5"):
    while True:
        val = get_input(prompt, default)
        try:
            return int(val)
        except:
            print("Invalid input! Please enter a whole number of years.")

def get_input(prompt, default=None):
    """Prompt user with an optional default value."""
    disp = f"{prompt} [{default}]: " if default else f"{prompt}: "
    val = input(disp).strip()
    return val if val else default

def select_car(cars, prompt="Select a car"):
    """Show a list and return the car ID by number selection."""
    car_ids = sorted(cars.keys())
    if not car_ids:
        print("Database is empty! Cannot select car.")
        return None

    print(f"\n{prompt}:")
    for i, cid in enumerate(car_ids):
        c = cars[cid]
        print(f"  {i+1}. {c['brand']} {c.get('model', cid)}")
    
    while True:
        choice = get_input(f"Enter number (1-{len(car_ids)})")
        try:
            if not choice: continue # Ignore empty enter
            idx = int(choice) - 1
            if 0 <= idx < len(car_ids):
                return car_ids[idx]
        except ValueError:
            pass
        print(f"Invalid choice '{choice}', please enter a number between 1 and {len(car_ids)}.")

def get_custom_car_wizard():
    print("\n--- NEW CAR WIZARD ---")
    brand = get_input("Brand")
    model = get_input("Model", "Custom Model")

    price = None
    while price is None:
        price_raw = get_input("Price (e.g. 500m or 1.2b)")
        price = parse_smart_value(price_raw)
        if price is None: print("Invalid price format.")

    ctype = ""
    while ctype not in ["ICE", "EV"]:
        ctype = get_input("Type (ICE/EV)", "ICE").upper()
        if ctype not in ["ICE", "EV"]: print("Please enter 'ICE' or 'EV'.")
    
    cons = get_num("Consumption (L/100km or kWh/100km)", "6.0")
    maint = get_num("Annual Maintenance (e.g. 8m, 15k)", "8,000,000")
    
    depr_raw = get_input("Depreciation Rate (Optional, e.g. 0.1)", "")
    depr = float(depr_raw) if depr_raw else None

    return {
        "brand": brand,
        "price": price,
        "type": ctype,
        "consumption": cons,
        "annual_maintenance": maint,
        "depreciation_rate": depr
    }

# --- MAIN INTERACTIVE FLOW ---

def check_data_recency():
    """Warns if market data constants are older than 9 months."""
    delta = (date.today() - LAST_UPDATED).days
    if delta > DATA_RECENCY_DAYS:
        print(f"  [!] Warning: Market prices may be outdated (last updated {LAST_UPDATED}).")
        print(f"      Please update src/config.py with current petrol/electricity prices.\n")

def interactive_mode(cars):
    print_header()
    print("Welcome! What would you like to do?")
    print("1. View Costs for 1 Car")
    print("2. Compare 2 Cars")
    print("3. Enter a Custom Car")
    print("4. List All Cars")
    print("5. Exit")
    
    choice = get_input("Action", "1")
    
    if choice == "5": return
    
    if choice == "4":
        print_car_list(cars)
        input("\nPress Enter to return to menu...")
        return interactive_mode(cars)

    # Common params
    city = get_input("City (hanoi/hcmc/province)", "hanoi")
    km = int(parse_smart_value(get_input("Annual KM", "15000")))
    years = int(get_input("Years of ownership", "5"))

    if choice == "1":
        cid = select_car(cars)
        print_result(cid, years, get_tco(cars[cid], city, km, years))
    elif choice == "2":
        c1, c2 = select_car(cars, "Car 1"), select_car(cars, "Car 2")
        print_comparison(c1, get_tco(cars[c1], city, km, years), c2, get_tco(cars[c2], city, km, years))
    elif choice == "3":
        car = get_custom_car_wizard()
        print_result(car["brand"], years, get_tco(car, city, km, years))

    # Loop back
    cont = get_input("\nRun another calculation? (y/n)", "y")
    if cont.lower() == 'y':
        return interactive_mode(cars)

# --- CLI ARG PARSER ---

def main():
    parser = argparse.ArgumentParser()
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
    
    if args.car in cars:
        print_result(args.car, args.years, get_tco(cars[args.car], args.city, args.km, args.years))
    elif args.compare:
        c1, c2 = args.compare
        if c1 in cars and c2 in cars:
            print_comparison(c1, get_tco(cars[c1], args.city, args.km, args.years), c2, get_tco(cars[c2], args.city, args.km, args.years))

if __name__ == "__main__":
    main()
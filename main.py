#!/usr/bin/env python3
"""
ViDrive - Minimalist TCO Calculator
"""

import sys
import argparse
import json
import os
from datetime import date

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
    text = text.lower().strip().replace(",", "")
    if not text:
        return None
    
    multiplier = 1
    if text.endswith('m'):
        multiplier = 1_000_000
        text = text[:-1]
    elif text.endswith('b'):
        multiplier = 1_000_000_000
        text = text[:-1]
    elif text.endswith('k'):
        multiplier = 1_000
        text = text[:-1]
        
    try:
        return float(text) * multiplier
    except ValueError:
        return None

def get_input(prompt, default=None):
    """Prompt user with an optional default value."""
    display_prompt = f"{prompt}"
    if default is not None:
        display_prompt += f" [{default}]"
    display_prompt += ": "
    
    val = input(display_prompt).strip()
    if not val and default is not None:
        return default
    return val

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
    brand = get_input("Brand", "Custom")
    model = get_input("Model", "Generic")
    
    price = None
    while price is None:
        price_raw = get_input("Price (e.g. 500m or 1.2b)")
        price = parse_smart_value(price_raw)
        if price is None: print("Invalid price format.")

    type_in = ""
    while type_in not in ["ICE", "EV"]:
        type_in = get_input("Type (ICE/EV)", "ICE").upper()
    
    consumption = None
    while consumption is None:
        cons_raw = get_input(f"Consumption ({'L/100km' if type_in == 'ICE' else 'kWh/100km'})")
        consumption = parse_smart_value(cons_raw) # reusing parser for simple floats too
        if consumption is None: print("Invalid number.")

    return {
        "brand": brand,
        "model": model,
        "price": price,
        "type": type_in,
        "consumption": consumption,
        "depreciation_rate": 0.10 if type_in == "ICE" else 0.15,
        "annual_maintenance": 8000000 if type_in == "ICE" else 5000000
    }

# --- MAIN INTERACTIVE FLOW ---

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
        car_id = select_car(cars)
        if car_id:
            res = get_tco(cars[car_id], city, km, years)
            print_result(car_id, years, res)
        
    elif choice == "2":
        id1 = select_car(cars, "Select Car 1")
        id2 = select_car(cars, "Select Car 2")
        if id1 and id2:
            r1 = get_tco(cars[id1], city, km, years)
            r2 = get_tco(cars[id2], city, km, years)
            print_comparison(id1, r1, id2, r2)
        
    elif choice == "3":
        car_data = get_custom_car_wizard()
        res = get_tco(car_data, city, km, years)
        print_result(car_data['model'], years, res)

    # Loop back
    cont = get_input("\nRun another calculation? (y/n)", "y")
    if cont.lower() == 'y':
        return interactive_mode(cars)

# --- CLI ARG PARSER ---

def main():
    parser = argparse.ArgumentParser(description="ViDrive TCO Calculator")
    parser.add_argument("--list", action="store_true", help="Show all cars")
    parser.add_argument("--city", default="hanoi", help="City (hanoi/hcmc/province)")
    parser.add_argument("--km", type=int, default=15000, help="Annual KM")
    parser.add_argument("--years", type=int, default=5, help="Ownership years")
    parser.add_argument("--car", help="ID of car to analyse")
    parser.add_argument("--compare", nargs=2, help="Compare two car IDs")
    parser.add_argument("--custom", action="store_true", help="Enter a custom car manually")
    
    # Check if any args were actually provided besides the filename
    if len(sys.argv) == 1:
        cars = load_data()
        interactive_mode(cars)
        return

    args = parser.parse_args()
    cars = load_data()
    
    if args.list:
        print_car_list(cars)
    elif args.custom:
        car_data = get_custom_car_wizard()
        res = get_tco(car_data, args.city, args.km, args.years)
        print_result(car_data['model'], args.years, res)
    elif args.car:
        if args.car in cars:
            res = get_tco(cars[args.car], args.city, args.km, args.years)
            print_result(args.car, args.years, res)
    elif args.compare:
        c1, c2 = args.compare
        if c1 in cars and c2 in cars:
            r1 = get_tco(cars[c1], args.city, args.km, args.years)
            r2 = get_tco(cars[c2], args.city, args.km, args.years)
            print_comparison(c1, r1, c2, r2)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

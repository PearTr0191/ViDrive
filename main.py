import sys, argparse

APP_VERSION = "0.4.1"

if sys.stdout.encoding != 'utf-8' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.config import *
from src.calculations import *
from src.cli import *

def interactive_mode(cars):
    print_header()
    check_data_recency()
    print("Welcome! What would you like to do?\n"
          "1. View Costs for 1 Car\n"
          "2. Compare 2 Cars\n"
          "3. Enter a Custom Car\n"
          "4. List All Cars\n"
          "5. Exit")

    cmd = ask("Action", "1")
    if cmd == "5": return

    if cmd == "4":
        print_car_list(cars)
        ask("Press Enter to return...")
        return interactive_mode(cars)

    city = ask("City/Province", "hanoi")
    area = get_area_tier(city)
    if area == 2:
        print("\n  Is this location a City/Town (Area 2) or a Rural District (Area 3)?")
        print("    1. City/Town [Default]\n    2. Rural District")
        if ask("  Selection", "1") == "2": area = 3

    print(f"  → {city.title()} → {area} (Tier)")
    km = int(ask("Annual KM", "15000", is_num=True))
    years = int(ask("Years of ownership", "5", is_num=True))
    ratio = ask("  Enter City Driving % (0-100)", "30", is_num=True) / 100.0
    show_opp = ask("  Include Capital Opportunity Cost? (y/n)", "y").lower() == 'y'

    # --- Action Dispatchers ---
    def run_single():
        cid = select_car(cars)
        if cid:
            res = get_tco(cars[cid], city, km, years, area=area, city_ratio=ratio)
            print_result(cid, years, res, show_opp=show_opp)

    def run_compare():
        c1, c2 = select_car(cars, "Car 1"), select_car(cars, "Car 2")
        if c1 and c2:
            r1 = get_tco(cars[c1], city, km, years, area=area, city_ratio=ratio)
            r2 = get_tco(cars[c2], city, km, years, area=area, city_ratio=ratio)
            print_comparison(c1, r1, c2, r2, show_opp=show_opp)

    def run_wizard():
        car = get_wizard_car()
        res = get_tco(car, city, km, years, area=area, city_ratio=ratio)
        print_result(car["brand"], years, res, show_opp=show_opp)

    # Dispatch Routing
    actions = {"1": run_single, "2": run_compare, "3": run_wizard}
    if cmd in actions: actions[cmd]()

    if ask("\nRun another calculation? (y/n)", "y").lower() == 'y':
        return interactive_mode(cars)

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

    if args.car and args.car in cars:
        print_result(args.car, args.years, get_tco(cars[args.car], args.city, args.km, args.years))
    elif args.compare:
        c1, c2 = args.compare
        if c1 in cars and c2 in cars:
            print_comparison(c1, get_tco(cars[c1], args.city, args.km, args.years),
                             c2, get_tco(cars[c2], args.city, args.km, args.years))

if __name__ == "__main__":
    main()
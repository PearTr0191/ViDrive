"""ViDrive v1.0.0 — Vietnamese Total Cost of Ownership Calculator for Vehicles."""
import sys
import os
import random

if sys.stdout.encoding != 'utf-8' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]

from src.config import APP_VERSION, MAX_COMPARISON_CARS, CITY_LIST
from src.calculations import *
from src.cli import (
    ViDriveError, print_header, print_quick_start, check_data_recency,
    check_pdflatex, ask, ask_bool, select_car, select_cars_n,
    print_car_list, search_cars, print_search_results, print_city_list,
    print_result, print_breakdown, print_comparison_n, print_history,
    fmt_vnd, clear_screen,
)
from src.i18n import set_language, t, _lang
from src.wizard import get_wizard_car
from src.persistence import save_result, load_history, load_result, delete_result
from src.export import export_single_csv, export_compare_csv


def run_single(cars, city, km, years, area, ratio, show_opp, verbose=False):
    """Run a single car TCO analysis."""
    cid = select_car(cars)
    if not cid:
        return
    car = cars[cid]
    res = get_tco(car, city, km, years, area=area, city_ratio=ratio)
    print_result(cid, years, res, show_opp=show_opp)
    if verbose:
        print_breakdown(car, city, km, years, area, ratio, res, show_opp=show_opp)

    loan = None
    if ask_bool(t('prompt_loan_calc'), default=False):
        loan = run_loan_calculator(res['on_road'], years)

    if ask_bool(t('prompt_export_pdf'), default=False):
        export_to_pdf_single(cid, years, res, city, km, years, area, ratio, show_opp, loan)

    if ask_bool(t('prompt_export_csv'), default=False):
        path = export_single_csv(cid, years, res, city, km, area, ratio, show_opp, loan)
        print(t('csv_exported', file=path))

    if ask_bool(t('prompt_save'), default=False):
        name = ask(t('prompt_save_name'), f"{cid}_{city.replace(' ', '_')}_{years}y")
        if name:
            data = {"type": "single", "car_id": cid, "city": city, "km": km,
                    "years": years, "area": area, "ratio": ratio, "show_opp": show_opp,
                    "result": res, "loan": loan}
            save_result(name, data)
            print(f"  Saved as '{name}' in ~/.vidrive/history.json")


def run_compare(cars, city, km, years, area, ratio, show_opp, verbose=False):
    """Run an N-car comparison (2 to MAX_COMPARISON_CARS)."""
    print(f"\n  {t('prompt_compare_count', max=MAX_COMPARISON_CARS)}")
    count_str = ask(t('prompt_compare_count_input'), "2")
    try:
        count = int(count_str or "2")
    except (ValueError, TypeError):
        count = 2

    if count < 2:
        raise ViDriveError(t('error_too_few_cars'))
    if count > MAX_COMPARISON_CARS:
        raise ViDriveError(t('error_too_many_cars', max=MAX_COMPARISON_CARS, count=count))

    chosen = select_cars_n(cars, count)
    if len(chosen) < 2:
        raise ViDriveError(t('error_too_few_cars'))

    results = [get_tco(cars[c], city, km, years, area=area, city_ratio=ratio) for c in chosen]
    print_comparison_n(chosen, results, year=years, show_opp=show_opp)

    if verbose:
        for i, (cid, res) in enumerate(zip(chosen, results)):
            print_breakdown(cars[cid], city, km, years, area, ratio, res, show_opp=show_opp)

    loans = None
    if ask_bool(t('prompt_loan_calc'), default=False):
        loans = []
        for c in chosen:
            loans.append(run_loan_calculator(cars[c]['on_road'], years))

    if ask_bool(t('prompt_export_pdf'), default=False):
        export_to_pdf_compare(chosen, results, years, city, km, years, area, ratio, show_opp, loans)

    if ask_bool(t('prompt_export_csv'), default=False):
        path = export_compare_csv(chosen, results, years, city, km, area, ratio, show_opp, loans)
        print(t('csv_exported', file=path))

    if ask_bool(t('prompt_save'), default=False):
        name = ask(t('prompt_save_name'), f"compare_{'_'.join(chosen)}_{years}y")
        if name:
            data = {"type": "compare", "cars": chosen, "city": city, "km": km,
                    "years": years, "area": area, "ratio": ratio, "show_opp": show_opp,
                    "results": results, "loans": loans}
            save_result(name, data)
            print(f"  Saved as '{name}' in ~/.vidrive/history.json")


def run_wizard(city, km, years, area, ratio, show_opp, verbose=False):
    """Run the custom car wizard."""
    car = get_wizard_car()
    if car is None:
        return
    res = get_tco(car, city, km, years, area=area, city_ratio=ratio)
    print_result(car["brand"], years, res, show_opp=show_opp)
    if verbose:
        print_breakdown(car, city, km, years, area, ratio, res, show_opp=show_opp)

    loan = None
    if ask_bool(t('prompt_loan_calc'), default=False):
        loan = run_loan_calculator(res['on_road'], years)

    if ask_bool(t('prompt_export_pdf'), default=False):
        export_to_pdf_single(car["brand"], years, res, city, km, years, area, ratio, show_opp, loan)

    if ask_bool(t('prompt_export_csv'), default=False):
        path = export_single_csv(car["brand"], years, res, city, km, area, ratio, show_opp, loan)
        print(t('csv_exported', file=path))


def run_search(cars):
    """Search for cars by brand, model, type, or segment."""
    print(f"\n{t('search_title')}")
    term = ask(t('search_prompt'), "")
    if not term:
        return
    results = search_cars(cars, term)
    if not results:
        print(t('search_no_results', term=term))
    else:
        print_search_results(results)
    ask(t('prompt_press_enter'), "")


def run_history(cars):
    """View and manage saved results."""
    history = load_history()
    if not history:
        print(f"\n{t('history_empty')}")
        ask(t('prompt_press_enter'), "")
        return

    while True:
        print_history(history)
        choice = ask(t('history_select'), "")
        if not choice:
            return
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(history):
                print(t('history_not_found'))
                continue
        except (ValueError, TypeError):
            print(t('history_not_found'))
            continue

        entry = history[idx]
        data = entry.get("data", {})
        name = entry.get("name", "?")
        timestamp = entry.get("timestamp", "?")

        print(f"\n{'=' * 60}")
        print(f"  Result: {name}")
        print(f"  Saved: {timestamp}")
        print(f"  Type: {data.get('type', '?')}")
        print(f"{'=' * 60}")

        if data.get("type") == "single":
            res = data.get("result", {})
            cid = data.get("car_id", "?")
            city = data.get("city", "?")
            km = data.get("km", 0)
            years = data.get("years", 5)
            area = data.get("area", 2)
            ratio = data.get("ratio", 0.3)
            show_opp = data.get("show_opp", False)
            print_result(cid, years, res, show_opp=show_opp)
        elif data.get("type") == "compare":
            car_ids = data.get("cars", [])
            results = data.get("results", [])
            years = data.get("years", 5)
            show_opp = data.get("show_opp", False)
            if len(results) >= 2:
                print_comparison_n(car_ids, results, year=years, show_opp=show_opp)

        if ask_bool(t('history_delete_prompt'), default=False):
            if delete_result(name):
                print(t('history_deleted', name=name))
                history = load_history()
                if not history:
                    return
            else:
                print(t('history_not_found'))

        if not ask_bool(t('history_recalc_prompt'), default=False):
            return


def run_demo(cars):
    """Run a pre-filled demo calculation with randomized inputs."""
    print(f"\n{t('demo_running')}")
    if not cars:
        print("  No cars available for demo.")
        return

    car_id = random.choice(list(cars.keys()))
    display_city, _, area, _ = random.choice(CITY_LIST)
    city = display_city
    km = random.choice([5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000])
    years = random.randint(1, 10)
    ratio = round(random.uniform(0.1, 0.7), 2)
    show_opp = random.choice([True, False])

    print(f"  Car: {cars[car_id]['brand']} {cars[car_id].get('model', car_id)}")
    print(f"  City: {display_city} (Area {area})")
    print(f"  Annual KM: {km:,} | Years: {years} | City ratio: {ratio*100:.0f}% | Opp. cost: {show_opp}")
    print()

    res = get_tco(cars[car_id], city, km, years, area=area, city_ratio=ratio)
    print_result(car_id, years, res, show_opp=show_opp)
    print_breakdown(cars[car_id], city, km, years, area, ratio, res, show_opp=show_opp)
    print(t('demo_complete'))
    ask(t('prompt_press_enter'), "")


def run_loan_calculator(on_road_price, years):
    """Interactive loan calculator."""
    print(f"\n{t('section_loan')}")
    down_pct = float(ask(t('prompt_down_payment'), "30", is_num=True) or 0)
    rate = float(ask(t('prompt_interest_rate'), "8.5", is_num=True) or 0) / 100.0
    term = int(ask(t('prompt_loan_term'), str(years), is_num=True) or 0)

    if term <= 0:
        raise ViDriveError(t('error_zero_years'))

    loan = calculate_loan_schedule(on_road_price, down_pct, rate, term)

    from src.cli import row
    row(t('label_loan_monthly'), loan['monthly_payment'], w=18)
    row(t('label_loan_total_interest'), loan['total_interest'], w=18)
    row(t('label_loan_total_repayment'), loan['total_repayment'], w=18)
    row(t('label_loan_effective_cost'), loan['effective_cost'], w=18)
    print()
    return loan


def export_to_pdf_single(car_id, year, res, city, km, years, area, ratio, show_opp, loan=None):
    """Export single car result to PDF via LaTeX."""
    from src.pdf_export import generate_pdf_single
    try:
        result = generate_pdf_single(car_id, year, res, city, km, years, area, ratio, show_opp, loan)
        print(f"\n{t('pdf_exported', file=result)}")
    except Exception as e:
        print(f"\n{t('pdf_error')}: {e}")


def export_to_pdf_compare(cars_data, results, year, city, km, years, area, ratio, show_opp, loans=None):
    """Export comparison result to PDF via LaTeX."""
    from src.pdf_export import generate_pdf_compare
    try:
        result = generate_pdf_compare(cars_data, results, year, city, km, years, area, ratio, show_opp, loans)
        print(f"\n{t('pdf_exported', file=result)}")
    except Exception as e:
        print(f"\n{t('pdf_error')}: {e}")


def get_common_params(cars):
    """Get common parameters (city, km, years, area, ratio, show_opp, verbose) from user."""
    city_input = ask(t('prompt_city'), t('prompt_city_default'))
    if city_input is None:
        city_input = t('prompt_city_default')
    display_city, area = resolve_city(city_input)
    if area == 2:
        print(t('prompt_area_q'))
        print(t('prompt_area_opts'))
        if ask(t('prompt_area_sel'), "1") == "2":
            area = 3
    print(t('prompt_area_result', city=display_city, area=area))

    km = ask(t('prompt_annual_km'), "15000", is_num=True)
    if km is None or km < 0:
        raise ViDriveError(t('error_negative_value', field=t('prompt_annual_km'), value=km))

    years = ask(t('prompt_years'), "5", is_num=True)
    if years is None or years <= 0:
        raise ViDriveError(t('error_zero_years'))
    if years > 50:
        raise ViDriveError(t('error_years_too_large', years=years))

    ratio = (ask(t('prompt_city_ratio'), "30", is_num=True) or 0.0) / 100.0
    if ratio < 0 or ratio > 1:
        ratio = 0.3

    show_opp = ask_bool(t('prompt_opp_cost'), default=False)
    verbose = ask_bool(t('prompt_verbose'), default=False)

    return display_city, km, years, area, ratio, show_opp, verbose


def interactive_mode(cars):
    """Main interactive menu loop."""
    print_header()
    check_data_recency()
    check_pdflatex()
    print_quick_start()
    print(t('welcome_msg'))
    print(t('menu_1_car'))
    print(t('menu_compare'))
    print(t('menu_wizard'))
    print(t('menu_list'))
    print(t('menu_search'))
    print(t('menu_history'))
    print(t('menu_cities'))
    print(t('menu_demo'))
    print(t('menu_exit'))

    cmd = ask(t('action'), "1")

    if cmd == "9":
        return

    while True:
        if cmd == "9":
            return

        if cmd == "4":
            print_car_list(cars)
            ask(t('prompt_press_enter'), "")
        elif cmd == "5":
            run_search(cars)
        elif cmd == "6":
            run_history(cars)
        elif cmd == "7":
            print_city_list()
            ask(t('prompt_press_enter'), "")
        elif cmd == "8":
            run_demo(cars)
            clear_screen()
        else:
            # Commands 1, 2, 3 need common parameters
            city, km, years, area, ratio, show_opp, verbose = get_common_params(cars)

            if cmd == "1":
                run_single(cars, city, km, years, area, ratio, show_opp, verbose)
            elif cmd == "2":
                run_compare(cars, city, km, years, area, ratio, show_opp, verbose)
            elif cmd == "3":
                run_wizard(city, km, years, area, ratio, show_opp, verbose)

            # After a calculation, clear the screen and return to the persistent menu
            clear_screen()

        # Re-display menu and prompt for next action
        print(t('menu_1_car'))
        print(t('menu_compare'))
        print(t('menu_wizard'))
        print(t('menu_list'))
        print(t('menu_search'))
        print(t('menu_history'))
        print(t('menu_cities'))
        print(t('menu_demo'))
        print(t('menu_exit'))
        print(t('menu_back_hint'))
        cmd = ask(t('action'), "1")


def main():
    """Entry point with error handling."""
    import argparse

    parser = argparse.ArgumentParser(
        description=f"ViDrive v{APP_VERSION} — Vietnamese Total Cost of Ownership Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Interactive mode
  python main.py --car vios_2026          # Single car analysis
  python main.py --compare vios_2026 city_2026  # Compare 2 cars
  python main.py --list-cities            # List supported cities
  python main.py --list-cars              # List all cars
  python main.py --search SUV             # Search cars
  python main.py --demo                   # Run pre-filled demo

Default language: Vietnamese. Use --lang en for English.
        """,
    )
    parser.add_argument("--car", help="Single car ID to analyze")
    parser.add_argument("--compare", nargs='+', help="2-10 car IDs to compare")
    parser.add_argument("--city", default="hanoi", help="City/Province (default: hanoi)")
    parser.add_argument("--km", type=float, default=15000, help="Annual kilometers (default: 15000)")
    parser.add_argument("--years", type=int, default=5, help="Years of ownership (default: 5)")
    parser.add_argument("--area", type=int, choices=[1, 2, 3], default=None, help="Area tier (1=Central, 2=Provincial, 3=Rural)")
    parser.add_argument("--city-ratio", type=float, default=30, help="City driving percent, 0-100 (default: 30)")
    parser.add_argument("--opp-cost", action="store_true", help="Include opportunity cost")
    parser.add_argument("--verbose", action="store_true", help="Show calculation breakdown with formulas")
    parser.add_argument("--lang", choices=["en", "vi"], default=None, help="Language (en/vi)")
    parser.add_argument("--list-cities", action="store_true", help="List supported cities and exit")
    parser.add_argument("--list-cars", action="store_true", help="List all cars and exit")
    parser.add_argument("--search", type=str, default=None, help="Search cars by keyword and exit")
    parser.add_argument("--demo", action="store_true", help="Run pre-filled demo calculation")
    parser.add_argument("--save", type=str, default=None, help="Save result to history with given name")
    parser.add_argument("--history", action="store_true", help="List saved results and exit")
    parser.add_argument("--csv", action="store_true", help="Export result to CSV (single car mode)")
    parser.add_argument("--csv-compare", action="store_true", help="Export comparison to CSV (compare mode)")

    # If no arguments at all, run interactive mode
    if len(sys.argv) == 1:
        lang = input(t('choose_language') + ": ").strip().lower() or 'vi'
        set_language(lang)
        if ask_bool(t('prompt_boot_interactive'), default=True):
            try:
                interactive_mode(load_data())
            except ViDriveError as e:
                print(f"\n{e}")
            except KeyboardInterrupt:
                print(t('error_keyboard_interrupt'))
        else:
            print_quick_start()
        return

    args = parser.parse_args()

    if args.lang:
        set_language(args.lang)

    cars = load_data()

    # Handle list/search/demo commands
    if args.list_cities:
        print_city_list()
        return

    if args.list_cars:
        print_car_list(cars)
        return

    if args.search:
        results = search_cars(cars, args.search)
        if results:
            print_search_results(results)
        else:
            print(t('search_no_results', term=args.search))
        return

    if args.demo:
        run_demo(cars)
        return

    # Handle --history flag
    if args.history:
        history = load_history()
        if not history:
            print(f"\n{t('history_empty')}")
        else:
            print_history(history)
        return

    # Validate common parameters
    if args.km < 0:
        print(t('error_negative_value', field='Annual KM', value=args.km))
        return
    if args.years <= 0:
        print(t('error_zero_years'))
        return
    if args.years > 50:
        print(t('error_years_too_large', years=args.years))
        return

    # Determine area
    display_city, resolved_area = resolve_city(args.city)
    area = args.area if args.area is not None else resolved_area

    city_ratio = args.city_ratio / 100.0
    if city_ratio < 0 or city_ratio > 1:
        city_ratio = 0.3

    show_opp = args.opp_cost
    verbose = args.verbose

    # Single car analysis
    if args.car:
        if args.car not in cars:
            print(t('error_car_not_found', car=args.car))
            return
        res = get_tco(cars[args.car], display_city, args.km, args.years, area=area, city_ratio=city_ratio)
        print_result(args.car, args.years, res, show_opp=show_opp)
        if verbose:
            print_breakdown(cars[args.car], display_city, args.km, args.years, area, city_ratio, res, show_opp=show_opp)
        if args.save:
            data = {"type": "single", "car_id": args.car, "city": display_city,
                    "km": args.km, "years": args.years, "area": area, "ratio": city_ratio,
                    "show_opp": show_opp, "result": res}
            save_result(args.save, data)
            print(f"  Saved as '{args.save}' in ~/.vidrive/history.json")
        if args.csv:
            path = export_single_csv(args.car, args.years, res, display_city, args.km, area, city_ratio, show_opp)
            print(t('csv_exported', file=path))
        return

    # Comparison mode
    if args.compare:
        if len(args.compare) < 2:
            print(t('error_too_few_cars'))
            return
        if len(args.compare) > MAX_COMPARISON_CARS:
            print(t('error_too_many_cars', max=MAX_COMPARISON_CARS, count=len(args.compare)))
            return

        car_ids = args.compare
        for c in car_ids:
            if c not in cars:
                print(t('error_car_not_found', car=c))
                return

        results = [get_tco(cars[c], display_city, args.km, args.years, area=area, city_ratio=city_ratio) for c in car_ids]
        print_comparison_n(car_ids, results, year=args.years, show_opp=show_opp)

        if verbose:
            for i, cid in enumerate(car_ids):
                print_breakdown(cars[cid], display_city, args.km, args.years, area, city_ratio, results[i], show_opp=show_opp)
        if args.save:
            data = {"type": "compare", "cars": car_ids, "city": display_city,
                    "km": args.km, "years": args.years, "area": area, "ratio": city_ratio,
                    "show_opp": show_opp, "results": results}
            save_result(args.save, data)
            print(f"  Saved as '{args.save}' in ~/.vidrive/history.json")
        if args.csv or args.csv_compare:
            path = export_compare_csv(car_ids, results, args.years, display_city, args.km, area, city_ratio, show_opp)
            print(t('csv_exported', file=path))
        return

    # If no action specified, show help
    parser.print_help()


if __name__ == "__main__":
    main()

import sys, argparse

APP_VERSION = "0.5.1"

if sys.stdout.encoding != 'utf-8' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.config import *
from src.calculations import *
from src.cli import *
from src.i18n import set_language, t, _lang

def interactive_mode(cars):
    print_header()
    check_data_recency()
    print(t('welcome_msg'))
    print(t('menu_1_car'))
    print(t('menu_compare'))
    print(t('menu_wizard'))
    print(t('menu_list'))
    print(t('menu_exit'))
    cmd = ask(t('action'), "1")
    if cmd == "5": return
    if cmd == "4":
        print_car_list(cars)
        ask(t('prompt_press_enter'))
        return interactive_mode(cars)
    city = ask(t('prompt_city'), t('prompt_city_default'))
    area = get_area_tier(city)
    if area == 2:
        print(t('prompt_area_q'))
        print(t('prompt_area_opts'))
        if ask(t('prompt_area_sel'), "1") == "2": area = 3
    print(t('prompt_area_result', city=city.title(), area=area))
    km = int(ask(t('prompt_annual_km'), "15000", is_num=True))
    years = int(ask(t('prompt_years'), "5", is_num=True))
    ratio = ask(t('prompt_city_ratio'), "30", is_num=True) / 100.0
    show_opp = ask_bool(t('prompt_opp_cost'), default=False)

    def run_single():
        cid = select_car(cars)
        if cid:
            res = get_tco(cars[cid], city, km, years, area=area, city_ratio=ratio)
            print_result(cid, years, res, show_opp=show_opp)
            # Ask about loan calculator FIRST
            if ask_bool(t('prompt_loan_calc'), default=False):
                run_loan_calculator(res['on_road'], years)
            # Then ask about PDF export (includes loan if calculated)
            if ask_bool(t('prompt_export_pdf'), default=False):
                export_to_pdf_single(cid, years, res, city, km, years, area, ratio, show_opp)

    def run_compare():
        c1 = select_car(cars, t('prompt_car_1'), allow_skip=False, selected=[])
        c2 = select_car(cars, t('prompt_car_2'), allow_skip=False, selected=[c1])
        c3 = None
        # Allow skipping the 3rd car - user can press Enter to compare only 2
        c3 = select_car(cars, t('prompt_car_3'), allow_skip=True, selected=[c1, c2])
        if c1 and c2:
            cars_to_compare = [c1, c2]
            results = [
                get_tco(cars[c1], city, km, years, area=area, city_ratio=ratio),
                get_tco(cars[c2], city, km, years, area=area, city_ratio=ratio),
            ]
            if c3:
                cars_to_compare.append(c3)
                results.append(get_tco(cars[c3], city, km, years, area=area, city_ratio=ratio))
            print_comparison_n(cars_to_compare, results, year=years, show_opp=show_opp)
            # Ask about PDF export
            if ask_bool(t('prompt_export_pdf'), default=False):
                export_to_pdf_compare(cars_to_compare, results, years, city, km, years, area, ratio, show_opp)

    def run_wizard():
        car = get_wizard_car()
        res = get_tco(car, city, km, years, area=area, city_ratio=ratio)
        print_result(car["brand"], years, res, show_opp=show_opp)
        if ask_bool(t('prompt_export_pdf'), default=False):
            export_to_pdf_single(car["brand"], years, res, city, km, years, area, ratio, show_opp)
        if ask_bool(t('prompt_loan_calc'), default=False):
            run_loan_calculator(res['on_road'], years)

    actions = {"1": run_single, "2": run_compare, "3": run_wizard}
    if cmd in actions: actions[cmd]()
    if ask_bool(t('prompt_run_again'), default=False):
        return interactive_mode(cars)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="hanoi")
    parser.add_argument("--km", type=float, default=15000)
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--car")
    parser.add_argument("--compare", nargs='+')
    parser.add_argument("--lang", default=None)
    parser.add_argument("--area", type=int, default=None)
    parser.add_argument("--city-ratio", type=float, default=30)
    parser.add_argument("--opp-cost", action="store_true")

    if len(sys.argv) == 1:
        lang = input(t('choose_language') + ": ").strip().lower() or 'vi'
        set_language(lang)
        interactive_mode(load_data())
        return

    args = parser.parse_args()
    if args.lang:
        set_language(args.lang)
    cars = load_data()
    
    # Determine area
    area = args.area if args.area is not None else get_area_tier(args.city)
    city_ratio = args.city_ratio / 100.0
    show_opp = args.opp_cost
    
    if args.car and args.car in cars:
        print_result(args.car, args.years, get_tco(cars[args.car], args.city, args.km, args.years, area=area, city_ratio=city_ratio), show_opp=show_opp)
    elif args.compare:
        if len(args.compare) >= 2 and len(args.compare) <= 3:
            car_ids = args.compare
            if all(c in cars for c in car_ids):
                results = [get_tco(cars[c], args.city, args.km, args.years, area=area, city_ratio=city_ratio) for c in car_ids]
                print_comparison_n(car_ids, results, year=args.years, show_opp=show_opp)

# --- PDF Export Functions ---

def export_to_pdf_single(car_id, year, res, city, km, years, area, ratio, show_opp):
    """Export single car result to PDF via LaTeX."""
    from src.pdf_export import generate_pdf_single
    try:
        generate_pdf_single(car_id, year, res, city, km, years, area, ratio, show_opp)
        print(f"\n{t('pdf_exported', file=car_id)}")
    except Exception as e:
        print(f"\n{t('pdf_error')}: {e}")


def export_to_pdf_compare(cars_data, results, year, city, km, years, area, ratio, show_opp):
    """Export comparison result to PDF via LaTeX."""
    from src.pdf_export import generate_pdf_compare
    try:
        generate_pdf_compare(cars_data, results, year, city, km, years, area, ratio, show_opp)
        print(f"\n{t('pdf_exported', file='compare')}")
    except Exception as e:
        print(f"\n{t('pdf_error')}: {e}")


# --- Loan Calculator ---

def run_loan_calculator(on_road_price, years):
    """Interactive loan calculator."""
    print(f"\n{t('section_loan')}")
    down_pct = float(ask(t('prompt_down_payment'), "30", is_num=True))
    rate = float(ask(t('prompt_interest_rate'), "8.5", is_num=True)) / 100.0
    term = int(ask(t('prompt_loan_term'), str(years), is_num=True))
    
    loan = calculate_loan_schedule(on_road_price, down_pct, rate, term)
    
    row(t('label_loan_monthly'), loan['monthly_payment'], w=18)
    row(t('label_loan_total_interest'), loan['total_interest'], w=18)
    row(t('label_loan_total_repayment'), loan['total_repayment'], w=18)
    row(t('label_loan_effective_cost'), loan['effective_cost'], w=18)
    print()


if __name__ == "__main__":
    main()

import sys, argparse

APP_VERSION = "0.4.2"

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

    def run_compare():
        c1 = select_car(cars, t('prompt_car_1'))
        c2 = select_car(cars, t('prompt_car_2'))
        if c1 and c2:
            r1 = get_tco(cars[c1], city, km, years, area=area, city_ratio=ratio)
            r2 = get_tco(cars[c2], city, km, years, area=area, city_ratio=ratio)
            print_comparison(c1, r1, c2, r2, year=years, show_opp=show_opp)

    def run_wizard():
        car = get_wizard_car()
        res = get_tco(car, city, km, years, area=area, city_ratio=ratio)
        print_result(car["brand"], years, res, show_opp=show_opp)

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
    parser.add_argument("--compare", nargs=2)
    parser.add_argument("--lang", default=None)

    if len(sys.argv) == 1:
        lang = input(t('choose_language') + ": ").strip().lower() or 'vi'
        set_language(lang)
        interactive_mode(load_data())
        return

    args = parser.parse_args()
    if args.lang:
        set_language(args.lang)
    cars = load_data()
    if args.car and args.car in cars:
        print_result(args.car, args.years, get_tco(cars[args.car], args.city, args.km, args.years))
    elif args.compare:
        c1, c2 = args.compare
        if c1 in cars and c2 in cars:
            print_comparison(c1, get_tco(cars[c1], args.city, args.km, args.years),
                             c2, get_tco(cars[c2], args.city, args.km, args.years),
                             year=args.years)

if __name__ == "__main__":
    main()
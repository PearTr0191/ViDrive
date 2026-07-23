"""ViDrive CLI display and interaction functions."""
from src.config import (
    BRAND_LIQUIDITY_MAP, LAST_UPDATED, DATA_RECENCY_DAYS, WIZARD_SEGMENTS,
    CITY_LIST, MAX_COMPARISON_CARS, APP_VERSION,
)
from datetime import date
from typing import overload, Literal
from src.i18n import t
from src import i18n as _i18n
import shutil
import os


def clear_screen():
    """Cross-platform terminal clear."""
    os.system('cls' if os.name == 'nt' else 'clear')


class ViDriveError(Exception):
    """User-facing error with a friendly message."""
    pass


def fmt_vnd(amount):
    return f"{amount:,.0f} VND"


def parse_val(text):
    if not text:
        return None
    text = text.lower().strip().replace(",", "")
    mult = {'k': 1_000, 'm': 1_000_000, 'b': 1_000_000_000}
    try:
        return float(text[:-1]) * mult[text[-1]] if text[-1] in mult else float(text)
    except (ValueError, IndexError, KeyError):
        return None


@overload
def ask(prompt: str, default: str | float | None = None, is_num: Literal[False] = False) -> str | None: ...  # pyright: ignore[reportOverlappingOverload]
@overload
def ask(prompt: str, default: str | float | None = None, is_num: Literal[True] = True) -> float | None: ...
def ask(prompt: str, default: str | float | None = None, is_num: bool = False) -> str | float | None:
    disp = f"{prompt} [{default}]: " if default else f"{prompt}: "
    while True:
        raw = input(disp).strip()
        if not raw:
            if default is not None:
                val = default
            else:
                continue  # re-prompt if no default and empty input
        else:
            val = raw
        if not is_num:
            return str(val)
        num = parse_val(str(val))
        if num is not None:
            return num
        print(t('input_invalid_num'))


def ask_bool(prompt, default=False):
    """Language-aware yes/no prompt. Uses y/n for English, c/k for Vietnamese."""
    yes_key = 'c' if _i18n._lang == 'vi' else 'y'
    no_key  = 'k' if _i18n._lang == 'vi' else 'n'
    default_char = yes_key if default else no_key
    disp = f"{prompt} [{default_char}]: "
    while True:
        val = input(disp).strip().lower() or default_char
        if val == yes_key:
            return True
        if val == no_key:
            return False
        print(f"  Please enter '{yes_key}' or '{no_key}'.")


def select_car(cars: dict, prompt: str = t('prompt_select_car'), allow_skip: bool = False, selected: list | None = None) -> str | None:
    car_ids = list(cars.keys())
    if not car_ids:
        return None
    print(f"\n{prompt}:")
    for i, cid in enumerate(car_ids):
        print(f"  {i+1}. {cars[cid]['brand']} {cars[cid].get('model', cid)}")
    n = len(car_ids)
    if allow_skip:
        print(f"  {t('prompt_skip')}")
    while True:
        choice = ask(t('prompt_number', n=n), default='' if allow_skip else None)
        if choice == '':
            if allow_skip:
                return None
            continue
        if choice is not None and str(choice).isdigit() and 1 <= int(choice) <= n:
            chosen = car_ids[int(choice)-1]
            if selected and chosen in selected:
                print(t('prompt_duplicate_car'))
                continue
            return chosen
        print(t('prompt_invalid_number', n=n))


def select_cars_n(cars, count, selected=None):
    """Select multiple cars for comparison, allowing skip for the last one."""
    if selected is None:
        selected = []
    chosen = []
    for i in range(count):
        is_last = (i == count - 1)
        prompt = t('prompt_car_n', n=i+1) if i >= 2 else (
            t('prompt_car_1') if i == 0 else t('prompt_car_2')
        )
        if is_last:
            prompt = t('prompt_car_skip', n=i+1)
        car = select_car(cars, prompt, allow_skip=is_last, selected=selected + chosen)
        if car is None and is_last:
            break  # User skipped the last car
        if car:
            chosen.append(car)
    return chosen


def check_data_recency():
    delta = (date.today() - LAST_UPDATED).days
    if delta > DATA_RECENCY_DAYS:
        print(t('data_recency_warn', date=str(LAST_UPDATED)))
        print(t('data_recency_action'))


def check_pdflatex():
    """Check for pdflatex and warn if not found."""
    if not shutil.which("pdflatex"):
        print(t('pdflatex_warn'))
        print(t('pdflatex_install'))


def print_header():
    print(f"\n{t('app_title')}\n")


def print_quick_start():
    """Print a quick-start guide for new users."""
    print(f"\n{t('quick_start_title')}")
    print(t('quick_start_1'))
    print(t('quick_start_2'))
    print(t('quick_start_3'))
    print(t('quick_start_4'))
    print(t('quick_start_5'))
    print(t('quick_start_6'))
    print(f"\n{t('quick_start_example')}")
    print(t('quick_start_args'))
    print()


def row(label: str, v1: int | float | str, v2: int | float | str | None = None, w: int = 22) -> None:
    f1 = fmt_vnd(v1) if isinstance(v1, (int, float)) else str(v1)
    if v2 is None:
        print(f"{label:<25} {f1:>{w}}")
    else:
        f2 = fmt_vnd(v2) if isinstance(v2, (int, float)) else str(v2)
        print(f"{label:<25} {f1:>22} {f2:>22}")


def row_n(label: str, *values: int | float | str, widths: list[int] | None = None) -> None:
    """Print a row with N value columns. widths is a list of column widths."""
    if widths is None:
        n = len(values)
        col_width = 22 if n <= 2 else max(14, 22 - (n - 2) * 2)
        widths = [col_width] * n
    formatted = []
    for v, w in zip(values, widths):
        f = fmt_vnd(v) if isinstance(v, (int, float)) else str(v)
        formatted.append(f"{f:>{w}}")
    print(f"{label:<25} " + " ".join(formatted))


def print_car_list(cars):
    print(f"{t('list_col_id'):<18} {t('list_col_brand'):<12} {t('list_col_model'):<20} {t('list_col_price'):>18} {t('list_col_liquidity'):>12}")
    print("-" * 75)
    for cid, c in cars.items():
        raw_liq = BRAND_LIQUIDITY_MAP.get(c['brand'], "Tier 3")
        if raw_liq.startswith('Tier 1'):
            liq = t('tier_1')
        elif raw_liq.startswith('Tier 2'):
            liq = t('tier_2')
        else:
            liq = t('tier_3')
        print(f"{cid:<18} {c['brand']:<12} {c.get('model', cid):<20} {fmt_vnd(c['price']):>18} {liq:>12}")


def search_cars(cars, term: str):
    """Search cars by brand, model, type, or segment. Returns filtered dict."""
    term_lower = term.lower().strip()
    if not term_lower:
        return cars
    results = {}
    for cid, c in cars.items():
        searchable = " ".join([
            c.get('brand', ''),
            c.get('model', ''),
            c.get('type', ''),
            c.get('segment', ''),
            cid,
        ]).lower()
        if term_lower in searchable:
            results[cid] = c
    return results


def print_search_results(cars):
    """Print search results in a rich table format."""
    print(f"\n{t('search_results', n=len(cars))}")
    print(f"{'ID':<18} {'Brand':<12} {'Model':<20} {'Type':<8} {'Segment':<12} {'Price':>15}")
    print("-" * 85)
    for cid, c in cars.items():
        print(f"{cid:<18} {c['brand']:<12} {c.get('model', cid):<20} {c.get('type',''):<8} {c.get('segment',''):<12} {fmt_vnd(c['price']):>15}")


def print_city_list():
    """Print all supported cities with their area tiers."""
    print(f"\n{t('city_list_title')}")
    print(f"{t('city_col_name'):<25} {t('city_col_area'):<10} {t('city_col_type'):<15}")
    print("-" * 55)
    for display, norm_key, area, diacritic_key in CITY_LIST:
        area_label = {1: t('city_area1'), 2: t('city_area2'), 3: t('city_area3')}[area]
        print(f"{display:<25} {area_label:<10} {diacritic_key:<15}")
    print()
    print(t('city_area1_note'))
    print(t('city_area2_note'))
    print(t('city_area3_note'))


def print_result(car_id, year, res, show_opp=False):
    print(f"{t('vehicle', id=car_id.upper())}\n" + "=" * 45 + f"\n{t('summary')}")
    parts = []
    parts.append((t('label_on_road'), res['on_road']))
    parts.append((t('label_net_tco', y=year), res['tco']))
    if show_opp:
        parts.append((t('label_opp_cost'), res['opp_cost']))
        parts.append((t('label_true_impact'), res['true_financial_impact']))
    parts.append((t('label_monthly'), res['monthly']))
    for label, val in parts:
        row(label, val, w=18)
    print("-" * 45 + f"\n{t('section_initial')}")
    for l, k in [(t('label_msrp'), 'price'), (t('label_reg_tax'), 'reg_tax'), (t('label_total_outlay'), 'on_road')]:
        row(l, res[k], w=18)
    print(f"\n{t('section_operating')}")
    for l, k in [(t('label_fuel'), 'fuel'), (t('label_maint'), 'maint'), (t('label_legal'), 'legal'), (t('label_operating'), 'operating')]:
        row(l, res[k], w=18)
    # Parking & Toll estimate (shown as provision, not in TCO)
    pt = res.get('parking_toll')
    if pt:
        row(t('label_parking_toll'), pt['total_over_period'], w=18)
        row(f"  {t('label_parking_monthly')}", pt['monthly_parking'], w=18)
        row(f"  {t('label_toll_monthly')}", pt['monthly_toll'], w=18)
    print(f"\n{t('section_resale')}")
    row(t('label_resale'), res['resale'], w=18)
    row(t('label_depreciation'), res['depreciation'], w=18)
    print(f" {t('label_resale_method')}: {t('resale_logic_' + res['resale_logic'])}")
    raw_liq = res.get('liquidity', '')
    if raw_liq.startswith('Tier 1'):
        liq_disp = t('tier_1')
    elif raw_liq.startswith('Tier 2'):
        liq_disp = t('tier_2')
    else:
        liq_disp = t('tier_3')
    print(f" {t('label_liquidity', liq=liq_disp)}\n\n" + "=" * 45 + "\n")


def print_breakdown(car, city, km, years, area, ratio, res, show_opp=False):
    """Print detailed calculation breakdown with formulas for transparency."""
    from src.calculations import get_fuel_breakdown, get_registration_breakdown, calculate_opportunity_cost

    print(f"\n{t('section_breakdown')}\n" + "=" * 60)

    # Fuel breakdown
    print(t('breakdown_fuel'))
    fb = get_fuel_breakdown(car, km, years, ratio)
    print(t('breakdown_fuel_consumption', consumption=fb['consumption']))
    print(t('breakdown_fuel_freeway', freeway=fb['freeway_mult'], city=fb['city_mult']))
    print(t('breakdown_fuel_adjusted', ratio=ratio*100, adj=fb['adjusted_consumption']))
    print(t('breakdown_fuel_price', label=fb['price_label']))
    print(t('breakdown_fuel_detail',
            km=km, adj_consumption=fb['adjusted_consumption'], price=fb['price'],
            years=years, total=fb['total_fuel']))
    print()

    # Registration breakdown
    print(t('breakdown_reg'))
    rb = get_registration_breakdown(car, area)
    print(t('breakdown_reg_detail', desc=rb['tax_desc']))
    print(t('breakdown_reg_plate', area=area, plate=rb['plate']))
    print(t('breakdown_reg_inspection', inspection=rb['inspection']))
    print(t('breakdown_reg_total', total=rb['total']))
    print()

    # Maintenance breakdown
    print(t('breakdown_maint'))
    maint = res['maint']
    base_annual = car.get('annual_maintenance', 8_000_000)
    milestones = (km * years) // 40_000
    major_cost = 5_000_000 if car['type'] == 'ICE' else (6_500_000 if car['type'] == 'ICE-D' else 1_500_000)
    print(t('breakdown_maint_detail',
            base=base_annual, years=years, milestones=milestones,
            major_cost=major_cost, total=maint))
    print()

    # Opportunity cost breakdown
    if show_opp:
        print(t('breakdown_opp'))
        print(t('breakdown_opp_detail',
                principal=res['on_road'], rate=0.065, years=years,
                total=res['opp_cost']))
        print()

    # Resale breakdown
    print(t('breakdown_resale'))
    print(t('breakdown_resale_detail', resale=res['resale'], method=t('resale_logic_' + res['resale_logic'])))
    print()

    # TCO formula
    print(t('breakdown_tco'))
    print(t('breakdown_tco_detail',
            on_road=res['on_road'], operating=res['operating'],
            resale=res['resale'], tco=res['tco']))
    print()

    # Data recency
    print(t('breakdown_data_recency', date=str(LAST_UPDATED)))
    print("=" * 60 + "\n")


def print_comparison(c1_id, r1, c2_id, r2, year=5, show_opp=False):
    print(f"\n{t('comparison_title', c1=c1_id.upper(), c2=c2_id.upper())}\n" + "=" * 75)
    print("-" * 75 + f"\n{t('summary')}")
    parts = [(t('label_on_road'), r1['on_road'], r2['on_road'])]
    parts += [(t('label_net_tco', y=year), r1['tco'], r2['tco'])]
    if show_opp:
        parts += [(t('label_opp_cost'), r1['opp_cost'], r2['opp_cost']),
                  (t('label_true_impact'), r1['true_financial_impact'], r2['true_financial_impact'])]
    parts += [(t('label_monthly'), r1['monthly'], r2['monthly'])]
    for label, v1, v2 in parts:
        row(label, v1, v2)
    print("-" * 75 + f"\n{t('section_initial')}")
    for l, k in [(t('label_msrp'), 'price'), (t('label_reg_tax'), 'reg_tax'), (t('label_total_outlay'), 'on_road')]:
        row(l, r1[k], r2[k])
    print(f"\n{t('section_operating')}")
    for l, k in [(t('label_fuel'), 'fuel'), (t('label_maint'), 'maint'), (t('label_operating'), 'operating')]:
        row(l, r1[k], r2[k])
    print(f"\n{t('section_resale')}")
    row(t('label_resale'), r1['resale'], r2['resale'])
    row(t('label_depreciation'), r1['depreciation'], r2['depreciation'])
    print(f" {t('label_resale_method')}: {t('resale_logic_' + r1['resale_logic'])}")
    def _liq_disp(raw):
        if raw.startswith('Tier 1'):
            return t('tier_1')
        if raw.startswith('Tier 2'):
            return t('tier_2')
        return t('tier_3')
    row(t('label_brand_liquidity'), _liq_disp(r1['liquidity']), _liq_disp(r2['liquidity']))
    print("-" * 75 + "\n")
    diff = r1['tco'] - r2['tco']
    win = c2_id.upper() if diff > 0 else c1_id.upper()
    print("-" * 75 + f"\n{t('comparison_verdict', winner=win, diff=fmt_vnd(abs(diff)))}\n" + "=" * 75 + "\n")


def print_comparison_n(cars_data, results, year=5, show_opp=False):
    """Generic N-car comparison (2 to MAX_COMPARISON_CARS)."""
    n = len(cars_data)
    if n < 2:
        raise ViDriveError(t('error_too_few_cars'))
    if n > MAX_COMPARISON_CARS:
        raise ViDriveError(t('error_too_many_cars', max=MAX_COMPARISON_CARS, count=n))

    car_ids = [c.upper() for c in cars_data]

    # Build comparison title
    if n == 2:
        title = t('comparison_title', c1=car_ids[0], c2=car_ids[1])
    else:
        title = "COMPARISON: " + " vs ".join(car_ids)

    print(f"\n{title}\n" + "=" * 75)
    print("-" * 75 + f"\n{t('summary')}")

    # Column widths: dynamic based on number of cars
    col_width = max(12, 22 - (n - 2) * 3)
    widths = [col_width] * n

    def _liq_disp(raw):
        if raw.startswith('Tier 1'):
            return t('tier_1')
        if raw.startswith('Tier 2'):
            return t('tier_2')
        return t('tier_3')

    # Summary section
    parts = [(t('label_on_road'), [r['on_road'] for r in results])]
    parts += [(t('label_net_tco', y=year), [r['tco'] for r in results])]
    if show_opp:
        parts += [(t('label_opp_cost'), [r['opp_cost'] for r in results]),
                  (t('label_true_impact'), [r['true_financial_impact'] for r in results])]
    parts += [(t('label_monthly'), [r['monthly'] for r in results])]

    for label, vals in parts:
        row_n(label, *vals, widths=widths)

    # Initial outlay
    print("-" * 75 + f"\n{t('section_initial')}")
    for l, k in [(t('label_msrp'), 'price'), (t('label_reg_tax'), 'reg_tax'), (t('label_total_outlay'), 'on_road')]:
        row_n(l, *[r[k] for r in results], widths=widths)

    # Operating costs
    print(f"\n{t('section_operating')}")
    for l, k in [(t('label_fuel'), 'fuel'), (t('label_maint'), 'maint'), (t('label_operating'), 'operating')]:
        row_n(l, *[r[k] for r in results], widths=widths)

    # Parking & Toll estimates (shown as provision)
    pt_list = [r.get('parking_toll') for r in results]
    if any(pt_list):
        print(f"\n{t('label_parking_toll')}")
        row_n(t('label_parking_monthly'), *[pt['monthly_parking'] if pt else 0 for pt in pt_list], widths=widths)
        row_n(t('label_toll_monthly'), *[pt['monthly_toll'] if pt else 0 for pt in pt_list], widths=widths)
        row_n(f"Total ({year}y)", *[pt['total_over_period'] if pt else 0 for pt in pt_list], widths=widths)

    # Resale
    print(f"\n{t('section_resale')}")
    row_n(t('label_resale'), *[r['resale'] for r in results], widths=widths)
    row_n(t('label_depreciation'), *[r['depreciation'] for r in results], widths=widths)
    print(f" {t('label_resale_method')}: {t('resale_logic_' + results[0]['resale_logic'])}")
    row_n(t('label_brand_liquidity'), *[_liq_disp(r['liquidity']) for r in results], widths=widths)

    # Verdict - rank cars by TCO (cheapest = most efficient)
    print("-" * 75 + "\n")
    ranked = sorted(range(n), key=lambda i: results[i]['tco'])
    best = ranked[0]
    print(f"{car_ids[best]} is the MOST ECONOMICAL")
    for i in ranked[1:]:
        diff = results[i]['tco'] - results[best]['tco']
        print(f"{car_ids[best]} is MORE ECONOMICAL than {car_ids[i]} by {fmt_vnd(diff)}")
    print("=" * 75 + "\n")


def print_history(history):
    """Print saved results history."""
    print(f"\n{t('history_title')}")
    if not history:
        print(t('history_empty'))
        return
    print("-" * 60)
    for i, entry in enumerate(history):
        print(t('history_entry', i=i+1, name=entry.get('name', '?'), timestamp=entry.get('timestamp', '?')))
    print("-" * 60)

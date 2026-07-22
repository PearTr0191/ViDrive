from src.config import BRAND_LIQUIDITY_MAP, LAST_UPDATED, DATA_RECENCY_DAYS, WIZARD_SEGMENTS
from datetime import date
from src.i18n import t
from src import i18n as _i18n

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
        raw = input(disp).strip()
        if not raw:
            if default is not None:
                val = default
            else:
                continue  # re-prompt if no default and empty input
        else:
            val = raw
        if not is_num: return val
        num = parse_val(str(val))
        if num is not None: return num
        print(t('input_invalid_num'))

def ask_bool(prompt, default=False):
    """Language-aware yes/no prompt. Uses y/n for English, c/k for Vietnamese."""
    yes_key = 'c' if _i18n._lang == 'vi' else 'y'
    no_key  = 'k' if _i18n._lang == 'vi' else 'n'
    default_char = yes_key if default else no_key
    disp = f"{prompt} [{default_char}]: "
    while True:
        val = input(disp).strip().lower() or default_char
        if val == yes_key: return True
        if val == no_key:  return False
        print(f"  Please enter '{yes_key}' or '{no_key}'.")

def select_car(cars, prompt=t('prompt_select_car'), allow_skip=False, selected=None):
    car_ids = list(cars.keys())
    if not car_ids: return None
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
        if str(choice).isdigit() and 1 <= int(choice) <= n:
            chosen = car_ids[int(choice)-1]
            if selected and chosen in selected:
                print(t('prompt_duplicate_car'))
                continue
            return chosen
        print(t('prompt_invalid_number', n=n))

def get_wizard_car():
    print(f"\n{t('wizard_title')}")
    data = {"brand": ask(t('wizard_brand')), "model": ask(t('wizard_model'), t('wizard_default_model'))}
    data["price"] = ask(t('wizard_price'), is_num=True)
    data["type"] = str(ask(t('wizard_type'), t('wizard_default_type'))).upper()
    data["consumption"] = ask(t('wizard_consumption'), t('wizard_default_consumption'), is_num=True)
    data["annual_maintenance"] = ask(t('wizard_annual_maint'), t('wizard_default_annual_maint'), is_num=True)
    data["seats"] = int(ask(t('wizard_seats'), "5", is_num=True))
    print(f"\n{t('wizard_segments_title')}")
    for i, seg in enumerate(WIZARD_SEGMENTS):
        print(f"    {i+1}. {seg}")
    n_seg = len(WIZARD_SEGMENTS)
    while True:
        seg_choice = ask(t('wizard_segment_prompt', n=n_seg), "1")
        if str(seg_choice).isdigit() and 1 <= int(seg_choice) <= n_seg:
            data["segment"] = WIZARD_SEGMENTS[int(seg_choice) - 1]
            break
        print(t('wizard_invalid_range', n=n_seg))
    depr = ask(t('wizard_depr'), "")
    data["depreciation_rate"] = float(depr) / 100 if depr else None
    return data

def check_data_recency():
    delta = (date.today() - LAST_UPDATED).days
    if delta > DATA_RECENCY_DAYS:
        print(t('data_recency_warn', date=str(LAST_UPDATED)))
        print(t('data_recency_action'))

def print_header():
    print(f"\n{t('app_title')}\n")

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
        # Default: 22 for 2 cars, 18 for 3 cars
        n = len(values)
        widths = [22 if n <= 2 else 18] * n
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
    """Generic N-car comparison (2 or 3 cars)."""
    n = len(cars_data)
    car_ids = [c.upper() for c in cars_data]

    # Build comparison title
    if n == 2:
        title = t('comparison_title', c1=car_ids[0], c2=car_ids[1])
    elif n == 3:
        title = f"{t('comparison_title', c1=car_ids[0], c2=car_ids[1])} vs {car_ids[2]}"
    else:
        title = "COMPARISON: " + " vs ".join(car_ids)

    print(f"\n{title}\n" + "=" * 75)
    print("-" * 75 + f"\n{t('summary')}")

    # Column widths: 22 for 2 cars, 18 for 3 cars
    col_width = 22 if n <= 2 else 18
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
    if n == 2:
        best, worst = ranked[0], ranked[1]
        diff = results[worst]['tco'] - results[best]['tco']
        print(f"{car_ids[best]} is MORE ECONOMICAL than {car_ids[worst]} by {fmt_vnd(diff)}")
    elif n == 3:
        best, second, worst = ranked[0], ranked[1], ranked[2]
        diff_best = results[worst]['tco'] - results[best]['tco']
        diff_second = results[worst]['tco'] - results[second]['tco']
        print(f"{car_ids[best]} is the MOST ECONOMICAL")
        print(f"{car_ids[best]} is MORE ECONOMICAL than {car_ids[worst]} (least) by {fmt_vnd(diff_best)}")
        print(f"{car_ids[second]} is MORE ECONOMICAL than {car_ids[worst]} (least) by {fmt_vnd(diff_second)}")
    print("=" * 75 + "\n")

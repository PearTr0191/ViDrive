from src.config import BRAND_LIQUIDITY_MAP, LAST_UPDATED, DATA_RECENCY_DAYS, WIZARD_SEGMENTS
from datetime import date
from src.i18n import t, _lang

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
        print(t('input_invalid_num'))

def ask_bool(prompt, default=False):
    """Language-aware yes/no prompt. Uses y/n for English, c/k for Vietnamese."""
    yes_key = 'c' if _lang == 'vi' else 'y'
    no_key  = 'k' if _lang == 'vi' else 'n'
    default_char = yes_key if default else no_key
    disp = f"{prompt} [{default_char}]: "
    while True:
        val = input(disp).strip().lower() or default_char
        if val == yes_key: return True
        if val == no_key:  return False
        print(f"  Please enter '{yes_key}' or '{no_key}'.")

def select_car(cars, prompt=t('prompt_select_car')):
    car_ids = list(cars.keys())
    if not car_ids: return None
    print(f"\n{prompt}:")
    for i, cid in enumerate(car_ids):
        print(f"  {i+1}. {cars[cid]['brand']} {cars[cid].get('model', cid)}")
    n = len(car_ids)
    while True:
        choice = ask(t('prompt_number', n=n))
        if choice and choice.isdigit() and 1 <= int(choice) <= n:
            return car_ids[int(choice)-1]
        print(t('prompt_invalid_number', n=n))

def get_wizard_car():
    print(f"\n{t('wizard_title')}")
    data = {"brand": ask(t('wizard_brand')), "model": ask(t('wizard_model'), t('wizard_default_model'))}
    data["price"] = ask(t('wizard_price'), is_num=True)
    data["type"] = ask(t('wizard_type'), t('wizard_default_type')).upper()
    data["consumption"] = ask(t('wizard_consumption'), t('wizard_default_consumption'), is_num=True)
    data["annual_maintenance"] = ask(t('wizard_annual_maint'), t('wizard_default_annual_maint'), is_num=True)
    data["seats"] = int(ask(t('wizard_seats'), "5", is_num=True))
    print(f"\n{t('wizard_segments_title')}")
    for i, seg in enumerate(WIZARD_SEGMENTS):
        print(f"    {i+1}. {seg}")
    n_seg = len(WIZARD_SEGMENTS)
    while True:
        seg_choice = ask(t('wizard_segment_prompt', n=n_seg), "1")
        if seg_choice.isdigit() and 1 <= int(seg_choice) <= n_seg:
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

def row(label, v1, v2=None, w=22):
    f1 = fmt_vnd(v1) if isinstance(v1, (int, float)) else str(v1)
    if v2 is None:
        print(f"{label:<25} {f1:>{w}}")
    else:
        f2 = fmt_vnd(v2) if isinstance(v2, (int, float)) else str(v2)
        print(f"{label:<25} {f1:>22} {f2:>22}")

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

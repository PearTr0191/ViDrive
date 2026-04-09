from src.config import fmt_vnd, BRAND_LIQUIDITY_MAP

def print_header():
    print("\n--- VIDRIVE TCO CALCULATOR ---\n")

def row(label, v1, v2=None, w=22):
    f1 = fmt_vnd(v1) if isinstance(v1, (int, float)) else str(v1)
    if v2 is None:
        print(f"{label:<25} {f1:>{w}}")
    else:
        f2 = fmt_vnd(v2) if isinstance(v2, (int, float)) else str(v2)
        print(f"{label:<25} {f1:>22} {f2:>22}")

def print_car_list(cars):
    print(f"{'ID':<15} {'Brand':<10} {'Model':<20} {'Price':>15} {'Liquidity':>12}")
    print("-" * 75)
    for cid, c in cars.items():
        liq = BRAND_LIQUIDITY_MAP.get(c['brand'], "Tier 3")
        print(f"{cid:<15} {c['brand']:<10} {c.get('model', cid):<20} {fmt_vnd(c['price']):>15} {liq:>12}")

def print_report(title, specs, res1, res2=None, divider=45):
    print(f"{title}\n" + "-" * divider)
    for label, key in specs:
        if res2: row(label, res1[key], res2[key])
        else: row(label, res1[key])

def print_result(car_id, year, res, show_opp=True):
    print(f"Vehicle: {car_id.upper()}\n" + "=" * 45 + "\nSUMMARY")
    
    sections = [
        (("On-road purchase price", "on_road")),
        (("Lost Bank Interest", "opp_cost") if show_opp else (f"Net TCO ({year} Years)", "tco")),
        (("True Financial Impact", "true_financial_impact") if show_opp else None),
        (("Monthly Average", "monthly"))
    ]
    for label, key in [s for s in sections if s]: row(label, res[key], w=18)
    
    print("-" * 45 + "\n1. INITIAL OUTLAY")
    for l, k in [("MSRP Price", "price"), (" - Registration Tax", "reg_tax"), ("Total Outlay", "on_road")]:
        row(l, res[k], w=18)
    
    print("\n2. OPERATING COSTS")
    for l, k in [("Fuel / Energy", "fuel"), ("Maintenance", "maint"), ("Insurance & Fees", "legal"), ("Total Operating", "operating")]:
        row(l, res[k], w=18)
    
    print("\n3. RESALE & DEPRECIATION")
    row("Predicted Resale", res['resale'], w=18)
    row("Total Depreciation", res['depreciation'], w=18)
    print(f" Liquidity: {res['liquidity']}\n\n4. ENVIRONMENTAL RISKS (Provisions)")
    print(f" Hydro-Risk Level: {res['hydro_risk']['risk_level']}")
    row(" Est. Repair Cost", res['hydro_risk']['estimate'], w=18)
    print(" (Not included in TCO totals)\n" + "=" * 45 + "\n")

def print_comparison(c1_id, r1, c2_id, r2, show_opp=True):
    print(f"\nCOMPARISON: {c1_id.upper()} vs {c2_id.upper()}\n" + "=" * 75)
    print(f"{'Lifecycle Phase':<25} {c1_id.upper():>22} {c2_id.upper():>22}\n" + "-" * 75 + "\nSUMMARY")
    
    sum_spec = [("On-road purchase price", "on_road")]
    if show_opp: sum_spec += [("Lost Bank Interest", "opp_cost"), ("True Financial Impact", "true_financial_impact")]
    sum_spec += [("Monthly Average", "monthly")]
    for label, key in sum_spec: row(label, r1[key], r2[key])
    
    print("-" * 75 + "\n1. INITIAL OUTLAY")
    for l, k in [("MSRP Price", "price"), (" - Registration Tax", "reg_tax"), ("Total Outlay", "on_road")]:
        row(l, r1[k], r2[k])
    
    print("\n2. OPERATING COSTS")
    for l, k in [("Fuel / Energy", "fuel"), ("Maintenance", "maint"), ("Total Operating", "operating")]:
        row(l, r1[k], r2[k])

    print("\n3. RESALE & DEPRECIATION")
    row("Predicted Resale", r1['resale'], r2['resale'])
    row("Total Depreciation", r1['depreciation'], r2['depreciation'])
    row("Brand Liquidity", r1['liquidity'], r2['liquidity'])
    
    print("-" * 75 + "\n4. ENVIRONMENTAL RISKS")
    row("Hydro-Risk (Flood)", r1['hydro_risk']['risk_level'], r2['hydro_risk']['risk_level'])
    row("Repair Provision", r1['hydro_risk']['estimate'], r2['hydro_risk']['estimate'])
    
    diff = r1['tco'] - r2['tco']
    win = c2_id.upper() if diff > 0 else c1_id.upper()
    print("-" * 75 + f"\nVERDICT: {win} is MORE ECONOMICAL by {fmt_vnd(abs(diff))}\n" + "=" * 75 + "\n")

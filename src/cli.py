from src.config import fmt_vnd

def print_header():
    print("\n--- VIDRIVE TCO CALCULATOR ---\n")

def print_car_list(cars):
    print(f"{'ID':<15} {'Brand':<10} {'Model':<20} {'Price':>15}")
    print("-" * 65)
    for cid, c in cars.items():
        print(f"{cid:<15} {c['brand']:<10} {c.get('model', cid):<20} {fmt_vnd(c['price']):>15}")
    print("\n")

def print_result(car_id, year, res):
    # Premium Lifecycle Output (Buy -> Run -> Exit)
    print(f"Vehicle: {car_id.upper()}")
    print("=" * 45)
    
    print("SUMMARY")
    print(f"On-road purchase price: {fmt_vnd(res['on_road']):>18}")
    print(f"Net TCO ({year} Years):      {fmt_vnd(res['tco']):>18}")
    print(f"Monthly Average:        {fmt_vnd(res['monthly']):>18}")
    print("-" * 45)

    print("1. INITIAL OUTLAY")
    print(f"MSRP Price:             {fmt_vnd(res['price']):>18}")
    print(f" - Registration Tax:    {fmt_vnd(res['reg']['tax']):>18}")
    print(f" - Plate & Inspection:  {fmt_vnd(res['reg']['plate'] + res['reg']['inspection']):>18}")
    print(f"Total Outlay:           {fmt_vnd(res['on_road']):>18}")
    print("")

    print("2. OPERATING COSTS")
    print(f"Fuel / Energy:          {fmt_vnd(res['fuel']):>18}")
    print(f"Maintenance:            {fmt_vnd(res['maint']):>18}")
    print(f"Insurance & Fees:       {fmt_vnd(res['legal']):>18}")
    print(f"Total Operating:        {fmt_vnd(res['operating']):>18}")
    print("")

    print("3. RESALE & DEPRECIATION")
    print(f"Predicted Resale:       {fmt_vnd(res['resale']):>18}")
    print(f"Total Depreciation:     {fmt_vnd(res['depreciation']):>18}")
    print(f" Logic: {res['resale_logic']}")
    print("=" * 45)
    print("\n")

def print_comparison(c1_id, c1_res, c2_id, c2_res):
    # Side-by-Side Comparison
    print(f"\nCOMPARISON: {c1_id.upper()} vs {c2_id.upper()}")
    print("=" * 75)
    
    print(f"{'Lifecycle Phase':<25} {c1_id.upper():>22} {c2_id.upper():>22}")
    print("-" * 75)

    print("SUMMARY")
    print(f"{'On-road purchase price':<25} {fmt_vnd(c1_res['on_road']):>22} {fmt_vnd(c2_res['on_road']):>22}")
    print(f"{'Net TCO (5 Years)':<25} {fmt_vnd(c1_res['tco']):>22} {fmt_vnd(c2_res['tco']):>22}")
    print(f"{'Monthly Average':<25} {fmt_vnd(c1_res['monthly']):>22} {fmt_vnd(c2_res['monthly']):>22}")
    print("-" * 75)

    print("1. INITIAL OUTLAY")
    print(f"{'MSRP Price':<25} {fmt_vnd(c1_res['price']):>22} {fmt_vnd(c2_res['price']):>22}")
    print(f"{' - Registration Tax':<25} {fmt_vnd(c1_res['reg']['tax']):>22} {fmt_vnd(c2_res['reg']['tax']):>22}")
    print(f"{'Total Outlay':<25} {fmt_vnd(c1_res['on_road']):>22} {fmt_vnd(c2_res['on_road']):>22}")
    print("")

    print("2. OPERATING COSTS")
    print(f"{'Fuel / Energy':<25} {fmt_vnd(c1_res['fuel']):>22} {fmt_vnd(c2_res['fuel']):>22}")
    print(f"{'Maintenance':<25} {fmt_vnd(c1_res['maint']):>22} {fmt_vnd(c2_res['maint']):>22}")
    print(f"{'Total Operating':<25} {fmt_vnd(c1_res['operating']):>22} {fmt_vnd(c2_res['operating']):>22}")
    print("")

    print("3. RESALE & DEPRECIATION")
    print(f"{'Predicted Resale':<25} {fmt_vnd(c1_res['resale']):>22} {fmt_vnd(c2_res['resale']):>22}")
    print(f"{'Total Depreciation':<25} {fmt_vnd(c1_res['depreciation']):>22} {fmt_vnd(c2_res['depreciation']):>22}")
    print("-" * 75)

    diff = c1_res['tco'] - c2_res['tco']
    winner = c2_id.upper() if diff > 0 else c1_id.upper()
    print(f"VERDICT: {winner} is MORE ECONOMICAL by {fmt_vnd(abs(diff))}")
    print("=" * 75)
    print("\n")

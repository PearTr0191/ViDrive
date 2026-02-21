from src.config import fmt_vnd

# Minimalist UI Helper Functions

def print_header():
    print("\n--- VIDRIVE TCO CALCULATOR ---\n")

def print_car_list(cars):
    print(f"{'ID':<15} {'Brand':<10} {'Model':<20} {'Price':>15}")
    print("-" * 65)
    for cid, c in cars.items():
        print(f"{cid:<15} {c['brand']:<10} {c.get('model', 'Unknown'):<20} {fmt_vnd(c['price']):>15}")
    print("\n")

def print_result(car_id, year, breakdown):
    # Minimalist result print
    print(f"Vehicle: {car_id.upper()}")
    print("-" * 40)
    print(f"Acquisition:     {fmt_vnd(breakdown['price'] + breakdown['reg_fee']):>15}")
    print(f"Fuel/Charge:     {fmt_vnd(breakdown['fuel_total']):>15}")
    print(f"Maintenance:     {fmt_vnd(breakdown['maint_total']):>15}")
    if breakdown['battery_total'] > 0:
        print(f"Battery Rent:    {fmt_vnd(breakdown['battery_total']):>15}")
    
    print("-" * 40)
    print(f"Total Spent:     {fmt_vnd(breakdown['tco'] + breakdown['resale']):>15}")
    print(f"Resale Value:   -{fmt_vnd(breakdown['resale']):>15}")
    print("=" * 40)
    print(f"NET TCO ({year}y): {fmt_vnd(breakdown['tco']):>15}")
    print(f"Monthly Cost:    {fmt_vnd(breakdown['monthly']):>15}")
    print("\n")

def print_comparison(c1_id, c1_res, c2_id, c2_res):
    # Simple side-by-side text
    print(f"\nCOMPARISON: {c1_id} vs {c2_id}")
    print("-" * 60)
    print(f"{'Metric':<20} {c1_id:>18} {c2_id:>18}")
    print("-" * 60)
    
    metrics = [
        ("Purchase Price", c1_res['price'], c2_res['price']),
        ("Registration", c1_res['reg_fee'], c2_res['reg_fee']),
        ("Fuel/Charge", c1_res['fuel_total'], c2_res['fuel_total']),
        ("Maintenance", c1_res['maint_total'], c2_res['maint_total']),
        ("Battery Rent", c1_res['battery_total'], c2_res['battery_total']),
        ("Resale Value", c1_res['resale'], c2_res['resale']),
    ]
    
    for label, v1, v2 in metrics:
        print(f"{label:<20} {fmt_vnd(v1):>18} {fmt_vnd(v2):>18}")
        
    print("-" * 60)
    # Highlight the winner
    diff = c1_res['tco'] - c2_res['tco']
    print(f"{'NET TCO':<20} {fmt_vnd(c1_res['tco']):>18} {fmt_vnd(c2_res['tco']):>18}")
    
    print("\nVERDICT:")
    if diff > 0:
        print(f"-> {c2_id} is CHEAPER by {fmt_vnd(abs(diff))}")
    elif diff < 0:
        print(f"-> {c1_id} is CHEAPER by {fmt_vnd(abs(diff))}")
    else:
        print("-> It's a TIE.")
    print("\n")

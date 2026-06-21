_lang = 'en'

def set_language(lang):
    global _lang
    if lang in TRANSLATIONS:
        _lang = lang

def t(key, **kwargs):
    text = TRANSLATIONS[_lang].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

TRANSLATIONS = {
    'en': {
        # Title & Menu
        'app_title': '--- VIDRIVE TCO CALCULATOR ---',
        'choose_language': 'Choose language / Chọn ngôn ngữ (en/vi)',
        'welcome_msg': 'Welcome! What would you like to do?',
        'menu_1_car': '1. View Costs for 1 Car',
        'menu_compare': '2. Compare 2 Cars',
        'menu_wizard': '3. Enter a Custom Car',
        'menu_list': '4. List All Cars',
        'menu_exit': '5. Exit',
        'action': 'Action',

        # Wizard
        'wizard_title': '--- NEW CAR WIZARD ---',
        'wizard_brand': 'Brand',
        'wizard_model': 'Model',
        'wizard_default_model': 'Custom',
        'wizard_price': 'Price (e.g. 500m)',
        'wizard_type': 'Type (ICE/ICE-D/HEV/EV)',
        'wizard_default_type': 'ICE',
        'wizard_consumption': 'Consumption (L or kWh /100km)',
        'wizard_default_consumption': '6.0',
        'wizard_annual_maint': 'Annual Maintenance',
        'wizard_default_annual_maint': '8000000',
        'wizard_seats': 'Seats',
        'wizard_segments_title': '  Vehicle Segments:',
        'wizard_segment_prompt': '  Segment (1-{n})',
        'wizard_depr': 'Custom Annual Depreciation % (optional, e.g. 8)',
        'wizard_invalid_range': '  Invalid. Enter 1-{n}.',

        # User prompts
        'prompt_city': 'City/Province',
        'prompt_city_default': 'hanoi',
        'prompt_area_q': '\n  Is this location a City/Town (Area 2) or a Rural District (Area 3)?',
        'prompt_area_opts': '    1. City/Town [Default]\n    2. Rural District',
        'prompt_area_sel': '  Selection',
        'prompt_area_result': '  \u2192 {city} \u2192 Tier {area}',
        'prompt_annual_km': 'Annual KM',
        'prompt_years': 'Years of ownership',
        'prompt_city_ratio': '  Enter City Driving % (0-100)',
        'prompt_opp_cost': '  Include Capital Opportunity Cost? (y/n)',
        'prompt_select_car': 'Select a car',
        'prompt_car_1': 'Car 1',
        'prompt_car_2': 'Car 2',
        'prompt_number': 'Enter number (1-{n})',
        'prompt_invalid_number': 'Invalid. Enter 1-{n}.',
        'prompt_press_enter': 'Press Enter to return...',
        'prompt_run_again': '\nRun another calculation? (y/n)',
        'input_invalid_num': "Invalid number format. Use digits or '500m'.",

        # Car list header
        'list_header': '{0:<15} {1:<10} {2:<20} {3:>15} {4:>12}',
        'list_col_id': 'ID',
        'list_col_brand': 'Brand',
        'list_col_model': 'Model',
        'list_col_price': 'Price',
        'list_col_liquidity': 'Liquidity',

        # Recency warning
        'data_recency_warn': '  [!] Market data may be outdated (last updated {date}).',
        'data_recency_action': '      Update src/config.py with current prices.',

        # Result sections
        'summary': 'SUMMARY',
        'vehicle': 'Vehicle: {id}',
        'section_initial': '1. INITIAL OUTLAY',
        'section_operating': '2. OPERATING COSTS',
        'section_resale': '3. RESALE & DEPRECIATION',
        'section_environment': '4. ENVIRONMENTAL RISKS (Provisions)',
        'env_not_included': ' (Not included in TCO totals)',

        # Result labels
        'label_on_road': 'On-road purchase price',
        'label_opp_cost': 'Lost Bank Interest',
        'label_true_impact': 'True Financial Impact',
        'label_monthly': 'Monthly Average',
        'label_msrp': 'MSRP Price',
        'label_reg_tax': ' - Registration Tax',
        'label_total_outlay': 'Total Outlay',
        'label_fuel': 'Fuel / Energy',
        'label_maint': 'Maintenance',
        'label_legal': 'Insurance & Fees',
        'label_operating': 'Total Operating',
        'label_resale': 'Predicted Resale',
        'label_depreciation': 'Total Depreciation',
        'label_liquidity': 'Liquidity: {liq}',
        'label_hydro_risk': 'Hydro-Risk Level: {level}',
        'label_hydro_estimate': ' Est. Repair Cost',
        'label_net_tco': 'Net TCO ({y} Years)',
        'label_brand_liquidity': 'Brand Liquidity',

        # Comparison
        'comparison_title': 'COMPARISON: {c1} vs {c2}',
        'comparison_header': '{0:<25} {1:>22} {2:>22}',
        'comparison_verdict': 'VERDICT: {winner} is MORE ECONOMICAL by {diff}',
        'comparison_hydro_risk': 'Hydro-Risk (Flood)',
        'comparison_repair_prov': 'Repair Provision',

        # Deprecation logic label
        'resale_logic_custom': 'Custom',
        'resale_logic_parametric': 'Parametric',
        'resale_logic_ml': 'ML Model',
    },

    'vi': {
        # Title & Menu
        'app_title': '--- VIDRIVE T\u00cdNH TO\u00c1N CHI PH\u00cd ---',
        'choose_language': 'Ch\u1ecdn ng\u00f4n ng\u1eef / Choose language (en/vi)',
        'welcome_msg': 'Ch\u00e0o m\u1eebng! B\u1ea1n mu\u1ed1n l\u00e0m g\u00ec?',
        'menu_1_car': '1. Xem chi ph\u00ed cho 1 xe',
        'menu_compare': '2. So s\u00e1nh 2 xe',
        'menu_wizard': '3. Nh\u1eadp xe t\u00f9y ch\u1ec9nh',
        'menu_list': '4. Danh s\u00e1ch xe',
        'menu_exit': '5. Tho\u00e1t',
        'action': 'L\u1ef1a ch\u1ecdn',

        # Wizard
        'wizard_title': '--- NH\u1eacP XE T\u00d9Y CH\u1ec8NH ---',
        'wizard_brand': 'Nh\u00e3n hi\u1ec7u',
        'wizard_model': 'Phi\u00ean b\u1ea3n',
        'wizard_default_model': 'T\u00f9y ch\u1ec9nh',
        'wizard_price': 'Gi\u00e1 (vd: 500m)',
        'wizard_type': 'Lo\u1ea1i (ICE/ICE-D/HEV/EV)',
        'wizard_default_type': 'ICE',
        'wizard_consumption': 'Ti\u00eau hao (L ho\u1eb7c kWh /100km)',
        'wizard_default_consumption': '6.0',
        'wizard_annual_maint': 'B\u1ea3o d\u01b0\u1ee1ng h\u00e0ng n\u0103m',
        'wizard_default_annual_maint': '8000000',
        'wizard_seats': 'S\u1ed1 gh\u1ebf',
        'wizard_segments_title': '  Ph\u00e2n kh\u00fac:',
        'wizard_segment_prompt': '  Ph\u00e2n kh\u00fac (1-{n})',
        'wizard_depr': 'T\u1ef7 l\u1ec7 kh\u1ea5u hao ri\u00eang % (t\u00f9y ch\u1ecdn, vd: 8)',
        'wizard_invalid_range': '  Kh\u00f4ng h\u1ee3p l\u1ec7. Nh\u1eadp 1-{n}.',

        # User prompts
        'prompt_city': 'Th\u00e0nh ph\u1ed1 / T\u1ec9nh',
        'prompt_city_default': 'hanoi',
        'prompt_area_q': '\n  \u0110\u00e2y c\u00f3 ph\u1ea3i l\u00e0 Qu\u1eadn/Huy\u1ec7n n\u1ed9i th\u00e0nh (Khu v\u1ef1c 2) hay Huy\u1ec7n ngo\u1ea1i th\u00e0nh (Khu v\u1ef1c 3)?',
        'prompt_area_opts': '    1. N\u1ed9i th\u00e0nh (Khu v\u1ef1c 2) [M\u1eb7c \u0111\u1ecbnh]\n    2. Ngo\u1ea1i th\u00e0nh (Khu v\u1ef1c 3)',
        'prompt_area_sel': '  L\u1ef1a ch\u1ecdn',
        'prompt_area_result': '  \u2192 {city} \u2192 Khu v\u1ef1c {area}',
        'prompt_annual_km': 'S\u1ed1 km/n\u0103m',
        'prompt_years': 'S\u1ed1 n\u0103m s\u1edf h\u1eefu',
        'prompt_city_ratio': '  % l\u00e1i xe trong ph\u1ed1 (0-100)',
        'prompt_opp_cost': '  Bao g\u1ed3m Chi ph\u00ed C\u01a1 h\u1ed9i? (c/k)',
        'prompt_select_car': 'Ch\u1ecdn xe',
        'prompt_car_1': 'Xe 1',
        'prompt_car_2': 'Xe 2',
        'prompt_number': 'Nh\u1eadp s\u1ed1 (1-{n})',
        'prompt_invalid_number': 'Kh\u00f4ng h\u1ee3p l\u1ec7. Nh\u1eadp 1-{n}.',
        'prompt_press_enter': 'Nh\u1ea5n Enter \u0111\u1ec3 ti\u1ebfp t\u1ee5c...',
        'prompt_run_again': '\nT\u00ednh l\u1ea1i? (c/k)',
        'input_invalid_num': '\u0110\u1ecbnh d\u1ea1ng s\u1ed1 kh\u00f4ng h\u1ee3p l\u1ec7. D\u00f9ng s\u1ed1 ho\u1eb7c \u2018500m\u2019.',

        # Car list header
        'list_header': '{0:<18} {1:<12} {2:<20} {3:>18} {4:>12}',
        'list_col_id': 'M\u00e3 s\u1ed1',
        'list_col_brand': 'H\u00e3ng',
        'list_col_model': 'D\u00f2ng xe',
        'list_col_price': 'Gi\u00e1',
        'list_col_liquidity': 'Thanh kho\u1ea3n',

        # Recency warning
        'data_recency_warn': '  [!] D\u1eef li\u1ec7u th\u1ecb tr\u01b0\u1eddng c\u00f3 th\u1ec3 \u0111\u00e3 l\u00e2u (c\u1eadp nh\u1eadt: {date}).',
        'data_recency_action': '      C\u1eadp nh\u1eadt gi\u00e1 trong src/config.py.',

        # Result sections
        'summary': 'T\u1ed4NG QUAN',
        'vehicle': 'Xe: {id}',
        'section_initial': '1. CHI PH\u00cd L\u0102N \u0110\u1ea6U',
        'section_operating': '2. CHI PH\u00cd V\u1eacN H\u00c0NH',
        'section_resale': '3. GI\u00c1 TR\u1eca C\u00d2N L\u1ea0I & KH\u1ea4U HAO',
        'section_environment': '4. R\u1ee6I RO M\u00d4I TR\u01af\u1edcNG (D\u1ef1 ph\u00f2ng)',
        'env_not_included': ' (Kh\u00f4ng t\u00ednh v\u00e0o TCO)',

        # Result labels
        'label_on_road': 'Gi\u00e1 l\u0103n b\u00e1nh',
        'label_opp_cost': 'L\u00e3i su\u1ea5t ti\u1ebft ki\u1ec7m m\u1ea5t \u0111i',
        'label_true_impact': 'T\u00e1c \u0111\u1ed9ng t\u00e0i ch\u00ednh th\u1ef1c',
        'label_monthly': 'Trung b\u00ecnh/th\u00e1ng',
        'label_msrp': 'Gi\u00e1 ni\u00eam y\u1ebft',
        'label_reg_tax': ' - Thu\u1ebf tr\u01b0\u1edbc b\u1ea1',
        'label_total_outlay': 'T\u1ed5ng chi ban \u0111\u1ea7u',
        'label_fuel': 'Nhi\u00ean li\u1ec7u / \u0110i\u1ec7n',
        'label_maint': 'B\u1ea3o d\u01b0\u1ee1ng',
        'label_legal': 'B\u1ea3o hi\u1ec3m & Ph\u00ed',
        'label_operating': 'T\u1ed5ng v\u1eadn h\u00e0nh',
        'label_resale': 'Gi\u00e1 tr\u1ecb c\u00f2n l\u1ea1i',
        'label_depreciation': 'Kh\u1ea5u hao',
        'label_liquidity': 'Thanh kho\u1ea3n: {liq}',
        'label_hydro_risk': 'R\u1ee7i ro ng\u1eadp: {level}',
        'label_hydro_estimate': ' Chi ph\u00ed s\u1eeda ch\u1eefa \u01b0\u1edbc t\u00ednh',
        'label_net_tco': 'TCO thu\u1ea7n ({y} n\u0103m)',
        'label_brand_liquidity': 'Thanh kho\u1ea3n th\u01b0\u01a1ng hi\u1ec7u',

        # Comparison
        'comparison_title': 'SO S\u00c1NH: {c1} vs {c2}',
        'comparison_header': '{0:<25} {1:>22} {2:>22}',
        'comparison_verdict': 'K\u1ebeT LU\u1eacN: {winner} R\u1eba H\u01a0N {diff}',
        'comparison_hydro_risk': 'R\u1ee7i ro ng\u1eadp (L\u0169)',
        'comparison_repair_prov': 'D\u1ef1 ph\u00f2ng s\u1eeda ch\u1eefa',

        # Deprecation logic label
        'resale_logic_custom': 'T\u00f9y ch\u1ec9nh',
        'resale_logic_parametric': 'Tham s\u1ed1',
        'resale_logic_ml': 'ML Model',
    },
}

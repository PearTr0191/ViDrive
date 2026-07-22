_lang = 'vi'

def set_language(lang):
    global _lang
    if lang in TRANSLATIONS:
        _lang = lang

def t(key: str, **kwargs: object) -> str:
    text = TRANSLATIONS[_lang].get(key, key)
    if text is None:
        text = key
    if kwargs:
        return text.format(**kwargs)
    return text

TRANSLATIONS = {
    'en': {
        # Title & Menu
        'app_title': '--- VIDRIVE TCO CALCULATOR ---',
        'choose_language': 'Choose language / Chọn ngôn ngữ (en/vi) (vi)',
        'welcome_msg': 'Welcome! What would you like to do?',
        'menu_1_car': '1. View Costs for 1 Car',
        'menu_compare': '2. Compare Cars',
        'menu_wizard': '3. Enter a Custom Car',
        'menu_list': '4. List All Cars',
        'menu_exit': '5. Exit',
        'action': 'Action',

        # Wizard
        'wiz_title': '--- NEW CAR WIZARD ---',
        'wiz_brand': 'Brand',
        'wiz_model': 'Model',
        'wiz_default_model': 'Custom',
        'wiz_price': 'Price (e.g. 500m)',
        'wiz_type': 'Type (ICE/ICE-D/HEV/EV)',
        'wiz_default_type': 'ICE',
        'wiz_consumption': 'Consumption (L or kWh /100km)',
        'wiz_default_consumption': '6.0',
        'wiz_annual_maint': 'Annual Maintenance',
        'wiz_default_annual_maint': '8000000',
        'wiz_seats': 'Seats',
        'wiz_segments_title': '  Vehicle Segments:',
        'wiz_segment_prompt': '  Segment (1-{n})',
        'wiz_depr': 'Custom Annual Depreciation % (optional, e.g. 8)',
        'wiz_invalid_range': '  Invalid. Enter 1-{n}.',

        # User prompts
        'prompt_city': 'City/Province',
        'prompt_city_default': 'hanoi',
        'prompt_area_q': '\n  Is this location a City/Town (Area 2) or a Rural District (Area 3)?',
        'prompt_area_opts': '    1. City/Town [Default]\n    2. Rural District',
        'prompt_area_sel': '  Selection',
        'prompt_area_result': '  → {city} → Tier {area}',
        'prompt_annual_km': 'Annual KM',
        'prompt_years': 'Years of ownership',
        'prompt_city_ratio': '  Enter City Driving % (0-100)',
        'prompt_opp_cost': '  Include Capital Opportunity Cost?',
        'prompt_select_car': 'Select a car',
        'prompt_car_1': 'Car 1',
        'prompt_car_2': 'Car 2',
        'prompt_car_3': 'Car 3 (optional, press Enter to skip)',
        'prompt_number': 'Enter number (1-{n})',
        'prompt_invalid_number': 'Invalid. Enter 1-{n}.',
        'prompt_press_enter': 'Press Enter to return...',
        'prompt_run_again': '\nRun another calculation?',
        'input_invalid_num': "Invalid number format. Use digits or '500m'.",
        'prompt_export_pdf': 'Export to PDF?',
        'pdf_exported': 'PDF exported: {file}',
        'pdf_error': 'PDF export failed',
        'prompt_loan_calc': 'Want to calculate a loan plan?',
        'prompt_down_payment': 'Down payment %',
        'prompt_interest_rate': 'Interest rate % (annual)',
        'prompt_loan_term': 'Loan term (years)',
        'section_loan': '4. LOAN / FINANCING PLAN',
        'label_loan_monthly': 'Monthly Payment',
        'label_loan_total_interest': 'Total Interest Paid',
        'label_loan_total_repayment': 'Total Repayment',
        'label_loan_effective_cost': 'Effective Cost (with Loan)',
        'label_parking_toll': 'Parking & Tolls (est.)',
        'label_parking_monthly': 'Monthly Parking',
        'label_toll_monthly': 'Monthly Toll',
        'menu_compare': '2. Compare Multiple Cars',

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
        'compare_header': '{0:<25} {1:>22} {2:>22}',
        'compare_verdict': 'VERDICT: {winner} is MORE ECONOMICAL by {diff}',
        'compare_hydro_risk': 'Hydro-Risk (Flood)',
        'compare_repair_prov': 'Repair Provision',

        # Deprecation logic label
        'resale_logic_custom': 'Custom',
        'resale_logic_parametric': 'Parametric',
        'resale_logic_ml': 'ML Model',

        # Liquidity / Tiers
        'tier_1': 'Tier 1 (High Liquidity)',
        'tier_2': 'Tier 2',
        'tier_3': 'Tier 3 (Niche Market)',

        # Missing keys
        'label_resale_method': 'Resale Method',
        'prompt_skip': 'Press Enter to skip',
        'prompt_duplicate_car': '  That car is already selected. Choose a different one.',
    },

    'vi': {
        # Title & Menu
        'app_title': '--- VIDRIVE - XE THẬT, GIÁ TRỊ THẬT---',
        'choose_language': 'Choose language / Chọn ngôn ngữ (en/vi) (vi)',
        'welcome_msg': 'Chào bạn! Bạn muốn làm gì?',
        'menu_1_car': '1. Xem chi phí cho 1 xe (Tính TCO)',
        'menu_compare': '2. So sánh xe',
        'menu_wizard': '3. Thêm xe mới / Nhập thông tin',
        'menu_list': '4. Danh sách xe',
        'menu_exit': '5. Thoát',
        'action': 'Lựa chọn',

        # Wizard
        'wiz_title': '--- THÊM XE MỚI ---',
        'wiz_brand': 'Hãng',
        'wiz_model': 'Phiên bản / Mẫu',
        'wiz_default_model': 'Tùy chỉnh',
        'wiz_price': 'Giá (vd: 500m)',
        'wiz_type': 'Loại (ICE/ICE-D/HEV/EV)',
        'wiz_default_type': 'ICE',
        'wiz_consumption': 'Mức tiêu thụ (L hoặc kWh/100km)',
        'wiz_default_consumption': '6.0',
        'wiz_annual_maint': 'Chi phí bảo dưỡng/năm',
        'wiz_default_annual_maint': '8000000',
        'wiz_seats': 'Số chỗ',
        'wiz_segments_title': '  Phân khúc xe:',
        'wiz_segment_prompt': '  Phân khúc (1-{n})',
        'wiz_depr': 'Tỷ lệ khấu hao/năm (%) (tùy chọn, vd: 8)',
        'wiz_invalid_range': '  Không hợp lệ. Nhập 1-{n}.',

        # User prompts
        'prompt_city': 'Thành phố / Tỉnh',
        'prompt_city_default': 'hanoi',
        'prompt_area_q': '\n  Bạn ở nội thành (Khu vực 2) hay ngoại thành (Khu vực 3)?',
        'prompt_area_opts': '    1. Nội thành (Khu vực 2) [Mặc định]\n    2. Ngoại thành (Khu vực 3)',
        'prompt_area_sel': '  Lựa chọn',
        'prompt_area_result': '  → {city} → Khu vực {area}',
        'prompt_annual_km': 'Số km/năm',
        'prompt_years': 'Số năm sở hữu',
        'prompt_city_ratio': '  Tỷ lệ km chạy trong đô thị (%) (0-100)',
        'prompt_opp_cost': '  Có tính lãi cơ hội bị bỏ lỡ?',
        'prompt_select_car': 'Chọn xe',
        'prompt_car_1': 'Xe 1',
        'prompt_car_2': 'Xe 2',
        'prompt_car_3': 'Xe 3 (tùy chọn, nhấn Enter để bỏ qua)',
        'prompt_number': 'Nhập số (1-{n})',
        'prompt_invalid_number': 'Không hợp lệ. Nhập 1-{n}.',
        'prompt_press_enter': 'Nhấn Enter để tiếp tục...',
        'prompt_run_again': '\nTính lại?',
        'input_invalid_num': 'Định dạng số không hợp lệ. Dùng số hoặc "500m".',
        'prompt_export_pdf': 'Xuất ra PDF?',
        'prompt_loan_calc': 'Muốn tính kế hoạch vay?',
        'prompt_down_payment': 'Tỷ lệ trả trước %',
        'prompt_interest_rate': 'Lãi suất % (năm)',
        'prompt_loan_term': 'Kỳ hạn vay (năm)',
        'section_loan': '4. KẾ HOẠCH VAY / TÀI CHÍNH',
        'label_loan_monthly': 'Trả góp hàng tháng',
        'label_loan_total_interest': 'Tổng lãi đã trả',
        'label_loan_total_repayment': 'Tổng trả nợ',
        'label_loan_effective_cost': 'Chi phí thực tế (có vay)',
        'label_parking_toll': 'Đỗ xe & BOT (ước tính)',
        'label_parking_monthly': 'Đỗ xe/tháng',
        'label_toll_monthly': 'BOT/tháng',
        'menu_compare': '2. So sánh 2-3 xe',

        # Car list header
        'list_header': '{0:<18} {1:<12} {2:<20} {3:>18} {4:>12}',
        'list_col_id': 'Mã',
        'list_col_brand': 'Hãng',
        'list_col_model': 'Mẫu/ Phiên bản',
        'list_col_price': 'Giá',
        'list_col_liquidity': 'Thanh khoản',

        # Recency warning
        'data_recency_warn': '  [!] Dữ liệu thị trường có thể đã cũ (cập nhật: {date}).',
        'data_recency_action': '      Cập nhật giá trong src/config.py.',

        # Result sections
        'summary': 'TỔNG QUAN',
        'vehicle': 'Xe: {id}',
        'section_initial': '1. CHI PHÍ BAN ĐẦU',
        'section_operating': '2. CHI PHÍ VẬN HÀNH',
        'section_resale': '3. GIÁ BÁN LẠI & KHẤU HAO',
        # section_environment and flood-risk removed

        # Result labels
        'label_on_road': 'Giá lăn bánh',
        'label_opp_cost': 'Lãi đầu tư bỏ lỡ',
        'label_true_impact': 'Tổng chi phí thực tế',
        'label_monthly': 'Trung bình/tháng',
        'label_msrp': 'Giá niêm yết',
        'label_reg_tax': ' - Thuế trước bạ',
        'label_total_outlay': 'Tổng chi phí ban đầu',
        'label_fuel': 'Nhiên liệu / Điện',
        'label_maint': 'Bảo dưỡng',
        'label_legal': 'Bảo hiểm & Phí',
        'label_operating': 'Tổng chi phí vận hành',
        'label_resale': 'Giá bán lại (ước tính)',
        'label_depreciation': 'Khấu hao',
        'label_resale_method': 'Phương pháp tính',
        'label_liquidity': 'Thanh khoản: {liq}',
        # hydro/flood labels removed
        'label_net_tco': 'TCO ròng ({y} năm)',
        'label_brand_liquidity': 'Thanh khoản thương hiệu',
        # Comparison
        'comparison_title': 'SO SÁNH: {c1} vs {c2}',
        'comparison_header': '{0:<25} {1:>22} {2:>22}',
        'compare_verdict': 'KẾT LUẬN: {winner} tiết kiệm hơn {diff}',
        # comparison hydro keys removed

        # Liquidity / Tiers
        'tier_1': 'Tier 1 (High Liquidity)',
        'tier_2': 'Tier 2',
        'tier_3': 'Tier 3 (Niche Market)',

        # hydro risk labels removed

        # Deprecation logic label
        'resale_logic_custom': 'Tùy chỉnh',
        'resale_logic_parametric': 'Tham số',
        'resale_logic_ml': 'Mô hình ML',

        # Skip / duplicate prompts
        'prompt_skip': 'Nhấn Enter để bỏ qua',
        'prompt_duplicate_car': '  Xe này đã được chọn. Chọn xe khác.',
    },
}

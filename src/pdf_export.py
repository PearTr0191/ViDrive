"""ViDrive PDF Export via LaTeX - generates professional TCO reports."""
import asyncio
import re
import shutil
import threading
from datetime import date
from pathlib import Path
import src.i18n as i18n_mod
from src.i18n import t
from src.config import (
    PARKING_TOLL_ESTIMATES,
    APP_VERSION,
    MAINTENANCE_SPIKES,
    EV_MAINTENANCE_DISCOUNT,
    PDF_EXPORT_MAX_CONCURRENT,
    PDF_EXPORT_TIMEOUT_SEC,
)
from src.calculations import is_area1_metro

# Process-wide bound on concurrent pdflatex/FPDF renders. A threading.Semaphore
# (not asyncio.Semaphore) is correct here because each render is launched from a
# worker thread via asyncio.run(); an asyncio.Semaphore would bind to whichever
# event loop first created it and then raise cross-loop errors on later calls.
_PDF_SEM = threading.Semaphore(PDF_EXPORT_MAX_CONCURRENT)


def _safe_id(value: str) -> str:
    """Sanitize an external identifier for safe use in a file name (no traversal)."""
    return re.sub(r'[^a-z0-9_]', '_', str(value).lower())[:64]


def _generate_text_report_single(car_id: str, year: int, res: dict, city: str, km: int, years: int, area: int, ratio: float, show_opp: bool, loan: dict | None = None) -> str:
    """Generate plain-text report for single car."""
    lines = []
    lines.append(t("pdf_title"))
    lines.append("=" * 60)
    lines.append(f"{t('pdf_vehicle')}: {car_id.upper()}")
    lines.append(f"Date: {date.today().strftime('%d/%m/%Y')}")
    lines.append(f"City: {city.title()} | Area: {area} | Annual KM: {km:,} | Years: {years}")
    lines.append(f"City Ratio: {ratio*100:.0f}% city / {100-ratio*100:.0f}% highway")
    lines.append(f"Language: {t('language_name')} | ViDrive v{APP_VERSION}")
    lines.append("")
    
    lines.append("-" * 60)
    lines.append(t("summary"))
    lines.append("-" * 60)
    lines.append(f"  On-road Price:     {res['on_road']:>15,.0f} VND")
    lines.append(f"  Net TCO ({years} yr): {res['tco']:>15,.0f} VND")
    if show_opp:
        lines.append(f"  Opportunity Cost:  {res['opp_cost']:>15,.0f} VND")
        lines.append(f"  True Impact:       {res['true_financial_impact']:>15,.0f} VND")
    lines.append(f"  Monthly Average:   {res['monthly']:>15,.0f} VND")
    lines.append("")
    
    lines.append("-" * 60)
    lines.append(t("section_initial"))
    lines.append("-" * 60)
    lines.append(f"  MSRP Price:        {res['price']:>15,.0f} VND")
    lines.append(f"  Registration Tax:  {res['reg_tax']:>15,.0f} VND")
    lines.append(f"  Total Outlay:      {res['on_road']:>15,.0f} VND")
    lines.append("")
    
    lines.append("-" * 60)
    lines.append(t("section_operating"))
    lines.append("-" * 60)
    lines.append(f"  Fuel / Energy:     {res['fuel']:>15,.0f} VND")
    lines.append(f"  Maintenance:       {res['maint']:>15,.0f} VND")
    lines.append(f"  Insurance & Fees:  {res['legal']:>15,.0f} VND")
    lines.append(f"  Total Operating:   {res['operating']:>15,.0f} VND")
    pt = res.get('parking_toll')
    if pt:
        lines.append(f"  Parking & Tolls:   {pt['total_over_period']:>15,.0f} VND (provision)")
        lines.append(f"    Monthly Parking: {pt['monthly_parking']:>15,.0f} VND")
        lines.append(f"    Monthly Toll:    {pt['monthly_toll']:>15,.0f} VND")
    lines.append("")
    lines.append(t("pdf_note_parking"))
    lines.append("")
    
    lines.append("-" * 60)
    lines.append(t("section_resale"))
    lines.append("-" * 60)
    lines.append(f"  Predicted Resale:  {res['resale']:>15,.0f} VND")
    lines.append(f"  Total Depreciation:{res['depreciation']:>15,.0f} VND")
    raw_liq = res.get('liquidity', '')
    if raw_liq.startswith('Tier 1'):
        liq_disp = t('tier_1')
    elif raw_liq.startswith('Tier 2'):
        liq_disp = t('tier_2')
    else:
        liq_disp = t('tier_3')
    lines.append(f"  Resale Method:     {t('resale_logic_' + res['resale_logic'])}")
    lines.append(f"  Liquidity:         {liq_disp}")
    lines.append("")
    
    if loan:
        lines.append("-" * 60)
        lines.append(t("section_loan"))
        lines.append("-" * 60)
        lines.append(f"  Monthly Payment:    {loan['monthly_payment']:>15,.0f} VND")
        lines.append(f"  Total Interest:     {loan['total_interest']:>15,.0f} VND")
        lines.append(f"  Total Repayment:    {loan['total_repayment']:>15,.0f} VND")
        lines.append(f"  Effective Cost:     {loan['effective_cost']:>15,.0f} VND")
        lines.append("")
    
    lines.append("-" * 60)
    lines.append(t("section_assumptions"))
    lines.append("-" * 60)
    lines.append(f"  City/Province:     {city.title()}")
    lines.append(f"  Area:              {_area_name(area, city)}")
    lines.append(f"  Annual KM:         {km:,}")
    lines.append(f"  Years:             {years}")
    lines.append(f"  City/Highway Split:{ratio*100:.0f}% / {100-ratio*100:.0f}%")
    lines.append(f"  Opportunity Cost:  {t('pdf_yes') if show_opp else t('pdf_no')}")
    lines.append("")
    lines.append("-" * 60)
    lines.append(t("pdf_footer", version=APP_VERSION))
    lines.append("=" * 60)
    
    return "\n".join(lines)


def _generate_text_report_compare(cars_data: list, results: list, year: int, city: str, km: int, years: int, area: int, ratio: float, show_opp: bool, loans: list | None = None) -> str:
    """Generate plain-text report for multi-car comparison."""
    car_ids = [c.upper() for c in cars_data]
    n = len(car_ids)
    
    lines = []
    lines.append("=" * 80)
    lines.append(t("pdf_compare_title"))
    lines.append("=" * 80)
    lines.append(f"Vehicles: {' vs '.join(car_ids)}")
    lines.append(f"Date: {date.today().strftime('%d/%m/%Y')}")
    lines.append(f"City: {city.title()} | Area: {area} | Annual KM: {km:,} | Years: {years}")
    lines.append(f"City Ratio: {ratio*100:.0f}% city / {100-ratio*100:.0f}% highway")
    lines.append(f"Language: {t('language_name')} | ViDrive v{APP_VERSION}")
    lines.append("")
    
    # Summary table
    lines.append("-" * 80)
    lines.append(t("pdf_comparison_summary"))
    lines.append("-" * 80)
    
    header = f"{'Metric':<30}"
    for cid in car_ids:
        header += f"{cid:>22}"
    lines.append(header)
    lines.append("-" * 80)
    
    def add_row(label, vals):
        row = f"{label:<30}"
        for v in vals:
            row += f"{v:>22}"
        lines.append(row)
    
    add_row("On-road Price", [_fmt_vnd(r['on_road']) for r in results])
    add_row(f"Net TCO ({years} yr)", [_fmt_vnd(r['tco']) for r in results])
    if show_opp:
        add_row("Opportunity Cost", [_fmt_vnd(r['opp_cost']) for r in results])
        add_row("True Impact", [_fmt_vnd(r['true_financial_impact']) for r in results])
    add_row("Monthly Average", [_fmt_vnd(r['monthly']) for r in results])
    lines.append("")
    
    # Initial Outlay
    lines.append("-" * 80)
    lines.append(t("section_initial"))
    lines.append("-" * 80)
    for k, label in [('price', 'MSRP Price'), ('reg_tax', 'Registration Tax'), ('on_road', 'Total Outlay')]:
        add_row(label, [_fmt_vnd(r[k]) for r in results])
    lines.append("")
    
    # Operating Costs
    lines.append("-" * 80)
    lines.append(t("section_operating"))
    lines.append("-" * 80)
    for k, label in [('fuel', 'Fuel / Energy'), ('maint', 'Maintenance'), ('operating', 'Total Operating')]:
        add_row(label, [_fmt_vnd(r[k]) for r in results])
    lines.append("")
    
    # Parking & Toll
    lines.append("-" * 80)
    lines.append("PARKING & TOLLS (Provisions)")
    lines.append("-" * 80)
    for i, r in enumerate(results):
        pt = r.get('parking_toll')
        if pt:
            lines.append(f"  {car_ids[i]}:")
            lines.append(f"    Monthly Parking: {_fmt_vnd(pt['monthly_parking'])}")
            lines.append(f"    Monthly Toll:    {_fmt_vnd(pt['monthly_toll'])}")
            lines.append(f"    Total ({years} yr):  {_fmt_vnd(pt['total_over_period'])}")
    lines.append("(Note: Parking & Toll estimates are provisions, not included in TCO total.)")
    lines.append("")
    
    # Resale & Depreciation
    lines.append("-" * 80)
    lines.append(t("section_resale"))
    lines.append("-" * 80)
    for k, label in [('resale', 'Predicted Resale'), ('depreciation', 'Total Depreciation')]:
        add_row(label, [_fmt_vnd(r[k]) for r in results])
    lines.append(f"  Resale Method:     {t('resale_logic_' + results[0]['resale_logic'])}")
    
    # Brand Liquidity
    lines.append("  Brand Liquidity:")
    for i, r in enumerate(results):
        raw_liq = r.get('liquidity', '')
        if raw_liq.startswith('Tier 1'):
            liq_disp = t('tier_1')
        elif raw_liq.startswith('Tier 2'):
            liq_disp = t('tier_2')
        else:
            liq_disp = t('tier_3')
        lines.append(f"    {car_ids[i]}: {liq_disp}")
    lines.append("")
    
    # Loan
    if loans:
        lines.append("-" * 80)
        lines.append(t("section_loan"))
        lines.append("-" * 80)
        for k, label in [
            ('monthly_payment', 'Monthly Payment'),
            ('total_interest', 'Total Interest'),
            ('total_repayment', 'Total Repayment'),
            ('effective_cost', 'Effective Cost'),
        ]:
            add_row(label, [_fmt_vnd(loan[k]) for loan in loans])
        lines.append("")
    
    # Verdict
    lines.append("-" * 80)
    lines.append(t("pdf_verdict_header"))
    lines.append("-" * 80)
    min_idx = min(range(n), key=lambda i: results[i]['tco'])
    winner = car_ids[min_idx]
    for i in range(n):
        if i != min_idx:
            diff = results[i]['tco'] - results[min_idx]['tco']
            lines.append(f"  {winner} is MORE ECONOMICAL by {_fmt_vnd(abs(diff))} vs {car_ids[i]}")
    lines.append("")
    
    # Assumptions
    lines.append("-" * 80)
    lines.append(t("section_assumptions"))
    lines.append("-" * 80)
    lines.append(f"  City/Province:     {city.title()}")
    lines.append(f"  Area:              {_area_name(area, city)}")
    lines.append(f"  Annual KM:         {km:,}")
    lines.append(f"  Years:             {years}")
    lines.append(f"  City/Highway Split:{ratio*100:.0f}% / {100-ratio*100:.0f}%")
    lines.append(f"  Opportunity Cost:  {t('pdf_yes') if show_opp else t('pdf_no')}")
    lines.append("")
    lines.append("-" * 80)
    lines.append(t("pdf_footer", version=APP_VERSION))
    lines.append("=" * 80)
    
    return "\n".join(lines)



def _check_pdflatex() -> bool:
    """Check if pdflatex is available."""
    return shutil.which("pdflatex") is not None


def _area_name(area: int, city: str) -> str:
    """Return the human-readable area name with metro sub-tier support."""
    base = {
        1: "Area 1 (Central City)",
        2: "Area 2 (Provincial City)",
        3: "Area 3 (Rural/District)",
    }.get(area, "Area 2")
    if area == 1 and city and is_area1_metro(city):
        return "Area 1 (Metro — Hanoi/HCMC core)"
    return base


def _maintenance_spike_rows(car: dict, km: int, years: int) -> list:
    """Build maintenance breakdown rows showing base + each spike tier applied."""
    car_type = car.get('type', 'ICE')
    base_annual = car.get('annual_maintenance', 8_000_000)
    is_ev = car_type == 'EV'
    effective_base = base_annual * (EV_MAINTENANCE_DISCOUNT if is_ev else 1.0)
    rows = [[f"Base annual (× {years} yr)", _fmt_vnd(effective_base * years)]]
    total_km = km * years
    spikes = MAINTENANCE_SPIKES.get(car_type, MAINTENANCE_SPIKES['ICE'])
    for threshold, cost in spikes:
        if total_km >= threshold:
            rows.append([f"Major service @ {threshold:,} km", _fmt_vnd(cost)])
    rows.append(["Total maintenance", _fmt_vnd(effective_base * years + sum(c for t, c in spikes if total_km >= t))])
    return rows


def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters."""
    # Order matters: backslash must be replaced FIRST to avoid double-escaping
    replacements = [
        ('\\', r'\textbackslash{}'),
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\textasciitilde{}'),
        ('^', r'\textasciicircum{}'),
    ]
    for char, esc in replacements:
        text = text.replace(char, esc)
    return text


def _fmt_vnd(amount) -> str:
    """Format as VND with commas."""
    return f"{amount:,.0f} VND"


def _generate_latex_header(title: str) -> str:
    """Generate LaTeX document header."""
    today = date.today().strftime("%d/%m/%Y")
    lang_name = "English" if i18n_mod._lang == 'en' else "Tiếng Việt"
    
    return f"""\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{geometry}}
\\usepackage{{booktabs}}
\\usepackage{{longtable}}
\\usepackage{{array}}
\\usepackage{{xcolor}}
\\usepackage{{graphicx}}
\\geometry{{margin=2cm}}
\\definecolor{{ViDriveBlue}}{{RGB}}{{0, 82, 204}}
\\definecolor{{ViDriveGray}}{{RGB}}{{240, 240, 240}}
\\definecolor{{WinnerGreen}}{{RGB}}{{0, 128, 0}}

\\begin{{document}}
\\thispagestyle{{empty}}

% Header
\\begin{{center}}
    {{\\LARGE \\textbf{{\\color{{ViDriveBlue}} {_escape_latex(t('pdf_title'))}}}}}\\\\[0.3cm]
    {{\\Large {_escape_latex(title)}}}\\\\[0.2cm]
    {{\\normalsize Generated: {today} | Language: {lang_name} | ViDrive v{APP_VERSION}}}
\\end{{center}}
\\vspace{{0.5cm}}
\\hrule
\\vspace{{0.5cm}}
"""


def _generate_latex_footer() -> str:
    """Generate LaTeX document footer."""
    return """
\\vspace{1cm}
\\hrule
\\vspace{0.3cm}
\\begin{center}
    {\\small Generated by ViDrive TCO Calculator v{APP_VERSION}}\\\\
    {\\small \\textit{For informational purposes only. Not financial advice.}}
\\end{center}
\\end{document}
"""


def _assumptions_box(city: str, km: int, years: int, area: int, city_ratio: float, show_opp: bool) -> str:
    """Generate assumptions box as a table."""
    area_name = _area_name(area, city)
    
    lines = [
        r"\begin{center}",
        r"\begin{tabular}{l l}",
        r"\toprule",
        f"{t('prompt_city').replace(':', '')} & {_escape_latex(city.title())} \\\\",
        f"{t('prompt_area_result', city=city.title(), area=area).replace('→', '->')} & {_escape_latex(area_name)} \\\\",
        f"{t('prompt_annual_km').replace(':', '')} & {km:,} km \\\\",
        f"{t('prompt_years').replace(':', '')} & {years} years \\\\",
        f"{t('prompt_city_ratio').replace(':', '').replace('%', '')} & {city_ratio*100:.0f}\\% city / {100-city_ratio*100:.0f}\\% highway \\\\",
        f"{t('prompt_opp_cost').replace(':', '').replace('?', '')} & {'Yes' if show_opp else 'No'} \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{center}",
        r"\vspace{0.5cm}",
    ]
    return "\n".join(lines)


def _section_table(rows: list, col_count: int = 2) -> str:
    """Generate a LaTeX table for a section."""
    if col_count == 2:
        col_spec = "l r"
    else:
        col_spec = "l" + " r" * col_count
    
    lines = [f"\\begin{{tabular}}{{{col_spec}}}", r"\toprule"]
    for row in rows:
        if len(row) == 2:
            lines.append(f"{_escape_latex(row[0])} & {_escape_latex(row[1])} \\\\")
        elif len(row) == 3:
            lines.append(f"{_escape_latex(row[0])} & {_escape_latex(row[1])} & {_escape_latex(row[2])} \\\\")
        elif len(row) == 4:
            lines.append(f"{_escape_latex(row[0])} & {_escape_latex(row[1])} & {_escape_latex(row[2])} & {_escape_latex(row[3])} \\\\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\vspace{0.3cm}"])
    return "\n".join(lines)


def _check_fpdf() -> bool:
    """Return True if the pure-Python fpdf2 engine is importable."""
    try:
        import fpdf  # noqa: F401
        return True
    except Exception:
        return False


def _fpdf_font_setup(pdf, lang: str = "en") -> tuple:
    """Register a readable Unicode TTF for the PDF body.

    Primary face is the bundled Computer-Modern-derived KaTeX_Main for a LaTeX look
    (note: case-sensitive filename). A Vietnamese-capable serif (Times New Roman) is
    registered as a glyph fallback so accents in VI exports still render. Falls through
    to system serifs -> Arial -> core Helvetica (latin-1 only) when the bundle is absent.

    Returns (family, has_bold).
    """
    fonts_dir = Path(__file__).resolve().parents[1] / "fonts"

    katex = {
        "": fonts_dir / "KaTeX_Main-Regular.ttf",
        "B": fonts_dir / "KaTeX_Main-Bold.ttf",
        "I": fonts_dir / "KaTeX_Main-Italic.ttf",
        "BI": fonts_dir / "KaTeX_Main-BoldItalic.ttf",
    }
    if katex[""].exists():
        pdf.add_font("Body", "", str(katex[""]))
        has_bold = katex["B"].exists()
        if has_bold:
            pdf.add_font("Body", "B", str(katex["B"]))
        if katex["I"].exists():
            pdf.add_font("Body", "I", str(katex["I"]))
        if katex["BI"].exists():
            pdf.add_font("Body", "BI", str(katex["BI"]))
        # Computer Modern lacks Vietnamese glyphs -> register a serif fallback
        for fb_reg, fb_bold in [
            ("C:/Windows/Fonts/times.ttf", "C:/Windows/Fonts/timesbd.ttf"),
            ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
        ]:
            if Path(fb_reg).exists():
                pdf.add_font("SerifFallback", "", fb_reg)
                if fb_bold and Path(fb_bold).exists():
                    pdf.add_font("SerifFallback", "B", fb_bold)
                try:
                    pdf.set_fallback_fonts(["SerifFallback"])
                except Exception:
                    pass
                break
        return "Body", has_bold

    for reg, bold in [
        ("C:/Windows/Fonts/times.ttf", "C:/Windows/Fonts/timesbd.ttf"),
        ("C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/georgiab.ttf"),
        ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf"),
    ]:
        if Path(reg).exists():
            pdf.add_font("Body", "", reg)
            has_bold = bool(bold and Path(bold).exists())
            if has_bold:
                pdf.add_font("Body", "B", bold)
            return "Body", has_bold
    return "Helvetica", True


def _liq_disp(raw: str) -> str:
    if raw and raw.startswith("Tier 1"):
        return t("tier_1")
    if raw and raw.startswith("Tier 2"):
        return t("tier_2")
    return t("tier_3")



def _generate_pdf_single_fpdf(car_id, year, res, city, km, years, area, ratio, show_opp, loan, pdf_file) -> Path:
    """Render a real, readable PDF (fpdf2) for a single-car report."""
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 15, 15)
    fam, has_bold = _fpdf_font_setup(pdf)
    pdf.add_page()

    def h1(text: str) -> None:
        pdf.set_font(fam, "B" if has_bold else "", 18)
        pdf.cell(0, 10, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    def meta(text: str) -> None:
        pdf.set_font(fam, "", 10)
        pdf.cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")

    def section(title: str) -> None:
        pdf.ln(1)
        pdf.set_font(fam, "B" if has_bold else "", 13)
        pdf.set_text_color(0, 82, 204)
        pdf.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

    def kv(rows: list) -> None:
        pdf.set_font(fam, "", 10)
        with pdf.table(width=pdf.epw, col_widths=(0.66, 0.34), line_height=6, first_row_as_headings=False) as table:
            for label, value in rows:
                r = table.row()
                r.cell(str(label))
                r.cell(str(value))

    h1(t("pdf_title"))
    meta(f"{car_id.upper()}  |  {km:,} km/yr  |  {years} yr")
    meta(f"{t('pdf_generated')}: {date.today().strftime('%d/%m/%Y')}  |  {t('language_name')}  |  ViDrive v{APP_VERSION}")
    pdf.ln(2)

    section(t("section_summary"))
    rows = [
        [t("label_on_road"), _fmt_vnd(res.get("on_road", 0))],
        [t("label_net_tco", y=years), _fmt_vnd(res.get("tco", 0))],
    ]
    if show_opp:
        rows += [
            [t("label_opp_cost"), _fmt_vnd(res.get("opp_cost", 0))],
            [t("label_true_impact"), _fmt_vnd(res.get("true_financial_impact", 0))],
        ]
    rows.append([t("label_monthly"), _fmt_vnd(res.get("monthly", 0))])
    kv(rows)

    section(t("section_initial"))
    kv([
        [t("label_msrp"), _fmt_vnd(res.get("price", 0))],
        [t("label_reg_tax"), _fmt_vnd(res.get("reg_tax", 0))],
        [t("label_total_outlay"), _fmt_vnd(res.get("on_road", 0))],
    ])

    section(t("section_operating"))
    op_rows = [
        [t("label_fuel"), _fmt_vnd(res.get("fuel", 0))],
        [t("label_maint"), _fmt_vnd(res.get("maint", 0))],
        [t("label_legal"), _fmt_vnd(res.get("legal", 0))],
        [t("label_operating"), _fmt_vnd(res.get("operating", 0))],
    ]
    pt = res.get("parking_toll")
    if pt:
        op_rows += [
            [t("label_parking_toll"), _fmt_vnd(pt.get("total_over_period", 0))],
            ["  " + t("label_parking_monthly"), _fmt_vnd(pt.get("monthly_parking", 0))],
            ["  " + t("label_toll_monthly"), _fmt_vnd(pt.get("monthly_toll", 0))],
        ]
    kv(op_rows)
    if pt:
        pdf.set_font(fam, "", 9)
        pdf.multi_cell(0, 5, t("pdf_note_parking"),
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    section(t("section_resale"))
    kv([
        [t("label_resale"), _fmt_vnd(res.get("resale", 0))],
        [t("label_depreciation"), _fmt_vnd(res.get("depreciation", 0))],
        [t("label_resale_method") + ": " + t("resale_logic_" + str(res.get("resale_logic", "ml"))), ""],
        [t("label_liquidity_short"), _liq_disp(res.get("liquidity", ""))],
    ])

    if loan:
        section(t("section_loan"))
        kv([
            [t("label_loan_monthly"), _fmt_vnd(loan.get("monthly_payment", 0))],
            [t("label_loan_total_interest"), _fmt_vnd(loan.get("total_interest", 0))],
            [t("label_loan_total_repayment"), _fmt_vnd(loan.get("total_repayment", 0))],
            [t("label_loan_effective_cost"), _fmt_vnd(loan.get("effective_cost", 0))],
        ])

    section(t("section_assumptions"))
    pdf.set_font(fam, "", 9)
    pdf.multi_cell(0, 5,
        f"{t('prompt_city')}: {city.title()}\n"
        f"{t('pdf_area_label')}: {_area_name(area, city)}\n"
        f"{t('prompt_annual_km')}: {km:,}\n"
        f"{t('prompt_years')}: {years}\n"
        f"{t('pdf_split')}: {ratio * 100:.0f}% / {100 - ratio * 100:.0f}%\n"
        f"{t('prompt_opp_cost')}: {t('pdf_yes') if show_opp else t('pdf_no')}",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(2)
    pdf.set_font(fam, "", 8)
    pdf.multi_cell(0, 4,
        t("pdf_footer", version=APP_VERSION),
        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.output(str(pdf_file))
    return pdf_file



def _generate_pdf_compare_fpdf(cars_data, results, year, city, km, years, area, ratio, show_opp, loans, pdf_file) -> Path:
    """Render a real, readable PDF (fpdf2) for a multi-car comparison."""
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(12, 12, 12)
    fam, has_bold = _fpdf_font_setup(pdf)
    pdf.add_page()
    car_ids = [c.upper() for c in cars_data]
    n = len(car_ids)

    pdf.set_font(fam, "B" if has_bold else "", 16)
    pdf.cell(0, 9, t("pdf_compare_title"), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.set_font(fam, "", 10)
    pdf.cell(0, 6, " vs ".join(car_ids) + f"  |  {km:,} km/yr  |  {years} yr", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
    pdf.ln(2)

    headers = ["Metric"] + car_ids
    colw = [0.34] + [0.66 / n] * n
    pdf.set_font(fam, "B" if has_bold else "", 10)
    with pdf.table(width=pdf.epw, col_widths=colw, line_height=6, first_row_as_headings=True) as table:
        hr = table.row()
        for h in headers:
            hr.cell(h)

        def add_cmp(label: str, key: str) -> None:
            r = table.row()
            r.cell(label)
            for res in results:
                r.cell(_fmt_vnd(res.get(key, 0)))

        add_cmp(t("label_on_road"), "on_road")
        add_cmp(t("label_net_tco", y=years), "tco")
        if show_opp:
            add_cmp(t("label_opp_cost"), "opp_cost")
            add_cmp(t("label_true_impact"), "true_financial_impact")
        add_cmp(t("label_monthly"), "monthly")
        add_cmp(t("label_msrp"), "price")
        add_cmp(t("label_reg_tax"), "reg_tax")
        add_cmp(t("label_fuel"), "fuel")
        add_cmp(t("label_maint"), "maint")
        add_cmp(t("label_operating"), "operating")
        add_cmp(t("label_resale"), "resale")
        add_cmp(t("label_depreciation"), "depreciation")
    pdf.ln(2)

    pdf.set_font(fam, "", 9)
    pdf.multi_cell(0, 5,
        f"Resale Method: {t('resale_logic_' + str(results[0].get('resale_logic', 'ml')))}\n"
        f"Brand Liquidity: " + "  |  ".join(
            f"{cid}: {_liq_disp(r.get('liquidity', ''))}" for cid, r in zip(car_ids, results)
        ),
        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)

    min_idx = min(range(n), key=lambda i: results[i]["tco"])
    winner = car_ids[min_idx]
    for i in range(n):
        if i != min_idx:
            diff = results[i]["tco"] - results[min_idx]["tco"]
            pdf.set_font(fam, "B" if has_bold else "", 10)
            pdf.set_text_color(0, 128, 0)
            pdf.cell(0, 6, t("compare_verdict", winner=winner, diff=_fmt_vnd(abs(diff))), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.set_font(fam, "B" if has_bold else "", 12)
    pdf.cell(0, 7, t("section_assumptions"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font(fam, "", 9)
    pdf.multi_cell(0, 5,
        f"{t('prompt_city')}: {city.title()}\n"
        f"{t('pdf_area_label')}: {_area_name(area, city)}\n"
        f"{t('prompt_annual_km')}: {km:,}\n"
        f"{t('prompt_years')}: {years}\n"
        f"{t('pdf_split')}: {ratio * 100:.0f}% / {100 - ratio * 100:.0f}%\n"
        f"{t('prompt_opp_cost')}: {t('pdf_yes') if show_opp else t('pdf_no')}",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_font(fam, "", 8)
    pdf.multi_cell(0, 4,
        t("pdf_footer", version=APP_VERSION),
        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.output(str(pdf_file))
    return pdf_file


def generate_pdf_single(car_id: str, year: int, res: dict, city: str, km: int, years: int, area: int, ratio: float, show_opp: bool, loan: dict | None = None, target_dir: Path | None = None) -> str:
    """Generate a real PDF for single-car TCO (pdflatex > fpdf2 > text fallback).

    Acquires the shared PDF semaphore and applies a per-render timeout.
    Writes all output files to *target_dir* (created via tempfile.mkdtemp by the
    caller) so the working directory is never polluted.
    Returns a human-readable status string.
    """
    with _PDF_SEM:
        sem = asyncio.Semaphore(PDF_EXPORT_MAX_CONCURRENT)
        return asyncio.run(
            _generate_pdf_single_async(sem, car_id, year, res, city, km, years, area, ratio, show_opp, loan, target_dir)
        )


async def _generate_pdf_single_async(
    sem: asyncio.Semaphore,
    car_id: str, year: int, res: dict, city: str, km: int, years: int,
    area: int, ratio: float, show_opp: bool, loan: dict | None,
    target_dir: Path | None,
) -> str:
    async with sem:
        pdflatex_available = _check_pdflatex()

        out_dir = target_dir if target_dir is not None else Path.cwd()
        # Sanitize car_id before using it in any file path (prevents traversal;
        # must match the safe_id computed by the API endpoint for the lookup).
        safe_car = _safe_id(car_id)
        filename_base = f"vidrive_{safe_car}_{date.today().strftime('%Y%m%d')}"
        tex_file = out_dir / f"{filename_base}.tex"
        pdf_file = out_dir / f"{filename_base}.pdf"

        # Build LaTeX content
        title = f"{car_id.upper()} | {t('prompt_annual_km')} {km:,} km | {years} {t('prompt_years').lower()}"
        latex = _generate_latex_header(title)

        # Summary Table
        latex += r"\section*{Summary}" + "\n"
        summary_rows = [
            [t('label_on_road'), _fmt_vnd(res['on_road'])],
            [t('label_net_tco', y=years), _fmt_vnd(res['tco'])],
        ]
        if show_opp:
            summary_rows.extend([
                [t('label_opp_cost'), _fmt_vnd(res['opp_cost'])],
                [t('label_true_impact'), _fmt_vnd(res['true_financial_impact'])],
            ])
        summary_rows.append([t('label_monthly'), _fmt_vnd(res['monthly'])])
        latex += _section_table(summary_rows)

        # Section 1: Initial Outlay
        latex += r"\section*{" + _escape_latex(t('section_initial')) + "}" + "\n"
        initial_rows = [
            [t('label_msrp'), _fmt_vnd(res['price'])],
            [t('label_reg_tax'), _fmt_vnd(res['reg_tax'])],
            [t('label_total_outlay'), _fmt_vnd(res['on_road'])],
        ]
        latex += _section_table(initial_rows)

        # Section 2: Operating Costs
        latex += r"\section*{" + _escape_latex(t('section_operating')) + "}" + "\n"
        operating_rows = [
            [t('label_fuel'), _fmt_vnd(res['fuel'])],
            [t('label_maint'), _fmt_vnd(res['maint'])],
            [t('label_legal'), _fmt_vnd(res['legal'])],
            [t('label_operating'), _fmt_vnd(res['operating'])],
        ]
        # Parking & Toll
        pt = res.get('parking_toll')
        if pt:
            operating_rows.extend([
                [t('label_parking_toll'), _fmt_vnd(pt['total_over_period'])],
                ["  " + t('label_parking_monthly'), _fmt_vnd(pt['monthly_parking'])],
                ["  " + t('label_toll_monthly'), _fmt_vnd(pt['monthly_toll'])],
            ])
        latex += _section_table(operating_rows)
        if pt:
            latex += r"\textit{Note: Parking \& Toll estimates are provisions, not included in TCO total.}" + "\n\n"

        # Section 3: Resale & Depreciation
        latex += r"\section*{" + _escape_latex(t('section_resale')) + "}" + "\n"
        resale_rows = [
            [t('label_resale'), _fmt_vnd(res['resale'])],
            [t('label_depreciation'), _fmt_vnd(res['depreciation'])],
            [t('label_resale_method') + ": " + t('resale_logic_' + res['resale_logic']), ""],
        ]
        latex += _section_table(resale_rows)

        # Liquidity
        raw_liq = res.get('liquidity', '')
        if raw_liq.startswith('Tier 1'):
            liq_disp = t('tier_1')
        elif raw_liq.startswith('Tier 2'):
            liq_disp = t('tier_2')
        else:
            liq_disp = t('tier_3')
        latex += f"{_escape_latex(t('label_liquidity', liq=liq_disp))}\n\n"

        # Section 4: Loan / Financing Plan (if provided)
        if loan:
            latex += r"\section*{" + _escape_latex(t('section_loan')) + "}" + "\n"
            loan_rows = [
                [t('label_loan_monthly'), _fmt_vnd(loan['monthly_payment'])],
                [t('label_loan_total_interest'), _fmt_vnd(loan['total_interest'])],
                [t('label_loan_total_repayment'), _fmt_vnd(loan['total_repayment'])],
                [t('label_loan_effective_cost'), _fmt_vnd(loan['effective_cost'])],
            ]
            latex += _section_table(loan_rows)

        # Assumptions
        latex += r"\section*{Assumptions}" + "\n"
        latex += _assumptions_box(city, km, years, area, ratio, show_opp)

        # Footer
        latex += _generate_latex_footer()

        # Write .tex file
        tex_file.write_text(latex, encoding='utf-8')

        # Compile to PDF if pdflatex is available
        if pdflatex_available:
            try:
                proc = await asyncio.wait_for(
                    asyncio.create_subprocess_exec(
                        "pdflatex", "-interaction=nonstopmode",
                        "-output-directory", str(out_dir), str(tex_file),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    ),
                    timeout=PDF_EXPORT_TIMEOUT_SEC,
                )
                proc_ret = await proc.wait()
                if proc_ret == 0:
                    # Run twice for cross-references
                    try:
                        proc2 = await asyncio.wait_for(
                            asyncio.create_subprocess_exec(
                                "pdflatex", "-interaction=nonstopmode",
                                "-output-directory", str(out_dir), str(tex_file),
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE,
                            ),
                            timeout=PDF_EXPORT_TIMEOUT_SEC,
                        )
                        await proc2.wait()
                    except asyncio.TimeoutExpired:
                        pass
                    # Clean up auxiliary files
                    for ext in ['.aux', '.log', '.out']:
                        aux_file = out_dir / f"{filename_base}{ext}"
                        if aux_file.exists():
                            aux_file.unlink()
                    return f"PDF generated: {pdf_file}"
                else:
                    return f"LaTeX compilation failed. .tex file saved: {tex_file}"
            except asyncio.TimeoutExpired:
                return f"LaTeX compilation timed out. .tex file saved: {tex_file}"
            except Exception as e:
                return f"PDF generation error: {e}. .tex file saved: {tex_file}"

        # Pure-Python PDF engine (no external TeX toolchain required)
        if _check_fpdf():
            try:
                await asyncio.to_thread(
                    _generate_pdf_single_fpdf, car_id, year, res, city, km, years,
                    area, ratio, show_opp, loan, pdf_file,
                )
                return f"PDF generated: {pdf_file}"
            except Exception:
                pass  # fall through to plain-text

        # Plain-text fallback when no PDF engine is available
        txt_file = out_dir / f"{filename_base}.txt"
        txt_content = _generate_text_report_single(car_id, year, res, city, km, years, area, ratio, show_opp, loan)
        txt_file.write_text(txt_content, encoding='utf-8')
        return f"PDF engine unavailable. .tex + .txt saved: {tex_file}, {txt_file} (install TeX Live/MiKTeX or fpdf2 for PDF)"


def generate_pdf_compare(cars_data: list, results: list, year: int, city: str, km: int, years: int, area: int, ratio: float, show_opp: bool, loans: list | None = None, target_dir: Path | None = None) -> str:
    """Generate PDF for multi-car comparison.

    Acquires the shared PDF semaphore and applies a per-render timeout.
    Writes all output files to *target_dir* so the working directory is never
    polluted.
    """
    with _PDF_SEM:
        sem = asyncio.Semaphore(PDF_EXPORT_MAX_CONCURRENT)
        return asyncio.run(
            _generate_pdf_compare_async(sem, cars_data, results, year, city, km, years, area, ratio, show_opp, loans, target_dir)
        )


async def _generate_pdf_compare_async(
    sem: asyncio.Semaphore,
    cars_data: list, results: list, year: int, city: str, km: int, years: int,
    area: int, ratio: float, show_opp: bool, loans: list | None,
    target_dir: Path | None,
) -> str:
    async with sem:
        pdflatex_available = _check_pdflatex()

        out_dir = target_dir if target_dir is not None else Path.cwd()
        filename_base = f"vidrive_compare_{date.today().strftime('%Y%m%d')}"
        tex_file = out_dir / f"{filename_base}.tex"
        pdf_file = out_dir / f"{filename_base}.pdf"

        car_ids = [c.upper() for c in cars_data]
        n = len(car_ids)

        # Build LaTeX content
        title = " vs ".join(car_ids) + f" | {t('prompt_annual_km')} {km:,} km | {years} {t('prompt_years').lower()}"
        latex = _generate_latex_header(title)

        # Summary Comparison Table
        latex += r"\section*{Comparison Summary}" + "\n"

        # Build header row
        if n == 2:
            col_spec = "l r r"
            header = ["Metric", car_ids[0], car_ids[1]]
        else:
            col_spec = "l r r r"
            header = ["Metric", car_ids[0], car_ids[1], car_ids[2]]

        summary_rows = [header]
        summary_rows.append([
            t('label_on_road'),
            _fmt_vnd(results[0]['on_road']),
            _fmt_vnd(results[1]['on_road']),
        ])
        if n == 3:
            summary_rows[-1].append(_fmt_vnd(results[2]['on_road']))

        summary_rows.append([
            t('label_net_tco', y=years),
            _fmt_vnd(results[0]['tco']),
            _fmt_vnd(results[1]['tco']),
        ])
        if n == 3:
            summary_rows[-1].append(_fmt_vnd(results[2]['tco']))

        if show_opp:
            summary_rows.append([
                t('label_opp_cost'),
                _fmt_vnd(results[0]['opp_cost']),
                _fmt_vnd(results[1]['opp_cost']),
            ])
            if n == 3:
                summary_rows[-1].append(_fmt_vnd(results[2]['opp_cost']))

            summary_rows.append([
                t('label_true_impact'),
                _fmt_vnd(results[0]['true_financial_impact']),
                _fmt_vnd(results[1]['true_financial_impact']),
            ])
            if n == 3:
                summary_rows[-1].append(_fmt_vnd(results[2]['true_financial_impact']))

        summary_rows.append([
            t('label_monthly'),
            _fmt_vnd(results[0]['monthly']),
            _fmt_vnd(results[1]['monthly']),
        ])
        if n == 3:
            summary_rows[-1].append(_fmt_vnd(results[2]['monthly']))

        # Build the table
        lines = [f"\\begin{{tabular}}{{{col_spec}}}", r"\toprule"]
        for i, row in enumerate(summary_rows):
            if i == 0:
                lines.append(" & ".join(_escape_latex(c) for c in row) + r" \\ \midrule")
            else:
                lines.append(" & ".join(_escape_latex(c) for c in row) + r" \\")
        lines.extend([r"\bottomrule", r"\end{tabular}", r"\vspace{0.5cm}"])
        latex += "\n".join(lines)

        # Initial Outlay
        latex += r"\section*{" + _escape_latex(t('section_initial')) + "}" + "\n"
        initial_rows = [["", *car_ids]]
        for k in ['price', 'reg_tax', 'on_road']:
            label = {'price': t('label_msrp'), 'reg_tax': t('label_reg_tax'), 'on_road': t('label_total_outlay')}[k]
            row = [label]
            for r in results:
                row.append(_fmt_vnd(r[k]))
            initial_rows.append(row)
        latex += _section_table(initial_rows, col_count=n)

        # Operating Costs
        latex += r"\section*{" + _escape_latex(t('section_operating')) + "}" + "\n"
        operating_rows = [["", *car_ids]]
        for k in ['fuel', 'maint', 'operating']:
            label = {'fuel': t('label_fuel'), 'maint': t('label_maint'), 'operating': t('label_operating')}[k]
            row = [label]
            for r in results:
                row.append(_fmt_vnd(r[k]))
            operating_rows.append(row)
        latex += _section_table(operating_rows, col_count=n)

        # Parking & Toll - generate as separate sub-table per car (cleaner layout)
        latex += r"\subsection*{" + _escape_latex(t('label_parking_toll')) + "}" + "\n"
        for i, r in enumerate(results):
            pt = r.get('parking_toll')
            if pt:
                pt_rows = [
                    [car_ids[i] + " - " + t('label_parking_monthly'), _fmt_vnd(pt['monthly_parking'])],
                    [car_ids[i] + " - " + t('label_toll_monthly'), _fmt_vnd(pt['monthly_toll'])],
                    [car_ids[i] + " - Total (" + str(years) + " yr)", _fmt_vnd(pt['total_over_period'])],
                ]
                lines = [r"\begin{tabular}{l r}", r"\toprule"]
                for row in pt_rows:
                    lines.append(" & ".join(_escape_latex(c) for c in row) + r" \\")
                lines.extend([r"\bottomrule", r"\end{tabular}", r"\vspace{0.3cm}"])
                latex += "\n".join(lines)
        latex += r"\textit{Note: Parking \& Toll estimates are provisions, not included in TCO total.}" + "\n\n"

        # Resale & Depreciation
        latex += r"\section*{" + _escape_latex(t('section_resale')) + "}" + "\n"
        resale_rows = [["", *car_ids]]
        for k in ['resale', 'depreciation']:
            label = {'resale': t('label_resale'), 'depreciation': t('label_depreciation')}[k]
            row = [label]
            for r in results:
                row.append(_fmt_vnd(r[k]))
            resale_rows.append(row)
        latex += _section_table(resale_rows, col_count=n)
        latex += f"{_escape_latex(t('label_resale_method') + ': ' + t('resale_logic_' + results[0]['resale_logic']))}\n\n"

        # Brand Liquidity
        liq_rows = [["", *car_ids]]
        row = [t('label_brand_liquidity')]
        for r in results:
            raw_liq = r.get('liquidity', '')
            if raw_liq.startswith('Tier 1'):
                liq_disp = t('tier_1')
            elif raw_liq.startswith('Tier 2'):
                liq_disp = t('tier_2')
            else:
                liq_disp = t('tier_3')
            row.append(liq_disp)
        liq_rows.append(row)
        latex += _section_table(liq_rows, col_count=n)

        # Section: Loan / Financing Plan (if provided)
        if loans:
            latex += r"\section*{" + _escape_latex(t('section_loan')) + "}" + "\n"
            loan_rows = [["", *car_ids]]
            for k in ['monthly_payment', 'total_interest', 'total_repayment', 'effective_cost']:
                label = {
                    'monthly_payment': t('label_loan_monthly'),
                    'total_interest': t('label_loan_total_interest'),
                    'total_repayment': t('label_loan_total_repayment'),
                    'effective_cost': t('label_loan_effective_cost'),
                }[k]
                row = [label]
                for loan in loans:
                    row.append(_fmt_vnd(loan[k]))
                loan_rows.append(row)
            latex += _section_table(loan_rows, col_count=n)

        # Verdict
        latex += r"\section*{Verdict}" + "\n"
        min_idx = min(range(n), key=lambda i: results[i]['tco'])
        winner = car_ids[min_idx]
        for i in range(n):
            if i != min_idx:
                diff = results[i]['tco'] - results[min_idx]['tco']
                verdict_text = t('compare_verdict', winner=winner, diff=_fmt_vnd(abs(diff)))
                latex += f"\\textbf{{\\color{{WinnerGreen}} {_escape_latex(verdict_text)}}}\\\\\n"

        # Assumptions
        latex += r"\section*{Assumptions}" + "\n"
        latex += _assumptions_box(city, km, years, area, ratio, show_opp)

        # Footer
        latex += _generate_latex_footer()

        # Write .tex file
        tex_file.write_text(latex, encoding='utf-8')

        # Compile to PDF if pdflatex available
        if pdflatex_available:
            try:
                proc = await asyncio.wait_for(
                    asyncio.create_subprocess_exec(
                        "pdflatex", "-interaction=nonstopmode",
                        "-output-directory", str(out_dir), str(tex_file),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    ),
                    timeout=PDF_EXPORT_TIMEOUT_SEC,
                )
                proc_ret = await proc.wait()
                if proc_ret == 0:
                    try:
                        proc2 = await asyncio.wait_for(
                            asyncio.create_subprocess_exec(
                                "pdflatex", "-interaction=nonstopmode",
                                "-output-directory", str(out_dir), str(tex_file),
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE,
                            ),
                            timeout=PDF_EXPORT_TIMEOUT_SEC,
                        )
                        await proc2.wait()
                    except asyncio.TimeoutExpired:
                        pass
                    for ext in ['.aux', '.log', '.out']:
                        aux_file = out_dir / f"{filename_base}{ext}"
                        if aux_file.exists():
                            aux_file.unlink()
                    return f"PDF generated: {pdf_file}"
                else:
                    return f"LaTeX compilation failed. .tex file saved: {tex_file}"
            except asyncio.TimeoutExpired:
                return f"LaTeX compilation timed out. .tex file saved: {tex_file}"
            except Exception as e:
                return f"PDF generation error: {e}. .tex file saved: {tex_file}"
        # Pure-Python PDF engine (no external TeX toolchain required)
        if _check_fpdf():
            try:
                await asyncio.to_thread(
                    _generate_pdf_compare_fpdf, cars_data, results, year, city, km, years,
                    area, ratio, show_opp, loans, pdf_file,
                )
                return f"PDF generated: {pdf_file}"
            except Exception:
                pass  # fall through to plain-text

        # Plain-text fallback when no PDF engine is available
        txt_file = out_dir / f"{filename_base}.txt"
        txt_content = _generate_text_report_compare(cars_data, results, year, city, km, years, area, ratio, show_opp, loans)
        txt_file.write_text(txt_content, encoding='utf-8')
        return f"pdflatex/fpdf2 unavailable. .tex + .txt saved: {tex_file}, {txt_file} (install TeX Live/MiKTeX or fpdf2 for PDF)"

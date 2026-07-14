"""
Multi-source scraper: extracts listings from chotot.vn, oto.com.vn, bonbanh.com
and merges into training_data.json.

Usage:
  python data/models/multi_source_scraper.py
  Then follow the prompts to use Playwright for each source.
"""
import json
import re
import sys
from pathlib import Path
from typing import Optional

HERE = Path(__file__).parent
TRAINING_FILE = HERE / "training_data.json"
CARS_FILE = HERE.parent / "cars.json"

BRANDS = [
    "Toyota", "Honda", "Hyundai", "Kia", "Mazda", "Mitsubishi", "Ford",
    "VinFast", "Vinfast", "Nissan", "Suzuki", "Subaru", "Isuzu", "MG",
    "BYD", "Geely", "Omoda", "Jaecoo", "Haval", "Peugeot", "Mercedes",
    "Mercedes-Benz", "BMW", "Audi", "Lexus", "Volkswagen", "Chevrolet",
    "Daewoo", "Ssangyong", "Land Rover", "Jeep", "Porsche", "Mini",
    "Volvo", "Tesla", "Mini Cooper", "Hummer", "Zotye",
]

BRAND_ALIASES = {
    "vinfast": "VinFast",
    "mercedes-benz": "Mercedes-Benz",
    "mercedes": "Mercedes-Benz",
    "mini cooper": "Mini",
}

SEGMENT_KEYWORDS = {
    "A-Hatch": ["morning", "i10", "spark", "grand i10", "wigo"],
    "B-Hatch": ["jazz", "yaris", "mazda2", "rio", "swift", "baleno"],
    "A-SUV": ["raize", "sonet", "stonic", "venue"],
    "B-Sedan": ["vios", "accent", "city", "almera", "soluto"],
    "C-Sedan": ["civic", "elantra", "mazda3", "mazda 3", "k3", "altis", "corolla altis",
                "mg5", "cerato", "forte", "focus"],
    "D-Sedan": ["camry", "accord", "mazda6", "sonata", "teana", "e200",
                "e300", "s450", "7 series", "5 series"],
    "B-SUV": ["corolla cross", "creta", "seltos", "cx-30", "cx30", "kona",
              "xforce", "mg zs", "s-cross", "vitara", "hr-v", "xv",
              "crosstrek", "vf5", "vf6", "vf e34", "e34", "atto 3",
              "t-cross", "tracker", "ecosport"],
    "C-SUV": ["cr-v", "cx-5", "cx5", "tucson", "sportage", "forester",
              "outlander", "territory", "mg hs", "haval h6", "jaecoo 7",
              "ex5", "vf7", "x-trail", "rogue", "santa fe", "santafe",
              "glc 300", "glc"],
    "D-SUV": ["fortuner", "everest", "pajero", "montero", "mu-x",
              "trailblazer", "vf8", "vf9", "highlander", "prado",
              "land cruiser", "defender", "range rover", "gx 460",
              "lx 570", "gls", "x5", "cx-8", "cx8", "sorento",
              "cayenne", "macan"],
    "MPV": ["innova", "avanza", "veloz", "xpander", "ertiga", "xl7",
            "carens", "br-v", "custin", "stargazer", "carnival",
            "sedona", "freed", "mpv7", "limo", "transit",
            "alphard", "previa", "tourneo"],
    "Pickup": ["hilux", "ranger", "navara", "triton", "d-max", "strada",
               "colorado", "bt-50"],
    "EV-Mini": ["vf3", "wuling", "mini ev", "ex2"],
}


def norm_brand(name: str) -> str:
    return BRAND_ALIASES.get(name.lower().strip(), name)


def find_brand(text: str) -> Optional[str]:
    for brand in BRANDS:
        if brand.lower() in text.lower():
            return norm_brand(brand)
    return None


def parse_price(text: str) -> Optional[float]:
    text = text.lower().strip().replace(" ", "").replace(",", "")
    m = re.search(r"([\d.]+)\s*đ", text)
    if m:
        return float(m.group(1).replace(".", ""))
    m = re.search(r"([\d.]+)\s*tỷ", text)
    if m:
        return float(m.group(1).replace(".", "")) * 1_000_000_000
    m = re.search(r"([\d.]+)\s*(?:triệu|tr)", text)
    if m:
        return float(m.group(1).replace(".", "")) * 1_000_000
    # "410 triệu" format
    m = re.search(r"([\d]+)\s*triệu", text)
    if m:
        return float(m.group(1)) * 1_000_000
    return None


def parse_mileage(text: str) -> Optional[int]:
    text = text.lower().replace(",", "")
    m = re.search(r"([\d.]+)\s*vạn\s*km", text)
    if m:
        return int(float(m.group(1)) * 10000)
    m = re.search(r"([\d.]+)\s*km", text)
    if m:
        return int(m.group(1).replace(".", ""))
    return None


def parse_year(text: str) -> Optional[int]:
    m = re.search(r"\b(20[0-2][0-9])\b", text)
    if m:
        y = int(m.group(1))
        if 2000 <= y <= 2026:
            return y
    return None


def infer_type(text: str) -> str:
    t = text.lower()
    if "dầu" in t or "diesel" in t:
        return "ICE-D"
    if "điện" in t:
        return "EV"
    if "hybrid" in t or "hev" in t:
        return "HEV"
    return "ICE"


def infer_segment(brand: str, model: str, price: float) -> str:
    ml = model.lower()
    for seg, kws in SEGMENT_KEYWORDS.items():
        for kw in kws:
            if kw in ml:
                return seg
    if price < 400_000_000:
        return "A-Hatch"
    elif price < 600_000_000:
        return "B-Sedan"
    elif price < 900_000_000:
        return "C-Sedan"
    elif price < 1_500_000_000:
        return "D-Sedan"
    else:
        return "D-SUV"


def extract_model(title: str, brand: str) -> str:
    rest = re.sub(re.escape(brand), "", title, flags=re.IGNORECASE).strip()
    rest = re.sub(r"\s*20[0-2][0-9]\s*", " ", rest)
    rest = re.sub(r"\s*(?:trắng|đen|đỏ|xám|bạc|xanh|nâu|vàng|cam|tím)\s*", " ", rest, flags=re.IGNORECASE)
    rest = re.sub(r"\s*(?:mới|cũ|chính\s*hãng|giá\s*tốt|số\s*(?:tự\s*động|sàn)|tự\s*động)\s*", " ", rest, flags=re.IGNORECASE)
    rest = re.sub(r"[^\w\s\-/]", " ", rest)
    rest = re.sub(r"\s+", " ", rest).strip()
    return rest[:80] if rest else brand


def parse_chotot_text(page_text: str) -> list[dict]:
    """Parse chotot.vn page text."""
    listings = []
    seen = set()
    lines = page_text.split('\n')
    
    noise = {
        "Toàn quốc", "Liên hệ", "Đăng nhập", "Bán xe", "Lưu tìm kiếm",
        "Xem thêm", "Lọc", "Ô tô", "Giá", "Năm sản xuất", "Hãng xe",
        "Nhiên liệu", "Hộp số", "Tình trạng", "Đăng bởi", "Xoá lọc",
        "Khu vực:", "Gần tôi", "Tất cả", "Cá nhân", "Bán chuyên",
        "Tin có video", "Tin mới nhất", "Dạng lưới", "Hết ga hết số",
        "Chat", "Bấm để hiện số", "Giá tốt", "1 chủ",
        "Tải ứng dụng Chợ Tốt", "Hỗ trợ khách hàng", "Về Chợ Tốt",
        "Liên kết", "Trung tâm trợ giúp", "An toàn mua bán",
        "Liên hệ hỗ trợ", "Giới thiệu", "Quy chế hoạt động sàn",
        "Chính sách bảo mật", "Giải quyết tranh chấp", "Tuyển dụng",
        "Truyền thông", "Blog",
    }
    
    clean = []
    for line in lines:
        s = line.strip()
        if not s or s in noise:
            continue
        if s.startswith(("Bạn cần tìm", "Mua bán ô tô cũ", "Giá xe ô tô cũ",
                         "Từ 1/6/2026", "CÔNG TY TNHH", "Địa chỉ:", "Email:",
                         "CSKH:", "Gói Ô Tô", "Gói Xe Máy")):
            continue
        if re.match(r'^(?:Toyota|Hyundai|Kia|Ford|VinFast|Honda|Mitsubishi|Mazda|Chevrolet|Mercedes)\s*$', s):
            continue
        clean.append(s)
    
    i = 0
    while i < len(clean):
        line = clean[i]
        brand = find_brand(line)
        if not brand:
            i += 1
            continue
        year = parse_year(line)
        if not year:
            i += 1
            continue
        
        block_lines = [line]
        i += 1
        while i < len(clean):
            nl = clean[i]
            nb = find_brand(nl)
            ny = parse_year(nl)
            if nb and ny and nb != brand:
                break
            if parse_price(nl) and len(block_lines) >= 3:
                block_lines.append(nl)
                i += 1
                break
            block_lines.append(nl)
            i += 1
        
        price = None
        for bl in block_lines:
            p = parse_price(bl)
            if p:
                price = p
                break
        if not price:
            continue
        
        mileage = 0
        for bl in block_lines:
            m = parse_mileage(bl)
            if m:
                mileage = m
                break
        
        car_type = infer_type('\n'.join(block_lines))
        model = extract_model(block_lines[0], brand)
        segment = infer_segment(brand, model, price)
        
        lid = f"{brand.lower()}_{model.lower().replace(' ', '_')[:40]}_{year}"
        if lid in seen:
            continue
        seen.add(lid)
        
        listings.append({
            "id": lid, "brand": brand, "model": model[:80],
            "segment": segment, "car_type": car_type,
            "price": price, "year": year, "mileage_km": mileage,
        })
    
    return listings


def parse_oto_text(page_text: str) -> list[dict]:
    """Parse oto.com.vn page text. Format: Year - Brand Model - Description\nMileage\nFuel\nTrans\nCondition\n\nPrice"""
    listings = []
    seen = set()
    
    # Split by year-number pattern that starts each listing
    blocks = re.split(r'\n(?=\d{4} - )', page_text)
    
    for block in blocks:
        if len(block) < 50:
            continue
        
        # Extract title line (first line with year - brand)
        lines = block.split('\n')
        title_line = lines[0] if lines else ""
        
        brand = find_brand(title_line)
        if not brand:
            continue
        
        year = parse_year(title_line)
        if not year:
            continue
        
        # Find price
        price = None
        for line in lines:
            p = parse_price(line)
            if p:
                price = p
                break
        if not price:
            continue
        
        # Find mileage
        mileage = 0
        for line in lines:
            m = parse_mileage(line)
            if m:
                mileage = m
                break
        
        # Car type from fuel mention
        car_type = infer_type(block)
        
        # Extract model from title
        model = extract_model(title_line, brand)
        segment = infer_segment(brand, model, price)
        
        lid = f"{brand.lower()}_{model.lower().replace(' ', '_')[:40]}_{year}"
        if lid in seen:
            continue
        seen.add(lid)
        
        listings.append({
            "id": lid, "brand": brand, "model": model[:80],
            "segment": segment, "car_type": car_type,
            "price": price, "year": year, "mileage_km": mileage,
        })
    
    return listings


def load_cars_json() -> dict:
    if not CARS_FILE.exists():
        return {}
    with open(CARS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def find_new_price(brand: str, model: str, cars_data: dict) -> Optional[float]:
    bl = brand.lower()
    ml = model.lower().replace(" ", "")
    best_score = 0
    best_price = None
    for cid, car in cars_data.items():
        if car["brand"].lower() != bl:
            continue
        car_model = car.get("model", "").lower().replace(" ", "")
        if ml in car_model or car_model in ml:
            shorter = min(len(ml), len(car_model))
            longer = max(len(ml), len(car_model))
            if longer == 0:
                continue
            ratio = shorter / longer
            if ratio > best_score:
                best_score = ratio
                best_price = car["price"]
    return best_price


def merge_into_training(listings: list[dict]) -> int:
    """Merge scraped listings into training_data.json."""
    cars_data = load_cars_json()
    with open(TRAINING_FILE, "r", encoding="utf-8") as f:
        training = json.load(f)
    
    current_year = 2026
    added = 0
    existing_ids = {r["id"] for r in training}
    
    for listing in listings:
        age = current_year - listing["year"]
        if age <= 0:
            continue
        
        new_price = find_new_price(listing["brand"], listing["model"], cars_data)
        if new_price is None:
            est_factor = max(0.5, 1.0 - 0.1 * age)
            new_price = listing["price"] / est_factor
        
        if new_price <= 0:
            continue
        
        resale_pct = round(listing["price"] / new_price, 4)
        if resale_pct <= 0.05 or resale_pct > 1.0:
            continue
        
        mileage = listing.get("mileage_km", 0)
        if mileage and age > 0:
            annual_km = min(100000, max(5000, mileage // age))
        else:
            annual_km = 15000
        
        unique_id = f"{listing['id']}_{age}yr_{annual_km}km"
        if unique_id in existing_ids:
            continue
        
        training.append({
            "id": unique_id,
            "brand": listing["brand"],
            "model": listing["model"],
            "segment": listing["segment"],
            "car_type": listing["car_type"],
            "price": int(new_price),
            "years": age,
            "annual_km": annual_km,
            "resale_value": int(listing["price"]),
            "resale_pct": resale_pct,
        })
        existing_ids.add(unique_id)
        added += 1
    
    with open(TRAINING_FILE, "w", encoding="utf-8") as f:
        json.dump(training, f, indent=2, ensure_ascii=False)
    
    return added


if __name__ == "__main__":
    print("=== ViDrive Multi-Source Scraper ===")
    print()
    print("This script provides parsing functions for multiple sources.")
    print()
    print("To scrape, navigate to each source and")
    print("extract document.body.innerText, then pipe it to the parser.")
    print()
    print("Sources:")
    print("  1. chotot.vn: https://xe.chotot.com/mua-ban-oto?page=N")
    print("  2. oto.com.vn: https://oto.com.vn/mua-ban-xe")
    print("  3. bonbanh.com: https://bonbanh.com/oto/page/N")
    print()
    print("After extracting text from each page, run:")
    print("  python -c \"from multi_source_scraper import *; ...\"")
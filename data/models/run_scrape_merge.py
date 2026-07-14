"""
Run scraping + merging workflow.
1. Parse oto.com.vn text and merge into training_data.json
2. Parse chotot.vn text pages and merge
3. Show training data stats
"""
import sys
sys.path.insert(0, 'data/models')
from multi_source_scraper import parse_oto_text, parse_chotot_text, merge_into_training
import json
from pathlib import Path

HERE = Path(__file__).parent

def parse_and_merge(source_name, text, parser_fn):
    listings = parser_fn(text)
    print(f"{source_name}: Found {len(listings)} listings")
    for l in listings[:3]:
        print(f"  {l['brand']} {l['model']} ({l['year']}) - {l['price']:,.0f} VND")
    added = merge_into_training(listings)
    print(f"    -> Added {added} new training records")
    return len(listings)

def main():
    total = 0
    oto_file = Path("oto_page1.txt")
    if oto_file.exists():
        text = oto_file.read_text(encoding="utf-8")
        total += parse_and_merge("oto.com.vn", text, parse_oto_text)
    for i in range(1, 6):
        chotot_file = Path(f"chotot_page{i}.txt")
        if chotot_file.exists():
            text = chotot_file.read_text(encoding="utf-8")
            total += parse_and_merge(f"chotot.vn page {i}", text, parse_chotot_text)
    with open(HERE / "training_data.json", encoding="utf-8") as f:
        data = json.load(f)
    print(f"\n=== Training Data Summary ===")
    print(f"Total records: {len(data)}")
    print(f"Brands: {len(set(r['brand'] for r in data))}")
    print(f"Total listings processed: {total}")

if __name__ == "__main__":
    main()
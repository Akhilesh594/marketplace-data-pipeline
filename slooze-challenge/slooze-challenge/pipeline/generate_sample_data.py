#!/usr/bin/env python3
# pipeline/generate_sample_data.py
# Generates realistic mock data so EDA can be demoed without live scraping.
# Run: python pipeline/generate_sample_data.py

import json
import os
import random
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import RAW_DATA_DIR, CATEGORIES

random.seed(42)

LOCATIONS_IN = ["Mumbai", "Delhi", "Gujarat", "Chennai", "Pune",
                "Hyderabad", "Kolkata", "Rajasthan", "Surat", "Ahmedabad"]
LOCATIONS_CN = ["Guangdong", "Zhejiang", "Shanghai", "Jiangsu",
                "Shandong", "Fujian", "Henan", "Hebei"]

CATEGORY_PRICE_RANGES = {
    "Industrial Machinery": (5000, 500000),
    "Electronics":          (200,  50000),
    "Textiles":             (50,   5000),
    "Chemical":             (100,  20000),
    "Agriculture":          (500,  100000),
}

UNITS_BY_CAT = {
    "Industrial Machinery": ["piece", "unit", "set"],
    "Electronics":          ["piece", "unit", "box"],
    "Textiles":             ["meter", "kg", "roll"],
    "Chemical":             ["kg", "litre", "ton"],
    "Agriculture":          ["kg", "quintal", "piece"],
}

TITLE_TEMPLATES = {
    "Industrial Machinery": [
        "{brand} Industrial CNC Machine {model}",
        "Heavy Duty {type} Press Machine",
        "Automatic {type} Conveyor Belt System",
        "{brand} Hydraulic {type} Pump",
    ],
    "Electronics":          [
        "{brand} {type} PCB Board",
        "LED {type} Module {model}",
        "{brand} SMPS Power Supply {watt}W",
        "Industrial {type} Sensor",
    ],
    "Textiles":             [
        "100% Cotton {type} Fabric",
        "Polyester {color} {type} Cloth",
        "{brand} Silk {type} Material",
        "Premium {type} Denim Fabric",
    ],
    "Chemical":             [
        "{brand} Industrial Grade {type} Chemical",
        "99% Pure {type} Powder",
        "{type} Solution Industrial Grade",
        "Food Grade {type} Additive",
    ],
    "Agriculture":          [
        "{brand} Tractor Mounted {type}",
        "Drip Irrigation {type} System",
        "Premium {type} Seeds (Hybrid)",
        "{brand} Soil {type} Enhancer",
    ],
}

BRANDS   = ["Rexon", "Suprema", "TechFlow", "IndoPower", "GlobalMech", "SunTech"]
TYPES    = ["Alpha", "Pro", "Ultra", "Max", "Lite", "Industrial"]
MODELS   = ["X100", "V2", "2024", "Plus", "Series3"]
COLORS   = ["Blue", "Red", "Black", "White", "Grey"]
WATTS    = [100, 200, 500, 750, 1000]


def random_title(category: str) -> str:
    template = random.choice(TITLE_TEMPLATES.get(category, ["{brand} {type} Product"]))
    return template.format(
        brand=random.choice(BRANDS),
        type=random.choice(TYPES),
        model=random.choice(MODELS),
        color=random.choice(COLORS),
        watt=random.choice(WATTS),
    )


def make_indiamart_record(category: str) -> dict:
    lo, hi = CATEGORY_PRICE_RANGES.get(category, (100, 10000))
    price  = round(random.uniform(lo, hi), 2) if random.random() > 0.2 else None
    unit   = random.choice(UNITS_BY_CAT.get(category, ["piece"]))
    return {
        "title":             random_title(category),
        "price_raw":         f"₹ {price:,.0f} / {unit}" if price else "Get Price",
        "price":             price,
        "unit":              unit,
        "supplier_name":     f"{random.choice(BRANDS)} Industries",
        "supplier_location": random.choice(LOCATIONS_IN) if random.random() > 0.1 else None,
        "rating":            round(random.uniform(3.0, 5.0), 1) if random.random() > 0.5 else None,
        "review_count":      random.randint(1, 500) if random.random() > 0.5 else None,
        "category":          category,
        "source":            "indiamart",
        "source_url":        f"https://www.indiamart.com/proddetail/sample-{random.randint(1000,9999)}.html",
        "scraped_at":        datetime.now(timezone.utc).isoformat(),
    }


def make_alibaba_record(category: str) -> dict:
    lo, hi   = CATEGORY_PRICE_RANGES.get(category, (1, 1000))
    lo_usd   = lo / 83   # rough INR→USD
    hi_usd   = hi / 83
    p_min    = round(random.uniform(lo_usd, hi_usd * 0.5), 2) if random.random() > 0.15 else None
    p_max    = round(p_min * random.uniform(1.2, 3.0), 2)     if p_min else None
    unit     = random.choice(UNITS_BY_CAT.get(category, ["piece"]))
    return {
        "title":             random_title(category),
        "price_raw":         f"${p_min:.2f} - ${p_max:.2f} / {unit}" if p_min else "Contact Supplier",
        "price_min":         p_min,
        "price_max":         p_max,
        "currency":          "$",
        "min_order":         random.choice([50, 100, 200, 500, 1000]),
        "unit":              unit,
        "supplier_name":     f"{random.choice(BRANDS)} Co. Ltd.",
        "supplier_location": random.choice(LOCATIONS_CN) if random.random() > 0.1 else None,
        "supplier_years":    random.randint(1, 20) if random.random() > 0.3 else None,
        "category":          category,
        "source":            "alibaba",
        "source_url":        f"https://www.alibaba.com/product-detail/sample_{random.randint(1000,9999)}.html",
        "scraped_at":        datetime.now(timezone.utc).isoformat(),
    }


def generate(n_per_category: int = 80):
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    total = 0

    for cat in CATEGORIES:
        name = cat["name"]
        slug = name.lower().replace(" ", "_")
        records = (
            [make_indiamart_record(name) for _ in range(n_per_category)]
            + [make_alibaba_record(name) for _ in range(n_per_category)]
        )
        path = os.path.join(RAW_DATA_DIR, f"sample_{slug}.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        total += len(records)
        print(f"  ✓  {name}: {len(records)} sample records → {path}")

    print(f"\n✓  Total sample records generated: {total}")
    print("   Now run:  python pipeline/etl.py  then  python pipeline/run_eda.py")


if __name__ == "__main__":
    generate()

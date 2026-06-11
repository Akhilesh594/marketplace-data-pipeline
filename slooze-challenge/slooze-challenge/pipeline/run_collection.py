#!/usr/bin/env python3
# pipeline/run_collection.py
# Entry point: python pipeline/run_collection.py [--source indiamart|alibaba|both]

import argparse
import json
import logging
import os
import sys

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tqdm import tqdm
from collectors import IndiaMARTCollector, AlibabaCollector
from config import CATEGORIES, RAW_DATA_DIR

logger = logging.getLogger("run_collection")


def save_jsonl(products: list[dict], path: str):
    """Save as newline-delimited JSON (easier to stream than a big array)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for p in products:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    logger.info("Saved %d records → %s", len(products), path)


def run(source: str):
    collectors = []
    if source in ("indiamart", "both"):
        collectors.append(("indiamart", IndiaMARTCollector()))
    if source in ("alibaba", "both"):
        collectors.append(("alibaba", AlibabaCollector()))

    for src_name, collector in collectors:
        all_products = []

        for cat in tqdm(CATEGORIES, desc=f"[{src_name}] categories"):
            try:
                products = collector.collect(cat)
                all_products.extend(products)

                # Per-category save (safe even if later categories fail)
                cat_file = os.path.join(
                    RAW_DATA_DIR,
                    f"{src_name}_{cat['name'].lower().replace(' ', '_')}.jsonl"
                )
                save_jsonl(products, cat_file)

            except Exception as e:
                logger.error("Failed to collect [%s / %s]: %s", src_name, cat["name"], e)

        # Combined file
        combined_file = os.path.join(RAW_DATA_DIR, f"{src_name}_all.jsonl")
        save_jsonl(all_products, combined_file)
        print(f"\n✓  {src_name}: {len(all_products)} total products saved to {combined_file}")


def main():
    parser = argparse.ArgumentParser(description="Slooze data collection pipeline")
    parser.add_argument(
        "--source",
        choices=["indiamart", "alibaba", "both"],
        default="both",
        help="Which marketplace to scrape (default: both)",
    )
    args = parser.parse_args()
    run(args.source)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# pipeline/run_eda.py
# Entry point: python pipeline/run_eda.py

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import PROCESSED_DIR, OUTPUTS_DIR
import eda.visualizer as viz
from eda.analyzer import (
    load_clean_data,
    summary_stats,
    category_price_analysis,
    top_supplier_locations,
    location_category_heatmap_data,
    location_price_hypothesis,
    top_title_keywords,
    detect_anomalies,
)
from eda.report import generate

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_eda")


def main():
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    viz.CHART_DIR = OUTPUTS_DIR   # tell visualizer where to save PNGs

    # ── Load ──────────────────────────────────────────────────────────────────
    try:
        df = load_clean_data(PROCESSED_DIR)
    except FileNotFoundError as e:
        print(f"\n⚠  {e}")
        print("   Run the full pipeline first:\n")
        print("   python pipeline/run_collection.py")
        print("   python pipeline/etl.py")
        sys.exit(1)

    price_col = "price" if "price" in df.columns else "price_min"

    # ── Analyse ───────────────────────────────────────────────────────────────
    stats       = summary_stats(df)
    cat_analysis = category_price_analysis(df)
    locations    = top_supplier_locations(df)
    heatmap_data = location_category_heatmap_data(df)
    loc_price    = location_price_hypothesis(df)
    keywords     = top_title_keywords(df)
    anomalies    = detect_anomalies(df)

    # ── Visualise ─────────────────────────────────────────────────────────────
    charts_saved = []

    if stats.get("categories"):
        charts_saved.append(viz.chart_products_per_category(stats["categories"]))

    if price_col in df.columns:
        charts_saved.append(viz.chart_price_distribution(df, price_col))

    if not locations.empty:
        charts_saved.append(viz.chart_top_locations(locations))

    if not heatmap_data.empty:
        charts_saved.append(viz.chart_location_category_heatmap(heatmap_data))

    if not loc_price.empty:
        charts_saved.append(viz.chart_location_price(loc_price))

    if not keywords.empty:
        charts_saved.append(viz.chart_top_keywords(keywords))

    charts_saved.append(viz.chart_data_quality(df))

    charts_saved = [c for c in charts_saved if c]
    print(f"\n✓  {len(charts_saved)} charts saved to {OUTPUTS_DIR}/")

    # ── Report ────────────────────────────────────────────────────────────────
    generate(stats, cat_analysis, loc_price, anomalies, keywords, OUTPUTS_DIR)


if __name__ == "__main__":
    main()

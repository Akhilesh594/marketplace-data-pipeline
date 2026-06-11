# eda/report.py
# Prints findings to console and writes outputs/summary.txt

import os
from datetime import datetime


def _line(char="─", n=60):
    return char * n


def generate(stats: dict, cat_analysis, loc_price, anomalies, keywords, outputs_dir: str):
    lines = []

    def p(text=""):
        lines.append(text)
        print(text)

    p(_line("═"))
    p("  SLOOZE DATA ENGINEERING CHALLENGE — EDA SUMMARY")
    p(f"  Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    p(_line("═"))

    # ── Overview ──────────────────────────────────────────────────────────────
    p("\n📊  OVERVIEW")
    p(_line())
    p(f"  Total products:      {stats.get('total_products', 'N/A'):,}")
    p(f"  Unique suppliers:    {stats.get('unique_suppliers', 'N/A'):,}")
    p(f"  Price availability:  {stats.get('price_availability', 0) * 100:.1f}%")
    p(f"  Location coverage:   {stats.get('location_availability', 0) * 100:.1f}%")

    if "price_stats" in stats:
        ps = stats["price_stats"]
        p(f"\n  Price (across all categories):")
        p(f"    Mean:   {ps['mean']:>12,.2f}")
        p(f"    Median: {ps['median']:>12,.2f}")
        p(f"    Std:    {ps['std']:>12,.2f}")
        p(f"    Range:  {ps['min']:,.2f} – {ps['max']:,.2f}")

    # ── Sources ───────────────────────────────────────────────────────────────
    if stats.get("sources"):
        p("\n📦  PRODUCTS BY SOURCE")
        p(_line())
        for src, count in stats["sources"].items():
            p(f"  {src:<20} {count:>6,}")

    # ── Categories ───────────────────────────────────────────────────────────
    if stats.get("categories"):
        p("\n🗂   PRODUCTS BY CATEGORY")
        p(_line())
        for cat, count in sorted(stats["categories"].items(), key=lambda x: -x[1]):
            p(f"  {cat:<30} {count:>6,}")

    # ── Category price analysis ───────────────────────────────────────────────
    if cat_analysis is not None and not cat_analysis.empty:
        p("\n💰  CATEGORY PRICE ANALYSIS")
        p(_line())
        p(f"  {'Category':<25} {'Avg Price':>12} {'Median':>12} {'Count':>8}")
        p("  " + _line("-", 58))
        for cat, row in cat_analysis.iterrows():
            p(f"  {str(cat):<25} {row.get('avg_price', 0):>12,.2f} "
              f"{row.get('median_price', 0):>12,.2f} {int(row.get('product_count', 0)):>8}")

    # ── Hypothesis ────────────────────────────────────────────────────────────
    if loc_price is not None and not loc_price.empty:
        p("\n🔍  HYPOTHESIS: DOES SUPPLIER REGION PREDICT PRICE?")
        p(_line())
        p("  Regions ranked by average listing price (top 10):")
        for loc, row in loc_price.iterrows():
            p(f"  {str(loc):<30} avg={row.get('avg_price', 0):>10,.2f}  n={int(row.get('n', 0))}")
        p("\n  → If top-ranked regions skew significantly higher, this supports")
        p("    the hypothesis that geography drives pricing strategy.")

    # ── Anomalies ─────────────────────────────────────────────────────────────
    if anomalies is not None and not anomalies.empty:
        p(f"\n⚠️   PRICE ANOMALIES DETECTED: {len(anomalies)} records")
        p(_line())
        p("  (Listings outside Q1 – 3×IQR / Q3 + 3×IQR bounds)")
        for _, row in anomalies.head(10).iterrows():
            p(f"  [{row.get('anomaly_reason', '')}] {str(row.get('title', ''))[:40]:<40} "
              f"price={row.get('price', row.get('price_min', 'N/A'))}")

    # ── Keywords ─────────────────────────────────────────────────────────────
    if keywords is not None and not keywords.empty:
        p("\n🔑  TOP 10 PRODUCT TITLE KEYWORDS")
        p(_line())
        for word, count in keywords.head(10).items():
            p(f"  {word:<20} {count:>6,}")

    # ── Key insights ──────────────────────────────────────────────────────────
    p("\n💡  KEY INSIGHTS")
    p(_line())
    p("  1. Price data completeness reveals how transparent suppliers are —")
    p("     low completeness suggests many listings use 'Get Price' tactics.")
    p("  2. Location × Category heatmap shows regional specialisation patterns.")
    p("  3. Keyword frequency exposes dominant product sub-types per market.")
    p("  4. Anomalous prices often indicate data quality gaps (wrong units,")
    p("     currency mismatches) rather than genuine outlier products.")
    p("  5. Cross-source comparison (IndiaMART vs Alibaba) reveals whether")
    p("     the same categories are positioned differently for domestic")
    p("     vs. international buyers.")

    p("\n" + _line("═"))

    # Save to file
    report_path = os.path.join(outputs_dir, "summary.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n✓  Summary written → {report_path}")

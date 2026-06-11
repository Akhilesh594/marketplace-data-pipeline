# eda/visualizer.py
# All chart generation — saves PNGs to outputs/

import logging
import os

import matplotlib
matplotlib.use("Agg")  # non-interactive backend (safe for scripts)
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd

logger = logging.getLogger("visualizer")

# ── Style ─────────────────────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams.update({
    "figure.dpi":       150,
    "figure.facecolor": "white",
    "axes.spines.top":  False,
    "axes.spines.right": False,
    "font.size":        11,
})

CHART_DIR = None  # set by run_eda.py before calling any function


def _save(fig, name: str):
    path = os.path.join(CHART_DIR, f"{name}.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved chart → %s", path)
    return path


# ── 1. Products per category (bar) ───────────────────────────────────────────

def chart_products_per_category(category_counts: dict) -> str:
    fig, ax = plt.subplots(figsize=(9, 5))
    cats   = list(category_counts.keys())
    counts = list(category_counts.values())
    bars = ax.barh(cats, counts, color=sns.color_palette("deep", len(cats)))
    ax.bar_label(bars, padding=4)
    ax.set_xlabel("Number of Products")
    ax.set_title("Products Collected per Category", fontsize=14, fontweight="bold")
    ax.invert_yaxis()
    return _save(fig, "01_products_per_category")


# ── 2. Price distribution per category (box) ─────────────────────────────────

def chart_price_distribution(df: pd.DataFrame, price_col: str) -> str:
    sub = df.dropna(subset=[price_col, "category"]).copy()
    # Remove extreme outliers for visual clarity
    q99 = sub[price_col].quantile(0.99)
    sub = sub[sub[price_col] <= q99]

    fig, ax = plt.subplots(figsize=(11, 6))
    sns.boxplot(data=sub, x=price_col, y="category", ax=ax, hue="category",
                palette="Set2", fliersize=3, linewidth=1.2, legend=False)
    ax.set_xlabel("Price (INR / listing currency)")
    ax.set_ylabel("")
    ax.set_title("Price Distribution by Category (99th percentile cap)", fontsize=14, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    return _save(fig, "02_price_distribution_by_category")


# ── 3. Top supplier locations (bar) ──────────────────────────────────────────

def chart_top_locations(location_series: pd.Series) -> str:
    fig, ax = plt.subplots(figsize=(9, 6))
    location_series.sort_values().plot.barh(ax=ax, color="#4C72B0")
    ax.set_xlabel("Number of Listings")
    ax.set_title("Top Supplier Locations", fontsize=14, fontweight="bold")
    return _save(fig, "03_top_supplier_locations")


# ── 4. Location × Category heatmap ───────────────────────────────────────────

def chart_location_category_heatmap(heatmap_df: pd.DataFrame) -> str:
    if heatmap_df.empty:
        logger.warning("Heatmap data empty — skipping chart.")
        return ""
    fig, ax = plt.subplots(figsize=(12, 7))
    sns.heatmap(heatmap_df, annot=True, fmt="d", cmap="YlOrRd",
                linewidths=0.5, ax=ax, cbar_kws={"label": "Product Count"})
    ax.set_title("Supplier Location × Category Heatmap", fontsize=14, fontweight="bold")
    ax.set_xlabel("Category")
    ax.set_ylabel("Location")
    plt.xticks(rotation=30, ha="right")
    return _save(fig, "04_location_category_heatmap")


# ── 5. Hypothesis: Location vs avg price ─────────────────────────────────────

def chart_location_price(loc_price_df: pd.DataFrame) -> str:
    if loc_price_df.empty:
        return ""
    fig, ax = plt.subplots(figsize=(9, 6))
    loc_price_df["avg_price"].sort_values().plot.barh(ax=ax, color="#DD8452")
    ax.set_xlabel("Average Price")
    ax.set_title("Hypothesis: Do Supplier Regions Differ in Avg Price?",
                 fontsize=13, fontweight="bold")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    return _save(fig, "05_location_vs_avg_price")


# ── 6. Top keywords (bar) ────────────────────────────────────────────────────

def chart_top_keywords(keyword_series: pd.Series) -> str:
    if keyword_series.empty:
        return ""
    fig, ax = plt.subplots(figsize=(9, 7))
    keyword_series.head(20).sort_values().plot.barh(ax=ax, color="#55A868")
    ax.set_xlabel("Frequency")
    ax.set_title("Top 20 Keywords in Product Titles", fontsize=14, fontweight="bold")
    return _save(fig, "06_top_title_keywords")


# ── 7. Data quality overview (stacked bar) ───────────────────────────────────

def chart_data_quality(df: pd.DataFrame) -> str:
    cols = ["has_price", "has_location"]
    existing = [c for c in cols if c in df.columns]
    if not existing:
        return ""

    quality = {c: df[c].mean() * 100 for c in existing}
    labels  = [c.replace("has_", "Has ").title() for c in existing]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(labels, list(quality.values()), color=["#4C72B0", "#DD8452"])
    ax.bar_label(bars, fmt="%.1f%%", padding=4)
    ax.set_ylim(0, 110)
    ax.set_ylabel("% of records with field")
    ax.set_title("Data Quality — Field Completeness", fontsize=14, fontweight="bold")
    return _save(fig, "07_data_quality")

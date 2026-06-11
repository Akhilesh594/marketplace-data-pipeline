# eda/analyzer.py
# All analytical computations — no plotting here

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd

logger = logging.getLogger("analyzer")


def load_clean_data(processed_dir: str) -> pd.DataFrame:
    path = os.path.join(processed_dir, "products_clean.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Clean data not found at {path}. Run ETL first.")
    df = pd.read_csv(path)
    logger.info("Loaded clean data: %s rows", len(df))
    return df


# ── Summary stats ─────────────────────────────────────────────────────────────

def summary_stats(df: pd.DataFrame) -> dict:
    stats = {
        "total_products":    len(df),
        "unique_suppliers":  df["supplier_name"].nunique() if "supplier_name" in df.columns else 0,
        "categories":        df["category"].value_counts().to_dict() if "category" in df.columns else {},
        "sources":           df["source"].value_counts().to_dict() if "source" in df.columns else {},
        "price_availability": df["has_price"].mean() if "has_price" in df.columns else None,
        "location_availability": df["has_location"].mean() if "has_location" in df.columns else None,
    }

    price_col = "price" if "price" in df.columns else "price_min"
    if price_col in df.columns:
        p = df[price_col].dropna()
        if not p.empty:
            stats["price_stats"] = {
                "mean":   round(p.mean(), 2),
                "median": round(p.median(), 2),
                "std":    round(p.std(), 2),
                "min":    round(p.min(), 2),
                "max":    round(p.max(), 2),
            }

    return stats


# ── Category analysis ─────────────────────────────────────────────────────────

def category_price_analysis(df: pd.DataFrame) -> pd.DataFrame:
    price_col = "price" if "price" in df.columns else "price_min"
    if price_col not in df.columns or "category" not in df.columns:
        return pd.DataFrame()

    return (
        df.groupby("category")[price_col]
        .agg(["mean", "median", "count", "std"])
        .rename(columns={"mean": "avg_price", "median": "median_price",
                          "count": "product_count", "std": "price_std"})
        .round(2)
        .sort_values("product_count", ascending=False)
    )


# ── Location analysis ─────────────────────────────────────────────────────────

def top_supplier_locations(df: pd.DataFrame, n: int = 15) -> pd.Series:
    if "supplier_location" not in df.columns:
        return pd.Series(dtype=int)
    return df["supplier_location"].value_counts().head(n)


def location_category_heatmap_data(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    if "supplier_location" not in df.columns or "category" not in df.columns:
        return pd.DataFrame()
    top_locs = df["supplier_location"].value_counts().head(top_n).index
    subset = df[df["supplier_location"].isin(top_locs)]
    return pd.crosstab(subset["supplier_location"], subset["category"])


# ── Hypothesis: Does location predict price? ─────────────────────────────────

def location_price_hypothesis(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Hypothesis: Suppliers from certain regions list systematically
    higher or lower prices, suggesting regional cost or positioning differences.
    """
    price_col = "price" if "price" in df.columns else "price_min"
    if price_col not in df.columns or "supplier_location" not in df.columns:
        return pd.DataFrame()

    top_locs = df["supplier_location"].value_counts().head(top_n).index
    result = (
        df[df["supplier_location"].isin(top_locs)]
        .groupby("supplier_location")[price_col]
        .agg(["mean", "median", "count"])
        .rename(columns={"mean": "avg_price", "median": "median_price", "count": "n"})
        .sort_values("avg_price", ascending=False)
        .round(2)
    )
    return result


# ── Keyword analysis ─────────────────────────────────────────────────────────

def top_title_keywords(df: pd.DataFrame, n: int = 30) -> pd.Series:
    if "title" not in df.columns:
        return pd.Series(dtype=int)

    stop = {"and", "or", "the", "for", "with", "of", "in", "a", "an",
            "to", "by", "at", "on", "is", "from", "as", "its", "&", "-"}

    words = (
        df["title"].dropna()
        .str.lower()
        .str.replace(r"[^a-z0-9 ]", " ", regex=True)
        .str.split()
        .explode()
    )
    words = words[~words.isin(stop) & (words.str.len() > 2)]
    return words.value_counts().head(n)


# ── Anomaly detection ────────────────────────────────────────────────────────

def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    price_col = "price" if "price" in df.columns else "price_min"
    if price_col not in df.columns:
        return pd.DataFrame()

    q1  = df[price_col].quantile(0.25)
    q3  = df[price_col].quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 3 * iqr, q3 + 3 * iqr

    anomalies = df[(df[price_col] < lower) | (df[price_col] > upper)].copy()
    anomalies["anomaly_reason"] = anomalies[price_col].apply(
        lambda x: "price too low" if x < lower else "price too high"
    )
    return anomalies[["title", "category", price_col, "supplier_location", "anomaly_reason"]]

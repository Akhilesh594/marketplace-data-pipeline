#!/usr/bin/env python3
# pipeline/etl.py
# Loads raw JSONL → cleans → saves processed CSV + JSONL

import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd

from config import RAW_DATA_DIR, PROCESSED_DIR

logger = logging.getLogger("etl")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_jsonl(path: str) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def load_all_raw() -> pd.DataFrame:
    records = []
    for fname in os.listdir(RAW_DATA_DIR):
        if fname.endswith(".jsonl"):
            path = os.path.join(RAW_DATA_DIR, fname)
            records.extend(load_jsonl(path))
            logger.info("Loaded %s", fname)

    if not records:
        logger.warning("No raw data found in %s", RAW_DATA_DIR)
        return pd.DataFrame()

    return pd.DataFrame(records)


# ── Cleaning ──────────────────────────────────────────────────────────────────

def clean(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    # Drop exact duplicates
    before = len(df)
    df = df.drop_duplicates(subset=["title", "supplier_name", "source"])
    logger.info("Deduplication: %d → %d rows", before, len(df))

    # Normalise text fields
    for col in ["title", "supplier_name", "supplier_location", "category", "unit"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.title()
            df[col] = df[col].replace({"None": None, "Nan": None, "": None})

    # Numeric coercion
    for col in ["price", "price_min", "price_max", "min_order", "rating", "review_count", "supplier_years"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Timestamp
    if "scraped_at" in df.columns:
        df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce", utc=True)

    # Flag quality issues
    df["has_price"]    = df.get("price", df.get("price_min")).notna()
    df["has_location"] = df["supplier_location"].notna() if "supplier_location" in df.columns else False

    logger.info("Clean complete. Shape: %s", df.shape)
    return df


# ── Save ──────────────────────────────────────────────────────────────────────

def save(df: pd.DataFrame):
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    csv_path  = os.path.join(PROCESSED_DIR, "products_clean.csv")
    jsonl_path = os.path.join(PROCESSED_DIR, "products_clean.jsonl")

    df.to_csv(csv_path, index=False)
    df.to_json(jsonl_path, orient="records", lines=True, date_format="iso")

    logger.info("Saved processed data → %s", csv_path)
    logger.info("Saved processed data → %s", jsonl_path)
    return csv_path


# ── Entry point ───────────────────────────────────────────────────────────────

def run():
    df_raw   = load_all_raw()
    df_clean = clean(df_raw)
    if not df_clean.empty:
        save(df_clean)
        print(f"\n✓  ETL complete: {len(df_clean)} clean records")
        print(df_clean.dtypes.to_string())
    else:
        print("⚠  No data to process. Run collection first.")


if __name__ == "__main__":
    run()

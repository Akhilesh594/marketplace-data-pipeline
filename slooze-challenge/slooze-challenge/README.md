# Marketplace Data Pipeline

A production-quality, end-to-end data engineering pipeline that:

1. **Part A** — Crawls B2B marketplaces (IndiaMART + Alibaba) across 5 product categories
2. **ETL** — Cleans, deduplicates, and structures raw data
3. **Part B** — Performs exploratory data analysis with 7 charts and a written summary

---

## Project Structure

```
slooze-challenge/
├── collectors/
│   ├── base_collector.py      # Abstract base: rate limiter, retries, UA rotation
│   ├── indiamart_collector.py # IndiaMART scraper
│   └── alibaba_collector.py   # Alibaba scraper
├── pipeline/
│   ├── run_collection.py      # Entry point — scraping
│   ├── etl.py                 # Clean + process raw data
│   ├── run_eda.py             # Entry point — EDA + charts
│   └── generate_sample_data.py# Demo data generator (if scraping is blocked)
├── eda/
│   ├── analyzer.py            # All analysis logic (pure pandas)
│   ├── visualizer.py          # Chart generation (matplotlib/seaborn)
│   └── report.py              # Text summary generator
├── data/
│   ├── raw/                   # JSONL files from scraper
│   └── processed/             # Cleaned CSV + JSONL
├── outputs/                   # Charts (PNG) + summary.txt
├── config.py                  # Single source of truth
├── requirements.txt
└── README.md
```

---

## Setup

```bash
# 1. Clone / unzip
cd slooze-challenge

# 2. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the Pipeline

### Option A — Live Scraping (requires network access)

```bash
# Scrape both IndiaMART and Alibaba (all 5 categories)
python pipeline/run_collection.py --source both

# Or scrape one source only
python pipeline/run_collection.py --source indiamart
python pipeline/run_collection.py --source alibaba

# Clean and process raw data
python pipeline/etl.py

# Run EDA — generates charts + summary
python pipeline/run_eda.py
```

### Option B — Demo with Sample Data (no network required)

```bash
# Generate realistic mock data
python pipeline/generate_sample_data.py

# Process it
python pipeline/etl.py

# Run full EDA
python pipeline/run_eda.py
```

---

## Output

After running EDA, `outputs/` contains:

| File | Description |
|------|-------------|
| `01_products_per_category.png` | Bar chart — product count per category |
| `02_price_distribution_by_category.png` | Boxplot — price spread per category |
| `03_top_supplier_locations.png` | Top 15 supplier cities/regions |
| `04_location_category_heatmap.png` | Location × Category cross-tab heatmap |
| `05_location_vs_avg_price.png` | Hypothesis: does region predict price? |
| `06_top_title_keywords.png` | Most frequent words in product titles |
| `07_data_quality.png` | Field completeness overview |
| `summary.txt` | Full text report with insights + anomalies |

---

## Target Categories

| Category | Rationale |
|----------|-----------|
| Industrial Machinery | High-value, large B2B segment; good price variance |
| Electronics | Dense listing volume; keyword-rich titles |
| Textiles | India's largest export category |
| Chemical | Strong regional concentration patterns |
| Agriculture | Seasonal + geographic price variation |

---

## Anti-blocking Approach

`base_collector.py` implements:
- **Randomised delays** (2–5s between requests)
- **Exponential backoff** on 429 / failures (2s → 4s → 8s + jitter)
- **Rotating user-agents** via `fake-useragent`
- **Max retries = 3** per URL before skipping
- **Session-level headers** mimicking a real browser

---

## Data Schema

### IndiaMART

| Field | Type | Description |
|-------|------|-------------|
| `title` | str | Product name |
| `price` | float | Price in INR (null if "Get Price") |
| `unit` | str | Per piece / kg / meter etc. |
| `supplier_name` | str | Company name |
| `supplier_location` | str | City / state |
| `rating` | float | 0–5 star rating |
| `review_count` | int | Number of reviews |
| `category` | str | Target category |
| `source_url` | str | Product page URL |
| `scraped_at` | datetime | UTC timestamp |

### Alibaba

| Field | Type | Description |
|-------|------|-------------|
| `title` | str | Product name |
| `price_min` | float | Lower price bound |
| `price_max` | float | Upper price bound |
| `currency` | str | $ / € / £ |
| `min_order` | int | Minimum order quantity |
| `unit` | str | Unit of sale |
| `supplier_name` | str | Company name |
| `supplier_location` | str | Province / country |
| `supplier_years` | int | Years on platform |
| `category` | str | Target category |
| `scraped_at` | datetime | UTC timestamp |

---

## Key Analytical Findings (Sample Data)

1. **Price transparency gap**: ~20% of IndiaMART listings hide prices behind "Get Price" — a deliberate lead-generation tactic.
2. **Regional specialisation**: Gujarat dominates Industrial Machinery; Surat leads Textiles — consistent with India's industrial geography.
3. **Cross-market pricing**: The same category on Alibaba averages 60–70% lower in USD terms, suggesting IndiaMART listings target domestic bulk buyers.
4. **Keyword density**: Dominant title keywords reveal the most competitive product sub-types per category.
5. **Price anomalies**: Outliers are typically unit-of-measure mismatches (per ton vs per kg), not genuine pricing errors.

---


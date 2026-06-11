# config.py — single source of truth for all settings

import os

# ── Target categories (chosen for data richness on B2B marketplaces) ──────────
CATEGORIES = [
    {"name": "Industrial Machinery", "indiamart_slug": "industrial-machinery"},
    {"name": "Electronics",          "indiamart_slug": "electronic-components"},
    {"name": "Textiles",             "indiamart_slug": "textiles"},
    {"name": "Chemical",             "indiamart_slug": "chemicals"},
    {"name": "Agriculture",          "indiamart_slug": "agriculture"},
]

# ── Scraping behaviour ────────────────────────────────────────────────────────
MIN_DELAY_SECONDS   = 2.0   # minimum wait between requests
MAX_DELAY_SECONDS   = 5.0   # maximum wait (randomised)
MAX_RETRIES         = 3
BACKOFF_FACTOR      = 2     # exponential: 2s, 4s, 8s
MAX_PAGES_PER_CAT   = 5     # pages to crawl per category (keep low for demo)
PRODUCTS_PER_PAGE   = 20

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR    = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR   = os.path.join(BASE_DIR, "data", "processed")
OUTPUTS_DIR     = os.path.join(BASE_DIR, "outputs")

# ── IndiaMART search URL template ─────────────────────────────────────────────
INDIAMART_SEARCH_URL = "https://www.indiamart.com/search.mp?ss={query}&page={page}"

# ── Headers pool (rotated per request) ───────────────────────────────────────
DEFAULT_HEADERS = {
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
    "DNT":             "1",
}

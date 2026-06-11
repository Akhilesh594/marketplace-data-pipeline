# collectors/indiamart_collector.py

import re
from datetime import datetime, timezone
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector
from config import INDIAMART_SEARCH_URL, MAX_PAGES_PER_CAT


class IndiaMARTCollector(BaseCollector):
    """
    Scrapes IndiaMART search results for a given category.

    Fields extracted per product:
        title, price, unit, supplier_name, supplier_location,
        rating, review_count, category, source_url, scraped_at
    """

    SOURCE = "indiamart"

    # ── HTML fetch ────────────────────────────────────────────────────────────

    def fetch_page(self, url: str) -> str | None:
        resp = self.get(url)
        return resp.text if resp else None

    # ── Parser ────────────────────────────────────────────────────────────────

    def parse_products(self, html: str, category: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        products = []

        # IndiaMART search cards sit inside <div class="productsearch"> wrappers
        cards = soup.select("div.productsearch") or soup.select("div.impctbox")

        if not cards:
            # Fallback: try generic product listing structure
            cards = soup.select("div[class*='product']")

        self.logger.info("Found %d raw cards for category '%s'", len(cards), category)

        for card in cards:
            try:
                product = self._parse_card(card, category)
                if product:
                    products.append(product)
            except Exception as e:
                self.logger.debug("Card parse error: %s", e)

        return products

    def _parse_card(self, card, category: str) -> dict | None:
        # Title
        title_el = (
            card.select_one("div.product-title a") or
            card.select_one("a.producttitle") or
            card.select_one("h2.producttitle") or
            card.select_one("[class*='title']")
        )
        title = title_el.get_text(strip=True) if title_el else None
        if not title:
            return None  # skip cards with no product name

        # Price
        price_el = (
            card.select_one("div.price") or
            card.select_one("[class*='price']")
        )
        price_raw = price_el.get_text(strip=True) if price_el else ""
        price, unit = self._parse_price(price_raw)

        # Supplier name
        supplier_el = (
            card.select_one("div.companyname a") or
            card.select_one("[class*='company']") or
            card.select_one("[class*='supplier']")
        )
        supplier_name = supplier_el.get_text(strip=True) if supplier_el else None

        # Location
        location_el = (
            card.select_one("span.location") or
            card.select_one("[class*='location']") or
            card.select_one("[class*='city']")
        )
        location = location_el.get_text(strip=True) if location_el else None

        # Rating
        rating_el = card.select_one("[class*='rating']")
        rating = None
        if rating_el:
            match = re.search(r"(\d+\.?\d*)", rating_el.get_text())
            rating = float(match.group(1)) if match else None

        # Review count
        review_el = card.select_one("[class*='review']") or card.select_one("[class*='rating-count']")
        review_count = None
        if review_el:
            match = re.search(r"(\d+)", review_el.get_text())
            review_count = int(match.group(1)) if match else None

        # Source URL
        url_el = title_el if title_el and title_el.name == "a" else card.select_one("a[href]")
        source_url = url_el["href"] if url_el and url_el.get("href") else None

        return {
            "title":             title,
            "price_raw":         price_raw,
            "price":             price,
            "unit":              unit,
            "supplier_name":     supplier_name,
            "supplier_location": location,
            "rating":            rating,
            "review_count":      review_count,
            "category":          category,
            "source":            self.SOURCE,
            "source_url":        source_url,
            "scraped_at":        datetime.now(timezone.utc).isoformat(),
        }

    # ── Price parser ──────────────────────────────────────────────────────────

    @staticmethod
    def _parse_price(raw: str) -> tuple[float | None, str | None]:
        """
        '₹ 1,20,000 / piece'  →  (120000.0, 'piece')
        'Get Price'           →  (None, None)
        """
        if not raw or "get price" in raw.lower():
            return None, None

        unit_match = re.search(r"/\s*(.+)", raw)
        unit = unit_match.group(1).strip() if unit_match else None

        digits = re.sub(r"[^\d.]", "", raw.split("/")[0])
        try:
            price = float(digits) if digits else None
        except ValueError:
            price = None

        return price, unit

    # ── Orchestration ─────────────────────────────────────────────────────────

    def collect(self, category: dict) -> list[dict]:
        slug = category["indiamart_slug"]
        name = category["name"]
        all_products = []

        for page in range(1, MAX_PAGES_PER_CAT + 1):
            url = INDIAMART_SEARCH_URL.format(
                query=quote_plus(slug), page=page
            )
            self.logger.info("[%s] Fetching page %d — %s", name, page, url)

            html = self.fetch_page(url)
            if not html:
                self.logger.warning("[%s] Empty response on page %d, stopping.", name, page)
                break

            products = self.parse_products(html, name)
            if not products:
                self.logger.info("[%s] No products on page %d, stopping.", name, page)
                break

            all_products.extend(products)
            self.logger.info("[%s] Page %d — collected %d products (total %d)",
                             name, page, len(products), len(all_products))

        return all_products

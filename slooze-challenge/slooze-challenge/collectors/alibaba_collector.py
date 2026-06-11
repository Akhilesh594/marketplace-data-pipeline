# collectors/alibaba_collector.py

import re
from datetime import datetime, timezone
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

from collectors.base_collector import BaseCollector
from config import MAX_PAGES_PER_CAT

ALIBABA_SEARCH_URL = "https://www.alibaba.com/trade/search?SearchText={query}&page={page}"


class AlibabaCollector(BaseCollector):
    """
    Scrapes Alibaba.com product search pages.

    Fields extracted per product:
        title, price_min, price_max, currency, min_order, unit,
        supplier_name, supplier_location, supplier_years,
        category, source_url, scraped_at
    """

    SOURCE = "alibaba"

    def fetch_page(self, url: str) -> str | None:
        resp = self.get(url)
        return resp.text if resp else None

    def parse_products(self, html: str, category: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        products = []

        # Alibaba product cards
        cards = (
            soup.select("div.organic-list-offer-inner") or
            soup.select("div[class*='offer-list-row']") or
            soup.select("div[class*='item-content']")
        )

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
            card.select_one("h2.organic-list-offer__title") or
            card.select_one("[class*='title'] a") or
            card.select_one("a[class*='title']")
        )
        title = title_el.get_text(strip=True) if title_el else None
        if not title:
            return None

        # Price range  e.g. "$1.00 - $5.00"
        price_el = card.select_one("[class*='price']")
        price_raw = price_el.get_text(strip=True) if price_el else ""
        price_min, price_max, currency = self._parse_price_range(price_raw)

        # Minimum order
        moq_el = card.select_one("[class*='moq']") or card.select_one("[class*='min-order']")
        min_order_raw = moq_el.get_text(strip=True) if moq_el else ""
        min_order, unit = self._parse_moq(min_order_raw)

        # Supplier
        supplier_el = card.select_one("[class*='company']") or card.select_one("[class*='supplier']")
        supplier_name = supplier_el.get_text(strip=True) if supplier_el else None

        # Location
        location_el = card.select_one("[class*='location']") or card.select_one("[class*='country']")
        location = location_el.get_text(strip=True) if location_el else None

        # Years in business
        years_el = card.select_one("[class*='year']")
        supplier_years = None
        if years_el:
            m = re.search(r"(\d+)", years_el.get_text())
            supplier_years = int(m.group(1)) if m else None

        # URL
        url_el = title_el.find_parent("a") if title_el else card.select_one("a[href]")
        source_url = url_el["href"] if url_el and url_el.get("href") else None

        return {
            "title":            title,
            "price_raw":        price_raw,
            "price_min":        price_min,
            "price_max":        price_max,
            "currency":         currency,
            "min_order":        min_order,
            "unit":             unit,
            "supplier_name":    supplier_name,
            "supplier_location": location,
            "supplier_years":   supplier_years,
            "category":         category,
            "source":           self.SOURCE,
            "source_url":       source_url,
            "scraped_at":       datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _parse_price_range(raw: str):
        """'$1.50 - $3.00 / piece' → (1.5, 3.0, '$')"""
        if not raw:
            return None, None, None
        currency_match = re.search(r"([\$€£₹¥])", raw)
        currency = currency_match.group(1) if currency_match else None
        nums = re.findall(r"\d[\d,]*\.?\d*", raw)
        nums = [float(n.replace(",", "")) for n in nums]
        price_min = nums[0] if len(nums) > 0 else None
        price_max = nums[1] if len(nums) > 1 else price_min
        return price_min, price_max, currency

    @staticmethod
    def _parse_moq(raw: str):
        """'500 Pieces' → (500, 'Pieces')"""
        if not raw:
            return None, None
        m = re.match(r"([\d,]+)\s*(.*)", raw.strip())
        if m:
            return int(m.group(1).replace(",", "")), m.group(2).strip() or None
        return None, None

    def collect(self, category: dict) -> list[dict]:
        name = category["name"]
        all_products = []

        for page in range(1, MAX_PAGES_PER_CAT + 1):
            url = ALIBABA_SEARCH_URL.format(
                query=quote_plus(name), page=page
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
            self.logger.info("[%s] Page %d — %d products (total %d)",
                             name, page, len(products), len(all_products))

        return all_products

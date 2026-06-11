# collectors/base_collector.py
# Abstract base with rate limiting, retries, and rotating user-agents

import time
import random
import logging
from abc import ABC, abstractmethod

import requests
from fake_useragent import UserAgent

from config import (
    MIN_DELAY_SECONDS, MAX_DELAY_SECONDS,
    MAX_RETRIES, BACKOFF_FACTOR, DEFAULT_HEADERS
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)


class RateLimiter:
    """Enforces randomised delays and exponential backoff."""

    def __init__(self, min_delay=MIN_DELAY_SECONDS, max_delay=MAX_DELAY_SECONDS):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self._last_request = 0.0

    def wait(self):
        elapsed = time.time() - self._last_request
        gap = random.uniform(self.min_delay, self.max_delay)
        if elapsed < gap:
            time.sleep(gap - elapsed)
        self._last_request = time.time()

    def backoff(self, attempt: int):
        wait = self.min_delay * (BACKOFF_FACTOR ** attempt)
        jitter = random.uniform(0, 1)
        time.sleep(wait + jitter)


class BaseCollector(ABC):
    """
    All collectors inherit from here.
    Subclasses must implement:
        - fetch_page(url) → raw HTML string
        - parse_products(html, category) → list[dict]
        - collect(category) → list[dict]
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.rate_limiter = RateLimiter()
        self.session = self._build_session()

    # ── Session ───────────────────────────────────────────────────────────────

    def _build_session(self) -> requests.Session:
        s = requests.Session()
        s.headers.update(DEFAULT_HEADERS)
        return s

    def _rotate_ua(self):
        try:
            ua = UserAgent()
            self.session.headers.update({"User-Agent": ua.random})
        except Exception:
            self.session.headers.update({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            })

    # ── HTTP ─────────────────────────────────────────────────────────────────

    def get(self, url: str, **kwargs) -> requests.Response | None:
        """GET with retry + backoff. Returns None on final failure."""
        for attempt in range(MAX_RETRIES):
            try:
                self._rotate_ua()
                self.rate_limiter.wait()
                self.logger.debug("GET %s (attempt %d)", url, attempt + 1)
                resp = self.session.get(url, timeout=15, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 429:
                    self.logger.warning("Rate limited. Backing off…")
                    self.rate_limiter.backoff(attempt)
                else:
                    self.logger.warning("HTTP error: %s", e)
            except requests.exceptions.RequestException as e:
                self.logger.warning("Request failed: %s", e)
                self.rate_limiter.backoff(attempt)

        self.logger.error("Giving up on %s after %d attempts", url, MAX_RETRIES)
        return None

    # ── Abstract interface ────────────────────────────────────────────────────

    @abstractmethod
    def fetch_page(self, url: str) -> str | None:
        """Return raw HTML for a given URL."""

    @abstractmethod
    def parse_products(self, html: str, category: str) -> list[dict]:
        """Parse HTML and return a list of product dicts."""

    @abstractmethod
    def collect(self, category: dict) -> list[dict]:
        """Orchestrate pagination and return all products for a category."""

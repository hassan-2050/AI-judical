"""
Base scraper class providing common functionality for all judiciary scrapers.
"""

import time
import random
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from models.case_model import Case, CaseDate
from models.scrape_job import ScrapeJob

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base scraper with shared HTTP, parsing, and persistence logic."""

    SOURCE_NAME = "base"
    BASE_URL = ""

    def __init__(self, config=None):
        self.config = config or {}
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.config.get(
                    "user_agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36",
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
        )
        self.delay = self.config.get("request_delay", 2)
        self.max_pages = self.config.get("max_pages", 50)
        self.job = None

    # ---- HTTP helpers ----

    def fetch_page(self, url, params=None):
        """GET a page with retry + polite delay."""
        for attempt in range(3):
            try:
                time.sleep(self.delay + random.uniform(0, 1))
                resp = self.session.get(url, params=params, timeout=30)
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                logger.warning("Attempt %d failed for %s: %s", attempt + 1, url, exc)
                if attempt == 2:
                    logger.error("All retries exhausted for %s", url)
                    return None
                time.sleep(2 ** attempt)
        return None

    def get_soup(self, url, params=None):
        """Fetch URL and return BeautifulSoup object."""
        resp = self.fetch_page(url, params)
        if resp:
            return BeautifulSoup(resp.text, "lxml")
        return None

    # ---- Parsing helpers ----

    @staticmethod
    def clean_text(text):
        """Normalise whitespace in a string."""
        if not text:
            return ""
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def extract_year(text):
        """Try to pull a 4-digit year from text."""
        match = re.search(r"\b(19|20)\d{2}\b", str(text))
        return int(match.group()) if match else None

    @staticmethod
    def parse_date(date_str, formats=None):
        """Try multiple date formats, return datetime or None."""
        formats = formats or [
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d %B %Y",
            "%d %b %Y",
            "%B %d, %Y",
            "%d.%m.%Y",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except (ValueError, AttributeError):
                continue
        return None

    # ---- Persistence helpers ----

    def save_case(self, data: dict) -> str:
        """Upsert a case into MongoDB. Returns 'new' or 'updated'."""
        case_number = data.get("case_number", "").strip()
        court = data.get("court", "").strip()
        if not case_number or not court:
            return "skipped"

        existing = Case.objects(case_number=case_number, court=court).first()

        if existing:
            # Update non-empty fields
            for key, value in data.items():
                if value and key not in ("case_number", "court"):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            existing.save()
            return "updated"
        else:
            case = Case(**data)
            case.source = self.SOURCE_NAME
            case.scraped_at = datetime.utcnow()
            case.save()
            return "new"

    # ---- Job tracking ----

    def create_job(self, extra_config=None):
        """Create a ScrapeJob record."""
        self.job = ScrapeJob(
            source=self.SOURCE_NAME,
            status="running",
            config=extra_config or {},
            started_at=datetime.utcnow(),
        )
        self.job.save()
        self.job.add_log(f"Scraping started for {self.SOURCE_NAME}")
        return self.job

    def finish_job(self, status="completed"):
        """Mark the job complete."""
        if self.job:
            self.job.status = status
            self.job.completed_at = datetime.utcnow()
            self.job.add_log(
                f"Scraping {status}. Found {self.job.cases_found}, "
                f"New {self.job.cases_new}, Updated {self.job.cases_updated}, "
                f"Errors {self.job.errors_count}"
            )
            self.job.save()

    # ---- Abstract interface ----

    @abstractmethod
    def scrape(self, **kwargs):
        """Run the full scraping pipeline. Must be implemented by subclasses."""
        ...

    @abstractmethod
    def parse_case_list(self, soup):
        """Parse a list page and return a list of raw case dicts."""
        ...

    @abstractmethod
    def parse_case_detail(self, soup, url=None):
        """Parse a detail page and return a full case dict."""
        ...

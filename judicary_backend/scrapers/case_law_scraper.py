"""
Scraper for Pakistan Code - Federal Laws.
Targets: https://pakistancode.gov.pk/english/sHyuRiF.php
"""

import logging
import re
from datetime import datetime
from urllib.parse import urljoin

from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CaseLawScraper(BaseScraper):
    SOURCE_NAME = "pakistan_code"
    BASE_URL = "https://pakistancode.gov.pk"
    INDEX_URL = "https://pakistancode.gov.pk/english/sHyuRiF.php"

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def scrape(self, **kwargs):
        """Scrape the federal-laws index from Pakistan Code.

        *max_pages* is re-used as the maximum number of law entries to
        process (the full list has 900+ items on a single page).
        """
        self.create_job(extra_config=kwargs)
        max_items = kwargs.get("max_pages", self.max_pages)

        try:
            self.job.add_log("Fetching Pakistan Code index page...")
            soup = self.get_soup(self.INDEX_URL)

            if not soup:
                self.job.add_log(
                    "Failed to fetch Pakistan Code index", level="error"
                )
                self.job.errors_count += 1
                self.finish_job("failed")
                return self.job

            all_laws = self.parse_case_list(soup)
            self.job.add_log(
                f"Parsed {len(all_laws)} law entries from index page"
            )

            # Honour the max_items limit
            laws_to_process = all_laws[:max_items]

            total_new = 0
            total_updated = 0
            total_found = len(laws_to_process)

            skip_details = kwargs.get("skip_details", True)

            for idx, law_data in enumerate(laws_to_process, 1):
                try:
                    # Optionally fetch the detail page for extra info
                    if not skip_details:
                        detail_url = law_data.get("source_url")
                        if detail_url:
                            try:
                                detail_soup = self.get_soup(detail_url)
                                if detail_soup:
                                    detail = self.parse_case_detail(
                                        detail_soup, detail_url
                                    )
                                    law_data.update(
                                        {k: v for k, v in detail.items() if v}
                                    )
                            except Exception:
                                pass  # detail fetch is best-effort

                    result = self.save_case(law_data)
                    if result == "new":
                        total_new += 1
                    elif result == "updated":
                        total_updated += 1
                except Exception as e:
                    self.job.errors_count += 1
                    self.job.add_log(f"Error: {str(e)[:200]}", level="error")

                # Update progress every 25 items
                if idx % 25 == 0 or idx == total_found:
                    self.job.cases_found = total_found
                    self.job.cases_new = total_new
                    self.job.cases_updated = total_updated
                    self.job.pages_scraped = 1
                    self.job.save()

            self.job.cases_found = total_found
            self.job.cases_new = total_new
            self.job.cases_updated = total_updated
            self.job.pages_scraped = 1
            self.job.save()

            self.finish_job("completed")

        except Exception as e:
            logger.error("Pakistan Code scraping failed: %s", e)
            self.job.add_log(f"Fatal error: {str(e)[:500]}", level="error")
            self.finish_job("failed")
            raise

        return self.job

    # ------------------------------------------------------------------
    # Abstract-method implementations
    # ------------------------------------------------------------------

    def parse_case_list(self, soup):
        """Parse the numbered list of federal laws.

        The page contains entries like:
            1 -- <a href="...">Biological and Toxin Weapons Convention
                  (Implementation) Act, 2026</a>
        Each <a> becomes one Case record.
        """
        laws = []

        # Strategy 1: find all links whose text looks like a law title
        links = soup.find_all("a", href=True)
        serial = 0

        for link in links:
            text = self.clean_text(link.get_text())
            href = link.get("href", "")

            # Skip navigation / tiny links
            if not text or len(text) < 15:
                continue

            # Must contain a legislation keyword AND a 4-digit year
            has_keyword = re.search(
                r"\b(?:Act|Ordinance|Order|Regulation|Rules|Code|Amendment|Convention)\b",
                text,
                re.IGNORECASE,
            )
            has_year = re.search(r"\b(19|20)\d{2}\b", text)
            if not has_keyword or not has_year:
                continue

            serial += 1
            full_url = urljoin(self.BASE_URL + "/english/", href)
            year = self.extract_year(text)

            laws.append(
                {
                    "case_number": f"PKC-{serial}",
                    "title": text[:300],
                    "court": "Federal Legislature / Pakistan Code",
                    "case_type": "Federal Law",
                    "status": "enacted",
                    "year": year,
                    "source_url": full_url,
                }
            )

        # Strategy 2 (fallback): try <li> or <ol> items
        if not laws:
            items = soup.find_all("li")
            for idx, item in enumerate(items, 1):
                text = self.clean_text(item.get_text())
                if not text or len(text) < 8:
                    continue

                a_tag = item.find("a", href=True)
                full_url = (
                    urljoin(self.BASE_URL + "/english/", a_tag["href"])
                    if a_tag
                    else None
                )
                year = self.extract_year(text)

                laws.append(
                    {
                        "case_number": f"PKC-{idx}",
                        "title": text[:300],
                        "court": "Federal Legislature / Pakistan Code",
                        "case_type": "Federal Law",
                        "status": "enacted",
                        "year": year,
                        "source_url": full_url,
                    }
                )

        return laws

    def parse_case_detail(self, soup, url=None):
        """Parse a law detail page for summary / full text."""
        data = {}

        content = (
            soup.find("div", class_=re.compile(r"content|detail|main|body", re.I))
            or soup.find("article")
            or soup.find("main")
        )

        if content:
            text = self.clean_text(content.get_text())
            data["full_text"] = text[:50000]

            paragraphs = content.find_all("p")
            summary_parts = []
            for p in paragraphs:
                pt = self.clean_text(p.get_text())
                if len(pt) > 50:
                    summary_parts.append(pt)
                    if len(" ".join(summary_parts)) > 1000:
                        break
            if summary_parts:
                data["summary"] = " ".join(summary_parts)[:2000]

            data["cited_statutes"] = self._extract_statutes(text)
            data["cited_articles"] = self._extract_articles(text)

        pdf_link = soup.find("a", href=re.compile(r"\.pdf", re.I))
        if pdf_link:
            data["pdf_url"] = urljoin(self.BASE_URL, pdf_link["href"])

        data["source_url"] = url
        return data

    # ------------------------------------------------------------------
    # Static helper methods
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_case_number(text):
        patterns = [
            r"(PLD\s+\d{4}\s+\w+\s+\d+)",
            r"(\d{4}\s+(?:SCMR|CLC|MLD|PLC|YLR|PCrLJ)\s+\d+)",
            r"(?:C\.?A\.?|W\.?P\.?|Crl\.?\s*A\.?)\s*(?:No\.?\s*)?\d+[\-/]\d+",
            r"(\d{4}\s*[A-Z]+\s*\d+)",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.I)
            if m:
                return m.group(0).strip()
        return None

    @staticmethod
    def _extract_judges(text):
        judges = []
        for m in re.findall(
            r"(?:Hon['\u2019]?ble\s+)?(?:Mr\.?\s+)?Justice\s+"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            text,
        ):
            name = m.strip()
            if len(name) > 5 and name not in judges:
                judges.append(name)
        return judges[:10]

    @staticmethod
    def _extract_cited_cases(text):
        cited = []
        for pat in [
            r"(PLD\s+\d{4}\s+\w+\s+\d+)",
            r"(\d{4}\s+(?:SCMR|CLC|MLD|PLC|YLR|PCrLJ)\s+\d+)",
        ]:
            for m in re.findall(pat, text, re.I):
                if m.strip() not in cited:
                    cited.append(m.strip())
        return cited[:50]

    @staticmethod
    def _extract_statutes(text):
        statutes = []
        for m in re.findall(
            r"((?:Section|S\.)\s+\d+[\w]*\s+(?:of\s+)?(?:the\s+)?"
            r"[\w\s]+(?:Act|Ordinance|Code)[\s,]*\d{4})",
            text,
            re.I,
        ):
            if m.strip() not in statutes:
                statutes.append(m.strip())
        return statutes[:30]

    @staticmethod
    def _extract_articles(text):
        articles = []
        for m in re.findall(
            r"(Article\s+\d+[\w]*(?:\s+of\s+the\s+Constitution)?)",
            text,
            re.I,
        ):
            if m.strip() not in articles:
                articles.append(m.strip())
        return articles[:20]

    @staticmethod
    def _extract_parties(text):
        appellants = []
        respondents = []
        m = re.search(
            r"([A-Z][\w\s\.]+?)\s+(?:vs?\.?|versus)\s+"
            r"([A-Z][\w\s\.]+?)(?:\n|$)",
            text[:2000],
        )
        if m:
            appellants = [m.group(1).strip()[:100]]
            respondents = [m.group(2).strip()[:100]]
        return appellants, respondents

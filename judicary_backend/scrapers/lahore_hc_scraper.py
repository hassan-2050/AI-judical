"""
Scraper for the Lahore High Court reported judgments.
Targets: https://data.lhc.gov.pk/reported_judgments/judgments_approved_for_reporting
"""

import logging
import re
from datetime import datetime
from urllib.parse import urljoin

from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class LahoreHighCourtScraper(BaseScraper):
    SOURCE_NAME = "lahore_high_court"
    BASE_URL = "https://data.lhc.gov.pk"
    JUDGMENTS_URL = (
        "https://data.lhc.gov.pk/reported_judgments/judgments_approved_for_reporting"
    )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def scrape(self, **kwargs):
        """Scrape reported judgments from the Lahore High Court data portal."""
        self.create_job(extra_config=kwargs)
        max_pages = kwargs.get("max_pages", self.max_pages)  # kept for API compat

        try:
            self.job.add_log("Fetching LHC reported-judgments page...")
            soup = self.get_soup(self.JUDGMENTS_URL)

            if not soup:
                self.job.add_log(
                    "Failed to fetch LHC judgments page", level="error"
                )
                self.job.errors_count += 1
                self.finish_job("failed")
                return self.job

            cases = self.parse_case_list(soup)
            self.job.add_log(f"Found {len(cases)} case entries on page")

            total_new = 0
            total_updated = 0
            total_found = len(cases)

            for case_data in cases:
                try:
                    result = self.save_case(case_data)
                    if result == "new":
                        total_new += 1
                    elif result == "updated":
                        total_updated += 1
                except Exception as e:
                    logger.error("Error saving LHC case: %s", e)
                    self.job.errors_count += 1
                    self.job.add_log(f"Error: {str(e)[:200]}", level="error")

            self.job.pages_scraped = 1
            self.job.cases_found = total_found
            self.job.cases_new = total_new
            self.job.cases_updated = total_updated
            self.job.save()

            self.finish_job("completed")

        except Exception as e:
            logger.error("LHC scraping failed: %s", e)
            self.job.add_log(f"Fatal error: {str(e)[:500]}", level="error")
            self.finish_job("failed")
            raise

        return self.job

    # ------------------------------------------------------------------
    # Abstract-method implementations
    # ------------------------------------------------------------------

    def parse_case_list(self, soup):
        """Parse the reported-judgments HTML table.

        Each table row has two columns:
          0 - serial number
          1 - case text block containing case_type + number/year,
              parties (in parentheses, separated by "Vs"),
              judge ("by Mr. Justice ..."),
              optional tag line ("Tag Line: ..."),
              and upload date ("uploaded on: DD-MM-YYYY").
        """
        cases = []

        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 2:
                    continue

                text = self.clean_text(cols[1].get_text())
                if not text or len(text) < 10:
                    continue

                case_data = self._parse_lhc_entry(text)
                if case_data:
                    cases.append(case_data)

        # Fallback: try to find entries outside a <table>
        if not cases:
            body = soup.find(
                "div", class_=re.compile(r"content|main|view", re.I)
            ) or soup
            # Look for numbered paragraphs
            for node in body.find_all(["p", "li", "div"]):
                text = self.clean_text(node.get_text())
                if re.match(r"^\d+\.\s+", text):
                    case_data = self._parse_lhc_entry(text)
                    if case_data:
                        cases.append(case_data)

        return cases

    def parse_case_detail(self, soup, url=None):
        """Parse a case detail / judgment page (if available)."""
        data = {}

        content = soup.find("article") or soup.find(
            "div", class_=re.compile(r"content|field|node|main", re.I)
        )

        if content:
            text = self.clean_text(content.get_text())
            data["full_text"] = text[:50000]
            data["summary"] = text[:2000]
            data["judge_names"] = self._extract_judges(text)

            appellants, respondents = self._extract_parties(text)
            if appellants:
                data["appellants"] = appellants
            if respondents:
                data["respondents"] = respondents

        pdf_link = soup.find("a", href=re.compile(r"\.pdf", re.I))
        if pdf_link:
            data["pdf_url"] = urljoin(self.BASE_URL, pdf_link["href"])

        data["source_url"] = url
        return data

    # ------------------------------------------------------------------
    # Internal parsing helpers
    # ------------------------------------------------------------------

    def _parse_lhc_entry(self, text):
        """Parse a single judgment text block from the LHC table.

        Expected patterns inside *text*:
          "Civil Revision 29718/25 (Syed Asif Imran ... Vs Zeenat Begum etc)
           by Mr. Justice Malik Waqar Haider Awan
           Tag Line: Though the Specific Relief Act ...
           uploaded on: 06-02-2026"
        """
        # Strip leading serial number ("1. ", "2. ", etc.)
        text = re.sub(r"^\d+\.\s*", "", text)

        # --- Case type + case number/year ---
        case_match = re.match(
            r"(?P<case_type>[A-Za-z\s\.]+?)\s+(?P<number>\d+[\w\-]*/\d{2,4})",
            text,
        )
        case_type = case_match.group("case_type").strip() if case_match else ""
        raw_number = case_match.group("number").strip() if case_match else ""
        case_number = f"{case_type} {raw_number}".strip() if case_match else text[:60]

        # --- Parties (between first '(' and matching ')' that contains Vs) ---
        appellants = []
        respondents = []
        parties_match = re.search(r"\(([^)]*?Vs[^)]*?)\)", text, re.IGNORECASE)
        if parties_match:
            parties_text = parties_match.group(1)
            parts = re.split(r"\s+Vs\.?\s+", parties_text, flags=re.IGNORECASE)
            if len(parts) >= 2:
                appellants = [parts[0].strip()[:200]]
                respondents = [parts[1].strip()[:200]]

        title_parts = []
        if appellants:
            title_parts.append(appellants[0])
        title_parts.append("Vs")
        if respondents:
            title_parts.append(respondents[0])
        title = " ".join(title_parts) if appellants or respondents else text[:200]

        # --- Judge ---
        judge_names = []
        judge_match = re.search(
            r"by\s+(?:Mr\.?\s+)?Justice\s+(.+?)(?=\s+Tag\s+Line|\s+uploaded\s+on|$)",
            text,
            re.IGNORECASE,
        )
        if judge_match:
            judge_names = [judge_match.group(1).strip().rstrip(". ")]

        # --- Tag line ---
        tag_match = re.search(
            r"Tag\s+Line:\s*(.+?)(?=\s+uploaded\s+on|$)",
            text,
            re.IGNORECASE,
        )
        tag_line = tag_match.group(1).strip() if tag_match else ""

        # --- Upload date ---
        date_match = re.search(r"uploaded\s+on:\s*([\d\-]+)", text, re.IGNORECASE)
        upload_date = None
        if date_match:
            upload_date = self.parse_date(date_match.group(1))

        year = self.extract_year(raw_number) or (
            upload_date.year if upload_date else None
        )

        return {
            "case_number": case_number,
            "title": title[:300],
            "court": "Lahore High Court",
            "case_type": case_type or None,
            "year": year,
            "judge_names": judge_names,
            "appellants": appellants,
            "respondents": respondents,
            "headnotes": tag_line[:2000] if tag_line else None,
            "summary": tag_line[:2000] if tag_line else None,
            "judgment_date": upload_date,
            "source_url": self.JUDGMENTS_URL,
            "status": "decided",
        }

    # ------------------------------------------------------------------
    # Static helper methods
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_case_number(text):
        patterns = [
            r"(W\.?P\.?\s*(?:No\.?\s*)?\d+[\-/]\d+(?:\s*of\s+\d{4})?)",
            r"((?:Crl\.?|Civil|Writ|Constitution|Family)\s*"
            r"(?:Appeal|Petition|Misc|Application|Original|Revision)"
            r"\s*No\.?\s*\d+[\-/]?\s*(?:of\s+)?\d{4})",
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
        patterns = [
            r"(?:Hon['\u2019]?ble\s+)?(?:Mr\.?\s+)?Justice\s+"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        ]
        for pat in patterns:
            for m in re.findall(pat, text):
                name = m.strip()
                if len(name) > 5 and name not in judges:
                    judges.append(name)
        return judges[:10]

    @staticmethod
    def _extract_parties(text):
        """Try to extract appellant and respondent names."""
        appellants = []
        respondents = []
        vs_match = re.search(
            r"([A-Z][\w\s\.]+?)\s+(?:vs\.?|versus|v\.?)\s+"
            r"([A-Z][\w\s\.]+?)(?:\n|$)",
            text[:2000],
        )
        if vs_match:
            appellants = [vs_match.group(1).strip()[:100]]
            respondents = [vs_match.group(2).strip()[:100]]
        return appellants, respondents

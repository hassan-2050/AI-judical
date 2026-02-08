"""
Scraper for the Supreme Court of Pakistan website.
Targets the publicly accessible homepage and cause-lists pages.
    Homepage : https://www.supremecourt.gov.pk/
    Cause-lists : https://www.supremecourt.gov.pk/cause-lists/
"""

import logging
import re
from datetime import datetime
from urllib.parse import urljoin

from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class SupremeCourtScraper(BaseScraper):
    SOURCE_NAME = "supreme_court_pk"
    BASE_URL = "https://www.supremecourt.gov.pk"
    HOMEPAGE_URL = "https://www.supremecourt.gov.pk/"
    CAUSE_LISTS_URL = "https://www.supremecourt.gov.pk/cause-lists/"

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def scrape(self, **kwargs):
        """Scrape available content from the Supreme Court of Pakistan.

        Strategy:
          1. Fetch the homepage - extract highlights, news items, and
             any linked PDFs.
          2. Fetch the cause-lists page - collect cause-list PDF links.
        """
        self.create_job(extra_config=kwargs)
        max_pages = kwargs.get("max_pages", self.max_pages)

        try:
            total_new = 0
            total_updated = 0
            total_found = 0
            pages_scraped = 0

            # ---------- Homepage ----------
            self.job.add_log("Fetching SC homepage...")
            home_soup = self.get_soup(self.HOMEPAGE_URL)

            if home_soup:
                cases = self.parse_case_list(home_soup)
                self.job.add_log(
                    f"Found {len(cases)} entries on homepage"
                )
                total_found += len(cases)

                for case_data in cases:
                    try:
                        result = self.save_case(case_data)
                        if result == "new":
                            total_new += 1
                        elif result == "updated":
                            total_updated += 1
                    except Exception as e:
                        logger.error("Error saving SC case: %s", e)
                        self.job.errors_count += 1
                        self.job.add_log(
                            f"Error: {str(e)[:200]}", level="error"
                        )

                pages_scraped += 1
            else:
                self.job.add_log(
                    "Homepage fetch failed (possible 403)", level="error"
                )
                self.job.errors_count += 1

            # ---------- Cause-lists page ----------
            if pages_scraped < max_pages:
                self.job.add_log("Fetching SC cause-lists page...")
                cl_soup = self.get_soup(self.CAUSE_LISTS_URL)

                if cl_soup:
                    cl_cases = self._parse_cause_list_page(cl_soup)
                    self.job.add_log(
                        f"Found {len(cl_cases)} cause-list entries"
                    )
                    total_found += len(cl_cases)

                    for case_data in cl_cases:
                        try:
                            result = self.save_case(case_data)
                            if result == "new":
                                total_new += 1
                            elif result == "updated":
                                total_updated += 1
                        except Exception as e:
                            logger.error("Error saving SC cause-list: %s", e)
                            self.job.errors_count += 1
                            self.job.add_log(
                                f"Error: {str(e)[:200]}", level="error"
                            )

                    pages_scraped += 1
                else:
                    self.job.add_log(
                        "Cause-lists page fetch failed", level="error"
                    )
                    self.job.errors_count += 1

            # ---------- Finalise ----------
            self.job.pages_scraped = pages_scraped
            self.job.cases_found = total_found
            self.job.cases_new = total_new
            self.job.cases_updated = total_updated
            self.job.save()

            status = "completed" if pages_scraped > 0 else "failed"
            self.finish_job(status)

        except Exception as e:
            logger.error("SC scraping failed: %s", e)
            self.job.add_log(f"Fatal error: {str(e)[:500]}", level="error")
            self.finish_job("failed")
            raise

        return self.job

    # ------------------------------------------------------------------
    # Abstract-method implementations
    # ------------------------------------------------------------------

    def parse_case_list(self, soup):
        """Parse the SC homepage for news / highlights / judgment links.

        The homepage contains:
          - article or div blocks with press-releases / highlights
          - links to PDF judgments and cause lists
          - tables with recent data
        """
        cases = []

        # --- 1. Table-based entries ---
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows[1:]:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    case_data = self._parse_table_row(cols)
                    if case_data:
                        cases.append(case_data)

        # --- 2. Article / div blocks ---
        articles = soup.find_all("article") or soup.find_all(
            "div",
            class_=re.compile(
                r"post|entry|judgment|case|highlight|news|item", re.I
            ),
        )
        for article in articles:
            case_data = self._parse_article_block(article)
            if case_data:
                cases.append(case_data)

        # --- 3. Link-based approach (PDF judgments, etc.) ---
        seen_hrefs = {c.get("source_url") for c in cases}
        links = soup.find_all("a", href=True)
        for link in links:
            href = link.get("href", "")
            text = self.clean_text(link.get_text())
            full_url = urljoin(self.BASE_URL, href)

            if full_url in seen_hrefs:
                continue

            if not text or len(text) < 5:
                continue

            is_relevant = any(
                kw in href.lower()
                for kw in [
                    "judgment",
                    "order",
                    "cause_list",
                    "cause-list",
                    ".pdf",
                    "press",
                    "notice",
                ]
            )
            if not is_relevant:
                continue

            case_number = self._extract_case_number(text)
            if not case_number:
                # Derive a synthetic case number from the filename / text
                case_number = self._case_number_from_url(href, text)

            if case_number:
                is_pdf = href.lower().endswith(".pdf")
                cases.append(
                    {
                        "case_number": case_number,
                        "title": text[:200],
                        "court": "Supreme Court of Pakistan",
                        "source_url": full_url,
                        "pdf_url": full_url if is_pdf else None,
                        "year": self.extract_year(text)
                        or self.extract_year(href),
                        "status": "pending"
                        if "cause" in href.lower()
                        else "decided",
                    }
                )
                seen_hrefs.add(full_url)

        return cases

    def parse_case_detail(self, soup, url=None):
        """Parse a case detail page."""
        data = {}

        content = soup.find("article") or soup.find(
            "div", class_=re.compile(r"content|entry|post|main", re.I)
        )

        if content:
            full_text = self.clean_text(content.get_text())
            data["full_text"] = full_text[:50000]

            first_p = content.find("p")
            if first_p:
                data["summary"] = self.clean_text(first_p.get_text())[:2000]

            data["judge_names"] = self._extract_judges(full_text)
            data["cited_cases"] = self._extract_cited_cases(full_text)
            data["cited_statutes"] = self._extract_statutes(full_text)

        pdf_link = soup.find("a", href=re.compile(r"\.pdf", re.I))
        if pdf_link:
            data["pdf_url"] = urljoin(self.BASE_URL, pdf_link["href"])

        data["source_url"] = url
        return data

    # ------------------------------------------------------------------
    # Internal parsing helpers
    # ------------------------------------------------------------------

    def _parse_cause_list_page(self, soup):
        """Parse the /cause-lists/ page for PDF links."""
        cases = []
        links = soup.find_all("a", href=True)

        for link in links:
            href = link.get("href", "")
            text = self.clean_text(link.get_text())
            full_url = urljoin(self.BASE_URL, href)

            if not href.lower().endswith(".pdf") and "cause" not in href.lower():
                continue

            if not text or len(text) < 3:
                continue

            case_number = self._case_number_from_url(href, text)
            if not case_number:
                continue

            cases.append(
                {
                    "case_number": case_number,
                    "title": f"Cause List - {text[:180]}",
                    "court": "Supreme Court of Pakistan",
                    "case_type": "Cause List",
                    "status": "pending",
                    "source_url": full_url,
                    "pdf_url": full_url if href.lower().endswith(".pdf") else None,
                    "year": self.extract_year(text) or self.extract_year(href),
                }
            )

        return cases

    def _parse_table_row(self, cols):
        """Parse a table row from any table on the SC pages."""
        try:
            texts = [self.clean_text(col.get_text()) for col in cols]
            link = None
            for col in cols:
                a = col.find("a", href=True)
                if a:
                    link = urljoin(self.BASE_URL, a["href"])
                    break

            case_number = None
            title = None
            date_str = None

            for text in texts:
                if (
                    re.search(r"\d+/\d+|[A-Z]+[\s\-]*\d+", text)
                    and not case_number
                ):
                    case_number = text
                elif self.parse_date(text) and not date_str:
                    date_str = text
                elif len(text) > 20 and not title:
                    title = text

            if not case_number:
                case_number = texts[0] if texts else None
            if not title:
                title = texts[1] if len(texts) > 1 else case_number
            if not case_number:
                return None

            return {
                "case_number": case_number,
                "title": (title or case_number)[:200],
                "court": "Supreme Court of Pakistan",
                "judgment_date": self.parse_date(date_str) if date_str else None,
                "year": self.extract_year(date_str or case_number),
                "source_url": link,
                "pdf_url": link if link and link.endswith(".pdf") else None,
            }
        except Exception as e:
            logger.debug("Error parsing table row: %s", e)
            return None

    def _parse_article_block(self, article):
        """Parse an article / div block listing a case or news item."""
        try:
            title_elem = article.find(["h2", "h3", "h4", "a"])
            if not title_elem:
                return None

            title = self.clean_text(title_elem.get_text())
            if not title or len(title) < 5:
                return None

            link = None
            a_tag = article.find("a", href=True)
            if a_tag:
                link = urljoin(self.BASE_URL, a_tag["href"])

            case_number = self._extract_case_number(title)
            if not case_number:
                case_number = title[:60]

            date_text = article.find(
                "span", class_=re.compile(r"date|time", re.I)
            )
            judgment_date = None
            if date_text:
                judgment_date = self.parse_date(date_text.get_text())

            return {
                "case_number": case_number,
                "title": title[:200],
                "court": "Supreme Court of Pakistan",
                "judgment_date": judgment_date,
                "year": self.extract_year(title),
                "source_url": link,
                "summary": self.clean_text(article.get_text())[:500],
            }
        except Exception as e:
            logger.debug("Error parsing article: %s", e)
            return None

    @staticmethod
    def _case_number_from_url(href, text):
        """Derive a synthetic case number from a URL or link text."""
        # Try filename without extension
        filename = href.rstrip("/").rsplit("/", 1)[-1]
        filename = re.sub(r"\.\w{3,4}$", "", filename)  # strip .pdf etc.
        if filename and len(filename) > 3:
            return f"SC-{filename[:80]}"
        if text and len(text) > 3:
            slug = re.sub(r"[^A-Za-z0-9]+", "-", text)[:60].strip("-")
            return f"SC-{slug}"
        return None

    # ------------------------------------------------------------------
    # Static helper methods
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_case_number(text):
        """Extract case number patterns like 'C.A. 123/2024'."""
        patterns = [
            r"(?:C\.?A\.?|Crl\.?\s*A\.?|C\.?P\.?|W\.?P\.?|S\.?M\.?C\.?|H\.?R\.?C\.?)"
            r"\s*(?:No\.?\s*)?(\d+[\-/]\d+(?:\s*(?:of|\/)\s*\d{4})?)",
            r"(?:Civil|Criminal|Writ|Constitution)\s+"
            r"(?:Appeal|Petition|Review|Application)"
            r"\s+No\.?\s*(\d+[\-/]?\s*(?:of\s+)?\d{4})",
            r"(\d{4}\s*[A-Z]+\s*\d+)",
            r"([A-Z][\w\.]+\s*\d+[\s/\-]*(?:of\s+)?\d{4})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        return None

    @staticmethod
    def _extract_judges(text):
        """Extract judge names from judgment text."""
        judges = []
        patterns = [
            r"(?:Hon['\u2019]?ble\s+)?(?:Mr\.?\s+)?Justice\s+"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            r"(?:JUSTICE|Justice)\s+([A-Z\s\.]+?)(?=\s*,|\s*and\s|\s*\n|\s*J\.)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),?\s*J\.?",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                name = m.strip().rstrip(",. ")
                if len(name) > 5 and name not in judges:
                    judges.append(name)
        return judges[:10]

    @staticmethod
    def _extract_cited_cases(text):
        """Extract cited case references."""
        cited = []
        patterns = [
            r"(PLD\s+\d{4}\s+\w+\s+\d+)",
            r"(\d{4}\s+SCMR\s+\d+)",
            r"(\d{4}\s+CLC\s+\d+)",
            r"(\d{4}\s+MLD\s+\d+)",
            r"(\d{4}\s+PLC\s+\d+)",
            r"(\d{4}\s+YLR\s+\d+)",
            r"(AIR\s+\d{4}\s+\w+\s+\d+)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                if m.strip() not in cited:
                    cited.append(m.strip())
        return cited[:50]

    @staticmethod
    def _extract_statutes(text):
        """Extract referenced statutes and articles."""
        statutes = []
        patterns = [
            r"((?:Section|S\.)\s+\d+[\w]*\s+(?:of\s+)?(?:the\s+)?"
            r"[A-Z][\w\s,]+(?:Act|Ordinance|Code|Order)[\s,]*\d{4})",
            r"(Article\s+\d+[\w]*\s+of\s+the\s+Constitution)",
            r"((?:Pakistan\s+Penal\s+Code|Cr\.?P\.?C\.?|C\.?P\.?C\.?|"
            r"Qanun-e-Shahadat)[\s,]*(?:Section\s+)?\d+[\w]*)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                clean = m.strip()
                if clean not in statutes:
                    statutes.append(clean)
        return statutes[:30]

    @staticmethod
    def _extract_parties(text):
        """Try to extract appellant and respondent names."""
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

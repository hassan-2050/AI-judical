"""
Scheduler for running scrapers on a schedule or on-demand.
"""

import logging
from datetime import datetime
from threading import Thread

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from scrapers.supreme_court_scraper import SupremeCourtScraper
from scrapers.lahore_hc_scraper import LahoreHighCourtScraper
from scrapers.case_law_scraper import CaseLawScraper

logger = logging.getLogger(__name__)

# Registry of available scrapers
SCRAPER_REGISTRY = {
    "supreme_court": SupremeCourtScraper,
    "lahore_hc": LahoreHighCourtScraper,
    "case_law": CaseLawScraper,
}


class ScraperScheduler:
    """Manages scraper scheduling and execution."""

    def __init__(self, app_config=None):
        self.config = app_config or {}
        self.scheduler = BackgroundScheduler()
        self._running_jobs = {}

    def start(self):
        """Start the scheduler with default jobs."""
        # Daily scrape of Supreme Court at 2 AM
        self.scheduler.add_job(
            self._run_scraper,
            CronTrigger(hour=2, minute=0),
            args=["supreme_court"],
            kwargs={"max_pages": 5},
            id="daily_sc",
            name="Daily Supreme Court Scrape",
            replace_existing=True,
        )

        # Daily scrape of Lahore HC at 3 AM
        self.scheduler.add_job(
            self._run_scraper,
            CronTrigger(hour=3, minute=0),
            args=["lahore_hc"],
            kwargs={"max_pages": 5},
            id="daily_lhc",
            name="Daily Lahore HC Scrape",
            replace_existing=True,
        )

        # Weekly full scrape on Sundays at 1 AM
        self.scheduler.add_job(
            self._run_scraper,
            CronTrigger(day_of_week="sun", hour=1, minute=0),
            args=["case_law"],
            kwargs={"max_pages": 20, "year": datetime.now().year},
            id="weekly_case_law",
            name="Weekly Case Law Scrape",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info("Scraper scheduler started")

    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scraper scheduler stopped")

    def run_now(self, scraper_name, **kwargs):
        """Run a scraper immediately in a background thread."""
        if scraper_name in self._running_jobs:
            return None, "Scraper is already running"

        scraper_class = SCRAPER_REGISTRY.get(scraper_name)
        if not scraper_class:
            return None, f"Unknown scraper: {scraper_name}"

        scraper = scraper_class(config=self.config)
        job = scraper.create_job(extra_config=kwargs)

        def _run():
            try:
                self._running_jobs[scraper_name] = job
                scraper.scrape(**kwargs)
            except Exception as e:
                logger.error("Scraper %s failed: %s", scraper_name, e)
            finally:
                self._running_jobs.pop(scraper_name, None)

        thread = Thread(target=_run, daemon=True)
        thread.start()

        return job, None

    def _run_scraper(self, scraper_name, **kwargs):
        """Internal method used by scheduler."""
        scraper_class = SCRAPER_REGISTRY.get(scraper_name)
        if not scraper_class:
            logger.error("Unknown scraper: %s", scraper_name)
            return

        try:
            scraper = scraper_class(config=self.config)
            scraper.scrape(**kwargs)
        except Exception as e:
            logger.error("Scheduled scrape failed for %s: %s", scraper_name, e)

    def get_status(self):
        """Get the current status of all scheduled and running jobs."""
        scheduled = []
        for job in self.scheduler.get_jobs():
            scheduled.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat()
                    if job.next_run_time
                    else None,
                }
            )

        running = {
            name: str(job.id) for name, job in self._running_jobs.items()
        }

        return {
            "scheduled_jobs": scheduled,
            "running_scrapers": running,
            "available_scrapers": list(SCRAPER_REGISTRY.keys()),
        }

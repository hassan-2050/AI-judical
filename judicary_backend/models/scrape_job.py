import mongoengine as me
from datetime import datetime


class ScrapeLog(me.EmbeddedDocument):
    """Log entry for a scraping step."""

    timestamp = me.DateTimeField(default=datetime.utcnow)
    message = me.StringField()
    level = me.StringField(choices=["info", "warning", "error"], default="info")


class ScrapeJob(me.Document):
    """Tracks a scraping job's lifecycle."""

    meta = {
        "collection": "scrape_jobs",
        "indexes": ["status", "source", "-started_at"],
    }

    source = me.StringField(required=True)  # e.g., "supreme_court", "lahore_hc"
    status = me.StringField(
        choices=["queued", "running", "completed", "failed", "cancelled"],
        default="queued",
    )
    total_pages = me.IntField(default=0)
    pages_scraped = me.IntField(default=0)
    cases_found = me.IntField(default=0)
    cases_new = me.IntField(default=0)
    cases_updated = me.IntField(default=0)
    errors_count = me.IntField(default=0)

    config = me.DictField()  # Scraper-specific configuration
    logs = me.EmbeddedDocumentListField(ScrapeLog)

    started_at = me.DateTimeField()
    completed_at = me.DateTimeField()
    created_at = me.DateTimeField(default=datetime.utcnow)

    def add_log(self, message, level="info"):
        self.logs.append(ScrapeLog(message=message, level=level))
        self.save()

    def to_json(self):
        return {
            "id": str(self.id),
            "source": self.source,
            "status": self.status,
            "total_pages": self.total_pages,
            "pages_scraped": self.pages_scraped,
            "cases_found": self.cases_found,
            "cases_new": self.cases_new,
            "cases_updated": self.cases_updated,
            "errors_count": self.errors_count,
            "config": self.config,
            "logs": [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "message": log.message,
                    "level": log.level,
                }
                for log in (self.logs or [])[-50:]  # Last 50 log entries
            ],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat(),
        }

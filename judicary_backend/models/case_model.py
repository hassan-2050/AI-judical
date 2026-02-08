import mongoengine as me
from datetime import datetime


class CaseParty(me.EmbeddedDocument):
    """Embedded document for case parties (appellants/respondents)."""

    name = me.StringField(required=True)
    role = me.StringField()  # e.g., "appellant", "respondent", "petitioner"
    advocate = me.StringField()


class CaseDate(me.EmbeddedDocument):
    """Embedded document for important case dates."""

    hearing_date = me.DateTimeField()
    judgment_date = me.DateTimeField()
    filing_date = me.DateTimeField()
    notification_date = me.DateTimeField()


class Case(me.Document):
    """Court case model – stores scraped and user-uploaded case data."""

    meta = {
        "collection": "cases",
        "indexes": [
            "case_number",
            "court",
            "status",
            "judge_names",
            "case_type",
            "year",
            {"fields": ["$title", "$summary", "$case_number"],
             "default_language": "english",
             "weights": {"title": 10, "case_number": 8, "summary": 5}},
        ],
    }

    # Core fields
    case_number = me.StringField(required=True)
    title = me.StringField(required=True)
    court = me.StringField(required=True)
    bench = me.StringField()
    case_type = me.StringField()
    year = me.IntField()
    status = me.StringField(
        choices=["pending", "decided", "adjourned", "disposed", "enacted", "unknown"],
        default="unknown",
    )

    # Parties
    appellants = me.ListField(me.StringField())
    respondents = me.ListField(me.StringField())
    parties = me.EmbeddedDocumentListField(CaseParty)

    # Judges
    judge_names = me.ListField(me.StringField())

    # Content
    summary = me.StringField()
    full_text = me.StringField()
    judgment_text = me.StringField()
    headnotes = me.StringField()

    # Dates
    dates = me.EmbeddedDocumentField(CaseDate)
    judgment_date = me.DateTimeField()
    filing_date = me.DateTimeField()

    # References
    cited_cases = me.ListField(me.StringField())
    cited_statutes = me.ListField(me.StringField())
    cited_articles = me.ListField(me.StringField())

    # Location & categorization
    locations = me.ListField(me.StringField())
    categories = me.ListField(me.StringField())
    tags = me.ListField(me.StringField())

    # Files
    source_url = me.StringField()
    pdf_url = me.StringField()
    file_name = me.StringField()

    # Scraping metadata
    source = me.StringField()  # which scraper produced this record
    scraped_at = me.DateTimeField()

    # Timestamps
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    def to_json(self):
        return {
            "id": str(self.id),
            "case_number": self.case_number,
            "title": self.title,
            "court": self.court,
            "bench": self.bench,
            "case_type": self.case_type,
            "year": self.year,
            "status": self.status,
            "appellants": self.appellants or [],
            "respondents": self.respondents or [],
            "judge_names": self.judge_names or [],
            "summary": self.summary or "",
            "judgment_text": self.judgment_text or "",
            "headnotes": self.headnotes or "",
            "judgment_date": self.judgment_date.isoformat() if self.judgment_date else None,
            "filing_date": self.filing_date.isoformat() if self.filing_date else None,
            "cited_cases": self.cited_cases or [],
            "cited_statutes": self.cited_statutes or [],
            "cited_articles": self.cited_articles or [],
            "locations": self.locations or [],
            "categories": self.categories or [],
            "tags": self.tags or [],
            "source_url": self.source_url,
            "pdf_url": self.pdf_url,
            "source": self.source,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    def to_card_json(self):
        """Lightweight representation for list views."""
        return {
            "id": str(self.id),
            "case_number": self.case_number,
            "title": self.title,
            "court": self.court,
            "case_type": self.case_type,
            "year": self.year,
            "status": self.status,
            "judge_names": self.judge_names or [],
            "summary": (self.summary or "")[:300],
            "judgment_date": self.judgment_date.isoformat() if self.judgment_date else None,
            "source": self.source,
        }

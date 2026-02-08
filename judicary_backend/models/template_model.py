"""Template model – stores legal document templates."""

import mongoengine as me
from datetime import datetime


class Template(me.Document):
    """Legal document template for generating standard legal documents."""

    meta = {
        "collection": "templates",
        "indexes": ["category", "language", "is_active"],
    }

    name = me.StringField(required=True)
    description = me.StringField()
    category = me.StringField(
        choices=["petition", "affidavit", "contract", "legal_notice",
                 "power_of_attorney", "bail_application", "writ_petition",
                 "appeal", "complaint", "agreement", "other"],
        required=True,
    )
    language = me.StringField(default="en", choices=["en", "ur", "both"])

    # Template content with placeholders like {{party_name}}, {{date}}, etc.
    content = me.StringField(required=True)
    placeholders = me.ListField(me.StringField())  # list of placeholder names

    # Metadata
    court_type = me.StringField()  # applicable court type
    jurisdiction = me.StringField()
    usage_count = me.IntField(default=0)
    is_active = me.BooleanField(default=True)

    created_by = me.ObjectIdField()
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    def to_json(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "language": self.language,
            "content": self.content,
            "placeholders": self.placeholders or [],
            "court_type": self.court_type,
            "jurisdiction": self.jurisdiction,
            "usage_count": self.usage_count,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_card(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "language": self.language,
            "court_type": self.court_type,
            "usage_count": self.usage_count,
        }

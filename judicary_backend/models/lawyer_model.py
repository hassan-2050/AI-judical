"""Lawyer model – directory of legal professionals."""

import mongoengine as me
from datetime import datetime


class LawyerReview(me.EmbeddedDocument):
    """Review for a lawyer."""
    user_id = me.ObjectIdField()
    rating = me.IntField(min_value=1, max_value=5)
    comment = me.StringField()
    created_at = me.DateTimeField(default=datetime.utcnow)


class Lawyer(me.Document):
    """Lawyer/Advocate profile for directory."""

    meta = {
        "collection": "lawyers",
        "indexes": [
            "specializations",
            "city",
            "court",
            "bar_council",
            {"fields": ["$name", "$specializations"],
             "default_language": "english"},
        ],
    }

    name = me.StringField(required=True)
    title = me.StringField()  # e.g., "Advocate", "Senior Advocate", "AOR"
    email = me.StringField()
    phone = me.StringField()
    address = me.StringField()
    city = me.StringField()
    province = me.StringField()

    # Professional details
    bar_council = me.StringField()
    license_number = me.StringField()
    court = me.StringField()  # primary court of practice
    experience_years = me.IntField()
    specializations = me.ListField(me.StringField())
    languages = me.ListField(me.StringField(), default=lambda: ["English", "Urdu"])
    bio = me.StringField()

    # Rating
    reviews = me.EmbeddedDocumentListField(LawyerReview)
    avg_rating = me.FloatField(default=0.0)
    total_reviews = me.IntField(default=0)

    is_verified = me.BooleanField(default=False)
    is_active = me.BooleanField(default=True)

    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    def to_json(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "title": self.title,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "city": self.city,
            "province": self.province,
            "bar_council": self.bar_council,
            "license_number": self.license_number,
            "court": self.court,
            "experience_years": self.experience_years,
            "specializations": self.specializations or [],
            "languages": self.languages or [],
            "bio": self.bio,
            "avg_rating": self.avg_rating,
            "total_reviews": self.total_reviews,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_card(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "title": self.title,
            "city": self.city,
            "court": self.court,
            "experience_years": self.experience_years,
            "specializations": (self.specializations or [])[:3],
            "avg_rating": self.avg_rating,
            "total_reviews": self.total_reviews,
            "is_verified": self.is_verified,
        }

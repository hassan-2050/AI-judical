import mongoengine as me
from datetime import datetime
from models.auth_model import Auth


class User(me.Document):
    """User profile model."""

    meta = {"collection": "users"}

    auth_id = me.ReferenceField(Auth, required=True, unique=True)
    first_name = me.StringField(required=True, max_length=100)
    last_name = me.StringField(max_length=100)
    gender = me.StringField(choices=["male", "female", "other"])
    phone_number = me.StringField(max_length=20)
    cnic_number = me.StringField(max_length=20)
    organization = me.StringField(max_length=200)
    country = me.StringField(max_length=100, default="Pakistan")
    province = me.StringField(max_length=100)
    city = me.StringField(max_length=100)
    address = me.StringField(max_length=500)
    subscription = me.StringField(
        choices=["free", "basic", "premium"], default="free"
    )
    saved_cases = me.ListField(me.StringField())
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    def to_json(self):
        return {
            "id": str(self.id),
            "auth_id": str(self.auth_id.id) if self.auth_id else None,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "gender": self.gender,
            "phone_number": self.phone_number,
            "cnic_number": self.cnic_number,
            "organization": self.organization,
            "country": self.country,
            "province": self.province,
            "city": self.city,
            "address": self.address,
            "subscription": self.subscription,
            "saved_cases": self.saved_cases,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

import mongoengine as me
from datetime import datetime


class Auth(me.Document):
    """Authentication credentials model."""

    meta = {"collection": "auth"}

    email = me.EmailField(required=True, unique=True)
    password = me.StringField(required=True)
    role = me.StringField(choices=["user", "admin", "scraper_admin"], default="user")
    is_active = me.BooleanField(default=True)
    last_login = me.DateTimeField()
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    def to_json_safe(self):
        """Return JSON without password."""
        return {
            "id": str(self.id),
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

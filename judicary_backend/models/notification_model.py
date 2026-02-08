"""Notification model – hearing reminders and system notifications."""

import mongoengine as me
from datetime import datetime


class Notification(me.Document):
    """User notifications for hearing dates, case updates, and system alerts."""

    meta = {
        "collection": "notifications",
        "indexes": ["user_id", "is_read", "-created_at", "reminder_date"],
        "ordering": ["-created_at"],
    }

    user_id = me.ObjectIdField(required=True)

    # Notification details
    title = me.StringField(required=True)
    message = me.StringField(required=True)
    notification_type = me.StringField(
        choices=["hearing_reminder", "case_update", "deadline", "system", "subscription"],
        default="system",
    )

    # Related entities
    case_id = me.ObjectIdField()
    case_number = me.StringField()

    # Reminder scheduling
    reminder_date = me.DateTimeField()
    is_recurring = me.BooleanField(default=False)
    recurrence_days = me.IntField()  # repeat every N days

    # Status
    is_read = me.BooleanField(default=False)
    is_sent = me.BooleanField(default=False)

    created_at = me.DateTimeField(default=datetime.utcnow)

    def to_json(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "case_id": str(self.case_id) if self.case_id else None,
            "case_number": self.case_number,
            "reminder_date": self.reminder_date.isoformat() if self.reminder_date else None,
            "is_recurring": self.is_recurring,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

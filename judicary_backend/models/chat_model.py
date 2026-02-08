"""Chat model – stores Munsif AI legal assistant conversations."""

import mongoengine as me
from datetime import datetime


class ChatMessage(me.EmbeddedDocument):
    """Single message in a chat session."""
    role = me.StringField(choices=["user", "assistant"], required=True)
    content = me.StringField(required=True)
    language = me.StringField(default="en")  # en or ur
    citations = me.ListField(me.StringField())  # case IDs referenced
    timestamp = me.DateTimeField(default=datetime.utcnow)


class ChatSession(me.Document):
    """AI chat session for Munsif AI legal assistant."""

    meta = {
        "collection": "chat_sessions",
        "indexes": ["user_id", "-created_at"],
        "ordering": ["-created_at"],
    }

    user_id = me.ObjectIdField(required=True)
    title = me.StringField(default="New Chat")
    messages = me.EmbeddedDocumentListField(ChatMessage)

    # Context
    context_type = me.StringField(
        choices=["general", "case_analysis", "legal_research", "prediction", "drafting"],
        default="general",
    )
    context_case_id = me.ObjectIdField()  # optional case being analyzed

    # Timestamps
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    def to_json(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "title": self.title,
            "context_type": self.context_type,
            "context_case_id": str(self.context_case_id) if self.context_case_id else None,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "language": m.language,
                    "citations": m.citations or [],
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                }
                for m in (self.messages or [])
            ],
            "message_count": len(self.messages or []),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_summary(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "context_type": self.context_type,
            "message_count": len(self.messages or []),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

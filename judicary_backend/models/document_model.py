"""Document model – stores uploaded legal documents and OCR results."""

import mongoengine as me
from datetime import datetime


class ExtractedEntity(me.EmbeddedDocument):
    """Named entity extracted from a document."""
    entity_type = me.StringField()  # PERSON, ORG, STATUTE, DATE, LOCATION, CASE_NUMBER, MONETARY
    value = me.StringField()
    confidence = me.FloatField(default=1.0)


class Document(me.Document):
    """Uploaded legal document with optional OCR and extraction results."""

    meta = {
        "collection": "documents",
        "indexes": ["user_id", "case_id", "doc_type", "created_at"],
    }

    user_id = me.ObjectIdField(required=True)
    case_id = me.ObjectIdField()  # optional link to a case

    # File info
    original_filename = me.StringField(required=True)
    stored_filename = me.StringField(required=True)
    file_path = me.StringField(required=True)
    file_size = me.IntField()  # bytes
    mime_type = me.StringField()
    doc_type = me.StringField(
        choices=["judgment", "petition", "affidavit", "evidence", "contract",
                 "legal_notice", "power_of_attorney", "other"],
        default="other",
    )

    # Extracted content
    extracted_text = me.StringField()
    summary = me.StringField()
    language = me.StringField(default="en")  # en or ur

    # NER extraction
    entities = me.EmbeddedDocumentListField(ExtractedEntity)

    # Status
    status = me.StringField(
        choices=["uploaded", "processing", "processed", "failed"],
        default="uploaded",
    )
    processing_error = me.StringField()

    # Timestamps
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    def to_json(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "case_id": str(self.case_id) if self.case_id else None,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "doc_type": self.doc_type,
            "summary": self.summary or "",
            "language": self.language,
            "status": self.status,
            "entities": [
                {"entity_type": e.entity_type, "value": e.value, "confidence": e.confidence}
                for e in (self.entities or [])
            ],
            "has_text": bool(self.extracted_text),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

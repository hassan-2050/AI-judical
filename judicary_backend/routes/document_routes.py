"""
Document Routes – Upload, manage, and process legal documents.
"""

import os
import uuid
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, g, send_file

from models.document_model import Document, ExtractedEntity
from services.extraction_service import extract_entities
from services.summary_service import generate_summary
from routes.auth_routes import token_required

logger = logging.getLogger(__name__)

document_bp = Blueprint("documents", __name__)

# Upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "txt", "doc", "docx", "png", "jpg", "jpeg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@document_bp.route("/documents/upload", methods=["POST"])
@token_required
def upload_document():
    """Upload a legal document."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    # Check file size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({"error": "File size exceeds 10 MB limit"}), 400

    # Save file
    ext = file.filename.rsplit(".", 1)[1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, stored_name)
    file.save(file_path)

    # Create document record
    doc = Document(
        user_id=g.current_user.id,
        original_filename=file.filename,
        stored_filename=stored_name,
        file_path=file_path,
        file_size=size,
        mime_type=file.content_type,
        doc_type=request.form.get("doc_type", "other"),
        status="uploaded",
    )

    # If it's a text file, extract content immediately
    if ext == "txt":
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            doc.extracted_text = text
            doc.status = "processing"
        except Exception as e:
            logger.error("Failed to read text file: %s", e)

    # Link to case if provided
    case_id = request.form.get("case_id")
    if case_id:
        try:
            from bson import ObjectId
            doc.case_id = ObjectId(case_id)
        except Exception:
            pass

    doc.save()

    # Process in background (for now, synchronous for text files)
    if doc.extracted_text:
        try:
            _process_document(doc)
        except Exception as e:
            logger.error("Document processing failed: %s", e)
            doc.status = "failed"
            doc.processing_error = str(e)
            doc.save()

    return jsonify({
        "message": "Document uploaded successfully",
        "document": doc.to_json(),
    }), 201


def _process_document(doc):
    """Process a document: extract entities, generate summary."""
    text = doc.extracted_text or ""
    if not text:
        doc.status = "failed"
        doc.processing_error = "No text content to process"
        doc.save()
        return

    # Extract entities
    entities = extract_entities(text)
    doc.entities = [
        ExtractedEntity(
            entity_type=e["entity_type"],
            value=e["value"],
            confidence=e.get("confidence", 0.85),
        )
        for e in entities
    ]

    # Generate summary
    if len(text) > 200:
        doc.summary = generate_summary(text, num_sentences=3)

    # Detect language
    from services.ai_service import detect_language
    doc.language = detect_language(text)

    doc.status = "processed"
    doc.updated_at = datetime.utcnow()
    doc.save()


@document_bp.route("/documents", methods=["GET"])
@token_required
def list_documents():
    """List documents for the current user."""
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    doc_type = request.args.get("doc_type")

    query = Document.objects(user_id=g.current_user.id)
    if doc_type:
        query = query.filter(doc_type=doc_type)

    total = query.count()
    docs = query.order_by("-created_at").skip((page - 1) * page_size).limit(page_size)

    return jsonify({
        "documents": [d.to_json() for d in docs],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }), 200


@document_bp.route("/documents/<doc_id>", methods=["GET"])
@token_required
def get_document(doc_id):
    """Get a specific document with full details."""
    try:
        doc = Document.objects(id=doc_id, user_id=g.current_user.id).first()
    except Exception:
        return jsonify({"error": "Invalid document ID"}), 400

    if not doc:
        return jsonify({"error": "Document not found"}), 404

    result = doc.to_json()
    # Include extracted text for detail view
    result["extracted_text"] = doc.extracted_text or ""
    return jsonify({"document": result}), 200


@document_bp.route("/documents/<doc_id>", methods=["DELETE"])
@token_required
def delete_document(doc_id):
    """Delete a document."""
    try:
        doc = Document.objects(id=doc_id, user_id=g.current_user.id).first()
    except Exception:
        return jsonify({"error": "Invalid document ID"}), 400

    if not doc:
        return jsonify({"error": "Document not found"}), 404

    # Delete file from disk
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except Exception as e:
        logger.error("Failed to delete file: %s", e)

    doc.delete()
    return jsonify({"message": "Document deleted"}), 200


@document_bp.route("/documents/<doc_id>/process", methods=["POST"])
@token_required
def process_document(doc_id):
    """Manually trigger processing of a document."""
    try:
        doc = Document.objects(id=doc_id, user_id=g.current_user.id).first()
    except Exception:
        return jsonify({"error": "Invalid document ID"}), 400

    if not doc:
        return jsonify({"error": "Document not found"}), 404

    # Try to extract text from PDF
    if not doc.extracted_text:
        ext = doc.original_filename.rsplit(".", 1)[1].lower() if "." in doc.original_filename else ""
        if ext == "pdf":
            try:
                import pdfplumber
                with pdfplumber.open(doc.file_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                doc.extracted_text = text
            except Exception as e:
                doc.status = "failed"
                doc.processing_error = f"PDF extraction failed: {str(e)}"
                doc.save()
                return jsonify({"error": "PDF text extraction failed", "detail": str(e)}), 500
        elif ext == "txt":
            try:
                with open(doc.file_path, "r", encoding="utf-8", errors="ignore") as f:
                    doc.extracted_text = f.read()
            except Exception as e:
                doc.status = "failed"
                doc.processing_error = str(e)
                doc.save()
                return jsonify({"error": "Failed to read file"}), 500
        else:
            return jsonify({"error": "Unsupported file format for text extraction. Supported: PDF, TXT"}), 400

    try:
        _process_document(doc)
        return jsonify({
            "message": "Document processed successfully",
            "document": doc.to_json(),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@document_bp.route("/documents/<doc_id>/download", methods=["GET"])
@token_required
def download_document(doc_id):
    """Download the original document file."""
    try:
        doc = Document.objects(id=doc_id, user_id=g.current_user.id).first()
    except Exception:
        return jsonify({"error": "Invalid document ID"}), 400

    if not doc:
        return jsonify({"error": "Document not found"}), 404

    if not os.path.exists(doc.file_path):
        return jsonify({"error": "File not found on server"}), 404

    return send_file(
        doc.file_path,
        download_name=doc.original_filename,
        as_attachment=True,
    )

"""
Translation Routes – Urdu-English legal translation API.
"""

import logging
from flask import Blueprint, request, jsonify

from services.translation_service import translate_legal_terms, get_legal_glossary, detect_language

logger = logging.getLogger(__name__)

translation_bp = Blueprint("translation", __name__)


@translation_bp.route("/translate", methods=["POST"])
def translate():
    """Translate legal text between English and Urdu."""
    data = request.json or {}
    text = data.get("text", "").strip()
    source_lang = data.get("source_lang", "auto")
    target_lang = data.get("target_lang", "auto")

    if not text:
        return jsonify({"error": "Text is required"}), 400

    result = translate_legal_terms(text, source_lang=source_lang, target_lang=target_lang)
    return jsonify(result), 200


@translation_bp.route("/translate/glossary", methods=["GET"])
def glossary():
    """Get the legal terminology glossary."""
    language = request.args.get("language", "en")
    terms = get_legal_glossary(language)
    return jsonify({
        "glossary": terms,
        "total": len(terms),
    }), 200


@translation_bp.route("/translate/detect", methods=["POST"])
def detect():
    """Detect the language of text."""
    data = request.json or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Text is required"}), 400

    lang = detect_language(text)
    return jsonify({
        "language": lang,
        "language_name": "Urdu" if lang == "ur" else "English",
    }), 200

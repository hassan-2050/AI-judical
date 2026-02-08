"""
AI Routes – Munsif AI Legal Assistant API
==========================================
Provides chat, case analysis, prediction, and case similarity endpoints.
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, g

from models.chat_model import ChatSession, ChatMessage
from models.case_model import Case
from services.ai_service import generate_ai_response, generate_case_analysis, detect_language, generate_gemini_summary
from services.summary_service import generate_summary, generate_headnotes
from services.extraction_service import extract_entities, extract_key_information
from services.similarity_service import find_similar_cases, find_similar_by_metadata
from routes.auth_routes import token_required

logger = logging.getLogger(__name__)

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/ai/chat", methods=["POST"])
@token_required
def chat():
    """Send a message to Munsif AI and get a response."""
    data = request.json or {}
    message = data.get("message", "").strip()
    session_id = data.get("session_id")
    language = data.get("language", "auto")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Get or create session
    session = None
    if session_id:
        try:
            session = ChatSession.objects(id=session_id, user_id=g.current_user.id).first()
        except Exception:
            pass

    if not session:
        session = ChatSession(
            user_id=g.current_user.id,
            title=message[:50] + ("..." if len(message) > 50 else ""),
        )
        session.save()

    # Search for relevant cases in database
    context_cases = []
    try:
        query_words = [w for w in message.split() if len(w) > 3][:5]
        if query_words:
            search_q = " ".join(query_words)
            cases = Case.objects.search_text(search_q).limit(5)
            context_cases = [c.to_card_json() if hasattr(c, 'to_card_json') else c.to_json() for c in cases]
    except Exception as e:
        logger.debug("Case search for AI context failed: %s", e)

    # Build conversation history for Gemini continuity
    history = []
    for m in session.messages:
        history.append({"role": m.role, "content": m.content})

    # Generate response
    ai_result = generate_ai_response(message, context_cases=context_cases, language=language, history=history)

    # Save messages to session
    user_msg = ChatMessage(role="user", content=message, language=detect_language(message))
    assistant_msg = ChatMessage(
        role="assistant",
        content=ai_result["response"],
        language=ai_result["language"],
        citations=ai_result.get("citations", []),
    )
    session.messages.append(user_msg)
    session.messages.append(assistant_msg)
    session.updated_at = datetime.utcnow()
    session.save()

    return jsonify({
        "session_id": str(session.id),
        "response": ai_result["response"],
        "language": ai_result["language"],
        "citations": ai_result.get("citations", []),
        "suggestions": ai_result.get("suggestions", []),
    }), 200


@ai_bp.route("/ai/sessions", methods=["GET"])
@token_required
def list_sessions():
    """List all chat sessions for the current user."""
    sessions = ChatSession.objects(user_id=g.current_user.id).order_by("-updated_at")
    return jsonify({
        "sessions": [s.to_summary() for s in sessions],
    }), 200


@ai_bp.route("/ai/sessions/<session_id>", methods=["GET"])
@token_required
def get_session(session_id):
    """Get a specific chat session with full messages."""
    try:
        session = ChatSession.objects(id=session_id, user_id=g.current_user.id).first()
    except Exception:
        return jsonify({"error": "Session not found"}), 404

    if not session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify({"session": session.to_json()}), 200


@ai_bp.route("/ai/sessions/<session_id>", methods=["DELETE"])
@token_required
def delete_session(session_id):
    """Delete a chat session."""
    try:
        session = ChatSession.objects(id=session_id, user_id=g.current_user.id).first()
        if session:
            session.delete()
    except Exception:
        pass
    return jsonify({"message": "Session deleted"}), 200


@ai_bp.route("/ai/analyze/<case_id>", methods=["GET"])
def analyze_case(case_id):
    """Generate AI analysis of a specific case."""
    try:
        case = Case.objects(id=case_id).first()
    except Exception:
        return jsonify({"error": "Invalid case ID"}), 400

    if not case:
        return jsonify({"error": "Case not found"}), 404

    case_data = case.to_json()
    analysis = generate_case_analysis(case_data)

    return jsonify({"analysis": analysis}), 200


@ai_bp.route("/ai/summarize/<case_id>", methods=["GET"])
def summarize_case(case_id):
    """Generate a summary of a case."""
    try:
        case = Case.objects(id=case_id).first()
    except Exception:
        return jsonify({"error": "Invalid case ID"}), 400

    if not case:
        return jsonify({"error": "Case not found"}), 404

    text = case.full_text or case.judgment_text or case.summary or ""
    num_sentences = request.args.get("sentences", 5, type=int)

    # Try Gemini first, fall back to extractive summary
    summary = generate_gemini_summary(text, num_sentences=num_sentences)
    if not summary:
        summary = generate_summary(text, num_sentences=num_sentences)
    headnotes = generate_headnotes(text)

    return jsonify({
        "case_id": str(case.id),
        "summary": summary,
        "headnotes": headnotes,
        "original_length": len(text),
        "summary_length": len(summary),
    }), 200


@ai_bp.route("/ai/extract/<case_id>", methods=["GET"])
def extract_case_entities(case_id):
    """Extract named entities from a case."""
    try:
        case = Case.objects(id=case_id).first()
    except Exception:
        return jsonify({"error": "Invalid case ID"}), 400

    if not case:
        return jsonify({"error": "Case not found"}), 404

    text = case.full_text or case.judgment_text or case.summary or case.title
    extraction = extract_key_information(text)

    return jsonify({
        "case_id": str(case.id),
        "extraction": extraction,
    }), 200


@ai_bp.route("/ai/similar/<case_id>", methods=["GET"])
def find_similar(case_id):
    """Find cases similar to the given case."""
    try:
        target = Case.objects(id=case_id).first()
    except Exception:
        return jsonify({"error": "Invalid case ID"}), 400

    if not target:
        return jsonify({"error": "Case not found"}), 404

    limit = request.args.get("limit", 10, type=int)
    method = request.args.get("method", "metadata")  # "tfidf" or "metadata"

    target_data = target.to_json()

    # Get candidate cases (same court or same type, limit to 200 for performance)
    query = Case.objects(id__ne=target.id)
    if target.court:
        query = query.filter(court=target.court)
    candidates = query.limit(200)
    candidate_data = [c.to_json() for c in candidates]

    # If not enough from same court, add more
    if len(candidate_data) < 50:
        more = Case.objects(id__ne=target.id).limit(200)
        more_data = [c.to_json() for c in more]
        seen = {c["id"] for c in candidate_data}
        for c in more_data:
            if c["id"] not in seen:
                candidate_data.append(c)

    if method == "tfidf":
        similar = find_similar_cases(target_data, candidate_data, top_n=limit)
    else:
        similar = find_similar_by_metadata(target_data, candidate_data, top_n=limit)

    return jsonify({
        "case_id": str(target.id),
        "similar_cases": similar,
        "method": method,
    }), 200


@ai_bp.route("/ai/extract-text", methods=["POST"])
def extract_text_entities():
    """Extract entities from arbitrary text (no case required)."""
    data = request.json or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Text is required"}), 400

    extraction = extract_key_information(text)
    summary = generate_summary(text, num_sentences=3) if len(text) > 200 else text

    return jsonify({
        "extraction": extraction,
        "summary": summary,
    }), 200

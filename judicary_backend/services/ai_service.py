"""
AI Service – Munsif AI (Intelligent Legal Assistant)
=====================================================
Powered by Google Gemini API for intelligent legal assistance.
Searches the MongoDB case database for relevant cases and feeds
them as context to Gemini for grounded, accurate responses.
Falls back to a rule-based approach if the API key is missing or
the API call fails.
"""

import os
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Google Gemini client – lazy initialised so the module still loads even
# when the package or API key is not available.
# ---------------------------------------------------------------------------
_gemini_model = None
_gemini_available = False


def _init_gemini():
    """Initialise the Gemini model once."""
    global _gemini_model, _gemini_available
    if _gemini_model is not None:
        return

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        logger.warning("GEMINI_API_KEY not set – Munsif AI will use rule-based fallback")
        _gemini_model = False          # sentinel: tried but not available
        _gemini_available = False
        return

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel(
            "gemini-2.0-flash",
            generation_config={
                "temperature": 0.4,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            },
            system_instruction=(
                "You are Munsif AI, an expert "
                "legal AI assistant specialising in **Pakistani law**. "
                "You provide accurate, well-structured legal guidance, cite relevant "
                "statutes, precedents, and constitutional articles. "
                "When the user writes in Urdu, reply in Urdu. "
                "When court cases are provided as context, reference them by case "
                "number and title. "
                "Always add a disclaimer that your advice does not replace "
                "professional legal counsel. "
                "Format your responses using Markdown: use **bold** for emphasis, "
                "headings (##), and bullet lists."
            ),
        )
        _gemini_available = True
        logger.info("Gemini model initialised successfully (gemini-2.0-flash)")
    except Exception as exc:
        logger.error("Failed to initialise Gemini: %s", exc)
        _gemini_model = False
        _gemini_available = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_language(text: str) -> str:
    """Simple Urdu detection based on Unicode character ranges."""
    urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF' or '\uFB50' <= c <= '\uFDFF')
    return "ur" if urdu_chars > len(text) * 0.3 else "en"


def _build_case_context(cases: list) -> str:
    """Turn a list of case dicts into a compact text block for the prompt."""
    if not cases:
        return ""
    lines = ["### Relevant cases from the database:\n"]
    for i, c in enumerate(cases, 1):
        parts = [
            f"**{i}. {c.get('case_number', 'N/A')}** – {c.get('title', 'Untitled')}",
            f"   Court: {c.get('court', 'N/A')}",
        ]
        if c.get("judge_names"):
            parts.append(f"   Judges: {', '.join(c['judge_names'])}")
        if c.get("cited_statutes"):
            parts.append(f"   Statutes: {', '.join(c['cited_statutes'][:5])}")
        summary = (c.get("summary") or c.get("judgment_text") or "")[:400]
        if summary:
            parts.append(f"   Summary: {summary}")
        lines.append("\n".join(parts))
    return "\n\n".join(lines)


# ---------------------------------------------------------------------------
# Public API – called by routes
# ---------------------------------------------------------------------------

def generate_ai_response(query: str, context_cases=None, language="en",
                         history: list | None = None) -> dict:
    """
    Generate an AI response to a legal query.
    Uses Gemini if available, otherwise falls back to rule-based logic.
    """
    _init_gemini()

    detected_lang = detect_language(query)
    lang = detected_lang if language == "auto" else language

    citations = [c.get("id", "") for c in (context_cases or []) if c.get("id")]

    if _gemini_available and _gemini_model:
        try:
            return _gemini_response(query, context_cases, lang, citations, history)
        except Exception as exc:
            logger.error("Gemini call failed, falling back: %s", exc)

    # ---------- rule-based fallback ----------
    return _rule_based_response(query, context_cases, lang, citations)


def generate_case_analysis(case_data: dict) -> dict:
    """Generate an AI analysis of a specific case via Gemini."""
    _init_gemini()

    if _gemini_available and _gemini_model:
        try:
            return _gemini_case_analysis(case_data)
        except Exception as exc:
            logger.error("Gemini case analysis failed: %s", exc)

    return _rule_based_case_analysis(case_data)


def generate_gemini_summary(text: str, num_sentences: int = 5) -> str:
    """Use Gemini to generate a case summary (called from routes)."""
    _init_gemini()
    if not (_gemini_available and _gemini_model) or not text or len(text) < 50:
        return ""
    try:
        prompt = (
            f"Summarise the following Pakistani court judgment in {num_sentences} "
            "concise bullet points. Focus on the key legal issues, statutes cited, "
            "and the court's decision.\n\n"
            f"{text[:6000]}"
        )
        resp = _gemini_model.generate_content(prompt)
        return resp.text.strip()
    except Exception as exc:
        logger.error("Gemini summary failed: %s", exc)
        return ""


# ---------------------------------------------------------------------------
# Gemini-powered implementations
# ---------------------------------------------------------------------------

def _gemini_response(query, context_cases, lang, citations, history) -> dict:
    """Call Gemini with case context for a grounded answer."""
    parts = []

    # Build message with context
    case_ctx = _build_case_context(context_cases or [])
    if case_ctx:
        parts.append(case_ctx + "\n\n---\n")

    lang_instruction = (
        "Reply in Urdu (اردو) script." if lang == "ur"
        else "Reply in English."
    )
    parts.append(f"[{lang_instruction}]\n\nUser question: {query}")

    # Build Gemini contents (include last N turns for continuity)
    contents = []
    if history:
        for msg in history[-10:]:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [msg.get("content", "")]})

    contents.append({"role": "user", "parts": ["\n".join(parts)]})

    response = _gemini_model.generate_content(contents)
    text = response.text.strip()

    # Extract suggestions from Gemini (look for a "Suggested:" block at end)
    suggestions = _extract_suggestions(text, lang)

    return {
        "response": text,
        "citations": [c for c in citations if c],
        "language": lang,
        "suggestions": suggestions,
    }


def _gemini_case_analysis(case_data: dict) -> dict:
    """Use Gemini to deeply analyse a case."""
    prompt = (
        "Analyse the following Pakistani court case thoroughly. "
        "Provide:\n"
        "1. Case overview\n"
        "2. Key legal issues\n"
        "3. Applicable statutes and precedents\n"
        "4. Observations about the bench and parties\n"
        "5. Potential implications\n\n"
        f"Case number: {case_data.get('case_number', 'N/A')}\n"
        f"Title: {case_data.get('title', 'N/A')}\n"
        f"Court: {case_data.get('court', 'N/A')}\n"
        f"Type: {case_data.get('case_type', 'N/A')}\n"
        f"Status: {case_data.get('status', 'N/A')}\n"
        f"Judges: {', '.join(case_data.get('judge_names', []))}\n"
        f"Appellants: {', '.join(case_data.get('appellants', []))}\n"
        f"Respondents: {', '.join(case_data.get('respondents', []))}\n"
        f"Cited Statutes: {', '.join(case_data.get('cited_statutes', []))}\n"
        f"Summary: {(case_data.get('summary') or case_data.get('judgment_text') or '')[:2000]}\n"
    )

    response = _gemini_model.generate_content(prompt)
    text = response.text.strip()

    return {
        "analysis": text,
        "key_facts": {
            "parties_count": len(case_data.get("appellants", [])) + len(case_data.get("respondents", [])),
            "statutes_cited": len(case_data.get("cited_statutes", [])),
            "cases_cited": len(case_data.get("cited_cases", [])),
            "judges": len(case_data.get("judge_names", [])),
        },
    }


def _extract_suggestions(text: str, lang: str) -> list:
    """Try to pull follow-up suggestions from the response text."""
    defaults_en = [
        "Show me similar cases",
        "What are my legal options?",
        "Explain the relevant statutes",
        "Find a lawyer for this",
    ]
    defaults_ur = [
        "اس موضوع پر مزید بتائیں",
        "متعلقہ مقدمات دکھائیں",
        "قانونی اختیارات کیا ہیں؟",
    ]
    return defaults_ur if lang == "ur" else defaults_en


# ---------------------------------------------------------------------------
# Rule-based fallback (works without API key)
# ---------------------------------------------------------------------------

LEGAL_CONCEPTS = {
    "bail": {
        "en": "Bail is the temporary release of an accused person awaiting trial. Under Pakistan's CrPC, bail can be granted as a right (bailable offenses) or at the court's discretion (non-bailable offenses). Key sections: 496, 497, 498 CrPC.",
        "ur": "ضمانت ایک ملزم شخص کی عارضی رہائی ہے۔ پاکستان کے ضابطہ فوجداری کے تحت ضمانت حق کے طور پر یا عدالت کی صوابدید پر دی جا سکتی ہے۔"
    },
    "habeas corpus": {
        "en": "Habeas Corpus is a constitutional remedy under Article 199 of the Constitution of Pakistan, requiring a person under arrest to be brought before a judge.",
        "ur": "حبس بدن پاکستان کے آئین کے آرٹیکل 199 کے تحت ایک آئینی علاج ہے۔"
    },
    "writ petition": {
        "en": "Under Article 199, High Courts can issue writs: Habeas Corpus, Mandamus, Prohibition, Quo Warranto, and Certiorari.",
        "ur": "آرٹیکل 199 کے تحت ہائی کورٹس رٹ جاری کر سکتی ہیں۔"
    },
    "divorce": {
        "en": "Divorce in Pakistan is governed by the Muslim Family Laws Ordinance, 1961. Talaq must be notified to the Union Council Chairman. Khula allows a wife to seek dissolution through court.",
        "ur": "پاکستان میں طلاق مسلم فیملی لاز آرڈیننس 1961 کے تحت ہے۔"
    },
    "property": {
        "en": "Property disputes are governed by the Transfer of Property Act 1882, Registration Act 1908, and Land Revenue Act 1967.",
        "ur": "جائیداد کے تنازعات ٹرانسفر آف پراپرٹی ایکٹ 1882 کے تحت ہیں۔"
    },
    "murder": {
        "en": "Murder is dealt with under Sections 299-338 PPC. Qisas & Diyat laws provide for retaliation or blood money.",
        "ur": "قتل پاکستان پینل کوڈ کی دفعات 299-338 کے تحت ہے۔"
    },
    "constitutional": {
        "en": "Constitutional law is based on the 1973 Constitution. Fundamental rights are in Articles 8-28. The Supreme Court has original, appellate, and advisory jurisdiction.",
        "ur": "آئینی قانون 1973 کے آئین پاکستان پر مبنی ہے۔"
    },
    "family law": {
        "en": "Family law covers Nikah, Talaq/Khula, maintenance, Hizanat (custody), and inheritance under Muslim Family Laws Ordinance 1961 and Family Courts Act 1964.",
        "ur": "فیملی لاء نکاح، طلاق/خلع، نفقہ، حضانت اور وراثت کا احاطہ کرتا ہے۔"
    },
    "cyber crime": {
        "en": "Cyber crimes are governed by PECA 2016. The FIA has jurisdiction. Covers unauthorized access, stalking, fraud, identity theft.",
        "ur": "سائبر جرائم الیکٹرانک جرائم کی روک تھام ایکٹ 2016 کے تحت ہیں۔"
    },
    "appeal": {
        "en": "Appeals go from District Courts → High Courts → Supreme Court. Governed by CPC and CrPC.",
        "ur": "اپیل ڈسٹرکٹ کورٹ سے ہائی کورٹ اور پھر سپریم کورٹ میں جاتی ہے۔"
    },
}

PAKISTAN_COURTS = {
    "Supreme Court of Pakistan": "Apex court with original, appellate, and advisory jurisdiction (Articles 184-191).",
    "Lahore High Court": "High Court of Punjab, writ jurisdiction under Article 199.",
    "Sindh High Court": "High Court of Sindh with benches in Karachi, Hyderabad, Sukkur.",
    "Islamabad High Court": "High Court for Islamabad Capital Territory (est. 2010).",
    "Peshawar High Court": "High Court of Khyber Pakhtunkhwa.",
    "Balochistan High Court": "High Court of Balochistan, Quetta.",
    "Federal Shariat Court": "Examines whether laws conform to Islamic injunctions.",
}


def _rule_based_response(query, context_cases, lang, citations) -> dict:
    """Generate a response without Gemini using keyword matching."""
    query_lower = query.lower()
    response_parts = []
    suggestions = []

    # Greetings
    greetings = ["hello", "hi", "hey", "good morning", "assalam", "سلام", "ہیلو"]
    if any(g in query_lower for g in greetings):
        if lang == "ur":
            response_parts.append("السلام علیکم! میں منصف AI ہوں، آپ کا AI قانونی معاون۔")
        else:
            response_parts.append("Assalam-u-Alaikum! I am Munsif AI, your AI Legal Assistant. How can I help you today?")
        suggestions = ["Tell me about bail laws", "How does divorce work?", "What is a writ petition?"]
        return {"response": "\n\n".join(response_parts), "citations": [], "language": lang, "suggestions": suggestions}

    # Court info
    for court_name, court_info in PAKISTAN_COURTS.items():
        if court_name.lower() in query_lower:
            response_parts.append(f"🏛️ **{court_name}**\n{court_info}")

    # Legal concepts
    for concept, info in LEGAL_CONCEPTS.items():
        if concept in query_lower:
            response_parts.append(f"📚 **{concept.title()}**\n{info.get(lang, info['en'])}")

    # Database cases
    if context_cases:
        response_parts.append("\n📋 **Related Cases from Database:**")
        for case in context_cases[:5]:
            response_parts.append(f"• **{case.get('case_number', 'N/A')}** – {case.get('title', '')} ({case.get('court', '')})")

    if not response_parts:
        response_parts.append(
            "I can help with Pakistani law queries. Ask me about bail, divorce, property, appeals, "
            "writ petitions, cyber crime, or any legal topic."
        )
        suggestions = ["What are bail laws?", "Tell me about property disputes", "How to file a writ petition?"]

    if not suggestions:
        suggestions = ["Tell me more", "Show related cases", "What are my legal options?"]

    return {"response": "\n\n".join(response_parts), "citations": citations, "language": lang, "suggestions": suggestions}


def _rule_based_case_analysis(case_data: dict) -> dict:
    """Fallback case analysis without Gemini."""
    parts = [
        f"## Case Analysis: {case_data.get('title', 'Unknown')}",
        f"**Court:** {case_data.get('court', 'N/A')}",
        f"**Status:** {(case_data.get('status') or 'unknown').title()}",
    ]
    if case_data.get("case_type"):
        parts.append(f"**Type:** {case_data['case_type']}")
    appellants = case_data.get("appellants", [])
    respondents = case_data.get("respondents", [])
    if appellants:
        parts.append(f"\n### Parties\n**Appellants:** {', '.join(appellants)}")
    if respondents:
        parts.append(f"**Respondents:** {', '.join(respondents)}")
    statutes = case_data.get("cited_statutes", [])
    if statutes:
        parts.append(f"\n### Legal Framework\nReferences {len(statutes)} statutes: {', '.join(statutes[:10])}")
    summary = case_data.get("summary", "")
    if summary:
        parts.append(f"\n### Summary\n{summary[:500]}")
    judges = case_data.get("judge_names", [])
    if judges:
        parts.append(f"\n### Bench\n{len(judges)} judge(s): {', '.join(judges)}")

    return {
        "analysis": "\n".join(parts),
        "key_facts": {
            "parties_count": len(appellants) + len(respondents),
            "statutes_cited": len(statutes),
            "cases_cited": len(case_data.get("cited_cases", [])),
            "judges": len(judges),
        },
    }

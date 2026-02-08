"""
Translation Service – Urdu-English Legal Translation
======================================================
Provides basic translation using dictionary-based approach
with legal terminology support.
"""

import re
import logging

logger = logging.getLogger(__name__)

# ----- Legal terminology dictionary (English -> Urdu) -----
LEGAL_DICT_EN_UR = {
    # Courts
    "supreme court": "سپریم کورٹ",
    "high court": "ہائی کورٹ",
    "district court": "ضلعی عدالت",
    "session court": "سیشن کورٹ",
    "family court": "فیملی کورٹ",
    "civil court": "دیوانی عدالت",
    "criminal court": "فوجداری عدالت",
    "appellate court": "اپیلٹ عدالت",
    "tribunal": "ٹربیونل",

    # Legal terms
    "judgment": "فیصلہ",
    "verdict": "فیصلہ",
    "order": "حکم",
    "decree": "ڈگری",
    "petition": "درخواست",
    "writ petition": "رٹ پٹیشن",
    "appeal": "اپیل",
    "bail": "ضمانت",
    "bail application": "ضمانت کی درخواست",
    "arrest": "گرفتاری",
    "warrant": "وارنٹ",
    "summons": "سمن",
    "notice": "نوٹس",
    "complaint": "شکایت",
    "case": "مقدمہ",
    "suit": "مقدمہ",
    "hearing": "سماعت",
    "trial": "مقدمے کی سماعت",
    "evidence": "ثبوت",
    "witness": "گواہ",
    "testimony": "گواہی",
    "exhibit": "نمائش",
    "affidavit": "حلف نامہ",
    "power of attorney": "مختار نامہ",
    "contract": "معاہدہ",
    "agreement": "معاہدہ",

    # Parties
    "plaintiff": "مدعی",
    "defendant": "مدعا علیہ",
    "appellant": "اپیل کنندہ",
    "respondent": "مجیب",
    "petitioner": "درخواست گزار",
    "accused": "ملزم",
    "complainant": "شکایت کنندہ",
    "advocate": "وکیل",
    "lawyer": "وکیل",
    "judge": "جج",
    "justice": "جسٹس",
    "magistrate": "مجسٹریٹ",

    # Actions
    "dismissed": "خارج",
    "allowed": "منظور",
    "granted": "منظور",
    "denied": "مسترد",
    "adjourned": "ملتوی",
    "disposed": "فیصل",
    "convicted": "مجرم قرار",
    "acquitted": "بری",
    "sentenced": "سزا سنائی",
    "pending": "زیر سماعت",
    "decided": "فیصل شدہ",

    # Legal concepts
    "jurisdiction": "دائرہ اختیار",
    "constitution": "آئین",
    "fundamental rights": "بنیادی حقوق",
    "law": "قانون",
    "statute": "قانون",
    "ordinance": "آرڈیننس",
    "act": "ایکٹ",
    "section": "دفعہ",
    "article": "آرٹیکل",
    "amendment": "ترمیم",
    "provision": "شق",
    "clause": "شق",
    "precedent": "نظیر",
    "habeas corpus": "حق حبس بدن",
    "mandamus": "حکم امتناعی",
    "injunction": "حکم امتناعی",
    "stay order": "قیام حکم",
    "contempt of court": "توہین عدالت",

    # Property
    "property": "جائیداد",
    "land": "زمین",
    "inheritance": "وراثت",
    "ownership": "ملکیت",
    "possession": "قبضہ",
    "transfer": "منتقلی",
    "registration": "رجسٹریشن",
    "mortgage": "رہن",
    "lease": "لیز",
    "rent": "کرایہ",
    "tenant": "کرایہ دار",
    "landlord": "مالک مکان",

    # Family law
    "marriage": "شادی / نکاح",
    "nikah": "نکاح",
    "divorce": "طلاق",
    "talaq": "طلاق",
    "khula": "خلع",
    "maintenance": "نان نفقہ",
    "dower": "حق مہر",
    "custody": "حضانت",
    "guardianship": "سرپرستی",
    "child": "بچہ",

    # Criminal
    "murder": "قتل",
    "theft": "چوری",
    "robbery": "ڈکیتی",
    "fraud": "دھوکہ",
    "forgery": "جعل سازی",
    "defamation": "ہتک عزت",
    "punishment": "سزا",
    "imprisonment": "قید",
    "fine": "جرمانہ",
    "death penalty": "سزائے موت",
    "life imprisonment": "عمر قید",
}

# Build reverse dictionary (Urdu -> English)
LEGAL_DICT_UR_EN = {v: k for k, v in LEGAL_DICT_EN_UR.items()}


def detect_language(text: str) -> str:
    """Detect if text is primarily Urdu or English."""
    urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF' or '\uFB50' <= c <= '\uFDFF')
    return "ur" if urdu_chars > len(text) * 0.3 else "en"


def translate_legal_terms(text: str, source_lang: str = "auto", target_lang: str = "auto") -> dict:
    """
    Translate legal text with terminology-aware translation.
    Uses dictionary-based approach for legal terms.

    Returns:
        dict with 'translated_text', 'source_lang', 'target_lang', 'terms_translated'
    """
    if source_lang == "auto":
        source_lang = detect_language(text)

    if target_lang == "auto":
        target_lang = "ur" if source_lang == "en" else "en"

    dictionary = LEGAL_DICT_EN_UR if source_lang == "en" else LEGAL_DICT_UR_EN
    translated = text
    terms_found = []

    # Sort by length (longer phrases first) to prevent partial replacements
    sorted_terms = sorted(dictionary.items(), key=lambda x: len(x[0]), reverse=True)

    for term, translation in sorted_terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        if pattern.search(translated):
            translated = pattern.sub(f"{translation} ({term})", translated, count=0)
            terms_found.append({"original": term, "translated": translation})

    return {
        "original_text": text,
        "translated_text": translated,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "terms_translated": terms_found,
        "is_partial": True,  # dictionary-based, not full translation
        "note": "Translation uses legal terminology dictionary. For complete translation, please consult a professional translator.",
    }


def get_legal_glossary(language: str = "en") -> list:
    """Return the legal terminology glossary."""
    glossary = []
    for en_term, ur_term in sorted(LEGAL_DICT_EN_UR.items()):
        glossary.append({
            "english": en_term,
            "urdu": ur_term,
        })
    return glossary

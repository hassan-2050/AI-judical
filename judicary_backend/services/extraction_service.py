"""
Extraction Service – Smart Information Extraction (NER)
========================================================
Extracts named entities from legal text using regex patterns
tuned for Pakistani legal documents.
"""

import re
import logging

logger = logging.getLogger(__name__)


# ----- Regex patterns for Pakistani legal entities -----

PATTERNS = {
    "CASE_NUMBER": [
        r'\b(?:PLD|SCMR|CLC|PLC|PLR|PCrLJ|YLR|MLD|NLR|PTD|PTCL)\s*\d{4}\s*\w+\s*\d+',
        r'\b(?:Civil|Criminal|Writ|Constitutional)\s*(?:Appeal|Petition|Misc|Reference|Review)\s*(?:No\.?|#)\s*\d+(?:\s*(?:of|/)\s*\d{4})?',
        r'\b(?:Cr\.?\s*A|C\.?\s*A|W\.?\s*P|Const\.?\s*P)\.?\s*(?:No\.?|#)\s*\d+(?:/\d{4})?',
        r'\b(?:F\.?A|R\.?F\.?A|S\.?A|C\.?R|RSA)\.?\s*(?:No\.?|#)\s*\d+(?:/\d{4})?',
    ],
    "STATUTE": [
        r'\b(?:Pakistan Penal Code|PPC|Cr\.?P\.?C|C\.?P\.?C|Qanun-e-Shahadat)',
        r'\b(?:The\s+)?(?:[\w\s]+(?:Act|Ordinance|Order|Rules|Regulation))\s*,?\s*(?:19|20)\d{2}',
        r'\bArticle\s+\d+(?:\s*\(\d+\))?(?:\s*of\s+the\s+Constitution)?',
        r'\bSection\s+\d+(?:\s*[A-Z])?(?:\s*(?:of|read\s+with)\s+[\w\s]+)?',
        r'\bOrder\s+[IVXLCDM]+\s*,?\s*Rule\s+\d+',
    ],
    "COURT": [
        r'\b(?:Supreme\s+Court\s+of\s+Pakistan|Federal\s+Shariat\s+Court)',
        r'\b(?:Lahore|Sindh|Peshawar|Balochistan|Islamabad)\s+High\s+Court',
        r'\b(?:District|Session|Civil|Family|Banking|Anti[-\s]?Terrorism|Special|Accountability)\s+Court',
        r'\b(?:National\s+Accountability\s+Bureau|NAB)\s+Court',
    ],
    "JUDGE": [
        r'\b(?:Mr\.?\s+)?Justice\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}',
        r'\b(?:Hon(?:ourable|\'ble)\s+)?(?:Chief\s+)?Justice\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}',
        r'\bJ\.\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}',
    ],
    "DATE": [
        r'\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\b',
        r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{4}',
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s*,?\s*\d{4}',
    ],
    "PERSON": [
        r'\b(?:Mr|Mrs|Ms|Mst|Muhammad|Mohammad|Syed|Ch|Rana|Malik|Sardar|Begum|Bibi)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}',
    ],
    "ORGANIZATION": [
        r'\b(?:Government\s+of\s+(?:Pakistan|Punjab|Sindh|KPK|Balochistan))',
        r'\b(?:Federal\s+(?:Government|Board\s+of\s+Revenue))',
        r'\b(?:State\s+Bank\s+of\s+Pakistan|SECP|FBR|NADRA|FIA|NAB)',
        r'\b(?:[\w\s]+(?:Corporation|Authority|Commission|Board|Department|Ministry))\b',
    ],
    "LOCATION": [
        r'\b(?:Islamabad|Lahore|Karachi|Peshawar|Quetta|Rawalpindi|Faisalabad|Multan|Hyderabad|Sialkot|Gujranwala|Abbottabad|Mardan|Sukkur|Bahawalpur)\b',
        r'\b(?:Punjab|Sindh|Khyber\s+Pakhtunkhwa|Balochistan|KPK|AJK|Gilgit[- ]Baltistan)\b',
    ],
    "MONETARY": [
        r'\bRs\.?\s*[\d,]+(?:\.\d{2})?(?:\s*(?:lac|lakh|crore|million|billion))?',
        r'\b\d+(?:,\d{2,3})*\s*(?:rupees|PKR)',
    ],
}


def extract_entities(text: str) -> list:
    """
    Extract named entities from legal text.
    Returns list of dicts: [{"entity_type": "...", "value": "...", "confidence": 0.9}]
    """
    if not text:
        return []

    entities = []
    seen = set()

    for entity_type, patterns in PATTERNS.items():
        for pattern in patterns:
            try:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    value = match.group().strip()
                    # De-duplicate
                    key = (entity_type, value.lower())
                    if key not in seen and len(value) > 2:
                        seen.add(key)
                        entities.append({
                            "entity_type": entity_type,
                            "value": value,
                            "confidence": 0.85,
                        })
            except re.error:
                continue

    # Sort by entity type
    entities.sort(key=lambda e: e["entity_type"])
    return entities


def extract_key_information(text: str) -> dict:
    """
    Extract structured key information from a legal document.
    Returns a comprehensive dict of extracted fields.
    """
    entities = extract_entities(text)

    result = {
        "case_numbers": [],
        "statutes": [],
        "courts": [],
        "judges": [],
        "dates": [],
        "persons": [],
        "organizations": [],
        "locations": [],
        "monetary_values": [],
        "all_entities": entities,
    }

    for e in entities:
        etype = e["entity_type"]
        value = e["value"]
        if etype == "CASE_NUMBER":
            result["case_numbers"].append(value)
        elif etype == "STATUTE":
            result["statutes"].append(value)
        elif etype == "COURT":
            result["courts"].append(value)
        elif etype == "JUDGE":
            result["judges"].append(value)
        elif etype == "DATE":
            result["dates"].append(value)
        elif etype == "PERSON":
            result["persons"].append(value)
        elif etype == "ORGANIZATION":
            result["organizations"].append(value)
        elif etype == "LOCATION":
            result["locations"].append(value)
        elif etype == "MONETARY":
            result["monetary_values"].append(value)

    return result

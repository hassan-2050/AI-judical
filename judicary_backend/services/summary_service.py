"""
Summary Service – Automatic Case Summary Generation
=====================================================
Extractive summarization using sentence scoring based on
keyword frequency, position, and legal term importance.
"""

import re
import logging

logger = logging.getLogger(__name__)

# Legal terms that indicate important sentences
LEGAL_IMPORTANCE_TERMS = {
    "held", "ordered", "directed", "decreed", "dismissed", "allowed",
    "appeal", "petition", "judgment", "verdict", "ruling", "decision",
    "convicted", "acquitted", "sentenced", "penalty", "fine",
    "plaintiff", "defendant", "appellant", "respondent", "petitioner",
    "section", "article", "provision", "statute", "ordinance", "act",
    "court", "bench", "justice", "honor", "tribunal",
    "therefore", "consequently", "accordingly", "hence", "thus",
    "concluded", "observed", "noted", "found", "determined",
    "constitutional", "fundamental", "rights", "jurisdiction",
    "evidence", "witness", "testimony", "exhibit",
    "precedent", "ratio", "obiter", "dictum",
}


def score_sentence(sentence: str, word_freq: dict, position: int, total: int) -> float:
    """Score a sentence for extractive summarization."""
    score = 0.0
    words = re.findall(r'\w+', sentence.lower())
    if not words:
        return 0.0

    # Word frequency score
    freq_score = sum(word_freq.get(w, 0) for w in words) / len(words)
    score += freq_score * 2.0

    # Legal importance terms
    legal_terms = sum(1 for w in words if w in LEGAL_IMPORTANCE_TERMS)
    score += legal_terms * 1.5

    # Position score - first and last sentences are usually important
    if position < 3:
        score += 2.0
    elif position < 6:
        score += 1.0
    if position >= total - 3:
        score += 1.5

    # Length penalty - too short or too long sentences score lower
    if len(words) < 5:
        score *= 0.5
    elif len(words) > 50:
        score *= 0.7

    # Bonus for sentences with key phrases
    sentence_lower = sentence.lower()
    key_phrases = ["the court", "it is held", "we hold", "the appeal", "the petition",
                   "is hereby", "the judgment", "in our opinion", "we are of the view",
                   "is dismissed", "is allowed", "is decreed"]
    if any(kp in sentence_lower for kp in key_phrases):
        score += 3.0

    return score


def generate_summary(text: str, num_sentences: int = 5) -> str:
    """
    Generate an extractive summary of legal text.
    Returns the top N most important sentences.
    """
    if not text or len(text.strip()) < 100:
        return text or ""

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if len(sentences) <= num_sentences:
        return text

    # Build word frequency map
    all_words = re.findall(r'\w+', text.lower())
    word_freq = {}
    for w in all_words:
        if len(w) > 3:  # skip short words
            word_freq[w] = word_freq.get(w, 0) + 1

    # Normalize frequencies
    max_freq = max(word_freq.values()) if word_freq else 1
    word_freq = {w: f / max_freq for w, f in word_freq.items()}

    # Score sentences
    scored = []
    for i, sent in enumerate(sentences):
        score = score_sentence(sent, word_freq, i, len(sentences))
        scored.append((i, sent, score))

    # Select top sentences, maintain original order
    scored.sort(key=lambda x: x[2], reverse=True)
    selected = sorted(scored[:num_sentences], key=lambda x: x[0])

    summary = " ".join(s[1] for s in selected)
    return summary


def generate_headnotes(text: str, max_points: int = 5) -> list:
    """
    Extract key legal headnotes from judgment text.
    Returns list of key points.
    """
    if not text:
        return []

    sentences = re.split(r'(?<=[.!?])\s+', text)
    headnote_patterns = [
        r'(?:held|ordered|directed|decreed)\s+that',
        r'(?:the court|this court|we)\s+(?:held|observed|noted|found)',
        r'(?:it is|it was)\s+(?:held|ordered|directed)',
        r'(?:the (?:appeal|petition|application))\s+(?:is|was)\s+(?:dismissed|allowed|disposed)',
        r'(?:per\s+curiam|ratio\s+decidendi)',
    ]

    headnotes = []
    for sent in sentences:
        sent_lower = sent.lower()
        for pattern in headnote_patterns:
            if re.search(pattern, sent_lower):
                # Clean and truncate
                clean_sent = sent.strip()
                if len(clean_sent) > 200:
                    clean_sent = clean_sent[:200] + "..."
                if clean_sent not in headnotes:
                    headnotes.append(clean_sent)
                break

        if len(headnotes) >= max_points:
            break

    return headnotes

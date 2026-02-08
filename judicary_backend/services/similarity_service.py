"""
Similarity Service – Find Similar Cases
=========================================
Uses TF-IDF cosine similarity to find cases similar to a given case.
Works with the existing MongoDB case collection.
"""

import re
import math
import logging
from collections import Counter

logger = logging.getLogger(__name__)


# ----- Stop words for legal text -----
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "this", "that",
    "these", "those", "it", "its", "not", "no", "nor", "as", "if", "than",
    "so", "such", "each", "every", "all", "both", "few", "more", "most",
    "other", "some", "any", "only", "own", "same", "very", "just", "also",
    "into", "about", "between", "through", "during", "before", "after",
    "above", "below", "under", "over", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "what", "which", "who",
    "whom", "up", "out", "off", "down", "they", "them", "their", "he",
    "him", "his", "she", "her", "we", "us", "our", "you", "your", "i", "me",
    "my", "said", "upon", "per", "mr", "mrs", "ms", "vs", "versus",
}


def tokenize(text: str) -> list:
    """Tokenize and clean text for TF-IDF."""
    if not text:
        return []
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    return [w for w in words if w not in STOP_WORDS]


def compute_tf(tokens: list) -> dict:
    """Compute term frequency."""
    counts = Counter(tokens)
    total = len(tokens) if tokens else 1
    return {word: count / total for word, count in counts.items()}


def compute_idf(documents_tokens: list) -> dict:
    """Compute inverse document frequency."""
    n = len(documents_tokens)
    if n == 0:
        return {}

    doc_freq = Counter()
    for tokens in documents_tokens:
        unique_tokens = set(tokens)
        for token in unique_tokens:
            doc_freq[token] += 1

    return {word: math.log(n / (df + 1)) + 1 for word, df in doc_freq.items()}


def compute_tfidf(tf: dict, idf: dict) -> dict:
    """Compute TF-IDF vector."""
    return {word: tf_val * idf.get(word, 0) for word, tf_val in tf.items()}


def cosine_similarity(vec1: dict, vec2: dict) -> float:
    """Compute cosine similarity between two TF-IDF vectors."""
    # Find common terms
    common = set(vec1.keys()) & set(vec2.keys())
    if not common:
        return 0.0

    dot_product = sum(vec1[t] * vec2[t] for t in common)
    mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

    if mag1 == 0 or mag2 == 0:
        return 0.0

    return dot_product / (mag1 * mag2)


def find_similar_cases(target_case: dict, candidate_cases: list, top_n: int = 10) -> list:
    """
    Find the most similar cases to a target case.

    Args:
        target_case: dict with 'title', 'summary', 'full_text', etc.
        candidate_cases: list of case dicts to compare against
        top_n: number of similar cases to return

    Returns:
        list of dicts with case info and similarity score
    """
    # Build target text
    target_text = " ".join(filter(None, [
        target_case.get("title", ""),
        target_case.get("summary", ""),
        target_case.get("case_type", ""),
        " ".join(target_case.get("cited_statutes", [])),
        " ".join(target_case.get("categories", [])),
    ]))
    target_tokens = tokenize(target_text)

    if not target_tokens:
        return []

    # Build candidate texts
    all_tokens = [target_tokens]
    candidate_texts = []
    for case in candidate_cases:
        text = " ".join(filter(None, [
            case.get("title", ""),
            case.get("summary", ""),
            case.get("case_type", ""),
            " ".join(case.get("cited_statutes", []) if case.get("cited_statutes") else []),
            " ".join(case.get("categories", []) if case.get("categories") else []),
        ]))
        tokens = tokenize(text)
        all_tokens.append(tokens)
        candidate_texts.append(tokens)

    # Compute IDF across all documents
    idf = compute_idf(all_tokens)

    # Compute target TF-IDF
    target_tf = compute_tf(target_tokens)
    target_tfidf = compute_tfidf(target_tf, idf)

    # Compute similarities
    results = []
    for i, (case, tokens) in enumerate(zip(candidate_cases, candidate_texts)):
        if str(case.get("id", "")) == str(target_case.get("id", "")) and target_case.get("id"):
            continue  # skip self

        candidate_tf = compute_tf(tokens)
        candidate_tfidf = compute_tfidf(candidate_tf, idf)
        sim = cosine_similarity(target_tfidf, candidate_tfidf)

        if sim > 0.01:  # minimum threshold
            results.append({
                "id": str(case.get("id", "")),
                "case_number": case.get("case_number", ""),
                "title": case.get("title", ""),
                "court": case.get("court", ""),
                "year": case.get("year"),
                "similarity": round(sim, 4),
            })

    # Sort by similarity descending
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_n]


def find_similar_by_metadata(target_case: dict, candidate_cases: list, top_n: int = 10) -> list:
    """
    Find similar cases using metadata matching (court, type, statutes, judges).
    Faster than TF-IDF but less nuanced.
    """
    target_court = (target_case.get("court") or "").lower()
    target_type = (target_case.get("case_type") or "").lower()
    target_statutes = set(s.lower() for s in (target_case.get("cited_statutes") or []))
    target_judges = set(j.lower() for j in (target_case.get("judge_names") or []))
    target_categories = set(c.lower() for c in (target_case.get("categories") or []))

    results = []
    for case in candidate_cases:
        if str(case.get("id", "")) == str(target_case.get("id", "")) and target_case.get("id"):
            continue

        score = 0.0
        # Court match
        if target_court and (case.get("court") or "").lower() == target_court:
            score += 2.0
        # Type match
        if target_type and (case.get("case_type") or "").lower() == target_type:
            score += 3.0
        # Statute overlap
        case_statutes = set(s.lower() for s in (case.get("cited_statutes") or []))
        statute_overlap = len(target_statutes & case_statutes)
        score += statute_overlap * 2.0
        # Judge overlap
        case_judges = set(j.lower() for j in (case.get("judge_names") or []))
        score += len(target_judges & case_judges) * 1.0
        # Category overlap
        case_cats = set(c.lower() for c in (case.get("categories") or []))
        score += len(target_categories & case_cats) * 1.5

        if score > 0:
            results.append({
                "id": str(case.get("id", "")),
                "case_number": case.get("case_number", ""),
                "title": case.get("title", ""),
                "court": case.get("court", ""),
                "year": case.get("year"),
                "similarity": round(min(score / 10.0, 1.0), 4),
            })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_n]

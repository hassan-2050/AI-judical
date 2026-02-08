"""Search routes – full-text and advanced filtering."""

from flask import Blueprint, request, jsonify
from mongoengine.queryset.visitor import Q

from models.case_model import Case

search_bp = Blueprint("search", __name__)


@search_bp.route("/search", methods=["GET"])
def search_cases():
    """
    Advanced case search with multiple parameters.
    Query params: q, court, judge, year_from, year_to, case_type, status, page, page_size
    """
    q = request.args.get("q", "").strip()
    court = request.args.get("court", "").strip()
    judge = request.args.get("judge", "").strip()
    year_from = request.args.get("year_from", type=int)
    year_to = request.args.get("year_to", type=int)
    case_type = request.args.get("case_type", "").strip()
    status = request.args.get("status", "").strip()
    appellant = request.args.get("appellant", "").strip()
    respondent = request.args.get("respondent", "").strip()
    statute = request.args.get("statute", "").strip()
    page = int(request.args.get("page", 1))
    page_size = min(int(request.args.get("page_size", 20)), 100)
    sort = request.args.get("sort", "-judgment_date")

    query = Q()

    # Full-text search on multiple fields
    if q and len(q) >= 2:
        text_q = (
            Q(title__icontains=q)
            | Q(summary__icontains=q)
            | Q(case_number__icontains=q)
            | Q(full_text__icontains=q)
            | Q(headnotes__icontains=q)
        )
        query &= text_q

    if court:
        query &= Q(court__icontains=court)

    if judge:
        query &= Q(judge_names__icontains=judge)

    if year_from:
        query &= Q(year__gte=year_from)

    if year_to:
        query &= Q(year__lte=year_to)

    if case_type:
        query &= Q(case_type__iexact=case_type)

    if status:
        query &= Q(status=status)

    if appellant:
        query &= Q(appellants__icontains=appellant)

    if respondent:
        query &= Q(respondents__icontains=respondent)

    if statute:
        query &= Q(cited_statutes__icontains=statute)

    total = Case.objects(query).count()
    cases = (
        Case.objects(query)
        .order_by(sort)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )

    return jsonify({
        "results": [c.to_card_json() for c in cases],
        "query": {
            "q": q,
            "court": court,
            "judge": judge,
            "year_from": year_from,
            "year_to": year_to,
            "case_type": case_type,
            "status": status,
        },
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }), 200


@search_bp.route("/search/filters", methods=["GET"])
def search_filters():
    """Return available filter values for the search interface."""
    # Distinct courts
    courts = Case.objects.distinct("court")
    courts = [c for c in courts if c]

    # Distinct case types
    case_types = Case.objects.distinct("case_type")
    case_types = [t for t in case_types if t]

    # Distinct statuses
    statuses = Case.objects.distinct("status")
    statuses = [s for s in statuses if s]

    # Year range
    year_pipeline = [
        {"$match": {"year": {"$ne": None}}},
        {"$group": {
            "_id": None,
            "min_year": {"$min": "$year"},
            "max_year": {"$max": "$year"},
        }},
    ]
    year_result = list(Case.objects.aggregate(*year_pipeline))

    # Top judges
    judge_pipeline = [
        {"$unwind": "$judge_names"},
        {"$group": {"_id": "$judge_names", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 50},
    ]
    judges = list(Case.objects.aggregate(*judge_pipeline))

    # Sources
    sources = Case.objects.distinct("source")
    sources = [s for s in sources if s]

    return jsonify({
        "courts": sorted(courts),
        "case_types": sorted(case_types),
        "statuses": statuses,
        "year_range": {
            "min": year_result[0]["min_year"] if year_result else None,
            "max": year_result[0]["max_year"] if year_result else None,
        },
        "judges": [{"name": j["_id"], "count": j["count"]} for j in judges],
        "sources": sources,
    }), 200


@search_bp.route("/search/suggest", methods=["GET"])
def search_suggest():
    """Return search suggestions / autocomplete based on partial query."""
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify({"suggestions": []}), 200

    # Search case numbers and titles
    cases = Case.objects(
        Q(case_number__icontains=q) | Q(title__icontains=q)
    ).only("case_number", "title", "court").limit(10)

    suggestions = []
    for c in cases:
        suggestions.append({
            "id": str(c.id),
            "case_number": c.case_number,
            "title": c.title[:100],
            "court": c.court,
        })

    return jsonify({"suggestions": suggestions}), 200

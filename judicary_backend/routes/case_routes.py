"""Case CRUD routes – list, detail, create, update, delete."""

from datetime import datetime

import bson
from flask import Blueprint, request, jsonify, g
from mongoengine.queryset.visitor import Q

from models.case_model import Case
from routes.auth_routes import token_required

case_bp = Blueprint("cases", __name__)


@case_bp.route("/cases", methods=["GET"])
def list_cases():
    """List cases with pagination, filtering, and search."""
    page = int(request.args.get("page", 1))
    page_size = min(int(request.args.get("page_size", 20)), 100)
    sort = request.args.get("sort", "-judgment_date")

    query = Q()

    # Text search
    search = request.args.get("search", "").strip()
    if search and len(search) >= 2:
        query &= Q(title__icontains=search) | Q(summary__icontains=search) | Q(case_number__icontains=search)

    # Filters
    court = request.args.get("court")
    if court:
        query &= Q(court__icontains=court)

    case_type = request.args.get("case_type")
    if case_type:
        query &= Q(case_type__iexact=case_type)

    year = request.args.get("year")
    if year:
        query &= Q(year=int(year))

    status = request.args.get("status")
    if status:
        query &= Q(status=status)

    judge = request.args.get("judge")
    if judge:
        query &= Q(judge_names__icontains=judge)

    source = request.args.get("source")
    if source:
        query &= Q(source=source)

    # Execute with pagination
    total = Case.objects(query).count()
    cases = (
        Case.objects(query)
        .order_by(sort)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )

    return jsonify({
        "cases": [c.to_card_json() for c in cases],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }), 200


@case_bp.route("/cases/<case_id>", methods=["GET"])
def get_case(case_id):
    """Get full case details."""
    if not bson.ObjectId.is_valid(case_id):
        return jsonify({"error": "Invalid case ID"}), 400

    case = Case.objects(id=case_id).first()
    if not case:
        return jsonify({"error": "Case not found"}), 404

    return jsonify({"case": case.to_json()}), 200


@case_bp.route("/cases", methods=["POST"])
@token_required
def create_case():
    """Create a new case (manual entry)."""
    data = request.json or {}

    required = ["case_number", "title", "court"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    case = Case(
        case_number=data["case_number"],
        title=data["title"],
        court=data["court"],
        bench=data.get("bench"),
        case_type=data.get("case_type"),
        year=data.get("year"),
        status=data.get("status", "unknown"),
        appellants=data.get("appellants", []),
        respondents=data.get("respondents", []),
        judge_names=data.get("judge_names", []),
        summary=data.get("summary", ""),
        full_text=data.get("full_text", ""),
        judgment_text=data.get("judgment_text", ""),
        headnotes=data.get("headnotes", ""),
        cited_cases=data.get("cited_cases", []),
        cited_statutes=data.get("cited_statutes", []),
        cited_articles=data.get("cited_articles", []),
        locations=data.get("locations", []),
        categories=data.get("categories", []),
        tags=data.get("tags", []),
        source_url=data.get("source_url"),
        pdf_url=data.get("pdf_url"),
        source="manual",
    )

    # Parse dates
    if data.get("judgment_date"):
        try:
            case.judgment_date = datetime.fromisoformat(data["judgment_date"])
        except ValueError:
            pass

    if data.get("filing_date"):
        try:
            case.filing_date = datetime.fromisoformat(data["filing_date"])
        except ValueError:
            pass

    case.save()

    return jsonify({"message": "Case created", "case": case.to_json()}), 201


@case_bp.route("/cases/<case_id>", methods=["PUT"])
@token_required
def update_case(case_id):
    """Update an existing case."""
    if not bson.ObjectId.is_valid(case_id):
        return jsonify({"error": "Invalid case ID"}), 400

    case = Case.objects(id=case_id).first()
    if not case:
        return jsonify({"error": "Case not found"}), 404

    data = request.json or {}
    updatable = [
        "title", "court", "bench", "case_type", "year", "status",
        "appellants", "respondents", "judge_names", "summary", "full_text",
        "judgment_text", "headnotes", "cited_cases", "cited_statutes",
        "cited_articles", "locations", "categories", "tags",
        "source_url", "pdf_url",
    ]

    for field in updatable:
        if field in data:
            setattr(case, field, data[field])

    case.updated_at = datetime.utcnow()
    case.save()

    return jsonify({"message": "Case updated", "case": case.to_json()}), 200


@case_bp.route("/cases/<case_id>", methods=["DELETE"])
@token_required
def delete_case(case_id):
    """Delete a case."""
    if not bson.ObjectId.is_valid(case_id):
        return jsonify({"error": "Invalid case ID"}), 400

    case = Case.objects(id=case_id).first()
    if not case:
        return jsonify({"error": "Case not found"}), 404

    case.delete()
    return jsonify({"message": "Case deleted"}), 200


@case_bp.route("/cases/stats", methods=["GET"])
def case_stats():
    """Get aggregate statistics about cases."""
    pipeline = [
        {"$group": {
            "_id": None,
            "total_cases": {"$sum": 1},
            "courts": {"$addToSet": "$court"},
            "years": {"$addToSet": "$year"},
        }},
    ]
    result = list(Case.objects.aggregate(*pipeline))

    # Court distribution
    court_pipeline = [
        {"$group": {"_id": "$court", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20},
    ]
    court_dist = list(Case.objects.aggregate(*court_pipeline))

    # Year distribution
    year_pipeline = [
        {"$match": {"year": {"$ne": None}}},
        {"$group": {"_id": "$year", "count": {"$sum": 1}}},
        {"$sort": {"_id": -1}},
        {"$limit": 30},
    ]
    year_dist = list(Case.objects.aggregate(*year_pipeline))

    # Status distribution
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    status_dist = list(Case.objects.aggregate(*status_pipeline))

    # Source distribution
    source_pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
    ]
    source_dist = list(Case.objects.aggregate(*source_pipeline))

    return jsonify({
        "total_cases": result[0]["total_cases"] if result else 0,
        "total_courts": len(result[0]["courts"]) if result else 0,
        "court_distribution": [
            {"court": d["_id"], "count": d["count"]} for d in court_dist
        ],
        "year_distribution": [
            {"year": d["_id"], "count": d["count"]} for d in year_dist
        ],
        "status_distribution": [
            {"status": d["_id"] or "unknown", "count": d["count"]} for d in status_dist
        ],
        "source_distribution": [
            {"source": d["_id"] or "unknown", "count": d["count"]} for d in source_dist
        ],
    }), 200

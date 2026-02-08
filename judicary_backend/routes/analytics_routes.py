"""Analytics routes – dashboard stats and data for charts."""

from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify

from models.case_model import Case
from models.scrape_job import ScrapeJob

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics/dashboard", methods=["GET"])
def dashboard_stats():
    """Primary dashboard data."""
    total_cases = Case.objects.count()

    # Recent 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_cases = Case.objects(created_at__gte=thirty_days_ago).count()

    # Courts count
    courts = Case.objects.distinct("court")
    total_courts = len([c for c in courts if c])

    # Scraper stats
    total_jobs = ScrapeJob.objects.count()
    completed_jobs = ScrapeJob.objects(status="completed").count()
    failed_jobs = ScrapeJob.objects(status="failed").count()

    # Latest job
    latest_job = ScrapeJob.objects.order_by("-created_at").first()

    # Cases by source
    source_pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    by_source = list(Case.objects.aggregate(*source_pipeline))

    return jsonify({
        "total_cases": total_cases,
        "recent_cases_30d": recent_cases,
        "total_courts": total_courts,
        "scraper": {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "latest_job": latest_job.to_json() if latest_job else None,
        },
        "cases_by_source": [
            {"source": d["_id"] or "unknown", "count": d["count"]}
            for d in by_source
        ],
    }), 200


@analytics_bp.route("/analytics/timeline", methods=["GET"])
def case_timeline():
    """Cases grouped by month for a timeline chart."""
    year = request.args.get("year", type=int, default=datetime.now().year)

    pipeline = [
        {"$match": {"year": year, "judgment_date": {"$ne": None}}},
        {"$group": {
            "_id": {"$month": "$judgment_date"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    monthly = list(Case.objects.aggregate(*pipeline))

    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]
    month_map = {d["_id"]: d["count"] for d in monthly}
    timeline = [
        {"month": months[i], "count": month_map.get(i + 1, 0)}
        for i in range(12)
    ]

    return jsonify({"year": year, "timeline": timeline}), 200


@analytics_bp.route("/analytics/courts", methods=["GET"])
def court_analytics():
    """Court-level analytics with proper status breakdown."""
    pipeline = [
        {"$group": {
            "_id": "$court",
            "total_cases": {"$sum": 1},
            "decided": {"$sum": {"$cond": [{"$eq": ["$status", "decided"]}, 1, 0]}},
            "pending": {"$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}},
            "adjourned": {"$sum": {"$cond": [{"$eq": ["$status", "adjourned"]}, 1, 0]}},
            "disposed": {"$sum": {"$cond": [{"$eq": ["$status", "disposed"]}, 1, 0]}},
            "enacted": {"$sum": {"$cond": [{"$eq": ["$status", "enacted"]}, 1, 0]}},
            "unknown": {"$sum": {"$cond": [{"$eq": ["$status", "unknown"]}, 1, 0]}},
        }},
        {"$sort": {"total_cases": -1}},
    ]
    courts = list(Case.objects.aggregate(*pipeline))

    return jsonify({
        "courts": [
            {
                "name": c["_id"] or "Unknown",
                "total_cases": c["total_cases"],
                "decided": c["decided"],
                "pending": c["pending"],
                "adjourned": c.get("adjourned", 0),
                "disposed": c.get("disposed", 0),
                "enacted": c.get("enacted", 0),
                "unknown": c.get("unknown", 0),
            }
            for c in courts
        ]
    }), 200


@analytics_bp.route("/analytics/judges", methods=["GET"])
def judge_analytics():
    """Top judges by case count."""
    limit = min(int(request.args.get("limit", 20)), 100)

    pipeline = [
        {"$unwind": "$judge_names"},
        {"$group": {"_id": "$judge_names", "case_count": {"$sum": 1}}},
        {"$sort": {"case_count": -1}},
        {"$limit": limit},
    ]
    judges = list(Case.objects.aggregate(*pipeline))

    return jsonify({
        "judges": [
            {"name": j["_id"], "case_count": j["case_count"]}
            for j in judges
        ]
    }), 200

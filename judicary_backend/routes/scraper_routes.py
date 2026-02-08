"""Scraper management routes – trigger, status, history."""

from flask import Blueprint, request, jsonify

from models.scrape_job import ScrapeJob
from scrapers.scheduler import ScraperScheduler, SCRAPER_REGISTRY
from routes.auth_routes import token_required

scraper_bp = Blueprint("scraper", __name__)

# Global scheduler instance (initialized in app.py)
scheduler = None


def init_scheduler(app_config=None):
    """Initialize the global scheduler. Called from app.py."""
    global scheduler
    scheduler = ScraperScheduler(app_config)
    return scheduler


@scraper_bp.route("/scraper/run", methods=["POST"])
@token_required
def run_scraper():
    """Trigger a scraper manually."""
    data = request.json or {}
    scraper_name = data.get("scraper")

    if not scraper_name:
        return jsonify({"error": "Scraper name is required"}), 400

    if scraper_name not in SCRAPER_REGISTRY:
        return jsonify({
            "error": f"Unknown scraper: {scraper_name}",
            "available": list(SCRAPER_REGISTRY.keys()),
        }), 400

    kwargs = {
        "max_pages": data.get("max_pages", 10),
        "year": data.get("year"),
        "court": data.get("court"),
        "scrape_type": data.get("scrape_type"),
    }
    # Remove None values
    kwargs = {k: v for k, v in kwargs.items() if v is not None}

    if scheduler is None:
        return jsonify({"error": "Scheduler not initialized"}), 500

    job, error = scheduler.run_now(scraper_name, **kwargs)
    if error:
        return jsonify({"error": error}), 409

    return jsonify({
        "message": f"Scraper '{scraper_name}' started",
        "job_id": str(job.id),
    }), 202


@scraper_bp.route("/scraper/status", methods=["GET"])
@token_required
def scraper_status():
    """Get overall scraper status."""
    if scheduler is None:
        return jsonify({"error": "Scheduler not initialized"}), 500

    return jsonify(scheduler.get_status()), 200


@scraper_bp.route("/scraper/jobs", methods=["GET"])
@token_required
def list_jobs():
    """List scraping job history with pagination."""
    page = int(request.args.get("page", 1))
    page_size = min(int(request.args.get("page_size", 20)), 50)
    source = request.args.get("source")
    status = request.args.get("status")

    query = ScrapeJob.objects
    if source:
        query = query.filter(source=source)
    if status:
        query = query.filter(status=status)

    total = query.count()
    jobs = (
        query.order_by("-created_at")
        .skip((page - 1) * page_size)
        .limit(page_size)
    )

    return jsonify({
        "jobs": [j.to_json() for j in jobs],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }), 200


@scraper_bp.route("/scraper/jobs/<job_id>", methods=["GET"])
@token_required
def get_job(job_id):
    """Get details of a specific scraping job."""
    job = ScrapeJob.objects(id=job_id).first()
    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({"job": job.to_json()}), 200


@scraper_bp.route("/scraper/available", methods=["GET"])
def available_scrapers():
    """List available scrapers (public endpoint)."""
    return jsonify({
        "scrapers": [
            {"name": name, "description": cls.__doc__ or name}
            for name, cls in SCRAPER_REGISTRY.items()
        ]
    }), 200

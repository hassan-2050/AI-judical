"""
Lawyer Routes – Lawyer directory CRUD API.
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, g

from models.lawyer_model import Lawyer, LawyerReview
from routes.auth_routes import token_required

logger = logging.getLogger(__name__)

lawyer_bp = Blueprint("lawyers", __name__)

# ----- Seed sample lawyers on first request -----
_lawyers_seeded = False


def seed_lawyers():
    """Create sample lawyers if none exist."""
    global _lawyers_seeded
    if _lawyers_seeded:
        return
    _lawyers_seeded = True

    if Lawyer.objects.count() > 0:
        return

    samples = [
        {"name": "Adv. Ahmed Khan", "title": "Senior Advocate", "city": "Lahore", "province": "Punjab",
         "court": "Lahore High Court", "bar_council": "Punjab Bar Council", "experience_years": 15,
         "specializations": ["Constitutional Law", "Criminal Law", "Civil Litigation"],
         "bio": "Senior Advocate practicing in Lahore High Court with 15+ years experience in constitutional and criminal matters.", "is_verified": True, "avg_rating": 4.5, "total_reviews": 12},
        {"name": "Adv. Fatima Zahra", "title": "Advocate High Court", "city": "Islamabad", "province": "ICT",
         "court": "Islamabad High Court", "bar_council": "Islamabad Bar Council", "experience_years": 8,
         "specializations": ["Family Law", "Civil Rights", "Women's Rights"],
         "bio": "Specializing in family law and women's rights cases. Active member of legal aid society.", "is_verified": True, "avg_rating": 4.8, "total_reviews": 20},
        {"name": "Adv. Muhammad Rashid", "title": "Advocate Supreme Court", "city": "Islamabad", "province": "ICT",
         "court": "Supreme Court of Pakistan", "bar_council": "Supreme Court Bar Association", "experience_years": 25,
         "specializations": ["Constitutional Law", "Corporate Law", "Banking Law"],
         "bio": "Advocate Supreme Court with 25 years of practice. Former additional AG.", "is_verified": True, "avg_rating": 4.9, "total_reviews": 35},
        {"name": "Adv. Sara Malik", "title": "Advocate", "city": "Karachi", "province": "Sindh",
         "court": "Sindh High Court", "bar_council": "Sindh Bar Council", "experience_years": 6,
         "specializations": ["Cyber Law", "Intellectual Property", "Corporate Law"],
         "bio": "Young dynamic lawyer specializing in cyber law and IT-related cases.", "is_verified": True, "avg_rating": 4.3, "total_reviews": 8},
        {"name": "Adv. Imran Siddiqui", "title": "Senior Advocate", "city": "Peshawar", "province": "KPK",
         "court": "Peshawar High Court", "bar_council": "KPK Bar Council", "experience_years": 20,
         "specializations": ["Criminal Law", "Land & Property", "Revenue Law"],
         "bio": "Veteran criminal lawyer with extensive experience in land and property disputes.", "is_verified": True, "avg_rating": 4.6, "total_reviews": 18},
        {"name": "Adv. Nadia Hussain", "title": "Advocate", "city": "Lahore", "province": "Punjab",
         "court": "Lahore High Court", "bar_council": "Punjab Bar Council", "experience_years": 10,
         "specializations": ["Tax Law", "Corporate Governance", "Commercial Law"],
         "bio": "Expert in taxation matters and corporate governance. Represents major corporations.", "is_verified": True, "avg_rating": 4.4, "total_reviews": 15},
        {"name": "Adv. Ali Hassan", "title": "Advocate", "city": "Quetta", "province": "Balochistan",
         "court": "Balochistan High Court", "bar_council": "Balochistan Bar Council", "experience_years": 12,
         "specializations": ["Human Rights", "Constitutional Law", "Criminal Defense"],
         "bio": "Dedicated to human rights advocacy and constitutional petitions.", "is_verified": True, "avg_rating": 4.7, "total_reviews": 10},
        {"name": "Adv. Zainab Bibi", "title": "Advocate", "city": "Multan", "province": "Punjab",
         "court": "District Court", "bar_council": "Punjab Bar Council", "experience_years": 5,
         "specializations": ["Family Law", "Child Custody", "Domestic Violence"],
         "bio": "Passionate about family law and protecting the rights of women and children.", "is_verified": False, "avg_rating": 4.2, "total_reviews": 6},
    ]

    for data in samples:
        try:
            lawyer = Lawyer(**data)
            lawyer.save()
        except Exception as e:
            logger.error("Failed to seed lawyer: %s", e)


@lawyer_bp.route("/lawyers", methods=["GET"])
def list_lawyers():
    """List lawyers with optional filters."""
    seed_lawyers()

    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    city = request.args.get("city")
    specialization = request.args.get("specialization")
    court = request.args.get("court")
    search = request.args.get("q")

    query = Lawyer.objects(is_active=True)
    if city:
        query = query.filter(city__icontains=city)
    if specialization:
        query = query.filter(specializations__icontains=specialization)
    if court:
        query = query.filter(court__icontains=court)
    if search:
        query = query.filter(name__icontains=search)

    total = query.count()
    lawyers = query.order_by("-avg_rating").skip((page - 1) * page_size).limit(page_size)

    return jsonify({
        "lawyers": [l.to_card() for l in lawyers],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }), 200


@lawyer_bp.route("/lawyers/<lawyer_id>", methods=["GET"])
def get_lawyer(lawyer_id):
    """Get lawyer details."""
    seed_lawyers()
    try:
        lawyer = Lawyer.objects(id=lawyer_id).first()
    except Exception:
        return jsonify({"error": "Invalid lawyer ID"}), 400

    if not lawyer:
        return jsonify({"error": "Lawyer not found"}), 404

    return jsonify({"lawyer": lawyer.to_json()}), 200


@lawyer_bp.route("/lawyers/<lawyer_id>/review", methods=["POST"])
@token_required
def add_review(lawyer_id):
    """Add a review for a lawyer."""
    try:
        lawyer = Lawyer.objects(id=lawyer_id).first()
    except Exception:
        return jsonify({"error": "Invalid lawyer ID"}), 400

    if not lawyer:
        return jsonify({"error": "Lawyer not found"}), 404

    data = request.json or {}
    rating = data.get("rating")
    comment = data.get("comment", "")

    if not rating or not (1 <= int(rating) <= 5):
        return jsonify({"error": "Rating must be between 1 and 5"}), 400

    review = LawyerReview(
        user_id=g.current_user.id,
        rating=int(rating),
        comment=comment,
    )
    lawyer.reviews.append(review)
    lawyer.total_reviews = len(lawyer.reviews)
    lawyer.avg_rating = sum(r.rating for r in lawyer.reviews) / lawyer.total_reviews
    lawyer.save()

    return jsonify({"message": "Review added", "avg_rating": lawyer.avg_rating}), 201


@lawyer_bp.route("/lawyers/specializations", methods=["GET"])
def list_specializations():
    """List all available specializations."""
    seed_lawyers()
    specs = Lawyer.objects.distinct("specializations")
    return jsonify({"specializations": sorted(specs)}), 200


@lawyer_bp.route("/lawyers/cities", methods=["GET"])
def list_cities():
    """List all cities where lawyers are available."""
    seed_lawyers()
    cities = Lawyer.objects.distinct("city")
    return jsonify({"cities": sorted([c for c in cities if c])}), 200

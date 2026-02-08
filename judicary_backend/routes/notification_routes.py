"""
Notification Routes – Hearing reminders and notification management.
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, g

from models.notification_model import Notification
from routes.auth_routes import token_required

logger = logging.getLogger(__name__)

notification_bp = Blueprint("notifications", __name__)


@notification_bp.route("/notifications", methods=["GET"])
@token_required
def list_notifications():
    """List notifications for the current user."""
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 20, type=int)
    unread_only = request.args.get("unread_only", "false").lower() == "true"

    query = Notification.objects(user_id=g.current_user.id)
    if unread_only:
        query = query.filter(is_read=False)

    total = query.count()
    unread_count = Notification.objects(user_id=g.current_user.id, is_read=False).count()
    notifications = query.order_by("-created_at").skip((page - 1) * page_size).limit(page_size)

    return jsonify({
        "notifications": [n.to_json() for n in notifications],
        "unread_count": unread_count,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size,
        },
    }), 200


@notification_bp.route("/notifications", methods=["POST"])
@token_required
def create_notification():
    """Create a hearing reminder or notification."""
    data = request.json or {}
    title = data.get("title", "").strip()
    message = data.get("message", "").strip()

    if not title or not message:
        return jsonify({"error": "Title and message are required"}), 400

    notif = Notification(
        user_id=g.current_user.id,
        title=title,
        message=message,
        notification_type=data.get("notification_type", "hearing_reminder"),
        case_number=data.get("case_number"),
        is_recurring=data.get("is_recurring", False),
        recurrence_days=data.get("recurrence_days"),
    )

    # Parse case_id
    case_id = data.get("case_id")
    if case_id:
        try:
            from bson import ObjectId
            notif.case_id = ObjectId(case_id)
        except Exception:
            pass

    # Parse reminder date
    reminder_date = data.get("reminder_date")
    if reminder_date:
        try:
            notif.reminder_date = datetime.fromisoformat(reminder_date.replace("Z", "+00:00"))
        except Exception:
            pass

    notif.save()

    return jsonify({
        "message": "Notification created",
        "notification": notif.to_json(),
    }), 201


@notification_bp.route("/notifications/<notif_id>/read", methods=["PUT"])
@token_required
def mark_read(notif_id):
    """Mark a notification as read."""
    try:
        notif = Notification.objects(id=notif_id, user_id=g.current_user.id).first()
    except Exception:
        return jsonify({"error": "Invalid notification ID"}), 400

    if not notif:
        return jsonify({"error": "Notification not found"}), 404

    notif.is_read = True
    notif.save()
    return jsonify({"message": "Marked as read"}), 200


@notification_bp.route("/notifications/read-all", methods=["PUT"])
@token_required
def mark_all_read():
    """Mark all notifications as read."""
    Notification.objects(user_id=g.current_user.id, is_read=False).update(set__is_read=True)
    return jsonify({"message": "All notifications marked as read"}), 200


@notification_bp.route("/notifications/<notif_id>", methods=["DELETE"])
@token_required
def delete_notification(notif_id):
    """Delete a notification."""
    try:
        notif = Notification.objects(id=notif_id, user_id=g.current_user.id).first()
        if notif:
            notif.delete()
    except Exception:
        pass
    return jsonify({"message": "Notification deleted"}), 200


@notification_bp.route("/notifications/upcoming", methods=["GET"])
@token_required
def upcoming_reminders():
    """Get upcoming reminders for the next N days."""
    days = request.args.get("days", 7, type=int)
    now = datetime.utcnow()
    future = now + timedelta(days=days)

    reminders = Notification.objects(
        user_id=g.current_user.id,
        notification_type="hearing_reminder",
        reminder_date__gte=now,
        reminder_date__lte=future,
    ).order_by("reminder_date")

    return jsonify({
        "reminders": [r.to_json() for r in reminders],
        "total": reminders.count(),
    }), 200

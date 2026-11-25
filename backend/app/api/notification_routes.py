"""Notifications - likes, comments and connection requests for the current user."""

from __future__ import annotations

from flask import Blueprint, jsonify

from app.api.errors import internal_error
from app.security.decorators import get_current_user_id, login_required
from app.services.social_service import SocialService

notification_bp = Blueprint("notifications", __name__)


@notification_bp.get("")
@login_required
def list_notifications() -> tuple[dict, int]:
    """Recent activity aimed at the signed-in student."""
    user_id = get_current_user_id()
    try:
        return jsonify({"data": SocialService().get_notifications(user_id)}), 200
    except Exception:
        return internal_error()


@notification_bp.get("/count")
@login_required
def notification_count() -> tuple[dict, int]:
    """Unread notification and message totals for the nav badges."""
    user_id = get_current_user_id()
    try:
        return jsonify({"data": SocialService().unread_counts(user_id)}), 200
    except Exception:
        return internal_error()


@notification_bp.post("/read")
@login_required
def mark_read() -> tuple[dict, int]:
    """Mark the notification list as seen."""
    user_id = get_current_user_id()
    try:
        SocialService().mark_notifications_read(user_id)
        return jsonify({"data": {"message": "Notifications marked read"}}), 200
    except Exception:
        return internal_error()

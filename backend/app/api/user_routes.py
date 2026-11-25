"""
User Routes - Search and User Details.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.api.errors import error_response, internal_error
from app.security.decorators import login_required
from app.services.user_service import UserService

user_bp = Blueprint("users", __name__)


@user_bp.get("/search")
@login_required
def search_users() -> tuple[dict, int]:
    """Search users by name or username prefix."""
    query = request.args.get("q", "").strip()
    limit = min(int(request.args.get("limit", 10)), 50)
    
    if not query:
        return jsonify({"data": {"users": []}}), 200
    
    try:
        user_service = UserService()
        users = user_service.search_users(query, limit)
        
        return jsonify({"data": {"users": users}}), 200
    except Exception:
        return internal_error()


@user_bp.get("/<user_id>")
@login_required
def get_user(user_id: str) -> tuple[dict, int]:
    """Get user details by ID."""
    try:
        user_service = UserService()
        user = user_service.get_user(user_id)
        
        if not user:
            return error_response("NOT_FOUND", "User not found", 404)
        
        return jsonify({"data": {"user": user}}), 200
    except Exception:
        return internal_error()
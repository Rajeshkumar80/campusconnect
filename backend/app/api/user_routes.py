"""
User Routes - Search and User Details.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

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
    except Exception as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500


@user_bp.get("/<user_id>")
@login_required
def get_user(user_id: str) -> tuple[dict, int]:
    """Get user details by ID."""
    try:
        user_service = UserService()
        user = user_service.get_user(user_id)
        
        if not user:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found"}}), 404
        
        return jsonify({"data": {"user": user}}), 200
    except Exception as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500
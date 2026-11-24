"""
Profile Routes - View and Update Own Profile.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.security.decorators import (
    get_current_user_id,
    login_required,
)
from app.services.engine import get_engine
from app.services.profile_service import ProfileService

profile_bp = Blueprint("profile", __name__)


@profile_bp.get("/me")
@login_required
def get_own_profile() -> tuple[dict, int]:
    """Get current user's profile."""
    user_id = get_current_user_id()
    
    try:
        profile_service = ProfileService()
        profile = profile_service.get_profile(user_id)
        
        if not profile:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Profile not found"}}), 404
        
        return jsonify({"data": {"profile": profile}}), 200
    except Exception as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500


@profile_bp.patch("/me")
@login_required
def update_own_profile() -> tuple[dict, int]:
    """Update current user's profile."""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    # Validate allowed fields
    allowed_fields = {"name", "programme", "year", "bio", "skills"}
    updates = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not updates:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "No valid fields to update"}}), 400
    
    # Validation
    if "name" in updates and not updates["name"].strip():
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Name cannot be empty"}}), 400
    if "year" in updates and (not isinstance(updates["year"], int) or updates["year"] < 1 or updates["year"] > 10):
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Year must be between 1 and 10"}}), 400
    if "skills" in updates and not isinstance(updates["skills"], list):
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Skills must be a list"}}), 400
    
    try:
        profile_service = ProfileService()
        profile = profile_service.update_profile(user_id, updates)
        
        if not profile:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Profile not found"}}), 404
        
        # Update trie if name changed
        if "name" in updates:
            engine = get_engine()
            engine.trie.insert(updates["name"].strip().lower(), user_id)
        
        return jsonify({"data": {"profile": profile}}), 200
    except Exception as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500


@profile_bp.get("/<user_id>")
@login_required
def get_user_profile(user_id: str) -> tuple[dict, int]:
    """Get another user's public profile."""
    try:
        profile_service = ProfileService()
        profile = profile_service.get_profile(user_id)
        
        if not profile:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "User not found"}}), 404
        
        # Return public profile (no sensitive data)
        return jsonify({"data": {"profile": profile}}), 200
    except Exception as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500
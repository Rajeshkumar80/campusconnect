"""
Post Routes - Create, List Own Posts, Delete, Feed.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.security.decorators import get_current_user_id, login_required
from app.services.post_service import PostService

post_bp = Blueprint("posts", __name__)


@post_bp.post("")
@login_required
def create_post() -> tuple[dict, int]:
    """Create a new text post."""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    text = data.get("text", "").strip()
    
    if not text:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Post text is required"}}), 400
    
    if len(text) > 5000:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Post text too long (max 5000 characters)"}}), 400
    
    try:
        post_service = PostService()
        post = post_service.create_post(user_id, text)
        
        return jsonify({"data": {"post": post}}), 201
    except Exception as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500


@post_bp.get("/mine")
@login_required
def get_own_posts() -> tuple[dict, int]:
    """Get current user's posts."""
    user_id = get_current_user_id()
    limit = min(int(request.args.get("limit", 20)), 100)
    
    try:
        post_service = PostService()
        posts = post_service.get_own_posts(user_id, limit)
        
        return jsonify({"data": {"posts": posts}}), 200
    except Exception as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500


@post_bp.delete("/<post_id>")
@login_required
def delete_post(post_id: str) -> tuple[dict, int]:
    """Delete own post."""
    user_id = get_current_user_id()
    
    try:
        post_service = PostService()
        success = post_service.delete_post(post_id, user_id)
        
        if not success:
            return jsonify({"error": {"code": "NOT_FOUND", "message": "Post not found or not authorized"}}), 404
        
        return jsonify({"data": {"message": "Post deleted"}}), 200
    except Exception as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500


@post_bp.get("/feed")
@login_required
def get_feed() -> tuple[dict, int]:
    """Get home feed - posts from accepted connections."""
    user_id = get_current_user_id()
    limit = min(int(request.args.get("limit", 20)), 50)
    
    try:
        post_service = PostService()
        feed = post_service.get_feed(user_id, limit)
        
        return jsonify({"data": {"feed": feed}}), 200
    except Exception as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500
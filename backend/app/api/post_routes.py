"""
Post Routes - Create, List Own Posts, Delete, Feed.
"""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.api.errors import error_response, internal_error
from app.media import MediaError, save_post_media
from app.security.decorators import get_current_user_id, login_required
from app.services.post_service import PostService
from app.services.social_service import SocialService

post_bp = Blueprint("posts", __name__)


def _safe_limit(default: int, maximum: int) -> int:
    """Parse a positive ?limit= value without crashing on bad input."""
    try:
        return max(1, min(int(request.args.get("limit", default)), maximum))
    except (TypeError, ValueError):
        return default


@post_bp.post("")
@login_required
def create_post() -> tuple[dict, int]:
    """Create a text post, optionally with one image or video attachment."""
    user_id = get_current_user_id()

    # JSON for text-only posts, multipart/form-data when a file is attached.
    data = request.get_json(silent=True) or {}
    form_text = request.form.get("text", "")
    text = (form_text if isinstance(form_text, str) else "") or data.get("text", "")
    text = text.strip() if isinstance(text, str) else ""

    media = None
    upload = request.files.get("media")
    if upload and upload.filename:
        try:
            media = save_post_media(upload, current_app.config["UPLOAD_FOLDER"])
        except MediaError as exc:
            return error_response("VALIDATION_ERROR", str(exc), 400)

    if not text and not media:
        return error_response("VALIDATION_ERROR", "Add some text or a photo/video", 400)

    if len(text) > 5000:
        return error_response("VALIDATION_ERROR", "Post text too long (max 5000 characters)", 400)

    try:
        post = PostService().create_post(user_id, text, media)
        return jsonify({"data": {"post": post}}), 201
    except Exception:
        return internal_error()


@post_bp.get("/mine")
@login_required
def get_own_posts() -> tuple[dict, int]:
    """Get current user's posts."""
    user_id = get_current_user_id()
    try:
        posts = PostService().get_own_posts(user_id, _safe_limit(20, 100))
        return jsonify({"data": {"posts": posts}}), 200
    except Exception:
        return internal_error()


@post_bp.get("/user/<user_id>")
@login_required
def get_user_posts(user_id: str) -> tuple[dict, int]:
    """Get any student's posts for their profile page."""
    viewer_id = get_current_user_id()
    try:
        posts = PostService().get_user_posts(
            user_id, viewer_id, _safe_limit(20, 100)
        )
        return jsonify({"data": {"posts": posts}}), 200
    except Exception:
        return internal_error()


@post_bp.post("/<post_id>/like")
@login_required
def toggle_like(post_id: str) -> tuple[dict, int]:
    """Like or unlike a post."""
    user_id = get_current_user_id()
    try:
        result = SocialService().toggle_like(post_id, user_id)
        return jsonify({"data": result}), 200
    except ValueError as exc:
        return error_response("NOT_FOUND", str(exc), 404)
    except Exception:
        return internal_error()


@post_bp.get("/<post_id>/comments")
@login_required
def get_comments(post_id: str) -> tuple[dict, int]:
    """List comments on a post, oldest first."""
    try:
        comments = SocialService().get_comments(post_id)
        return jsonify({"data": {"comments": comments}}), 200
    except Exception:
        return internal_error()


@post_bp.post("/<post_id>/comments")
@login_required
def add_comment(post_id: str) -> tuple[dict, int]:
    """Add a comment to a post."""
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    if not isinstance(text, str):
        return error_response("VALIDATION_ERROR", "Comment text is required", 400)
    try:
        comment = SocialService().add_comment(post_id, user_id, text)
        return jsonify({"data": {"comment": comment}}), 201
    except ValueError as exc:
        return error_response("VALIDATION_ERROR", str(exc), 400)
    except Exception:
        return internal_error()


@post_bp.post("/<post_id>/share")
@login_required
def share_post(post_id: str) -> tuple[dict, int]:
    """Send a post into one or more connections' message threads."""
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}
    recipient_ids = data.get("recipient_ids") or []
    note = data.get("note", "")
    if not isinstance(recipient_ids, list) or not all(
        isinstance(item, str) for item in recipient_ids
    ):
        return error_response("VALIDATION_ERROR", "recipient_ids must be a list", 400)
    if not isinstance(note, str):
        return error_response("VALIDATION_ERROR", "note must be text", 400)
    try:
        sent = SocialService().share_post(user_id, post_id, recipient_ids, note)
        return jsonify({"data": {"sent": sent}}), 201
    except PermissionError as exc:
        return error_response("FORBIDDEN", str(exc), 403)
    except ValueError as exc:
        return error_response("VALIDATION_ERROR", str(exc), 400)
    except Exception:
        return internal_error()


@post_bp.delete("/<post_id>")
@login_required
def delete_post(post_id: str) -> tuple[dict, int]:
    """Delete own post."""
    user_id = get_current_user_id()
    try:
        if not PostService().delete_post(post_id, user_id):
            return error_response("NOT_FOUND", "Post not found or not authorized", 404)
        return jsonify({"data": {"message": "Post deleted"}}), 200
    except Exception:
        return internal_error()


@post_bp.get("/feed")
@login_required
def get_feed() -> tuple[dict, int]:
    """Get home feed - posts from accepted connections."""
    user_id = get_current_user_id()
    try:
        feed = PostService().get_feed(user_id, _safe_limit(20, 50))
        return jsonify({"data": {"feed": feed}}), 200
    except Exception:
        return internal_error()

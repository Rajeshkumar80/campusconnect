"""Direct messages - threads, conversation history and sending."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from app.api.errors import error_response, internal_error
from app.media import MediaError, save_message_media
from app.security.decorators import get_current_user_id, login_required
from app.services.social_service import SocialService

message_bp = Blueprint("messages", __name__)


@message_bp.get("/threads")
@login_required
def list_threads() -> tuple[dict, int]:
    """Connections with their latest message and unread count."""
    user_id = get_current_user_id()
    try:
        return jsonify({"data": {"threads": SocialService().get_threads(user_id)}}), 200
    except Exception:
        return internal_error()


@message_bp.get("/unread-count")
@login_required
def unread_count() -> tuple[dict, int]:
    """Unread message total for the nav badge."""
    user_id = get_current_user_id()
    try:
        return jsonify({"data": SocialService().unread_counts(user_id)}), 200
    except Exception:
        return internal_error()


@message_bp.get("/<user_id>")
@login_required
def get_conversation(user_id: str) -> tuple[dict, int]:
    """Conversation with one connection; marks their messages read."""
    current_user_id = get_current_user_id()
    try:
        data = SocialService().get_conversation(current_user_id, user_id)
        return jsonify({"data": data}), 200
    except PermissionError as exc:
        return error_response("FORBIDDEN", str(exc), 403)
    except ValueError as exc:
        return error_response("NOT_FOUND", str(exc), 404)
    except Exception:
        return internal_error()


@message_bp.post("/<user_id>")
@login_required
def send_message(user_id: str) -> tuple[dict, int]:
    """Send text, a photo/PDF/voice note, or a shared post."""
    sender_id = get_current_user_id()

    data = request.get_json(silent=True) or {}
    text = request.form.get("text", "") or data.get("text", "")
    text = text if isinstance(text, str) else ""
    shared_post_id = data.get("shared_post_id") or request.form.get("shared_post_id")
    if not isinstance(shared_post_id, str):
        shared_post_id = None

    media = None
    upload = request.files.get("media")
    if upload and upload.filename:
        try:
            media = save_message_media(upload, current_app.config["UPLOAD_FOLDER"])
        except MediaError as exc:
            return error_response("VALIDATION_ERROR", str(exc), 400)

    try:
        message = SocialService().send_message(
            sender_id, user_id, text=text, media=media, shared_post_id=shared_post_id
        )
        return jsonify({"data": {"message": message}}), 201
    except PermissionError as exc:
        return error_response("FORBIDDEN", str(exc), 403)
    except ValueError as exc:
        return error_response("VALIDATION_ERROR", str(exc), 400)
    except Exception:
        return internal_error()

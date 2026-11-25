"""Media Routes - Serve uploaded post images and videos to signed-in users."""

from __future__ import annotations

from flask import Blueprint, Response, current_app, send_file

from app.api.errors import error_response
from app.media import resolve_media
from app.security.decorators import login_required

media_bp = Blueprint("media", __name__)


@media_bp.get("/<filename>")
@login_required
def get_media(filename: str) -> Response | tuple[dict, int]:
    """Serve a stored attachment with a safe MIME type."""
    resolved = resolve_media(filename, current_app.config["UPLOAD_FOLDER"])
    if not resolved:
        return error_response("NOT_FOUND", "Media not found", 404)

    path, mimetype = resolved
    response = send_file(path, mimetype=mimetype, conditional=True, max_age=3600)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Disposition"] = f'inline; filename="{filename}"'
    response.headers["Cache-Control"] = "private, max-age=3600"
    return response

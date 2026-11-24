"""
CSRF Protection for Flask.
"""

from __future__ import annotations

from flask import g, request
from flask_wtf.csrf import CSRFProtect, generate_csrf, validate_csrf
from werkzeug.exceptions import BadRequest

csrf = CSRFProtect()


def init_csrf(app) -> None:
    """Initialize CSRF protection."""
    csrf.init_app(app)
    
    @app.before_request
    def _csrf_protect():
        """CSRF protection for state-changing methods."""
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            # Skip for API endpoints that use token auth (if implemented)
            # For cookie-based auth, validate CSRF
            if not _is_csrf_exempt():
                try:
                    validate_csrf(request.headers.get("X-CSRFToken") or request.form.get("csrf_token"))
                except Exception:
                    raise BadRequest("CSRF token missing or invalid")
    
    @app.after_request
    def _add_csrf_token(response):
        """Add CSRF token to response headers for SPA."""
        if hasattr(g, "csrf_token"):
            response.headers["X-CSRFToken"] = g.csrf_token
        return response


def _is_csrf_exempt() -> bool:
    """Check if endpoint is exempt from CSRF."""
    # Health endpoints
    if request.path.startswith("/api/v1/health"):
        return True
    # Auth endpoints (login/register don't need CSRF for initial auth)
    if request.path.startswith("/api/v1/auth"):
        return True
    return False


def get_csrf_token() -> str:
    """Get CSRF token for frontend."""
    return generate_csrf()
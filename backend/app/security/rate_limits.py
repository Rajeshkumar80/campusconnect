"""
Rate Limiting Configuration.
"""

from __future__ import annotations

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def get_user_id_for_rate_limit() -> str:
    """Get user identifier for rate limiting (IP or user ID)."""
    # In production, use user ID if authenticated
    from flask import session
    if "user_id" in session:
        return f"user:{session['user_id']}"
    return f"ip:{get_remote_address()}"


# Rate limit configurations
RATE_LIMITS = {
    "auth": {
        "register": "5 per minute",
        "login": "10 per minute",
        "logout": "20 per minute",
    },
    "search": "30 per minute",
    "connections": {
        "requests": "20 per minute",
        "actions": "30 per minute",
    },
    "posts": {
        "create": "10 per minute",
        "feed": "60 per minute",
    },
    "profile": {
        "update": "10 per minute",
    },
}


def apply_rate_limits(limiter: Limiter) -> None:
    """Apply rate limits to endpoints (called after blueprint registration)."""
    # These are applied via decorators in route files

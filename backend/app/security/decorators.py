"""
Security Decorators - Authentication and Authorization.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps

from flask import g, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash


# Argon2id password hashing
def hash_password(password: str) -> str:
    """Hash password using Argon2id via werkzeug (PBKDF2 fallback)."""
    # Using werkzeug's generate_password_hash with pbkdf2:sha256 as fallback
    # For true Argon2id, use argon2-cffi directly
    try:
        from argon2 import PasswordHasher
        ph = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            salt_len=16,
        )
        return ph.hash(password)
    except ImportError:
        # Fallback to werkzeug
        return generate_password_hash(password, method="pbkdf2:sha256:600000", salt_length=16)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    try:
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        ph.verify(password_hash, password)
        return True
    except Exception:
        # Fallback to werkzeug
        return check_password_hash(password_hash, password)


def login_required(f: Callable) -> Callable:
    """Decorator to require authenticated user."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Authentication required"}}), 401
        g.current_user_id = session["user_id"]
        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id() -> str | None:
    """Get current user ID from session."""
    return session.get("user_id")


def set_current_user(user_id: str) -> None:
    """Set current user in session."""
    session["user_id"] = user_id
    session.permanent = True


def clear_current_user() -> None:
    """Clear current user from session."""
    session.clear()


def require_ownership(resource_user_id: str) -> bool:
    """Check if current user owns the resource."""
    current_user_id = get_current_user_id()
    return current_user_id == resource_user_id


def require_connection_participant(user_a: str, user_b: str) -> bool:
    """Check if current user is one of the connection participants."""
    current_user_id = get_current_user_id()
    return current_user_id in (user_a, user_b)


def require_request_recipient(recipient_id: str) -> bool:
    """Check if current user is the request recipient."""
    current_user_id = get_current_user_id()
    return current_user_id == recipient_id


def require_request_sender(sender_id: str) -> bool:
    """Check if current user is the request sender."""
    current_user_id = get_current_user_id()
    return current_user_id == sender_id
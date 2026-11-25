"""
Security Decorators - Authentication and Authorization.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps

from flask import g, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash

# Argon2id parameters - hash and verify must use the same settings.
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536
ARGON2_PARALLELISM = 4


def _argon2_hasher():
    """Return an Argon2id hasher, or None if argon2-cffi is unavailable."""
    try:
        from argon2 import PasswordHasher
    except ImportError:
        return None

    return PasswordHasher(
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=32,
        salt_len=16,
    )


# Argon2id password hashing
def hash_password(password: str) -> str:
    """Hash a password using Argon2id (PBKDF2 fallback if argon2-cffi is missing)."""
    hasher = _argon2_hasher()
    if hasher is not None:
        return hasher.hash(password)
    return generate_password_hash(password, method="pbkdf2:sha256:600000", salt_length=16)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a stored hash. Never raises."""
    if not password or not password_hash:
        return False

    if password_hash.startswith("$argon2"):
        hasher = _argon2_hasher()
        if hasher is None:
            return False
        try:
            return bool(hasher.verify(password_hash, password))
        except Exception:
            return False

    try:
        return bool(check_password_hash(password_hash, password))
    except Exception:
        return False


def login_required(f: Callable) -> Callable:
    """Decorator to require authenticated user."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return (
                jsonify({"error": {"code": "UNAUTHORIZED", "message": "Authentication required"}}),
                401,
            )
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

"""
Authentication Routes - Register, Login, Logout, Current User.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_wtf.csrf import generate_csrf

from app.api.errors import error_response, internal_error
from app.extensions import csrf, limiter
from app.security.decorators import (
    clear_current_user,
    get_current_user_id,
    set_current_user,
)
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/csrf")
@csrf.exempt
def csrf_token() -> tuple[dict, int]:
    """Issue a CSRF token for the SPA (also returned in the X-CSRFToken header)."""
    token = generate_csrf()
    response = jsonify({"data": {"csrf_token": token}})
    response.headers["X-CSRFToken"] = token
    return response, 200


@auth_bp.post("/register")
@csrf.exempt
@limiter.limit("20 per minute")
def register() -> tuple[dict, int]:
    """Register a new user."""
    data = request.get_json() or {}
    
    username = data.get("username", "").strip()
    password = data.get("password", "")
    name = data.get("name", "").strip()
    programme = data.get("programme", "").strip()
    year = data.get("year", 0)
    bio = data.get("bio", "").strip()
    skills = data.get("skills", [])
    
    # Validation
    if not username:
        return error_response("VALIDATION_ERROR", "Username is required", 400)
    if not password:
        return error_response("VALIDATION_ERROR", "Password is required", 400)
    if len(password) < 8:
        return error_response("VALIDATION_ERROR", "Password must be at least 8 characters", 400)
    if not name:
        return error_response("VALIDATION_ERROR", "Name is required", 400)
    
    try:
        auth_service = AuthService()
        user = auth_service.register(
            username=username,
            password=password,
            name=name,
            programme=programme,
            year=year,
            bio=bio,
            skills=skills,
        )
        
        # Auto-login after registration
        set_current_user(user["user_id"])
        
        return jsonify({
            "data": {
                "user": user,
                "message": "Registration successful",
            }
        }), 201
    except ValueError as e:
        return error_response("CONFLICT", str(e), 409)
    except Exception:
        return internal_error()


@auth_bp.post("/login")
@csrf.exempt
@limiter.limit("30 per minute")
def login() -> tuple[dict, int]:
    """Log in a user."""
    data = request.get_json() or {}
    
    username = data.get("username", "").strip()
    password = data.get("password", "")
    
    if not username or not password:
        return error_response("VALIDATION_ERROR", "Username and password required", 400)
    
    try:
        auth_service = AuthService()
        user = auth_service.login(username, password)
        
        set_current_user(user["user_id"])
        
        return jsonify({
            "data": {
                "user": user,
                "message": "Login successful",
            }
        }), 200
    except ValueError:
        # Generic error to prevent account enumeration
        return error_response("UNAUTHORIZED", "Invalid username or password", 401)
    except Exception:
        return internal_error()


@auth_bp.post("/logout")
def logout() -> tuple[dict, int]:
    """Log out the current user."""
    clear_current_user()
    return jsonify({"data": {"message": "Logged out successfully"}}), 200


@auth_bp.get("/me")
def current_user() -> tuple[dict, int]:
    """Get current authenticated user."""
    user_id = get_current_user_id()
    if not user_id:
        return error_response("UNAUTHORIZED", "Not authenticated", 401)
    
    try:
        auth_service = AuthService()
        user = auth_service.get_current_user(user_id)
        if not user:
            clear_current_user()
            return error_response("UNAUTHORIZED", "User not found", 401)
        
        return jsonify({"data": {"user": user}}), 200
    except Exception:
        return internal_error()

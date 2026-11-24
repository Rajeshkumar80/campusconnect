"""
Authentication Routes - Register, Login, Logout, Current User.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.security.decorators import (
    clear_current_user,
    get_current_user_id,
    set_current_user,
)
from app.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
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
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Username is required"}}), 400
    if not password:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Password is required"}}), 400
    if len(password) < 8:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Password must be at least 8 characters"}}), 400
    if not name:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Name is required"}}), 400
    
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
        return jsonify({"error": {"code": "CONFLICT", "message": str(e)}}), 409
    except Exception as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500


@auth_bp.post("/login")
def login() -> tuple[dict, int]:
    """Log in a user."""
    data = request.get_json() or {}
    
    username = data.get("username", "").strip()
    password = data.get("password", "")
    
    if not username or not password:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Username and password required"}}), 400
    
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
        return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Invalid username or password"}}), 401
    except Exception as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500


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
        return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Not authenticated"}}), 401
    
    try:
        auth_service = AuthService()
        user = auth_service.get_current_user(user_id)
        if not user:
            clear_current_user()
            return jsonify({"error": {"code": "UNAUTHORIZED", "message": "User not found"}}), 401
        
        return jsonify({"data": {"user": user}}), 200
    except Exception as e:
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": str(e)}}), 500
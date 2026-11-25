"""
Connection Routes - Connection Requests, Accepted Connections, Discovery.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from app.api.errors import error_response, internal_error
from app.security.decorators import (
    get_current_user_id,
    login_required,
)
from app.services.connection_service import ConnectionService

connection_bp = Blueprint("connections", __name__)


@connection_bp.get("")
@login_required
def list_connections() -> tuple[dict, int]:
    """List current user's accepted connections."""
    user_id = get_current_user_id()
    
    try:
        conn_service = ConnectionService()
        connections = conn_service.get_connections(user_id)
        
        return jsonify({"data": {"connections": connections}}), 200
    except Exception:
        return internal_error()


@connection_bp.post("/requests")
@login_required
def send_connection_request() -> tuple[dict, int]:
    """Send a connection request."""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    recipient_id = data.get("recipient_id", "").strip()
    
    if not recipient_id:
        return error_response("VALIDATION_ERROR", "Recipient ID is required", 400)
    
    if recipient_id == user_id:
        return error_response("VALIDATION_ERROR", "Cannot connect to yourself", 400)
    
    try:
        conn_service = ConnectionService()
        request_obj = conn_service.send_request(user_id, recipient_id)
        
        return jsonify({"data": {"request": request_obj}}), 201
    except ValueError as e:
        return error_response("CONFLICT", str(e), 409)
    except Exception:
        return internal_error()


@connection_bp.get("/requests/incoming")
@login_required
def get_incoming_requests() -> tuple[dict, int]:
    """Get incoming pending connection requests."""
    user_id = get_current_user_id()
    
    try:
        conn_service = ConnectionService()
        requests = conn_service.get_incoming_requests(user_id)
        
        return jsonify({"data": {"requests": requests}}), 200
    except Exception:
        return internal_error()


@connection_bp.get("/requests/outgoing")
@login_required
def get_outgoing_requests() -> tuple[dict, int]:
    """Get outgoing pending connection requests."""
    user_id = get_current_user_id()
    
    try:
        conn_service = ConnectionService()
        requests = conn_service.get_outgoing_requests(user_id)
        
        return jsonify({"data": {"requests": requests}}), 200
    except Exception:
        return internal_error()


@connection_bp.post("/requests/<request_id>/accept")
@login_required
def accept_request(request_id: str) -> tuple[dict, int]:
    """Accept a connection request."""
    user_id = get_current_user_id()
    
    try:
        conn_service = ConnectionService()
        request_obj = conn_service.accept_request(request_id, user_id)
        
        return jsonify({"data": {"request": request_obj}}), 200
    except ValueError as e:
        return error_response("FORBIDDEN", str(e), 403)
    except Exception:
        return internal_error()


@connection_bp.post("/requests/<request_id>/reject")
@login_required
def reject_request(request_id: str) -> tuple[dict, int]:
    """Reject a connection request."""
    user_id = get_current_user_id()
    
    try:
        conn_service = ConnectionService()
        request_obj = conn_service.reject_request(request_id, user_id)
        
        return jsonify({"data": {"request": request_obj}}), 200
    except ValueError as e:
        return error_response("FORBIDDEN", str(e), 403)
    except Exception:
        return internal_error()


@connection_bp.post("/requests/<request_id>/cancel")
@login_required
def cancel_request(request_id: str) -> tuple[dict, int]:
    """Cancel a sent connection request."""
    user_id = get_current_user_id()
    
    try:
        conn_service = ConnectionService()
        request_obj = conn_service.cancel_request(request_id, user_id)
        
        return jsonify({"data": {"request": request_obj}}), 200
    except ValueError as e:
        return error_response("FORBIDDEN", str(e), 403)
    except Exception:
        return internal_error()


@connection_bp.delete("/<user_id>")
@login_required
def remove_connection(user_id: str) -> tuple[dict, int]:
    """Remove an accepted connection."""
    current_user_id = get_current_user_id()
    
    # The session user may only drop their own edge with the target user.
    if current_user_id == user_id:
        return error_response("VALIDATION_ERROR", "Cannot remove a connection with yourself", 400)
    
    try:
        conn_service = ConnectionService()
        success = conn_service.remove_connection(current_user_id, user_id)
        
        if not success:
            return error_response("NOT_FOUND", "Connection not found", 404)
        
        return jsonify({"data": {"message": "Connection removed"}}), 200
    except Exception:
        return internal_error()


@connection_bp.get("/<user_id>/mutual")
@login_required
def get_mutual_connections(user_id: str) -> tuple[dict, int]:
    """Get mutual connections with another user."""
    current_user_id = get_current_user_id()
    
    try:
        conn_service = ConnectionService()
        mutual = conn_service.get_mutual_connections(current_user_id, user_id)
        
        return jsonify({"data": {"mutual_connections": mutual}}), 200
    except Exception:
        return internal_error()


@connection_bp.get("/<user_id>/degree")
@login_required
def get_connection_degree(user_id: str) -> tuple[dict, int]:
    """Get degree of connection to another user."""
    current_user_id = get_current_user_id()
    
    try:
        conn_service = ConnectionService()
        degree = conn_service.get_connection_degree(current_user_id, user_id)
        
        return jsonify({"data": {"degree": degree}}), 200
    except Exception:
        return internal_error()


@connection_bp.get("/<user_id>/path")
@login_required
def get_shortest_path(user_id: str) -> tuple[dict, int]:
    """Get shortest connection path to another user."""
    current_user_id = get_current_user_id()
    
    try:
        conn_service = ConnectionService()
        path = conn_service.get_shortest_path(current_user_id, user_id)
        
        return jsonify({"data": {"path": path}}), 200
    except Exception:
        return internal_error()


@connection_bp.get("/suggestions")
@login_required
def get_suggestions() -> tuple[dict, int]:
    """Get people you may know suggestions."""
    user_id = get_current_user_id()
    limit = min(int(request.args.get("limit", 10)), 50)
    
    try:
        conn_service = ConnectionService()
        suggestions = conn_service.get_suggestions(user_id, limit)
        
        return jsonify({"data": {"suggestions": suggestions}}), 200
    except Exception:
        return internal_error()

"""Shared JSON error responses for the REST API."""

from __future__ import annotations

from flask import Response, current_app, jsonify


def error_response(code: str, message: str, status: int) -> tuple[Response, int]:
    """Build a JSON error response using the standard error envelope."""
    return jsonify({"error": {"code": code, "message": message}}), status


def internal_error() -> tuple[Response, int]:
    """Log the exception and return a generic 500 without leaking internals."""
    current_app.logger.exception("Unhandled API error")
    return error_response("INTERNAL_ERROR", "An unexpected error occurred", 500)

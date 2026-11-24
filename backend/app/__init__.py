"""
CampusConnect Backend Application Package.

Flask app factory with DSA core integration.
"""

from __future__ import annotations

import os
from flask import Flask, jsonify

from app.config import get_config
from app.extensions import init_extensions


def create_app(config_name: str | None = None) -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        config_name: Configuration environment name (development, testing, production)
    
    Returns:
        Configured Flask application.
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_name:
        os.environ["FLASK_ENV"] = config_name
    config = get_config()
    app.config.from_object(config)
    
    # Initialize extensions
    init_extensions(app)
    
    # Initialize DSA engine
    from app.services.engine import init_engine
    init_engine(app)
    
    # Register blueprints
    from app.api.auth_routes import auth_bp
    from app.api.connection_routes import connection_bp
    from app.api.health_routes import health_bp
    from app.api.post_routes import post_bp
    from app.api.profile_routes import profile_bp
    from app.api.user_routes import user_bp
    
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(profile_bp, url_prefix="/api/v1/profiles")
    app.register_blueprint(user_bp, url_prefix="/api/v1/users")
    app.register_blueprint(connection_bp, url_prefix="/api/v1/connections")
    app.register_blueprint(post_bp, url_prefix="/api/v1/posts")
    app.register_blueprint(health_bp, url_prefix="/api/v1/health")
    
    # Global error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": str(e)}}), 400
    
    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": {"code": "UNAUTHORIZED", "message": "Authentication required"}}), 401
    
    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Access denied"}}), 403
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Resource not found"}}), 404
    
    @app.errorhandler(409)
    def conflict(e):
        return jsonify({"error": {"code": "CONFLICT", "message": str(e)}}), 409
    
    @app.errorhandler(429)
    def rate_limited(e):
        return jsonify({"error": {"code": "RATE_LIMITED", "message": "Too many requests"}}), 429
    
    @app.errorhandler(500)
    def internal_error(e):
        # Log the actual error for debugging
        app.logger.error(f"Internal server error: {e}")
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}}), 500
    
    return app


__version__ = "0.1.0"
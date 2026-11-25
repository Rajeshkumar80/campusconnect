"""
CampusConnect Backend Application Package.

Flask app factory with DSA core integration.
"""

from __future__ import annotations

import os

from flask import Flask
from flask_wtf.csrf import CSRFError

from app.api.errors import error_response
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
    from app.api.media_routes import media_bp
    from app.api.message_routes import message_bp
    from app.api.notification_routes import notification_bp
    from app.api.post_routes import post_bp
    from app.api.profile_routes import profile_bp
    from app.api.user_routes import user_bp
    
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(profile_bp, url_prefix="/api/v1/profiles")
    app.register_blueprint(user_bp, url_prefix="/api/v1/users")
    app.register_blueprint(connection_bp, url_prefix="/api/v1/connections")
    app.register_blueprint(post_bp, url_prefix="/api/v1/posts")
    app.register_blueprint(message_bp, url_prefix="/api/v1/messages")
    app.register_blueprint(notification_bp, url_prefix="/api/v1/notifications")
    app.register_blueprint(media_bp, url_prefix="/api/v1/media")
    app.register_blueprint(health_bp, url_prefix="/api/v1/health")
    
    # Global error handlers
    @app.errorhandler(CSRFError)
    def csrf_error(e):
        return error_response(
            "CSRF_TOKEN_MISSING",
            "CSRF token missing or invalid. Refresh the page and try again.",
            400,
        )

    @app.errorhandler(400)
    def bad_request(e):
        return error_response("BAD_REQUEST", str(e), 400)
    
    @app.errorhandler(401)
    def unauthorized(e):
        return error_response("UNAUTHORIZED", "Authentication required", 401)
    
    @app.errorhandler(403)
    def forbidden(e):
        return error_response("FORBIDDEN", "Access denied", 403)
    
    @app.errorhandler(404)
    def not_found(e):
        return error_response("NOT_FOUND", "Resource not found", 404)
    
    @app.errorhandler(409)
    def conflict(e):
        return error_response("CONFLICT", str(e), 409)
    
    @app.errorhandler(429)
    def rate_limited(e):
        return error_response("RATE_LIMITED", "Too many requests", 429)

    @app.errorhandler(413)
    def file_too_large(e):
        return error_response(
            "FILE_TOO_LARGE",
            "That file is too large. Images up to 10 MB, videos up to 50 MB.",
            413,
        )
    
    @app.errorhandler(500)
    def internal_error(e):
        # Log the actual error for debugging
        app.logger.error(f"Internal server error: {e}")
        return error_response("INTERNAL_ERROR", "An unexpected error occurred", 500)
    
    return app


__version__ = "0.1.0"

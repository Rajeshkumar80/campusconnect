"""
Health Check Routes.
"""

from __future__ import annotations

from flask import Blueprint, jsonify

from app.extensions import mongo_client

health_bp = Blueprint("health", __name__)


@health_bp.get("/live")
def liveness() -> tuple[dict, int]:
    """Liveness probe - process is alive."""
    return jsonify({"status": "alive"}), 200


@health_bp.get("/ready")
def readiness() -> tuple[dict, int]:
    """Readiness probe - dependencies are ready."""
    try:
        # Check MongoDB connection
        if mongo_client:
            mongo_client.admin.command("ping")
            db_ready = True
        else:
            db_ready = False
        
        # Check DSA engine
        from app.services.engine import get_engine
        engine = get_engine()
        engine_ready = engine.is_initialized
        
        ready = db_ready and engine_ready
        
        return jsonify({
            "status": "ready" if ready else "not_ready",
            "dependencies": {
                "mongodb": "ok" if db_ready else "unavailable",
                "dsa_engine": "initialized" if engine_ready else "not_initialized",
            },
        }), 200 if ready else 503
    except Exception as e:
        return jsonify({
            "status": "not_ready",
            "error": str(e),
        }), 503
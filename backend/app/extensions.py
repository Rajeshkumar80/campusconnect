"""
Flask Extensions Setup.
"""

from __future__ import annotations

from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from pymongo import MongoClient
from pymongo.database import Database

from app.config import get_config

# Extension instances
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri="memory://",
)

# MongoDB client (initialized in app factory)
mongo_client: MongoClient | None = None
mongo_db: Database | None = None


def init_extensions(app: Flask) -> None:
    """Initialize all Flask extensions."""
    config = get_config()

    # CORS allowlist - credentialed requests need an explicit origin list
    allowed_origins = [
        origin.strip()
        for origin in config.CORS_ALLOWED_ORIGINS.split(",")
        if origin.strip()
    ]
    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "X-CSRFToken", "X-CSRF-Token"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    # CSRF Protection
    csrf.init_app(app)
    
    # Rate Limiter
    limiter.init_app(app)
    
    # MongoDB
    global mongo_client, mongo_db
    mongo_client = MongoClient(config.MONGODB_URI)
    mongo_db = mongo_client[config.MONGODB_DATABASE]

    # Create indexes
    _create_indexes(mongo_db)


def _drop_index_if_exists(collection, name: str) -> None:
    """Drop an index if it exists."""
    if name in collection.index_information():
        collection.drop_index(name)


def _create_indexes(db: Database) -> None:
    """Create MongoDB indexes."""
    # Users collection
    db.users.create_index("username", unique=True)
    db.users.create_index("created_at")

    # Profiles use the default _id index, which is already unique.

    # Connection requests: at most one *pending* request per ordered pair.
    # Older attempts are kept as history, so the index is partial.
    _drop_index_if_exists(
        db.connection_requests,
        "sender_id_1_recipient_id_1_status_1",
    )
    db.connection_requests.create_index(
        [("sender_id", 1), ("recipient_id", 1)],
        unique=True,
        partialFilterExpression={"status": "pending"},
    )
    db.connection_requests.create_index([("recipient_id", 1), ("status", 1)])
    db.connection_requests.create_index([("sender_id", 1), ("status", 1)])
    
    # Connections (canonical pairs)
    db.connections.create_index(
        [("user_low", 1), ("user_high", 1)],
        unique=True,
    )
    db.connections.create_index("user_low")
    db.connections.create_index("user_high")
    
    # Posts
    db.posts.create_index([("author_id", 1), ("created_at", -1)])
    db.posts.create_index("created_at")


def get_mongo_db() -> Database:
    """Get MongoDB database instance."""
    if mongo_db is None:
        raise RuntimeError("MongoDB not initialized. Call init_extensions first.")
    return mongo_db
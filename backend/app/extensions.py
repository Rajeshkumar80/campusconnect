"""
Flask Extensions Setup.
"""

from __future__ import annotations

from flask import Flask
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
    
    # Register teardown
    app.teardown_appcontext(_close_mongo)


def _create_indexes(db: Database) -> None:
    """Create MongoDB indexes."""
    # Users collection
    db.users.create_index("username", unique=True)
    db.users.create_index("created_at")
    
    # Profiles collection
    db.profiles.create_index("_id", unique=True)
    
    # Connection requests
    db.connection_requests.create_index(
        [("sender_id", 1), ("recipient_id", 1), ("status", 1)],
        unique=True,
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


def _close_mongo(exception: BaseException | None = None) -> None:
    """Close MongoDB connection on teardown."""
    global mongo_client
    if mongo_client:
        mongo_client.close()
        mongo_client = None


def get_mongo_db() -> Database:
    """Get MongoDB database instance."""
    if mongo_db is None:
        raise RuntimeError("MongoDB not initialized. Call init_extensions first.")
    return mongo_db
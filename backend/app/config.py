"""
Flask Application Configuration.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent

# Load the local .env before the config classes read the environment.
load_dotenv()


class Config:
    """Base configuration."""
    
    # Flask
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    FLASK_ENV: str = os.environ.get("FLASK_ENV", "development")
    FLASK_DEBUG: bool = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    # MongoDB
    MONGODB_URI: str = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DATABASE: str = os.environ.get("MONGODB_DATABASE", "campusconnect")
    
    # Frontend
    FRONTEND_ORIGIN: str = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
    # Comma-separated allowlist. Requests from other origins are rejected.
    CORS_ALLOWED_ORIGINS: str = os.environ.get(
        "CORS_ALLOWED_ORIGINS", os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")
    )
    
    # Session
    SESSION_COOKIE_SECURE: bool = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    PERMANENT_SESSION_LIFETIME: int = 86400  # 24 hours
    
    # Rate limiting
    RATELIMIT_DEFAULT: str = "100 per minute"
    RATELIMIT_STORAGE_URL: str = "memory://"
    RATELIMIT_ENABLED: bool = os.environ.get("RATELIMIT_ENABLED", "true").lower() == "true"

    # Media uploads (post images/videos). Files live outside the source tree.
    UPLOAD_FOLDER: str = os.environ.get("UPLOAD_FOLDER", str(BACKEND_DIR / "uploads"))
    MAX_CONTENT_LENGTH: int = 60 * 1024 * 1024
    
    # Security
    BCRYPT_ROUNDS: int = 12
    ARGON2_TIME_COST: int = 3
    ARGON2_MEMORY_COST: int = 65536
    ARGON2_PARALLELISM: int = 4


class DevelopmentConfig(Config):
    """Development configuration."""
    FLASK_DEBUG: bool = True


class TestingConfig(Config):
    """Testing configuration."""
    TESTING: bool = True
    FLASK_DEBUG: bool = False
    MONGODB_DATABASE: str = "campusconnect_test"
    RATELIMIT_ENABLED: bool = False
    WTF_CSRF_ENABLED: bool = False
    SECRET_KEY: str = "test-secret-key"


class ProductionConfig(Config):
    """Production configuration."""
    FLASK_DEBUG: bool = False
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_SAMESITE: str = "Strict"


CONFIG_MAP: Final[dict[str, type[Config]]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config() -> Config:
    """Get configuration based on environment."""
    env = os.environ.get("FLASK_ENV", "development").lower()
    config_class = CONFIG_MAP.get(env, CONFIG_MAP["default"])
    return config_class()
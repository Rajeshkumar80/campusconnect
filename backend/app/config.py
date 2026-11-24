"""
Flask Application Configuration.
"""

from __future__ import annotations

import os
from typing import Final


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
    
    # Session
    SESSION_COOKIE_SECURE: bool = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    PERMANENT_SESSION_LIFETIME: int = 86400  # 24 hours
    
    # Rate limiting
    RATELIMIT_DEFAULT: str = "100 per minute"
    RATELIMIT_STORAGE_URL: str = "memory://"
    
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
"""
Authentication Service - Business logic for user authentication.
"""

from __future__ import annotations

from typing import Any

from app.repositories.interfaces import UserRepository
from app.security.decorators import hash_password, verify_password
from app.services.engine import get_engine


class AuthService:
    """Authentication service coordinating user registration and login."""
    
    def __init__(self) -> None:
        self._engine = get_engine()
        # Get repositories from engine's initialization context
        from app.extensions import get_mongo_db
        from app.repositories.mongo_user_repository import MongoUserRepository
        
        db = get_mongo_db()
        self._user_repo: UserRepository = MongoUserRepository(db)
    
    def register(
        self,
        username: str,
        password: str,
        name: str,
        programme: str,
        year: int,
        bio: str,
        skills: list[str],
    ) -> dict[str, Any]:
        """Register a new user."""
        # Check username uniqueness
        existing = self._user_repo.get_user_by_username(username.lower())
        if existing:
            raise ValueError("Username already taken")
        
        # Hash password
        password_hash = hash_password(password)
        
        # Generate user ID
        import uuid
        user_id = str(uuid.uuid4())
        
        # Create user
        self._user_repo.create_user(user_id, username.lower(), password_hash)
        
        # Create profile
        profile_data = {
            "name": name,
            "programme": programme,
            "year": year,
            "bio": bio,
            "skills": skills,
        }
        self._user_repo.create_profile(user_id, profile_data)
        
        # Update DSA engine
        self._engine.graph.add_user(user_id)
        self._engine.trie.insert(username.lower(), user_id)
        self._engine.trie.insert(name.lower(), user_id)
        
        return {
            "user_id": user_id,
            "username": username.lower(),
            "profile": {
                "name": name,
                "programme": programme,
                "year": year,
                "bio": bio,
                "skills": skills,
            },
        }
    
    def login(self, username: str, password: str) -> dict[str, Any]:
        """Authenticate user and return user data."""
        user = self._user_repo.get_user_by_username(username.lower())
        if not user:
            raise ValueError("Invalid credentials")
        
        # Verify password
        if not verify_password(password, user.get("password_hash", "")):
            raise ValueError("Invalid credentials")
        
        # Check account status
        if user.get("status") != "active":
            raise ValueError("Account is not active")
        
        # Return user data (without password hash)
        profile = user.get("profile", {})
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "profile": {
                "name": profile.get("name", ""),
                "programme": profile.get("programme", ""),
                "year": profile.get("year", 0),
                "bio": profile.get("bio", ""),
                "skills": profile.get("skills", []),
            },
        }
    
    def get_current_user(self, user_id: str) -> dict[str, Any] | None:
        """Get current user data by ID."""
        user = self._user_repo.get_user_by_id(user_id)
        if not user:
            return None
        
        profile = user.get("profile", {})
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "profile": {
                "name": profile.get("name", ""),
                "programme": profile.get("programme", ""),
                "year": profile.get("year", 0),
                "bio": profile.get("bio", ""),
                "skills": profile.get("skills", []),
            },
        }
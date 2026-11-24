"""
User Service - Business logic for user search and lookup.
"""

from __future__ import annotations

from typing import Any

from app.extensions import get_mongo_db
from app.repositories.interfaces import UserRepository
from app.repositories.mongo_user_repository import MongoUserRepository
from app.services.engine import get_engine


class UserService:
    """User service for search and lookup operations."""
    
    def __init__(self) -> None:
        self._engine = get_engine()
        db = get_mongo_db()
        self._user_repo: UserRepository = MongoUserRepository(db)
    
    def search_users(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search users by prefix on username or name."""
        # Use trie for prefix search
        user_ids = self._engine.trie.prefix_search(query, limit=limit * 2)
        
        # Get full user data
        users = []
        for user_id in user_ids[:limit]:
            user = self._user_repo.get_user_by_id(user_id)
            if user and user.get("status") == "active":
                profile = user.get("profile", {})
                users.append({
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "name": profile.get("name", ""),
                    "programme": profile.get("programme", ""),
                    "year": profile.get("year", 0),
                })
        
        return users
    
    def get_user(self, user_id: str) -> dict[str, Any] | None:
        """Get user by ID."""
        user = self._user_repo.get_user_by_id(user_id)
        if not user or user.get("status") != "active":
            return None
        
        profile = user.get("profile", {})
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "name": profile.get("name", ""),
            "programme": profile.get("programme", ""),
            "year": profile.get("year", 0),
            "bio": profile.get("bio", ""),
            "skills": profile.get("skills", []),
        }
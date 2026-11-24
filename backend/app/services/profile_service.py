"""
Profile Service - Business logic for user profiles.
"""

from __future__ import annotations

from typing import Any

from app.extensions import get_mongo_db
from app.repositories.interfaces import UserRepository
from app.repositories.mongo_user_repository import MongoUserRepository
from app.services.engine import get_engine


class ProfileService:
    """Profile service for viewing and updating user profiles."""
    
    def __init__(self) -> None:
        self._engine = get_engine()
        db = get_mongo_db()
        self._user_repo: UserRepository = MongoUserRepository(db)
    
    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        """Get user profile by ID."""
        profile = self._user_repo.get_profile(user_id)
        if not profile:
            return None
        
        return {
            "user_id": profile["user_id"],
            "name": profile["name"],
            "programme": profile["programme"],
            "year": profile["year"],
            "bio": profile["bio"],
            "skills": profile["skills"],
            "updated_at": profile["updated_at"],
        }
    
    def update_profile(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        """Update user profile."""
        success = self._user_repo.update_profile(user_id, updates)
        if not success:
            return None
        
        return self.get_profile(user_id)
"""
MongoDB User Repository Implementation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.repositories.interfaces import UserRepository


class MongoUserRepository(UserRepository):
    """MongoDB implementation of UserRepository."""
    
    def __init__(self, db) -> None:
        self._db = db
        self._users = db.users
        self._profiles = db.profiles
    
    def create_user(
        self,
        user_id: str,
        username: str,
        password_hash: str,
    ) -> dict[str, Any]:
        """Create a new user account."""
        now = datetime.now(UTC)
        user_doc = {
            "_id": user_id,
            "username": username.lower(),
            "password_hash": password_hash,
            "created_at": now,
            "updated_at": now,
            "status": "active",
        }
        self._users.insert_one(user_doc)
        
        # Create empty profile
        profile_doc = {
            "_id": user_id,
            "name": "",
            "programme": "",
            "year": 0,
            "bio": "",
            "skills": [],
            "updated_at": now,
        }
        self._profiles.insert_one(profile_doc)
        
        return self._format_user(user_doc, profile_doc)
    
    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Get user by ID."""
        user = self._users.find_one({"_id": user_id})
        if not user:
            return None
        profile = self._profiles.find_one({"_id": user_id})
        return self._format_user(user, profile)
    
    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """Get user by normalized username."""
        user = self._users.find_one({"username": username.lower()})
        if not user:
            return None
        profile = self._profiles.find_one({"_id": user["_id"]})
        return self._format_user(user, profile)
    
    def get_all_users(self) -> list[dict[str, Any]]:
        """Get all users (for startup rebuild)."""
        users = list(self._users.find({"status": "active"}))
        result = []
        for user in users:
            profile = self._profiles.find_one({"_id": user["_id"]})
            result.append(self._format_user(user, profile))
        return result
    
    def update_user(self, user_id: str, updates: dict[str, Any]) -> bool:
        """Update user fields."""
        # Only allow safe fields to be updated
        allowed = {"status"}
        safe_updates = {k: v for k, v in updates.items() if k in allowed}
        if not safe_updates:
            return False
        
        safe_updates["updated_at"] = datetime.now(UTC)
        result = self._users.update_one(
            {"_id": user_id},
            {"$set": safe_updates},
        )
        return result.modified_count > 0
    
    def create_profile(self, user_id: str, profile_data: dict[str, Any]) -> dict[str, Any]:
        """Create user profile."""
        now = datetime.now(UTC)
        profile_doc = {
            "_id": user_id,
            "name": profile_data.get("name", ""),
            "programme": profile_data.get("programme", ""),
            "year": profile_data.get("year", 0),
            "bio": profile_data.get("bio", ""),
            "skills": profile_data.get("skills", []),
            "updated_at": now,
        }
        self._profiles.insert_one(profile_doc)
        return self._format_profile(profile_doc)
    
    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        """Get user profile."""
        profile = self._profiles.find_one({"_id": user_id})
        if not profile:
            return None
        return self._format_profile(profile)
    
    def update_profile(self, user_id: str, updates: dict[str, Any]) -> bool:
        """Update user profile."""
        allowed = {"name", "programme", "year", "bio", "skills"}
        safe_updates = {k: v for k, v in updates.items() if k in allowed}
        if not safe_updates:
            return False
        
        safe_updates["updated_at"] = datetime.now(UTC)
        result = self._profiles.update_one(
            {"_id": user_id},
            {"$set": safe_updates},
        )
        return result.modified_count > 0
    
    def _format_user(self, user: dict, profile: dict | None) -> dict[str, Any]:
        """Format user document for API response."""
        return {
            "user_id": user["_id"],
            "username": user["username"],
            "created_at": user["created_at"].isoformat() if isinstance(user["created_at"], datetime) else user["created_at"],
            "status": user["status"],
            "profile": self._format_profile(profile) if profile else None,
        }
    
    def _format_profile(self, profile: dict) -> dict[str, Any]:
        """Format profile document for API response."""
        return {
            "user_id": profile["_id"],
            "name": profile.get("name", ""),
            "programme": profile.get("programme", ""),
            "year": profile.get("year", 0),
            "bio": profile.get("bio", ""),
            "skills": profile.get("skills", []),
            "updated_at": profile["updated_at"].isoformat() if isinstance(profile["updated_at"], datetime) else profile["updated_at"],
        }
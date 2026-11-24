"""
MongoDB Post Repository Implementation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.repositories.interfaces import PostRepository


class MongoPostRepository(PostRepository):
    """MongoDB implementation of PostRepository."""
    
    def __init__(self, db) -> None:
        self._db = db
        self._posts = db.posts
    
    def create_post(
        self,
        author_id: str,
        text: str,
    ) -> dict[str, Any]:
        """Create a new post."""
        now = datetime.now(UTC)
        post_id = str(uuid4())
        post_doc = {
            "_id": post_id,
            "author_id": author_id,
            "text": text,
            "created_at": now,
            "updated_at": now,
        }
        self._posts.insert_one(post_doc)
        return self._format_post(post_doc)
    
    def get_post(self, post_id: str) -> dict[str, Any] | None:
        """Get post by ID."""
        post = self._posts.find_one({"_id": post_id})
        if not post:
            return None
        return self._format_post(post)
    
    def get_posts_by_author(
        self,
        author_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get posts by author, newest first."""
        posts = list(self._posts.find(
            {"author_id": author_id}
        ).sort("created_at", -1).limit(limit))
        return [self._format_post(p) for p in posts]
    
    def delete_post(self, post_id: str, author_id: str) -> bool:
        """Delete a post (only by author)."""
        result = self._posts.delete_one({
            "_id": post_id,
            "author_id": author_id,
        })
        return result.deleted_count > 0
    
    def get_posts_by_authors(
        self,
        author_ids: list[str],
        limit_per_author: int = 50,
    ) -> dict[str, list[dict[str, Any]]]:
        """Get posts for multiple authors (for feed merging)."""
        result = {}
        for author_id in author_ids:
            posts = self.get_posts_by_author(author_id, limit_per_author)
            result[author_id] = posts
        return result
    
    def _format_post(self, post: dict) -> dict[str, Any]:
        """Format post document for API response."""
        return {
            "post_id": post["_id"],
            "author_id": post["author_id"],
            "text": post["text"],
            "created_at": post["created_at"].isoformat() if isinstance(post["created_at"], datetime) else post["created_at"],
            "updated_at": post["updated_at"].isoformat() if isinstance(post["updated_at"], datetime) else post["updated_at"],
        }
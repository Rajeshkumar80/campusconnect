"""
Post Service - Business logic for posts and feed.
"""

from __future__ import annotations

from typing import Any

from app.dsa import (
    create_post_streams_from_raw,
    merge_post_streams,
)
from app.extensions import get_mongo_db
from app.repositories.interfaces import ConnectionRepository, PostRepository
from app.repositories.mongo_connection_repository import MongoConnectionRepository
from app.repositories.mongo_post_repository import MongoPostRepository
from app.repositories.mongo_user_repository import MongoUserRepository
from app.services.engine import get_engine


class PostService:
    """Post service for managing posts and feed generation."""
    
    def __init__(self) -> None:
        self._engine = get_engine()
        db = get_mongo_db()
        self._post_repo: PostRepository = MongoPostRepository(db)
        self._conn_repo: ConnectionRepository = MongoConnectionRepository(db)
        self._user_repo = MongoUserRepository(db)
    
    def create_post(self, author_id: str, text: str) -> dict[str, Any]:
        """Create a new post."""
        # Create in repository
        post_doc = self._post_repo.create_post(author_id, text)
        
        return post_doc
    
    def get_own_posts(self, author_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get posts by author."""
        return self._post_repo.get_posts_by_author(author_id, limit)
    
    def delete_post(self, post_id: str, author_id: str) -> bool:
        """Delete a post (only by author)."""
        return self._post_repo.delete_post(post_id, author_id)
    
    def get_feed(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get home feed - merged posts from accepted connections."""
        # Get user's connections
        connection_ids = self._conn_repo.get_connections(user_id)
        
        if not connection_ids:
            return []
        
        # Get posts from each connection
        posts_by_author = self._post_repo.get_posts_by_authors(
            connection_ids,
            limit_per_author=50,
        )
        
        # Convert to streams for heap merge
        streams = create_post_streams_from_raw(posts_by_author, max_per_author=50)
        
        # Merge using heap
        merged_posts = merge_post_streams(streams, limit=limit)
        
        # Enrich with author info
        feed = []
        for post in merged_posts:
            author = self._user_repo.get_user_by_id(post.author_id)
            if author and author.get("status") == "active":
                profile = author.get("profile", {})
                feed.append({
                    "post_id": post.post_id,
                    "author_id": post.author_id,
                    "author_username": author["username"],
                    "author_name": profile.get("name", ""),
                    "text": post.text,
                    "created_at": post.created_at,
                })
        
        return feed
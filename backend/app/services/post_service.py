"""
Post Service - Business logic for posts and feed.
"""

from __future__ import annotations

from typing import Any

from flask import current_app

from app.dsa import (
    create_post_streams_from_raw,
    merge_post_streams,
)
from app.extensions import get_mongo_db
from app.media import delete_media_file
from app.repositories.interfaces import ConnectionRepository, PostRepository
from app.repositories.mongo_connection_repository import MongoConnectionRepository
from app.repositories.mongo_post_repository import MongoPostRepository
from app.repositories.mongo_user_repository import MongoUserRepository
from app.services.engine import get_engine
from app.services.social_service import SocialService


class PostService:
    """Post service for managing posts and feed generation."""

    def __init__(self) -> None:
        self._engine = get_engine()
        db = get_mongo_db()
        self._post_repo: PostRepository = MongoPostRepository(db)
        self._conn_repo: ConnectionRepository = MongoConnectionRepository(db)
        self._user_repo = MongoUserRepository(db)
        self._social = SocialService()

    def create_post(
        self,
        author_id: str,
        text: str,
        media: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new post, removing the uploaded file if persistence fails."""
        try:
            return self._post_repo.create_post(author_id, text, media)
        except Exception:
            delete_media_file(media, current_app.config["UPLOAD_FOLDER"])
            raise

    def _author_identity(self, user_id: str) -> dict[str, str]:
        user = self._user_repo.get_user_by_id(user_id) or {}
        profile = user.get("profile") or {}
        return {
            "author_username": user.get("username", ""),
            "author_name": profile.get("name", ""),
        }

    def get_own_posts(self, author_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get posts by author with interaction state for the viewer."""
        posts = self._post_repo.get_posts_by_author(author_id, limit)
        if not posts:
            return []
        identity = self._author_identity(author_id)
        return [
            {**post, **identity}
            for post in self._social.decorate_posts(posts, author_id)
        ]

    def get_user_posts(
        self, target_id: str, viewer_id: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get another student's posts for their profile page."""
        posts = self._post_repo.get_posts_by_author(target_id, limit)
        if not posts:
            return []
        identity = self._author_identity(target_id)
        return [
            {**post, **identity}
            for post in self._social.decorate_posts(posts, viewer_id)
        ]

    def delete_post(self, post_id: str, author_id: str) -> bool:
        """Delete a post (only by author) and its attachment."""
        post = self._post_repo.get_post(post_id)
        if not post or post["author_id"] != author_id:
            return False
        if not self._post_repo.delete_post(post_id, author_id):
            return False
        delete_media_file(post.get("media"), current_app.config["UPLOAD_FOLDER"])
        return True

    def get_feed(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get home feed - merged posts from accepted connections."""
        connection_ids = self._conn_repo.get_connections(user_id)
        if not connection_ids:
            return []

        posts_by_author = self._post_repo.get_posts_by_authors(
            connection_ids,
            limit_per_author=50,
        )
        streams = create_post_streams_from_raw(posts_by_author, max_per_author=50)
        merged_posts = merge_post_streams(streams, limit=limit)

        feed = []
        for post in merged_posts:
            author = self._user_repo.get_user_by_id(post.author_id)
            if author and author.get("status") == "active":
                profile = author.get("profile") or {}
                feed.append({
                    "post_id": post.post_id,
                    "author_id": post.author_id,
                    "author_username": author["username"],
                    "author_name": profile.get("name", ""),
                    "text": post.text,
                    "media": post.media,
                    "created_at": post.created_at,
                })

        return self._social.decorate_posts(feed, user_id)

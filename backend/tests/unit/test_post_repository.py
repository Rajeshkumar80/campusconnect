"""Unit tests for the MongoDB post repository formatting."""

from datetime import UTC, datetime
from types import SimpleNamespace

from app.repositories.mongo_post_repository import MongoPostRepository


def _repo() -> MongoPostRepository:
    """Build a repository without touching a real MongoDB connection."""
    return MongoPostRepository(SimpleNamespace(posts=None))


class TestFormatPost:
    def test_created_at_is_numeric_timestamp(self):
        repo = _repo()
        now = datetime.now(UTC)

        formatted = repo._format_post(
            {"_id": "p1", "author_id": "u1", "text": "hi", "created_at": now, "updated_at": now}
        )

        assert isinstance(formatted["created_at"], float)
        assert formatted["created_at"] == now.timestamp()

    def test_numeric_created_at_passes_through(self):
        repo = _repo()

        formatted = repo._format_post(
            {
                "_id": "p1",
                "author_id": "u1",
                "text": "hi",
                "created_at": 1000.0,
                "updated_at": 1000.0,
            }
        )

        assert formatted["created_at"] == 1000.0

    def test_formatted_posts_can_be_merged_by_the_feed_heap(self):
        """Regression: ISO strings used to make the heap merge raise TypeError."""
        from app.dsa import create_post_streams_from_raw, merge_post_streams

        repo = _repo()
        now = datetime.now(UTC)
        posts = [
            repo._format_post(
                {"_id": "p1", "author_id": "u1", "text": "a", "created_at": now, "updated_at": now}
            ),
            repo._format_post(
                {"_id": "p2", "author_id": "u2", "text": "b", "created_at": now, "updated_at": now}
            ),
        ]

        streams = create_post_streams_from_raw({"u1": posts[:1], "u2": posts[1:]})
        merged = merge_post_streams(streams, limit=10)

        assert len(merged) == 2

    def test_media_survives_the_feed_merge(self):
        from app.dsa import create_post_streams_from_raw, merge_post_streams

        repo = _repo()
        now = datetime.now(UTC)
        media = {"url": "/api/v1/media/abc.png", "type": "image"}
        post = repo._format_post(
            {
                "_id": "p1",
                "author_id": "u1",
                "text": "",
                "media": media,
                "created_at": now,
                "updated_at": now,
            }
        )

        merged = merge_post_streams(create_post_streams_from_raw({"u1": [post]}), limit=10)

        assert merged[0].media == media

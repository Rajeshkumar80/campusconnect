"""Likes, comments, notifications, direct messages and post sharing.

Kept in one service because they all read the same few collections and the
feature set is small. Mongo is accessed directly here: these documents are
not part of the DSA core, which stays pure Python.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from flask import current_app

from app.extensions import get_mongo_db
from app.media import delete_media_file
from app.repositories.mongo_connection_repository import MongoConnectionRepository
from app.repositories.mongo_user_repository import MongoUserRepository

MAX_MESSAGE_LENGTH = 2000
MAX_COMMENT_LENGTH = 1000


def _now() -> datetime:
    return datetime.now(UTC)


def _timestamp(value: Any) -> float:
    """Normalise Mongo datetimes and ISO strings to a Unix timestamp."""
    if isinstance(value, datetime):
        return (value.replace(tzinfo=UTC) if value.tzinfo is None else value).timestamp()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class SocialService:
    """Interaction layer for posts, notifications and messages."""

    def __init__(self) -> None:
        db = get_mongo_db()
        self._posts = db.posts
        self._likes = db.post_likes
        self._comments = db.comments
        self._messages = db.messages
        self._users = db.users
        self._user_repo = MongoUserRepository(db)
        self._conn_repo = MongoConnectionRepository(db)

    # ---- shared helpers -------------------------------------------------

    def _summary(self, user_id: str) -> dict[str, Any] | None:
        user = self._user_repo.get_user_by_id(user_id)
        if not user or user.get("status") != "active":
            return None
        profile = user.get("profile") or {}
        return {
            "user_id": user["user_id"],
            "username": user["username"],
            "name": profile.get("name", ""),
            "programme": profile.get("programme", ""),
            "year": profile.get("year", 0),
        }

    def _post_snapshot(self, post_id: str) -> dict[str, Any] | None:
        post = self._posts.find_one({"_id": post_id})
        if not post:
            return None
        author = self._summary(post["author_id"])
        return {
            "post_id": post_id,
            "text": post.get("text", ""),
            "media": post.get("media"),
            "author_name": (author or {}).get("name", ""),
            "author_username": (author or {}).get("username", ""),
        }

    def decorate_posts(
        self, posts: list[dict[str, Any]], viewer_id: str | None
    ) -> list[dict[str, Any]]:
        """Attach like/comment counts, viewer's like state, and recent likers."""
        post_ids = [post["post_id"] for post in posts]
        if not post_ids:
            return posts

        like_counts: dict[str, int] = {}
        comment_counts: dict[str, int] = {}
        liked: set[str] = set()

        for row in self._likes.aggregate([
            {"$match": {"post_id": {"$in": post_ids}}},
            {"$group": {"_id": "$post_id", "n": {"$sum": 1}}},
        ]):
            like_counts[row["_id"]] = row["n"]
        for row in self._comments.aggregate([
            {"$match": {"post_id": {"$in": post_ids}}},
            {"$group": {"_id": "$post_id", "n": {"$sum": 1}}},
        ]):
            comment_counts[row["_id"]] = row["n"]
        if viewer_id:
            for row in self._likes.find(
                {"post_id": {"$in": post_ids}, "user_id": viewer_id}, {"post_id": 1}
            ):
                liked.add(row["post_id"])

        # Fetch recent likers for posts that have likes
        likers_map: dict[str, list[dict[str, Any]]] = {}
        for post_id in post_ids:
            if like_counts.get(post_id, 0) > 0:
                likers_map[post_id] = self.get_likers(post_id, 5)

        for post in posts:
            post_id = post["post_id"]
            post["like_count"] = like_counts.get(post_id, 0)
            post["comment_count"] = comment_counts.get(post_id, 0)
            post["liked_by_me"] = post_id in liked
            post["likers"] = likers_map.get(post_id, [])
        return posts

    # ---- likes and comments --------------------------------------------

    def toggle_like(self, post_id: str, user_id: str) -> dict[str, Any]:
        if not self._posts.find_one({"_id": post_id}, {"_id": 1}):
            raise ValueError("Post not found")
        like_id = f"{post_id}:{user_id}"
        existing = self._likes.find_one({"_id": like_id})
        if existing:
            self._likes.delete_one({"_id": like_id})
            liked = False
        else:
            self._likes.insert_one(
                {"_id": like_id, "post_id": post_id, "user_id": user_id, "created_at": _now()}
            )
            liked = True
        return {"liked": liked, "like_count": self._likes.count_documents({"post_id": post_id})}

    def _format_comment(self, doc: dict[str, Any]) -> dict[str, Any]:
        author = self._summary(doc["author_id"]) or {}
        return {
            "comment_id": doc["_id"],
            "post_id": doc["post_id"],
            "author_id": doc["author_id"],
            "author_name": author.get("name", ""),
            "author_username": author.get("username", ""),
            "text": doc["text"],
            "created_at": _timestamp(doc["created_at"]),
        }

    def get_comments(self, post_id: str) -> list[dict[str, Any]]:
        docs = self._comments.find({"post_id": post_id}).sort("created_at", 1).limit(200)
        return [self._format_comment(doc) for doc in docs]

    def add_comment(self, post_id: str, user_id: str, text: str) -> dict[str, Any]:
        text = text.strip()
        if not text:
            raise ValueError("Write something first")
        if len(text) > MAX_COMMENT_LENGTH:
            raise ValueError(f"Comment too long (max {MAX_COMMENT_LENGTH} characters)")
        if not self._posts.find_one({"_id": post_id}, {"_id": 1}):
            raise ValueError("Post not found")
        doc = {
            "_id": str(uuid4()),
            "post_id": post_id,
            "author_id": user_id,
            "text": text,
            "created_at": _now(),
        }
        self._comments.insert_one(doc)
        return self._format_comment(doc)

    def get_likers(self, post_id: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get recent users who liked a post, with their names."""
        docs = self._likes.find({"post_id": post_id}).sort("created_at", -1).limit(limit)
        likers = []
        for doc in docs:
            user = self._summary(doc["user_id"])
            if user:
                likers.append({
                    "user_id": user["user_id"],
                    "name": user["name"],
                    "username": user["username"],
                })
        return likers

    # ---- notifications --------------------------------------------------

    def _my_post_ids(self, user_id: str) -> list[str]:
        return [p["_id"] for p in self._posts.find({"author_id": user_id}, {"_id": 1})]

    def get_notifications(self, user_id: str) -> dict[str, Any]:
        items: list[dict[str, Any]] = []

        for request in self._conn_repo.get_pending_incoming(user_id):
            actor = self._summary(request["sender_id"])
            if not actor:
                continue
            items.append({
                "id": request["request_id"],
                "type": "connection_request",
                "actor": actor,
                "text": "sent you a connection request",
                "created_at": _timestamp(request["created_at"]),
            })

        post_ids = self._my_post_ids(user_id)
        post_text = {
            p["_id"]: (p.get("text") or "")[:90]
            for p in self._posts.find({"_id": {"$in": post_ids}}, {"text": 1})
        }

        for like in self._likes.find(
            {"post_id": {"$in": post_ids}, "user_id": {"$ne": user_id}}
        ).sort("created_at", -1).limit(25):
            actor = self._summary(like["user_id"])
            if actor:
                items.append({
                    "id": like["_id"],
                    "type": "like",
                    "actor": actor,
                    "post_id": like["post_id"],
                    "post_text": post_text.get(like["post_id"], ""),
                    "text": "liked your post",
                    "created_at": _timestamp(like["created_at"]),
                })

        for comment in self._comments.find(
            {"post_id": {"$in": post_ids}, "author_id": {"$ne": user_id}}
        ).sort("created_at", -1).limit(25):
            actor = self._summary(comment["author_id"])
            if actor:
                items.append({
                    "id": comment["_id"],
                    "type": "comment",
                    "actor": actor,
                    "post_id": comment["post_id"],
                    "post_text": post_text.get(comment["post_id"], ""),
                    "text": f"commented: {comment['text'][:90]}",
                    "created_at": _timestamp(comment["created_at"]),
                })

        items.sort(key=lambda item: item["created_at"], reverse=True)

        user = self._users.find_one({"_id": user_id}, {"notifications_seen_at": 1}) or {}
        seen_at = _timestamp(user.get("notifications_seen_at"))
        unread = sum(1 for item in items if item["created_at"] > seen_at)
        return {"notifications": items[:40], "unread": unread}

    def mark_notifications_read(self, user_id: str) -> None:
        self._users.update_one(
            {"_id": user_id}, {"$set": {"notifications_seen_at": _now()}}
        )

    # ---- messages -------------------------------------------------------

    def _format_message(self, doc: dict[str, Any]) -> dict[str, Any]:
        shared = (
            self._post_snapshot(doc["shared_post_id"])
            if doc.get("shared_post_id")
            else None
        )
        return {
            "message_id": doc["_id"],
            "sender_id": doc["sender_id"],
            "recipient_id": doc["recipient_id"],
            "text": doc.get("text", ""),
            "media": doc.get("media"),
            "shared_post": shared,
            "created_at": _timestamp(doc["created_at"]),
            "read_at": _timestamp(doc["read_at"]) if doc.get("read_at") else None,
        }

    def get_threads(self, user_id: str) -> list[dict[str, Any]]:
        partner_ids = set(self._conn_repo.get_connections(user_id))
        for doc in self._messages.find(
            {"$or": [{"sender_id": user_id}, {"recipient_id": user_id}]},
            {"sender_id": 1, "recipient_id": 1},
        ).limit(500):
            partner_ids.add(
                doc["recipient_id"] if doc["sender_id"] == user_id else doc["sender_id"]
            )

        threads = []
        for partner_id in partner_ids:
            user = self._summary(partner_id)
            if not user:
                continue
            last = self._messages.find_one(
                {"$or": [
                    {"sender_id": user_id, "recipient_id": partner_id},
                    {"sender_id": partner_id, "recipient_id": user_id},
                ]}
            , sort=[("created_at", -1)])
            unread = self._messages.count_documents({
                "sender_id": partner_id,
                "recipient_id": user_id,
                "read_at": None,
            })
            threads.append({
                "user": user,
                "last_message": self._format_message(last) if last else None,
                "unread": unread,
            })

        threads.sort(
            key=lambda t: (t["last_message"] or {}).get("created_at", 0), reverse=True
        )
        return threads

    def get_conversation(self, user_id: str, other_id: str) -> dict[str, Any]:
        other = self._summary(other_id)
        if not other:
            raise ValueError("User not found")
        if not self._conn_repo.are_connected(user_id, other_id):
            raise PermissionError("Connect with this student to message them")

        self._messages.update_many(
            {"sender_id": other_id, "recipient_id": user_id, "read_at": None},
            {"$set": {"read_at": _now()}},
        )
        docs = list(
            self._messages.find({"$or": [
                {"sender_id": user_id, "recipient_id": other_id},
                {"sender_id": other_id, "recipient_id": user_id},
            ]}).sort("created_at", -1).limit(200)
        )
        docs.reverse()
        return {
            "user": other,
            "messages": [self._format_message(doc) for doc in docs],
        }

    def send_message(
        self,
        sender_id: str,
        recipient_id: str,
        text: str = "",
        media: dict[str, Any] | None = None,
        shared_post_id: str | None = None,
    ) -> dict[str, Any]:
        text = (text or "").strip()
        if not text and not media and not shared_post_id:
            raise ValueError("Write a message or attach a file")
        if len(text) > MAX_MESSAGE_LENGTH:
            raise ValueError(f"Message too long (max {MAX_MESSAGE_LENGTH} characters)")
        if sender_id == recipient_id:
            raise ValueError("You cannot message yourself")
        if not self._summary(recipient_id):
            raise ValueError("Recipient not found")
        if not self._conn_repo.are_connected(sender_id, recipient_id):
            raise PermissionError("Connect with this student to message them")
        if shared_post_id and not self._posts.find_one({"_id": shared_post_id}, {"_id": 1}):
            raise ValueError("Post not found")

        doc = {
            "_id": str(uuid4()),
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "text": text,
            "media": media,
            "shared_post_id": shared_post_id,
            "created_at": _now(),
            "read_at": None,
        }
        try:
            self._messages.insert_one(doc)
        except Exception:
            delete_media_file(media, current_app.config["UPLOAD_FOLDER"])
            raise
        return self._format_message(doc)

    def share_post(
        self, sender_id: str, post_id: str, recipient_ids: list[str], note: str = ""
    ) -> int:
        if not self._posts.find_one({"_id": post_id}, {"_id": 1}):
            raise ValueError("Post not found")
        if not recipient_ids:
            raise ValueError("Pick at least one connection")
        sent = 0
        for recipient_id in recipient_ids[:20]:
            self.send_message(
                sender_id, recipient_id, text=note, shared_post_id=post_id
            )
            sent += 1
        return sent

    def unread_counts(self, user_id: str) -> dict[str, int]:
        unread_messages = self._messages.count_documents({
            "recipient_id": user_id,
            "read_at": None,
        })
        return {
            "messages": unread_messages,
            "notifications": self.get_notifications(user_id)["unread"],
        }

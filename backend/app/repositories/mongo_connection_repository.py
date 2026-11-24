"""
MongoDB Connection Repository Implementation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.repositories.interfaces import ConnectionRepository


class MongoConnectionRepository(ConnectionRepository):
    """MongoDB implementation of ConnectionRepository."""
    
    def __init__(self, db) -> None:
        self._db = db
        self._requests = db.connection_requests
        self._connections = db.connections
    
    def _canonical_pair(self, user_a: str, user_b: str) -> tuple[str, str]:
        """Return canonical ordered pair (lower, higher)."""
        return (user_a, user_b) if user_a < user_b else (user_b, user_a)
    
    # Connection requests
    def create_request(
        self,
        sender_id: str,
        recipient_id: str,
    ) -> dict[str, Any]:
        """Create a new pending connection request."""
        now = datetime.now(UTC)
        request_id = str(uuid4())
        request_doc = {
            "_id": request_id,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        self._requests.insert_one(request_doc)
        return self._format_request(request_doc)
    
    def get_request(self, request_id: str) -> dict[str, Any] | None:
        """Get request by ID."""
        request = self._requests.find_one({"_id": request_id})
        if not request:
            return None
        return self._format_request(request)
    
    def update_request_status(
        self,
        request_id: str,
        status: str,
    ) -> bool:
        """Update request status (accepted, rejected, cancelled)."""
        result = self._requests.update_one(
            {"_id": request_id, "status": "pending"},
            {"$set": {"status": status, "updated_at": datetime.now(UTC)}},
        )
        return result.modified_count > 0
    
    def get_pending_incoming(self, user_id: str) -> list[dict[str, Any]]:
        """Get pending requests where user is recipient."""
        requests = list(self._requests.find({
            "recipient_id": user_id,
            "status": "pending",
        }).sort("created_at", -1))
        return [self._format_request(r) for r in requests]
    
    def get_pending_outgoing(self, user_id: str) -> list[dict[str, Any]]:
        """Get pending requests where user is sender."""
        requests = list(self._requests.find({
            "sender_id": user_id,
            "status": "pending",
        }).sort("created_at", -1))
        return [self._format_request(r) for r in requests]
    
    def has_pending_between(self, user_a: str, user_b: str) -> bool:
        """Check if pending request exists between users."""
        return self._requests.count_documents({
            "$or": [
                {"sender_id": user_a, "recipient_id": user_b, "status": "pending"},
                {"sender_id": user_b, "recipient_id": user_a, "status": "pending"},
            ],
        }) > 0
    
    def get_all_pending_requests(self) -> list[dict[str, Any]]:
        """Get all pending requests (for startup rebuild)."""
        requests = list(self._requests.find({"status": "pending"}))
        return [self._format_request(r) for r in requests]
    
    # Accepted connections
    def create_connection(self, user_a: str, user_b: str) -> dict[str, Any]:
        """Create an accepted connection (undirected edge)."""
        user_low, user_high = self._canonical_pair(user_a, user_b)
        now = datetime.now(UTC)
        connection_doc = {
            "_id": f"{user_low}:{user_high}",
            "user_low": user_low,
            "user_high": user_high,
            "created_at": now,
        }
        self._connections.insert_one(connection_doc)
        return self._format_connection(connection_doc)
    
    def remove_connection(self, user_a: str, user_b: str) -> bool:
        """Remove an accepted connection."""
        user_low, user_high = self._canonical_pair(user_a, user_b)
        result = self._connections.delete_one({
            "user_low": user_low,
            "user_high": user_high,
        })
        return result.deleted_count > 0
    
    def get_connections(self, user_id: str) -> list[str]:
        """Get all connected user IDs for a user."""
        connections = self._connections.find({
            "$or": [
                {"user_low": user_id},
                {"user_high": user_id},
            ],
        })
        result = []
        for conn in connections:
            other = conn["user_high"] if conn["user_low"] == user_id else conn["user_low"]
            result.append(other)
        return result
    
    def are_connected(self, user_a: str, user_b: str) -> bool:
        """Check if two users are connected."""
        user_low, user_high = self._canonical_pair(user_a, user_b)
        return self._connections.count_documents({
            "user_low": user_low,
            "user_high": user_high,
        }) > 0
    
    def get_all_accepted_connections(self) -> list[dict[str, Any]]:
        """Get all accepted connections (for startup rebuild)."""
        connections = list(self._connections.find({}))
        return [self._format_connection(c) for c in connections]
    
    def _format_request(self, request: dict) -> dict[str, Any]:
        """Format request document for API response."""
        return {
            "request_id": request["_id"],
            "sender_id": request["sender_id"],
            "recipient_id": request["recipient_id"],
            "status": request["status"],
            "created_at": request["created_at"].isoformat() if isinstance(request["created_at"], datetime) else request["created_at"],
            "updated_at": request["updated_at"].isoformat() if isinstance(request["updated_at"], datetime) else request["updated_at"],
        }
    
    def _format_connection(self, connection: dict) -> dict[str, Any]:
        """Format connection document for API response."""
        return {
            "user_low": connection["user_low"],
            "user_high": connection["user_high"],
            "created_at": connection["created_at"].isoformat() if isinstance(connection["created_at"], datetime) else connection["created_at"],
        }
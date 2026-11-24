"""
Connection Service - Business logic for connections and requests.
"""

from __future__ import annotations

from typing import Any

from app.extensions import get_mongo_db
from app.repositories.interfaces import ConnectionRepository
from app.repositories.mongo_connection_repository import MongoConnectionRepository
from app.repositories.mongo_user_repository import MongoUserRepository
from app.services.engine import get_engine


class ConnectionService:
    """Connection service for managing connection requests and accepted connections."""
    
    def __init__(self) -> None:
        self._engine = get_engine()
        db = get_mongo_db()
        self._conn_repo: ConnectionRepository = MongoConnectionRepository(db)
        self._user_repo = MongoUserRepository(db)
    
    def get_connections(self, user_id: str) -> list[dict[str, Any]]:
        """Get user's accepted connections with profile info."""
        connected_ids = self._conn_repo.get_connections(user_id)
        
        connections = []
        for conn_id in connected_ids:
            user = self._user_repo.get_user_by_id(conn_id)
            if user and user.get("status") == "active":
                profile = user.get("profile", {})
                connections.append({
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "name": profile.get("name", ""),
                    "programme": profile.get("programme", ""),
                    "year": profile.get("year", 0),
                })
        
        return connections
    
    def send_request(self, sender_id: str, recipient_id: str) -> dict[str, Any]:
        """Send a connection request."""
        # Check recipient exists
        recipient = self._user_repo.get_user_by_id(recipient_id)
        if not recipient or recipient.get("status") != "active":
            raise ValueError("Recipient not found")
        
        # Check if already connected
        if self._conn_repo.are_connected(sender_id, recipient_id):
            raise ValueError("Already connected")
        
        # Check for existing pending request
        if self._conn_repo.has_pending_between(sender_id, recipient_id):
            raise ValueError("Pending request already exists")
        
        # Create request in repository
        request_doc = self._conn_repo.create_request(sender_id, recipient_id)
        
        # Update DSA engine request queue
        self._engine.request_queue.create_request(sender_id, recipient_id)
        
        return request_doc
    
    def get_incoming_requests(self, user_id: str) -> list[dict[str, Any]]:
        """Get incoming pending requests."""
        return self._conn_repo.get_pending_incoming(user_id)
    
    def get_outgoing_requests(self, user_id: str) -> list[dict[str, Any]]:
        """Get outgoing pending requests."""
        return self._conn_repo.get_pending_outgoing(user_id)
    
    def accept_request(self, request_id: str, actor_id: str) -> dict[str, Any]:
        """Accept a connection request."""
        # Get request to verify
        request_doc = self._conn_repo.get_request(request_id)
        if not request_doc:
            raise ValueError("Request not found")
        
        if request_doc["recipient_id"] != actor_id:
            raise ValueError("Only the recipient can accept this request")
        
        if request_doc["status"] != "pending":
            raise ValueError("Request is not pending")
        
        sender_id = request_doc["sender_id"]
        recipient_id = request_doc["recipient_id"]
        
        # Update repository
        self._conn_repo.update_request_status(request_id, "accepted")
        self._conn_repo.create_connection(sender_id, recipient_id)
        
        # Update DSA engine
        self._engine.request_queue.accept_request(request_id, actor_id)
        self._engine.graph.add_edge(sender_id, recipient_id)
        
        return self._conn_repo.get_request(request_id)
    
    def reject_request(self, request_id: str, actor_id: str) -> dict[str, Any]:
        """Reject a connection request."""
        request_doc = self._conn_repo.get_request(request_id)
        if not request_doc:
            raise ValueError("Request not found")
        
        if request_doc["recipient_id"] != actor_id:
            raise ValueError("Only the recipient can reject this request")
        
        if request_doc["status"] != "pending":
            raise ValueError("Request is not pending")
        
        # Update repository
        self._conn_repo.update_request_status(request_id, "rejected")
        
        # Update DSA engine
        self._engine.request_queue.reject_request(request_id, actor_id)
        
        return self._conn_repo.get_request(request_id)
    
    def cancel_request(self, request_id: str, actor_id: str) -> dict[str, Any]:
        """Cancel a sent connection request."""
        request_doc = self._conn_repo.get_request(request_id)
        if not request_doc:
            raise ValueError("Request not found")
        
        if request_doc["sender_id"] != actor_id:
            raise ValueError("Only the sender can cancel this request")
        
        if request_doc["status"] != "pending":
            raise ValueError("Request is not pending")
        
        # Update repository
        self._conn_repo.update_request_status(request_id, "cancelled")
        
        # Update DSA engine
        self._engine.request_queue.cancel_request(request_id, actor_id)
        
        return self._conn_repo.get_request(request_id)
    
    def remove_connection(self, user_a: str, user_b: str) -> bool:
        """Remove an accepted connection."""
        # Remove from repository
        success = self._conn_repo.remove_connection(user_a, user_b)
        if not success:
            return False
        
        # Update DSA engine
        self._engine.graph.remove_edge(user_a, user_b)
        
        return True
    
    def get_mutual_connections(self, user_a: str, user_b: str) -> list[dict[str, Any]]:
        """Get mutual connections between two users."""
        mutual_ids = self._engine.graph.mutual_neighbors(user_a, user_b)
        
        mutual = []
        for uid in mutual_ids:
            user = self._user_repo.get_user_by_id(uid)
            if user and user.get("status") == "active":
                profile = user.get("profile", {})
                mutual.append({
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "name": profile.get("name", ""),
                    "programme": profile.get("programme", ""),
                    "year": profile.get("year", 0),
                })
        
        return mutual
    
    def get_connection_degree(self, source: str, target: str) -> dict[str, Any]:
        """Get degree of connection between two users."""
        from app.dsa import degree_label, degree_of_connection, shortest_path
        
        degree = degree_of_connection(self._engine.graph, source, target)
        label = degree_label(self._engine.graph, source, target)
        path = shortest_path(self._engine.graph, source, target)
        
        return {
            "degree": degree,
            "label": label,
            "path": path,
            "connected": degree is not None,
        }
    
    def get_shortest_path(self, source: str, target: str) -> list[str] | None:
        """Get shortest path between two users."""
        from app.dsa import shortest_path
        return shortest_path(self._engine.graph, source, target)
    
    def get_suggestions(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get people you may know suggestions."""
        # Get pending request IDs to exclude
        incoming = self._conn_repo.get_pending_incoming(user_id)
        outgoing = self._conn_repo.get_pending_outgoing(user_id)
        pending_ids = {r["sender_id"] for r in incoming} | {r["recipient_id"] for r in outgoing}
        
        # Get suggestions from DSA engine
        suggestions = self._engine.get_suggestions_with_explanation(
            user_id,
            limit=limit,
            exclude_pending=pending_ids,
        )
        
        # Enrich with user profile data
        enriched = []
        for s in suggestions:
            user = self._user_repo.get_user_by_id(s["user_id"])
            if user and user.get("status") == "active":
                profile = user.get("profile", {})
                enriched.append({
                    "user_id": user["user_id"],
                    "username": user["username"],
                    "name": profile.get("name", ""),
                    "programme": profile.get("programme", ""),
                    "year": profile.get("year", 0),
                    "score": s["score"],
                    "mutual_count": s["mutual_count"],
                    "explanation": s["explanation"],
                })
        
        return enriched
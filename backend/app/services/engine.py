"""
DSA Engine Service - In-memory data structures initialization and management.

This service coordinates the DSA core modules and manages the in-memory
graph, trie, request queue, and other algorithmic data structures.
"""

from __future__ import annotations

from flask import Flask

from app.dsa import (
    Graph,
    RequestQueue,
    Trie,
)
from app.repositories.interfaces import (
    ConnectionRepository,
    PostRepository,
    UserRepository,
)


class DSAEngine:
    """
    Central DSA engine managing all in-memory data structures.
    
    Rebuilt from persistent storage on startup, updated through
    service layer after successful persistence operations.
    """
    
    def __init__(self) -> None:
        self.graph = Graph()
        self.trie = Trie()
        self.request_queue = RequestQueue()
        self._initialized = False
    
    def initialize(
        self,
        user_repo: UserRepository,
        connection_repo: ConnectionRepository,
        post_repo: PostRepository,
    ) -> None:
        """
        Rebuild all in-memory structures from persistent storage.
        
        Called once on application startup.
        """
        # Load users and build trie
        users = user_repo.get_all_users()
        for user in users:
            self.graph.add_user(user["user_id"])
            # Index username and display name for prefix search
            self.trie.insert(user["username"], user["user_id"])
            if user.get("name"):
                self.trie.insert(user["name"], user["user_id"])
        
        # Load accepted connections and build graph
        connections = connection_repo.get_all_accepted_connections()
        for conn in connections:
            self.graph.add_edge(conn["user_low"], conn["user_high"])
        
        # Load pending requests
        pending_requests = connection_repo.get_all_pending_requests()
        self.request_queue.rebuild_from_requests(pending_requests)
        
        self._initialized = True
    
    def rebuild_graph(self, connection_repo: ConnectionRepository) -> None:
        """Rebuild just the graph from persistent connections."""
        self.graph = Graph()
        # Re-add users first
        # Note: In production, we'd reload users too. For simplicity,
        # we assume users haven't changed or are re-added via user repo.
        connections = connection_repo.get_all_accepted_connections()
        for conn in connections:
            self.graph.add_edge(conn["user_low"], conn["user_high"])
    
    def rebuild_trie(self, user_repo: UserRepository) -> None:
        """Rebuild trie from all users."""
        self.trie = Trie()
        users = user_repo.get_all_users()
        for user in users:
            self.trie.insert(user["username"], user["user_id"])
            if user.get("name"):
                self.trie.insert(user["name"], user["user_id"])
    
    def rebuild_request_queue(self, connection_repo: ConnectionRepository) -> None:
        """Rebuild request queue from pending requests."""
        pending_requests = connection_repo.get_all_pending_requests()
        self.request_queue.rebuild_from_requests(pending_requests)
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized


# Global engine instance
_engine: DSAEngine | None = None


def init_engine(app: Flask) -> None:
    """Initialize the DSA engine within Flask app context."""
    global _engine
    _engine = DSAEngine()
    
    # Initialize with repositories (will be called after extensions setup)
    with app.app_context():
        from app.extensions import get_mongo_db
        from app.repositories.mongo_connection_repository import (
            MongoConnectionRepository,
        )
        from app.repositories.mongo_post_repository import MongoPostRepository
        from app.repositories.mongo_user_repository import MongoUserRepository
        
        db = get_mongo_db()
        user_repo = MongoUserRepository(db)
        connection_repo = MongoConnectionRepository(db)
        post_repo = MongoPostRepository(db)
        
        _engine.initialize(user_repo, connection_repo, post_repo)


def get_engine() -> DSAEngine:
    """Get the global DSA engine instance."""
    if _engine is None:
        raise RuntimeError("DSA Engine not initialized. Call init_engine first.")
    return _engine
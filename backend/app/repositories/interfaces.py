"""
Repository Interfaces - Abstract base classes for data access.

These interfaces define the contract between services and persistence layer.
Allows swapping implementations (MongoDB, in-memory test adapter, etc.)
without changing service logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class UserRepository(ABC):
    """Interface for user and profile data access."""
    
    @abstractmethod
    def create_user(
        self,
        user_id: str,
        username: str,
        password_hash: str,
    ) -> dict[str, Any]:
        """Create a new user account."""
        ...
    
    @abstractmethod
    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Get user by ID."""
        ...
    
    @abstractmethod
    def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        """Get user by normalized username."""
        ...
    
    @abstractmethod
    def get_all_users(self) -> list[dict[str, Any]]:
        """Get all users (for startup rebuild)."""
        ...
    
    @abstractmethod
    def update_user(self, user_id: str, updates: dict[str, Any]) -> bool:
        """Update user fields."""
        ...
    
    # Profile methods
    @abstractmethod
    def create_profile(self, user_id: str, profile_data: dict[str, Any]) -> dict[str, Any]:
        """Create user profile."""
        ...
    
    @abstractmethod
    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        """Get user profile."""
        ...
    
    @abstractmethod
    def update_profile(self, user_id: str, updates: dict[str, Any]) -> bool:
        """Update user profile."""
        ...


class ConnectionRepository(ABC):
    """Interface for connection and request data access."""
    
    # Connection requests
    @abstractmethod
    def create_request(
        self,
        sender_id: str,
        recipient_id: str,
    ) -> dict[str, Any]:
        """Create a new pending connection request."""
        ...
    
    @abstractmethod
    def get_request(self, request_id: str) -> dict[str, Any] | None:
        """Get request by ID."""
        ...
    
    @abstractmethod
    def update_request_status(
        self,
        request_id: str,
        status: str,
    ) -> bool:
        """Update request status (accepted, rejected, cancelled)."""
        ...
    
    @abstractmethod
    def get_pending_incoming(self, user_id: str) -> list[dict[str, Any]]:
        """Get pending requests where user is recipient."""
        ...
    
    @abstractmethod
    def get_pending_outgoing(self, user_id: str) -> list[dict[str, Any]]:
        """Get pending requests where user is sender."""
        ...
    
    @abstractmethod
    def has_pending_between(self, user_a: str, user_b: str) -> bool:
        """Check if pending request exists between users."""
        ...
    
    @abstractmethod
    def get_all_pending_requests(self) -> list[dict[str, Any]]:
        """Get all pending requests (for startup rebuild)."""
        ...
    
    # Accepted connections
    @abstractmethod
    def create_connection(self, user_a: str, user_b: str) -> dict[str, Any]:
        """Create an accepted connection (undirected edge)."""
        ...
    
    @abstractmethod
    def remove_connection(self, user_a: str, user_b: str) -> bool:
        """Remove an accepted connection."""
        ...
    
    @abstractmethod
    def get_connections(self, user_id: str) -> list[str]:
        """Get all connected user IDs for a user."""
        ...
    
    @abstractmethod
    def are_connected(self, user_a: str, user_b: str) -> bool:
        """Check if two users are connected."""
        ...
    
    @abstractmethod
    def get_all_accepted_connections(self) -> list[dict[str, Any]]:
        """Get all accepted connections (for startup rebuild)."""
        ...


class PostRepository(ABC):
    """Interface for post data access."""
    
    @abstractmethod
    def create_post(
        self,
        author_id: str,
        text: str,
    ) -> dict[str, Any]:
        """Create a new post."""
        ...
    
    @abstractmethod
    def get_post(self, post_id: str) -> dict[str, Any] | None:
        """Get post by ID."""
        ...
    
    @abstractmethod
    def get_posts_by_author(
        self,
        author_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get posts by author, newest first."""
        ...
    
    @abstractmethod
    def delete_post(self, post_id: str, author_id: str) -> bool:
        """Delete a post (only by author)."""
        ...
    
    @abstractmethod
    def get_posts_by_authors(
        self,
        author_ids: list[str],
        limit_per_author: int = 50,
    ) -> dict[str, list[dict[str, Any]]]:
        """Get posts for multiple authors (for feed merging)."""
        ...


class RepositoryFactory(ABC):
    """Factory for creating repository instances."""
    
    @abstractmethod
    def create_user_repository(self) -> UserRepository:
        ...
    
    @abstractmethod
    def create_connection_repository(self) -> ConnectionRepository:
        ...
    
    @abstractmethod
    def create_post_repository(self) -> PostRepository:
        ...
"""
DSA Core: Adjacency-list graph for accepted connections.

Represents the undirected student connection network using adjacency lists.
Invariants:
- No self-edges
- No duplicate edges
- Undirected symmetry: v in adjacency[u] iff u in adjacency[v]
- Isolated users have empty neighbour sets
"""

from __future__ import annotations

from collections.abc import Iterable


class Graph:
    """
    Undirected graph using adjacency lists (dict of sets).
    
    Space complexity: O(V + E) where V = users, E = accepted connections.
    All operations maintain the undirected invariant.
    """

    def __init__(self) -> None:
        self._adjacency: dict[str, set[str]] = {}

    def add_user(self, user_id: str) -> None:
        """
        Add an isolated user to the graph.
        
        Time: O(1) average
        Idempotent: safe to call multiple times.
        """
        if user_id not in self._adjacency:
            self._adjacency[user_id] = set()

    def add_edge(self, user_a: str, user_b: str) -> None:
        """
        Add an undirected edge between two users.
        
        Time: O(1) average
        Raises:
            ValueError: if user_a == user_b (self-edge) or edge already exists.
        """
        if user_a == user_b:
            raise ValueError("Self-edges are not allowed")
        
        self.add_user(user_a)
        self.add_user(user_b)
        
        if user_b in self._adjacency[user_a]:
            raise ValueError(f"Edge already exists between {user_a} and {user_b}")
        
        self._adjacency[user_a].add(user_b)
        self._adjacency[user_b].add(user_a)

    def remove_edge(self, user_a: str, user_b: str) -> None:
        """
        Remove an undirected edge between two users.
        
        Time: O(1) average
        Raises:
            ValueError: if edge does not exist.
        """
        if user_a not in self._adjacency or user_b not in self._adjacency:
            raise ValueError("One or both users not in graph")
        
        if user_b not in self._adjacency[user_a]:
            raise ValueError(f"Edge does not exist between {user_a} and {user_b}")
        
        self._adjacency[user_a].remove(user_b)
        self._adjacency[user_b].remove(user_a)

    def neighbors(self, user_id: str) -> set[str]:
        """
        Get the neighbour set of a user.
        
        Time: O(1) average
        Returns: Copy of the neighbour set (safe to mutate).
        Raises:
            KeyError: if user not in graph.
        """
        if user_id not in self._adjacency:
            raise KeyError(f"User {user_id} not in graph")
        return self._adjacency[user_id].copy()

    def mutual_neighbors(self, user_a: str, user_b: str) -> set[str]:
        """
        Get mutual neighbours (intersection of neighbour sets).
        
        Time: O(min(deg(u), deg(v))) average
        Returns: Set of user IDs that are neighbours of both users.
        """
        if user_a not in self._adjacency or user_b not in self._adjacency:
            return set()
        # Iterate over smaller set for efficiency
        neighbors_a = self._adjacency[user_a]
        neighbors_b = self._adjacency[user_b]
        if len(neighbors_a) > len(neighbors_b):
            neighbors_a, neighbors_b = neighbors_b, neighbors_a
        return {n for n in neighbors_a if n in neighbors_b}

    def degree(self, user_id: str) -> int:
        """Get the degree (number of connections) of a user."""
        if user_id not in self._adjacency:
            raise KeyError(f"User {user_id} not in graph")
        return len(self._adjacency[user_id])

    def has_user(self, user_id: str) -> bool:
        """Check if user exists in graph."""
        return user_id in self._adjacency

    def has_edge(self, user_a: str, user_b: str) -> bool:
        """Check if an edge exists between two users."""
        return (
            user_a in self._adjacency
            and user_b in self._adjacency[user_a]
        )

    def all_users(self) -> set[str]:
        """Get all user IDs in the graph."""
        return set(self._adjacency.keys())

    def edge_count(self) -> int:
        """Get total number of undirected edges."""
        return sum(len(neighbors) for neighbors in self._adjacency.values()) // 2

    def rebuild_from_edges(self, edges: Iterable[tuple[str, str]]) -> None:
        """
        Rebuild the entire graph from a collection of edges.
        Used for startup reconstruction from persistent storage.
        
        Time: O(V + E)
        """
        self._adjacency.clear()
        for user_a, user_b in edges:
            self.add_edge(user_a, user_b)

    def __contains__(self, user_id: str) -> bool:
        return user_id in self._adjacency

    def __len__(self) -> int:
        return len(self._adjacency)

    def __repr__(self) -> str:
        return f"Graph(users={len(self)}, edges={self.edge_count()})"
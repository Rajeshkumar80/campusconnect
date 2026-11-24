"""
Unit tests for the DSA Graph module.
Tests cover: isolated users, normal edges, duplicate edges, self-edge rejection, edge removal.
"""

import pytest

from app.dsa.graph import Graph


class TestGraph:
    """Test cases for the Graph class."""

    def test_add_user_creates_isolated_user(self):
        """Adding a user creates an isolated node with empty neighbour set."""
        g = Graph()
        g.add_user("alice")
        assert g.has_user("alice")
        assert g.neighbors("alice") == set()
        assert g.degree("alice") == 0

    def test_add_user_idempotent(self):
        """Adding the same user twice is safe (idempotent)."""
        g = Graph()
        g.add_user("alice")
        g.add_user("alice")
        assert g.degree("alice") == 0

    def test_add_edge_creates_undirected_connection(self):
        """Adding an edge creates connections in both directions."""
        g = Graph()
        g.add_edge("alice", "bob")
        
        assert g.has_edge("alice", "bob")
        assert g.has_edge("bob", "alice")
        assert g.neighbors("alice") == {"bob"}
        assert g.neighbors("bob") == {"alice"}
        assert g.degree("alice") == 1
        assert g.degree("bob") == 1

    def test_add_edge_auto_adds_users(self):
        """Adding an edge auto-adds users if they don't exist."""
        g = Graph()
        g.add_edge("alice", "bob")
        assert g.has_user("alice")
        assert g.has_user("bob")

    def test_self_edge_raises_error(self):
        """Self-edges are rejected with ValueError."""
        g = Graph()
        with pytest.raises(ValueError, match="Self-edges are not allowed"):
            g.add_edge("alice", "alice")

    def test_duplicate_edge_raises_error(self):
        """Duplicate edges are rejected with ValueError."""
        g = Graph()
        g.add_edge("alice", "bob")
        with pytest.raises(ValueError, match="already exists"):
            g.add_edge("alice", "bob")
        with pytest.raises(ValueError, match="already exists"):
            g.add_edge("bob", "alice")  # reverse order also duplicate

    def test_remove_edge_removes_both_directions(self):
        """Removing an edge removes connections in both directions."""
        g = Graph()
        g.add_edge("alice", "bob")
        g.remove_edge("alice", "bob")
        
        assert not g.has_edge("alice", "bob")
        assert not g.has_edge("bob", "alice")
        assert g.neighbors("alice") == set()
        assert g.neighbors("bob") == set()

    def test_remove_edge_reverse_order_works(self):
        """Removing edge in reverse order works."""
        g = Graph()
        g.add_edge("alice", "bob")
        g.remove_edge("bob", "alice")
        assert not g.has_edge("alice", "bob")

    def test_remove_nonexistent_edge_raises_error(self):
        """Removing an edge that doesn't exist raises ValueError."""
        g = Graph()
        g.add_user("alice")
        g.add_user("bob")
        with pytest.raises(ValueError, match="does not exist"):
            g.remove_edge("alice", "bob")

    def test_remove_edge_with_missing_user_raises_error(self):
        """Removing edge with missing user raises ValueError."""
        g = Graph()
        g.add_user("alice")
        with pytest.raises(ValueError, match="not in graph"):
            g.remove_edge("alice", "bob")

    def test_mutual_neighbors(self):
        """Mutual neighbors returns intersection of neighbour sets."""
        g = Graph()
        # alice -- bob -- charlie
        # alice -- diana
        g.add_edge("alice", "bob")
        g.add_edge("bob", "charlie")
        g.add_edge("alice", "diana")
        
        # bob and alice share no mutual neighbors (direct connection not counted)
        assert g.mutual_neighbors("alice", "bob") == set()
        
        # alice and charlie have bob as mutual
        assert g.mutual_neighbors("alice", "charlie") == {"bob"}
        
        # bob and diana have alice as mutual
        assert g.mutual_neighbors("bob", "diana") == {"alice"}

    def test_mutual_neighbors_with_missing_users(self):
        """Mutual neighbors with missing users returns empty set."""
        g = Graph()
        g.add_user("alice")
        assert g.mutual_neighbors("alice", "bob") == set()
        assert g.mutual_neighbors("bob", "alice") == set()
        assert g.mutual_neighbors("bob", "charlie") == set()

    def test_all_users(self):
        """All users returns all user IDs in graph."""
        g = Graph()
        g.add_edge("alice", "bob")
        g.add_edge("charlie", "diana")
        assert g.all_users() == {"alice", "bob", "charlie", "diana"}

    def test_edge_count(self):
        """Edge count returns correct number of undirected edges."""
        g = Graph()
        assert g.edge_count() == 0
        g.add_edge("alice", "bob")
        assert g.edge_count() == 1
        g.add_edge("bob", "charlie")
        assert g.edge_count() == 2
        g.add_edge("alice", "charlie")
        assert g.edge_count() == 3

    def test_rebuild_from_edges(self):
        """Rebuild reconstructs graph from edge list."""
        g = Graph()
        edges = [("alice", "bob"), ("bob", "charlie"), ("alice", "diana")]
        g.rebuild_from_edges(edges)
        
        assert g.has_edge("alice", "bob")
        assert g.has_edge("bob", "charlie")
        assert g.has_edge("alice", "diana")
        assert not g.has_edge("alice", "charlie")
        assert g.all_users() == {"alice", "bob", "charlie", "diana"}

    def test_rebuild_clears_existing(self):
        """Rebuild clears existing graph state."""
        g = Graph()
        g.add_edge("alice", "bob")
        g.rebuild_from_edges([("charlie", "diana")])
        
        assert not g.has_user("alice")
        assert g.has_edge("charlie", "diana")

    def test_neighbors_returns_copy(self):
        """Neighbors returns a copy, not the internal set."""
        g = Graph()
        g.add_edge("alice", "bob")
        neighbors = g.neighbors("alice")
        neighbors.add("charlie")  # mutate the copy
        assert "charlie" not in g.neighbors("alice")

    def test_contains_operator(self):
        """Graph supports 'in' operator for users."""
        g = Graph()
        g.add_user("alice")
        assert "alice" in g
        assert "bob" not in g

    def test_len_returns_user_count(self):
        """len() returns number of users."""
        g = Graph()
        assert len(g) == 0
        g.add_user("alice")
        assert len(g) == 1
        g.add_user("bob")
        assert len(g) == 2
        g.add_edge("alice", "bob")  # doesn't add new users
        assert len(g) == 2
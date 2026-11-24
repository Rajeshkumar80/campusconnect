"""
Unit tests for the DSA BFS module.
Tests cover: direct, two-hop, three-hop, longer, same-user and disconnected cases.
"""

import pytest

from app.dsa.bfs import (
    bfs,
    degree_label,
    degree_of_connection,
    reachable_within,
    shortest_path,
)
from app.dsa.graph import Graph


class TestBFS:
    """Test cases for BFS functions."""

    def setup_method(self):
        """Set up a test graph for each test."""
        self.g = Graph()
        # Graph structure:
        # alice -- bob -- charlie -- diana
        #   |           |
        #   +-- eve ----+
        self.g.add_edge("alice", "bob")
        self.g.add_edge("bob", "charlie")
        self.g.add_edge("charlie", "diana")
        self.g.add_edge("alice", "eve")
        self.g.add_edge("eve", "charlie")
        # frank is isolated
        self.g.add_user("frank")

    def test_bfs_basic_distances(self):
        """BFS computes correct distances from source."""
        result = bfs(self.g, "alice")
        
        assert result.distances["alice"] == 0
        assert result.distances["bob"] == 1
        assert result.distances["eve"] == 1
        assert result.distances["charlie"] == 2  # alice -> bob -> charlie (or eve -> charlie)
        assert result.distances["diana"] == 3
        assert "frank" not in result.distances

    def test_bfs_parent_map(self):
        """BFS parent map allows path reconstruction."""
        result = bfs(self.g, "alice")
        
        # Path to diana: alice -> bob -> charlie -> diana
        path = result.get_path("diana")
        assert path == ["alice", "bob", "charlie", "diana"]
        
        # Path to eve: alice -> eve
        path = result.get_path("eve")
        assert path == ["alice", "eve"]

    def test_bfs_deterministic_order(self):
        """BFS processes neighbors in sorted order for determinism."""
        g = Graph()
        g.add_edge("alice", "zebra")
        g.add_edge("alice", "alpha")
        g.add_edge("alice", "beta")
        
        result = bfs(g, "alice")
        
        # First level neighbors should be visited in alphabetical order
        # The parent of each should be alice
        assert result.parents["alpha"] == "alice"
        assert result.parents["beta"] == "alice"
        assert result.parents["zebra"] == "alice"

    def test_bfs_missing_source_raises(self):
        """BFS with missing source raises KeyError."""
        with pytest.raises(KeyError):
            bfs(self.g, "nonexistent")

    def test_shortest_path_direct(self):
        """Shortest path for direct connection."""
        path = shortest_path(self.g, "alice", "bob")
        assert path == ["alice", "bob"]

    def test_shortest_path_two_hop(self):
        """Shortest path for two-hop connection."""
        path = shortest_path(self.g, "alice", "charlie")
        assert path == ["alice", "bob", "charlie"]
        # Alternative path alice -> eve -> charlie also length 2
        # Should pick lexicographically smaller path due to sorted neighbors

    def test_shortest_path_three_hop(self):
        """Shortest path for three-hop connection."""
        path = shortest_path(self.g, "alice", "diana")
        assert path == ["alice", "bob", "charlie", "diana"]

    def test_shortest_path_same_user(self):
        """Shortest path from user to themselves."""
        path = shortest_path(self.g, "alice", "alice")
        assert path == ["alice"]

    def test_shortest_path_disconnected(self):
        """Shortest path for disconnected users returns None."""
        path = shortest_path(self.g, "alice", "frank")
        assert path is None

    def test_shortest_path_missing_user(self):
        """Shortest path with missing user returns None."""
        path = shortest_path(self.g, "alice", "nonexistent")
        assert path is None

    def test_degree_of_connection_direct(self):
        """Degree for direct connection is 1."""
        assert degree_of_connection(self.g, "alice", "bob") == 1

    def test_degree_of_connection_two_hop(self):
        """Degree for two-hop connection is 2."""
        assert degree_of_connection(self.g, "alice", "charlie") == 2

    def test_degree_of_connection_three_hop(self):
        """Degree for three-hop connection is 3."""
        assert degree_of_connection(self.g, "alice", "diana") == 3

    def test_degree_of_connection_same_user(self):
        """Degree for same user is 0."""
        assert degree_of_connection(self.g, "alice", "alice") == 0

    def test_degree_of_connection_beyond_three(self):
        """Degree for distance > 3 returns actual distance (not None)."""
        # Create a 4-hop path
        g = Graph()
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        g.add_edge("c", "d")
        g.add_edge("d", "e")
        assert degree_of_connection(g, "a", "e") == 4

    def test_degree_of_connection_disconnected(self):
        """Degree for disconnected users returns None."""
        assert degree_of_connection(self.g, "alice", "frank") is None

    def test_degree_of_connection_missing_user(self):
        """Degree with missing user returns None."""
        assert degree_of_connection(self.g, "alice", "nonexistent") is None

    def test_degree_label(self):
        """Degree labels are human-readable."""
        assert degree_label(self.g, "alice", "alice") == "Self"
        assert degree_label(self.g, "alice", "bob") == "1st"
        assert degree_label(self.g, "alice", "charlie") == "2nd"
        assert degree_label(self.g, "alice", "diana") == "3rd"
        assert degree_label(self.g, "alice", "frank") == "Not connected"

    def test_degree_label_beyond_three(self):
        """Degree label for distance > 3 is '3+'."""
        g = Graph()
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        g.add_edge("c", "d")
        g.add_edge("d", "e")
        assert degree_label(g, "a", "e") == "3+"

    def test_reachable_within(self):
        """Reachable within returns users and their distances."""
        result = reachable_within(self.g, "alice", max_depth=2)
        
        assert result["bob"] == 1
        assert result["eve"] == 1
        assert result["charlie"] == 2
        assert "diana" not in result  # distance 3 > max_depth 2
        assert "frank" not in result
        assert "alice" not in result  # source excluded

    def test_reachable_within_max_depth_three(self):
        """Reachable within depth 3 includes diana."""
        result = reachable_within(self.g, "alice", max_depth=3)
        assert result["diana"] == 3

    def test_reachable_within_missing_source(self):
        """Reachable within with missing source returns empty."""
        result = reachable_within(self.g, "nonexistent", max_depth=3)
        assert result == {}

    def test_bfs_result_get_path_none(self):
        """BFSResult.get_path returns None for unreachable target."""
        result = bfs(self.g, "alice")
        assert result.get_path("frank") is None
        assert result.get_path("nonexistent") is None
"""
Unit tests for the DSA Recommendations module.
Tests cover: empty graph, ties, exclusion rules, pending request handling.
"""


from app.dsa.graph import Graph
from app.dsa.recommendations import (
    _generate_candidates,
    _score_common_neighbors,
    _score_jaccard,
    get_suggestions,
    get_suggestions_with_explanation,
)


class TestRecommendations:
    """Test cases for recommendation functions."""

    def setup_method(self):
        """Set up a test graph for each test."""
        # Graph structure:
        # alice -- bob -- charlie
        #   |       |       |
        #   +-- diana -- eve
        # frank -- grace (separate component)
        # helen (isolated)
        self.g = Graph()
        self.g.add_edge("alice", "bob")
        self.g.add_edge("bob", "charlie")
        self.g.add_edge("alice", "diana")
        self.g.add_edge("diana", "eve")
        self.g.add_edge("charlie", "eve")
        self.g.add_edge("frank", "grace")
        self.g.add_user("helen")

    def test_generate_candidates_basic(self):
        """Candidates are neighbours of neighbours, excluding self and direct connections."""
        candidates = _generate_candidates(self.g, "alice")
        
        # alice's neighbors: bob, diana
        # bob's neighbors: alice, charlie
        # diana's neighbors: alice, eve
        # Candidates: charlie (via bob), eve (via diana)
        assert candidates == {"charlie", "eve"}

    def test_generate_candidates_excludes_self(self):
        """Self is never a candidate."""
        candidates = _generate_candidates(self.g, "alice")
        assert "alice" not in candidates

    def test_generate_candidates_excludes_direct_connections(self):
        """Direct connections are not candidates."""
        candidates = _generate_candidates(self.g, "alice")
        assert "bob" not in candidates
        assert "diana" not in candidates

    def test_generate_candidates_missing_user(self):
        """Missing user returns empty candidate set."""
        candidates = _generate_candidates(self.g, "nonexistent")
        assert candidates == set()

    def test_generate_candidates_isolated_user(self):
        """Isolated user has no candidates."""
        candidates = _generate_candidates(self.g, "helen")
        assert candidates == set()

    def test_generate_candidates_separate_component(self):
        """Users in separate components are not candidates."""
        candidates = _generate_candidates(self.g, "frank")
        # frank's neighbor: grace; grace's neighbor: frank
        # No other candidates
        assert candidates == set()

    def test_score_common_neighbors(self):
        """Common neighbour count is correct."""
        # alice and charlie share bob as mutual
        assert _score_common_neighbors(self.g, "alice", "charlie") == 1
        
        # alice and eve share diana as mutual
        assert _score_common_neighbors(self.g, "alice", "eve") == 1
        
        # bob and eve share charlie as mutual (bob: alice,charlie; eve: diana,charlie)
        assert _score_common_neighbors(self.g, "bob", "eve") == 1

    def test_score_jaccard(self):
        """Jaccard similarity is correct."""
        # alice neighbors: {bob, diana}
        # charlie neighbors: {bob, eve}
        # intersection: {bob} = 1, union: {bob, diana, eve} = 3
        # Jaccard = 1/3
        score = _score_jaccard(self.g, "alice", "charlie")
        assert abs(score - 1/3) < 0.001
        
        # Identical neighbor sets
        g = Graph()
        g.add_edge("a", "x")
        g.add_edge("a", "y")
        g.add_edge("b", "x")
        g.add_edge("b", "y")
        # Both have neighbors {x, y}
        score = _score_jaccard(g, "a", "b")
        assert abs(score - 1.0) < 0.001
        
        # No overlap
        g2 = Graph()
        g2.add_edge("a", "x")
        g2.add_edge("b", "y")
        score = _score_jaccard(g2, "a", "b")
        assert score == 0.0

    def test_get_suggestions_basic(self):
        """Basic suggestions work correctly."""
        suggestions = get_suggestions(self.g, "alice", limit=10)
        
        # alice's candidates: charlie (1 mutual: bob), eve (1 mutual: diana)
        # Both have score 1, tie-break by user_id
        assert len(suggestions) == 2
        assert suggestions[0].user_id == "charlie"  # c < e
        assert suggestions[1].user_id == "eve"
        assert suggestions[0].mutual_count == 1
        assert suggestions[1].mutual_count == 1

    def test_get_suggestions_ranking(self):
        """Suggestions ranked by mutual count descending, then user_id."""
        # bob's candidates: diana (mutual: alice=1), eve (mutual: charlie=1)
        # Both have 1 mutual, tie-break by user_id: diana < eve
        suggestions = get_suggestions(self.g, "bob", limit=10)
        
        assert len(suggestions) == 2
        assert suggestions[0].user_id == "diana"
        assert suggestions[0].mutual_count == 1
        assert suggestions[1].user_id == "eve"
        assert suggestions[1].mutual_count == 1

    def test_get_suggestions_limit(self):
        """Limit parameter restricts results."""
        suggestions = get_suggestions(self.g, "alice", limit=1)
        assert len(suggestions) == 1
        assert suggestions[0].user_id == "charlie"

    def test_get_suggestions_exclude_pending(self):
        """Exclude pending requests from suggestions."""
        # alice has pending request to charlie
        suggestions = get_suggestions(self.g, "alice", exclude_pending={"charlie"})
        
        assert len(suggestions) == 1
        assert suggestions[0].user_id == "eve"

    def test_get_suggestions_missing_user(self):
        """Missing user returns empty list."""
        suggestions = get_suggestions(self.g, "nonexistent")
        assert suggestions == []

    def test_get_suggestions_isolated_user(self):
        """Isolated user gets no suggestions."""
        suggestions = get_suggestions(self.g, "helen")
        assert suggestions == []

    def test_get_suggestions_zero_score_excluded(self):
        """Candidates with zero mutual connections are excluded."""
        # frank and grace only know each other, no 2-hop candidates with mutuals
        suggestions = get_suggestions(self.g, "frank")
        assert suggestions == []

    def test_get_suggestions_with_explanation(self):
        """Suggestions with explanation include human-readable text."""
        suggestions = get_suggestions_with_explanation(self.g, "alice")
        
        assert len(suggestions) == 2
        assert suggestions[0]["user_id"] == "charlie"
        assert suggestions[0]["explanation"] == "1 mutual connection"
        assert suggestions[0]["mutual_count"] == 1

    def test_tie_break_stable_by_user_id(self):
        """Ties broken by user_id ascending for determinism."""
        g = Graph()
        g.add_edge("alice", "bob")
        g.add_edge("bob", "charlie")
        g.add_edge("bob", "alpha")  # alpha and charlie both have 1 mutual (bob)
        
        suggestions = get_suggestions(g, "alice")
        
        # Both have score 1, alpha < charlie lexicographically
        assert suggestions[0].user_id == "alpha"
        assert suggestions[1].user_id == "charlie"

    def test_jaccard_ranking(self):
        """Jaccard ranking works when enabled."""
        suggestions = get_suggestions(self.g, "alice", use_jaccard=True)
        
        # Both charlie and eve have 1 mutual, but different union sizes
        # charlie neighbors: {bob, eve} -> union with alice {bob, diana} = {bob, diana, eve} = 3
        # eve neighbors: {diana, charlie} -> union with alice {bob, diana} = {bob, diana, charlie} = 3
        # Both Jaccard = 1/3, tie-break by user_id
        assert len(suggestions) == 2
        assert suggestions[0].user_id == "charlie"
        assert suggestions[1].user_id == "eve"
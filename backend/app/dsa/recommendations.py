"""
DSA Core: People You May Know recommendations.

Generates connection suggestions ranked by common-neighbour count
(or optionally Jaccard similarity).

Algorithm:
1. Candidate set = neighbours of neighbours (2-hop reachable users)
2. Exclude: self, existing connections, users with pending requests (if tracked)
3. Score each candidate by |N(u) ∩ N(v)| (common neighbour count)
4. Optional: Jaccard score = |N(u) ∩ N(v)| / |N(u) ∪ N(v)|
5. Rank by descending score, then stable tie-break by user ID.

Time complexity: O(deg(u) * avg_deg) for candidate generation + scoring.
Space: O(V) for candidate set.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.dsa.graph import Graph


@dataclass(frozen=True, order=True)
class Suggestion:
    """A single connection suggestion with score and explanation."""
    user_id: str
    score: int
    mutual_count: int
    # For tie-breaking: user_id is the first sort key (due to order=True)
    
    @property
    def explanation(self) -> str:
        """Human-readable explanation of the score."""
        if self.mutual_count == 1:
            return "1 mutual connection"
        return f"{self.mutual_count} mutual connections"


def _generate_candidates(graph: Graph, user_id: str) -> set[str]:
    """
    Generate candidate users for suggestions: neighbours of neighbours.
    
    Excludes the user themselves and their direct connections.
    """
    if user_id not in graph:
        return set()
    
    direct_neighbors = graph.neighbors(user_id)
    candidates = set()
    
    for neighbor in direct_neighbors:
        for neighbor_of_neighbor in graph.neighbors(neighbor):
            if neighbor_of_neighbor != user_id and neighbor_of_neighbor not in direct_neighbors:
                candidates.add(neighbor_of_neighbor)
    
    return candidates


def _score_common_neighbors(graph: Graph, user_id: str, candidate_id: str) -> int:
    """
    Score a candidate by common neighbour count.
    
    Returns: |N(user) ∩ N(candidate)|
    """
    return len(graph.mutual_neighbors(user_id, candidate_id))


def _score_jaccard(graph: Graph, user_id: str, candidate_id: str) -> float:
    """
    Score a candidate by Jaccard similarity.
    
    J(u,v) = |N(u) ∩ N(v)| / |N(u) ∪ N(v)|
    Returns 0.0 if union is empty.
    """
    neighbors_u = graph.neighbors(user_id)
    neighbors_v = graph.neighbors(candidate_id)
    
    if not neighbors_u and not neighbors_v:
        return 0.0
    
    intersection = len(neighbors_u & neighbors_v)
    union = len(neighbors_u | neighbors_v)
    
    if union == 0:
        return 0.0
    
    return intersection / union


def get_suggestions(
    graph: Graph,
    user_id: str,
    *,
    limit: int = 10,
    exclude_pending: set[str] | None = None,
    use_jaccard: bool = False,
) -> list[Suggestion]:
    """
    Get ranked connection suggestions for a user.
    
    Args:
        graph: The connection graph
        user_id: User to get suggestions for
        limit: Maximum number of suggestions to return
        exclude_pending: Set of user IDs with pending requests (sent or received)
        use_jaccard: If True, use Jaccard similarity; else common neighbour count
    
    Returns:
        List of Suggestion objects, ranked by score (descending), then user_id (ascending).
    
    Time: O(deg(u) * avg_deg + C log C) where C = candidate count
    """
    if user_id not in graph:
        return []
    
    candidates = _generate_candidates(graph, user_id)
    
    # Exclude users with pending requests if provided
    if exclude_pending:
        candidates -= exclude_pending
    
    if not candidates:
        return []
    
    # Score all candidates
    scored: list[Suggestion] = []
    for candidate in candidates:
        if use_jaccard:
            score = _score_jaccard(graph, user_id, candidate)
            # Convert to integer for consistent ordering (scale by 10000)
            score_int = int(score * 10000)
        else:
            mutual = _score_common_neighbors(graph, user_id, candidate)
            score_int = mutual
        
        if score_int > 0:  # Only suggest if there's at least some connection
            scored.append(Suggestion(
                user_id=candidate,
                score=score_int,
                mutual_count=_score_common_neighbors(graph, user_id, candidate),
            ))
    
    # Sort by score descending, then user_id ascending (stable tie-break)
    scored.sort(key=lambda s: (-s.score, s.user_id))
    
    return scored[:limit]


def get_suggestions_with_explanation(
    graph: Graph,
    user_id: str,
    *,
    limit: int = 10,
    exclude_pending: set[str] | None = None,
) -> list[dict]:
    """
    Get suggestions with detailed explanation for API response.
    
    Returns list of dicts with: user_id, score, mutual_count, explanation
    """
    suggestions = get_suggestions(graph, user_id, limit=limit, exclude_pending=exclude_pending)
    return [
        {
            "user_id": s.user_id,
            "score": s.score,
            "mutual_count": s.mutual_count,
            "explanation": s.explanation,
        }
        for s in suggestions
    ]
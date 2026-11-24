"""
DSA Core: Breadth-First Search for shortest paths and connection degrees.

Implements BFS on the adjacency-list graph for:
- Shortest path finding (unweighted graph)
- Connection degree classification (1st, 2nd, 3rd)
- Depth-limited reachability

Complexity: O(V + E) worst case for full traversal.
"""

from __future__ import annotations

from collections import deque

from app.dsa.graph import Graph


class BFSResult:
    """Result of a BFS traversal."""

    def __init__(
        self,
        distances: dict[str, int],
        parents: dict[str, str | None],
    ) -> None:
        self.distances = distances
        self.parents = parents

    def get_path(self, target: str) -> list[str] | None:
        """Reconstruct path from source to target."""
        if target not in self.parents:
            return None
        path = []
        curr = target
        while curr is not None:
            path.append(curr)
            curr = self.parents[curr]
        path.reverse()
        return path


def bfs(graph: Graph, source: str) -> BFSResult:
    """
    Perform BFS from source node.
    
    Returns distances and parent map for all reachable nodes.
    
    Time: O(V + E) where V = reachable nodes, E = edges among them.
    Space: O(V)
    
    Determinism: Neighbors are processed in sorted order for stable results.
    """
    if source not in graph:
        raise KeyError(f"Source user {source} not in graph")

    distances: dict[str, int] = {source: 0}
    parents: dict[str, str | None] = {source: None}
    queue = deque([source])

    while queue:
        current = queue.popleft()
        current_dist = distances[current]
        
        # Sort neighbors for deterministic traversal order
        for neighbor in sorted(graph.neighbors(current)):
            if neighbor not in distances:
                distances[neighbor] = current_dist + 1
                parents[neighbor] = current
                queue.append(neighbor)

    return BFSResult(distances, parents)


def shortest_path(graph: Graph, source: str, target: str) -> list[str] | None:
    """
    Find one shortest path between source and target using BFS.
    
    Returns list of user IDs from source to target inclusive, or None if no path.
    
    Time: O(V + E) worst case
    """
    if source == target:
        return [source]
    
    if source not in graph or target not in graph:
        return None

    result = bfs(graph, source)
    return result.get_path(target)


def degree_of_connection(graph: Graph, source: str, target: str) -> int | None:
    """
    Get the degree of connection (graph distance) between two users.
    
    Returns:
        0 for same user
        1 for direct connection (1st degree)
        2 for friend-of-friend (2nd degree)
        3 for friend-of-friend-of-friend (3rd degree)
        >3 for connected but beyond 3rd degree
        None if not connected
    
    Time: O(V + E) worst case.
    """
    if source == target:
        return 0
    
    if source not in graph or target not in graph:
        return None

    # Full BFS to get actual distance (needed to distinguish >3 from disconnected)
    distances: dict[str, int] = {source: 0}
    queue = deque([source])

    while queue:
        current = queue.popleft()
        current_dist = distances[current]
        
        for neighbor in sorted(graph.neighbors(current)):
            if neighbor not in distances:
                distances[neighbor] = current_dist + 1
                if neighbor == target:
                    return current_dist + 1
                queue.append(neighbor)

    return None  # not connected


def degree_of_connection_bounded(graph: Graph, source: str, target: str, max_depth: int = 3) -> int | None:
    """
    Get degree of connection with early termination at max_depth.
    
    Returns actual distance if <= max_depth, None if > max_depth or not connected.
    Use this for performance when you only need to know if users are within N degrees.
    """
    if source == target:
        return 0
    
    if source not in graph or target not in graph:
        return None

    distances: dict[str, int] = {source: 0}
    queue = deque([source])

    while queue:
        current = queue.popleft()
        current_dist = distances[current]
        
        if current_dist >= max_depth:
            continue
            
        for neighbor in sorted(graph.neighbors(current)):
            if neighbor not in distances:
                distances[neighbor] = current_dist + 1
                if neighbor == target:
                    return current_dist + 1
                queue.append(neighbor)

    return None


def degree_label(graph: Graph, source: str, target: str) -> str:
    """
    Get human-readable degree label.
    
    Returns: "1st", "2nd", "3rd", "3+", "Not connected", or "Self"
    
    Per PRD: Users farther away should be labelled "3+" or "Beyond 3rd",
    not incorrectly labelled third-degree.
    """
    if source == target:
        return "Self"
    
    degree = degree_of_connection(graph, source, target)
    
    if degree is None:
        return "Not connected"
    if degree == 1:
        return "1st"
    if degree == 2:
        return "2nd"
    if degree == 3:
        return "3rd"
    return "3+"


def reachable_within(graph: Graph, source: str, max_depth: int = 3) -> dict[str, int]:
    """
    Get all users reachable within max_depth hops from source.
    
    Returns dict mapping user_id -> distance (1 to max_depth).
    Excludes the source user.
    
    Time: O(V + E) bounded by max_depth
    """
    if source not in graph:
        return {}

    distances: dict[str, int] = {source: 0}
    queue = deque([source])
    result: dict[str, int] = {}

    while queue:
        current = queue.popleft()
        current_dist = distances[current]
        
        if current_dist >= max_depth:
            continue
            
        for neighbor in sorted(graph.neighbors(current)):
            if neighbor not in distances:
                distances[neighbor] = current_dist + 1
                if current_dist + 1 <= max_depth:
                    result[neighbor] = current_dist + 1
                    queue.append(neighbor)

    return result
"""
DSA Core Package - Data Structures and Algorithms for CampusConnect.

Exports:
- Graph: Adjacency-list graph for accepted connections
- BFS: Breadth-first search for shortest paths and degrees
- Recommendations: People-you-may-know suggestions
- Trie: Prefix search for usernames/display names
- FeedHeap: Heap-based feed merging
- RequestQueue: Connection request state management
"""

from app.dsa.bfs import (
    bfs,
    degree_label,
    degree_of_connection,
    degree_of_connection_bounded,
    reachable_within,
    shortest_path,
)
from app.dsa.feed_heap import (
    Post,
    create_post_streams_from_raw,
    merge_post_streams,
    merge_post_streams_with_metadata,
)
from app.dsa.graph import Graph
from app.dsa.recommendations import (
    Suggestion,
    get_suggestions,
    get_suggestions_with_explanation,
)
from app.dsa.request_queue import (
    ConnectionRequest,
    RequestQueue,
    RequestStatus,
)
from app.dsa.trie import PrefixIndex, Trie

__all__ = [
    "ConnectionRequest",
    "Graph",
    "Post",
    "PrefixIndex",
    "RequestQueue",
    "RequestStatus",
    "Suggestion",
    "Trie",
    "bfs",
    "create_post_streams_from_raw",
    "degree_label",
    "degree_of_connection",
    "degree_of_connection_bounded",
    "get_suggestions",
    "get_suggestions_with_explanation",
    "merge_post_streams",
    "merge_post_streams_with_metadata",
    "reachable_within",
    "shortest_path",
]
"""
DSA Core: Heap-based feed merge for home feed.

Merges time-ordered post streams from accepted connections using a max-heap
to produce a newest-first feed efficiently.

Algorithm:
- Each connection's posts are already sorted by time (newest first)
- Use a max-heap (via negative timestamps) to merge k sorted streams
- Heap entry: (-timestamp, tie_breaker, author_id, stream_index, post_data)
- Pop from heap, yield post, push next from same stream

Complexity: O(P log C) for P posts returned from C connection streams.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from heapq import heappop, heappush


@dataclass(frozen=True)
class Post:
    """A post in the feed."""
    post_id: str
    author_id: str
    text: str
    created_at: float  # Unix timestamp
    # Additional fields can be added as needed


@dataclass(order=True)
class HeapEntry:
    """
    Heap entry for merging post streams.
    
    Uses negative timestamp for max-heap behavior (newest first).
    Tie-breaker ensures stable ordering for equal timestamps.
    """
    neg_timestamp: float
    tie_breaker: int
    author_id: str = field(compare=False)
    stream_index: int = field(compare=False)
    post: Post = field(compare=False)


def merge_post_streams(
    streams: list[list[Post]],
    *,
    limit: int = 20,
) -> list[Post]:
    """
    Merge multiple time-ordered post streams into a single newest-first feed.
    
    Args:
        streams: List of post lists, each sorted newest-first (descending created_at)
        limit: Maximum number of posts to return
    
    Returns:
        List of posts merged newest-first, up to limit.
    
    Time: O(P log C) where P = posts returned, C = number of streams
    Space: O(C) for heap
    
    Assumptions:
    - Each stream is pre-sorted by created_at descending (newest first)
    - Timestamps are comparable (Unix timestamps)
    - Streams may be empty
    """
    if not streams:
        return []
    
    heap: list[HeapEntry] = []
    tie_breaker = 0
    
    # Initialize heap with first post from each non-empty stream
    for stream_idx, stream in enumerate(streams):
        if stream:
            post = stream[0]
            entry = HeapEntry(
                neg_timestamp=-post.created_at,
                tie_breaker=tie_breaker,
                author_id=post.author_id,
                stream_index=stream_idx,
                post=post,
            )
            heappush(heap, entry)
            tie_breaker += 1
    
    result: list[Post] = []
    stream_positions = [0] * len(streams)
    
    while heap and len(result) < limit:
        entry = heappop(heap)
        result.append(entry.post)
        
        # Advance in the stream this post came from
        stream_idx = entry.stream_index
        stream_positions[stream_idx] += 1
        next_pos = stream_positions[stream_idx]
        
        if next_pos < len(streams[stream_idx]):
            next_post = streams[stream_idx][next_pos]
            next_entry = HeapEntry(
                neg_timestamp=-next_post.created_at,
                tie_breaker=tie_breaker,
                author_id=next_post.author_id,
                stream_index=stream_idx,
                post=next_post,
            )
            heappush(heap, next_entry)
            tie_breaker += 1
    
    return result


def merge_post_streams_with_metadata(
    streams: list[list[Post]],
    *,
    limit: int = 20,
) -> list[dict]:
    """
    Merge streams and return posts with metadata for API response.
    
    Returns list of dicts with post data plus author info placeholder.
    """
    posts = merge_post_streams(streams, limit=limit)
    return [
        {
            "post_id": post.post_id,
            "author_id": post.author_id,
            "text": post.text,
            "created_at": post.created_at,
        }
        for post in posts
    ]


def create_post_streams_from_raw(
    posts_by_author: dict[str, list[dict]],
    *,
    max_per_author: int = 50,
) -> list[list[Post]]:
    """
    Convert raw post data from repository into sorted streams for merging.
    
    Args:
        posts_by_author: Dict mapping author_id -> list of post dicts
        max_per_author: Maximum posts to load per author (bounds memory)
    
    Returns:
        List of Post streams, each sorted newest-first.
    """
    streams = []
    
    for author_id, posts in posts_by_author.items():
        # Sort by created_at descending (newest first)
        sorted_posts = sorted(
            posts,
            key=lambda p: p["created_at"],
            reverse=True,
        )
        
        # Limit per author
        limited = sorted_posts[:max_per_author]
        
        stream = [
            Post(
                post_id=p["post_id"],
                author_id=author_id,
                text=p["text"],
                created_at=p["created_at"],
            )
            for p in limited
        ]
        
        if stream:
            streams.append(stream)
    
    return streams
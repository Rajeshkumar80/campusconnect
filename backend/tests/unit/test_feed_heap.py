"""
Unit tests for the DSA Feed Heap module.
Tests cover: equal timestamps, empty streams, pagination boundary, no unrelated author stream.
"""


from app.dsa.feed_heap import (
    Post,
    create_post_streams_from_raw,
    merge_post_streams,
    merge_post_streams_with_metadata,
)


class TestFeedHeap:
    """Test cases for feed heap merging."""

    def test_merge_two_streams(self):
        """Merge two streams correctly."""
        stream1 = [
            Post("p1", "alice", "Post 1", 1000.0),
            Post("p2", "alice", "Post 2", 900.0),
        ]
        stream2 = [
            Post("p3", "bob", "Post 3", 950.0),
            Post("p4", "bob", "Post 4", 800.0),
        ]
        
        result = merge_post_streams([stream1, stream2], limit=10)
        
        # Should be ordered by timestamp: 1000, 950, 900, 800
        assert [p.post_id for p in result] == ["p1", "p3", "p2", "p4"]

    def test_merge_three_streams(self):
        """Merge three streams."""
        stream1 = [Post("p1", "a", "", 1000.0)]
        stream2 = [Post("p2", "b", "", 900.0)]
        stream3 = [Post("p3", "c", "", 800.0)]
        
        result = merge_post_streams([stream1, stream2, stream3], limit=10)
        assert [p.post_id for p in result] == ["p1", "p2", "p3"]

    def test_equal_timestamps_stable_order(self):
        """Equal timestamps use tie-breaker for stable ordering."""
        stream1 = [
            Post("p1", "alice", "", 1000.0),
            Post("p2", "alice", "", 900.0),
        ]
        stream2 = [
            Post("p3", "bob", "", 1000.0),  # Same timestamp as p1
            Post("p4", "bob", "", 800.0),
        ]
        
        result = merge_post_streams([stream1, stream2], limit=10)
        
        # Both have timestamp 1000, but stream1 was added to heap first
        # So p1 should come before p3 due to tie-breaker
        assert result[0].post_id == "p1"
        assert result[1].post_id == "p3"
        assert result[2].post_id == "p2"
        assert result[3].post_id == "p4"

    def test_limit_respected(self):
        """Limit parameter restricts output."""
        stream1 = [Post(f"p{i}", "a", "", float(1000 - i * 10)) for i in range(10)]
        stream2 = [Post(f"q{i}", "b", "", float(995 - i * 10)) for i in range(10)]
        
        result = merge_post_streams([stream1, stream2], limit=5)
        assert len(result) == 5

    def test_empty_streams(self):
        """Empty streams are handled correctly."""
        result = merge_post_streams([[], []], limit=10)
        assert result == []
        
        stream1 = [Post("p1", "a", "", 1000.0)]
        result = merge_post_streams([stream1, []], limit=10)
        assert len(result) == 1
        assert result[0].post_id == "p1"

    def test_single_stream(self):
        """Single stream works."""
        stream = [
            Post("p1", "a", "", 1000.0),
            Post("p2", "a", "", 900.0),
        ]
        result = merge_post_streams([stream], limit=10)
        assert [p.post_id for p in result] == ["p1", "p2"]

    def test_no_unrelated_author_stream(self):
        """Only provided streams are merged (no extra authors)."""
        stream1 = [Post("p1", "alice", "", 1000.0)]
        stream2 = [Post("p2", "bob", "", 900.0)]
        
        result = merge_post_streams([stream1, stream2], limit=10)
        
        # Only alice and bob posts
        author_ids = {p.author_id for p in result}
        assert author_ids == {"alice", "bob"}

    def test_pagination_boundary(self):
        """Pagination works at exact limit boundary."""
        # Create 25 posts across 2 streams
        stream1 = [Post(f"p{i}", "a", "", float(1000 - i)) for i in range(15)]
        stream2 = [Post(f"q{i}", "b", "", float(1000 - i)) for i in range(10)]
        
        result = merge_post_streams([stream1, stream2], limit=20)
        assert len(result) == 20
        
        # Verify they're in correct order (interleaved by timestamp)
        timestamps = [p.created_at for p in result]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_create_streams_from_raw(self):
        """Convert raw dict data to Post streams."""
        posts_by_author = {
            "alice": [
                {"post_id": "p1", "text": "Hello", "created_at": 1000.0},
                {"post_id": "p2", "text": "World", "created_at": 900.0},
            ],
            "bob": [
                {"post_id": "p3", "text": "Foo", "created_at": 950.0},
            ],
        }
        
        streams = create_post_streams_from_raw(posts_by_author)
        
        assert len(streams) == 2
        # Each stream sorted newest-first
        assert streams[0][0].created_at >= streams[0][1].created_at if len(streams[0]) > 1 else True
        assert streams[1][0].created_at == 950.0

    def test_create_streams_max_per_author(self):
        """Max per author limits stream size."""
        posts_by_author = {
            "alice": [
                {"post_id": f"p{i}", "text": "", "created_at": float(1000 - i)}
                for i in range(100)
            ],
        }
        
        streams = create_post_streams_from_raw(posts_by_author, max_per_author=10)
        
        assert len(streams) == 1
        assert len(streams[0]) == 10
        # Should have newest 10
        assert streams[0][0].post_id == "p0"
        assert streams[0][9].post_id == "p9"

    def test_merge_with_metadata(self):
        """Merge with metadata returns dict format."""
        stream1 = [Post("p1", "alice", "Hello", 1000.0)]
        stream2 = [Post("p2", "bob", "World", 900.0)]
        
        result = merge_post_streams_with_metadata([stream1, stream2], limit=10)
        
        assert len(result) == 2
        assert result[0]["post_id"] == "p1"
        assert result[0]["author_id"] == "alice"
        assert result[0]["text"] == "Hello"
        assert result[0]["created_at"] == 1000.0

    def test_many_streams(self):
        """Merge many streams efficiently."""
        streams = [
            [Post(f"p{i}", f"author{i}", "", float(1000 - i))]
            for i in range(20)
        ]
        
        result = merge_post_streams(streams, limit=10)
        assert len(result) == 10
        # Should be top 10 by timestamp
        assert result[0].created_at == 1000.0
        assert result[9].created_at == 991.0

    def test_streams_unsorted_shows_heap_behavior(self):
        """Heap correctly picks global max from current stream positions."""
        # Even if stream isn't pre-sorted, heap picks from current head of each stream
        stream1 = [
            Post("p1", "a", "", 900.0),   # Older first
            Post("p2", "a", "", 1000.0),  # Newer second
        ]
        stream2 = [Post("p3", "b", "", 950.0)]
        
        result = merge_post_streams([stream1, stream2], limit=10)
        
        # Heap compares current heads: p1(900) vs p3(950) -> p3 wins (newer)
        # stream2 exhausted, stream1 still at p1(900) -> p1 wins
        # stream1 advances to p2(1000) -> p2 wins
        assert result[0].post_id == "p3"
        assert result[1].post_id == "p1"
        assert result[2].post_id == "p2"
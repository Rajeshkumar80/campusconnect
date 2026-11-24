"""
Unit tests for the DSA Trie module.
Tests cover: empty prefix policy, case handling, partial prefix, no match, duplicate names.
"""


from app.dsa.trie import PrefixIndex, Trie


class TestTrie:
    """Test cases for the Trie class."""

    def setup_method(self):
        """Set up a fresh trie for each test."""
        self.trie = Trie()

    def test_insert_and_search(self):
        """Basic insert and prefix search."""
        self.trie.insert("alice", "user1")
        self.trie.insert("alicia", "user2")
        self.trie.insert("bob", "user3")
        
        results = self.trie.prefix_search("ali", limit=10)
        assert set(results) == {"user1", "user2"}
    
    def test_prefix_search_limit(self):
        """Limit parameter restricts results."""
        self.trie.insert("alice", "user1")
        self.trie.insert("alicia", "user2")
        self.trie.insert("alison", "user3")
        self.trie.insert("alex", "user4")
        
        results = self.trie.prefix_search("ali", limit=2)
        assert len(results) == 2
        # Should be sorted by key: alice, alicia
        assert results == ["user1", "user2"]

    def test_case_insensitive(self):
        """Search is case-insensitive."""
        self.trie.insert("Alice", "user1")
        self.trie.insert("ALICIA", "user2")
        
        results = self.trie.prefix_search("ali")
        assert set(results) == {"user1", "user2"}
        
        results = self.trie.prefix_search("ALI")
        assert set(results) == {"user1", "user2"}

    def test_exact_match(self):
        """Exact match returns users for that key."""
        self.trie.insert("alice", "user1")
        self.trie.insert("alice", "user2")  # Same key, different users
        
        results = self.trie.exact_match("alice")
        assert results == {"user1", "user2"}
        
        results = self.trie.exact_match("ALICE")
        assert results == {"user1", "user2"}

    def test_no_match_returns_empty(self):
        """No matching prefix returns empty list."""
        self.trie.insert("alice", "user1")
        
        results = self.trie.prefix_search("bob")
        assert results == []

    def test_empty_prefix_returns_empty(self):
        """Empty prefix returns empty list (not all users)."""
        self.trie.insert("alice", "user1")
        self.trie.insert("bob", "user2")
        
        results = self.trie.prefix_search("")
        assert results == []
        
        results = self.trie.prefix_search("   ")
        assert results == []

    def test_remove_key(self):
        """Remove a key-user_id pair."""
        self.trie.insert("alice", "user1")
        self.trie.insert("alice", "user2")
        
        self.trie.remove("alice", "user1")
        results = self.trie.exact_match("alice")
        assert results == {"user2"}
        
        self.trie.remove("alice", "user2")
        results = self.trie.exact_match("alice")
        assert results == set()

    def test_remove_nonexistent(self):
        """Removing nonexistent key/user is safe."""
        self.trie.insert("alice", "user1")
        self.trie.remove("bob", "user1")  # No error
        self.trie.remove("alice", "user2")  # No error
        assert self.trie.exact_match("alice") == {"user1"}

    def test_update_key(self):
        """Update a user's key (e.g., username change)."""
        self.trie.insert("alice_old", "user1")
        
        self.trie.update_key("alice_old", "alice_new", "user1")
        
        assert self.trie.exact_match("alice_old") == set()
        assert self.trie.exact_match("alice_new") == {"user1"}
        assert self.trie.prefix_search("alice") == ["user1"]

    def test_duplicate_names_different_users(self):
        """Multiple users can have the same name/username."""
        self.trie.insert("alice", "user1")
        self.trie.insert("alice", "user2")
        self.trie.insert("alice", "user3")
        
        results = self.trie.prefix_search("alice")
        assert set(results) == {"user1", "user2", "user3"}

    def test_partial_prefix(self):
        """Partial prefix matches correctly."""
        self.trie.insert("alexander", "user1")
        self.trie.insert("alexandra", "user2")
        self.trie.insert("alex", "user3")
        
        results = self.trie.prefix_search("alex")
        assert set(results) == {"user1", "user2", "user3"}
        
        results = self.trie.prefix_search("alexa")
        assert set(results) == {"user1", "user2"}

    def test_special_characters(self):
        """Handles special characters in keys."""
        self.trie.insert("alice_smith", "user1")
        self.trie.insert("alice-smith", "user2")
        
        results = self.trie.prefix_search("alice")
        assert set(results) == {"user1", "user2"}

    def test_unicode(self):
        """Handles unicode characters."""
        self.trie.insert("alice", "user1")
        self.trie.insert("alice", "user2")
        self.trie.insert("alice", "user3")
        
        results = self.trie.prefix_search("ali")
        assert set(results) == {"user1", "user2", "user3"}

    def test_clear(self):
        """Clear removes all entries."""
        self.trie.insert("alice", "user1")
        self.trie.clear()
        
        assert self.trie.prefix_search("alice") == []
        assert self.trie.exact_match("alice") == set()


class TestPrefixIndex:
    """Test cases for the PrefixIndex fallback."""

    def setup_method(self):
        """Set up a fresh index for each test."""
        self.index = PrefixIndex()

    def test_insert_and_search(self):
        """Basic insert and prefix search."""
        self.index.insert("alice", "user1")
        self.index.insert("alicia", "user2")
        self.index.insert("bob", "user3")
        
        results = self.index.prefix_search("ali", limit=10)
        assert set(results) == {"user1", "user2"}

    def test_case_insensitive(self):
        """Search is case-insensitive."""
        self.index.insert("Alice", "user1")
        
        results = self.index.prefix_search("ali")
        assert results == ["user1"]

    def test_remove(self):
        """Remove works correctly."""
        self.index.insert("alice", "user1")
        self.index.remove("alice", "user1")
        
        results = self.index.prefix_search("alice")
        assert results == []

    def test_update_key(self):
        """Update key works."""
        self.index.insert("alice_old", "user1")
        self.index.update_key("alice_old", "alice_new", "user1")
        
        results = self.index.prefix_search("alice")
        assert results == ["user1"]

    def test_duplicate_names(self):
        """Multiple users with same name."""
        self.index.insert("alice", "user1")
        self.index.insert("alice", "user2")
        
        results = self.index.prefix_search("alice")
        assert set(results) == {"user1", "user2"}

    def test_empty_prefix(self):
        """Empty prefix returns empty."""
        self.index.insert("alice", "user1")
        
        results = self.index.prefix_search("")
        assert results == []

    def test_clear(self):
        """Clear works."""
        self.index.insert("alice", "user1")
        self.index.clear()
        
        assert self.index.prefix_search("alice") == []

    def test_consistency_with_trie(self):
        """PrefixIndex gives same results as Trie for same data."""
        trie = Trie()
        index = PrefixIndex()
        
        test_data = [
            ("alice", "user1"),
            ("alicia", "user2"),
            ("alex", "user3"),
            ("bob", "user4"),
            ("bobby", "user5"),
        ]
        
        for key, uid in test_data:
            trie.insert(key, uid)
            index.insert(key, uid)
        
        for prefix in ["a", "al", "ali", "alex", "b", "bo", "bob", "x"]:
            trie_results = set(trie.prefix_search(prefix, limit=10))
            index_results = set(index.prefix_search(prefix, limit=10))
            assert trie_results == index_results, f"Mismatch for prefix '{prefix}'"
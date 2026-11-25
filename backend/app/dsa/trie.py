"""
DSA Core: Trie for prefix search on usernames and display names.

Provides O(L + K) prefix lookup where L = prefix length, K = results returned.
Supports case-insensitive search with consistent normalization.

Also includes a simple sorted-list fallback for correctness verification.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TrieNode:
    """A node in the trie."""
    children: dict[str, TrieNode] = field(default_factory=dict)
    user_ids: set[str] = field(default_factory=set)


class Trie:
    """
    Trie for prefix search on user identifiers.
    
    Normalizes all keys to lowercase for case-insensitive search.
    Each terminal node stores a set of user IDs that have that exact key.
    
    Space: O(total characters in all keys)
    Insert: O(L) where L = key length
    Prefix search: O(L + K) where K = results returned
    """
    
    def __init__(self) -> None:
        self._root = TrieNode()
        self._key_to_users: dict[str, set[str]] = {}  # For updates/removal
    
    @staticmethod
    def _normalize(key: str) -> str:
        """Normalize key for case-insensitive matching."""
        return key.strip().lower()
    
    def insert(self, key: str, user_id: str) -> None:
        """
        Insert a key-user_id pair into the trie.
        
        If the key already exists for this user, it's idempotent.
        """
        norm_key = self._normalize(key)
        if not norm_key:
            return
        
        # Track for updates
        if norm_key not in self._key_to_users:
            self._key_to_users[norm_key] = set()
        self._key_to_users[norm_key].add(user_id)
        
        node = self._root
        for char in norm_key:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.user_ids.add(user_id)
    
    def remove(self, key: str, user_id: str) -> None:
        """
        Remove a key-user_id pair from the trie.
        
        If the key has no more user_ids, the path could be pruned
        (not implemented for simplicity - harmless for this scale).
        """
        norm_key = self._normalize(key)
        if not norm_key or norm_key not in self._key_to_users:
            return
        
        self._key_to_users[norm_key].discard(user_id)
        if not self._key_to_users[norm_key]:
            del self._key_to_users[norm_key]
        
        node = self._root
        for char in norm_key:
            if char not in node.children:
                return  # Key not in trie (shouldn't happen)
            node = node.children[char]
        node.user_ids.discard(user_id)
    
    def update_key(self, old_key: str, new_key: str, user_id: str) -> None:
        """Update a user's key (e.g., username change)."""
        self.remove(old_key, user_id)
        self.insert(new_key, user_id)
    
    def prefix_search(self, prefix: str, limit: int = 10) -> list[str]:
        """
        Search for user IDs matching the given prefix.
        
        Returns user IDs in lexicographic order of their keys.
        Limited to `limit` results.
        
        Time: O(L + K) where L = prefix length, K = results
        """
        norm_prefix = self._normalize(prefix)
        if not norm_prefix:
            return []
        
        node = self._root
        for char in norm_prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        # Collect all user_ids in this subtree, sorted by key
        results: list[tuple[str, str]] = []  # (key, user_id)
        self._collect(node, norm_prefix, results)
        
        # Sort by key for deterministic ordering, then take limit
        results.sort(key=lambda x: x[0])
        return [user_id for _, user_id in results[:limit]]
    
    def _collect(self, node: TrieNode, prefix: str, results: list[tuple[str, str]]) -> None:
        """Recursively collect all (key, user_id) pairs in subtree."""
        for user_id in node.user_ids:
            results.append((prefix, user_id))
        for char, child in node.children.items():
            self._collect(child, prefix + char, results)
    
    def exact_match(self, key: str) -> set[str]:
        """Get user IDs for an exact key match."""
        norm_key = self._normalize(key)
        return self._key_to_users.get(norm_key, set()).copy()
    
    def clear(self) -> None:
        """Clear the trie."""
        self._root = TrieNode()
        self._key_to_users.clear()


class PrefixIndex:
    """
    Simple sorted-list fallback for prefix search.
    
    Used for correctness verification and as a simpler alternative
    when the dataset is small enough that O(N) scan is acceptable.
    """
    
    def __init__(self) -> None:
        self._entries: list[tuple[str, str]] = []  # (normalized_key, user_id)
        self._user_to_keys: dict[str, set[str]] = {}
    
    @staticmethod
    def _normalize(key: str) -> str:
        return key.strip().lower()
    
    def insert(self, key: str, user_id: str) -> None:
        norm_key = self._normalize(key)
        if not norm_key:
            return
        
        if user_id not in self._user_to_keys:
            self._user_to_keys[user_id] = set()
        if norm_key in self._user_to_keys[user_id]:
            return  # Already indexed
        
        self._user_to_keys[user_id].add(norm_key)
        # Insert maintaining sorted order
        import bisect
        bisect.insort(self._entries, (norm_key, user_id))
    
    def remove(self, key: str, user_id: str) -> None:
        norm_key = self._normalize(key)
        if user_id in self._user_to_keys:
            self._user_to_keys[user_id].discard(norm_key)
            if not self._user_to_keys[user_id]:
                del self._user_to_keys[user_id]
        
        # Remove from entries (linear scan - acceptable for small N)
        self._entries = [(k, u) for k, u in self._entries if not (k == norm_key and u == user_id)]
    
    def update_key(self, old_key: str, new_key: str, user_id: str) -> None:
        self.remove(old_key, user_id)
        self.insert(new_key, user_id)
    
    def prefix_search(self, prefix: str, limit: int = 10) -> list[str]:
        norm_prefix = self._normalize(prefix)
        if not norm_prefix:
            return []
        
        import bisect
        # Find leftmost entry with prefix
        left = bisect.bisect_left(self._entries, (norm_prefix, ""))
        
        results = []
        # Scan a bit extra for dedup
        scan_end = min(len(self._entries), left + limit * 3)
        for i in range(left, scan_end):
            key, user_id = self._entries[i]
            if not key.startswith(norm_prefix):
                break
            if user_id not in results:
                results.append(user_id)
                if len(results) >= limit:
                    break
        
        return results
    
    def clear(self) -> None:
        self._entries.clear()
        self._user_to_keys.clear()
    
    def __len__(self) -> int:
        return len(self._entries)
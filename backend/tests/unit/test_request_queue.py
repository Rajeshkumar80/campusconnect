"""
Unit tests for the DSA Request Queue module.
Tests cover: send, accept, reject, cancel, duplicate, self-request, invalid actor/state.
"""


import pytest

from app.dsa.request_queue import (
    RequestQueue,
    RequestStatus,
)


class TestRequestQueue:
    """Test cases for RequestQueue."""

    def setup_method(self):
        """Set up a fresh queue for each test."""
        self.queue = RequestQueue()

    def test_create_request(self):
        """Create a basic pending request."""
        request = self.queue.create_request("alice", "bob")
        
        assert request.sender_id == "alice"
        assert request.recipient_id == "bob"
        assert request.status == RequestStatus.PENDING
        assert request.request_id in self.queue
        assert len(self.queue) == 1

    def test_self_request_raises_error(self):
        """Self-requests are rejected."""
        with pytest.raises(ValueError, match="yourself"):
            self.queue.create_request("alice", "alice")

    def test_duplicate_request_raises_error(self):
        """Duplicate pending request in same direction is rejected."""
        self.queue.create_request("alice", "bob")
        
        with pytest.raises(ValueError, match="already exists"):
            self.queue.create_request("alice", "bob")

    def test_reverse_pending_request_raises_error(self):
        """Reverse pending request is rejected."""
        self.queue.create_request("alice", "bob")
        
        with pytest.raises(ValueError, match="already has a pending request"):
            self.queue.create_request("bob", "alice")

    def test_accept_request(self):
        """Recipient can accept a pending request."""
        request = self.queue.create_request("alice", "bob")
        
        accepted = self.queue.accept_request(request.request_id, "bob")
        
        assert accepted.status == RequestStatus.ACCEPTED
        assert accepted.request_id == request.request_id
        assert self.queue.get_request(request.request_id).status == RequestStatus.ACCEPTED

    def test_accept_by_non_recipient_raises_error(self):
        """Only recipient can accept."""
        request = self.queue.create_request("alice", "bob")
        
        with pytest.raises(ValueError, match="Only the recipient"):
            self.queue.accept_request(request.request_id, "alice")
        
        with pytest.raises(ValueError, match="Only the recipient"):
            self.queue.accept_request(request.request_id, "charlie")

    def test_accept_non_pending_raises_error(self):
        """Cannot accept non-pending request."""
        request = self.queue.create_request("alice", "bob")
        self.queue.accept_request(request.request_id, "bob")
        
        with pytest.raises(ValueError, match="Only pending"):
            self.queue.accept_request(request.request_id, "bob")

    def test_reject_request(self):
        """Recipient can reject a pending request."""
        request = self.queue.create_request("alice", "bob")
        
        rejected = self.queue.reject_request(request.request_id, "bob")
        
        assert rejected.status == RequestStatus.REJECTED
        assert self.queue.get_request(request.request_id).status == RequestStatus.REJECTED

    def test_reject_by_non_recipient_raises_error(self):
        """Only recipient can reject."""
        request = self.queue.create_request("alice", "bob")
        
        with pytest.raises(ValueError, match="Only the recipient"):
            self.queue.reject_request(request.request_id, "alice")

    def test_cancel_request(self):
        """Sender can cancel a pending request."""
        request = self.queue.create_request("alice", "bob")
        
        cancelled = self.queue.cancel_request(request.request_id, "alice")
        
        assert cancelled.status == RequestStatus.CANCELLED
        assert self.queue.get_request(request.request_id).status == RequestStatus.CANCELLED

    def test_cancel_by_non_sender_raises_error(self):
        """Only sender can cancel."""
        request = self.queue.create_request("alice", "bob")
        
        with pytest.raises(ValueError, match="Only the sender"):
            self.queue.cancel_request(request.request_id, "bob")

    def test_cancel_non_pending_raises_error(self):
        """Cannot cancel non-pending request."""
        request = self.queue.create_request("alice", "bob")
        self.queue.accept_request(request.request_id, "bob")
        
        with pytest.raises(ValueError, match="Only pending"):
            self.queue.cancel_request(request.request_id, "alice")

    def test_get_pending_incoming(self):
        """Get incoming pending requests for a user."""
        self.queue.create_request("alice", "bob")
        self.queue.create_request("charlie", "bob")
        self.queue.create_request("bob", "diana")  # outgoing for bob
        
        incoming = self.queue.get_pending_incoming("bob")
        
        assert len(incoming) == 2
        sender_ids = {r.sender_id for r in incoming}
        assert sender_ids == {"alice", "charlie"}

    def test_get_pending_outgoing(self):
        """Get outgoing pending requests for a user."""
        self.queue.create_request("bob", "alice")
        self.queue.create_request("bob", "charlie")
        self.queue.create_request("diana", "bob")  # incoming for bob
        
        outgoing = self.queue.get_pending_outgoing("bob")
        
        assert len(outgoing) == 2
        recipient_ids = {r.recipient_id for r in outgoing}
        assert recipient_ids == {"alice", "charlie"}

    def test_has_pending_between(self):
        """Check if pending request exists between two users."""
        self.queue.create_request("alice", "bob")
        
        assert self.queue.has_pending_between("alice", "bob")
        assert self.queue.has_pending_between("bob", "alice")  # Either direction
        assert not self.queue.has_pending_between("alice", "charlie")

    def test_get_pending_between(self):
        """Get specific pending request between two users."""
        request = self.queue.create_request("alice", "bob")
        
        found = self.queue.get_pending_between("alice", "bob")
        assert found is not None
        assert found.request_id == request.request_id
        
        # Reverse direction returns None
        found = self.queue.get_pending_between("bob", "alice")
        assert found is None

    def test_accepted_request_not_in_pending(self):
        """Accepted requests don't appear in pending lists."""
        request = self.queue.create_request("alice", "bob")
        self.queue.accept_request(request.request_id, "bob")
        
        incoming = self.queue.get_pending_incoming("bob")
        outgoing = self.queue.get_pending_outgoing("alice")
        
        assert len(incoming) == 0
        assert len(outgoing) == 0

    def test_rejected_request_not_in_pending(self):
        """Rejected requests don't appear in pending lists."""
        request = self.queue.create_request("alice", "bob")
        self.queue.reject_request(request.request_id, "bob")
        
        incoming = self.queue.get_pending_incoming("bob")
        assert len(incoming) == 0

    def test_cancelled_request_not_in_pending(self):
        """Cancelled requests don't appear in pending lists."""
        request = self.queue.create_request("alice", "bob")
        self.queue.cancel_request(request.request_id, "alice")
        
        outgoing = self.queue.get_pending_outgoing("alice")
        assert len(outgoing) == 0

    def test_rebuild_from_requests(self):
        """Rebuild queue from persistent storage."""
        # Create some requests
        req1 = self.queue.create_request("alice", "bob")
        req2 = self.queue.create_request("bob", "charlie")
        self.queue.accept_request(req1.request_id, "bob")
        
        # Get all requests
        all_requests = list(self.queue._requests.values())
        
        # Rebuild
        new_queue = RequestQueue()
        new_queue.rebuild_from_requests(all_requests)
        
        assert len(new_queue) == 2
        assert new_queue.get_request(req1.request_id).status == RequestStatus.ACCEPTED
        assert new_queue.get_request(req2.request_id).status == RequestStatus.PENDING
        assert new_queue.has_pending_between("bob", "charlie")

    def test_request_immutability(self):
        """ConnectionRequest is immutable (frozen dataclass)."""
        request = self.queue.create_request("alice", "bob")
        
        with pytest.raises(AttributeError):
            request.status = RequestStatus.ACCEPTED
        
        with pytest.raises(AttributeError):
            request.sender_id = "charlie"

    def test_pending_after_accept_allows_new_request(self):
        """After acceptance, new request in same direction can be created."""
        req1 = self.queue.create_request("alice", "bob")
        self.queue.accept_request(req1.request_id, "bob")
        
        # Should be able to create new request (though in practice
        # they'd be connected, but queue allows it)
        req2 = self.queue.create_request("alice", "bob")
        assert req2.status == RequestStatus.PENDING
        assert req2.request_id != req1.request_id

    def test_multiple_users_independent(self):
        """Requests between different user pairs are independent."""
        self.queue.create_request("alice", "bob")
        self.queue.create_request("charlie", "diana")
        self.queue.create_request("eve", "frank")
        
        assert len(self.queue) == 3
        assert self.queue.has_pending_between("alice", "bob")
        assert self.queue.has_pending_between("charlie", "diana")
        assert self.queue.has_pending_between("eve", "frank")
        assert not self.queue.has_pending_between("alice", "charlie")

    def test_get_nonexistent_request(self):
        """Getting nonexistent request returns None."""
        assert self.queue.get_request("nonexistent") is None
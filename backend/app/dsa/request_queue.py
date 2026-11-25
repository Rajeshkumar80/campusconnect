"""
DSA Core: Connection request state management.

Models pending connection requests as directed stateful records,
separate from the accepted undirected graph.

State machine:
    pending -> accepted (recipient accepts)
    pending -> rejected (recipient rejects)
    pending -> cancelled (sender cancels)

Only valid actor/state transitions are allowed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4


class RequestStatus(StrEnum):
    """Connection request status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ConnectionRequest:
    """
    A directed connection request from sender to recipient.
    
    Not an edge in the accepted graph - only becomes an edge on acceptance.
    """
    request_id: str
    sender_id: str
    recipient_id: str
    status: RequestStatus
    created_at: datetime
    updated_at: datetime


class RequestQueue:
    """
    Manages connection requests with validated state transitions.
    
    Uses dict for O(1) lookup by request_id and compound indexes
    for sender/recipient queries.
    """
    
    def __init__(self) -> None:
        self._requests: dict[str, ConnectionRequest] = {}
        # Indexes for efficient queries
        self._by_sender: dict[str, set[str]] = {}      # sender_id -> set of request_ids
        self._by_recipient: dict[str, set[str]] = {}   # recipient_id -> set of request_ids
        self._by_pair_status: dict[tuple[str, str, RequestStatus], str] = {}
        # key: (sender, recipient, status) -> request_id
    
    def _add_indexes(self, request: ConnectionRequest) -> None:
        """Add request to all indexes."""
        self._by_sender.setdefault(request.sender_id, set()).add(request.request_id)
        self._by_recipient.setdefault(request.recipient_id, set()).add(request.request_id)
        self._by_pair_status[(request.sender_id, request.recipient_id, request.status)] = (
            request.request_id
        )

    def _remove_indexes(self, request: ConnectionRequest) -> None:
        """Remove request from all indexes."""
        self._by_sender.get(request.sender_id, set()).discard(request.request_id)
        if not self._by_sender.get(request.sender_id):
            self._by_sender.pop(request.sender_id, None)
        
        self._by_recipient.get(request.recipient_id, set()).discard(request.request_id)
        if not self._by_recipient.get(request.recipient_id):
            self._by_recipient.pop(request.recipient_id, None)
        
        self._by_pair_status.pop((request.sender_id, request.recipient_id, request.status), None)
    
    def _update_status_index(self, request: ConnectionRequest, old_status: RequestStatus) -> None:
        """Update status index after status change."""
        self._by_pair_status.pop((request.sender_id, request.recipient_id, old_status), None)
        self._by_pair_status[(request.sender_id, request.recipient_id, request.status)] = (
            request.request_id
        )

    def create_request(
        self,
        sender_id: str,
        recipient_id: str,
        request_id: str | None = None,
    ) -> ConnectionRequest:
        """
        Create a new pending connection request.

        Args:
            request_id: Optional ID to use instead of a generated one. Callers that
                persist the request must pass the persisted ID so both layers agree.

        Raises:
            ValueError: If self-request, duplicate pending, or reverse pending exists.
        """
        if sender_id == recipient_id:
            raise ValueError("Cannot send request to yourself")
        
        # Check for existing pending request in either direction
        existing = self._by_pair_status.get((sender_id, recipient_id, RequestStatus.PENDING))
        if existing:
            raise ValueError("Pending request already exists")
        
        existing_reverse = self._by_pair_status.get(
            (recipient_id, sender_id, RequestStatus.PENDING)
        )
        if existing_reverse:
            raise ValueError("Recipient already has a pending request to you")
        
        now = datetime.now(UTC)
        request = ConnectionRequest(
            request_id=request_id or str(uuid4()),
            sender_id=sender_id,
            recipient_id=recipient_id,
            status=RequestStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        
        self._requests[request.request_id] = request
        self._add_indexes(request)
        return request
    
    def accept_request(self, request_id: str, actor_id: str) -> ConnectionRequest:
        """
        Accept a pending request.
        
        Only the recipient can accept.
        
        Raises:
            ValueError: If request not found, not pending, or actor not recipient.
        """
        request = self._get_request(request_id)
        
        if request.status != RequestStatus.PENDING:
            raise ValueError("Only pending requests can be accepted")
        
        if actor_id != request.recipient_id:
            raise ValueError("Only the recipient can accept the request")
        
        old_status = request.status
        updated = ConnectionRequest(
            request_id=request.request_id,
            sender_id=request.sender_id,
            recipient_id=request.recipient_id,
            status=RequestStatus.ACCEPTED,
            created_at=request.created_at,
            updated_at=datetime.now(UTC),
        )
        
        self._requests[request_id] = updated
        self._update_status_index(updated, old_status)
        return updated
    
    def reject_request(self, request_id: str, actor_id: str) -> ConnectionRequest:
        """
        Reject a pending request.
        
        Only the recipient can reject.
        
        Raises:
            ValueError: If request not found, not pending, or actor not recipient.
        """
        request = self._get_request(request_id)
        
        if request.status != RequestStatus.PENDING:
            raise ValueError("Only pending requests can be rejected")
        
        if actor_id != request.recipient_id:
            raise ValueError("Only the recipient can reject the request")
        
        old_status = request.status
        updated = ConnectionRequest(
            request_id=request.request_id,
            sender_id=request.sender_id,
            recipient_id=request.recipient_id,
            status=RequestStatus.REJECTED,
            created_at=request.created_at,
            updated_at=datetime.now(UTC),
        )
        
        self._requests[request_id] = updated
        self._update_status_index(updated, old_status)
        return updated
    
    def cancel_request(self, request_id: str, actor_id: str) -> ConnectionRequest:
        """
        Cancel a pending request.
        
        Only the sender can cancel.
        
        Raises:
            ValueError: If request not found, not pending, or actor not sender.
        """
        request = self._get_request(request_id)
        
        if request.status != RequestStatus.PENDING:
            raise ValueError("Only pending requests can be cancelled")
        
        if actor_id != request.sender_id:
            raise ValueError("Only the sender can cancel the request")
        
        old_status = request.status
        updated = ConnectionRequest(
            request_id=request.request_id,
            sender_id=request.sender_id,
            recipient_id=request.recipient_id,
            status=RequestStatus.CANCELLED,
            created_at=request.created_at,
            updated_at=datetime.now(UTC),
        )
        
        self._requests[request_id] = updated
        self._update_status_index(updated, old_status)
        return updated
    
    def get_request(self, request_id: str) -> ConnectionRequest | None:
        """Get a request by ID."""
        return self._requests.get(request_id)
    
    def _get_request(self, request_id: str) -> ConnectionRequest:
        """Get request or raise ValueError."""
        request = self._requests.get(request_id)
        if not request:
            raise ValueError("Request not found")
        return request
    
    def get_pending_incoming(self, user_id: str) -> list[ConnectionRequest]:
        """Get all pending requests where user is recipient."""
        request_ids = self._by_recipient.get(user_id, set())
        return [
            self._requests[rid] for rid in request_ids
            if self._requests[rid].status == RequestStatus.PENDING
        ]
    
    def get_pending_outgoing(self, user_id: str) -> list[ConnectionRequest]:
        """Get all pending requests where user is sender."""
        request_ids = self._by_sender.get(user_id, set())
        return [
            self._requests[rid] for rid in request_ids
            if self._requests[rid].status == RequestStatus.PENDING
        ]
    
    def has_pending_between(self, user_a: str, user_b: str) -> bool:
        """Check if there's a pending request between two users (either direction)."""
        return (
            (user_a, user_b, RequestStatus.PENDING) in self._by_pair_status
            or (user_b, user_a, RequestStatus.PENDING) in self._by_pair_status
        )
    
    def get_pending_between(self, sender_id: str, recipient_id: str) -> ConnectionRequest | None:
        """Get pending request from sender to recipient if exists."""
        rid = self._by_pair_status.get((sender_id, recipient_id, RequestStatus.PENDING))
        if rid:
            return self._requests[rid]
        return None
    
    def rebuild_from_requests(self, requests: list[ConnectionRequest]) -> None:
        """Rebuild queue from persistent storage (startup)."""
        self._requests.clear()
        self._by_sender.clear()
        self._by_recipient.clear()
        self._by_pair_status.clear()
        
        for req in requests:
            self._requests[req.request_id] = req
            self._add_indexes(req)
    
    def __len__(self) -> int:
        return len(self._requests)
    
    def __contains__(self, request_id: str) -> bool:
        return request_id in self._requests
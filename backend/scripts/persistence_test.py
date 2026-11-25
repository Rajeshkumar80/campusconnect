"""Persistence check across a backend restart (FR-18).

Usage:
    python scripts\\persistence_test.py setup
    <restart the backend>
    python scripts\\persistence_test.py verify
"""

from __future__ import annotations

import sys

from smoke_test import FAILED, PASSED, Client, check

USERS = [
    ("restart_alice", "Alice Restart", "B.Tech CSE", 2),
    ("restart_bob", "Bob Restart", "B.Tech IT", 3),
]


def register(client: Client, username: str, name: str, programme: str, year: int) -> dict:
    status, body = client.post(
        "/auth/register",
        {
            "username": username,
            "password": "CampusPass123",
            "name": name,
            "programme": programme,
            "year": year,
            "bio": "persistence fixture",
            "skills": ["Python"],
        },
    )
    if status != 201:
        print(f"    register {username} -> {status} {body}")
        return {}
    return body.get("data", {}).get("user", {})


def setup() -> int:
    alice = Client()
    alice.get("/auth/csrf")
    alice_user = register(alice, *USERS[0])
    bob = Client()
    bob.get("/auth/csrf")
    bob_user = register(bob, *USERS[1])
    check("alice registered", bool(alice_user), str(alice_user))
    check("bob registered", bool(bob_user), str(bob_user))
    if not alice_user or not bob_user:
        return 1

    status, body = alice.post(
        "/connections/requests", {"recipient_id": bob_user["user_id"]}
    )
    check("request created", status == 201, f"{status} {body}")
    request_id = body.get("data", {}).get("request", {}).get("request_id")

    status, body = bob.post(f"/connections/requests/{request_id}/accept")
    check("request accepted", status == 200, f"{status} {body}")

    status, body = alice.post("/posts", {"text": "persistence check post"})
    check("post created", status == 201, f"{status} {body}")
    return 0


def verify() -> int:
    alice = Client()
    alice.get("/auth/csrf")
    status, body = alice.post(
        "/auth/login", {"username": "restart_alice", "password": "CampusPass123"}
    )
    check("login works after restart", status == 200, f"{status} {body}")
    if status != 200:
        return 1

    status, body = alice.get("/connections")
    conns = body.get("data", {}).get("connections", [])
    check("connection survived restart", len(conns) == 1, f"{status} {body}")
    check(
        "connection summary correct",
        bool(conns) and conns[0]["username"] == "restart_bob",
        str(conns),
    )

    status, body = alice.get("/posts/mine")
    posts = body.get("data", {}).get("posts", [])
    check("post survived restart", len(posts) == 1, f"{status} {body}")

    # FR-16: the feed shows only connections' posts, so check bob's feed.
    bob = Client()
    bob.get("/auth/csrf")
    status, body = bob.post(
        "/auth/login", {"username": "restart_bob", "password": "CampusPass123"}
    )
    check("bob can log in after restart", status == 200, f"{status} {body}")
    status, body = bob.get("/posts/feed")
    feed = body.get("data", {}).get("feed", [])
    check("feed merge works after restart", len(feed) == 1, f"{status} {body}")

    # The graph is rebuilt from storage, so degree must still resolve.
    bob_id = conns[0]["user_id"] if conns else "missing"
    status, body = alice.get(f"/connections/{bob_id}/degree")
    check(
        "graph rebuilt: degree is 1",
        body.get("data", {}).get("degree", {}).get("degree") == 1,
        f"{status} {body}",
    )

    # The trie is rebuilt from storage, including display names.
    status, body = alice.get("/users/search?q=bob")
    found = body.get("data", {}).get("users", [])
    check("trie rebuilt: search by name prefix", any(u["username"] == "restart_bob" for u in found), str(body))
    status, body = alice.get("/users/search?q=restart")
    found = body.get("data", {}).get("users", [])
    check("trie rebuilt: search by username prefix", any(u["username"] == "restart_bob" for u in found), str(body))

    print(f"\n{'=' * 50}")
    print(f"PASSED: {len(PASSED)}   FAILED: {len(FAILED)}")
    for failure in FAILED:
        print(f"  FAILED: {failure}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    phase = sys.argv[1] if len(sys.argv) > 1 else "setup"
    sys.exit(setup() if phase == "setup" else verify())

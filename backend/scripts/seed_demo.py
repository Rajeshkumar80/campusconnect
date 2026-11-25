"""Rebuild the synthetic demo world: five students, a connection graph and a few posts.

Run from backend/:  .venv\\Scripts\\python.exe scripts\\seed_demo.py
Restart the Flask server afterwards so its in-memory graph reloads.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pymongo

from app import create_app

PASSWORD = "CampusPass123"

USERS = [
    {
        "username": "asha_demo",
        "name": "Asha Menon",
        "programme": "B.Tech Computer Science",
        "year": 3,
        "bio": "Graphs, chai and late-night debugging. Building CampusConnect for the DSA mini-project.",
        "skills": ["Python", "Flask", "React", "Data Structures"],
    },
    {
        "username": "dev_demo",
        "name": "Dev Rao",
        "programme": "B.Tech Computer Science",
        "year": 3,
        "bio": "Backend and databases. Usually found optimising a query that did not need it.",
        "skills": ["MongoDB", "SQL", "Flask", "System Design"],
    },
    {
        "username": "mira_demo",
        "name": "Mira Iyer",
        "programme": "B.Tech Electronics",
        "year": 2,
        "bio": "Embedded systems, PCB layouts, and a growing interest in graph algorithms.",
        "skills": ["C++", "Embedded C", "PCB Design"],
    },
    {
        "username": "kiran_demo",
        "name": "Kiran Shetty",
        "programme": "B.Tech Mechanical",
        "year": 4,
        "bio": "Formula Student team. CAD by day, simulation by night.",
        "skills": ["SolidWorks", "ANSYS", "Manufacturing"],
    },
    {
        "username": "noor_demo",
        "name": "Noor Khan",
        "programme": "M.Tech Data Science",
        "year": 1,
        "bio": "Recommendation systems and graph mining. Looking for project collaborators.",
        "skills": ["Python", "Pandas", "Graph Mining", "ML"],
    },
]

# Accepted edges, listed once each.
EDGES = [
    ("asha_demo", "dev_demo"),
    ("asha_demo", "mira_demo"),
    ("dev_demo", "mira_demo"),
    ("dev_demo", "kiran_demo"),
    ("mira_demo", "noor_demo"),
    ("kiran_demo", "noor_demo"),
]

# Sent but not yet accepted, so the recipient sees a live request.
PENDING = [("kiran_demo", "asha_demo")]

POSTS = [
    ("dev_demo", "Mongo index lesson of the day: a partial unique index lets rejected requests be re-sent without duplicate pending rows. Small schema change, whole class of bugs gone."),
    ("mira_demo", "Finally got the line-following robot to stop drifting left. The fix was a two-line PID tweak and an embarrassing amount of time."),
    ("noor_demo", "Reading about Jaccard similarity for friend recommendations. Curious how it behaves on small campus graphs compared to plain common-neighbour counts."),
    ("dev_demo", "Library, third floor, 11 pm. The Wi-Fi is faster and the coffee machine still works. Highly recommended study spot."),
    ("asha_demo", "Shipped the photo upload flow for CampusConnect today — magic-byte checks, size caps, and cleanup when a post is deleted."),
]


def main() -> int:
    app = create_app("development")
    app.config["WTF_CSRF_ENABLED"] = False

    db = pymongo.MongoClient(app.config["MONGODB_URI"]).get_database(
        app.config["MONGODB_DATABASE"]
    )

    usernames = [user["username"] for user in USERS]
    if "--reset" in sys.argv:
        for collection in ("users", "profiles", "connections", "connection_requests", "posts"):
            db[collection].delete_many({})

    existing = list(db.users.find({"username": {"$in": usernames}}, {"_id": 1}))
    existing_ids = [user["_id"] for user in existing]
    if existing_ids:
        db.connections.delete_many(
            {"$or": [{"user_low": {"$in": existing_ids}}, {"user_high": {"$in": existing_ids}}]}
        )
        db.connection_requests.delete_many(
            {"$or": [{"sender_id": {"$in": existing_ids}}, {"recipient_id": {"$in": existing_ids}}]}
        )
        db.posts.delete_many({"author_id": {"$in": existing_ids}})
        db.profiles.delete_many({"_id": {"$in": existing_ids}})
        db.users.delete_many({"_id": {"$in": existing_ids}})

    client = app.test_client()
    ids: dict[str, str] = {}

    for user in USERS:
        response = client.post("/api/v1/auth/register", json={**user, "password": PASSWORD})
        assert response.status_code == 201, (user["username"], response.get_json())
        ids[user["username"]] = response.get_json()["data"]["user"]["user_id"]
        client.post("/api/v1/auth/logout")

    def login(username: str) -> None:
        response = client.post(
            "/api/v1/auth/login", json={"username": username, "password": PASSWORD}
        )
        assert response.status_code == 200, (username, response.get_json())

    for sender, recipient in EDGES:
        login(sender)
        response = client.post(
            "/api/v1/connections/requests", json={"recipient_id": ids[recipient]}
        )
        assert response.status_code == 201, (sender, recipient, response.get_json())
        request_id = response.get_json()["data"]["request"]["request_id"]
        client.post("/api/v1/auth/logout")

        login(recipient)
        response = client.post(f"/api/v1/connections/requests/{request_id}/accept")
        assert response.status_code == 200, (recipient, sender, response.get_json())
        client.post("/api/v1/auth/logout")

    for sender, recipient in PENDING:
        login(sender)
        response = client.post(
            "/api/v1/connections/requests", json={"recipient_id": ids[recipient]}
        )
        assert response.status_code == 201, (sender, recipient, response.get_json())
        client.post("/api/v1/auth/logout")

    for author, text in POSTS:
        login(author)
        response = client.post("/api/v1/posts", json={"text": text})
        assert response.status_code == 201, (author, response.get_json())
        client.post("/api/v1/auth/logout")

    print(f"Seeded {len(USERS)} users, {len(EDGES)} accepted connections, "
          f"{len(PENDING)} pending request(s) and {len(POSTS)} posts.")
    print(f"Log in with any demo username and password {PASSWORD}.")
    print("Restart the Flask server so the in-memory graph picks up the new edges.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Seed CampusConnect with the full class list directly via MongoDB."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pymongo
from argon2 import PasswordHasher

from app import create_app

PASSWORD = "CampusPass123"
ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16)

USERS = [
    {"username": "pruthvi", "name": "Pruthvi", "programme": "B.Tech Computer Science", "year": 3,
     "bio": "Building cool things with code.", "skills": ["Python", "React", "DSA"]},
    {"username": "rajesh", "name": "Rajesh", "programme": "B.Tech Computer Science", "year": 3,
     "bio": "Full-stack developer.", "skills": ["Flask", "MongoDB", "React"]},
    {"username": "sahana", "name": "Sahana", "programme": "B.Tech Computer Science", "year": 3,
     "bio": "Love algorithms and graphs.", "skills": ["Python", "Graph Theory", "Competitive Programming"]},
    {"username": "chandhu", "name": "Chandhu", "programme": "B.Tech Electronics", "year": 2,
     "bio": "Embedded systems enthusiast.", "skills": ["C", "Embedded C", "PCB Design"]},
    {"username": "manasa", "name": "Manasa", "programme": "B.Tech Computer Science", "year": 3,
     "bio": "Frontend and UI lover.", "skills": ["React", "TypeScript", "Tailwind"]},
    {"username": "mithun", "name": "Mithun", "programme": "B.Tech Mechanical", "year": 4,
     "bio": "CAD and simulations.", "skills": ["SolidWorks", "ANSYS", "Manufacturing"]},
    {"username": "samarth", "name": "Samarth", "programme": "B.Tech Computer Science", "year": 2,
     "bio": "Backend APIs and databases.", "skills": ["Node.js", "PostgreSQL", "Docker"]},
    {"username": "kushi", "name": "Kushi", "programme": "B.Tech Computer Science", "year": 3,
     "bio": "Data structures and algorithms.", "skills": ["Python", "DSA", "LeetCode"]},
    {"username": "harshala", "name": "Harshala", "programme": "M.Tech Data Science", "year": 1,
     "bio": "ML and recommendation systems.", "skills": ["Python", "PyTorch", "Graph Mining"]},
    {"username": "punith", "name": "Punith", "programme": "B.Tech Civil", "year": 4,
     "bio": "Structural analysis.", "skills": ["AutoCAD", "STAAD.Pro", "Revit"]},
    {"username": "amaravathi", "name": "Amaravathi", "programme": "B.Tech Electrical", "year": 3,
     "bio": "Power systems and IoT.", "skills": ["MATLAB", "Arduino", "IoT"]},
    {"username": "keshav", "name": "Keshav", "programme": "B.Tech Computer Science", "year": 2,
     "bio": "Competitive programmer.", "skills": ["C++", "Algorithms", "Codeforces"]},
    {"username": "manju", "name": "Manju", "programme": "B.Tech Electronics", "year": 3,
     "bio": "VLSI and chip design.", "skills": ["Verilog", "VLSI", "Cadence"]},
    {"username": "pavan", "name": "Pavan", "programme": "B.Tech Mechanical", "year": 3,
     "bio": "Robotics and automation.", "skills": ["ROS", "Python", "Robotics"]},
    {"username": "vinay", "name": "Vinay", "programme": "B.Tech Computer Science", "year": 2,
     "bio": "Cloud and DevOps.", "skills": ["AWS", "Kubernetes", "Terraform"]},
    {"username": "preetham", "name": "Preetham", "programme": "B.Tech Computer Science", "year": 3,
     "bio": "Security and cryptography.", "skills": ["Python", "Security", "CTF"]},
    {"username": "jeevan", "name": "Jeevan", "programme": "B.Tech Civil", "year": 2,
     "bio": "Construction management.", "skills": ["Primavera", "MS Project", "BIM"]},
    {"username": "prajwal", "name": "Prajwal", "programme": "B.Tech Computer Science", "year": 3,
     "bio": "Full-stack web dev.", "skills": ["MERN", "Next.js", "GraphQL"]},
    {"username": "sanjay", "name": "Sanjay", "programme": "B.Tech Electronics", "year": 4,
     "bio": "Signal processing.", "skills": ["MATLAB", "DSP", "Python"]},
    {"username": "mithin", "name": "Mithin", "programme": "B.Tech Computer Science", "year": 2,
     "bio": "Mobile development.", "skills": ["Flutter", "Dart", "Firebase"]},
    {"username": "suhas", "name": "Suhas", "programme": "B.Tech Computer Science", "year": 3,
     "bio": "Distributed systems.", "skills": ["Go", "gRPC", "Microservices"]},
    {"username": "chaithnya", "name": "Chaithnya", "programme": "M.Tech Data Science", "year": 1,
     "bio": "NLP and LLMs.", "skills": ["Python", "Transformers", "HuggingFace"]},
    {"username": "sneha", "name": "Sneha", "programme": "B.Tech Computer Science", "year": 3,
     "bio": "UI/UX and frontend.", "skills": ["Figma", "React", "CSS"]},
    {"username": "sanjana", "name": "Sanjana", "programme": "B.Tech Computer Science", "year": 2,
     "bio": "Backend and APIs.", "skills": ["Java", "Spring Boot", "MySQL"]},
    {"username": "monika", "name": "Monika", "programme": "B.Tech Electronics", "year": 3,
     "bio": "IoT and sensors.", "skills": ["ESP32", "MQTT", "Arduino"]},
    {"username": "anjali", "name": "Anjali", "programme": "B.Tech Computer Science", "year": 3,
     "bio": "Testing and QA.", "skills": ["Selenium", "Playwright", "Cypress"]},
    {"username": "geetha", "name": "Geetha", "programme": "B.Tech Computer Science", "year": 4,
     "bio": "Database internals.", "skills": ["PostgreSQL", "ClickHouse", "SQL"]},
]

# Connections: ring + cross links (avoid duplicates)
usernames = [u["username"] for u in USERS]
EDGES = []
for i in range(len(usernames)):
    EDGES.append((usernames[i], usernames[(i + 1) % len(usernames)]))
cross = [
    ("pruthvi", "sahana"), ("rajesh", "sahana"),
    ("manasa", "kushi"), ("manasa", "sneha"), ("kushi", "sneha"),
    ("mithun", "punith"), ("pavan", "jeevan"),
    ("samarth", "vinay"), ("samarth", "suhas"),
    ("harshala", "chaithnya"), ("harshala", "geetha"),
    ("keshav", "preetham"), ("preetham", "prajwal"),
    ("manju", "sanjay"), ("manju", "monika"),
    ("vinay", "suhas"), ("prajwal", "sanjana"),
    ("mithin", "anjali"), ("sneha", "sanjana"),
]
EDGES.extend(cross)

# Pending requests
PENDING = [
    ("geetha", "pruthvi"),
    ("anjali", "rajesh"),
    ("sanjana", "sahana"),
]

# Posts
POSTS = [(u["username"], f"Hello from {u['name']}! Just joined CampusConnect.") for u in USERS]


def main() -> int:
    app = create_app("development")
    app.config["RATELIMIT_ENABLED"] = False

    db = pymongo.MongoClient(app.config["MONGODB_URI"]).get_database(
        app.config["MONGODB_DATABASE"]
    )

    # Full reset
    for collection in ("users", "profiles", "connections", "connection_requests", "posts"):
        db[collection].delete_many({})

    now = datetime.now(UTC)
    password_hash = ph.hash(PASSWORD)
    ids: dict[str, str] = {}

    # Insert users + profiles
    for user in USERS:
        user_id = str(uuid4())
        ids[user["username"]] = user_id
        db.users.insert_one({
            "_id": user_id,
            "username": user["username"],
            "password_hash": password_hash,
            "created_at": now,
            "updated_at": now,
            "status": "active",
        })
        db.profiles.insert_one({
            "_id": user_id,
            "name": user["name"],
            "programme": user["programme"],
            "year": user["year"],
            "bio": user["bio"],
            "skills": user["skills"],
            "updated_at": now,
        })

    # Insert accepted connections (undirected: store with user_low < user_high)
    for sender, recipient in EDGES:
        u1, u2 = ids[sender], ids[recipient]
        low, high = (u1, u2) if u1 < u2 else (u2, u1)
        conn_id = f"{low}:{high}"
        if not db.connections.find_one({"_id": conn_id}):
            db.connections.insert_one({
                "_id": conn_id,
                "user_low": low,
                "user_high": high,
                "created_at": now,
            })

    # Insert connection requests (pending)
    for sender, recipient in PENDING:
        req_id = str(uuid4())
        db.connection_requests.insert_one({
            "_id": req_id,
            "sender_id": ids[sender],
            "recipient_id": ids[recipient],
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        })

    # Insert posts
    for author, text in POSTS:
        post_id = str(uuid4())
        db.posts.insert_one({
            "_id": post_id,
            "author_id": ids[author],
            "text": text,
            "media": None,
            "created_at": now,
            "updated_at": now,
        })

    print(f"Seeded {len(USERS)} users, {len(EDGES)} connections, {len(PENDING)} pending requests, {len(POSTS)} posts.")
    print(f"All passwords: {PASSWORD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
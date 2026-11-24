# CampusConnect

A student networking web application for Chanakya University, built as a DSA mini-project demonstrating core data structures and algorithms.

## Architecture

```
React + TypeScript + Vite (Frontend)
    ↓ HTTPS/JSON
Flask REST API (Backend)
    ↓
Application Services
    ├── Python DSA Engine (in-memory)
    │   ├── Graph (adjacency lists)
    │   ├── BFS (shortest paths, degrees)
    │   ├── Recommendations (common neighbors/Jaccard)
    │   ├── Trie (prefix search)
    │   ├── FeedHeap (heap merge for feed)
    │   └── RequestQueue (connection request state machine)
    └── Repository Layer (MongoDB)
```

## Features

### Mandatory (per university brief)
- ✅ User registration/login with Argon2id password hashing
- ✅ Student profiles (name, programme, year, bio, skills)
- ✅ Connection requests (send, accept, reject, cancel)
- ✅ Accepted connections (undirected graph)
- ✅ Mutual connections
- ✅ People you may know (ranked by common neighbors)
- ✅ Connection degree (1st/2nd/3rd/3+/Not connected)
- ✅ Shortest connection chain (BFS)
- ✅ Text posts (create, delete own)
- ✅ Home feed (newest-first from connections, heap merge)
- ✅ Prefix search (Trie-based)
- ✅ MongoDB persistence with startup rebuild

### DSA Implementation
| Feature | Data Structure / Algorithm | Complexity |
|---------|---------------------------|------------|
| Network graph | Adjacency list `dict[str, set[str]]` | O(V+E) space |
| Shortest path | BFS + queue + parent map | O(V+E) |
| Connection degree | BFS limited to depth 3 | O(V+E) bounded |
| Mutual connections | Set intersection | O(min(deg(u), deg(v))) |
| Suggestions | Common neighbor count | O(deg(u) × avg_deg) |
| Prefix search | Trie | O(L+K) |
| Feed merge | Max-heap (`heapq`) | O(P log C) |
| Request queue | State machine with indexes | O(1) operations |

## Project Structure

```
campusconnect/
├── PRD.md                 # Product Requirements Document
├── PLAN.md                # Technical Architecture Plan
├── EXECUTION.md           # Step-by-step Implementation Runbook
├── README.md              # This file
├── .gitignore
├── .env.example           # Environment variable template
├── backend/
│   ├── wsgi.py            # WSGI entry point
│   ├── pyproject.toml     # Python dependencies
│   ├── app/
│   │   ├── __init__.py    # Flask app factory
│   │   ├── config.py      # Configuration
│   │   ├── extensions.py  # Flask extensions (MongoDB, CSRF, Rate limiting)
│   │   ├── dsa/           # Pure Python DSA modules
│   │   │   ├── graph.py
│   │   │   ├── bfs.py
│   │   │   ├── recommendations.py
│   │   │   ├── trie.py
│   │   │   ├── feed_heap.py
│   │   │   └── request_queue.py
│   │   ├── api/           # REST API routes
│   │   ├── services/      # Business logic
│   │   ├── repositories/  # Data access (MongoDB)
│   │   ├── security/      # Auth, CSRF, rate limiting
│   │   └── utils/
│   └── tests/
│       ├── unit/          # DSA unit tests (119 tests)
│       └── integration/   # Flask app factory tests
└── frontend/              # React + TypeScript + Vite (to be implemented)
```

## Setup

### Prerequisites
- Python 3.12+
- Node.js LTS
- MongoDB (connection URI provided separately)

### Backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt  # or use pyproject.toml
cp .env.example .env
# Edit .env with real MongoDB URI
python wsgi.py
```

### Running Tests
```bash
cd backend
.venv\Scripts\Activate.ps1
pytest tests/ -v
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Current user

### Profiles
- `GET /api/v1/profiles/me` - Get own profile
- `PATCH /api/v1/profiles/me` - Update own profile
- `GET /api/v1/profiles/<user_id>` - Get user's public profile

### Users/Search
- `GET /api/v1/users/search?q=<prefix>` - Prefix search
- `GET /api/v1/users/<user_id>` - Get user details

### Connections
- `GET /api/v1/connections` - List connections
- `POST /api/v1/connections/requests` - Send request
- `GET /api/v1/connections/requests/incoming` - Incoming requests
- `GET /api/v1/connections/requests/outgoing` - Outgoing requests
- `POST /api/v1/connections/requests/<id>/accept` - Accept request
- `POST /api/v1/connections/requests/<id>/reject` - Reject request
- `POST /api/v1/connections/requests/<id>/cancel` - Cancel request
- `DELETE /api/v1/connections/<user_id>` - Remove connection
- `GET /api/v1/connections/<user_id>/mutual` - Mutual connections
- `GET /api/v1/connections/<user_id>/degree` - Connection degree
- `GET /api/v1/connections/<user_id>/path` - Shortest path
- `GET /api/v1/connections/suggestions` - People you may know

### Posts
- `POST /api/v1/posts` - Create post
- `GET /api/v1/posts/mine` - Own posts
- `DELETE /api/v1/posts/<post_id>` - Delete own post
- `GET /api/v1/posts/feed` - Home feed

### Health
- `GET /api/v1/health/live` - Liveness probe
- `GET /api/v1/health/ready` - Readiness probe

## Security

- Argon2id password hashing
- HttpOnly, Secure, SameSite session cookies
- CSRF protection on state-changing requests
- Rate limiting on auth, search, connections, posts
- Server-side authorization on all protected operations
- NoSQL injection prevention (allowlisted fields)
- XSS-safe rendering (no `dangerouslySetInnerHTML`)
- Strict CORS allowlist

## DSA Explainability

Each algorithm module includes:
- Complexity analysis (time/space)
- Deterministic tie-breaking rules
- Comprehensive unit tests
- Inline documentation explaining the approach

## University Submission

- All mandatory requirements implemented
- DSA engine independent of Flask/MongoDB
- Adjacency-list graph with BFS demonstrated
- Prefix search (Trie) and heap-based feed merge demonstrated
- MongoDB persistence with indexes
- Passwords hashed with Argon2id
- Authorization tests pass
- 4-5 synthetic user demo dataset ready
- Clean architecture with separation of concerns

## Team

Up to 4 students. Every member must understand the complete system for viva.
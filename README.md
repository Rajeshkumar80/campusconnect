# CampusConnect

A student networking platform for **Chanakya University**, built as a **Data Structures & Algorithms mini-project**.

Students can create profiles, connect with classmates, share posts with photos or video, like and comment, message each other with files and voice notes, and discover people through graph-based mutual-connection suggestions. The DSA core is written in **pure Python** with no framework or database dependency, so every data structure and algorithm can be demonstrated and tested on its own.

**Stack:** React 19 + TypeScript + Vite · Flask REST API · MongoDB · pure-Python DSA engine

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [DSA Core](#dsa-core)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Data Model](#data-model)
- [Media Storage](#media-storage)
- [Security](#security)
- [Testing and Quality](#testing-and-quality)
- [Troubleshooting](#troubleshooting)
- [Known Limitations](#known-limitations)
- [Documentation](#documentation)

---

## Overview

CampusConnect is a small, complete social network:

- **Accounts** — register and log in with Argon2id-hashed passwords and cookie sessions.
- **Profiles** — name, programme, year, bio and skills, editable from Settings.
- **Network** — send, accept, reject and cancel connection requests; accepted connections form an undirected graph.
- **Feed** — newest-first posts from your accepted connections, merged with a heap.
- **Posts** — text plus one optional image or video; likes, comments and sharing.
- **Messages** — 1-to-1 chat with text, images, PDFs, voice notes and shared posts.
- **Discover** — mutual-connection-ranked suggestions, followed by other students.
- **Notifications** — likes, comments and incoming requests, with unread badges.
- **Search** — Trie-based prefix search on usernames and names.

All application data is persisted in MongoDB. The DSA engine is rebuilt in memory from MongoDB on startup and kept in sync as connections change.

---

## Features

### Accounts and profiles
- Registration with validation and automatic login.
- Argon2id password hashing (time cost 3, memory 64 MB, parallelism 4).
- Session cookies (`HttpOnly`, `SameSite=Lax`, optional `Secure`).
- Editable profile: display name, programme, year, bio, skills.
- Initials-based avatars generated in the UI.

### Network and DSA
- Connection requests with a four-state machine: `pending → accepted | rejected | cancelled`.
- Accepted connections stored once per canonical pair (`user_low < user_high`).
- Mutual connection count and connection degree (1st/2nd/3rd/3+).
- Shortest connection chain via BFS.
- "People you may know" ranked by common neighbours, with Jaccard similarity available in the DSA module.
- Discover page lists ranked mutual suggestions first, then remaining students with zero mutuals.

### Posts and feed
- Create text posts (max 5,000 characters) with one optional image or video.
- Dedicated `/create-post` page; publishing redirects back to the feed.
- Newest-first home feed from accepted connections, merged with a max-heap.
- Like/unlike with Instagram-style display: "Rajesh and 5 others like this".
- Comments with author names, newest last, visible counts next to likes.
- Share a post into a direct message.
- Delete your own posts (and their media file).
- Profile pages show any student's posts.

### Messaging
- Threads for every accepted connection, including connections with no messages yet.
- Text, image, PDF and voice-note messages.
- Voice notes recorded in the browser (`MediaRecorder`, `.weba`).
- Shared-post messages render a compact post card.
- Unread counts and per-conversation read state.
- Message button appears only for accepted connections.
- Polling appends only new messages by `message_id`, so the conversation does not jump.

### Notifications
- Likes, comments and incoming connection requests.
- Unread state tracked with `notifications_seen_at`.
- Nav badge combines pending requests, unseen likes/comments and unread messages.
- Polling-based refresh (no WebSocket dependency).

### UI/UX
- Light theme: white surfaces with orange `#ff8c00` accents.
- Dark theme: pure black surfaces with the same orange accent.
- Sharper corners (`rounded-lg` / `rounded-xl`), consistent spacing and alignment.
- Image lightbox instead of opening a new tab.
- Space bar inside inputs/textareas never scrolls the page.
- Responsive layout with a persistent desktop sidebar and mobile navigation.

---

## Tech Stack

### Frontend

| Technology | Version | Purpose |
|---|---|---|
| React | 19.3 | UI components |
| TypeScript | 7.0 | Type safety |
| Vite | 8.3 | Dev server and production build |
| React Router | 7.18 | Client-side routing |
| Tailwind CSS | 3.4 | Styling and theme tokens |
| PostCSS + Autoprefixer | 8.5 / 10.7 | CSS pipeline |
| Framer Motion | 14.14 | Page and component transitions |
| Headless UI | 2.2 | Accessible modals and menus |
| Lucide React | 1.79 | Icons |
| Axios | 1.21 | HTTP client with CSRF retry |
| date-fns | 4.4 | Relative timestamps |
| clsx + tailwind-merge | 2.1 / 3.7 | Conditional class composition |
| oxlint | 1.90 | Linting |

### Backend

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.12+ (3.14 tested) | Runtime |
| Flask | 3.1 | REST API and app factory |
| Werkzeug | 3.1 | WSGI and dev server |
| PyMongo | 4.20 | MongoDB driver |
| Flask-CORS | 6.0 | Origin allowlist |
| Flask-Limiter | 4.1 | Rate limiting |
| Flask-WTF | 1.3 | CSRF protection |
| argon2-cffi | 25.1 | Argon2id password hashing |
| python-dotenv | 1.2 | `.env` loading |
| pytest | 9.2 | Test runner |
| Ruff | 0.17 | Lint and format |

### Database and tooling

| Technology | Purpose |
|---|---|
| MongoDB 7+ (8.3 tested) or MongoDB Atlas | Document persistence |
| dnspython | `mongodb+srv://` DNS resolution |
| Git + GitHub | Version control |
| Node.js 20+ / npm 10+ | Frontend toolchain |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  React 19 + TypeScript + Vite            http://localhost:5173
│  Router · AuthContext · Tailwind · Framer Motion            │
└──────────────────────────┬──────────────────────────────────┘
                           │ JSON over HTTP
                           │ session cookie + X-CSRFToken
┌──────────────────────────▼──────────────────────────────────┐
│  Flask REST API                          http://localhost:5000
│  Blueprints → Services → Repositories                       │
│  CSRF · rate limiting · CORS allowlist · authorization      │
├──────────────────────────┬──────────────────────────────────┤
│  Pure-Python DSA engine  │  MongoDB                         │
│  Graph · BFS · Trie      │  users, profiles, connections,   │
│  Heap · Jaccard · Queue  │  requests, posts, likes,         │
│                          │  comments, messages              │
└──────────────────────────┴──────────────────────────────────┘
```

**Request flow**

1. React calls the API with `withCredentials: true`; the session cookie identifies the user.
2. Axios fetches a CSRF token from `GET /api/v1/auth/csrf` and sends it as `X-CSRFToken` on every write.
3. Flask validates the session, CSRF token and rate limit, then calls a service.
4. The service applies business rules and calls a MongoDB repository.
5. Graph/search/feed operations use the in-memory DSA engine, which is rebuilt from MongoDB at startup.

**Layers**

| Layer | Location | Responsibility |
|---|---|---|
| Routes | `backend/app/api/` | HTTP parsing, status codes, error envelopes |
| Services | `backend/app/services/` | Business rules, authorization, DSA orchestration |
| Repositories | `backend/app/repositories/` | MongoDB queries and document mapping |
| DSA core | `backend/app/dsa/` | Framework-free data structures and algorithms |
| Security | `backend/app/security/` | Login decorators and rate-limit definitions |
| Media | `backend/app/media.py` | Upload validation, magic-byte checks, storage |

---

## DSA Core

Every module in `backend/app/dsa/` is pure Python and independently unit-tested.

| Module | Structure / Algorithm | Used for | Complexity |
|---|---|---|---|
| `graph.py` | Adjacency list `dict[str, set[str]]` | Undirected connection network | `O(V + E)` space |
| `bfs.py` | Breadth-first search with queue and parent map | Shortest connection chain, degree | `O(V + E)` |
| `recommendations.py` | Two-hop candidates + common-neighbour count; optional Jaccard | "People you may know", Discover ranking | `O(deg(u) × avg_deg)` |
| `trie.py` | Prefix tree with lowercase normalisation | Username/name prefix search | `O(L + K)` |
| `feed_heap.py` | K-way merge with a max-heap (`heapq`, negated timestamps) | Newest-first home feed | `O(P log C)` |
| `request_queue.py` | Indexed request state machine | Send/accept/reject/cancel requests | `O(1)` per operation |

**Definitions**

- `V` = students, `E` = accepted connections, `L` = prefix length, `K` = results returned.
- `P` = posts returned in the feed, `C` = connection streams being merged.
- `deg(u)` = number of connections of user `u`.

**Design notes**

- Graph nodes are user IDs; edges are stored once as canonical pairs.
- BFS uses a `deque`, a visited set and a parent map, giving deterministic shortest paths.
- Recommendations exclude the user, direct connections and existing pending requests.
- Ties are broken deterministically by user ID so results are stable across runs.
- The feed heap stores `(-timestamp, tie_breaker, author_id, stream_index, post)`; each pop pushes the next post from the same author stream.
- MongoDB remains the source of truth; the DSA engine is a derived in-memory index rebuilt on startup.

---

## Project Structure

```
campusconnect/
├── backend/
│   ├── app/
│   │   ├── __init__.py                 # Flask app factory
│   │   ├── config.py                   # Environment-driven configuration
│   │   ├── extensions.py               # MongoDB, CSRF, CORS, rate limiter, indexes
│   │   ├── media.py                    # Upload allowlists, magic bytes, storage
│   │   ├── api/
│   │   │   ├── auth_routes.py
│   │   │   ├── connection_routes.py
│   │   │   ├── errors.py
│   │   │   ├── health_routes.py
│   │   │   ├── media_routes.py
│   │   │   ├── message_routes.py
│   │   │   ├── notification_routes.py
│   │   │   ├── post_routes.py
│   │   │   ├── profile_routes.py
│   │   │   └── user_routes.py
│   │   ├── dsa/
│   │   │   ├── graph.py
│   │   │   ├── bfs.py
│   │   │   ├── recommendations.py
│   │   │   ├── trie.py
│   │   │   ├── feed_heap.py
│   │   │   └── request_queue.py
│   │   ├── repositories/
│   │   │   ├── interfaces.py
│   │   │   ├── formatting.py
│   │   │   ├── mongo_user_repository.py
│   │   │   ├── mongo_connection_repository.py
│   │   │   └── mongo_post_repository.py
│   │   ├── security/
│   │   │   ├── decorators.py
│   │   │   └── rate_limits.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── connection_service.py
│   │   │   ├── engine.py
│   │   │   ├── post_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── social_service.py
│   │   │   └── user_service.py
│   │   └── utils/
│   ├── scripts/
│   │   ├── seed_all.py                 # 27 students, connections, posts
│   │   ├── seed_demo.py
│   │   ├── smoke_test.py
│   │   └── persistence_test.py
│   ├── tests/
│   │   ├── unit/                       # DSA, media and repository tests
│   │   └── integration/                # App factory test
│   ├── uploads/                        # Runtime media (git-ignored)
│   ├── .env.example
│   ├── pyproject.toml
│   └── wsgi.py                         # WSGI entry point
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── feed/                   # Composer, PostCard, PostMedia
│   │   │   ├── layout/                 # AuthShell, Layout
│   │   │   ├── profile/                # NetworkPanel
│   │   │   ├── ui/                     # Avatar, Badge, Button, Card, Input, Modal, PageHeader, Toast
│   │   │   └── ProtectedRoute.tsx
│   │   ├── context/AuthContext.tsx
│   │   ├── lib/api.ts                  # Axios client, CSRF retry, media URLs
│   │   ├── pages/                      # 11 route pages
│   │   ├── types/index.ts
│   │   ├── App.tsx
│   │   ├── index.css                   # Theme tokens and component classes
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── .gitignore
├── CREDENTIALS.md                      # 27 demo accounts
├── EXECUTION.md                        # Runbook and implementation record
├── PLAN..md                            # Technical plan
├── PRD.md                              # Product requirements
├── QA_REFERENCE.md                     # Viva questions and answers
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python 3.12+** (tested on 3.14)
- **Node.js 20+** and npm
- **MongoDB** — either:
  - a local server at `mongodb://localhost:27017`, or
  - a MongoDB Atlas cluster (`mongodb+srv://...`)

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/campusconnect.git
cd campusconnect
```

### 2. Backend

```powershell
cd backend

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate       # macOS / Linux

# Install the project and dev tools
pip install -e ".[dev]"

# Create your local environment file
Copy-Item .env.example .env       # Windows
# cp .env.example .env            # macOS / Linux

# Edit .env and set MONGODB_URI (local or Atlas)
```

Seed the demo dataset:

```powershell
python scripts/seed_all.py
```

> **Warning:** `seed_all.py` performs a full reset of `users`, `profiles`, `connections`, `connection_requests` and `posts`. Do not run it against a database you want to keep.

Start the API:

```powershell
python wsgi.py
```

The backend listens on **http://localhost:5000**.

### 3. Frontend

```powershell
cd frontend
npm install
npm run dev
```

The frontend listens on **http://localhost:5173**.

### 4. Open the app

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:5000/api/v1 |
| Liveness | http://localhost:5000/api/v1/health/live |
| Readiness | http://localhost:5000/api/v1/health/ready |

### Demo credentials

The seed script creates **27 real database accounts**. All share the same password:

```
Password: CampusPass123
```

Example usernames: `pruthvi`, `rajesh`, `sahana`, `manasa`, `harshala`, `mithun`, `kushi`.

The complete list is in [CREDENTIALS.md](CREDENTIALS.md).

---

## Environment Variables

Backend variables live in `backend/.env` (git-ignored). Start from `backend/.env.example`.

| Variable | Default | Purpose |
|---|---|---|
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB or Atlas connection string |
| `MONGODB_DATABASE` | `campusconnect` | Database name |
| `SECRET_KEY` | dev fallback | Flask session and CSRF signing key — set a long random value |
| `FLASK_ENV` | `development` | `development`, `testing` or `production` |
| `FLASK_DEBUG` | `false` | Enable Flask debug mode |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Frontend origin |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated CORS allowlist |
| `SESSION_COOKIE_SECURE` | `false` | Set `true` behind HTTPS |
| `PERMANENT_SESSION_LIFETIME` | `86400` | Session lifetime in seconds |
| `RATELIMIT_DEFAULT` | `100 per minute` | Global rate limit |
| `RATELIMIT_STORAGE_URL` | `memory://` | Limiter storage backend |
| `RATELIMIT_ENABLED` | `true` | Disable limits in tests with `false` |
| `UPLOAD_FOLDER` | `backend/uploads` | Absolute or relative media directory |
| `MAX_CONTENT_LENGTH` | `62914560` | Maximum request size (60 MB) |
| `ARGON2_TIME_COST` | `3` | Argon2id iterations |
| `ARGON2_MEMORY_COST` | `65536` | Argon2id memory in KiB |
| `ARGON2_PARALLELISM` | `4` | Argon2id lanes |

Frontend (optional):

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_URL` | `http://localhost:5000/api/v1` | Backend API base URL |

> `.env` is git-ignored. Only `.env.example` is committed. Never commit real credentials or secrets.

---

## API Reference

**Base URL:** `http://localhost:5000/api/v1`

**Response envelopes**

```json
{ "data": { ... } }
```

```json
{ "error": { "code": "VALIDATION_ERROR", "message": "Username is required" } }
```

**Authentication:** cookie session. **Writes:** send `X-CSRFToken` from `GET /auth/csrf`. Login and registration are CSRF-exempt.

### Authentication

| Method | Path | Description |
|---|---|---|
| `GET` | `/auth/csrf` | Issue a CSRF token (also in `X-CSRFToken` response header) |
| `POST` | `/auth/register` | Register and auto-login |
| `POST` | `/auth/login` | Log in |
| `POST` | `/auth/logout` | Log out |
| `GET` | `/auth/me` | Current user and profile |

### Profiles and users

| Method | Path | Description |
|---|---|---|
| `GET` | `/profiles/me` | Own profile |
| `PATCH` | `/profiles/me` | Update name, programme, year, bio, skills |
| `GET` | `/profiles/<user_id>` | Another student's public profile |
| `GET` | `/users/<user_id>` | User summary |
| `GET` | `/users/search?q=<prefix>` | Trie prefix search |

### Connections

| Method | Path | Description |
|---|---|---|
| `GET` | `/connections` | Accepted connections |
| `DELETE` | `/connections/<user_id>` | Remove a connection |
| `GET` | `/connections/<user_id>/mutual` | Mutual connections |
| `GET` | `/connections/<user_id>/degree` | 1st/2nd/3rd/3+/not connected |
| `GET` | `/connections/<user_id>/path` | Shortest BFS chain |
| `POST` | `/connections/requests` | Send a request |
| `GET` | `/connections/requests/incoming` | Incoming requests |
| `GET` | `/connections/requests/outgoing` | Outgoing requests |
| `POST` | `/connections/requests/<request_id>/accept` | Accept |
| `POST` | `/connections/requests/<request_id>/reject` | Reject |
| `POST` | `/connections/requests/<request_id>/cancel` | Cancel |
| `GET` | `/connections/suggestions` | Ranked "people you may know" |

### Posts and interactions

| Method | Path | Description |
|---|---|---|
| `POST` | `/posts` | Create a post (JSON text, or multipart with `media`) |
| `GET` | `/posts/feed` | Home feed (heap merge) |
| `GET` | `/posts/mine` | Own posts |
| `GET` | `/posts/user/<user_id>` | Any student's posts |
| `DELETE` | `/posts/<post_id>` | Delete own post |
| `POST` | `/posts/<post_id>/like` | Toggle like |
| `GET` | `/posts/<post_id>/comments` | List comments |
| `POST` | `/posts/<post_id>/comments` | Add a comment |
| `POST` | `/posts/<post_id>/share` | Share a post into a message |

### Messages

| Method | Path | Description |
|---|---|---|
| `GET` | `/messages/threads` | Connections with latest message and unread count |
| `GET` | `/messages/unread-count` | Unread message total |
| `GET` | `/messages/<user_id>` | Conversation; marks received messages read |
| `POST` | `/messages/<user_id>` | Send text, media or a shared post |

Messaging requires an accepted connection; other users receive `403`.

### Notifications

| Method | Path | Description |
|---|---|---|
| `GET` | `/notifications` | Likes, comments and requests for the current user |
| `GET` | `/notifications/count` | Unread notifications and messages |
| `POST` | `/notifications/read` | Mark notifications as seen |

### Media and health

| Method | Path | Description |
|---|---|---|
| `GET` | `/media/<filename>` | Authenticated media download |
| `GET` | `/health/live` | Process is alive |
| `GET` | `/health/ready` | MongoDB and DSA engine readiness |

---

## Data Model

| Collection | Key fields |
|---|---|
| `users` | `_id`, `username` (unique), `password_hash`, `created_at` |
| `profiles` | `_id` (= user ID), `name`, `programme`, `year`, `bio`, `skills` |
| `connection_requests` | `_id`, `sender_id`, `recipient_id`, `status`, `created_at`, `updated_at` |
| `connections` | `_id` = `"low:high"`, `user_low`, `user_high`, `created_at` |
| `posts` | `_id`, `author_id`, `text`, `media`, `created_at`, `updated_at` |
| `post_likes` | `post_id`, `user_id`, `created_at` |
| `comments` | `_id`, `post_id`, `author_id`, `text`, `created_at` |
| `messages` | `_id`, `sender_id`, `recipient_id`, `text`, `media`, `shared_post_id`, `created_at`, `read_at` |

**Indexes created at startup**

- `users.username` — unique
- `users.created_at`
- `connection_requests (sender_id, recipient_id)` — unique, only for `status: "pending"`
- `connection_requests (recipient_id, status)`
- `connection_requests (sender_id, status)`
- `connections (user_low, user_high)` — unique
- `connections.user_low`, `connections.user_high`
- `posts (author_id, created_at desc)`
- `posts.created_at`

Connections are stored once per pair using a canonical ordering, so the graph is undirected without duplicate edges.

---

## Media Storage

| Kind | Extensions | Max size |
|---|---|---|
| Post image | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` | 10 MB |
| Post video | `.mp4`, `.webm`, `.mov` | 50 MB |
| Message image | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` | 10 MB |
| Message document | `.pdf` | 20 MB |
| Message audio | `.mp3`, `.wav`, `.ogg`, `.m4a`, `.weba` | 20 MB |

- Files are stored under `UPLOAD_FOLDER` with UUID names.
- The original filename is kept only for display.
- Uploads are validated by extension **and** magic bytes, so a renamed executable cannot pass as media.
- Files are served only through the authenticated `GET /api/v1/media/<filename>` route.
- Deleting a post also removes its media file.

---

## Security

- **Passwords:** Argon2id with configurable time/memory/parallelism.
- **Sessions:** signed cookies, `HttpOnly`, `SameSite=Lax`, `Secure` in production.
- **CSRF:** Flask-WTF token on every state-changing request; the SPA fetches and retries automatically.
- **Authorization:** every protected route resolves the user server-side; ownership checks on delete, profile edits and messaging.
- **Rate limits:** 20/min register, 30/min login, 100/min global.
- **CORS:** explicit origin allowlist with credentials; no wildcard.
- **Input handling:** field allowlists, length limits, type checks and parameterised Mongo queries.
- **Uploads:** extension + magic-byte validation, size caps, UUID filenames, authenticated download.
- **Errors:** generic 500 responses; stack traces and secrets stay in server logs.
- **XSS:** React escapes content; no `dangerouslySetInnerHTML`.

> For production, set a strong `SECRET_KEY`, enable `SESSION_COOKIE_SECURE`, run behind HTTPS, and move rate-limit storage to Redis.

---

## Testing and Quality

### Backend

```powershell
cd backend
.venv\Scripts\python.exe -m pytest tests/ -q
.venv\Scripts\ruff.exe check .
.venv\Scripts\ruff.exe format --check .
```

- **131 tests** across unit and integration suites.
- Unit coverage: graph, BFS, recommendations, Trie, feed heap, request queue, media validation, post repository.
- Integration coverage: app factory, configuration and route registration.

### Frontend

```powershell
cd frontend
npm run build      # tsc -b + vite build
npm run lint       # oxlint
```

The production build must pass with zero TypeScript errors.

### Manual smoke test

```powershell
cd backend
python scripts/smoke_test.py
```

---

## Troubleshooting

### `ServerSelectionTimeoutError` / `TLSV1_ALERT_INTERNAL_ERROR` with Atlas

TCP reaches Atlas but the TLS handshake is rejected. This is almost always the **IP access list**, not the driver:

1. Open MongoDB Atlas → **Network Access**.
2. Add your current public IP, or `0.0.0.0/0` for a short-lived demo.
3. Wait about a minute, then restart the backend.

Check your public IP:

```powershell
(Invoke-RestMethod -Uri "https://api.ipify.org")
```

Also confirm the cluster is not paused (M0 clusters pause after inactivity).

### Backend starts but the frontend gets CORS errors

- `CORS_ALLOWED_ORIGINS` must contain the exact frontend origin, including scheme and port.
- Restart the backend after changing `.env`.

### `400 CSRF_TOKEN_MISSING`

The SPA normally retries automatically. If it persists, confirm `GET /api/v1/auth/csrf` returns a token and that cookies are enabled.

### Uploaded images return 404

- Confirm `UPLOAD_FOLDER` exists and is writable.
- Use an absolute path on Windows, for example:
  `UPLOAD_FOLDER=C:/Users/<you>/Desktop/campusconnect/backend/uploads`
- Restart the backend after changing it.

### Port already in use

```powershell
Get-NetTCPConnection -LocalPort 5000 -State Listen
Stop-Process -Id <OwningProcess>
```

### Seeded accounts cannot log in

Re-run `python scripts/seed_all.py` from `backend/`. It resets the demo collections and recreates all 27 accounts with `CampusPass123`.

---

## Known Limitations

- Real-time updates use polling (messages and notifications), not WebSockets.
- One media attachment per post.
- No profile-photo upload; avatars are generated from initials.
- No email verification or password reset.
- Uploaded files live on local disk; production would use object storage.
- Rate-limit storage is in-memory and resets on restart.

These are deliberate scope choices for a course project, not hidden defects.

---

## Documentation

| File | Contents |
|---|---|
| [PRD.md](PRD.md) | Product requirements and scope |
| [PLAN..md](PLAN..md) | Technical architecture and implementation plan |
| [EXECUTION.md](EXECUTION.md) | Runbook, verification record and demo script |
| [QA_REFERENCE.md](QA_REFERENCE.md) | Viva questions, answers and tech-stack walkthrough |
| [CREDENTIALS.md](CREDENTIALS.md) | All 27 demo accounts |

---

## Team

Built for the Chanakya University DSA mini-project (team of up to four). Every member should be able to explain the graph, BFS, Trie, heap merge, Jaccard ranking, request state machine, authentication flow and MongoDB schema.

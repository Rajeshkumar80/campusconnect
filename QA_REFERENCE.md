# CampusConnect — DSA Mini-Project: Complete Q&A Reference

**Project:** CampusConnect — Chanakya University Student Network  
**Stack:** React + TypeScript (Vite) | Flask REST API | MongoDB (local or Atlas) | Pure-Python DSA Core  
**Team:** ≤4 members | **Deadline:** 27-Nov-2026

---

## 1. Graph Modeling

### Q1. Why are accepted connections modeled as **undirected edges** and pending requests as **directed edges**?

**Answer.**  
- **Accepted connection = mutual friendship.** If *A* is connected to *B*, then *B* is connected to *A*. This is symmetric → **undirected edge**. We store it once with a canonical ordering `(user_low, user_high)` so the adjacency list is compact and lookups are `O(1)`.  
- **Pending request = one-way intent.** *A* sent a request to *B*; *B* has not accepted. This is asymmetric → **directed edge** `sender → recipient`. The direction matters for accept/reject/cancel logic.

### Q2. How do you prevent **self-loops** and **parallel/duplicate edges**?

**Answer.**  
- **Self-loops:** Every mutating endpoint (`send`, `accept`, `reject`, `cancel`, `remove`, `message`) checks `if sender_id == recipient_id: raise ValueError("You cannot connect/message yourself")`.  
- **Parallel edges:**  
  - Connections collection has a **unique compound index** on `(user_low, user_high)`. MongoDB rejects duplicate inserts.  
  - Requests collection has a **unique compound index** on `(sender_id, recipient_id)` + status filter.  
  - Application-level guard: before inserting, we query `are_connected(a, b)` / `has_pending_request(a, b)` and return a clean error instead of relying on the index exception.

---

## 2. Adjacency List Storage & Complexities

### Q3. How are connections stored using adjacency lists?

**Answer.**  
Core MongoDB collections:

| Collection | Document Shape | Indexes |
|------------|----------------|---------|
| `connections` | `{ _id: "<low>:<high>", user_low: "<uid>", user_high: "<uid>", created_at: <ts> }` | Unique on `(user_low, user_high)`, single-field on `user_low`, `user_high` |
| `connection_requests` | `{ _id: "<req_id>", sender_id, recipient_id, status: "pending|accepted|rejected|cancelled", created_at, updated_at }` | Unique partial on `(sender_id, recipient_id)` where `status="pending"`, plus `(recipient_id, status)` and `(sender_id, status)` |

**In-memory adjacency list (built on startup):**  
```python
# dict[user_id] -> set[neighbor_id]
adj: dict[str, set[str]] = defaultdict(set)
for doc in connections.find():
    adj[doc["user_low"]].add(doc["user_high"])
    adj[doc["user_high"]].add(doc["user_low"])
```
Rebuilt in `app/services/engine.py` by `DSAEngine.initialize()` on every process start.

### Q4. Time & Space Complexities of Connection Operations

| Operation | Time | Space | Notes |
|-----------|------|-------|-------|
| **Send request** | `O(1)` avg | `O(1)` | Insert into `connection_requests`; unique index prevents dupes |
| **Accept request** | `O(1)` avg | `O(1)` | Update request status to `accepted` + insert canonical connection |
| **Reject / Cancel** | `O(1)` avg | `O(1)` | Update request status or delete |
| **Remove connection** | `O(1)` avg | `O(1)` | Delete from `connections` by canonical `_id` |
| **Are connected?** | `O(1)` | — | `connections.count_documents({_id: canonical(a,b)})` |
| **Get all connections** | `O(deg(u))` | `O(deg(u))` | Two index scans on `user_low` / `user_high` merged |
| **Memory (adj list)** | — | `O(|V| + |E|)` | `2|E|` integers in `dict[set]` |

---

## 3. Mutual Connections & BFS Degrees

### Q5. How do you find **mutual connections** between two users?

**Answer.**  
```python
def mutual_neighbors(self, user_a: str, user_b: str) -> set[str]:
    return self._adj[user_a] & self._adj[user_b]   # set intersection
```
- **Time:** `O(min(deg(a), deg(b)))` — iterate smaller set, `O(1)` membership in larger.  
- **Space:** `O(k)` for `k` mutuals.

### Q6. How does **BFS** compute 1st/2nd/3rd degree and a shortest chain?

**Answer.**  
```python
def reachable_within(graph: Graph, source: str, max_depth: int = 3) -> dict[str, int]:
    dist = {source: 0}
    q = deque([source])
    while q:
        u = q.popleft()
        if dist[u] == max_depth:
            continue
        for v in graph.neighbors(u):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist
```
- **1st degree:** direct neighbors (`dist == 1`)  
- **2nd degree:** friends-of-friends (`dist == 2`)  
- **3rd degree:** friends-of-friends-of-friends (`dist == 3`)  
- **Shortest chain:** during BFS store `parent[v] = u`; reconstruct by backtracking from target to source.  
- **Complexity:** `O(|V| + |E|)` worst-case, but capped at `max_degree` → visits only nodes within 3 hops. On campus graph (sparse, ~27 nodes) it's microseconds.

---

## 4. "People You May Know" Ranking

### Q7. Which similarity measure do you use and why?

**Answer.** The default score is the **common-neighbour count**. **Jaccard similarity** is implemented as an optional normalisation.

```
common(u, v)  = |N(u) ∩ N(v)|
jaccard(u, v) = |N(u) ∩ N(v)| / |N(u) ∪ N(v)|
```

- **Why common neighbours by default?** On a small campus graph, the raw mutual count is the most direct signal and produces a stable integer ranking.
- **Why Jaccard as an option?** It is normalised `[0,1]`, comparable across users with different degree, parameter-free (unlike Katz/PageRank), and interpretable as "the fraction of combined connections that are mutual".
- **Cost:** `O(min(deg(u), deg(v)))` for the intersection; the union size is `deg(u) + deg(v) - mutual`.

**Algorithm (Discover page):**
```python
def get_suggestions(graph, user_id, limit=20, use_jaccard=False):
    candidates = neighbours_of_neighbours(graph, user_id)
    candidates -= graph.neighbors(user_id) | {user_id}
    scored = []
    for v in candidates:
        mutual = len(graph.neighbors(user_id) & graph.neighbors(v))
        if mutual == 0:
            continue
        if use_jaccard:
            union = len(graph.neighbors(user_id) | graph.neighbors(v))
            score = mutual / union
        else:
            score = mutual
        scored.append((score, mutual, v))
    scored.sort(reverse=True)   # score, then mutual, then user ID
    return scored[:limit]
```

### Q8. Edge cases — no connections / disconnected components?

**Answer.**  
- If `deg(user) == 0` → there are no mutual candidates. Fallback: append the remaining active students (excluding self, existing connections and pending requests) with `score = 0`, `mutual_count = 0` and the explanation "New to your campus network", so the page is never empty.  
- Disconnected components: BFS naturally stops at component boundary; those users get `mutual = 0` and appear in fallback bucket.

---

## 5. Why Graph Computations Run in Python Memory

### Q9. Why not push graph algorithms, pathfinding, ranking, feed sorting to SQL/NoSQL?

**Answer.**  
| Reason | Explanation |
|--------|-------------|
| **Random access patterns** | BFS, Jaccard, heap-merge need **pointer-chasing** across adjacency lists — terrible for SQL joins / MongoDB `$lookup` pipelines. |
| **Latency** | In-memory `dict[set]` gives `O(1)` neighbour iteration; DB round-trips add milliseconds per hop. |
| **Algorithmic fidelity** | Heap merge (feed), trie (search), BFS (degrees) are **data-structure algorithms**, not declarative queries. Expressing them in SQL/MQL is awkward, slow, and unmaintainable. |
| **Deterministic reproducibility** | Unit tests (`tests/unit/test_bfs.py`, `test_feed_heap.py`, `test_recommendations.py`) run against pure Python objects — no DB required, CI is fast. |
| **Separation of concerns** | DSA engine (`app/dsa/`) has **zero imports** from Flask, MongoDB, or React. It can be tested, benchmarked, or swapped independently. |

**Only persistence crosses the boundary:** on startup `DSAEngine.initialize()` loads `connections` → adjacency list; on write, the service layer updates MongoDB **and** mutates the in-memory structure.

---

## 6. Persistence Layer — MongoDB ↔ In-Memory Sync

### Q10. How are in-memory structures rebuilt on application restart?

**Answer.**  
`app/services/engine.py` — `DSAEngine` singleton:

```python
class DSAEngine:
    def __init__(self):
        self.graph = Graph()
        self.trie = Trie()
        self.request_queue = RequestQueue()
        self._initialized = False

    def initialize(self, user_repo, connection_repo, post_repo):
        for user in user_repo.get_all_users():
            self.graph.add_user(user["user_id"])
            self.trie.insert(user["username"], user["user_id"])
            name = (user.get("profile") or {}).get("name")
            if name:
                self.trie.insert(name, user["user_id"])
        for conn in connection_repo.get_all_accepted_connections():
            self.graph.add_edge(conn["user_low"], conn["user_high"])
        self.request_queue.rebuild_from_requests(
            connection_repo.get_all_pending_requests()
        )
        self._initialized = True
```

**Called once** at Flask app factory startup via `init_engine(app)` in `app/__init__.py`.  
**On mutation** (send/accept/reject/cancel request, accept/remove connection, register user): the service layer updates MongoDB first, then calls `graph.add_edge()`, `graph.remove_edge()`, `graph.add_user()`, `trie.insert()` or the matching `request_queue` method — a dual write to MongoDB + in-memory.

**No serialization to disk** — MongoDB is the source of truth; in-memory is a derived cache rebuilt in <50 ms for 27 users.

---

## 7. Home Feed — Heap Merge

### Q11. How does the heap merge time-ordered posts from connections newest-first?

**Answer.**  
Each connection has a **descending-time post stream** (max 50 posts per author, pre-sorted by `created_at`).  
We merge `k` sorted streams using a **max-heap** on `created_at`:

```python
def merge_post_streams(streams: list[list[Post]], limit: int) -> list[Post]:
    # heap elements: (-created_at, author_idx, post_idx)
    heap = [(-s[0].created_at, i, 0) for i, s in enumerate(streams) if s]
    heapq.heapify(heap)
    merged = []
    while heap and len(merged) < limit:
        neg_ts, i, j = heapq.heappop(heap)
        merged.append(streams[i][j])
        if j + 1 < len(streams[i]):
            nxt = streams[i][j + 1]
            heapq.heappush(heap, (-nxt.created_at, i, j + 1))
    return merged
```

- **Time:** `O(limit × log k)` — `k ≤ 27`, `limit = 20` → negligible.  
- **Space:** `O(k)` for heap + `O(limit)` for output.  
- **Why not sort all posts?** `O(N log N)` where `N = k × 50`. Heap is asymptotically better and streams naturally.

---

## 8. User Lookup & Prefix Search — Trie

### Q12. How do you achieve fast user lookup and live prefix search?

| Operation | Structure | Time |
|-----------|-----------|------|
| **By user_id** | MongoDB primary-key lookup (`users.find_one({"_id": user_id})`) | Indexed, effectively `O(1)` |
| **By username** | Unique `username` index | Indexed, effectively `O(1)` |
| **Prefix search** | **Trie** over `username` + display name | `O(L + m)` where `L = prefix length`, `m = matches` |

**Trie node:**
```python
@dataclass
class TrieNode:
    children: dict[str, "TrieNode"] = field(default_factory=dict)
    user_ids: set[str] = field(default_factory=set)
```
- Insert: walk/create nodes for each char, add `user_id` to terminal node's set.  
- Search: walk prefix; if found, return union of `user_ids` in subtree (DFS).  
- **Why Trie?** Beats `LIKE 'prefix%'` (full scan) and is faster than regex. Handles 27 users instantly; scales to 100k+.

---

## 9. Password Hashing

### Q13. How are passwords hashed and why never plain text?

**Answer.**  
- **Algorithm:** **Argon2id** (via `argon2-cffi`, `argon2.PasswordHasher`) — winner of Password Hashing Competition, memory-hard, side-channel resistant.  
- **Parameters:** `time_cost=3`, `memory_cost=65536` (64 MiB), `parallelism=4`, 16-byte salt, 32-byte hash.  
- **Storage:** only the PHC string (`$argon2id$v=19$m=65536,t=3,p=4$...`) in `users.password_hash`.  
- **Verification:** `PasswordHasher().verify(stored_hash, plain)` — constant-time comparison inside the library.

**Why not plain / unsalted / fast hash?**  
| Risk | Mitigation |
|------|------------|
| DB leak → immediate credential stuffing | Argon2id makes GPU cracking infeasible |
| Rainbow tables | Per-user 16-byte salt |
| Timing attacks | `argon2-cffi` constant-time verify |
| Future hardware | Memory-hard; increase `m`, `t` via config |

---

## 10. DSA Engine ↔ UI Decoupling

### Q14. How is the core DSA engine separated from the UI?

**Answer.**  
```
├── app/dsa/                 # Pure Python — ZERO external deps
│   ├── graph.py             # Adjacency list, mutual neighbours, degree
│   ├── bfs.py               # Shortest path, degree, reachable-within
│   ├── trie.py              # Prefix search
│   ├── feed_heap.py         # Heap merge
│   ├── recommendations.py   # Common-neighbour ranking (Jaccard optional)
│   └── request_queue.py     # Connection-request state machine
├── app/services/            # Thin adapters
│   ├── engine.py            # DSAEngine (loads from Mongo, exposes DSA)
│   ├── connection_service.py
│   ├── post_service.py
│   └── social_service.py
├── app/api/                 # Flask blueprints → HTTP + JSON
└── frontend/                # React + TS — talks only to /api/v1/*
```

- **DSA layer** has **no imports** from `flask`, `pymongo`, `react`, etc.  
- **Unit tests** (`tests/unit/`) import only `app.dsa.*` — run in 0.5 s without DB.  
- **UI** consumes REST endpoints; no knowledge of trie/heap/BFS internals.

---

## 11. Optional Features — Data Structures & Algorithms

| Feature | Backing DS/Algo | Location |
|---------|----------------|----------|
| **Image/Video posts** | File on disk (`backend/uploads/`, UUID name), metadata in `posts.media`; not GridFS | `app/media.py`, `post_routes.py` |
| **Likes** | `post_likes` collection, `_id = "<post_id>:<user_id>"` (unique); `decorate_posts()` aggregates counts | `social_service.py` |
| **Comments** | `comments` collection, sorted oldest-first, capped at 200 | `social_service.py` |
| **Notifications** | In-app list derived from `post_likes`, `comments`, `connection_requests`; `notifications_seen_at` on user doc | `notification_routes.py` |
| **Direct Messages** | `messages` collection; thread = all msgs between two connected users; `read_at` for unread count | `message_routes.py` |
| **Share post** | Sends a message with `shared_post_id` (no repost model) | `social_service.share_post()` |
| **Voice notes** | Browser `MediaRecorder` → `audio/webm` (`.weba`) → uploaded as message media | `MessagesPage.tsx` |
| **Lightbox** | In-page modal (React state) — no new tab | `PostMedia.tsx` |

---

## 12. Code Walkthrough — Key Modules

### `app/dsa/graph.py`
```python
class Graph:
    def __init__(self):
        self._adj: dict[str, set[str]] = defaultdict(set)

    def add_edge(self, a: str, b: str) -> None:
        if a == b: raise ValueError("self-loop")
        self._adj[a].add(b)
        self._adj[b].add(a)

    def remove_edge(self, a: str, b: str) -> None:
        self._adj[a].discard(b)
        self._adj[b].discard(a)

    def neighbors(self, u: str) -> set[str]:
        return self._adj.get(u, set())

    def mutual(self, a: str, b: str) -> list[str]:
        return list(self._adj[a] & self._adj[b])

    def bfs_degrees(self, src: str, max_d: int = 3) -> dict[str, int]:
        # standard BFS with distance map
```
**Justification:** `dict[set]` gives `O(1)` add/remove/contains, `O(deg)` iteration, `O(min(deg))` intersection. Adjacency matrix would be `O(|V|²)` space — wasteful for sparse campus graph.

### `app/dsa/feed_heap.py`
```python
def merge_post_streams(streams: list[list[Post]], limit: int) -> list[Post]:
    heap = [(-s[0].created_at, i, 0) for i, s in enumerate(streams) if s]
    heapq.heapify(heap)
    # pop smallest (-ts) → largest ts, push next from same stream
```
**Justification:** k-way merge via heap is optimal `O(limit log k)`. Alternative `sorted(chain(*streams), key=ts, reverse=True)[:limit]` is `O(N log N)`.

### `app/dsa/trie.py`
```python
class Trie:
    def __init__(self): self.root = TrieNode()
    def insert(self, word: str, user_id: str): ...
    def search(self, prefix: str) -> set[str]: ...
```
**Justification:** Trie gives `O(L + m)` prefix search vs `O(|users| × L)` linear scan. For 27 users it's overkill but demonstrates the DSA; scales to 100k+.

### `app/dsa/recommendations.py`
```python
def _score_jaccard(graph, user_id, candidate_id) -> float:
    a = graph.neighbors(user_id)
    b = graph.neighbors(candidate_id)
    return len(a & b) / len(a | b) if (a | b) else 0.0

def get_suggestions_with_explanation(graph, user_id, limit=20, use_jaccard=False):
    # common-neighbour score by default; Jaccard when use_jaccard=True
```
**Justification:** Common-neighbour count is the simplest structural signal for a small campus graph; Jaccard is available as a parameter-free, normalised alternative. Katz/PageRank need a damping factor and power iteration, which is overkill for "people you may know".

---

## 13. Team Work Division

| Member | Primary Ownership | Verified |
|--------|-------------------|----------|
| **Member 1 (You)** | DSA core (`app/dsa/*`), `DSAEngine`, `PostService`, `SocialService`, Flask API routes, MongoDB schemas, seeding, tests | ✅ All 131 tests pass |
| **Member 2** | React frontend: `FeedPage`, `CreatePostPage`, `PostCard`, `PostMedia`, `Composer`, types, API client, Tailwind theme | ✅ Build clean, manual E2E verified |
| **Member 3** | React: `ProfilePage`, `MessagesPage`, `NotificationsPage`, `ConnectionsPage`, `DiscoverPage`, `SearchPage`, `Layout`, `AuthShell` | ✅ All pages load, interactions work |
| **Member 4** | Infra: local/Atlas MongoDB setup, `.env.example`, WSGI entry point, README/EXECUTION docs, viva prep | ✅ Runs locally, documented |

**Cross-review:** Every PR reviewed by at least one other member; `code-review` skill used.

---

## 14. AI Tools Usage & Verification

| Tool | Used For | Verification |
|------|----------|--------------|
| **Claude / OpenCode** | Scaffolding Flask blueprints, React components, Tailwind config, test stubs | Manual code review, ran tests, checked types (`tsc -b`), `ruff` |
| **GitHub Copilot** | Boilerplate imports, small helper functions | Spot-checked logic, replaced with own where wrong |
| **ChatGPT** | Argon2id parameter selection, Jaccard vs Katz trade-off discussion | Cross-referenced `argon2-cffi` docs and academic papers |

**Rule:** No AI-generated code committed without human reading, running, and understanding it. All DSA algorithms written from scratch to match course requirements.

---

## 15. Tech Stack — End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        REACT + TYPESCRIPT (Vite)                    │
│  • Pages: Feed, CreatePost, Profile, Messages, Notifications,       │
│           Connections, Discover, Search, Settings                   │
│  • Components: PostCard, PostMedia, Composer, Layout, AuthShell     │
│  • State: React hooks + Context (Auth), no Redux                    │
│  • Styling: Tailwind CSS (custom design tokens)                     │
│  • Build: `npm run build` → `dist/` (Vite dev server in development; Flask serves the API only)
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTPS /api/v1/* (cookies)
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FLASK REST API                                │
│  • Blueprints: auth, profiles, connections, posts, media,           │
│                messages, notifications, users                       │
│  • Security: Argon2id, HttpOnly/SameSite cookies, CSRF, rate-limit  │
│  • Services: PostService, ConnectionService, SocialService,         │
│              DSAEngine (DSA adapter)                                 │
│  • Runs: `python wsgi.py` (dev) or any WSGI server (production)      │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ PyMongo
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MONGODB (local or Atlas)                       │
│  Collections: users, profiles, connections, connection_requests,    │
│               posts, post_likes, comments, messages                 │
│  Indexes: unique username, unique (user_low,user_high), partial     │
│           unique pending (sender,recipient), post author/time       │
└─────────────────────────────────────────────────────────────────────┘
```

**Data flow example — Create Post:**
1. User clicks **New post** → `/create-post` page (React)  
2. Types text, attaches image → clicks **Publish**  
3. `POST /api/v1/posts` (multipart) → Flask `post_routes.create_post`  
4. `PostService.create_post()` → saves file to `backend/uploads/uuid.ext`  
5. Inserts `posts` doc with `media` metadata  
6. Returns new post → React redirects to `/`  
7. `FeedPage` reloads → `GET /api/v1/posts/feed` → `PostService.get_feed()`  
8. `PostService.get_feed()` merges connection streams via **feed_heap** → newest-first JSON  
9. React renders `PostCard` with like/comment/share, lightbox for image

**Data flow example — Discover:**
1. `GET /api/v1/connections/suggestions` → `ConnectionService.get_suggestions()`  
2. `DSAEngine` + `get_suggestions()` → **common-neighbour ranking** on the in-memory adjacency list (Jaccard optional)  
3. Returns ranked list with `mutual_count` → React renders cards with "Connect" button

---

## Appendix — Key Commands

```bash
# Backend
cd backend
.venv\Scripts\python.exe -m pytest tests/ -q      # 131 passed
.venv\Scripts\ruff.exe check .                   # clean
.venv\Scripts\python.exe -m flask --app wsgi:app run --port 5000

# Frontend
cd frontend
npm run build                                    # clean
npm run dev -- --port 5173

# Seed DB (27 users, password: CampusPass123)
cd backend
.venv\Scripts\python.exe scripts/seed_all.py
```

**Demo accounts:** `pruthvi`, `rajesh`, `sahana`, `geetha`, … (see `CREDENTIALS.md`)

---

*Generated for Chanakya University DSA Mini-Project viva — 27-Nov-2026*
# PLAN.md — CampusConnect
## Technical Architecture and Delivery Plan

**Companion documents:** `PRD.md` defines what must be built; `EXECUTION.md` defines the order and commands/workflow for building it.  
**Architecture:** React + TypeScript + Vite → Flask REST API → application services → Python DSA engine + MongoDB repository.

---

## 1. Architecture principles

1. **DSA-first core:** graph and algorithm modules must not import Flask, React or PyMongo.
2. **Persistence is not computation:** MongoDB stores durable records; Python in-memory structures perform graph, recommendation and feed algorithms.
3. **One source of business rules:** API routes call services; services call repositories and DSA modules. Do not duplicate rules in React.
4. **Test each layer independently:** core algorithms run with ordinary Python tests and no database.
5. **Secure by default:** validate inputs, authorize every operation, protect sessions and keep secrets outside source control.
6. **Incremental delivery:** mandatory features first; optional enhancements only after the core passes.
7. **Explainability:** every algorithm has a documented purpose, complexity, example and test.

## 2. Proposed repository structure

```text
campusconnect/
├── README.md
├── PRD.md
├── PLAN.md
├── EXECUTION.md
├── .gitignore
├── .env.example
├── docker-compose.yml                 # optional local MongoDB only
├── backend/
│   ├── pyproject.toml                 # or requirements.txt; choose one dependency strategy
│   ├── wsgi.py
│   ├── app/
│   │   ├── __init__.py                # Flask app factory
│   │   ├── config.py
│   │   ├── extensions.py              # PyMongo/session/CSRF/limiter setup
│   │   ├── api/
│   │   │   ├── auth_routes.py
│   │   │   ├── profile_routes.py
│   │   │   ├── user_routes.py
│   │   │   ├── connection_routes.py
│   │   │   ├── post_routes.py
│   │   │   └── health_routes.py
│   │   ├── schemas/                   # request/response validation
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── profile_service.py
│   │   │   ├── connection_service.py
│   │   │   ├── feed_service.py
│   │   │   └── search_service.py
│   │   ├── dsa/
│   │   │   ├── graph.py
│   │   │   ├── bfs.py
│   │   │   ├── recommendations.py
│   │   │   ├── trie.py
│   │   │   ├── feed_heap.py
│   │   │   └── request_queue.py
│   │   ├── repositories/
│   │   │   ├── interfaces.py
│   │   │   ├── mongo_user_repository.py
│   │   │   ├── mongo_connection_repository.py
│   │   │   └── mongo_post_repository.py
│   │   ├── security/
│   │   │   ├── decorators.py
│   │   │   ├── csrf.py
│   │   │   └── rate_limits.py
│   │   └── utils/
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── security/
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── src/
    │   ├── app/
    │   ├── components/
    │   ├── features/
    │   │   ├── auth/
    │   │   ├── profile/
    │   │   ├── connections/
    │   │   ├── discover/
    │   │   ├── feed/
    │   │   └── search/
    │   ├── lib/
    │   │   ├── api.ts
    │   │   ├── schemas.ts
    │   │   └── auth.ts
    │   ├── styles/
    │   └── tests/
    └── e2e/
```

Keep the structure understandable. Do not create empty abstraction layers just to match the tree. Add modules when a real responsibility exists.

## 3. Technology decisions

| Concern | Selection | Role / note |
|---|---|---|
| Language — backend | Python 3.12+ (or supported stable version available in lab) | DSA and API |
| API framework | Flask | Small REST API and app factory |
| Frontend | React + TypeScript + Vite | Browser UI |
| Styling | Tailwind CSS + CSS variables | Design tokens and responsive layout |
| Components | shadcn/ui (selectively) | Accessible primitives; customize visual identity |
| Animation | Framer Motion | Page and component transitions; respect reduced motion |
| Database | MongoDB + PyMongo | Durable persistence; URI supplied later |
| Password hashing | Argon2id via maintained Python package | Password hash verification |
| Validation | Pydantic or Marshmallow (choose one) | Validate API payloads consistently |
| API contract | OpenAPI / Swagger | Document request and response shapes |
| Backend tests | pytest | Unit and integration tests |
| Frontend tests | Vitest + React Testing Library | Component and utility tests |
| Browser tests | Playwright | End-to-end user journeys |
| Lint/format | Ruff (Python), ESLint + Prettier (TypeScript) | Consistent code quality |
| Version control | Git + GitHub | Source history and submission |
| Optional local services | Docker Compose | Reproducible local MongoDB if needed |

Pin dependencies and commit the chosen lockfiles. Verify compatibility before installing; do not mix multiple validation, state-management or component systems without a reason.

## 4. Layer responsibilities and data flow

```text
React pages/components
        │ HTTPS/JSON
        ▼
Flask API routes ── authentication / validation / authorization
        ▼
Application services
        ├── Python DSA engine (in-memory graph, trie, heap, BFS)
        └── Repository interfaces
                  ▼
             MongoDB
```

### Startup flow
1. Load configuration from environment.
2. Connect to MongoDB and verify readiness.
3. Create required indexes.
4. Load users, accepted connections, pending requests and relevant post metadata.
5. Build in-memory adjacency lists, user hash maps and prefix index.
6. Expose readiness only after critical initialization succeeds.

### Mutation flow
1. Authenticate and validate request.
2. Authorize actor and check current persisted state.
3. Persist the canonical state transition.
4. After successful persistence, update in-memory graph/index.
5. Return a safe response.
6. If memory update fails, mark/rebuild the affected in-memory state from persistence; do not silently leave it inconsistent.

For a multi-process deployment, each process has its own memory. This student project should initially run a single backend process for the in-memory graph. If multiple workers are later used, implement a deliberate cache invalidation/rebuild strategy or central graph service; do not assume process-local memory is shared.

## 5. DSA implementation plan

### 5.1 Graph
Represent accepted connections as:
```python
adjacency: dict[str, set[str]]
```
Maintain invariant `v in adjacency[u]` iff `u in adjacency[v]`. Include isolated users with empty neighbour sets. Never add self-edges.

Methods:
- `add_user(user_id)`
- `add_edge(user_a, user_b)`
- `remove_edge(user_a, user_b)`
- `neighbors(user_id)`
- `mutual_neighbors(user_a, user_b)`

Graph class contains no database calls. Service/repository layer coordinates persistence and graph updates.

### 5.2 BFS / degrees / shortest path
Use `collections.deque`, visited set and parent map.
- `shortest_path(source, target)` returns `[source, ..., target]` or `None`.
- `degree_of_connection(source, target)` returns edge distance or `None`.
- `reachable_within(source, max_depth=3)` returns users and distances.
- Complexity: O(V+E) worst case; adjacency-list traversal.
- Determinism: sort neighbour IDs during traversal or use stable insertion ordering; choose one and test it.

### 5.3 Suggestions
First release: common-neighbour count or Jaccard similarity.
- Candidate set: users reached through neighbours' neighbours.
- Exclude self, existing neighbours and blocked/ineligible users if such a feature exists.
- Handle pending requests consistently.
- Tie-break by normalized username or ID.
- Return score explanation, e.g. “3 mutual connections”.
- Do not expose private graph data beyond what the product allows.

### 5.4 Trie / prefix search
Trie node: `children: dict[str, TrieNode]`, `user_ids: set[str]` or terminal ID list.
- Normalize case and Unicode consistently.
- Insert/update/remove users when username or display name changes.
- Prefix search returns a bounded number of suggestions.
- Keep a simple indexed fallback for correctness tests.
- Complexity: O(L+K) to traverse prefix and emit K results, excluding sorting if sorting is required.

### 5.5 Feed heap
Load time-ordered post streams for accepted connections, then merge in Python with `heapq`.
- Heap entry includes timestamp, stable tie-breaker, author ID and stream position.
- Use descending-time semantics (e.g. negative timestamp).
- Bound page size and avoid loading unlimited posts.
- Ensure only accepted connections' posts are included.
- Complexity approximately O(P log C) for P returned posts across C streams.
- Database may fetch bounded per-author ordered records; final multi-stream merge/ranking must occur in Python.

### 5.6 Requests and notifications
Connection requests are directed records with explicit states: `pending`, `accepted`, `rejected`, `cancelled`.
Use indexed maps/queues for in-memory processing where useful, but persisted request state remains canonical. Notifications/queue are optional and must not be confused with accepted graph edges.

## 6. MongoDB model and indexes

MongoDB URI is intentionally a placeholder until supplied. Use `MONGODB_URI` and `MONGODB_DATABASE` environment variables. Never put the real URI in source files, README screenshots, frontend variables or Git history.

### Collections

**users**
```json
{
  "_id": "user_id",
  "username": "normalized_unique_username",
  "password_hash": "argon2id_hash",
  "created_at": "UTC datetime",
  "updated_at": "UTC datetime",
  "status": "active"
}
```

**profiles**
```json
{
  "_id": "user_id",
  "name": "Display Name",
  "programme": "B.Tech ...",
  "year": 3,
  "bio": "Short bio",
  "skills": ["Python", "DSA"],
  "updated_at": "UTC datetime"
}
```

**connection_requests**
```json
{
  "_id": "request_id",
  "sender_id": "user_a",
  "recipient_id": "user_b",
  "status": "pending",
  "created_at": "UTC datetime",
  "updated_at": "UTC datetime"
}
```

**connections**
```json
{
  "_id": "canonical_pair_key",
  "user_low": "lexicographically_smaller_id",
  "user_high": "larger_id",
  "created_at": "UTC datetime"
}
```

**posts**
```json
{
  "_id": "post_id",
  "author_id": "user_id",
  "text": "Project / technical idea",
  "created_at": "UTC datetime",
  "updated_at": "UTC datetime"
}
```

Optional collections only when features are implemented: `notifications`, `likes`, `comments`, `groups`, `group_members`.

### Index plan
- `users.username`: unique.
- `profiles._id`: unique (or use `user_id` unique).
- `connection_requests`: compound index on sender, recipient and status; additional recipient/status index for inbox.
- `connections`: unique canonical pair and indexes on `user_low` / `user_high`.
- `posts`: compound index on author and descending creation time.
- Optional notification index on recipient/read/created time.

Use UTC-aware timestamps. Validate ObjectId/string conversion at one boundary. Keep the schema consistent; do not mix string and ObjectId identifiers casually.

## 7. REST API contract (proposed)

Base path: `/api/v1`. All request/response bodies use JSON unless documented otherwise. Exact payload schemas should be finalized before frontend integration.

| Method | Endpoint | Purpose | Authorization |
|---|---|---|---|
| POST | `/auth/register` | Create account | Public, rate-limited |
| POST | `/auth/login` | Start session | Public, rate-limited |
| POST | `/auth/logout` | End session | Authenticated |
| GET | `/auth/me` | Current user | Authenticated |
| GET | `/users/search?q=` | Prefix search | Authenticated |
| GET | `/users/{user_id}` | Public student profile | Authenticated |
| PATCH | `/profiles/me` | Update own profile | Authenticated |
| GET | `/connections` | List own connections | Authenticated |
| POST | `/connection-requests` | Send request | Authenticated |
| GET | `/connection-requests/incoming` | Incoming pending requests | Authenticated |
| GET | `/connection-requests/outgoing` | Outgoing pending requests | Authenticated |
| POST | `/connection-requests/{id}/accept` | Accept request | Recipient only |
| POST | `/connection-requests/{id}/reject` | Reject request | Recipient only |
| POST | `/connection-requests/{id}/cancel` | Cancel request | Sender only |
| DELETE | `/connections/{user_id}` | Remove accepted edge | Either participant |
| GET | `/users/{id}/mutual-connections` | Mutual neighbours | Authenticated |
| GET | `/users/{id}/connection-degree` | Degree from current user | Authenticated |
| GET | `/users/{id}/shortest-path` | BFS shortest chain | Authenticated |
| GET | `/connections/suggestions` | Ranked suggestions | Authenticated |
| POST | `/posts` | Create text post | Authenticated |
| GET | `/posts/mine` | Own posts | Authenticated |
| DELETE | `/posts/{post_id}` | Delete own post | Owner only |
| GET | `/feed` | Home feed | Authenticated |
| GET | `/health/live` | Process liveness | Public/minimal |
| GET | `/health/ready` | Dependency readiness | Public/minimal |

### API response conventions
Success:
```json
{"data": {}, "meta": {}}
```
Error:
```json
{"error": {"code": "VALIDATION_ERROR", "message": "Please check the submitted fields."}}
```
Use correct HTTP status codes (201 create, 200 read/update, 204 delete where appropriate, 400 validation, 401 unauthenticated, 403 forbidden, 404 missing, 409 conflict, 429 rate limit, 500 generic server error). Never return stack traces or raw database exception messages.

## 8. Security architecture checklist

### Backend
- Argon2id password hashing; no plaintext or reversible password storage.
- Session cookie: HttpOnly, Secure in HTTPS, SameSite policy; session expiry and rotation after login.
- CSRF token for state-changing cookie-authenticated requests.
- Login and sensitive endpoint rate limits.
- Server-side validation and allowlisted fields.
- Server-side ownership/role checks for every protected operation.
- NoSQL injection prevention: never pass arbitrary client JSON directly into MongoDB filters or updates.
- Safe text output; no unsafe HTML rendering.
- CORS allowlist, not wildcard with credentials.
- Request size limits and pagination caps.
- Production-safe errors and redacted logs.
- Secure headers and HTTPS deployment.

### Frontend
- Keep tokens/secrets out of localStorage where possible; use HttpOnly cookie session design.
- Do not rely on client-side route guards as authorization.
- Render text as text; avoid `dangerouslySetInnerHTML`.
- Validate for usability, but trust only backend validation.
- Avoid leaking sensitive API responses into logs or analytics.
- Use safe dependency versions and lockfile.
- CSP must be compatible with actual build; avoid unsafe inline script allowances where possible.
- Respect reduced motion and provide accessible focus states.

### MongoDB and environment
- Least-privilege database user.
- Network allowlist/private networking where supported.
- URI in backend-only environment variable.
- `.env` ignored by Git; `.env.example` contains placeholders.
- No database URI in Vite `VITE_*` variables.
- Indexes and input validation.
- Backups and restore procedure appropriate to hosting.

### Security verification cases
1. User A cannot edit User B's profile.
2. User A cannot delete User B's post.
3. Non-recipient cannot accept/reject a request.
4. Non-sender cannot cancel a request.
5. Unauthenticated calls to protected APIs fail.
6. Logout invalidates session.
7. Script payload is displayed as harmless text.
8. Mongo operator payloads are rejected or treated as plain strings.
9. CSRF attempt fails for cookie-authenticated mutation.
10. Repeated login/search/request calls are throttled.
11. Oversized request is rejected.
12. Errors do not disclose secrets or stack traces.

## 9. UI design system plan

### Visual concept
A premium campus network with a distinct visual identity, not a clone of LinkedIn. Suggested direction: “modern academic studio” — ink/navy typography, warm neutral surfaces, one vivid blue/indigo accent, subtle gradients and restrained glass-like layers only where contrast remains strong.

### Design tokens
Define CSS variables for:
- Background, surface, elevated surface, text, muted text, border, primary, accent, success, warning and danger.
- Font families and type scale.
- Spacing scale (4/8/12/16/24/32/48).
- Radius scale and shadow levels.
- Focus ring and motion duration/easing.

### Screen layout
- Desktop: compact left navigation, central feed/content column, contextual right rail.
- Tablet: collapsible navigation and two-column content where practical.
- Mobile: bottom navigation or compact top navigation; one-column feed.
- Consistent page header, breadcrumbs only where useful, clear empty states.

### Motion rules
- Framer Motion for short transitions and purposeful feedback.
- Use transform/opacity rather than expensive layout animation where possible.
- Respect `prefers-reduced-motion`.
- Avoid parallax, constant floating objects, excessive blur and animation on every element.
- Do not delay critical actions for animation.

### Accessibility
- Semantic landmarks and headings.
- Keyboard-operable menus/dialogs.
- Visible focus and accessible names.
- Color contrast checked against WCAG AA targets.
- Error messages associated with fields.
- Reduced-motion support.
- Do not encode status by color alone.

## 10. Delivery milestones

| Milestone | Scope | Exit gate |
|---|---|---|
| M0 | Requirements, repo, environment, design decisions | PRD and architecture agreed |
| M1 | Pure Python DSA engine | Unit tests pass; no Flask/DB dependency in DSA |
| M2 | Flask API using repository abstraction/test adapter | API contract and integration tests pass |
| M3 | Backend security baseline | Auth, authorization, CSRF/session and validation tests pass |
| M4 | React UI shell and mandatory screens | Main screens work against API contract |
| M5 | Frontend hardening and accessibility | XSS-safe rendering, reduced motion, keyboard and responsive checks |
| M6 | MongoDB repository and persistence | Restart/rebuild tests pass; indexes verified |
| M7 | Full integration with 4–5 synthetic users | All end-to-end and DSA tests pass |
| M8 | Optional enhancements and polish | Only after mandatory exit gates |
| M9 | Report, demo, GitHub cleanup and viva | Clean-clone setup and demonstration succeed |

**Important sequencing note:** The requested execution order develops and verifies the backend first using repository interfaces and a test/in-memory adapter. MongoDB is integrated after the frontend foundation, as requested, but its schema and repository contracts are designed earlier. This avoids writing algorithm code that depends on MongoDB and keeps the project testable before the connection URI is available.

## 11. Four-to-five-user demo dataset

Use synthetic accounts, for example:
- Asha (`asha_demo`)
- Dev (`dev_demo`)
- Mira (`mira_demo`)
- Kiran (`kiran_demo`)
- Noor (`noor_demo`)

Suggested accepted graph:
`Asha—Dev`, `Asha—Mira`, `Dev—Kiran`, `Mira—Kiran`, `Kiran—Noor`.

Demo scenarios:
- Asha and Dev are first-degree.
- Asha and Kiran are second-degree.
- Asha and Noor are third-degree.
- Show a shortest chain and mutual connections.
- Add a disconnected synthetic account only in algorithm unit tests if needed; keep the requested demo to 4–5 accounts.
- Create pending requests in both directions in a controlled test.
- Publish posts from connected users and verify newest-first feed.
- Verify no post from a non-connection appears.

## 12. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Scope creep from optional features | Complete mandatory requirements before enhancements |
| Graph and DB become inconsistent | Persist first, update memory after success; rebuild on startup; add consistency tests |
| MongoDB URI arrives late | Build against repository interface and test adapter; integrate URI only in backend environment |
| Multi-process memory divergence | Run one backend process for demo; document scaling limitation |
| Security added too late | Security gates after backend and frontend; test throughout |
| UI polish consumes DSA time | Freeze core acceptance criteria and algorithm tests first |
| Students cannot explain generated code | Review, comment and individually explain each module |
| Feed loads too much data | Bounded pagination and per-author limited streams |
| Duplicate requests/races | Unique indexes, state checks, idempotent service logic |

## 13. Submission checklist

- [ ] All mandatory requirements mapped to working features.
- [ ] DSA engine independent from Flask and MongoDB.
- [ ] Adjacency-list graph and BFS demonstrated.
- [ ] Prefix search and heap-based feed merge demonstrated.
- [ ] MongoDB persistence and indexes work.
- [ ] Passwords are hashed.
- [ ] Authorization tests pass.
- [ ] 4–5 synthetic users tested.
- [ ] Responsive UI and reduced motion checked.
- [ ] README and `.env.example` are complete.
- [ ] No real credentials or secrets committed.
- [ ] GitHub repository link included in report.
- [ ] Report uses university template and is not a code dump.
- [ ] Each team member can explain the algorithms and security decisions.

# PRD.md — CampusConnect
## Product Requirements Document

**Project type:** University DSA mini-project  
**Institutional basis:** Chanakya University, School of Engineering, III Semester B.Tech, Formative Assessment: Mini Project — Data Structures and Algorithms (2026–27)  
**Working product name:** CampusConnect (renameable)  
**Status:** Baseline specification  
**Primary implementation:** React + TypeScript frontend, Python Flask backend, MongoDB persistence  
**Team size:** Up to four students; every student must understand the complete system.

---

## 1. Executive summary

CampusConnect is a student networking web application for students of Chanakya University. It enables students to create profiles, publish project and technical-idea posts, discover other students, send and manage connection requests, view mutual connections, and understand how they are connected through a graph.

The application is inspired by professional and social networking products, but its defining academic purpose is to demonstrate correct, explainable use of Data Structures and Algorithms (DSA). The interface must call a Python backend whose core graph and other algorithmic operations run on in-memory data structures. MongoDB is used for durable storage, not as a substitute for the required algorithms.

The project is a responsive website. The university brief permits Flask, Streamlit, React or similar interfaces and states that a console application is the minimum acceptable interface. It does not require an Android or iOS APK.

## 2. Source requirements and scope boundary

The university brief specifies the following assessment distribution:

| Assessment component | Marks |
|---|---:|
| Core Engine and DSA Usage | 30 |
| Implementation | 20 |
| Report | 10 |
| Understanding of Project and Viva | 40 |
| **Total** | **100** |

The brief says:
- Teams may contain up to four members, but evaluation is individual.
- AI tools may be used to build the user interface, but students are answerable for every submitted line; code they cannot explain will not earn marks.
- Submit a brief design description, meaningful code comments, the standard report template, and one report copy per team with the GitHub repository link.
- The report is not intended to be a pasted copy of the codebase.
- The stated submission date is 27-11-2026; maximum marks are 100 and total duration is three weeks. Confirm any changes with the course instructor.

### 2.1 Mandatory requirements from the brief

**Accounts**
1. Sign up with a unique username and password; log in and log out.
2. Store passwords only in hashed form, never as plain text.
3. Every user has a viewable profile containing name, programme, year, short bio and skills.

**Connections**
1. Send, accept, reject and cancel connection requests; remove an existing connection.
2. View your connections and mutual connections shared with another user.
3. Show “people you may know”, ranked by a chosen measure.
4. Show degree of connection (1st, 2nd, 3rd) and one shortest chain of connections between users.
5. Store the network using adjacency lists.

**Posts and feed**
1. Create text posts about projects or technical ideas.
2. View and delete your own posts.
3. Show a home feed of posts from connections, newest first.

**Search**
1. Search users by name or username.
2. Provide suggestions as the user types (prefix search).

**Persistence**
1. All data must survive an application restart.
2. MongoDB is selected for this implementation (the brief lists SQLite, JSON files or MongoDB as possible storage options).
3. Storage keeps the data. Graph computations (suggestions, degrees, paths, feed) must run in Python on in-memory data structures, not through database queries.

**Interface**
1. Build a user interface with Flask, Streamlit, React or similar. React is selected.
2. Keep the core engine separate from the interface so a console or web interface can call the same functions.
3. If React is used, expose the core through a small REST API in Flask or FastAPI. Flask is selected.

### 2.2 Optional enhancements from the brief

These are optional, but should be attempted only after all mandatory requirements are correct:
- Image posts in addition to text posts.
- Likes and comments on posts, including replies to comments.
- Notifications for connection requests, likes and comments.
- Trending posts among connections.
- Groups or communities of closely connected students.

Each enhancement must be backed by a suitable data structure. Do not let optional work compromise the mandatory features or the DSA demonstration.

### 2.3 Suggested DSA examples from the brief

The brief gives these examples (not mandatory prescriptions):
- Network as a graph using adjacency lists; degree and shortest chain using BFS.
- Pending requests and notifications as queues.
- Home feed by merging connections’ time-ordered posts using a heap.
- User lookup using a hash table; name search using a trie.
- Undo and back navigation using a stack.
- People-you-may-know ranking using Jaccard similarity (overlap of neighbours) or Katz-style scoring (number of paths between users, weighted by length).

## 3. Product goals

1. Deliver every mandatory workflow in the university brief.
2. Make the DSA engine visible, testable and explainable.
3. Maintain a clean separation between UI, API, application services, DSA engine and persistence.
4. Provide a responsive, accessible, polished student-networking experience.
5. Protect accounts, profile data, posts and API endpoints using sensible security controls.
6. Make the application reproducible on another student's machine through documented setup instructions.
7. Support a controlled demo with four to five test accounts.

### 3.1 Non-goals

- Native Android/iOS application or APK.
- Production-scale public social network.
- Real-time chat, video calls or payment processing.
- Scraping student information from university systems.
- Using MongoDB aggregation or database graph queries to perform the assessed graph algorithms.
- Claiming production security certification or penetration-test assurance without evidence.

## 4. Users and permissions

### Student (primary user)
- Register, log in and log out.
- View and edit their own profile.
- View other students' profiles.
- Search students and use prefix suggestions.
- Manage connection requests and accepted connections.
- View mutual connections, connection degree and shortest path.
- Create, view and delete their own text posts.
- View the feed from accepted connections.
- Use optional enhancements if implemented.

### Administrator / demo operator (limited operational role)
An administrator is not required by the brief. For the mini-project, operational access should be limited to database setup, test-data seeding, log review and moderation support. Do not add an administrator role unless it is implemented with explicit authorization checks and documented.

## 5. Core user journeys

### 5.1 Registration and login
1. Student opens registration.
2. Enters unique username, password and required profile fields.
3. Backend validates input and username uniqueness.
4. Backend hashes the password using Argon2id and stores only the hash.
5. Student logs in; backend verifies the hash and establishes a protected session.
6. Student can log out and the session becomes invalid.

### 5.2 Profile
1. Student views their own profile.
2. Student edits name, programme, year, short bio and skills.
3. Other authenticated students can view the public student profile.
4. A student cannot edit another student's profile.

### 5.3 Connection lifecycle
1. Student A sends a request to Student B.
2. Request is stored as pending and represented as a directed sender-to-recipient relationship.
3. Student B accepts or rejects it; Student A may cancel it before response.
4. On acceptance, create one undirected accepted connection in the graph.
5. Either connected user can remove the accepted connection.
6. Prevent self-connections, duplicate pending requests, duplicate accepted edges and invalid state transitions.

### 5.4 Network exploration
1. Student opens their connections list.
2. Student selects another user to view mutual connections.
3. Application computes connection degree and one shortest chain using BFS.
4. “People you may know” excludes self, already-connected users and users with a pending request where appropriate; candidates are ranked using a documented score.

### 5.5 Posts and feed
1. Student creates a text post about a project or technical idea.
2. Student can see and delete their own posts.
3. Home feed contains posts authored by accepted connections, newest first.
4. Feed computation occurs in Python using in-memory data structures; database reads may load the relevant records, but ranking/merging is performed by the application.

### 5.6 Search
1. Student enters a name or username prefix.
2. Backend returns matching users with a bounded result count.
3. Suggestions update as the prefix changes.
4. Search must be case-normalized consistently and must not expose password hashes or private account data.

## 6. Functional requirements and acceptance criteria

| ID | Requirement | Acceptance evidence |
|---|---|---|
| FR-01 | Unique username registration | Duplicate username is rejected; valid user persists |
| FR-02 | Secure login/logout | Correct password succeeds; incorrect password fails; logout invalidates session |
| FR-03 | Hashed password storage | Database contains a password hash, never the submitted password |
| FR-04 | Student profile | Required fields can be created, viewed and edited by owner |
| FR-05 | Send request | Valid request becomes pending |
| FR-06 | Accept/reject/cancel | Only valid actor and state can perform each transition |
| FR-07 | Remove connection | Edge is removed from both adjacency directions and persistence |
| FR-08 | Connections list | Accepted neighbours are returned |
| FR-09 | Mutual connections | Intersection of two users' neighbour sets is correct |
| FR-10 | People-you-may-know | Excludes self and existing connections; ranking is deterministic and explained |
| FR-11 | Degree of connection | 1st/2nd/3rd degree is derived from shortest graph distance |
| FR-12 | Shortest chain | BFS returns a shortest path or a clear no-path result |
| FR-13 | Adjacency-list graph | Accepted network is represented in Python adjacency lists |
| FR-14 | Create text post | Authenticated user can create a validated post |
| FR-15 | Delete own post | Owner can delete; another user cannot |
| FR-16 | Home feed | Only accepted connections' posts; newest first |
| FR-17 | Prefix search | Name and username prefix suggestions work |
| FR-18 | Persistence | Users, profiles, accepted connections, requests and posts survive restart |
| FR-19 | Separation of concerns | DSA/core functions can be tested without React or Flask request context |
| FR-20 | React interface | Responsive web UI calls Flask REST API |

**Degree semantics:** distance 1 = first-degree connection; distance 2 = second-degree; distance 3 = third-degree. Distance 0 is the signed-in user. Users farther away should be labelled “3+” or “Beyond 3rd”, not incorrectly labelled third-degree. No path should be reported as “Not connected through the current network”.

## 7. DSA and algorithm requirements

The following is the proposed implementation mapping. Complexity assumes an adjacency-list graph with `V` users and `E` accepted undirected connections.

| Feature | Data structure / algorithm | Expected complexity | Why it is used |
|---|---|---|---|
| Student network | `dict[user_id, set[neighbour_id]]` adjacency list | Space O(V+E) | Efficient sparse graph representation |
| Connection request lookup | Hash map keyed by request ID or `(sender, recipient)` | Average O(1) lookup | Prevent duplicates and locate request state |
| Mutual connections | Set intersection | O(min(deg(u), deg(v))) average | Find common neighbours |
| Shortest chain | BFS + queue + parent map | O(V+E) | Shortest path in an unweighted graph |
| Connection degree | BFS limited to depth 3 | O(V+E), bounded traversal | Determine first/second/third-degree reachability |
| Suggestions | Common-neighbour count / Jaccard score | Candidate-dependent; document implementation | Rank users with shared network |
| Prefix suggestions | Trie (or a clearly documented prefix index) | O(L+K) after trie traversal, where L is prefix length and K results emitted | Efficient prefix lookup |
| User lookup | Python dictionary/hash map | Average O(1) | Direct user-ID and normalized username lookup |
| Home feed merge | Max-heap / `heapq` over per-author time-ordered posts | O(P log C) for P emitted posts from C connection streams | Merge newest-first streams |
| Pending requests | Queue-like ordering or indexed request collection | O(1) enqueue; lookup depends on index | Process pending work in order |
| Notifications (optional) | Queue / deque | O(1) append/pop at ends | Ordered notification processing |
| Undo/back (optional) | Stack | O(1) push/pop | Last-in-first-out history |
| Likes/comments (optional) | Sets/maps and indexed collections | Depends on operation | Avoid duplicate likes and associate comments |
| Groups (optional) | Group membership sets; optionally graph | Set-operation dependent | Represent communities |

### 7.1 Algorithm rules
- The accepted connection graph is undirected and contains no self-edges or duplicate edges.
- A pending request is a directed stateful request, not an accepted graph edge.
- Accepting a request inserts the edge in both adjacency sets.
- Removing a connection removes both directions.
- Rejecting or cancelling a request must not create an accepted edge.
- Rebuild the in-memory graph and indexes from MongoDB at application startup, and update them through a controlled service after successful persistence operations.
- Do not use MongoDB graph lookup, aggregation pipelines or database queries as a replacement for BFS, mutual-neighbour computation, suggestion ranking or feed merging.
- Document tie-breaking rules so algorithm output is repeatable in tests and viva.

### 7.2 Suggested people-you-may-know scoring
Start with a simple, explainable common-neighbour score:
`score(u, v) = |N(u) ∩ N(v)|`.
An optional normalized Jaccard score is:
`J(u,v) = |N(u) ∩ N(v)| / |N(u) ∪ N(v)|`, with zero when the union is empty.
Rank by descending score, then stable username/user ID order. Exclude the current user, existing connections and unsuitable pending-request candidates. Explain the chosen measure in the UI/report and viva. Katz scoring is an optional advanced extension, not required for the first implementation.

## 8. Data and persistence requirements

MongoDB is the selected persistent store. The actual MongoDB connection URI will be supplied later by the project owner and must be provided through an environment variable, never committed to Git.

Proposed collections:
- `users`: `_id`, normalized `username`, `password_hash`, created/updated timestamps, account status.
- `profiles`: `user_id`, name, programme, year, bio, skills, updated timestamp.
- `connection_requests`: sender ID, recipient ID, status, created/updated timestamps.
- `connections`: canonical pair of user IDs and created timestamp; enforce one record per pair.
- `posts`: author ID, text, created/updated timestamps, optional media metadata only if image posts are implemented.
- `notifications`: recipient, actor, type, reference, read status and timestamp (optional enhancement).
- `comments` / `likes` / `groups`: only if corresponding enhancements are implemented.

Use unique indexes for normalized usernames and canonical connection pairs; indexes for request recipient/status, post author/time and feed retrieval fields. Validate IDs and document shapes at the service boundary. Never store raw passwords, session secrets or MongoDB credentials in source control.

**Consistency:** Persist a state transition first, then update the in-memory graph/indexes only after the database operation succeeds. For operations spanning multiple documents, use a MongoDB transaction only if the selected MongoDB deployment supports it; otherwise design an idempotent, recoverable operation and document the limitation. Rebuild in-memory state from persisted canonical records on restart.

## 9. API requirements

Use versioned JSON REST endpoints under `/api/v1`. The detailed endpoint contract belongs in `PLAN.md`.

Minimum API groups:
- Authentication: register, login, logout, current session.
- Profiles: get profile, update own profile.
- Users/search: prefix search, user details.
- Connections: list, send request, incoming/outgoing requests, accept, reject, cancel, remove, mutual connections, suggestions, degree and shortest path.
- Posts: create, list own posts, delete own post, home feed.
- Health: liveness/readiness checks that do not reveal secrets.

All endpoints must validate input, enforce authorization, return consistent error shapes and avoid leaking internal stack traces.

## 10. UI/UX requirements

### 10.1 Visual direction
Create a distinctive, professional campus-networking product: editorial typography, restrained gradients, clear hierarchy, high-quality spacing, crisp cards, subtle depth and purposeful motion. The interface should feel polished rather than overloaded. A “premium” look must not compromise readability, performance, accessibility or academic clarity.

Suggested theme:
- Dark navy/ink foundation with a light neutral content surface, or a consistent light theme with deep navy typography.
- One primary accent (electric blue/indigo) and one restrained secondary accent.
- Consistent design tokens for spacing, radii, shadows, typography and focus states.
- Use CSS variables/design tokens rather than scattered one-off values.

### 10.2 Main screens
1. Sign up / sign in.
2. Onboarding and profile completion.
3. Home dashboard and connection feed.
4. Student profile.
5. Connections list and mutual connections.
6. Connection requests (incoming/outgoing).
7. Discover / people-you-may-know.
8. Network explorer showing degree and shortest chain.
9. Student search with prefix suggestions.
10. Create post and own-post management.
11. Notifications only if the optional feature is implemented.
12. Accessible error, empty, loading and success states.

### 10.3 Motion and interaction
- Use Framer Motion for restrained page transitions, list entrance, modal and menu transitions, and feedback.
- Respect `prefers-reduced-motion`; provide reduced or disabled motion.
- Avoid animation that delays navigation, hides information, causes layout shifts or distracts from content.
- Use skeletons only while loading; never show fake loading for decoration.
- Support keyboard navigation, visible focus, semantic HTML, sufficient contrast and accessible labels.
- Provide responsive layouts for mobile browser, tablet and desktop.

## 11. Security and privacy requirements

Security is part of the implementation, not a final cosmetic phase. Use a defense-in-depth approach.

### Authentication and sessions
- Hash passwords with Argon2id using a maintained library and safe parameters.
- Never log or return passwords, hashes, session tokens or secrets.
- Prefer secure, HttpOnly, SameSite cookies for browser sessions; if using cookie authentication, implement CSRF protection on state-changing requests.
- Set `Secure` cookies in HTTPS environments; configure session expiry and logout invalidation.
- Apply login throttling and generic authentication errors to reduce brute-force and account enumeration.
- Use strong, random application secrets from environment variables.

### Authorization
- Enforce authorization in Flask services/routes, not merely by hiding UI buttons.
- A user may edit only their own profile and delete only their own posts.
- Only the request recipient may accept/reject; only the sender may cancel; only a participant may remove a connection.
- Validate ownership and relationship state on every request.

### Input, API and browser security
- Validate types, lengths, formats, enumerations and identifiers on the server.
- Use parameterized/driver-supported MongoDB operations; never construct raw query operators from untrusted user JSON.
- Prevent NoSQL injection by allowlisting accepted fields and rejecting unexpected operator-shaped input.
- Escape/render user text safely; do not inject user content as raw HTML. If rich text is ever introduced, use a vetted sanitizer.
- Configure strict CORS allowlists for the actual frontend origin; do not combine wildcard origins with credentials.
- Use CSRF protection when cookie-based authentication is used.
- Apply rate limits to login, registration, search, requests and post creation.
- Set security headers: Content-Security-Policy appropriate to the build, X-Content-Type-Options, Referrer-Policy, frame protection via CSP `frame-ancestors`, and a suitable Permissions-Policy.
- Use HTTPS in deployment.
- Limit request body size and post/profile field lengths.
- Return generic production errors; keep detailed diagnostics in protected server logs.
- Avoid exposing stack traces, database errors, internal IDs unnecessarily or secrets in frontend bundles.

### Infrastructure and operations
- Keep `.env` out of Git; commit only `.env.example` with placeholder values.
- Restrict MongoDB network access and database user privileges to the minimum required.
- Never use an administrator/root database account in the application.
- Keep dependencies pinned/locked and review known vulnerabilities.
- Do not enable debug mode in production.
- Back up persistent data and test restoration if deployment requires it.
- Collect minimal logs; never log passwords, cookies, tokens or full sensitive request bodies.

### Threats to test
- Broken access control / IDOR.
- NoSQL injection.
- Stored and reflected XSS.
- CSRF (where cookie sessions are used).
- Brute force and credential stuffing.
- Session fixation or reuse after logout.
- CORS misconfiguration.
- Excessive request/body sizes and resource exhaustion.
- Duplicate/racing connection requests.
- Information leakage through errors, logs or search.
- Insecure secrets and database permissions.

This is a project security baseline, not a claim that all vulnerabilities can be eliminated. Record findings, fixes and residual risks in the final report.

## 12. Non-functional requirements

| Area | Requirement |
|---|---|
| Correctness | All mandatory acceptance tests pass |
| Explainability | Each DSA feature has an explanation, complexity and test |
| Maintainability | Layered modules, type hints, meaningful comments and clear naming |
| Reliability | Persistent records survive restart; errors do not corrupt graph state |
| Performance | Avoid unnecessary full graph traversal; bound search/feed results |
| Accessibility | Keyboard-operable controls, semantic labels, visible focus, reduced motion |
| Responsiveness | Usable on mobile, tablet and desktop browsers |
| Security | Server-side validation, authorization, safe sessions and secrets management |
| Observability | Health endpoints and useful redacted logs |
| Reproducibility | Documented local setup, seed script and test commands |

## 13. Testing and quality gates

Test with at least four to five distinct student accounts. Include connected and disconnected users, pending requests, mutual connections, posts and invalid actions.

Required test layers:
- Unit tests for graph, BFS, suggestions, trie/prefix search, heap feed merge and request-state transitions.
- API integration tests for authentication, permissions, validation and persistence.
- Frontend component tests for forms, loading/error/empty states and protected actions.
- End-to-end tests for complete student journeys.
- Security tests for IDOR, NoSQL injection payloads, XSS payload handling, CSRF (if applicable), rate limiting and session invalidation.
- Restart test: stop and restart the app; confirm users, connections, requests and posts are restored.
- Concurrency/duplicate test: submit duplicate connection requests and verify only one valid state exists.

Never use real student credentials or personal data in test fixtures. Use synthetic accounts.

## 14. Deliverables

1. Working responsive web application.
2. Python DSA/core engine independent of the UI.
3. Flask REST API.
4. MongoDB persistence and indexes.
5. React frontend.
6. Unit, integration and end-to-end tests.
7. `.env.example` with placeholders only.
8. README with setup, run, test and architecture instructions.
9. Architecture diagram and API documentation.
10. Brief design description, meaningful code comments and GitHub repository link.
11. University-format project report; do not paste the entire codebase into the report.
12. Viva notes explaining each DSA choice, operation and complexity.

## 15. Definition of done

The project is ready for submission only when:
- Every mandatory requirement in Section 2.1 is implemented and demonstrated.
- Graph computations are performed in Python on in-memory structures.
- The adjacency-list graph is correct after request acceptance/removal and after restart.
- All data persists in MongoDB.
- Authorization and security tests pass.
- Four to five synthetic users can complete the main workflows.
- The interface is responsive and accessible, with reduced-motion support.
- The team can explain every important module, algorithm, API and security decision.
- Setup, test and demonstration instructions work from a clean clone.

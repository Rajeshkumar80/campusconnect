# EXECUTION.md — CampusConnect
## Step-by-step Implementation and Verification Runbook

This is the operational sequence. Follow it in order and do not skip an exit gate. The MongoDB URI will be added later through a backend environment variable; never paste it into source code, frontend configuration, screenshots or Git.

**Companion documents:** `PRD.md` = requirements; `PLAN.md` = architecture and contracts; this file = execution order.

---

## 0. Rules before coding

1. Read `PRD.md` and `PLAN.md` first.
2. Keep mandatory requirements ahead of optional enhancements.
3. Build the DSA engine as pure Python modules. No Flask imports, database calls or frontend code inside `backend/app/dsa/`.
4. Every feature needs tests and a short explanation of its data structure/algorithm.
5. Use synthetic demo data only.
6. Commit small, meaningful Git changes.
7. Never commit `.env`, database credentials, password samples or session secrets.
8. Do not claim security is complete merely because a security library is installed.

## 1. Initial machine and repository setup

### 1.1 Install/check prerequisites
- Python 3.12+ (or the stable version supported by the lab environment).
- Node.js LTS and npm.
- Git.
- A code editor.
- MongoDB connection details later; local MongoDB via Docker is optional.

Verify:
```bash
python --version
node --version
npm --version
git --version
```

### 1.2 Create repository
```bash
mkdir campusconnect
cd campusconnect
git init
mkdir backend frontend
```

Create `.gitignore` before secrets or virtual environments:
```gitignore
.env
.env.*
!.env.example
.venv/
venv/
__pycache__/
.pytest_cache/
.ruff_cache/
.coverage
htmlcov/
node_modules/
dist/
build/
.DS_Store
*.log
```

Create `.env.example` with placeholders only:
```dotenv
FLASK_ENV=development
FLASK_DEBUG=false
SECRET_KEY=replace-with-a-long-random-secret
MONGODB_URI=mongodb://placeholder-do-not-use
MONGODB_DATABASE=campusconnect
FRONTEND_ORIGIN=http://localhost:5173
SESSION_COOKIE_SECURE=false
```
Do not use the placeholder as a real database connection. Copy it to `.env` only when configuring a local environment.

Create the three project documents and README in the repository. Commit:

git url https://github.com/Rajeshkumar80/campusconnect.git
```bash
git add .gitignore .env.example README.md PRD.md PLAN.md EXECUTION.md
git commit -m "docs: define CampusConnect requirements and implementation plan"
```

## 2. Backend first — build the DSA core without Flask or MongoDB

### 2.1 Create Python environment
```bash
cd backend
python -m venv .venv
```
Activate it:
- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Windows CMD: `.venv\Scripts\activate.bat`
- macOS/Linux: `source .venv/bin/activate`

Install the initial development dependencies selected in `PLAN.md`:
```bash
python -m pip install --upgrade pip
pip install flask pytest ruff
```
Add packages only when their responsibility is introduced (Argon2 library, validation library, PyMongo, CSRF/session and rate-limit libraries). Pin and lock the final dependencies before submission.

### 2.2 Implement in this order

**A. `dsa/graph.py`**
- Implement adjacency-list graph using `dict[str, set[str]]`.
- Add/remove user and edge; get neighbours; get mutual neighbours.
- Enforce no self-edge, no duplicate edge and undirected symmetry.
- Write tests for isolated users, normal edges, duplicate edges, self-edge rejection and edge removal.

**B. `dsa/bfs.py`**
- Implement BFS using `collections.deque`.
- Track visited nodes, distance and parent.
- Return one shortest path or `None`.
- Implement degree classification and depth-limited reachability.
- Test direct, two-hop, three-hop, longer, same-user and disconnected cases.

**C. `dsa/recommendations.py`**
- Generate candidates through neighbours-of-neighbours.
- Exclude self and existing connections.
- Implement common-neighbour count first; optionally Jaccard after baseline works.
- Stable tie-break and explain score.
- Test empty graph, ties and exclusion rules.

**D. `dsa/trie.py`**
- Implement insert, prefix search and remove/update if profile changes require it.
- Normalize case consistently.
- Return bounded, stable results.
- Test empty prefix policy, case, partial prefix, no match and duplicate names.

**E. `dsa/feed_heap.py`**
- Implement a heap merge over already time-ordered per-author post streams.
- Return newest-first posts with stable tie-breaks.
- Test equal timestamps, empty streams, pagination boundary and no unrelated author stream.

**F. `dsa/request_queue.py` or request-state module**
- Model pending requests and legal state transitions.
- Do not represent pending requests as graph edges.
- Test send, accept, reject, cancel, duplicate, self-request and invalid actor/state.

### 2.3 Run core checks
```bash
pytest -q
ruff check .
```
Add type checking if selected. Do not proceed until core tests pass.

**Exit gate A:** DSA functions work in isolation, have complexity notes, and do not import Flask, PyMongo or frontend modules.

## 3. Flask backend and API using repository interfaces

### 3.1 Add Flask app factory
Implement:
- `create_app(config)` for testable app creation.
- Separate development/test/production configuration.
- Blueprints for auth, profiles, users, connections, posts and health.
- Central error handlers and JSON response format.
- Request ID and redacted structured logging if time permits.

Do not put all business logic in route handlers.

### 3.2 Repository abstraction and test adapter
Define repository interfaces for users, profiles, connection requests, accepted connections and posts. For this phase, implement a lightweight in-memory/fake repository for API tests. It is a test adapter, not the final persistence layer.

Services should:
1. Validate business state.
2. Call repository methods.
3. Update the in-memory DSA engine only after a successful state change.
4. Return DTOs that never include password hashes or secrets.

### 3.3 Implement API groups in this order
1. Health and error response format.
2. Register/login/logout/current user (initial functional implementation; security hardening follows in Section 4).
3. Profile read/update.
4. User prefix search.
5. Connection request lifecycle.
6. Accepted connections list/removal.
7. Mutual connections, suggestions, degree and shortest path.
8. Create/list/delete own posts.
9. Home feed.

Use the endpoint contract in `PLAN.md`. Validate all incoming payloads. Enforce ownership and actor rules in services, not only in React.

### 3.4 API verification
Use pytest Flask test client or an API client:
- Valid and invalid payloads.
- Correct status codes.
- Missing/invalid IDs.
- Unauthorized and forbidden actions.
- Connection lifecycle and graph consistency.
- Feed contains only accepted connections' posts and is newest-first.
- Prefix search returns only intended public fields.

**Exit gate B:** Every mandatory backend workflow works with the test repository. DSA tests still pass. API routes do not contain algorithm implementations.

## 4. Backend security hardening and verification

Do this before connecting a public frontend.

### 4.1 Authentication and session
- Integrate Argon2id password hashing using a maintained package.
- Hash before persistence; verify on login.
- Never store or log plaintext passwords.
- Use a secure session design. Preferred browser approach: server-managed session in an HttpOnly cookie with SameSite policy; Secure in HTTPS deployments.
- Rotate session on login and invalidate it on logout.
- Set idle/absolute expiry appropriate to the demo.
- Use CSRF tokens for state-changing cookie-authenticated requests.

If choosing JWT instead, document why, expiry, refresh/revocation strategy and storage risks. Do not put long-lived bearer tokens in localStorage by default.

### 4.2 Authorization matrix
Write tests for:
- Only owner updates their profile.
- Only owner deletes a post.
- Only recipient accepts/rejects.
- Only sender cancels.
- Only a connection participant removes that connection.
- Unauthenticated user cannot call protected endpoints.
- User cannot change protected fields such as role, password hash or account status through profile updates.

### 4.3 Input and API protections
- Strict schemas, maximum lengths and allowed fields.
- Reject unexpected MongoDB operator keys such as `$where` or dotted paths from client-controlled payloads.
- Never pass client-provided JSON directly as a MongoDB filter/update.
- Rate-limit registration, login, search, requests and post creation.
- Set body-size limits and pagination limits.
- Configure CORS to the exact frontend origin; credentials only with explicit origins.
- Add safe production error handling and redacted logs.
- Add security headers and HTTPS configuration for deployment.
- Ensure user post text is returned as text and never rendered as trusted HTML.

### 4.4 Backend security tests
Test:
- Wrong password and generic login errors.
- Rate limiting.
- CSRF failure for cookie mutation without valid token.
- Session invalidation after logout.
- IDOR attempts against profile/post/request IDs.
- NoSQL injection-shaped inputs.
- Oversized body.
- Error response does not reveal stack trace, database URI or secrets.

**Exit gate C:** Backend security tests pass; known limitations are recorded. Do not claim a formal penetration test unless one has actually been performed.

## 5. React frontend foundation

### 5.1 Bootstrap frontend
From repository root:
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install
```
Install and configure Tailwind CSS using the instructions for the selected Tailwind version. Add React Router, Framer Motion, an API client and selected accessible UI primitives. Use one consistent package manager and commit its lockfile.

### 5.2 Build design system before pages
Create:
- CSS variables/design tokens.
- Typography scale, spacing, radii, shadows and color roles.
- Buttons, inputs, cards, badges, avatars, dialogs, dropdowns, skeletons and toasts.
- Responsive navigation.
- Light/dark theme only if both can be tested consistently.

Visual target: premium student-networking product, strong hierarchy, generous whitespace, restrained gradients, clean cards and purposeful motion. Avoid visual clutter and excessive glass effects.

### 5.3 Build pages in workflow order
1. Sign in / sign up.
2. Profile onboarding and profile view/edit.
3. Main application shell and navigation.
4. Home feed and create post.
5. Connections list.
6. Incoming/outgoing requests.
7. Discover and suggestions.
8. Search autocomplete.
9. Network detail: mutual connections, degree and shortest chain.
10. Loading, empty, error, not-found and unauthorized states.

Use typed API functions and shared request/response types. The frontend must not calculate authoritative graph results itself; it displays backend results.

### 5.4 Motion and UX quality
Use Framer Motion selectively:
- Short page transitions.
- Card/list entrance where it improves orientation.
- Modal and dropdown transitions.
- Small interaction feedback.
- No long intro animation or blocking splash screen.
- Respect `prefers-reduced-motion` with a reduced-motion configuration.
- Prevent layout shift; preserve keyboard focus when dialogs open/close.

**Exit gate D:** Main screens render and complete their workflows against the Flask API contract. No mock-only feature should be presented as complete.

## 6. Frontend security, accessibility and quality checks

- Do not use `dangerouslySetInnerHTML` for user-generated content.
- Keep secrets and database URI out of frontend code and `VITE_*` variables.
- Use backend session cookies with `credentials` configured intentionally and CSRF token handling.
- Client route guards are for navigation only; backend remains authoritative.
- Avoid putting session tokens in localStorage.
- Validate forms for user feedback and rely on backend validation for security.
- Do not expose stack traces or sensitive API responses in UI.
- Add accessible labels, semantic headings, keyboard support, visible focus and contrast checks.
- Test mobile widths and browser zoom.
- Test reduced-motion mode.
- Review dependency audit output and resolve or document relevant issues.

Commands (depending on configured scripts):
```bash
npm run lint
npm run test
npm run build
```

**Exit gate E:** Frontend builds cleanly, key accessibility checks pass, user text is safely rendered and authentication is not implemented only on the client.

## 7. MongoDB integration — add the real URI when supplied

This stage is intentionally after the initial backend, API checks, backend security and frontend foundation. The repository contracts and schemas were designed earlier so the database can be integrated without rewriting the DSA engine.

### 7.1 Configure connection securely
In backend-only `.env`:
```dotenv
MONGODB_URI=<the-real-uri-supplied-by-project-owner>
MONGODB_DATABASE=campusconnect
```
Do not paste the URI into this Markdown file, GitHub, frontend `.env`, screenshots, issue trackers or chat-visible code. If a URI is accidentally exposed, rotate its credentials.

### 7.2 Create Mongo repositories
Implement PyMongo repositories for:
- users and profiles,
- connection requests and accepted connections,
- posts,
- optional enhancement collections only when required.

Create indexes from `PLAN.md`. Use least-privilege database credentials. Confirm network access restrictions in the MongoDB provider.

### 7.3 Data consistency
- Persist the canonical state transition first.
- Update in-memory graph/indexes only after successful persistence.
- Use unique indexes to prevent duplicate usernames and duplicate canonical connection edges.
- Make request transitions idempotent or reject invalid repeated transitions clearly.
- On application startup, rebuild graph and indexes from persisted users/connections.
- Add a consistency check comparing stored accepted edges with in-memory adjacency invariants.
- If MongoDB is unavailable, readiness should fail and the app should not pretend writes succeeded.

### 7.4 Persistence tests
1. Register users and restart backend.
2. Verify users/profiles remain.
3. Accept a connection and restart.
4. Verify adjacency graph reconstructs correctly.
5. Create posts and restart.
6. Verify own posts and feed remain.
7. Reject/cancel requests and verify state after restart.
8. Attempt duplicate usernames and duplicate connection edges.
9. Simulate DB failure and verify memory is not falsely updated.

**Exit gate F:** MongoDB persistence and startup graph reconstruction pass. Graph algorithms still execute in Python memory, never through MongoDB graph queries.

## 8. Full end-to-end testing with 4–5 users

Use synthetic accounts only:
- Asha (`asha_demo`)
- Dev (`dev_demo`)
- Mira (`mira_demo`)
- Kiran (`kiran_demo`)
- Noor (`noor_demo`)

Create accepted graph:
`Asha—Dev`, `Asha—Mira`, `Dev—Kiran`, `Mira—Kiran`, `Kiran—Noor`.

### Test scenarios
**Accounts**
- Register all accounts.
- Duplicate username rejected.
- Login/logout works.
- Password database field is a hash.

**Profiles**
- Each user can view profiles.
- Owner can update their profile.
- Another user cannot edit it.

**Connections**
- Send request, accept, reject and cancel.
- Duplicate and self requests rejected.
- Remove an accepted connection.
- Check graph symmetry after each operation.
- Check pending requests do not appear as graph edges.

**Graph and discovery**
- Asha → Dev = 1st degree.
- Asha → Kiran = 2nd degree.
- Asha → Noor = 3rd degree.
- Verify BFS path is shortest.
- Verify mutual connections and suggestion ranking.
- Verify disconnected case in unit tests.

**Posts and feed**
- Create posts from several users.
- Delete own post.
- Attempt to delete another user's post.
- Confirm feed contains accepted connections' posts only, newest first.
- Confirm a non-connection's post is excluded.

**Search**
- Search by username and display-name prefix.
- Check case handling and no-match state.
- Confirm hashes/private fields are never returned.

**Restart**
- Stop and restart backend.
- Verify all persistent data and graph reconstruction.

### Test record template
| Test ID | User/action | Expected result | Actual result | Pass/fail | Evidence |
|---|---|---|---|---|---|
| E2E-01 | Asha registers | Account created | | | |
| E2E-02 | Duplicate Asha username | Conflict | | | |
| E2E-03 | Asha sends Dev request | Pending request | | | |
| E2E-04 | Dev accepts | Undirected edge exists | | | |
| E2E-05 | Asha to Kiran | 2nd-degree path | | | |
| E2E-06 | Asha feed | Connected posts newest-first | | | |
| E2E-07 | Asha deletes Dev's post | Forbidden | | | |
| E2E-08 | Restart app | Data and graph restored | | | |

Record actual results; never mark a test passed without running it.

## 9. Optional enhancements — only after mandatory exit gates

Implement one at a time:
1. Likes with a set/unique `(user_id, post_id)` relation.
2. Comments and replies with parent-comment references and authorization.
3. Notifications using a queue/deque for in-memory ordering and persistent records.
4. Trending among connections using a documented score and heap.
5. Groups using membership sets and clear access rules.
6. Image posts only with file type/size checks, safe storage, generated filenames, authorization and no executable uploads.

For every enhancement: identify the data structure, implement service/API/UI, add persistence, test permissions and explain complexity. Do not add all enhancements just to make the UI look larger.

## 10. Final security and release audit

### Application security
- [ ] Passwords hashed with Argon2id.
- [ ] No plaintext passwords or secrets in logs.
- [ ] Sessions protected, rotated and invalidated on logout.
- [ ] CSRF protection enabled for cookie-authenticated mutations.
- [ ] Every protected action has server-side authorization.
- [ ] NoSQL filters/updates use allowlisted server-built objects.
- [ ] User content rendered as text; XSS test payloads harmless.
- [ ] Rate limits active.
- [ ] CORS allowlist exact.
- [ ] Request size and pagination limits active.
- [ ] Production errors do not expose stack traces.
- [ ] Security headers configured.
- [ ] HTTPS used for deployed environment.
- [ ] MongoDB user has least privilege and network access is restricted.
- [ ] `.env` ignored and secrets absent from Git history.
- [ ] Dependencies reviewed and lockfiles committed.

### DSA correctness
- [ ] Adjacency list represents accepted undirected graph.
- [ ] Pending request is directed and separate from accepted graph.
- [ ] BFS returns shortest path.
- [ ] Degree labels are accurate.
- [ ] Mutual connections use neighbour intersection.
- [ ] Suggestions use documented score and tie-break.
- [ ] Prefix search works.
- [ ] Feed merge uses a heap in Python.
- [ ] No assessed graph computation is delegated to MongoDB.

### UX and release
- [ ] Responsive mobile/tablet/desktop layouts.
- [ ] Keyboard navigation and visible focus.
- [ ] Contrast and labels checked.
- [ ] Reduced motion works.
- [ ] Loading, empty, error and success states exist.
- [ ] Frontend production build succeeds.
- [ ] Backend tests and frontend tests pass.
- [ ] Clean-clone setup instructions verified.

## 11. Documentation, report and viva preparation

### README must include
- Project overview and feature list.
- Architecture diagram.
- Prerequisites and setup steps.
- Environment variables with placeholders only.
- Backend and frontend run commands.
- Test commands.
- Synthetic demo account creation instructions (do not publish reusable real passwords).
- API documentation location.
- Known limitations and optional features implemented.

### University report
Use the standard template supplied by the university. Include:
- Problem statement and objectives.
- Requirements and design.
- Architecture and module descriptions.
- DSA choices with rationale and complexity.
- Screenshots and test evidence.
- Results, limitations and future work.
- GitHub repository link.
Do not paste the complete codebase into the report.

### Viva preparation for every team member
Be able to explain:
1. Why the accepted network is an undirected graph.
2. Why a pending request is a directed relation and not an edge.
3. Why adjacency lists are suitable.
4. How BFS guarantees a shortest path in an unweighted graph.
5. How first/second/third degree is calculated.
6. How mutual connections are computed.
7. How suggestion score and tie-break work.
8. How trie prefix search works.
9. How heap merge produces newest-first feed.
10. Why MongoDB stores data but Python performs graph computations.
11. How the graph is rebuilt after restart.
12. How passwords are hashed and how authorization prevents IDOR.
13. What security tests were actually run.
14. Which optional enhancements were completed and their data structures.

## 12. Final release sequence

1. Freeze feature scope.
2. Run backend unit/integration/security tests.
3. Run frontend lint/tests/build.
4. Run 4–5-user end-to-end scenarios.
5. Run restart and persistence checks.
6. Complete security checklist and record residual risks.
7. Verify clean Git clone and setup.
8. Capture genuine screenshots and test evidence.
9. Complete university report and GitHub link.
10. Rehearse individual viva explanations.
11. Submit before the instructor-confirmed deadline.

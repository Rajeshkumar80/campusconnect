"""End-to-end API smoke test against a running backend on :5000.

Usage: .venv\\Scripts\\python.exe scripts\\smoke_test.py
"""

from __future__ import annotations

import http.cookiejar
import json
import sys
import urllib.error
import urllib.request

BASE = "http://localhost:5000/api/v1"

PASSED: list[str] = []
FAILED: list[str] = []


class Client:
    """Minimal cookie-aware HTTP client for the API."""

    def __init__(self) -> None:
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar)
        )
        self.csrf: str | None = None

    def request(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        url = f"{BASE}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("Origin", "http://localhost:5173")
        if self.csrf and method in ("POST", "PUT", "PATCH", "DELETE"):
            req.add_header("X-CSRFToken", self.csrf)
        try:
            with self.opener.open(req) as resp:
                payload = resp.read().decode()
                token = resp.headers.get("X-CSRFToken")
                if token:
                    self.csrf = token
                return resp.status, json.loads(payload) if payload else {}
        except urllib.error.HTTPError as err:
            payload = err.read().decode()
            token = err.headers.get("X-CSRFToken")
            if token:
                self.csrf = token
            try:
                return err.code, json.loads(payload) if payload else {}
            except json.JSONDecodeError:
                return err.code, {"raw": payload}

    def get(self, path: str) -> tuple[int, dict]:
        return self.request("GET", path)

    def post(self, path: str, body: dict | None = None) -> tuple[int, dict]:
        return self.request("POST", path, body)

    def patch(self, path: str, body: dict | None = None) -> tuple[int, dict]:
        return self.request("PATCH", path, body)

    def delete(self, path: str) -> tuple[int, dict]:
        return self.request("DELETE", path)


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        PASSED.append(label)
        print(f"  PASS  {label}")
    else:
        FAILED.append(f"{label} :: {detail}")
        print(f"  FAIL  {label} :: {detail}")


def register(client: Client, username: str, name: str, programme: str, year: int) -> dict:
    status, body = client.post(
        "/auth/register",
        {
            "username": username,
            "password": "CampusPass123",
            "name": name,
            "programme": programme,
            "year": year,
            "bio": f"{name} demo account",
            "skills": ["Python", "React"],
        },
    )
    if status != 201:
        print(f"    register {username} -> {status} {body}")
        return {}
    return body.get("data", {}).get("user", {})


DEMOS = [
    ("asha_demo", "Asha Menon", "B.Tech CSE", 3),
    ("dev_demo", "Dev Sharma", "B.Tech IT", 2),
    ("mira_demo", "Mira Iyer", "BCA", 1),
    ("kiran_demo", "Kiran Rao", "B.Tech ECE", 3),
    ("noor_demo", "Noor Khan", "B.Sc Maths", 2),
]


def main() -> int:
    print("\n== health ==")
    anon = Client()
    status, body = anon.get("/health/live")
    check("health/live returns 200", status == 200, f"status={status} body={body}")

    print("\n== csrf ==")
    status, body = anon.get("/auth/csrf")
    check("auth/csrf returns 200", status == 200, f"status={status}")
    check("auth/csrf body has token", bool(body.get("data", {}).get("csrf_token")), str(body))
    check("auth/csrf sets header", bool(anon.csrf), "no X-CSRFToken header")

    print("\n== register demo users ==")
    clients: dict[str, Client] = {}
    users: dict[str, dict] = {}
    for username, name, programme, year in DEMOS:
        client = Client()
        client.get("/auth/csrf")
        user = register(client, username, name, programme, year)
        if user:
            clients[username] = client
            users[username] = user
        check(f"register {username}", bool(user.get("user_id")), f"body={user}")
    check("all 5 demo users registered", len(users) == 5, f"got {len(users)}")

    print("\n== duplicate username rejected ==")
    dup = Client()
    dup.get("/auth/csrf")
    status, body = dup.post(
        "/auth/register",
        {
            "username": "asha_demo",
            "password": "CampusPass123",
            "name": "Copy",
            "programme": "X",
            "year": 1,
            "bio": "",
            "skills": [],
        },
    )
    check("duplicate username -> 409", status == 409, f"status={status} body={body}")

    print("\n== login ==")
    asha = clients["asha_demo"]
    status, body = asha.post("/auth/login", {"username": "asha_demo", "password": "CampusPass123"})
    check("login correct password -> 200", status == 200, f"status={status} body={body}")
    check("login returns user", bool(body.get("data", {}).get("user", {}).get("user_id")), str(body))

    bad = Client()
    bad.get("/auth/csrf")
    status, body = bad.post("/auth/login", {"username": "asha_demo", "password": "wrong"})
    check("login wrong password -> 401", status == 401, f"status={status} body={body}")

    print("\n== session ==")
    status, body = asha.get("/auth/me")
    check("auth/me returns logged-in user", status == 200 and body.get("data", {}).get("user"), f"{status} {body}")

    anon2 = Client()
    status, _ = anon2.get("/auth/me")
    check("auth/me without session -> 401", status == 401, f"status={status}")

    print("\n== connections ==")
    dev = clients["dev_demo"]
    mira = clients["mira_demo"]

    status, body = asha.post("/connections/requests", {"recipient_id": users["dev_demo"]["user_id"]})
    check("send connection request -> 201", status == 201, f"status={status} body={body}")
    request_id = body.get("data", {}).get("request", {}).get("request_id")

    status, body = dev.get("/connections/requests/incoming")
    incoming = body.get("data", {}).get("requests", [])
    check("recipient sees incoming request", status == 200 and len(incoming) == 1, f"{status} {body}")
    check(
        "incoming request carries sender profile",
        bool(incoming and incoming[0].get("sender", {}).get("username") == "asha_demo"),
        str(incoming),
    )

    status, body = asha.get("/connections/requests/outgoing")
    outgoing = body.get("data", {}).get("requests", [])
    check("sender sees outgoing request", status == 200 and len(outgoing) == 1, f"{status} {body}")
    check(
        "outgoing request carries recipient profile",
        bool(outgoing and outgoing[0].get("recipient", {}).get("username") == "dev_demo"),
        str(outgoing),
    )

    status, body = dev.post(f"/connections/requests/{request_id}/accept")
    check("recipient accepts request -> 200", status == 200, f"status={status} body={body}")

    status, body = asha.get("/connections")
    conns = body.get("data", {}).get("connections", [])
    check("accepted connection listed", status == 200 and len(conns) == 1, f"{status} {body}")
    check("connection carries user summary", bool(conns and conns[0].get("username") == "dev_demo"), str(conns))

    print("\n== csrf enforcement ==")
    no_csrf = Client()
    no_csrf.get("/auth/csrf")
    no_csrf.csrf = None
    status, body = no_csrf.post("/posts", {"text": "should fail"})
    check("POST without CSRF token -> 400", status == 400, f"status={status} body={body}")
    check(
        "CSRF error code is CSRF_TOKEN_MISSING",
        body.get("error", {}).get("code") == "CSRF_TOKEN_MISSING",
        str(body),
    )

    print("\n== posts + feed ==")
    status, body = asha.post("/posts", {"text": "Hello from Asha - DSA project demo post."})
    check("create post -> 201", status == 201, f"status={status} body={body}")
    post_id = body.get("data", {}).get("post", {}).get("post_id")

    status, body = dev.post("/posts", {"text": "Hi from Dev, looking for project partners."})
    check("connection creates post -> 201", status == 201, f"status={status} body={body}")

    status, body = dev.get("/posts/feed")
    feed = body.get("data", {}).get("feed", [])
    check("feed returns 200", status == 200, f"status={status} body={body}")
    # FR-16: the feed contains only accepted connections' posts, newest first.
    check("feed contains connection posts only", len(feed) == 1, f"feed={feed}")
    check(
        "feed post is from the connection",
        bool(feed) and feed[0]["author_username"] == "asha_demo",
        str(feed),
    )
    check(
        "feed post created_at is numeric",
        all(isinstance(p.get("created_at"), (int, float)) for p in feed),
        str(feed),
    )

    status, body = asha.post("/posts", {"text": ""})
    check("empty post rejected -> 400", status == 400, f"status={status} body={body}")

    print("\n== post ownership ==")
    status, body = dev.delete(f"/posts/{post_id}")
    check("cannot delete another user's post (403/404)", status in (403, 404), f"status={status} body={body}")
    status, body = asha.delete(f"/posts/{post_id}")
    check("owner can delete own post -> 200", status == 200, f"status={status} body={body}")

    print("\n== graph ==")
    status, body = asha.get(f"/connections/{users['dev_demo']['user_id']}/degree")
    check("degree endpoint works", status == 200, f"status={status} body={body}")
    check("degree of direct connection is 1", body.get("data", {}).get("degree", {}).get("degree") == 1, str(body))

    status, body = mira.get(f"/connections/{users['dev_demo']['user_id']}/degree")
    check("degree for disconnected user", status == 200, f"status={status} body={body}")

    status, body = asha.get(f"/connections/{users['dev_demo']['user_id']}/path")
    check("shortest path endpoint works", status == 200, f"status={status} body={body}")

    status, body = asha.get(f"/connections/{users['dev_demo']['user_id']}/mutual")
    check("mutual endpoint works", status == 200, f"status={status} body={body}")

    print("\n== search + suggestions ==")
    status, body = asha.get("/users/search?q=dev")
    users_found = body.get("data", {}).get("users", [])
    check("search finds dev_demo", status == 200 and any(u["username"] == "dev_demo" for u in users_found), str(body))

    status, body = asha.get("/connections/suggestions?limit=10")
    suggestions = body.get("data", {}).get("suggestions", [])
    check("suggestions endpoint works", status == 200, f"status={status} body={body}")
    check("suggestions exclude self", all(s["username"] != "asha_demo" for s in suggestions), str(suggestions))

    print("\n== profile ==")
    status, body = asha.get("/profiles/me")
    check("get own profile -> 200", status == 200, f"status={status} body={body}")
    status, body = asha.patch("/profiles/me", {"bio": "Updated bio from smoke test", "skills": ["Python", "MongoDB"]})
    check("update own profile -> 200", status == 200, f"status={status} body={body}")
    check("profile update persisted", body.get("data", {}).get("profile", {}).get("bio") == "Updated bio from smoke test", str(body))

    status, body = dev.patch(f"/profiles/{users['asha_demo']['user_id']}", {"bio": "hijacked"})
    check("cannot patch another profile (404/403/405)", status in (403, 404, 405), f"status={status} body={body}")

    print("\n== no secret leakage ==")
    for label, path in [
        ("auth/me", "/auth/me"),
        ("users/<id>", f"/users/{users['dev_demo']['user_id']}"),
        ("users/search", "/users/search?q=demo"),
        ("connections", "/connections"),
        ("profiles/me", "/profiles/me"),
    ]:
        status, body = asha.get(path)
        raw = json.dumps(body)
        check(f"{label} hides password hash", "password_hash" not in raw, raw[:200])
        check(f"{label} hides mongo uri", "mongodb://" not in raw, raw[:200])

    print("\n== remove connection ==")
    status, body = asha.delete(f"/connections/{users['dev_demo']['user_id']}")
    check("remove connection -> 200", status == 200, f"status={status} body={body}")
    status, body = asha.get("/connections")
    check("connection removed from list", len(body.get("data", {}).get("connections", [])) == 0, str(body))
    status, body = dev.get("/connections")
    check("connection removed from other side too", len(body.get("data", {}).get("connections", [])) == 0, str(body))

    print("\n== logout ==")
    status, body = asha.post("/auth/logout")
    check("logout -> 200", status == 200, f"status={status} body={body}")
    status, _ = asha.get("/auth/me")
    check("session invalid after logout", status == 401, f"status={status}")

    print(f"\n{'=' * 50}")
    print(f"PASSED: {len(PASSED)}   FAILED: {len(FAILED)}")
    for failure in FAILED:
        print(f"  FAILED: {failure}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())

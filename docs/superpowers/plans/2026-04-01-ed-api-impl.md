# ed-api Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a full-featured Python client for the EdStem API with typed models, resource-based architecture, markdown/XML conversion, rate limiting, and a Typer CLI with `--json` output.

**Architecture:** The `EdClient` class manages auth and HTTP, delegating to resource classes (`UserResource`, `ThreadsResource`, etc.) that each wrap a set of related API endpoints. All public APIs accept/return markdown; Ed XML conversion is handled internally. An `_http.py` module handles rate limiting, retries, and error mapping. The CLI is a thin Typer wrapper that creates an `EdClient` and calls resource methods.

**Tech Stack:** Python 3.11+, uv, httpx, Typer, Rich, python-dotenv, BeautifulSoup4 (for XML conversion)

**Important API details:**
- No dedicated "list courses" endpoint — courses come from `GET /api/user` response
- No dedicated search endpoint — search is client-side filtering of thread list
- Thread edit requires fetch-merge-put (not true partial update)
- `content` fields use Ed's custom XML format; `document` fields are server-rendered HTML
- Accept answer endpoint: `POST /api/threads/{thread_id}/accept/{comment_id}`
- Set private: via `PUT /api/threads/{thread_id}` with `is_private` field
- Comment replies: `POST /api/comments/{comment_id}/comments`

---

## File Map

```
ed-api/
├── pyproject.toml
├── README.md
├── src/
│   └── ed_api/
│       ├── __init__.py              # Re-export EdClient
│       ├── models.py                # Thread, ThreadDetail, Comment, UserSummary, etc.
│       ├── exceptions.py            # EdAuthError, EdNotFoundError, etc.
│       ├── content.py               # markdown_to_ed_xml, ed_xml_to_markdown
│       ├── _http.py                 # HttpClient wrapper (httpx + rate limit + retries)
│       ├── client.py                # EdClient main class
│       ├── resources/
│       │   ├── __init__.py
│       │   ├── user.py              # UserResource
│       │   ├── courses.py           # CoursesResource
│       │   ├── threads.py           # ThreadsResource
│       │   ├── comments.py          # CommentsResource
│       │   └── files.py             # FilesResource
│       └── cli/
│           ├── __init__.py
│           ├── main.py              # Typer app + subcommands
│           ├── auth.py              # auth check, whoami
│           ├── courses.py           # courses list, users
│           ├── threads.py           # threads list, get, search, create, edit, actions
│           ├── comments.py          # comments post, reply, endorse, accept
│           ├── files.py             # files upload
│           └── content.py           # content to-xml, to-markdown
├── tests/
│   ├── conftest.py                  # Shared fixtures, mock HTTP client
│   ├── test_models.py
│   ├── test_exceptions.py
│   ├── test_content.py
│   ├── test_http.py
│   ├── test_user.py
│   ├── test_courses.py
│   ├── test_threads.py
│   ├── test_comments.py
│   ├── test_files.py
│   ├── test_client.py
│   ├── test_cli.py
│   └── fixtures/
│       └── responses/               # JSON files with sample API responses
│           ├── user_info.json
│           ├── thread_list.json
│           ├── thread_detail.json
│           ├── comment.json
│           └── file_upload.json
```

---

### Task 1: Project Scaffolding + Fixtures

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/ed_api/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/fixtures/responses/*.json`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "ed-api"
version = "0.1.0"
description = "Full-featured Python client for the EdStem API. Typed models, Typer CLI, markdown/XML conversion."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "httpx>=0.27.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
    "python-dotenv>=1.0.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=5.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-httpx>=0.30.0",
    "respx>=0.21.0",
]

[project.scripts]
ed-api = "ed_api.cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/ed_api"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 2: Create README.md**

```markdown
# ed-api

Full-featured Python client for the EdStem API.
```

- [ ] **Step 3: Create src/ed_api/__init__.py**

```python
"""ed-api: Full-featured Python client for the EdStem API."""
```

- [ ] **Step 4: Create sample API response fixtures**

`tests/fixtures/responses/user_info.json`:
```json
{
  "user": {
    "id": 12345,
    "role": "user",
    "name": "Test User",
    "email": "test@example.com",
    "username": "testuser",
    "avatar": null,
    "activated": true,
    "created_at": "2024-01-15T10:00:00.000Z",
    "course_role": null,
    "secondary_emails": [],
    "has_password": true
  },
  "courses": [
    {
      "course": {
        "id": 54321,
        "code": "CS7646",
        "name": "ML4T",
        "year": "2026",
        "session": "spring",
        "status": "active",
        "created_at": "2026-01-01T00:00:00.000Z"
      },
      "role": {
        "user_id": 12345,
        "course_id": 54321,
        "role": "admin",
        "digest": false,
        "created_at": "2026-01-01T00:00:00.000Z",
        "deleted_at": null
      }
    }
  ]
}
```

`tests/fixtures/responses/thread_list.json`:
```json
{
  "threads": [
    {
      "id": 100,
      "number": 1,
      "user_id": 99,
      "course_id": 54321,
      "type": "question",
      "title": "get_data() returns NaN",
      "content": "<document version=\"2.0\"><paragraph>My data has NaN values</paragraph></document>",
      "document": "<p>My data has NaN values</p>",
      "category": "Project 1",
      "subcategory": "",
      "subsubcategory": "",
      "flag_count": 0,
      "star_count": 2,
      "view_count": 45,
      "unique_view_count": 30,
      "vote_count": 3,
      "reply_count": 2,
      "unresolved_count": 0,
      "is_locked": false,
      "is_pinned": false,
      "is_private": false,
      "is_endorsed": false,
      "is_answered": true,
      "is_student_answered": true,
      "is_staff_answered": false,
      "is_archived": false,
      "is_anonymous": false,
      "is_megathread": false,
      "anonymous_comments": false,
      "approved_status": "approved",
      "created_at": "2026-03-15T10:30:00.000Z",
      "updated_at": "2026-03-16T14:22:00.000Z",
      "deleted_at": null,
      "pinned_at": null,
      "anonymous_id": 0,
      "vote": 0,
      "is_seen": true,
      "is_starred": false,
      "is_watched": false,
      "new_reply_count": 0,
      "user": {
        "id": 99,
        "name": "Student A",
        "role": "user",
        "course_role": "student",
        "avatar": null
      }
    }
  ]
}
```

`tests/fixtures/responses/thread_detail.json`:
```json
{
  "thread": {
    "id": 100,
    "number": 1,
    "user_id": 99,
    "course_id": 54321,
    "type": "question",
    "title": "get_data() returns NaN",
    "content": "<document version=\"2.0\"><paragraph>My data has NaN values</paragraph></document>",
    "document": "<p>My data has NaN values</p>",
    "category": "Project 1",
    "subcategory": "",
    "subsubcategory": "",
    "is_locked": false,
    "is_pinned": false,
    "is_private": false,
    "is_endorsed": false,
    "is_answered": true,
    "is_student_answered": true,
    "is_staff_answered": true,
    "is_archived": false,
    "is_anonymous": false,
    "created_at": "2026-03-15T10:30:00.000Z",
    "updated_at": "2026-03-16T14:22:00.000Z",
    "deleted_at": null,
    "answers": [
      {
        "id": 200,
        "user_id": 88,
        "course_id": 54321,
        "thread_id": 100,
        "parent_id": null,
        "type": "answer",
        "content": "<document version=\"2.0\"><paragraph>The NaN values are expected due to lookback period.</paragraph></document>",
        "document": "<p>The NaN values are expected due to lookback period.</p>",
        "is_endorsed": true,
        "is_anonymous": false,
        "is_private": false,
        "is_resolved": false,
        "created_at": "2026-03-15T12:00:00.000Z",
        "updated_at": "2026-03-15T12:00:00.000Z",
        "deleted_at": null,
        "vote_count": 5,
        "comments": []
      }
    ],
    "comments": [
      {
        "id": 201,
        "user_id": 99,
        "course_id": 54321,
        "thread_id": 100,
        "parent_id": null,
        "type": "comment",
        "content": "<document version=\"2.0\"><paragraph>Thank you!</paragraph></document>",
        "document": "<p>Thank you!</p>",
        "is_endorsed": false,
        "is_anonymous": false,
        "is_private": false,
        "is_resolved": false,
        "created_at": "2026-03-15T14:00:00.000Z",
        "updated_at": "2026-03-15T14:00:00.000Z",
        "deleted_at": null,
        "vote_count": 0,
        "comments": []
      }
    ]
  },
  "users": [
    {"id": 99, "name": "Student A", "role": "user", "course_role": "student", "avatar": null},
    {"id": 88, "name": "TA Smith", "role": "user", "course_role": "staff", "avatar": null}
  ]
}
```

`tests/fixtures/responses/comment.json`:
```json
{
  "comment": {
    "id": 300,
    "user_id": 88,
    "course_id": 54321,
    "thread_id": 100,
    "parent_id": null,
    "type": "comment",
    "content": "<document version=\"2.0\"><paragraph>Here is my response.</paragraph></document>",
    "document": "<p>Here is my response.</p>",
    "is_endorsed": false,
    "is_anonymous": false,
    "is_private": false,
    "is_resolved": false,
    "created_at": "2026-03-16T10:00:00.000Z",
    "updated_at": "2026-03-16T10:00:00.000Z",
    "deleted_at": null,
    "vote_count": 0,
    "comments": []
  }
}
```

`tests/fixtures/responses/file_upload.json`:
```json
{
  "file": {
    "user_id": 12345,
    "id": "abc123def456",
    "filename": "screenshot.png",
    "extension": "png",
    "created_at": "2026-03-16T10:00:00.000Z"
  }
}
```

- [ ] **Step 5: Create tests/conftest.py**

```python
"""Shared test fixtures for ed-api tests."""

import json
import pathlib
from unittest.mock import AsyncMock, MagicMock

import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures" / "responses"


def load_fixture(name: str) -> dict:
    """Load a JSON fixture file."""
    return json.loads((FIXTURES_DIR / name).read_text())


@pytest.fixture
def user_info_response() -> dict:
    return load_fixture("user_info.json")


@pytest.fixture
def thread_list_response() -> dict:
    return load_fixture("thread_list.json")


@pytest.fixture
def thread_detail_response() -> dict:
    return load_fixture("thread_detail.json")


@pytest.fixture
def comment_response() -> dict:
    return load_fixture("comment.json")


@pytest.fixture
def file_upload_response() -> dict:
    return load_fixture("file_upload.json")
```

- [ ] **Step 6: Verify scaffolding**

```bash
cd E:/workspaces/school/gt/ed-api
uv sync
uv run pytest --co -q
```

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml README.md src/ tests/
git commit -m "feat: project scaffolding with fixtures and conftest"
```

---

### Task 2: Exceptions

**Files:**
- Create: `src/ed_api/exceptions.py`
- Create: `tests/test_exceptions.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_exceptions.py`:
```python
from ed_api.exceptions import (
    EdAPIError,
    EdAuthError,
    EdNotFoundError,
    EdForbiddenError,
    EdRateLimitError,
)


class TestExceptions:
    def test_base_error_has_status_and_body(self):
        err = EdAPIError("something failed", status_code=500, response_body={"error": "internal"})
        assert err.status_code == 500
        assert err.response_body == {"error": "internal"}
        assert "something failed" in str(err)

    def test_auth_error_is_api_error(self):
        err = EdAuthError("bad token", status_code=401, response_body={})
        assert isinstance(err, EdAPIError)
        assert err.status_code == 401

    def test_not_found_error(self):
        err = EdNotFoundError("thread 999", status_code=404, response_body={})
        assert err.status_code == 404

    def test_forbidden_error(self):
        err = EdForbiddenError("no access", status_code=403, response_body={})
        assert err.status_code == 403

    def test_rate_limit_error(self):
        err = EdRateLimitError("slow down", status_code=429, response_body={})
        assert err.status_code == 429
```

- [ ] **Step 2: Verify fail, then implement**

`src/ed_api/exceptions.py`:
```python
"""Exception classes for ed-api."""


class EdAPIError(Exception):
    """Base exception for all Ed API errors."""

    def __init__(self, message: str, status_code: int, response_body: dict):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class EdAuthError(EdAPIError):
    """Authentication failed (401)."""


class EdForbiddenError(EdAPIError):
    """Insufficient permissions (403)."""


class EdNotFoundError(EdAPIError):
    """Resource not found (404)."""


class EdRateLimitError(EdAPIError):
    """Rate limited (429)."""
```

- [ ] **Step 3: Run tests, verify pass**

Run: `uv run pytest tests/test_exceptions.py -v`

- [ ] **Step 4: Commit**

```bash
git add src/ed_api/exceptions.py tests/test_exceptions.py
git commit -m "feat: exception classes with status code and response body"
```

---

### Task 3: Data Models

**Files:**
- Create: `src/ed_api/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_models.py`:
```python
from datetime import datetime
from ed_api.models import (
    UserSummary, UserInfo, CourseUser, Course, CourseEnrollment,
    Thread, ThreadDetail, Comment,
    parse_thread, parse_thread_detail, parse_comment, parse_user_info,
)


class TestUserSummary:
    def test_create(self):
        u = UserSummary(id=1, name="Alice", role="staff")
        assert u.name == "Alice"
        assert u.role == "staff"

    def test_is_staff(self):
        assert UserSummary(id=1, name="A", role="staff").is_staff is True
        assert UserSummary(id=1, name="A", role="admin").is_staff is True
        assert UserSummary(id=1, name="A", role="student").is_staff is False


class TestThread:
    def test_parse_from_api(self, thread_list_response):
        raw = thread_list_response["threads"][0]
        thread = parse_thread(raw)
        assert thread.id == 100
        assert thread.number == 1
        assert thread.title == "get_data() returns NaN"
        assert thread.type == "question"
        assert thread.category == "Project 1"
        assert thread.is_answered is True
        assert isinstance(thread.author, UserSummary)
        assert isinstance(thread.created_at, datetime)


class TestThreadDetail:
    def test_parse_with_comments(self, thread_detail_response):
        raw = thread_detail_response
        thread = parse_thread_detail(raw)
        assert isinstance(thread, ThreadDetail)
        assert len(thread.comments) == 2  # 1 answer + 1 comment
        assert thread.comments[0].is_endorsed is True  # the answer

    def test_is_unanswered(self, thread_detail_response):
        raw = thread_detail_response
        thread = parse_thread_detail(raw)
        assert thread.is_unanswered is False

    def test_has_staff_response(self, thread_detail_response):
        raw = thread_detail_response
        users = {u["id"]: u for u in raw["users"]}
        thread = parse_thread_detail(raw)
        assert thread.has_staff_response is True


class TestComment:
    def test_parse_from_api(self, comment_response):
        raw = comment_response["comment"]
        comment = parse_comment(raw)
        assert comment.id == 300
        assert comment.thread_id == 100
        assert comment.parent_id is None


class TestUserInfo:
    def test_parse_user_info(self, user_info_response):
        info = parse_user_info(user_info_response)
        assert info.user.id == 12345
        assert info.user.name == "Test User"
        assert len(info.courses) == 1
        assert info.courses[0].course.code == "CS7646"
        assert info.courses[0].role == "admin"
```

- [ ] **Step 2: Verify fail, then implement**

`src/ed_api/models.py`:
```python
"""Data models for ed-api."""

from dataclasses import dataclass, field
from datetime import datetime


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    # Ed uses ISO format with Z suffix
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s)


@dataclass
class UserSummary:
    id: int
    name: str
    role: str  # "student", "staff", "admin"

    @property
    def is_staff(self) -> bool:
        return self.role in ("staff", "admin")


@dataclass
class UserInfo:
    id: int
    name: str
    email: str
    role: str
    avatar: str | None = None


@dataclass
class Course:
    id: int
    code: str
    name: str
    year: str
    session: str
    status: str  # "active" or "archived"


@dataclass
class CourseEnrollment:
    course: Course
    role: str  # "student", "staff", "admin"


@dataclass
class ParsedUserInfo:
    user: UserInfo
    courses: list[CourseEnrollment]


@dataclass
class CourseUser:
    id: int
    name: str
    email: str
    role: str
    course_role: str

    @property
    def is_staff(self) -> bool:
        return self.course_role in ("staff", "admin")


@dataclass
class Comment:
    id: int
    thread_id: int
    parent_id: int | None
    user_id: int
    author: UserSummary | None
    type: str  # "comment" or "answer"
    content: str  # Ed XML (raw)
    is_endorsed: bool
    is_anonymous: bool
    is_private: bool
    created_at: datetime | None
    vote_count: int = 0
    replies: list["Comment"] = field(default_factory=list)


@dataclass
class Thread:
    id: int
    course_id: int
    number: int
    type: str  # "question", "post", "announcement"
    title: str
    content: str  # Ed XML (raw)
    category: str
    subcategory: str | None
    author: UserSummary
    is_pinned: bool
    is_private: bool
    is_locked: bool
    is_endorsed: bool
    is_answered: bool
    is_staff_answered: bool
    is_student_answered: bool
    created_at: datetime | None
    updated_at: datetime | None
    view_count: int = 0
    vote_count: int = 0
    reply_count: int = 0


@dataclass
class ThreadDetail(Thread):
    comments: list[Comment] = field(default_factory=list)
    users: dict[int, UserSummary] = field(default_factory=dict)

    @property
    def is_unanswered(self) -> bool:
        return len(self.comments) == 0

    @property
    def has_staff_response(self) -> bool:
        for c in self.comments:
            author = self.users.get(c.user_id)
            if author and author.is_staff:
                return True
        return False

    @property
    def has_student_only(self) -> bool:
        return len(self.comments) > 0 and not self.has_staff_response

    @property
    def needs_followup(self) -> bool:
        if not self.has_staff_response:
            return False
        last_staff_idx = -1
        for i, c in enumerate(self.comments):
            author = self.users.get(c.user_id)
            if author and author.is_staff:
                last_staff_idx = i
        # Student commented after last staff response
        return last_staff_idx < len(self.comments) - 1


# --- Parse functions ---

def parse_thread(raw: dict) -> Thread:
    user_data = raw.get("user", {})
    author = UserSummary(
        id=user_data.get("id", 0),
        name=user_data.get("name", "Unknown"),
        role=user_data.get("course_role") or user_data.get("role", "student"),
    )
    return Thread(
        id=raw["id"],
        course_id=raw.get("course_id", 0),
        number=raw.get("number", 0),
        type=raw.get("type", "post"),
        title=raw.get("title", ""),
        content=raw.get("content", ""),
        category=raw.get("category", ""),
        subcategory=raw.get("subcategory") or None,
        author=author,
        is_pinned=raw.get("is_pinned", False),
        is_private=raw.get("is_private", False),
        is_locked=raw.get("is_locked", False),
        is_endorsed=raw.get("is_endorsed", False),
        is_answered=raw.get("is_answered", False),
        is_staff_answered=raw.get("is_staff_answered", False),
        is_student_answered=raw.get("is_student_answered", False),
        created_at=_parse_dt(raw.get("created_at")),
        updated_at=_parse_dt(raw.get("updated_at")),
        view_count=raw.get("view_count", 0),
        vote_count=raw.get("vote_count", 0),
        reply_count=raw.get("reply_count", 0),
    )


def parse_comment(raw: dict, users: dict[int, UserSummary] | None = None) -> Comment:
    author = None
    if users and raw.get("user_id") in users:
        author = users[raw["user_id"]]
    replies = [parse_comment(r, users) for r in raw.get("comments", [])]
    return Comment(
        id=raw["id"],
        thread_id=raw.get("thread_id", 0),
        parent_id=raw.get("parent_id"),
        user_id=raw.get("user_id", 0),
        author=author,
        type=raw.get("type", "comment"),
        content=raw.get("content", ""),
        is_endorsed=raw.get("is_endorsed", False),
        is_anonymous=raw.get("is_anonymous", False),
        is_private=raw.get("is_private", False),
        created_at=_parse_dt(raw.get("created_at")),
        vote_count=raw.get("vote_count", 0),
        replies=replies,
    )


def parse_thread_detail(raw: dict) -> ThreadDetail:
    thread_data = raw.get("thread", raw)
    users_list = raw.get("users", [])
    users = {}
    for u in users_list:
        users[u["id"]] = UserSummary(
            id=u["id"],
            name=u.get("name", "Unknown"),
            role=u.get("course_role") or u.get("role", "student"),
        )

    base = parse_thread(thread_data)
    answers = [parse_comment(a, users) for a in thread_data.get("answers", [])]
    comments = [parse_comment(c, users) for c in thread_data.get("comments", [])]
    all_comments = answers + comments

    return ThreadDetail(
        id=base.id,
        course_id=base.course_id,
        number=base.number,
        type=base.type,
        title=base.title,
        content=base.content,
        category=base.category,
        subcategory=base.subcategory,
        author=base.author,
        is_pinned=base.is_pinned,
        is_private=base.is_private,
        is_locked=base.is_locked,
        is_endorsed=base.is_endorsed,
        is_answered=base.is_answered,
        is_staff_answered=base.is_staff_answered,
        is_student_answered=base.is_student_answered,
        created_at=base.created_at,
        updated_at=base.updated_at,
        view_count=base.view_count,
        vote_count=base.vote_count,
        reply_count=base.reply_count,
        comments=all_comments,
        users=users,
    )


def parse_user_info(raw: dict) -> ParsedUserInfo:
    u = raw["user"]
    user = UserInfo(
        id=u["id"],
        name=u["name"],
        email=u["email"],
        role=u.get("role", "user"),
        avatar=u.get("avatar"),
    )
    courses = []
    for entry in raw.get("courses", []):
        c = entry["course"]
        course = Course(
            id=c["id"],
            code=c.get("code", ""),
            name=c.get("name", ""),
            year=c.get("year", ""),
            session=c.get("session", ""),
            status=c.get("status", "active"),
        )
        role = entry.get("role", {}).get("role", "student")
        courses.append(CourseEnrollment(course=course, role=role))
    return ParsedUserInfo(user=user, courses=courses)
```

- [ ] **Step 3: Run tests, verify pass**

Run: `uv run pytest tests/test_models.py -v`

- [ ] **Step 4: Commit**

```bash
git add src/ed_api/models.py tests/test_models.py
git commit -m "feat: data models with parse functions for API responses"
```

---

### Task 4: Content Conversion (Markdown ↔ Ed XML)

**Files:**
- Create: `src/ed_api/content.py`
- Create: `tests/test_content.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_content.py`:
```python
from ed_api.content import markdown_to_ed_xml, ed_xml_to_markdown


class TestMarkdownToEdXml:
    def test_simple_paragraph(self):
        xml = markdown_to_ed_xml("Hello world")
        assert '<document version="2.0">' in xml
        assert "<paragraph>" in xml
        assert "Hello world" in xml

    def test_heading(self):
        xml = markdown_to_ed_xml("## My Heading")
        assert '<heading level="2">' in xml
        assert "My Heading" in xml

    def test_bold(self):
        xml = markdown_to_ed_xml("Some **bold** text")
        assert "<bold>" in xml
        assert "bold" in xml

    def test_italic(self):
        xml = markdown_to_ed_xml("Some *italic* text")
        assert "<italic>" in xml

    def test_code_inline(self):
        xml = markdown_to_ed_xml("Use `print()` function")
        assert "<code>" in xml
        assert "print()" in xml

    def test_code_block(self):
        xml = markdown_to_ed_xml("```python\nprint('hello')\n```")
        assert "<snippet" in xml or "<pre>" in xml

    def test_link(self):
        xml = markdown_to_ed_xml("[Click here](https://example.com)")
        assert '<link href="https://example.com">' in xml

    def test_list(self):
        xml = markdown_to_ed_xml("- Item 1\n- Item 2")
        assert '<list style="bullet">' in xml
        assert "<list-item>" in xml

    def test_numbered_list(self):
        xml = markdown_to_ed_xml("1. First\n2. Second")
        assert '<list style="number">' in xml


class TestEdXmlToMarkdown:
    def test_simple_paragraph(self):
        xml = '<document version="2.0"><paragraph>Hello world</paragraph></document>'
        md = ed_xml_to_markdown(xml)
        assert "Hello world" in md

    def test_heading(self):
        xml = '<document version="2.0"><heading level="2">My Heading</heading></document>'
        md = ed_xml_to_markdown(xml)
        assert "## My Heading" in md

    def test_bold(self):
        xml = '<document version="2.0"><paragraph>Some <bold>bold</bold> text</paragraph></document>'
        md = ed_xml_to_markdown(xml)
        assert "**bold**" in md

    def test_code_inline(self):
        xml = '<document version="2.0"><paragraph>Use <code>print()</code></paragraph></document>'
        md = ed_xml_to_markdown(xml)
        assert "`print()`" in md

    def test_link(self):
        xml = '<document version="2.0"><paragraph><link href="https://example.com">Click</link></paragraph></document>'
        md = ed_xml_to_markdown(xml)
        assert "[Click](https://example.com)" in md

    def test_roundtrip_simple(self):
        original = "Hello **bold** and *italic* text"
        xml = markdown_to_ed_xml(original)
        md = ed_xml_to_markdown(xml)
        assert "bold" in md
        assert "italic" in md
```

- [ ] **Step 2: Verify fail, then implement**

`src/ed_api/content.py`:
```python
"""Markdown ↔ Ed XML content conversion.

EdStem uses a custom XML format for post bodies. This module converts
between standard markdown and Ed's XML format.
"""

import re
from xml.sax.saxutils import escape as xml_escape

from bs4 import BeautifulSoup


def markdown_to_ed_xml(md: str) -> str:
    """Convert markdown text to Ed's XML document format."""
    lines = md.split("\n")
    elements: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Code block (fenced)
        if line.strip().startswith("```"):
            lang_match = re.match(r"^```(\w*)", line.strip())
            lang = lang_match.group(1) if lang_match else ""
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```
            code = "\n".join(code_lines)
            if lang:
                elements.append(f'<snippet language="{lang}" runnable="false">{xml_escape(code)}</snippet>')
            else:
                elements.append(f"<pre>{xml_escape(code)}</pre>")
            continue

        # Heading
        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading_match:
            level = len(heading_match.group(1))
            text = _inline_to_xml(heading_match.group(2))
            elements.append(f'<heading level="{level}">{text}</heading>')
            i += 1
            continue

        # Unordered list
        if re.match(r"^[-*+]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*+]\s+", lines[i]):
                item_text = re.sub(r"^[-*+]\s+", "", lines[i])
                items.append(f"<list-item><paragraph>{_inline_to_xml(item_text)}</paragraph></list-item>")
                i += 1
            elements.append(f'<list style="bullet">{"".join(items)}</list>')
            continue

        # Ordered list
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                item_text = re.sub(r"^\d+\.\s+", "", lines[i])
                items.append(f"<list-item><paragraph>{_inline_to_xml(item_text)}</paragraph></list-item>")
                i += 1
            elements.append(f'<list style="number">{"".join(items)}</list>')
            continue

        # Blank line — skip
        if not line.strip():
            i += 1
            continue

        # Regular paragraph
        text = _inline_to_xml(line)
        elements.append(f"<paragraph>{text}</paragraph>")
        i += 1

    return f'<document version="2.0">{"".join(elements)}</document>'


def _inline_to_xml(text: str) -> str:
    """Convert inline markdown formatting to Ed XML tags."""
    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<bold>\1</bold>", text)
    text = re.sub(r"__(.+?)__", r"<bold>\1</bold>", text)
    # Italic: *text* or _text_
    text = re.sub(r"\*(.+?)\*", r"<italic>\1</italic>", text)
    text = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<italic>\1</italic>", text)
    # Inline code: `code`
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Links: [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<link href="\2">\1</link>', text)
    return text


def ed_xml_to_markdown(xml: str) -> str:
    """Convert Ed's XML document format to markdown."""
    soup = BeautifulSoup(xml, "lxml-xml")
    doc = soup.find("document")
    if not doc:
        # Try parsing as fragment
        soup = BeautifulSoup(xml, "html.parser")
        doc = soup
    return _node_to_markdown(doc).strip()


def _node_to_markdown(node) -> str:
    """Recursively convert an XML node to markdown."""
    if node.string is not None and node.name is None:
        return str(node.string)

    parts = []
    for child in node.children:
        if child.name is None:
            parts.append(str(child))
            continue

        tag = child.name.lower() if child.name else ""

        if tag == "document":
            parts.append(_node_to_markdown(child))
        elif tag == "heading":
            level = int(child.get("level", 1))
            text = _node_to_markdown(child)
            parts.append(f"\n{'#' * level} {text}\n")
        elif tag == "paragraph":
            text = _node_to_markdown(child)
            parts.append(f"\n{text}\n")
        elif tag == "bold":
            parts.append(f"**{_node_to_markdown(child)}**")
        elif tag == "italic":
            parts.append(f"*{_node_to_markdown(child)}*")
        elif tag == "underline":
            parts.append(f"__{_node_to_markdown(child)}__")
        elif tag == "code":
            parts.append(f"`{_node_to_markdown(child)}`")
        elif tag == "pre":
            parts.append(f"\n```\n{_node_to_markdown(child)}\n```\n")
        elif tag == "snippet":
            lang = child.get("language", "")
            parts.append(f"\n```{lang}\n{_node_to_markdown(child)}\n```\n")
        elif tag == "link":
            href = child.get("href", "")
            text = _node_to_markdown(child)
            parts.append(f"[{text}]({href})")
        elif tag == "list":
            style = child.get("style", "bullet")
            items = child.find_all("list-item", recursive=False)
            for idx, item in enumerate(items, 1):
                item_text = _node_to_markdown(item).strip()
                if style == "number":
                    parts.append(f"\n{idx}. {item_text}")
                else:
                    parts.append(f"\n- {item_text}")
            parts.append("\n")
        elif tag == "list-item":
            parts.append(_node_to_markdown(child))
        elif tag == "math":
            parts.append(f"${_node_to_markdown(child)}$")
        elif tag == "callout":
            text = _node_to_markdown(child)
            ctype = child.get("type", "info")
            parts.append(f"\n> **{ctype.upper()}:** {text}\n")
        elif tag == "spoiler":
            parts.append(f"\n||{_node_to_markdown(child)}||\n")
        elif tag == "image":
            src = child.get("src", "")
            parts.append(f"![image]({src})")
        elif tag == "figure":
            parts.append(_node_to_markdown(child))
        elif tag == "file":
            url = child.get("url", "")
            parts.append(f"[file]({url})")
        else:
            parts.append(_node_to_markdown(child))

    return "".join(parts)
```

- [ ] **Step 3: Run tests, verify pass**

Run: `uv run pytest tests/test_content.py -v`

- [ ] **Step 4: Commit**

```bash
git add src/ed_api/content.py tests/test_content.py
git commit -m "feat: markdown to Ed XML bidirectional conversion"
```

---

### Task 5: HTTP Client Wrapper

**Files:**
- Create: `src/ed_api/_http.py`
- Create: `tests/test_http.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_http.py`:
```python
import httpx
import pytest
from unittest.mock import patch, MagicMock
from ed_api._http import HttpClient
from ed_api.exceptions import EdAuthError, EdNotFoundError, EdRateLimitError, EdAPIError


class TestHttpClient:
    def test_creates_with_token(self):
        client = HttpClient(token="test-token", region="us")
        assert client._base_url == "https://us.edstem.org/api/"

    def test_au_region(self):
        client = HttpClient(token="test-token", region="au")
        assert client._base_url == "https://au.edstem.org/api/"

    def test_auth_header_set(self):
        client = HttpClient(token="my-token", region="us")
        assert client._client.headers["Authorization"] == "Bearer my-token"

    def test_maps_401_to_auth_error(self):
        client = HttpClient(token="bad", region="us")
        with patch.object(client._client, "request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            mock_resp.json.return_value = {"message": "bad token"}
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401", request=MagicMock(), response=mock_resp
            )
            mock_req.return_value = mock_resp
            with pytest.raises(EdAuthError):
                client.get("user")

    def test_maps_404_to_not_found(self):
        client = HttpClient(token="tok", region="us")
        with patch.object(client._client, "request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_resp.json.return_value = {"message": "not found"}
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404", request=MagicMock(), response=mock_resp
            )
            mock_req.return_value = mock_resp
            with pytest.raises(EdNotFoundError):
                client.get("threads/999")

    def test_maps_429_to_rate_limit(self):
        client = HttpClient(token="tok", region="us")
        with patch.object(client._client, "request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 429
            mock_resp.json.return_value = {"message": "rate limited"}
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "429", request=MagicMock(), response=mock_resp
            )
            mock_req.return_value = mock_resp
            with pytest.raises(EdRateLimitError):
                client.get("threads")
```

- [ ] **Step 2: Verify fail, then implement**

`src/ed_api/_http.py`:
```python
"""HTTP client wrapper with rate limiting, retries, and error mapping."""

import time

import httpx

from ed_api.exceptions import (
    EdAPIError,
    EdAuthError,
    EdForbiddenError,
    EdNotFoundError,
    EdRateLimitError,
)

ERROR_MAP = {
    401: EdAuthError,
    403: EdForbiddenError,
    404: EdNotFoundError,
    429: EdRateLimitError,
}


class HttpClient:
    """Wraps httpx.Client with Ed-specific auth, error handling, and rate limiting."""

    def __init__(
        self,
        token: str,
        region: str = "us",
        rate_limit: float = 5.0,
        max_retries: int = 3,
    ):
        self._base_url = f"https://{region}.edstem.org/api/"
        self._rate_limit = rate_limit
        self._max_retries = max_retries
        self._min_interval = 1.0 / rate_limit if rate_limit > 0 else 0
        self._last_request_time = 0.0

        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    def _throttle(self):
        """Enforce rate limit by sleeping if needed."""
        if self._min_interval > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make an HTTP request with rate limiting and error mapping."""
        url = self._base_url + path

        for attempt in range(self._max_retries):
            self._throttle()
            try:
                response = self._client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                try:
                    body = e.response.json()
                except Exception:
                    body = {"raw": e.response.text}

                # Retry on 429 with backoff
                if status == 429 and attempt < self._max_retries - 1:
                    wait = 2 ** attempt
                    time.sleep(wait)
                    continue

                error_cls = ERROR_MAP.get(status, EdAPIError)
                msg = body.get("message", f"HTTP {status}")
                raise error_cls(msg, status_code=status, response_body=body) from e

        # Should not reach here
        raise EdAPIError("Max retries exceeded", status_code=0, response_body={})

    def get(self, path: str, params: dict | None = None) -> httpx.Response:
        return self._request("GET", path, params=params)

    def post(self, path: str, json: dict | None = None, **kwargs) -> httpx.Response:
        return self._request("POST", path, json=json, **kwargs)

    def put(self, path: str, json: dict | None = None) -> httpx.Response:
        return self._request("PUT", path, json=json)

    def delete(self, path: str) -> httpx.Response:
        return self._request("DELETE", path)

    def upload(self, path: str, files: dict) -> httpx.Response:
        return self._request("POST", path, files=files)

    def close(self):
        self._client.close()
```

- [ ] **Step 3: Run tests, verify pass**

Run: `uv run pytest tests/test_http.py -v`

- [ ] **Step 4: Commit**

```bash
git add src/ed_api/_http.py tests/test_http.py
git commit -m "feat: HTTP client wrapper with rate limiting and error mapping"
```

---

### Task 6: Resource Classes (User, Courses, Threads, Comments, Files)

**Files:**
- Create: `src/ed_api/resources/__init__.py`
- Create: `src/ed_api/resources/user.py`
- Create: `src/ed_api/resources/courses.py`
- Create: `src/ed_api/resources/threads.py`
- Create: `src/ed_api/resources/comments.py`
- Create: `src/ed_api/resources/files.py`
- Create: `tests/test_user.py`
- Create: `tests/test_courses.py`
- Create: `tests/test_threads.py`
- Create: `tests/test_comments.py`
- Create: `tests/test_files.py`

This is a large task. Each resource class wraps the HTTP client with typed methods. Tests mock the HTTP client.

- [ ] **Step 1: Create resources/__init__.py**

```python
"""Resource classes for Ed API operations."""
```

- [ ] **Step 2: Write UserResource + tests**

`src/ed_api/resources/user.py`:
```python
"""User resource."""

from ed_api._http import HttpClient
from ed_api.models import ParsedUserInfo, parse_user_info


class UserResource:
    def __init__(self, http: HttpClient):
        self._http = http

    def info(self) -> ParsedUserInfo:
        """Get authenticated user info and enrolled courses."""
        response = self._http.get("user")
        return parse_user_info(response.json())

    def activity(
        self,
        user_id: int,
        course_id: int,
        limit: int = 30,
        offset: int = 0,
        filter: str = "all",
    ) -> list[dict]:
        """List user's threads and comments in a course."""
        response = self._http.get(
            f"users/{user_id}/profile/activity",
            params={
                "courseID": course_id,
                "limit": limit,
                "offset": offset,
                "filter": filter,
            },
        )
        return response.json().get("items", [])
```

`tests/test_user.py`:
```python
from unittest.mock import MagicMock
from ed_api.resources.user import UserResource
from ed_api.models import ParsedUserInfo


class TestUserResource:
    def test_info(self, user_info_response):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = user_info_response
        mock_http.get.return_value = mock_resp

        resource = UserResource(mock_http)
        result = resource.info()

        assert isinstance(result, ParsedUserInfo)
        assert result.user.name == "Test User"
        mock_http.get.assert_called_once_with("user")

    def test_activity(self):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": [{"type": "thread", "value": {}}]}
        mock_http.get.return_value = mock_resp

        resource = UserResource(mock_http)
        result = resource.activity(user_id=1, course_id=2, limit=10)

        assert len(result) == 1
        mock_http.get.assert_called_once()
```

- [ ] **Step 3: Write CoursesResource + tests**

`src/ed_api/resources/courses.py`:
```python
"""Courses resource."""

from ed_api._http import HttpClient
from ed_api.models import Course, CourseEnrollment, CourseUser, parse_user_info


class CoursesResource:
    def __init__(self, http: HttpClient):
        self._http = http

    def list(self) -> list[CourseEnrollment]:
        """List enrolled courses (from user info endpoint)."""
        response = self._http.get("user")
        info = parse_user_info(response.json())
        return info.courses

    def users(self, course_id: int, role: str | None = None) -> list[CourseUser]:
        """List users in a course. Optionally filter by role."""
        response = self._http.get(f"courses/{course_id}/analytics/users")
        users_data = response.json().get("users", [])
        users = [
            CourseUser(
                id=u["id"],
                name=u.get("name", ""),
                email=u.get("email", ""),
                role=u.get("role", "user"),
                course_role=u.get("course_role", "student"),
            )
            for u in users_data
        ]
        if role:
            users = [u for u in users if u.course_role == role]
        return users
```

`tests/test_courses.py`:
```python
from unittest.mock import MagicMock
from ed_api.resources.courses import CoursesResource


class TestCoursesResource:
    def test_list(self, user_info_response):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = user_info_response
        mock_http.get.return_value = mock_resp

        resource = CoursesResource(mock_http)
        result = resource.list()

        assert len(result) == 1
        assert result[0].course.code == "CS7646"

    def test_users(self):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "users": [
                {"id": 1, "name": "Alice", "email": "a@b.com", "role": "user", "course_role": "staff"},
                {"id": 2, "name": "Bob", "email": "b@b.com", "role": "user", "course_role": "student"},
            ]
        }
        mock_http.get.return_value = mock_resp

        resource = CoursesResource(mock_http)
        all_users = resource.users(54321)
        assert len(all_users) == 2

        staff = resource.users(54321, role="staff")
        assert len(staff) == 1
        assert staff[0].name == "Alice"
```

- [ ] **Step 4: Write ThreadsResource + tests**

`src/ed_api/resources/threads.py`:
```python
"""Threads resource."""

from typing import Generator

from ed_api._http import HttpClient
from ed_api.content import markdown_to_ed_xml
from ed_api.models import Thread, ThreadDetail, parse_thread, parse_thread_detail


class ThreadsResource:
    def __init__(self, http: HttpClient):
        self._http = http

    def list(
        self,
        course_id: int,
        limit: int = 100,
        offset: int = 0,
        sort: str = "new",
    ) -> list[Thread]:
        """List threads in a course."""
        response = self._http.get(
            f"courses/{course_id}/threads",
            params={"limit": limit, "offset": offset, "sort": sort},
        )
        return [parse_thread(t) for t in response.json().get("threads", [])]

    def list_all(
        self, course_id: int, sort: str = "new"
    ) -> Generator[Thread, None, None]:
        """Iterate all threads in a course (handles pagination)."""
        offset = 0
        limit = 100
        while True:
            threads = self.list(course_id, limit=limit, offset=offset, sort=sort)
            if not threads:
                break
            yield from threads
            if len(threads) < limit:
                break
            offset += limit

    def get(self, thread_id: int) -> ThreadDetail:
        """Get a thread by global ID, including comments."""
        response = self._http.get(f"threads/{thread_id}")
        return parse_thread_detail(response.json())

    def get_by_number(self, course_id: int, thread_number: int) -> ThreadDetail:
        """Get a thread by course-local number."""
        response = self._http.get(f"courses/{course_id}/threads/{thread_number}")
        return parse_thread_detail(response.json())

    def search(self, course_id: int, query: str, limit: int = 100) -> list[Thread]:
        """Search threads by title and content (client-side filtering)."""
        query_lower = query.lower()
        results = []
        for thread in self.list_all(course_id):
            if (query_lower in thread.title.lower() or
                    query_lower in thread.category.lower()):
                results.append(thread)
                if len(results) >= limit:
                    break
        return results

    def create(
        self,
        course_id: int,
        title: str,
        body: str,
        type: str = "question",
        category: str = "",
        is_private: bool = False,
        is_anonymous: bool = False,
    ) -> Thread:
        """Create a new thread. Body is markdown (converted to Ed XML)."""
        response = self._http.post(
            f"courses/{course_id}/threads",
            json={
                "thread": {
                    "type": type,
                    "title": title,
                    "category": category,
                    "subcategory": "",
                    "subsubcategory": "",
                    "content": markdown_to_ed_xml(body),
                    "is_pinned": False,
                    "is_private": is_private,
                    "is_anonymous": is_anonymous,
                    "is_megathread": False,
                    "anonymous_comments": False,
                }
            },
        )
        return parse_thread(response.json().get("thread", {}))

    def edit(
        self,
        thread_id: int,
        title: str | None = None,
        body: str | None = None,
        category: str | None = None,
        is_private: bool | None = None,
    ) -> Thread:
        """Edit a thread. Fetches current state, merges changes, sends PUT."""
        # Fetch current thread to merge
        current = self._http.get(f"threads/{thread_id}").json().get("thread", {})

        if title is not None:
            current["title"] = title
        if body is not None:
            current["content"] = markdown_to_ed_xml(body)
        if category is not None:
            current["category"] = category
        if is_private is not None:
            current["is_private"] = is_private

        response = self._http.put(
            f"threads/{thread_id}",
            json={"thread": current},
        )
        return parse_thread(response.json().get("thread", {}))

    def lock(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/lock")

    def unlock(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/unlock")

    def pin(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/pin")

    def unpin(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/unpin")

    def set_private(self, thread_id: int, private: bool = True) -> None:
        """Set thread visibility."""
        self.edit(thread_id, is_private=private)

    def endorse(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/endorse")

    def unendorse(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/unendorse")

    def star(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/star")

    def unstar(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/unstar")
```

`tests/test_threads.py`:
```python
from unittest.mock import MagicMock, call
from ed_api.resources.threads import ThreadsResource
from ed_api.models import Thread, ThreadDetail


class TestThreadsResource:
    def _make_resource(self, responses=None):
        mock_http = MagicMock()
        if responses:
            mock_resp = MagicMock()
            mock_resp.json.side_effect = responses if isinstance(responses, list) else [responses]
            mock_http.get.return_value = mock_resp
            mock_http.post.return_value = mock_resp
            mock_http.put.return_value = mock_resp
        return ThreadsResource(mock_http), mock_http

    def test_list(self, thread_list_response):
        resource, mock_http = self._make_resource()
        mock_resp = MagicMock()
        mock_resp.json.return_value = thread_list_response
        mock_http.get.return_value = mock_resp

        result = resource.list(54321, limit=50)
        assert len(result) == 1
        assert isinstance(result[0], Thread)
        assert result[0].title == "get_data() returns NaN"

    def test_get(self, thread_detail_response):
        resource, mock_http = self._make_resource()
        mock_resp = MagicMock()
        mock_resp.json.return_value = thread_detail_response
        mock_http.get.return_value = mock_resp

        result = resource.get(100)
        assert isinstance(result, ThreadDetail)
        assert result.title == "get_data() returns NaN"
        assert len(result.comments) == 2

    def test_lock(self):
        resource, mock_http = self._make_resource()
        resource.lock(100)
        mock_http.post.assert_called_once_with("threads/100/lock")

    def test_endorse(self):
        resource, mock_http = self._make_resource()
        resource.endorse(100)
        mock_http.post.assert_called_once_with("threads/100/endorse")

    def test_pin(self):
        resource, mock_http = self._make_resource()
        resource.pin(100)
        mock_http.post.assert_called_once_with("threads/100/pin")
```

- [ ] **Step 5: Write CommentsResource + tests**

`src/ed_api/resources/comments.py`:
```python
"""Comments resource."""

from ed_api._http import HttpClient
from ed_api.content import markdown_to_ed_xml
from ed_api.models import Comment, parse_comment


class CommentsResource:
    def __init__(self, http: HttpClient):
        self._http = http

    def post(
        self,
        thread_id: int,
        content: str,
        is_answer: bool = False,
        is_private: bool = False,
        is_anonymous: bool = False,
    ) -> Comment:
        """Post a comment or answer on a thread. Content is markdown."""
        response = self._http.post(
            f"threads/{thread_id}/comments",
            json={
                "comment": {
                    "type": "answer" if is_answer else "comment",
                    "content": markdown_to_ed_xml(content),
                    "is_private": is_private,
                    "is_anonymous": is_anonymous,
                }
            },
        )
        return parse_comment(response.json().get("comment", {}))

    def reply(
        self,
        comment_id: int,
        content: str,
        is_private: bool = False,
        is_anonymous: bool = False,
    ) -> Comment:
        """Reply to an existing comment. Content is markdown."""
        response = self._http.post(
            f"comments/{comment_id}/comments",
            json={
                "comment": {
                    "type": "comment",
                    "content": markdown_to_ed_xml(content),
                    "is_private": is_private,
                    "is_anonymous": is_anonymous,
                }
            },
        )
        return parse_comment(response.json().get("comment", {}))

    def edit(self, comment_id: int, content: str) -> Comment:
        """Edit an existing comment. Content is markdown."""
        response = self._http.put(
            f"comments/{comment_id}",
            json={
                "comment": {
                    "content": markdown_to_ed_xml(content),
                }
            },
        )
        return parse_comment(response.json().get("comment", {}))

    def endorse(self, comment_id: int) -> None:
        self._http.post(f"comments/{comment_id}/endorse")

    def unendorse(self, comment_id: int) -> None:
        self._http.post(f"comments/{comment_id}/unendorse")

    def accept(self, thread_id: int, comment_id: int) -> None:
        """Accept a comment as the answer to a thread."""
        self._http.post(f"threads/{thread_id}/accept/{comment_id}")
```

`tests/test_comments.py`:
```python
from unittest.mock import MagicMock
from ed_api.resources.comments import CommentsResource
from ed_api.models import Comment


class TestCommentsResource:
    def test_post_comment(self, comment_response):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = comment_response
        mock_http.post.return_value = mock_resp

        resource = CommentsResource(mock_http)
        result = resource.post(100, "Here is my response.")

        assert isinstance(result, Comment)
        assert result.id == 300
        mock_http.post.assert_called_once()
        call_args = mock_http.post.call_args
        assert call_args[0][0] == "threads/100/comments"

    def test_post_answer(self, comment_response):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = comment_response
        mock_http.post.return_value = mock_resp

        resource = CommentsResource(mock_http)
        resource.post(100, "The answer is...", is_answer=True)

        call_args = mock_http.post.call_args
        body = call_args[1]["json"]["comment"]
        assert body["type"] == "answer"

    def test_reply(self, comment_response):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = comment_response
        mock_http.post.return_value = mock_resp

        resource = CommentsResource(mock_http)
        resource.reply(200, "Follow-up reply")

        call_args = mock_http.post.call_args
        assert call_args[0][0] == "comments/200/comments"

    def test_endorse(self):
        mock_http = MagicMock()
        resource = CommentsResource(mock_http)
        resource.endorse(200)
        mock_http.post.assert_called_once_with("comments/200/endorse")

    def test_accept(self):
        mock_http = MagicMock()
        resource = CommentsResource(mock_http)
        resource.accept(thread_id=100, comment_id=200)
        mock_http.post.assert_called_once_with("threads/100/accept/200")
```

- [ ] **Step 6: Write FilesResource + tests**

`src/ed_api/resources/files.py`:
```python
"""Files resource."""

import mimetypes
import pathlib

from ed_api._http import HttpClient


STATIC_FILE_URL = "https://static.us.edusercontent.com/files/"


class FilesResource:
    def __init__(self, http: HttpClient, region: str = "us"):
        self._http = http
        self._static_url = f"https://static.{region}.edusercontent.com/files/"

    def upload(self, filename: str, file_bytes: bytes, content_type: str) -> str:
        """Upload a file. Returns the static URL."""
        response = self._http.upload(
            "files",
            files={"attachment": (filename, file_bytes, content_type)},
        )
        file_id = response.json()["file"]["id"]
        return self._static_url + file_id

    def upload_from_path(self, file_path: str | pathlib.Path) -> str:
        """Upload a file from a local path. Auto-detects MIME type."""
        path = pathlib.Path(file_path)
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type is None:
            mime_type = "application/octet-stream"
        file_bytes = path.read_bytes()
        return self.upload(path.name, file_bytes, mime_type)
```

`tests/test_files.py`:
```python
from unittest.mock import MagicMock
from ed_api.resources.files import FilesResource


class TestFilesResource:
    def test_upload(self, file_upload_response):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = file_upload_response
        mock_http.upload.return_value = mock_resp

        resource = FilesResource(mock_http, region="us")
        url = resource.upload("test.png", b"fake-png-bytes", "image/png")

        assert "abc123def456" in url
        mock_http.upload.assert_called_once()

    def test_upload_from_path(self, tmp_path, file_upload_response):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = file_upload_response
        mock_http.upload.return_value = mock_resp

        test_file = tmp_path / "screenshot.png"
        test_file.write_bytes(b"fake-png-bytes")

        resource = FilesResource(mock_http, region="us")
        url = resource.upload_from_path(test_file)

        assert "abc123def456" in url
```

- [ ] **Step 7: Run all resource tests**

Run: `uv run pytest tests/test_user.py tests/test_courses.py tests/test_threads.py tests/test_comments.py tests/test_files.py -v`

- [ ] **Step 8: Commit**

```bash
git add src/ed_api/resources/ tests/test_user.py tests/test_courses.py tests/test_threads.py tests/test_comments.py tests/test_files.py
git commit -m "feat: resource classes for user, courses, threads, comments, files"
```

---

### Task 7: EdClient Main Class

**Files:**
- Create: `src/ed_api/client.py`
- Create: `tests/test_client.py`
- Modify: `src/ed_api/__init__.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_client.py`:
```python
import os
import pytest
from unittest.mock import patch, MagicMock
from ed_api.client import EdClient
from ed_api.resources.user import UserResource
from ed_api.resources.courses import CoursesResource
from ed_api.resources.threads import ThreadsResource
from ed_api.resources.comments import CommentsResource
from ed_api.resources.files import FilesResource


class TestEdClient:
    def test_create_with_token(self):
        client = EdClient(token="test-token")
        assert isinstance(client.user, UserResource)
        assert isinstance(client.courses, CoursesResource)
        assert isinstance(client.threads, ThreadsResource)
        assert isinstance(client.comments, CommentsResource)
        assert isinstance(client.files, FilesResource)

    def test_create_with_env_var(self):
        with patch.dict(os.environ, {"ED_API_TOKEN": "env-token"}):
            client = EdClient()
            assert client._http is not None

    def test_create_without_token_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="token"):
                EdClient()

    def test_region_default(self):
        client = EdClient(token="tok")
        assert client._region == "us"

    def test_region_override(self):
        client = EdClient(token="tok", region="au")
        assert client._region == "au"

    def test_region_from_env(self):
        with patch.dict(os.environ, {"ED_API_TOKEN": "tok", "ED_REGION": "eu"}):
            client = EdClient()
            assert client._region == "eu"
```

- [ ] **Step 2: Verify fail, then implement**

`src/ed_api/client.py`:
```python
"""EdClient: main entry point for the ed-api library."""

import os

from dotenv import load_dotenv

from ed_api._http import HttpClient
from ed_api.resources.comments import CommentsResource
from ed_api.resources.courses import CoursesResource
from ed_api.resources.files import FilesResource
from ed_api.resources.threads import ThreadsResource
from ed_api.resources.user import UserResource


class EdClient:
    """Client for the EdStem API.

    Token is resolved from (in order):
    1. Constructor argument
    2. ED_API_TOKEN environment variable
    3. .env file in working directory
    """

    def __init__(
        self,
        token: str | None = None,
        region: str | None = None,
        rate_limit: float = 5.0,
    ):
        load_dotenv()

        self._token = token or os.environ.get("ED_API_TOKEN")
        if not self._token:
            raise ValueError(
                "No API token provided. Pass token= to EdClient, "
                "set ED_API_TOKEN environment variable, or add it to a .env file."
            )

        self._region = region or os.environ.get("ED_REGION", "us")
        self._http = HttpClient(
            token=self._token,
            region=self._region,
            rate_limit=rate_limit,
        )

        self.user = UserResource(self._http)
        self.courses = CoursesResource(self._http)
        self.threads = ThreadsResource(self._http)
        self.comments = CommentsResource(self._http)
        self.files = FilesResource(self._http, region=self._region)

    def close(self):
        """Close the HTTP client."""
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
```

- [ ] **Step 3: Update __init__.py**

`src/ed_api/__init__.py`:
```python
"""ed-api: Full-featured Python client for the EdStem API."""

from ed_api.client import EdClient
from ed_api.exceptions import (
    EdAPIError,
    EdAuthError,
    EdForbiddenError,
    EdNotFoundError,
    EdRateLimitError,
)
from ed_api.models import (
    Comment,
    Course,
    CourseEnrollment,
    CourseUser,
    Thread,
    ThreadDetail,
    UserInfo,
    UserSummary,
)

__all__ = [
    "EdClient",
    "EdAPIError",
    "EdAuthError",
    "EdForbiddenError",
    "EdNotFoundError",
    "EdRateLimitError",
    "Comment",
    "Course",
    "CourseEnrollment",
    "CourseUser",
    "Thread",
    "ThreadDetail",
    "UserInfo",
    "UserSummary",
]
```

- [ ] **Step 4: Run tests, verify pass**

Run: `uv run pytest tests/test_client.py -v`

- [ ] **Step 5: Commit**

```bash
git add src/ed_api/client.py src/ed_api/__init__.py tests/test_client.py
git commit -m "feat: EdClient main class with resource namespacing"
```

---

### Task 8: CLI

**Files:**
- Create: `src/ed_api/cli/__init__.py`
- Create: `src/ed_api/cli/main.py`
- Create: `src/ed_api/cli/auth.py`
- Create: `src/ed_api/cli/courses.py`
- Create: `src/ed_api/cli/threads.py`
- Create: `src/ed_api/cli/comments.py`
- Create: `src/ed_api/cli/files.py`
- Create: `src/ed_api/cli/content.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Create CLI structure**

`src/ed_api/cli/__init__.py`:
```python
"""CLI for ed-api."""
```

`src/ed_api/cli/main.py`:
```python
"""Typer CLI entry point for ed-api."""

import typer

from ed_api.cli.auth import app as auth_app
from ed_api.cli.courses import app as courses_app
from ed_api.cli.threads import app as threads_app
from ed_api.cli.comments import app as comments_app
from ed_api.cli.files import app as files_app
from ed_api.cli.content import app as content_app

app = typer.Typer(name="ed-api", help="EdStem API client.")
app.add_typer(auth_app, name="auth")
app.add_typer(courses_app, name="courses")
app.add_typer(threads_app, name="threads")
app.add_typer(comments_app, name="comments")
app.add_typer(files_app, name="files")
app.add_typer(content_app, name="content")
```

`src/ed_api/cli/auth.py`:
```python
"""Auth CLI commands."""

import json
import typer
from rich.console import Console
from ed_api.client import EdClient

app = typer.Typer(help="Authentication commands.")
console = Console()


@app.command()
def check(
    json_output: bool = typer.Option(False, "--json"),
):
    """Verify API token is valid."""
    try:
        client = EdClient()
        info = client.user.info()
        if json_output:
            print(json.dumps({"status": "ok", "user": info.user.name}))
        else:
            console.print(f"[green]Token valid.[/green] Logged in as {info.user.name}")
    except Exception as e:
        if json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[red]Token invalid:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def whoami(
    json_output: bool = typer.Option(False, "--json"),
):
    """Show current user info."""
    client = EdClient()
    info = client.user.info()
    if json_output:
        print(json.dumps({
            "id": info.user.id,
            "name": info.user.name,
            "email": info.user.email,
            "courses": [
                {"id": c.course.id, "code": c.course.code, "name": c.course.name, "role": c.role}
                for c in info.courses
            ],
        }))
    else:
        console.print(f"[bold]{info.user.name}[/bold] ({info.user.email})")
        for c in info.courses:
            console.print(f"  {c.course.code} — {c.course.name} ({c.role})")
```

`src/ed_api/cli/courses.py`:
```python
"""Courses CLI commands."""

import json
import typer
from rich.console import Console
from rich.table import Table
from ed_api.client import EdClient

app = typer.Typer(help="Course commands.")
console = Console()


@app.command(name="list")
def list_courses(
    json_output: bool = typer.Option(False, "--json"),
):
    """List enrolled courses."""
    client = EdClient()
    courses = client.courses.list()
    if json_output:
        print(json.dumps([
            {"id": c.course.id, "code": c.course.code, "name": c.course.name,
             "year": c.course.year, "session": c.course.session, "role": c.role}
            for c in courses
        ]))
    else:
        table = Table(title="Courses")
        table.add_column("ID")
        table.add_column("Code")
        table.add_column("Name")
        table.add_column("Role")
        for c in courses:
            table.add_row(str(c.course.id), c.course.code, c.course.name, c.role)
        console.print(table)


@app.command()
def users(
    course_id: int = typer.Argument(help="Course ID"),
    role: str = typer.Option(None, "--role", help="Filter by role"),
    json_output: bool = typer.Option(False, "--json"),
):
    """List users in a course."""
    client = EdClient()
    users_list = client.courses.users(course_id, role=role)
    if json_output:
        print(json.dumps([
            {"id": u.id, "name": u.name, "email": u.email, "role": u.course_role}
            for u in users_list
        ]))
    else:
        table = Table(title=f"Users in course {course_id}")
        table.add_column("ID")
        table.add_column("Name")
        table.add_column("Role")
        for u in users_list:
            table.add_row(str(u.id), u.name, u.course_role)
        console.print(table)
```

`src/ed_api/cli/threads.py`:
```python
"""Threads CLI commands."""

import json
import typer
from rich.console import Console
from rich.table import Table
from ed_api.client import EdClient

app = typer.Typer(help="Thread commands.")
console = Console()


@app.command(name="list")
def list_threads(
    course_id: int = typer.Argument(help="Course ID"),
    limit: int = typer.Option(30, "--limit"),
    sort: str = typer.Option("new", "--sort"),
    json_output: bool = typer.Option(False, "--json"),
):
    """List threads in a course."""
    client = EdClient()
    threads = client.threads.list(course_id, limit=limit, sort=sort)
    if json_output:
        print(json.dumps([
            {"id": t.id, "number": t.number, "title": t.title, "type": t.type,
             "category": t.category, "is_answered": t.is_answered,
             "reply_count": t.reply_count, "created_at": str(t.created_at)}
            for t in threads
        ]))
    else:
        table = Table(title=f"Threads in course {course_id}")
        table.add_column("#")
        table.add_column("Title")
        table.add_column("Category")
        table.add_column("Replies")
        for t in threads:
            table.add_row(str(t.number), t.title, t.category, str(t.reply_count))
        console.print(table)


@app.command()
def get(
    thread_ref: str = typer.Argument(help="Thread ID or course_id:number"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Get a thread with comments."""
    client = EdClient()
    if ":" in thread_ref:
        course_id, number = thread_ref.split(":", 1)
        thread = client.threads.get_by_number(int(course_id), int(number))
    else:
        thread = client.threads.get(int(thread_ref))
    if json_output:
        print(json.dumps({
            "id": thread.id, "number": thread.number, "title": thread.title,
            "content": thread.content, "category": thread.category,
            "is_answered": thread.is_answered,
            "comments": [
                {"id": c.id, "type": c.type, "content": c.content,
                 "is_endorsed": c.is_endorsed, "user_id": c.user_id}
                for c in thread.comments
            ],
        }))
    else:
        console.print(f"[bold]#{thread.number}:[/bold] {thread.title}")
        console.print(f"Category: {thread.category}")
        for c in thread.comments:
            label = "[answer]" if c.type == "answer" else "[comment]"
            endorsed = " (endorsed)" if c.is_endorsed else ""
            console.print(f"\n  {label}{endorsed} by user {c.user_id}")


@app.command()
def search(
    course_id: int = typer.Argument(help="Course ID"),
    query: str = typer.Argument(help="Search query"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Search threads."""
    client = EdClient()
    threads = client.threads.search(course_id, query)
    if json_output:
        print(json.dumps([
            {"id": t.id, "number": t.number, "title": t.title, "category": t.category}
            for t in threads
        ]))
    else:
        for t in threads:
            console.print(f"  #{t.number}: {t.title} [{t.category}]")


@app.command()
def lock(thread_id: int = typer.Argument()):
    """Lock a thread."""
    EdClient().threads.lock(thread_id)
    console.print(f"Thread {thread_id} locked.")


@app.command()
def unlock(thread_id: int = typer.Argument()):
    """Unlock a thread."""
    EdClient().threads.unlock(thread_id)
    console.print(f"Thread {thread_id} unlocked.")


@app.command()
def pin(thread_id: int = typer.Argument()):
    """Pin a thread."""
    EdClient().threads.pin(thread_id)
    console.print(f"Thread {thread_id} pinned.")


@app.command()
def unpin(thread_id: int = typer.Argument()):
    """Unpin a thread."""
    EdClient().threads.unpin(thread_id)
    console.print(f"Thread {thread_id} unpinned.")


@app.command()
def private(thread_id: int = typer.Argument()):
    """Mark a thread as private."""
    EdClient().threads.set_private(thread_id, private=True)
    console.print(f"Thread {thread_id} marked private.")


@app.command()
def public(thread_id: int = typer.Argument()):
    """Mark a thread as public."""
    EdClient().threads.set_private(thread_id, private=False)
    console.print(f"Thread {thread_id} marked public.")


@app.command()
def endorse(thread_id: int = typer.Argument()):
    """Endorse a thread."""
    EdClient().threads.endorse(thread_id)
    console.print(f"Thread {thread_id} endorsed.")


@app.command()
def unendorse(thread_id: int = typer.Argument()):
    """Remove endorsement from a thread."""
    EdClient().threads.unendorse(thread_id)
    console.print(f"Thread {thread_id} unendorsed.")
```

`src/ed_api/cli/comments.py`:
```python
"""Comments CLI commands."""

import json
import typer
from rich.console import Console
from ed_api.client import EdClient

app = typer.Typer(help="Comment commands.")
console = Console()


@app.command()
def post(
    thread_id: int = typer.Argument(help="Thread ID"),
    body: str = typer.Option(..., "--body", help="Comment body (markdown)"),
    answer: bool = typer.Option(False, "--answer", help="Post as answer"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Post a comment on a thread."""
    client = EdClient()
    comment = client.comments.post(thread_id, body, is_answer=answer)
    if json_output:
        print(json.dumps({"id": comment.id, "type": comment.type, "thread_id": comment.thread_id}))
    else:
        console.print(f"Posted {comment.type} (id: {comment.id}) on thread {thread_id}")


@app.command()
def reply(
    comment_id: int = typer.Argument(help="Comment ID to reply to"),
    body: str = typer.Option(..., "--body", help="Reply body (markdown)"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Reply to a comment."""
    client = EdClient()
    comment = client.comments.reply(comment_id, body)
    if json_output:
        print(json.dumps({"id": comment.id, "type": comment.type}))
    else:
        console.print(f"Replied (id: {comment.id}) to comment {comment_id}")


@app.command()
def endorse(comment_id: int = typer.Argument()):
    """Endorse a comment."""
    EdClient().comments.endorse(comment_id)
    console.print(f"Comment {comment_id} endorsed.")


@app.command()
def unendorse(comment_id: int = typer.Argument()):
    """Remove endorsement from a comment."""
    EdClient().comments.unendorse(comment_id)
    console.print(f"Comment {comment_id} unendorsed.")


@app.command()
def accept(
    thread_id: int = typer.Argument(help="Thread ID"),
    comment_id: int = typer.Argument(help="Comment ID to accept as answer"),
):
    """Accept a comment as the answer."""
    EdClient().comments.accept(thread_id, comment_id)
    console.print(f"Comment {comment_id} accepted as answer for thread {thread_id}.")
```

`src/ed_api/cli/files.py`:
```python
"""Files CLI commands."""

import json
import typer
from rich.console import Console
from ed_api.client import EdClient

app = typer.Typer(help="File commands.")
console = Console()


@app.command()
def upload(
    file_path: str = typer.Argument(help="Path to file to upload"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Upload a file to Ed."""
    client = EdClient()
    url = client.files.upload_from_path(file_path)
    if json_output:
        print(json.dumps({"url": url}))
    else:
        console.print(f"Uploaded: {url}")
```

`src/ed_api/cli/content.py`:
```python
"""Content conversion CLI commands."""

import json
import typer
from rich.console import Console
from ed_api.content import markdown_to_ed_xml, ed_xml_to_markdown

app = typer.Typer(help="Content conversion commands.")
console = Console()


@app.command(name="to-xml")
def to_xml(
    markdown: str = typer.Argument(help="Markdown text to convert"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Convert markdown to Ed XML."""
    xml = markdown_to_ed_xml(markdown)
    if json_output:
        print(json.dumps({"xml": xml}))
    else:
        console.print(xml)


@app.command(name="to-markdown")
def to_markdown(
    xml: str = typer.Argument(help="Ed XML to convert"),
    json_output: bool = typer.Option(False, "--json"),
):
    """Convert Ed XML to markdown."""
    md = ed_xml_to_markdown(xml)
    if json_output:
        print(json.dumps({"markdown": md}))
    else:
        console.print(md)
```

- [ ] **Step 2: Write CLI tests**

`tests/test_cli.py`:
```python
from typer.testing import CliRunner
from ed_api.cli.main import app
from ed_api.content import markdown_to_ed_xml, ed_xml_to_markdown

runner = CliRunner()


class TestContentCLI:
    def test_to_xml(self):
        result = runner.invoke(app, ["content", "to-xml", "Hello **world**", "--json"])
        assert result.exit_code == 0
        assert "document" in result.stdout

    def test_to_markdown(self):
        xml = '<document version="2.0"><paragraph>Hello</paragraph></document>'
        result = runner.invoke(app, ["content", "to-markdown", xml, "--json"])
        assert result.exit_code == 0
        assert "Hello" in result.stdout


class TestCLIHelp:
    def test_main_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "ed-api" in result.stdout.lower() or "edstem" in result.stdout.lower()

    def test_threads_help(self):
        result = runner.invoke(app, ["threads", "--help"])
        assert result.exit_code == 0

    def test_comments_help(self):
        result = runner.invoke(app, ["comments", "--help"])
        assert result.exit_code == 0
```

- [ ] **Step 3: Run all tests**

Run: `uv run pytest -v`

- [ ] **Step 4: Commit**

```bash
git add src/ed_api/cli/ tests/test_cli.py
git commit -m "feat: Typer CLI with --json output for all commands"
```

---

### Task 9: Full Test Suite + Push

- [ ] **Step 1: Run the complete test suite**

Run: `uv run pytest -v`
Expected: All tests pass.

- [ ] **Step 2: Verify CLI help works**

```bash
uv run ed-api --help
uv run ed-api threads --help
uv run ed-api content to-xml "## Hello" --json
```

- [ ] **Step 3: Push to GitHub**

```bash
cd E:/workspaces/school/gt/ed-api
git push
```

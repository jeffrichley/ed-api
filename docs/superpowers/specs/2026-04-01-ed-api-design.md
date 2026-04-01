# ed-api: EdStem API Client — Design Spec

## Overview

A full-featured Python client for the EdStem API. Covers all known endpoints
(reverse-engineered from the EdStem web app, cross-referenced with edstem-mcp's
22-tool coverage). Designed for reuse by anyone using EdStem, not specific to any
course or use case.

## Tech Stack

| Component | Choice |
|-----------|--------|
| Package manager | uv |
| CLI framework | Typer |
| Logging | Rich |
| HTTP client | httpx (async support for future service mode) |
| Output modes | Rich (human) / JSON (machine, via `--json` flag) |

## API Token Management

- Token sourced from (in priority order):
  1. Constructor argument: `EdClient(token="...")`
  2. Environment variable: `ED_API_TOKEN`
  3. `.env` file in working directory
- Token is a Bearer token passed in the `Authorization` header
- Token creation URL: https://edstem.org/us/settings/api-tokens
- Region support: `ED_REGION` env var (default: `us`, also: `au`, `ca`, `eu`, `uk`)
- Base URL constructed from region: `https://{region}.edstem.org/api/`

## Python API

### Client Structure

```python
from ed_api import EdClient

client = EdClient(token="...", region="us")

# Namespaced by resource
client.user         # User operations
client.courses      # Course operations
client.threads      # Thread operations
client.comments     # Comment operations
client.files        # File operations
```

### User Operations

```python
client.user.info() -> UserInfo
client.user.activity(course_id, limit=30, offset=0, filter="all") -> list[ActivityItem]
```

### Course Operations

```python
client.courses.list() -> list[Course]
client.courses.get(course_id) -> Course
client.courses.users(course_id) -> list[CourseUser]
client.courses.users(course_id, role="staff") -> list[CourseUser]  # filter by role
```

### Thread Operations

```python
client.threads.list(course_id, limit=100, offset=0, sort="new") -> list[Thread]
client.threads.get(thread_id) -> ThreadDetail  # includes comments
client.threads.get_by_number(course_id, thread_number) -> ThreadDetail
client.threads.search(course_id, query) -> list[Thread]
client.threads.create(course_id, params: CreateThreadParams) -> Thread
client.threads.edit(thread_id, params: EditThreadParams) -> Thread
client.threads.lock(thread_id) -> None
client.threads.unlock(thread_id) -> None
client.threads.pin(thread_id) -> None
client.threads.unpin(thread_id) -> None
client.threads.set_private(thread_id, private=True) -> None
client.threads.endorse(thread_id) -> None
client.threads.unendorse(thread_id) -> None
client.threads.star(thread_id) -> None
client.threads.unstar(thread_id) -> None
```

### Comment Operations

```python
client.comments.post(thread_id, content, is_answer=False) -> Comment
client.comments.reply(comment_id, content) -> Comment
client.comments.edit(comment_id, content) -> Comment
client.comments.endorse(comment_id) -> None
client.comments.unendorse(comment_id) -> None
client.comments.accept(comment_id) -> None  # mark as accepted answer
```

### File Operations

```python
client.files.upload(filename, file_bytes, content_type) -> str  # returns URL
client.files.upload_from_path(file_path) -> str  # convenience, auto-detects MIME
```

### Content Conversion

```python
from ed_api.content import markdown_to_ed_xml, ed_xml_to_markdown

xml = markdown_to_ed_xml("## Hello\n\nSome **bold** text")
md = ed_xml_to_markdown('<document version="2.0"><heading level="2">Hello</heading>...')
```

EdStem uses a custom XML format for post bodies. All public-facing APIs in ed-api
accept and return markdown. The XML conversion is internal but exposed for advanced use.

### Data Models

All models are dataclasses with full type hints.

```python
@dataclass
class Thread:
    id: int
    course_id: int
    number: int                    # course-local thread number (the # in the UI)
    type: str                      # "question", "post", "announcement"
    title: str
    content: str                   # markdown (converted from Ed XML)
    category: str
    subcategory: str | None
    author: UserSummary
    is_pinned: bool
    is_private: bool
    is_locked: bool
    is_endorsed: bool
    is_answered: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class ThreadDetail(Thread):
    comments: list[Comment]

@dataclass
class Comment:
    id: int
    thread_id: int
    parent_id: int | None          # None = top-level, set = reply
    author: UserSummary
    content: str                   # markdown
    is_answer: bool
    is_endorsed: bool
    is_accepted: bool
    created_at: datetime

@dataclass
class UserSummary:
    id: int
    name: str
    role: str                      # "student", "staff", "admin"

@dataclass
class CourseUser(UserSummary):
    email: str

@dataclass
class Course:
    id: int
    code: str
    name: str
    year: str
    session: str
    status: str                    # "active" or "archived"
```

### Helper Methods

```python
# Thread status helpers (used by ed-bot)
thread = client.threads.get(342)

thread.is_unanswered        # no comments at all
thread.has_staff_response    # at least one comment from staff/admin
thread.has_student_only      # comments exist but none from staff
thread.needs_followup        # staff answered but student replied after
```

## CLI

Every command supports `--json` for machine-readable output.

```bash
# Auth
ed-api auth check                          # verify token is valid
ed-api auth whoami                         # show current user info

# Courses
ed-api courses list
ed-api courses users 12345
ed-api courses users 12345 --role staff

# Threads
ed-api threads list 12345                  # list threads in course
ed-api threads list 12345 --limit 50 --sort new
ed-api threads get 342                     # get thread by global ID
ed-api threads get 12345:42                # get thread by course:number
ed-api threads search 12345 "bollinger bands"
ed-api threads create 12345 --title "..." --body "..." --category "General"
ed-api threads edit 342 --title "New Title"
ed-api threads lock 342
ed-api threads unlock 342
ed-api threads pin 342
ed-api threads unpin 342
ed-api threads private 342
ed-api threads public 342
ed-api threads endorse 342
ed-api threads unendorse 342

# Comments
ed-api comments post 342 --body "Here's the answer..."
ed-api comments post 342 --body "..." --answer        # post as answer
ed-api comments reply 98765 --body "Follow-up..."
ed-api comments endorse 98765
ed-api comments unendorse 98765
ed-api comments accept 98765                           # accept as answer

# Files
ed-api files upload ./screenshot.png

# Content
ed-api content to-xml "## Hello\n\nSome text"
ed-api content to-markdown '<document version="2.0">...'
```

## Error Handling

```python
from ed_api.exceptions import (
    EdAuthError,       # invalid or expired token
    EdNotFoundError,   # thread/comment/course not found
    EdForbiddenError,  # insufficient permissions
    EdRateLimitError,  # rate limited by EdStem
    EdAPIError,        # generic API error
)
```

All exceptions include the HTTP status code and the raw response body for debugging.

## Rate Limiting

EdStem's rate limits are undocumented. The client includes:
- Automatic retry with exponential backoff on 429 responses
- Configurable rate limiter: `EdClient(rate_limit=10)` (requests per second)
- Default: 5 requests/second (conservative)

## Pagination Helper

```python
# Iterate all threads without manual offset management
for thread in client.threads.list_all(course_id=12345):
    print(thread.title)
```

`list_all()` is a generator that handles pagination internally, yielding one
thread at a time. Available on `threads.list_all()` and `user.activity_all()`.

## Project Structure

```
ed-api/
├── pyproject.toml
├── README.md
├── src/
│   └── ed_api/
│       ├── __init__.py          # Public API: EdClient
│       ├── client.py            # EdClient main class
│       ├── resources/
│       │   ├── __init__.py
│       │   ├── user.py          # UserResource
│       │   ├── courses.py       # CoursesResource
│       │   ├── threads.py       # ThreadsResource
│       │   ├── comments.py      # CommentsResource
│       │   └── files.py         # FilesResource
│       ├── models.py            # Dataclasses
│       ├── content.py           # Markdown ↔ Ed XML conversion
│       ├── exceptions.py        # Exception classes
│       ├── pagination.py        # Pagination helpers
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py          # Typer app entry point
│       │   ├── auth.py
│       │   ├── courses.py
│       │   ├── threads.py
│       │   ├── comments.py
│       │   ├── files.py
│       │   └── content.py
│       └── _http.py             # HTTP client wrapper (rate limiting, retries)
└── tests/
    ├── test_client.py
    ├── test_content.py
    ├── test_models.py
    └── fixtures/
        └── sample_responses/    # Recorded API responses for testing
```

## References

- [edstem-mcp](https://github.com/rob-9/edstem-mcp) — 22-tool MCP server, TypeScript.
  Used as reference for complete endpoint list and markdown→XML conversion.
- [edapi](https://github.com/smartspot2/edapi) — Existing Python client (incomplete).
  Used as reference for API endpoint URLs and response types.
- [edapi docs/api_docs.md](https://github.com/smartspot2/edapi/blob/master/docs/api_docs.md)
  — Reverse-engineered endpoint documentation and Ed XML format reference.

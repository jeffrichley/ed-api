# Python API Reference

## EdClient

The main entry point for the library.

```python
from ed_api import EdClient
```

### Constructor

```python
EdClient(
    token: str | None = None,
    region: str | None = None,
    rate_limit: float = 5.0,
)
```

| Parameter | Default | Description |
|---|---|---|
| `token` | `None` | API token. Falls back to `ED_API_TOKEN` env var or `.env` file. |
| `region` | `None` | EdStem region (`"us"` or `"au"`). Falls back to `ED_REGION` env var, then `"us"`. |
| `rate_limit` | `5.0` | Maximum requests per second. |

Raises `ValueError` if no token is found from any source.

### Resources

| Attribute | Type | Description |
|---|---|---|
| `client.user` | `UserResource` | Current user info |
| `client.courses` | `CoursesResource` | Course and enrollment operations |
| `client.threads` | `ThreadsResource` | Thread CRUD and moderation |
| `client.comments` | `CommentsResource` | Comment operations |
| `client.files` | `FilesResource` | File uploads |

### Methods

```python
client.close() -> None
```

Closes the underlying HTTP connection pool. Called automatically when used as a context manager.

### Context manager

```python
with EdClient() as client:
    threads = client.threads.list(course_id=12345)
# HTTP connection is closed here automatically
```

---

## UserResource

```python
client.user
```

### Methods

```python
user.info() -> ParsedUserInfo
```

Returns full user info including enrolled courses.

---

## CoursesResource

```python
client.courses
```

### Methods

```python
courses.list() -> list[CourseEnrollment]
```

List all courses the current user is enrolled in.

```python
courses.users(course_id: int, role: str | None = None) -> list[CourseUser]
```

List users in a course. Pass `role="student"`, `role="staff"`, or `role="admin"` to filter.

---

## ThreadsResource

```python
client.threads
```

### Methods

```python
threads.list(
    course_id: int,
    limit: int = 100,
    offset: int = 0,
    sort: str = "new",
) -> list[Thread]
```

List threads in a course. `sort` accepts `"new"`, `"top"`, `"unanswered"`.

```python
threads.list_all(
    course_id: int,
    sort: str = "new",
) -> Generator[Thread, None, None]
```

Generator that paginates through all threads. Yields one `Thread` at a time.

```python
threads.get(thread_id: int) -> ThreadDetail
```

Get a thread by its global ID, including all comments.

```python
threads.get_by_number(course_id: int, thread_number: int) -> ThreadDetail
```

Get a thread by its course-local number (the `#N` displayed in the UI).

```python
threads.search(course_id: int, query: str, limit: int = 100) -> list[Thread]
```

Search threads by title and category (client-side, fetches all threads).

```python
threads.create(
    course_id: int,
    title: str,
    body: str,
    type: str = "question",
    category: str = "",
    is_private: bool = False,
    is_anonymous: bool = False,
) -> Thread
```

Create a new thread. `body` is Markdown, converted to Ed XML automatically.

```python
threads.edit(
    thread_id: int,
    title: str | None = None,
    body: str | None = None,
    category: str | None = None,
    is_private: bool | None = None,
) -> Thread
```

Edit a thread. Only provided fields are updated; others are preserved.

```python
threads.lock(thread_id: int) -> None
threads.unlock(thread_id: int) -> None
threads.pin(thread_id: int) -> None
threads.unpin(thread_id: int) -> None
threads.endorse(thread_id: int) -> None
threads.unendorse(thread_id: int) -> None
threads.star(thread_id: int) -> None
threads.unstar(thread_id: int) -> None
threads.set_private(thread_id: int, private: bool = True) -> None
threads.delete(thread_id: int) -> None
```

---

## CommentsResource

```python
client.comments
```

### Methods

```python
comments.post(
    thread_id: int,
    content: str,
    is_answer: bool = False,
    is_private: bool = False,
    is_anonymous: bool = False,
) -> Comment
```

Post a comment on a thread. `content` is Markdown.

```python
comments.reply(
    comment_id: int,
    content: str,
    is_private: bool = False,
    is_anonymous: bool = False,
) -> Comment
```

Reply to an existing comment. `content` is Markdown.

```python
comments.edit(comment_id: int, content: str) -> Comment
```

Edit a comment. `content` is Markdown.

```python
comments.endorse(comment_id: int) -> None
comments.unendorse(comment_id: int) -> None
comments.accept(comment_id: int) -> None
comments.delete(comment_id: int) -> None
```

---

## FilesResource

```python
client.files
```

### Methods

```python
files.upload(filename: str, file_bytes: bytes, content_type: str) -> str
```

Upload raw bytes. Returns the static CDN URL.

```python
files.upload_from_path(file_path: str | pathlib.Path) -> str
```

Upload a file from disk. MIME type is auto-detected. Returns the static CDN URL.

---

## Content conversion functions

```python
from ed_api.content import markdown_to_ed_xml, ed_xml_to_markdown
```

```python
markdown_to_ed_xml(md: str) -> str
```

Convert Markdown text to Ed's XML document format. Supports headings, bold, italic, inline code, fenced code blocks, ordered/unordered lists, and links.

```python
ed_xml_to_markdown(xml: str) -> str
```

Convert Ed's XML document format to Markdown. Handles all standard Ed XML tags.

---

## Data Models

All models are Python `dataclass` instances.

### Thread

```python
@dataclass
class Thread:
    id: int
    course_id: int
    number: int
    type: str                    # "question" | "post" | "announcement"
    title: str
    content: str                 # Ed XML
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
    view_count: int
    vote_count: int
    reply_count: int
```

### ThreadDetail

Extends `Thread` with comments and user map:

```python
@dataclass
class ThreadDetail(Thread):
    comments: list[Comment]
    users: dict[int, UserSummary]

    # Computed properties:
    @property
    def is_unanswered(self) -> bool: ...
    @property
    def has_staff_response(self) -> bool: ...
    @property
    def has_student_only(self) -> bool: ...
    @property
    def needs_followup(self) -> bool: ...
```

`needs_followup` is `True` when a student has commented after the last staff response.

### Comment

```python
@dataclass
class Comment:
    id: int
    thread_id: int
    parent_id: int | None
    user_id: int
    author: UserSummary | None
    type: str                    # "comment" | "answer"
    content: str                 # Ed XML
    is_endorsed: bool
    is_anonymous: bool
    is_private: bool
    created_at: datetime | None
    vote_count: int
    replies: list[Comment]
```

### UserSummary

```python
@dataclass
class UserSummary:
    id: int
    name: str
    role: str                    # "student" | "staff" | "admin"

    @property
    def is_staff(self) -> bool: ...
```

### UserInfo

```python
@dataclass
class UserInfo:
    id: int
    name: str
    email: str
    role: str
    avatar: str | None
```

### ParsedUserInfo

```python
@dataclass
class ParsedUserInfo:
    user: UserInfo
    courses: list[CourseEnrollment]
```

### Course

```python
@dataclass
class Course:
    id: int
    code: str
    name: str
    year: str
    session: str
    status: str                  # "active" | "archived"
```

### CourseEnrollment

```python
@dataclass
class CourseEnrollment:
    course: Course
    role: str                    # "student" | "staff" | "admin"
```

### CourseUser

```python
@dataclass
class CourseUser:
    id: int
    name: str
    email: str
    role: str
    course_role: str             # "student" | "staff" | "admin"

    @property
    def is_staff(self) -> bool: ...
```

---

## Exceptions

All exceptions inherit from `EdAPIError`.

```python
from ed_api.exceptions import (
    EdAPIError,
    EdAuthError,
    EdForbiddenError,
    EdNotFoundError,
    EdRateLimitError,
)
```

### EdAPIError

Base class for all API errors.

```python
class EdAPIError(Exception):
    status_code: int
    response_body: dict
```

### EdAuthError

HTTP 401 — invalid or missing token.

### EdForbiddenError

HTTP 403 — insufficient permissions for the requested operation.

### EdNotFoundError

HTTP 404 — the requested resource does not exist.

### EdRateLimitError

HTTP 429 — rate limited by the server. The HTTP client retries automatically with exponential backoff before raising this.

### Example: handling errors

```python
from ed_api import EdClient
from ed_api.exceptions import EdNotFoundError, EdForbiddenError, EdAuthError

client = EdClient()

try:
    detail = client.threads.get(thread_id=999999)
except EdNotFoundError:
    print("Thread not found.")
except EdForbiddenError:
    print("You don't have permission to view this thread.")
except EdAuthError:
    print("Authentication failed — check your token.")
```

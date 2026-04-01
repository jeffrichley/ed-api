# Threads

Threads are the primary content unit in EdStem — questions, posts, and announcements all live as threads within a course.

## Listing threads

```python
from ed_api import EdClient

client = EdClient()

# Basic listing — returns up to 100 threads by default
threads = client.threads.list(course_id=12345)

# With options
threads = client.threads.list(
    course_id=12345,
    limit=50,
    offset=0,
    sort="new",  # "new" | "top" | "unanswered"
)

for t in threads:
    print(f"#{t.number}: {t.title}")
    print(f"  type={t.type}, category={t.category}")
    print(f"  pinned={t.is_pinned}, private={t.is_private}, locked={t.is_locked}")
    print(f"  answered={t.is_answered}, replies={t.reply_count}")
```

## Iterating all threads (pagination)

`list_all()` is a generator that automatically pages through all threads:

```python
count = 0
for thread in client.threads.list_all(course_id=12345, sort="new"):
    count += 1
    if thread.is_answered:
        print(f"#{thread.number}: {thread.title}")

print(f"Total threads: {count}")
```

This handles courses with thousands of threads efficiently — it fetches 100 at a time and yields each thread as it comes.

## Getting a single thread

By global thread ID (includes comments):

```python
detail = client.threads.get(thread_id=987654)
print(detail.title)
print(f"Author: {detail.author.name}")
print(f"Comments: {len(detail.comments)}")
```

By course-local number (the `#42` style number visible in the EdStem UI):

```python
detail = client.threads.get_by_number(course_id=12345, thread_number=42)
```

`get()` and `get_by_number()` both return `ThreadDetail`, which extends `Thread` with a list of comments and a user map.

## Thread properties

| Property | Type | Description |
|---|---|---|
| `id` | `int` | Global thread ID |
| `course_id` | `int` | Owning course |
| `number` | `int` | Course-local thread number |
| `type` | `str` | `"question"`, `"post"`, `"announcement"` |
| `title` | `str` | Thread title |
| `content` | `str` | Body as Ed XML |
| `category` | `str` | Thread category |
| `subcategory` | `str \| None` | Thread subcategory |
| `author` | `UserSummary` | Thread author |
| `is_pinned` | `bool` | Pinned to top |
| `is_private` | `bool` | Visible to staff only |
| `is_locked` | `bool` | Replies disabled |
| `is_endorsed` | `bool` | Endorsed by staff |
| `is_answered` | `bool` | Has an accepted answer |
| `is_staff_answered` | `bool` | Staff has responded |
| `is_student_answered` | `bool` | A student has responded |
| `created_at` | `datetime \| None` | Creation time (UTC) |
| `updated_at` | `datetime \| None` | Last update time (UTC) |
| `view_count` | `int` | Number of views |
| `vote_count` | `int` | Number of votes |
| `reply_count` | `int` | Number of replies |

## ThreadDetail extra properties

`ThreadDetail` inherits all `Thread` fields and adds:

| Property | Type | Description |
|---|---|---|
| `comments` | `list[Comment]` | All comments and answers |
| `users` | `dict[int, UserSummary]` | User map (id → summary) |
| `is_unanswered` | `bool` | True if no comments at all |
| `has_staff_response` | `bool` | True if any comment is from staff |
| `has_student_only` | `bool` | Comments exist but none from staff |
| `needs_followup` | `bool` | Student posted after last staff response |

## Searching threads

`search()` performs client-side filtering across all threads in a course:

```python
results = client.threads.search(course_id=12345, query="assignment 3")
for t in results:
    print(f"#{t.number}: {t.title} [{t.category}]")
```

!!! note "Client-side search"
    `search()` fetches all threads via `list_all()` and filters by title and category. For large courses, this may make many API requests.

## Creating a thread

Body content is written in Markdown and automatically converted to Ed XML:

```python
thread = client.threads.create(
    course_id=12345,
    title="Assignment 3 clarification",
    body="Can someone clarify what format the output should be in?\n\n- Option A\n- Option B",
    type="question",       # "question" | "post" | "announcement"
    category="Assignments",
    is_private=False,
    is_anonymous=False,
)
print(f"Created #{thread.number}: {thread.title} (id={thread.id})")
```

## Editing a thread

Only provide the fields you want to change — unchanged fields are preserved:

```python
thread = client.threads.edit(
    thread_id=987654,
    title="Updated title",
    body="Updated body in **Markdown**.",
    category="General",
    is_private=True,
)
```

`edit()` fetches the current thread state, merges your changes, and sends the full object back to the API.

## Moderation actions

These operations return `None` on success and raise on error.

### Lock and unlock

Locking prevents new replies:

```python
client.threads.lock(thread_id=987654)
client.threads.unlock(thread_id=987654)
```

### Pin and unpin

Pinned threads appear at the top of the thread list:

```python
client.threads.pin(thread_id=987654)
client.threads.unpin(thread_id=987654)
```

### Private and public

```python
client.threads.set_private(thread_id=987654, private=True)
client.threads.set_private(thread_id=987654, private=False)
```

### Endorse and unendorse

```python
client.threads.endorse(thread_id=987654)
client.threads.unendorse(thread_id=987654)
```

### Star and unstar

```python
client.threads.star(thread_id=987654)
client.threads.unstar(thread_id=987654)
```

## Deleting a thread

```python
client.threads.delete(thread_id=987654)
```

!!! danger "Deletion is permanent"
    Deleted threads cannot be recovered through the API.

## Working with thread content

Thread bodies are stored as Ed XML. Use the content module to convert:

```python
from ed_api.content import ed_xml_to_markdown

detail = client.threads.get(thread_id=987654)
body_md = ed_xml_to_markdown(detail.content)
print(body_md)
```

See [Content Conversion](content.md) for full details.

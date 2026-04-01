# Quick Start

This guide walks you through the most common operations using ed-api.

## Prerequisites

- ed-api installed (see [Installation](installation.md))
- `ED_API_TOKEN` set in your environment or `.env` file

## 1. Authenticate

Verify your token works:

```bash
ed-api auth check
```

See who you are:

```bash
ed-api auth whoami
```

In Python:

```python
from ed_api import EdClient

client = EdClient()
info = client.user.info()
print(f"Hello, {info.user.name}!")
print(f"Email: {info.user.email}")
```

## 2. List your courses

```bash
ed-api courses list
```

```python
from ed_api import EdClient

client = EdClient()
for enrollment in client.courses.list():
    course = enrollment.course
    print(f"{course.id}: {course.code} — {course.name} ({enrollment.role})")
```

Sample output:

```
12345: CS101 — Introduction to Computer Science (staff)
12346: CS201 — Data Structures (student)
```

## 3. Browse threads

List recent threads in a course (replace `12345` with your course ID):

```bash
ed-api threads list 12345 --limit 10
```

```python
threads = client.threads.list(course_id=12345, limit=10, sort="new")
for t in threads:
    status = "answered" if t.is_answered else "open"
    print(f"#{t.number}: {t.title} [{status}] — {t.reply_count} replies")
```

## 4. Read a thread

Get a thread by its course-local number:

```bash
ed-api threads get 12345:42
```

Get by global thread ID:

```bash
ed-api threads get 987654
```

```python
detail = client.threads.get_by_number(course_id=12345, thread_number=42)
print(detail.title)
print(f"Posted by: {detail.author.name}")
print(f"Comments: {len(detail.comments)}")

# Access comments
for comment in detail.comments:
    author = detail.users.get(comment.user_id)
    name = author.name if author else "Unknown"
    print(f"  [{comment.type}] {name}: {comment.is_endorsed and '(endorsed)' or ''}")
```

## 5. Post a comment

Comments are written in Markdown — ed-api converts to Ed XML automatically:

```bash
ed-api comments post 987654 --body "Thanks for the great question! The answer is **yes**."
```

Post as an answer (staff feature):

```bash
ed-api comments post 987654 --body "Here is the solution." --answer
```

```python
comment = client.comments.post(
    thread_id=987654,
    content="Thanks for the question!\n\nHere's a code example:\n\n```python\nx = 42\n```",
    is_answer=False,
)
print(f"Posted comment id={comment.id}")
```

## 6. Create a thread

```bash
ed-api threads create 12345 \
  --title "Office hours tomorrow cancelled" \
  --body "Hi everyone, office hours are cancelled tomorrow." \
  --type announcement \
  --category General
```

```python
thread = client.threads.create(
    course_id=12345,
    title="Where is the assignment rubric?",
    body="I can't find the rubric for Assignment 3. Could someone point me to it?",
    type="question",
    category="Assignments",
)
print(f"Created thread #{thread.number}: {thread.title}")
```

## 7. Search threads

```bash
ed-api threads search 12345 "assignment rubric"
```

```python
results = client.threads.search(course_id=12345, query="rubric")
for t in results:
    print(f"#{t.number}: {t.title}")
```

## Using as a context manager

The recommended pattern for scripts — automatically closes the HTTP connection:

```python
from ed_api import EdClient

with EdClient() as client:
    courses = client.courses.list()
    for enrollment in courses:
        threads = list(client.threads.list_all(enrollment.course.id))
        print(f"{enrollment.course.name}: {len(threads)} threads")
```

## JSON output

Every CLI command supports `--json` for piping to `jq` or other tools:

```bash
ed-api threads list 12345 --json | jq '.[] | select(.is_answered == false) | .title'
```

```bash
ed-api auth whoami --json | jq '.courses[].id'
```

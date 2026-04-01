# Comments

Comments are responses to threads. EdStem distinguishes between regular comments and answers — answers can be endorsed as the official solution to a question thread.

## Posting a comment

Comment bodies are written in Markdown and automatically converted to Ed XML:

```python
from ed_api import EdClient

client = EdClient()

comment = client.comments.post(
    thread_id=987654,
    content="Thanks for the question! Here's what you need to know.",
)
print(f"Posted comment id={comment.id}")
```

### Post as an answer

For question threads, you can post a response as an "answer" (appears in a distinct section in the EdStem UI):

```python
comment = client.comments.post(
    thread_id=987654,
    content="The correct approach is:\n\n```python\nresult = [x**2 for x in range(10)]\n```",
    is_answer=True,
)
```

### Post privately

Private comments are visible only to staff and the thread author:

```python
comment = client.comments.post(
    thread_id=987654,
    content="This is a private note visible only to staff.",
    is_private=True,
)
```

### Post anonymously

```python
comment = client.comments.post(
    thread_id=987654,
    content="Anonymous comment here.",
    is_anonymous=True,
)
```

## Replying to a comment

Nest a reply under an existing comment:

```python
reply = client.comments.reply(
    comment_id=111222,
    content="Thanks, that clarifies it!",
)
print(f"Replied with comment id={reply.id}")
```

Reply options:

```python
reply = client.comments.reply(
    comment_id=111222,
    content="Private follow-up.",
    is_private=True,
    is_anonymous=False,
)
```

## Editing a comment

Edit replaces the comment body. Pass Markdown — it is converted to Ed XML:

```python
updated = client.comments.edit(
    comment_id=111222,
    content="Corrected answer: the result is `42`, not `41`.",
)
```

## Comment properties

| Property | Type | Description |
|---|---|---|
| `id` | `int` | Global comment ID |
| `thread_id` | `int` | Parent thread |
| `parent_id` | `int \| None` | Parent comment (for replies) |
| `user_id` | `int` | Author user ID |
| `author` | `UserSummary \| None` | Resolved author (if available) |
| `type` | `str` | `"comment"` or `"answer"` |
| `content` | `str` | Body as Ed XML |
| `is_endorsed` | `bool` | Endorsed by staff |
| `is_anonymous` | `bool` | Posted anonymously |
| `is_private` | `bool` | Visible to staff only |
| `created_at` | `datetime \| None` | Creation time (UTC) |
| `vote_count` | `int` | Number of votes |
| `replies` | `list[Comment]` | Nested replies |

## Endorsing and unendorsing

Endorsement marks a comment as a high-quality response (staff action):

```python
client.comments.endorse(comment_id=111222)
client.comments.unendorse(comment_id=111222)
```

## Accepting as the answer

Accept marks a comment as the definitive answer to the thread question:

```python
client.comments.accept(comment_id=111222)
```

This sets `thread.is_answered = True` on the parent thread.

## Deleting a comment

```python
client.comments.delete(comment_id=111222)
```

!!! danger "Deletion is permanent"
    Deleted comments cannot be recovered.

## Accessing comments via ThreadDetail

When you fetch a thread with `get()` or `get_by_number()`, comments come pre-loaded:

```python
detail = client.threads.get_by_number(course_id=12345, thread_number=10)

for comment in detail.comments:
    # Resolve author from the thread's user map
    author = detail.users.get(comment.user_id)
    name = author.name if author else f"User {comment.user_id}"
    role = author.role if author else "unknown"

    print(f"[{comment.type}] by {name} ({role})")
    print(f"  endorsed={comment.is_endorsed}, replies={len(comment.replies)}")

    # Access nested replies
    for reply in comment.replies:
        reply_author = detail.users.get(reply.user_id)
        print(f"    -> {reply_author.name if reply_author else 'unknown'}: reply")
```

## Converting comment content

Comment bodies are Ed XML. Convert to Markdown for display:

```python
from ed_api.content import ed_xml_to_markdown

for comment in detail.comments:
    md = ed_xml_to_markdown(comment.content)
    print(md)
```

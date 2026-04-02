<div class="iris-hero" markdown>

# ed-api

Full-featured Python client for the EdStem API

[Get Started](getting-started/installation.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/jeffrichley/ed-api){ .md-button }

</div>

<div class="iris-cards" markdown>

<div class="iris-card" markdown>

### Typed Models

All API responses are parsed into strongly-typed Python dataclasses — `Thread`, `Comment`, `Course`, `UserSummary`, and more. No raw dictionaries.

</div>

<div class="iris-card" markdown>

### Markdown-Native

Write posts and comments in standard Markdown. ed-api automatically converts to EdStem's XML format on the way in, and back to Markdown on the way out.

</div>

<div class="iris-card" markdown>

### Rate Limiting

Built-in token-bucket rate limiting (default: 5 req/s) with automatic exponential backoff on 429 responses. Protect your account from throttling.

</div>

<div class="iris-card" markdown>

### Dual-Mode CLI

Every operation available as both a Python API and a Typer CLI command. Rich terminal output by default; pass `--json` anywhere for machine-readable output.

</div>

<div class="iris-card" markdown>

### Resource-Based

Clean resource namespaces: `client.threads`, `client.comments`, `client.courses`, `client.files`, `client.lessons`, `client.user`. Mirrors how EdStem organizes its API.

</div>

<div class="iris-card" markdown>

### Lessons & Slides

Browse course lessons and slides — list modules, retrieve individual slides, and pull all video slide URLs (Kaltura) for a course with `client.lessons`.

</div>

<div class="iris-card" markdown>

### Content Conversion

`markdown_to_ed_xml()` and `ed_xml_to_markdown()` handle headings, bold, italic, inline code, fenced code blocks, ordered/unordered lists, and links.

</div>

</div>

## Quick Example

```python
from ed_api import EdClient

with EdClient() as client:  # token from ED_API_TOKEN env var
    # List your courses
    for enrollment in client.courses.list():
        print(enrollment.course.name, enrollment.role)

    # List threads in a course
    threads = client.threads.list(course_id=12345, limit=20)
    for t in threads:
        print(f"#{t.number}: {t.title} ({t.reply_count} replies)")

    # Get a specific thread with comments
    detail = client.threads.get_by_number(course_id=12345, thread_number=42)
    print(detail.title)
    for comment in detail.comments:
        print(f"  - {comment.type} by user {comment.user_id}")

    # Post a comment (Markdown is auto-converted to Ed XML)
    comment = client.comments.post(
        thread_id=detail.id,
        content="Great question! Here's the answer:\n\n```python\nprint('hello')\n```",
    )
    print(f"Posted comment id={comment.id}")
```

## Installation

```bash
pip install ed-api
# or with uv
uv add ed-api
```

Set your token:

```bash
export ED_API_TOKEN=your_token_here
# or create a .env file
echo "ED_API_TOKEN=your_token_here" > .env
```

See the [Installation guide](getting-started/installation.md) for full details.

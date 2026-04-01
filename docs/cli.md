# CLI Reference

ed-api ships with a full Typer CLI. All commands support `--json` for machine-readable output.

## Installation

The `ed-api` command is available after installing the package:

```bash
pip install ed-api
# or
uv add ed-api
```

## Global usage

```
ed-api [GROUP] [COMMAND] [ARGS] [OPTIONS]
```

Add `--help` to any command for inline documentation:

```bash
ed-api --help
ed-api threads --help
ed-api threads list --help
```

---

## auth — Authentication

### `auth check`

Verify the API token is valid.

```bash
ed-api auth check
ed-api auth check --json
```

**Output (default):**
```
Token valid. Logged in as Jane Smith
```

**Output (--json):**
```json
{"status": "ok", "user": "Jane Smith"}
```

**Error output (--json):**
```json
{"status": "error", "message": "Authentication failed"}
```

---

### `auth whoami`

Show current user info and enrolled courses.

```bash
ed-api auth whoami
ed-api auth whoami --json
```

**Output (--json):**
```json
{
  "id": 1234,
  "name": "Jane Smith",
  "email": "jane@example.com",
  "courses": [
    {"id": 12345, "code": "CS101", "name": "Intro to CS", "role": "staff"}
  ]
}
```

---

## courses — Course management

### `courses list`

List all enrolled courses.

```bash
ed-api courses list
ed-api courses list --json
```

**Output (--json):**
```json
[
  {
    "id": 12345,
    "code": "CS101",
    "name": "Introduction to Computer Science",
    "year": "2025",
    "session": "Spring",
    "role": "staff"
  }
]
```

---

### `courses users COURSE_ID`

List users enrolled in a course.

```bash
ed-api courses users 12345
ed-api courses users 12345 --role staff
ed-api courses users 12345 --role student
ed-api courses users 12345 --json
```

**Options:**

| Option | Description |
|---|---|
| `--role TEXT` | Filter by role: `student`, `staff`, `admin` |
| `--json` | JSON output |

**Output (--json):**
```json
[
  {"id": 9001, "name": "Alice Lee", "email": "alice@example.com", "role": "student"}
]
```

---

## threads — Thread operations

### `threads list COURSE_ID`

List threads in a course.

```bash
ed-api threads list 12345
ed-api threads list 12345 --limit 50
ed-api threads list 12345 --sort top
ed-api threads list 12345 --no-pinned
ed-api threads list 12345 --json
```

**Options:**

| Option | Default | Description |
|---|---|---|
| `--limit INT` | `30` | Number of threads to fetch |
| `--sort TEXT` | `new` | Sort: `new`, `top`, `unanswered` |
| `--no-pinned` | `False` | Exclude pinned threads |
| `--json` | `False` | JSON output |

**Output (--json):**
```json
[
  {
    "id": 987654,
    "number": 42,
    "title": "Where is the assignment rubric?",
    "type": "question",
    "category": "Assignments",
    "is_answered": false,
    "is_pinned": false,
    "reply_count": 3,
    "created_at": "2025-03-01 14:23:00+00:00"
  }
]
```

---

### `threads get THREAD_REF`

Get a thread with all comments.

```bash
# By global thread ID
ed-api threads get 987654

# By course_id:thread_number
ed-api threads get 12345:42

ed-api threads get 12345:42 --json
```

**Output (--json):**
```json
{
  "id": 987654,
  "number": 42,
  "title": "Where is the rubric?",
  "content": "<document version=\"2.0\">...</document>",
  "category": "Assignments",
  "is_answered": false,
  "comments": [
    {"id": 111, "type": "comment", "content": "...", "is_endorsed": false, "user_id": 9001}
  ]
}
```

---

### `threads create COURSE_ID`

Create a new thread.

```bash
ed-api threads create 12345 \
  --title "Assignment 3 question" \
  --body "Can someone clarify the output format?" \
  --type question \
  --category Assignments

ed-api threads create 12345 \
  --title "Office hours cancelled" \
  --body "No office hours this Friday." \
  --type announcement \
  --private \
  --json
```

**Options:**

| Option | Default | Description |
|---|---|---|
| `--title TEXT` | required | Thread title |
| `--body TEXT` | required | Thread body (Markdown) |
| `--type TEXT` | `question` | `question`, `post`, `announcement` |
| `--category TEXT` | `General` | Thread category |
| `--private` | `False` | Create as private |
| `--json` | `False` | JSON output |

---

### `threads edit THREAD_ID`

Edit an existing thread.

```bash
ed-api threads edit 987654 --title "Updated title"
ed-api threads edit 987654 --body "New body text."
ed-api threads edit 987654 --category "General" --json
```

**Options:**

| Option | Description |
|---|---|
| `--title TEXT` | New title (optional) |
| `--body TEXT` | New body in Markdown (optional) |
| `--category TEXT` | New category (optional) |
| `--json` | JSON output |

---

### `threads search COURSE_ID QUERY`

Search threads by title and category.

```bash
ed-api threads search 12345 "assignment rubric"
ed-api threads search 12345 "final exam" --json
```

**Output (--json):**
```json
[
  {"id": 987654, "number": 42, "title": "Where is the rubric?", "category": "Assignments"}
]
```

---

### `threads lock THREAD_ID`

Lock a thread (disables new replies).

```bash
ed-api threads lock 987654
```

---

### `threads unlock THREAD_ID`

Unlock a locked thread.

```bash
ed-api threads unlock 987654
```

---

### `threads pin THREAD_ID`

Pin a thread to the top of the list.

```bash
ed-api threads pin 987654
```

---

### `threads unpin THREAD_ID`

Unpin a pinned thread.

```bash
ed-api threads unpin 987654
```

---

### `threads private THREAD_ID`

Mark a thread as private (visible only to staff).

```bash
ed-api threads private 987654
```

---

### `threads public THREAD_ID`

Mark a private thread as public.

```bash
ed-api threads public 987654
```

---

### `threads endorse THREAD_ID`

Endorse a thread.

```bash
ed-api threads endorse 987654
```

---

### `threads unendorse THREAD_ID`

Remove endorsement from a thread.

```bash
ed-api threads unendorse 987654
```

---

### `threads delete THREAD_ID`

Delete a thread permanently.

```bash
ed-api threads delete 987654
```

---

## comments — Comment operations

### `comments post THREAD_ID`

Post a comment on a thread.

```bash
ed-api comments post 987654 --body "Great question!"
ed-api comments post 987654 --body "The answer is 42." --answer
ed-api comments post 987654 --body "Private note." # no --answer flag
ed-api comments post 987654 --body "Posted." --json
```

**Options:**

| Option | Default | Description |
|---|---|---|
| `--body TEXT` | required | Comment body (Markdown) |
| `--answer` | `False` | Post as an answer |
| `--json` | `False` | JSON output |

**Output (--json):**
```json
{"id": 111222, "type": "comment", "thread_id": 987654}
```

---

### `comments reply COMMENT_ID`

Reply to an existing comment.

```bash
ed-api comments reply 111222 --body "Thanks for clarifying!"
ed-api comments reply 111222 --body "Follow-up question..." --json
```

**Options:**

| Option | Description |
|---|---|
| `--body TEXT` | Reply body (Markdown) |
| `--json` | JSON output |

---

### `comments endorse COMMENT_ID`

Endorse a comment (staff action).

```bash
ed-api comments endorse 111222
```

---

### `comments unendorse COMMENT_ID`

Remove endorsement from a comment.

```bash
ed-api comments unendorse 111222
```

---

### `comments accept COMMENT_ID`

Accept a comment as the answer to its thread question.

```bash
ed-api comments accept 111222
```

---

### `comments delete COMMENT_ID`

Delete a comment permanently.

```bash
ed-api comments delete 111222
```

---

## files — File uploads

### `files upload FILE_PATH`

Upload a file to EdStem's CDN.

```bash
ed-api files upload diagram.png
ed-api files upload report.pdf --json
```

**Output (default):**
```
Uploaded: https://static.us.edusercontent.com/files/abc123...
```

**Output (--json):**
```json
{"url": "https://static.us.edusercontent.com/files/abc123..."}
```

---

## content — Content conversion

### `content to-xml MARKDOWN`

Convert Markdown text to Ed XML format.

```bash
ed-api content to-xml "Hello **world**!"
ed-api content to-xml "# Title\n\nSome text." --json
```

**Output (--json):**
```json
{"xml": "<document version=\"2.0\"><paragraph>Hello <bold>world</bold>!</paragraph></document>"}
```

---

### `content to-markdown XML`

Convert Ed XML to Markdown.

```bash
ed-api content to-markdown '<document version="2.0"><paragraph>Hello <bold>world</bold>!</paragraph></document>'
ed-api content to-markdown '...' --json
```

**Output (--json):**
```json
{"markdown": "Hello **world**!"}
```

---

## Scripting with --json

All `--json` flags print valid JSON to stdout and suppress all other output, making it easy to pipe into `jq`:

```bash
# Get IDs of all unanswered threads
ed-api threads list 12345 --json | jq '.[] | select(.is_answered == false) | .id'

# Get all staff emails
ed-api courses users 12345 --role staff --json | jq -r '.[].email'

# Check token and exit non-zero on failure
ed-api auth check --json | jq -e '.status == "ok"'
```

# Courses & Users

## Listing your courses

`client.courses.list()` returns all courses you are enrolled in, fetched from the EdStem user info endpoint:

```python
from ed_api import EdClient

client = EdClient()

enrollments = client.courses.list()
for enrollment in enrollments:
    course = enrollment.course
    print(f"{course.id}: {course.code} — {course.name}")
    print(f"  Year: {course.year}, Session: {course.session}")
    print(f"  Status: {course.status}, Your role: {enrollment.role}")
```

### CourseEnrollment fields

| Field | Type | Description |
|---|---|---|
| `course` | `Course` | The course object |
| `role` | `str` | Your role: `"student"`, `"staff"`, `"admin"` |

### Course fields

| Field | Type | Description |
|---|---|---|
| `id` | `int` | Course ID (use this for API calls) |
| `code` | `str` | Course code (e.g. `CS101`) |
| `name` | `str` | Full course name |
| `year` | `str` | Academic year |
| `session` | `str` | Session or semester |
| `status` | `str` | `"active"` or `"archived"` |

### Finding active courses

```python
active = [e for e in client.courses.list() if e.course.status == "active"]
for e in active:
    print(f"{e.course.code}: {e.course.name} (role: {e.role})")
```

### Finding courses where you are staff

```python
teaching = [e for e in client.courses.list() if e.role in ("staff", "admin")]
for e in teaching:
    print(f"Teaching: {e.course.name}")
```

## Listing users in a course

`client.courses.users()` returns all enrolled users in a course. This uses the analytics endpoint and is available to staff and admins:

```python
users = client.courses.users(course_id=12345)
for user in users:
    print(f"{user.name} <{user.email}> — {user.course_role}")
```

### Filter by role

Pass `role=` to filter to a specific course role:

```python
# Get only students
students = client.courses.users(course_id=12345, role="student")
print(f"Students: {len(students)}")

# Get only staff
staff = client.courses.users(course_id=12345, role="staff")
for s in staff:
    print(f"  {s.name} <{s.email}>")

# Get admins
admins = client.courses.users(course_id=12345, role="admin")
```

### CourseUser fields

| Field | Type | Description |
|---|---|---|
| `id` | `int` | User ID |
| `name` | `str` | Display name |
| `email` | `str` | Email address |
| `role` | `str` | Global Ed role |
| `course_role` | `str` | Role in this course: `"student"`, `"staff"`, `"admin"` |
| `is_staff` | `bool` | Property: True if staff or admin |

### Example: build a student email list

```python
students = client.courses.users(course_id=12345, role="student")
emails = [u.email for u in students]
print("\n".join(emails))
```

### Example: find unanswered threads for a course

```python
unanswered = []
for thread in client.threads.list_all(course_id=12345):
    if not thread.is_answered and thread.type == "question":
        unanswered.append(thread)

print(f"Unanswered questions: {len(unanswered)}")
for t in unanswered[:10]:
    print(f"  #{t.number}: {t.title}")
```

## CLI usage

```bash
# List your courses
ed-api courses list

# List as JSON
ed-api courses list --json

# List users in a course
ed-api courses users 12345

# Filter by role
ed-api courses users 12345 --role staff

# JSON output
ed-api courses users 12345 --json | jq '.[] | .email'
```

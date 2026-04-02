# Lessons & Slides

EdStem courses can contain structured lessons made up of slides. Lessons are grouped into modules, and each slide can hold different content types: documents, quizzes, code exercises, PDFs, videos, web pages, or raw HTML.

## Listing lessons in a course

`list()` returns all lessons and their modules for a course:

```python
from ed_api import EdClient

client = EdClient()

lessons = client.lessons.list(course_id=12345)

for lesson in lessons:
    print(f"[{lesson.id}] {lesson.title}  (module: {lesson.module_id})")
```

Each `Lesson` object includes high-level metadata. Use `get()` to load the full slide list.

## Getting a lesson with slides

`get()` fetches a single lesson together with all of its slides:

```python
lesson = client.lessons.get(lesson_id=67890)

print(f"Lesson: {lesson.title}")
print(f"Slides: {len(lesson.slides)}")

for slide in lesson.slides:
    print(f"  [{slide.id}] {slide.title}  type={slide.type}")
```

## Getting a single slide

Retrieve one slide directly by its ID:

```python
slide = client.lessons.get_slide(slide_id=11223)
print(f"{slide.title} — {slide.type}")
```

## Filtering video slides

`video_slides()` is a convenience method that returns every slide of type `"video"` across all lessons in a course:

```python
video_slides = client.lessons.video_slides(course_id=12345)

for slide in video_slides:
    print(f"{slide.title}: {slide.video_url}")
```

Video URLs are Kaltura stream links. They may be `None` for slides that have not yet been published.

## Slide types

EdStem supports several slide types:

| Type | Description |
|---|---|
| `"document"` | Rich-text document slide |
| `"quiz"` | Interactive quiz |
| `"code"` | Code exercise or playground |
| `"pdf"` | Embedded PDF |
| `"video"` | Kaltura video |
| `"webpage"` | Embedded external URL |
| `"html"` | Raw HTML content |

## Data models

### Lesson

| Property | Type | Description |
|---|---|---|
| `id` | `int` | Global lesson ID |
| `course_id` | `int` | Owning course |
| `module_id` | `int \| None` | Parent module (if grouped) |
| `title` | `str` | Lesson title |
| `slides` | `list[Slide]` | Slides (populated by `get()`) |

### Slide

| Property | Type | Description |
|---|---|---|
| `id` | `int` | Global slide ID |
| `lesson_id` | `int` | Parent lesson |
| `title` | `str` | Slide title |
| `type` | `str` | Content type (see table above) |
| `video_url` | `str \| None` | Kaltura video URL (video slides only) |

### Module

| Property | Type | Description |
|---|---|---|
| `id` | `int` | Global module ID |
| `course_id` | `int` | Owning course |
| `title` | `str` | Module title |

## Example: collect all video URLs

```python
with EdClient() as client:
    for slide in client.lessons.video_slides(course_id=12345):
        if slide.video_url:
            print(f"{slide.title}: {slide.video_url}")
```

## Example: walk every slide in every lesson

```python
with EdClient() as client:
    for lesson in client.lessons.list(course_id=12345):
        full = client.lessons.get(lesson_id=lesson.id)
        for slide in full.slides:
            print(f"{full.title} / {slide.title} [{slide.type}]")
```

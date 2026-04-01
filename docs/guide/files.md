# Files

ed-api supports uploading files to EdStem's static CDN. Uploaded files return a permanent URL that can be embedded in thread or comment content.

## Upload from a file path

The simplest method — pass a local file path and ed-api handles everything:

```python
from ed_api import EdClient

client = EdClient()

url = client.files.upload_from_path("diagram.png")
print(url)
# https://static.us.edusercontent.com/files/abc123...
```

MIME type is auto-detected from the file extension using Python's `mimetypes` module. If the type cannot be determined, `application/octet-stream` is used.

## Upload from bytes

For files you already have in memory, or when you need to control the filename and content type:

```python
with open("chart.pdf", "rb") as f:
    file_bytes = f.read()

url = client.files.upload(
    filename="chart.pdf",
    file_bytes=file_bytes,
    content_type="application/pdf",
)
print(url)
```

## Method signatures

```python
def upload(self, filename: str, file_bytes: bytes, content_type: str) -> str:
    """Upload a file. Returns the static URL."""

def upload_from_path(self, file_path: str | pathlib.Path) -> str:
    """Upload a file from a local path. Auto-detects MIME type."""
```

Both methods return a `str` — the full static CDN URL for the uploaded file.

## Embedding uploaded files in content

Use the URL in Markdown when creating or editing threads and comments. ed-api's Markdown converter handles image and link syntax:

```python
# Upload a screenshot
url = client.files.upload_from_path("error_screenshot.png")

# Embed in a thread body
thread = client.threads.create(
    course_id=12345,
    title="Getting an error on line 42",
    body=f"I'm seeing this error:\n\n![Error screenshot]({url})\n\nAny ideas?",
    type="question",
    category="Debug Help",
)
```

## Region and CDN URL

The static CDN URL includes your configured region:

| Region | CDN base URL |
|---|---|
| `us` | `https://static.us.edusercontent.com/files/` |
| `au` | `https://static.au.edusercontent.com/files/` |

The region is inherited from your `EdClient` configuration.

## CLI usage

```bash
# Upload a single file
ed-api files upload diagram.png

# Get JSON with the URL
ed-api files upload diagram.png --json
# {"url": "https://static.us.edusercontent.com/files/abc123..."}
```

## Common file types

| Type | Extension | MIME type |
|---|---|---|
| PNG image | `.png` | `image/png` |
| JPEG image | `.jpg`, `.jpeg` | `image/jpeg` |
| GIF image | `.gif` | `image/gif` |
| PDF document | `.pdf` | `application/pdf` |
| Plain text | `.txt` | `text/plain` |
| CSV | `.csv` | `text/csv` |
| Python file | `.py` | `text/x-python` |
| ZIP archive | `.zip` | `application/zip` |

## Error handling

```python
from ed_api.exceptions import EdAPIError, EdForbiddenError

try:
    url = client.files.upload_from_path("large_file.zip")
except EdForbiddenError:
    print("File uploads not permitted for your account role.")
except EdAPIError as e:
    print(f"Upload failed: {e} (status={e.status_code})")
```

"""Files resource."""

import mimetypes
import pathlib

from ed_api._http import HttpClient


class FilesResource:
    def __init__(self, http: HttpClient, region: str = "us"):
        self._http = http
        self._static_url = f"https://static.{region}.edusercontent.com/files/"

    def upload(self, filename: str, file_bytes: bytes, content_type: str) -> str:
        """Upload a file. Returns the static URL."""
        response = self._http.upload(
            "files",
            files={"attachment": (filename, file_bytes, content_type)},
        )
        file_id = response.json()["file"]["id"]
        return self._static_url + file_id

    def upload_from_path(self, file_path: str | pathlib.Path) -> str:
        """Upload a file from a local path. Auto-detects MIME type."""
        path = pathlib.Path(file_path)
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type is None:
            mime_type = "application/octet-stream"
        file_bytes = path.read_bytes()
        return self.upload(path.name, file_bytes, mime_type)

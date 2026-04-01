"""EdClient: main entry point for the ed-api library."""

import os

from dotenv import find_dotenv, load_dotenv

from ed_api._http import HttpClient
from ed_api.resources.comments import CommentsResource
from ed_api.resources.courses import CoursesResource
from ed_api.resources.files import FilesResource
from ed_api.resources.lessons import LessonsResource
from ed_api.resources.threads import ThreadsResource
from ed_api.resources.user import UserResource


class EdClient:
    """Client for the EdStem API.

    Token is resolved from (in order):
    1. Constructor argument
    2. ED_API_TOKEN environment variable
    3. .env file in working directory
    """

    def __init__(
        self,
        token: str | None = None,
        region: str | None = None,
        rate_limit: float = 5.0,
    ):
        load_dotenv(find_dotenv(usecwd=True))

        self._token = token or os.environ.get("ED_API_TOKEN")
        if not self._token:
            raise ValueError(
                "No API token provided. Pass token= to EdClient, "
                "set ED_API_TOKEN environment variable, or add it to a .env file."
            )

        self._region = region or os.environ.get("ED_REGION", "us")
        self._http = HttpClient(
            token=self._token,
            region=self._region,
            rate_limit=rate_limit,
        )

        self.user = UserResource(self._http)
        self.courses = CoursesResource(self._http)
        self.threads = ThreadsResource(self._http)
        self.comments = CommentsResource(self._http)
        self.files = FilesResource(self._http, region=self._region)
        self.lessons = LessonsResource(self._http)

    def close(self):
        """Close the HTTP client."""
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

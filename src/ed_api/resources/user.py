"""User resource."""

from ed_api._http import HttpClient
from ed_api.models import ParsedUserInfo, parse_user_info


class UserResource:
    def __init__(self, http: HttpClient):
        self._http = http

    def info(self) -> ParsedUserInfo:
        """Get authenticated user info and enrolled courses."""
        response = self._http.get("user")
        return parse_user_info(response.json())

    def activity(
        self,
        user_id: int,
        course_id: int,
        limit: int = 30,
        offset: int = 0,
        filter: str = "all",
    ) -> list[dict]:
        """List user's threads and comments in a course."""
        response = self._http.get(
            f"users/{user_id}/profile/activity",
            params={
                "courseID": course_id,
                "limit": limit,
                "offset": offset,
                "filter": filter,
            },
        )
        return response.json().get("items", [])

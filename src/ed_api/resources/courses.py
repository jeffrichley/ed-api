"""Courses resource."""

from __future__ import annotations

from ed_api._http import HttpClient
from ed_api.models import CourseEnrollment, CourseUser, parse_user_info


class CoursesResource:
    def __init__(self, http: HttpClient):
        self._http = http

    def list(self) -> list[CourseEnrollment]:
        """List enrolled courses (from user info endpoint)."""
        response = self._http.get("user")
        info = parse_user_info(response.json())
        return info.courses

    def users(self, course_id: int, role: str | None = None) -> list[CourseUser]:
        """List users in a course. Optionally filter by role."""
        response = self._http.get(f"courses/{course_id}/analytics/users")
        users_data = response.json().get("users", [])
        users = [
            CourseUser(
                id=u["id"],
                name=u.get("name", ""),
                email=u.get("email", ""),
                role=u.get("role", "user"),
                course_role=u.get("course_role", "student"),
            )
            for u in users_data
        ]
        if role:
            users = [u for u in users if u.course_role == role]
        return users

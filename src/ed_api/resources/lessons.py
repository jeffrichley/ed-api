"""Lessons resource."""

from __future__ import annotations

from ed_api._http import HttpClient
from ed_api.models import Lesson, Module, Slide, parse_lesson, parse_module, parse_slide


class LessonsResource:
    def __init__(self, http: HttpClient):
        self._http = http

    def list(self, course_id: int) -> tuple[list[Lesson], list[Module]]:
        """List all lessons and modules for a course."""
        response = self._http.get(f"courses/{course_id}/lessons")
        data = response.json()
        lessons = [parse_lesson(l) for l in data.get("lessons", [])]
        modules = [parse_module(m) for m in data.get("modules", [])]
        return lessons, modules

    def get(self, lesson_id: int) -> Lesson:
        """Get a lesson with all slides."""
        response = self._http.get(f"lessons/{lesson_id}")
        return parse_lesson(response.json().get("lesson", {}))

    def get_slide(self, slide_id: int) -> Slide:
        """Get a single slide."""
        response = self._http.get(f"lessons/slides/{slide_id}")
        return parse_slide(response.json().get("slide", {}))

    def video_slides(self, course_id: int) -> list[tuple[Lesson, Slide]]:
        """Get all video slides across all lessons in a course.
        Returns list of (lesson, slide) pairs."""
        lessons, _ = self.list(course_id)
        results = []
        for lesson_summary in lessons:
            lesson = self.get(lesson_summary.id)
            for slide in lesson.slides:
                if slide.type == "video":
                    results.append((lesson, slide))
        return results

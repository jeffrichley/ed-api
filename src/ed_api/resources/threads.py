"""Threads resource."""

from __future__ import annotations

from typing import Generator

from ed_api._http import HttpClient
from ed_api.content import markdown_to_ed_xml
from ed_api.models import Thread, ThreadDetail, parse_thread, parse_thread_detail


class ThreadsResource:
    def __init__(self, http: HttpClient):
        self._http = http

    def list(
        self,
        course_id: int,
        limit: int = 100,
        offset: int = 0,
        sort: str = "new",
    ) -> list[Thread]:
        """List threads in a course."""
        response = self._http.get(
            f"courses/{course_id}/threads",
            params={"limit": limit, "offset": offset, "sort": sort},
        )
        return [parse_thread(t) for t in response.json().get("threads", [])]

    def list_all(
        self, course_id: int, sort: str = "new"
    ) -> Generator[Thread, None, None]:
        """Iterate all threads in a course (handles pagination)."""
        offset = 0
        limit = 100
        while True:
            threads = self.list(course_id, limit=limit, offset=offset, sort=sort)
            if not threads:
                break
            yield from threads
            if len(threads) < limit:
                break
            offset += limit

    def get(self, thread_id: int) -> ThreadDetail:
        """Get a thread by global ID, including comments."""
        response = self._http.get(f"threads/{thread_id}")
        return parse_thread_detail(response.json())

    def get_by_number(self, course_id: int, thread_number: int) -> ThreadDetail:
        """Get a thread by course-local number."""
        response = self._http.get(f"courses/{course_id}/threads/{thread_number}")
        return parse_thread_detail(response.json())

    def search(self, course_id: int, query: str, limit: int = 100) -> list[Thread]:
        """Search threads by title and content (client-side filtering)."""
        query_lower = query.lower()
        results = []
        for thread in self.list_all(course_id):
            if (query_lower in thread.title.lower() or
                    query_lower in thread.category.lower()):
                results.append(thread)
                if len(results) >= limit:
                    break
        return results

    def create(
        self,
        course_id: int,
        title: str,
        body: str,
        type: str = "question",
        category: str = "",
        is_private: bool = False,
        is_anonymous: bool = False,
    ) -> Thread:
        """Create a new thread. Body is markdown (converted to Ed XML)."""
        response = self._http.post(
            f"courses/{course_id}/threads",
            json={
                "thread": {
                    "type": type,
                    "title": title,
                    "category": category,
                    "subcategory": "",
                    "subsubcategory": "",
                    "content": markdown_to_ed_xml(body),
                    "is_pinned": False,
                    "is_private": is_private,
                    "is_anonymous": is_anonymous,
                    "is_megathread": False,
                    "anonymous_comments": False,
                }
            },
        )
        return parse_thread(response.json().get("thread", {}))

    def edit(
        self,
        thread_id: int,
        title: str | None = None,
        body: str | None = None,
        category: str | None = None,
        is_private: bool | None = None,
    ) -> Thread:
        """Edit a thread. Fetches current state, merges changes, sends PUT."""
        # Fetch current thread to merge
        current = self._http.get(f"threads/{thread_id}").json().get("thread", {})

        if title is not None:
            current["title"] = title
        if body is not None:
            current["content"] = markdown_to_ed_xml(body)
        if category is not None:
            current["category"] = category
        if is_private is not None:
            current["is_private"] = is_private

        response = self._http.put(
            f"threads/{thread_id}",
            json={"thread": current},
        )
        return parse_thread(response.json().get("thread", {}))

    def lock(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/lock")

    def unlock(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/unlock")

    def pin(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/pin")

    def unpin(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/unpin")

    def set_private(self, thread_id: int, private: bool = True) -> None:
        """Set thread visibility."""
        self.edit(thread_id, is_private=private)

    def endorse(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/endorse")

    def unendorse(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/unendorse")

    def star(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/star")

    def unstar(self, thread_id: int) -> None:
        self._http.post(f"threads/{thread_id}/unstar")

    def delete(self, thread_id: int) -> None:
        """Delete a thread."""
        self._http.delete(f"threads/{thread_id}")

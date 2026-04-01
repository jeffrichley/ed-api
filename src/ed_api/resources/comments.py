"""Comments resource."""

from ed_api._http import HttpClient
from ed_api.content import markdown_to_ed_xml
from ed_api.models import Comment, parse_comment


class CommentsResource:
    def __init__(self, http: HttpClient):
        self._http = http

    def post(
        self,
        thread_id: int,
        content: str,
        is_answer: bool = False,
        is_private: bool = False,
        is_anonymous: bool = False,
    ) -> Comment:
        """Post a comment or answer on a thread. Content is markdown."""
        response = self._http.post(
            f"threads/{thread_id}/comments",
            json={
                "comment": {
                    "type": "answer" if is_answer else "comment",
                    "content": markdown_to_ed_xml(content),
                    "is_private": is_private,
                    "is_anonymous": is_anonymous,
                }
            },
        )
        return parse_comment(response.json().get("comment", {}))

    def reply(
        self,
        comment_id: int,
        content: str,
        is_private: bool = False,
        is_anonymous: bool = False,
    ) -> Comment:
        """Reply to an existing comment. Content is markdown."""
        response = self._http.post(
            f"comments/{comment_id}/comments",
            json={
                "comment": {
                    "type": "comment",
                    "content": markdown_to_ed_xml(content),
                    "is_private": is_private,
                    "is_anonymous": is_anonymous,
                }
            },
        )
        return parse_comment(response.json().get("comment", {}))

    def edit(self, comment_id: int, content: str) -> Comment:
        """Edit an existing comment. Content is markdown."""
        response = self._http.put(
            f"comments/{comment_id}",
            json={
                "comment": {
                    "content": markdown_to_ed_xml(content),
                }
            },
        )
        return parse_comment(response.json().get("comment", {}))

    def endorse(self, comment_id: int) -> None:
        self._http.post(f"comments/{comment_id}/endorse")

    def unendorse(self, comment_id: int) -> None:
        self._http.post(f"comments/{comment_id}/unendorse")

    def accept(self, thread_id: int, comment_id: int) -> None:
        """Accept a comment as the answer to a thread."""
        self._http.post(f"threads/{thread_id}/accept/{comment_id}")

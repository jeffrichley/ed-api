from unittest.mock import MagicMock
from ed_api.resources.comments import CommentsResource
from ed_api.models import Comment


class TestCommentsResource:
    def test_post_comment(self, comment_response):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = comment_response
        mock_http.post.return_value = mock_resp

        resource = CommentsResource(mock_http)
        result = resource.post(100, "Here is my response.")

        assert isinstance(result, Comment)
        assert result.id == 300
        mock_http.post.assert_called_once()
        call_args = mock_http.post.call_args
        assert call_args[0][0] == "threads/100/comments"

    def test_post_answer(self, comment_response):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = comment_response
        mock_http.post.return_value = mock_resp

        resource = CommentsResource(mock_http)
        resource.post(100, "The answer is...", is_answer=True)

        call_args = mock_http.post.call_args
        body = call_args[1]["json"]["comment"]
        assert body["type"] == "answer"

    def test_reply(self, comment_response):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = comment_response
        mock_http.post.return_value = mock_resp

        resource = CommentsResource(mock_http)
        resource.reply(200, "Follow-up reply")

        call_args = mock_http.post.call_args
        assert call_args[0][0] == "comments/200/comments"

    def test_endorse(self):
        mock_http = MagicMock()
        resource = CommentsResource(mock_http)
        resource.endorse(200)
        mock_http.post.assert_called_once_with("comments/200/endorse")

    def test_accept(self):
        mock_http = MagicMock()
        resource = CommentsResource(mock_http)
        resource.accept(thread_id=100, comment_id=200)
        mock_http.post.assert_called_once_with("threads/100/accept/200")

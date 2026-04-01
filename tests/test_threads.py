from unittest.mock import MagicMock
from ed_api.resources.threads import ThreadsResource
from ed_api.models import Thread, ThreadDetail


class TestThreadsResource:
    def _make_resource(self, responses=None):
        mock_http = MagicMock()
        if responses:
            mock_resp = MagicMock()
            mock_resp.json.side_effect = responses if isinstance(responses, list) else [responses]
            mock_http.get.return_value = mock_resp
            mock_http.post.return_value = mock_resp
            mock_http.put.return_value = mock_resp
        return ThreadsResource(mock_http), mock_http

    def test_list(self, thread_list_response):
        resource, mock_http = self._make_resource()
        mock_resp = MagicMock()
        mock_resp.json.return_value = thread_list_response
        mock_http.get.return_value = mock_resp

        result = resource.list(54321, limit=50)
        assert len(result) == 1
        assert isinstance(result[0], Thread)
        assert result[0].title == "get_data() returns NaN"

    def test_get(self, thread_detail_response):
        resource, mock_http = self._make_resource()
        mock_resp = MagicMock()
        mock_resp.json.return_value = thread_detail_response
        mock_http.get.return_value = mock_resp

        result = resource.get(100)
        assert isinstance(result, ThreadDetail)
        assert result.title == "get_data() returns NaN"
        assert len(result.comments) == 2

    def test_lock(self):
        resource, mock_http = self._make_resource()
        resource.lock(100)
        mock_http.post.assert_called_once_with("threads/100/lock")

    def test_endorse(self):
        resource, mock_http = self._make_resource()
        resource.endorse(100)
        mock_http.post.assert_called_once_with("threads/100/endorse")

    def test_pin(self):
        resource, mock_http = self._make_resource()
        resource.pin(100)
        mock_http.post.assert_called_once_with("threads/100/pin")

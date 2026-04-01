from unittest.mock import MagicMock
from ed_api.resources.user import UserResource
from ed_api.models import ParsedUserInfo


class TestUserResource:
    def test_info(self, user_info_response):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = user_info_response
        mock_http.get.return_value = mock_resp

        resource = UserResource(mock_http)
        result = resource.info()

        assert isinstance(result, ParsedUserInfo)
        assert result.user.name == "Test User"
        mock_http.get.assert_called_once_with("user")

    def test_activity(self):
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"items": [{"type": "thread", "value": {}}]}
        mock_http.get.return_value = mock_resp

        resource = UserResource(mock_http)
        result = resource.activity(user_id=1, course_id=2, limit=10)

        assert len(result) == 1
        mock_http.get.assert_called_once()

import httpx
import pytest
from unittest.mock import patch, MagicMock
from ed_api._http import HttpClient
from ed_api.exceptions import EdAuthError, EdNotFoundError, EdRateLimitError, EdAPIError


class TestHttpClient:
    def test_creates_with_token(self):
        client = HttpClient(token="test-token", region="us")
        assert client._base_url == "https://us.edstem.org/api/"

    def test_au_region(self):
        client = HttpClient(token="test-token", region="au")
        assert client._base_url == "https://au.edstem.org/api/"

    def test_auth_header_set(self):
        client = HttpClient(token="my-token", region="us")
        assert client._client.headers["Authorization"] == "Bearer my-token"

    def test_maps_401_to_auth_error(self):
        client = HttpClient(token="bad", region="us")
        with patch.object(client._client, "request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            mock_resp.json.return_value = {"message": "bad token"}
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "401", request=MagicMock(), response=mock_resp
            )
            mock_req.return_value = mock_resp
            with pytest.raises(EdAuthError):
                client.get("user")

    def test_maps_404_to_not_found(self):
        client = HttpClient(token="tok", region="us")
        with patch.object(client._client, "request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_resp.json.return_value = {"message": "not found"}
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404", request=MagicMock(), response=mock_resp
            )
            mock_req.return_value = mock_resp
            with pytest.raises(EdNotFoundError):
                client.get("threads/999")

    def test_maps_429_to_rate_limit(self):
        client = HttpClient(token="tok", region="us")
        with patch.object(client._client, "request") as mock_req:
            mock_resp = MagicMock()
            mock_resp.status_code = 429
            mock_resp.json.return_value = {"message": "rate limited"}
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "429", request=MagicMock(), response=mock_resp
            )
            mock_req.return_value = mock_resp
            with pytest.raises(EdRateLimitError):
                client.get("threads")

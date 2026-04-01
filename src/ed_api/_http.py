"""HTTP client wrapper with rate limiting, retries, and error mapping."""

import time

import httpx

from ed_api.exceptions import (
    EdAPIError,
    EdAuthError,
    EdForbiddenError,
    EdNotFoundError,
    EdRateLimitError,
)

ERROR_MAP = {
    401: EdAuthError,
    403: EdForbiddenError,
    404: EdNotFoundError,
    429: EdRateLimitError,
}


class HttpClient:
    """Wraps httpx.Client with Ed-specific auth, error handling, and rate limiting."""

    def __init__(
        self,
        token: str,
        region: str = "us",
        rate_limit: float = 5.0,
        max_retries: int = 3,
    ):
        self._base_url = f"https://{region}.edstem.org/api/"
        self._rate_limit = rate_limit
        self._max_retries = max_retries
        self._min_interval = 1.0 / rate_limit if rate_limit > 0 else 0
        self._last_request_time = 0.0

        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=30.0,
        )

    def _throttle(self):
        """Enforce rate limit by sleeping if needed."""
        if self._min_interval > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
        self._last_request_time = time.time()

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make an HTTP request with rate limiting and error mapping."""
        url = self._base_url + path

        for attempt in range(self._max_retries):
            self._throttle()
            try:
                response = self._client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                try:
                    body = e.response.json()
                except Exception:
                    body = {"raw": e.response.text}

                # Retry on 429 with backoff
                if status == 429 and attempt < self._max_retries - 1:
                    wait = 2 ** attempt
                    time.sleep(wait)
                    continue

                error_cls = ERROR_MAP.get(status, EdAPIError)
                msg = body.get("message", f"HTTP {status}")
                raise error_cls(msg, status_code=status, response_body=body) from e

        # Should not reach here
        raise EdAPIError("Max retries exceeded", status_code=0, response_body={})

    def get(self, path: str, params: dict | None = None) -> httpx.Response:
        return self._request("GET", path, params=params)

    def post(self, path: str, json: dict | None = None, **kwargs) -> httpx.Response:
        return self._request("POST", path, json=json, **kwargs)

    def put(self, path: str, json: dict | None = None) -> httpx.Response:
        return self._request("PUT", path, json=json)

    def delete(self, path: str) -> httpx.Response:
        return self._request("DELETE", path)

    def upload(self, path: str, files: dict) -> httpx.Response:
        return self._request("POST", path, files=files)

    def close(self):
        self._client.close()

from ed_api.exceptions import (
    EdAPIError,
    EdAuthError,
    EdNotFoundError,
    EdForbiddenError,
    EdRateLimitError,
)


class TestExceptions:
    def test_base_error_has_status_and_body(self):
        err = EdAPIError("something failed", status_code=500, response_body={"error": "internal"})
        assert err.status_code == 500
        assert err.response_body == {"error": "internal"}
        assert "something failed" in str(err)

    def test_auth_error_is_api_error(self):
        err = EdAuthError("bad token", status_code=401, response_body={})
        assert isinstance(err, EdAPIError)
        assert err.status_code == 401

    def test_not_found_error(self):
        err = EdNotFoundError("thread 999", status_code=404, response_body={})
        assert err.status_code == 404

    def test_forbidden_error(self):
        err = EdForbiddenError("no access", status_code=403, response_body={})
        assert err.status_code == 403

    def test_rate_limit_error(self):
        err = EdRateLimitError("slow down", status_code=429, response_body={})
        assert err.status_code == 429

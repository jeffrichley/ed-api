import os
import pytest
from unittest.mock import patch
from ed_api.client import EdClient
from ed_api.resources.user import UserResource
from ed_api.resources.courses import CoursesResource
from ed_api.resources.threads import ThreadsResource
from ed_api.resources.comments import CommentsResource
from ed_api.resources.files import FilesResource


class TestEdClient:
    def test_create_with_token(self):
        client = EdClient(token="test-token")
        assert isinstance(client.user, UserResource)
        assert isinstance(client.courses, CoursesResource)
        assert isinstance(client.threads, ThreadsResource)
        assert isinstance(client.comments, CommentsResource)
        assert isinstance(client.files, FilesResource)

    def test_create_with_env_var(self):
        with patch.dict(os.environ, {"ED_API_TOKEN": "env-token"}):
            client = EdClient()
            assert client._http is not None

    def test_create_without_token_raises(self):
        # Clear all potential token sources
        env_without_token = {k: v for k, v in os.environ.items() if k != "ED_API_TOKEN"}
        with patch.dict(os.environ, env_without_token, clear=True):
            with pytest.raises(ValueError, match="token"):
                EdClient()

    def test_region_default(self):
        client = EdClient(token="tok")
        assert client._region == "us"

    def test_region_override(self):
        client = EdClient(token="tok", region="au")
        assert client._region == "au"

    def test_region_from_env(self):
        with patch.dict(os.environ, {"ED_API_TOKEN": "tok", "ED_REGION": "eu"}):
            client = EdClient()
            assert client._region == "eu"
